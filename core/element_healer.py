"""
Self-healing element finder for Appium (Android + iOS).

When a locator fails, this module applies 6 progressively-weaker strategies
before declaring an element missing. Because the UzioMobile app uses
visible-text locators (no testIDs), healing focuses on text matching variants.

Strategy cascade:
    S1  Wait + retry exact text
    S2  Case-insensitive + trimmed text
    S3  Partial text (longest meaningful word, contains)
    S4  Accessibility id / content-desc / name
    S5  Widget-class + text (Button/TextView vs XCUIElementTypeButton/StaticText)
    S6  Page-source scan -> broad contains() match

Every heal is recorded in a HealResult so the Reporting Agent can show what
was healed and the Self-Healing Agent can decide whether to patch the test.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException


@dataclass
class HealResult:
    original_text: str
    healed: bool = False
    winning_strategy: Optional[str] = None
    winning_locator: Optional[str] = None
    failed_strategies: List[str] = field(default_factory=list)
    element: object = None

    def __str__(self):
        if not self.healed:
            return (f"[HEAL_FAIL] '{self.original_text}' — all strategies exhausted. "
                    f"Tried: {self.failed_strategies}")
        return (f"[HEALED] '{self.original_text}' via {self.winning_strategy} "
                f"-> {self.winning_locator}")


_STOP_WORDS = {"the", "and", "for", "are", "was", "with", "that",
               "this", "from", "has", "have", "you", "your"}


def longest_meaningful_word(text: str) -> str:
    """Return the longest >=4-char non-stopword token (for partial matching)."""
    if not text:
        return text
    best = ""
    for word in __import__("re").split(r"[\s\-_/().,]+", text):
        if len(word) < 4 or word.lower() in _STOP_WORDS:
            continue
        if len(word) > len(best):
            best = word
    return best or text.split()[0]


def find(driver, text: str, context: str = "tap", timeout: int = 2) -> HealResult:
    """
    Try to locate an element by display text, applying healing strategies.

    Args:
        driver:  Appium driver (Android or iOS)
        text:    visible text / label to find
        context: "tap" | "verify" | "input" — biases widget-class strategy
        timeout: seconds to wait in S1

    Returns:
        HealResult — check .healed and .element
    """
    result = HealResult(original_text=text)

    # ── S1: wait + exact ──────────────────────────────────────────────────
    time.sleep(timeout)
    el = _try_exact(driver, text)
    if el:
        return HealResult(text, True, "S1-Exact(after wait)", f"text='{text}'", element=el)
    result.failed_strategies.append("S1-Exact")

    # ── S2: case-insensitive + trim ───────────────────────────────────────
    el = _try_case_insensitive(driver, text.strip())
    if el:
        return HealResult(text, True, "S2-CaseInsensitive", f"text~='{text.strip()}'", element=el)
    result.failed_strategies.append("S2-CaseInsensitive")

    # ── S3: partial text ──────────────────────────────────────────────────
    partial = longest_meaningful_word(text)
    el = _try_partial(driver, partial)
    if el:
        return HealResult(text, True, "S3-Partial", f"contains('{partial}')", element=el)
    result.failed_strategies.append(f"S3-Partial({partial})")

    # ── S4: accessibility id ──────────────────────────────────────────────
    el = _try_accessibility_id(driver, text) or _try_accessibility_id(driver, partial)
    if el:
        return HealResult(text, True, "S4-AccessibilityId", f"a11y~='{partial}'", element=el)
    result.failed_strategies.append("S4-AccessibilityId")

    # ── S5: widget-class + text ───────────────────────────────────────────
    el = _try_widget_class(driver, partial, context)
    if el:
        return HealResult(text, True, "S5-WidgetClass", f"widget~='{partial}'", element=el)
    result.failed_strategies.append("S5-WidgetClass")

    # ── S6: page-source scan ──────────────────────────────────────────────
    el = _try_page_source(driver, text, partial)
    if el:
        return HealResult(text, True, "S6-PageSourceScan", f"source~='{partial}'", element=el)
    result.failed_strategies.append("S6-PageSourceScan")

    print(result)
    return result


# ─── Strategy implementations ─────────────────────────────────────────────────

def _find_first(driver, *xpaths):
    for xp in xpaths:
        try:
            els = driver.find_elements(AppiumBy.XPATH, xp)
            if els:
                return els[0]
        except WebDriverException:
            continue
    return None


def _try_exact(driver, text):
    return _find_first(
        driver,
        f"//*[@text='{text}' or @content-desc='{text}']",
        f"//*[@name='{text}' or @label='{text}' or @value='{text}']",
    )


def _try_case_insensitive(driver, text):
    lower = text.lower()
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    low = "abcdefghijklmnopqrstuvwxyz"
    return _find_first(
        driver,
        f"//*[translate(@text,'{upper}','{low}')='{lower}']",
        f"//*[translate(@name,'{upper}','{low}')='{lower}' or "
        f"translate(@label,'{upper}','{low}')='{lower}']",
    )


def _try_partial(driver, partial):
    return _find_first(
        driver,
        f"//*[contains(@text, '{partial}') or contains(@content-desc, '{partial}')]",
        f"//*[contains(@name, '{partial}') or contains(@label, '{partial}')]",
    )


def _try_accessibility_id(driver, value):
    try:
        els = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, value)
        if els:
            return els[0]
    except WebDriverException:
        pass
    return _find_first(driver, f"//*[@content-desc='{value}']")


def _try_widget_class(driver, partial, context):
    if context == "tap":
        widgets = ["android.widget.Button", "android.widget.TextView",
                   "android.widget.ImageView", "XCUIElementTypeButton"]
    else:
        widgets = ["android.widget.TextView", "android.widget.EditText",
                   "android.widget.CheckBox", "XCUIElementTypeStaticText",
                   "XCUIElementTypeTextField"]
    for w in widgets:
        el = _find_first(driver, f"//{w}[contains(@text, '{partial}')]")
        if el:
            return el
    return None


def _try_page_source(driver, text, partial):
    try:
        src = driver.page_source or ""
    except WebDriverException:
        return None
    if text in src or partial in src:
        return _find_first(
            driver,
            f"//*[contains(@text,'{partial}') or contains(@content-desc,'{partial}')]",
            f"//*[contains(@name,'{partial}') or contains(@value,'{partial}') "
            f"or contains(@label,'{partial}')]",
        )
    return None
