"""
BasePage — common Appium interactions with built-in self-healing.

All page objects extend this. Methods accept VISIBLE TEXT (since UzioMobile has
no testIDs) and fall back to the ElementHealer cascade when a direct match fails.
"""

import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions import interaction

from core import element_healer
from core.config_loader import config


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.default_timeout = config.timeout("default")
        self.is_ios = config.platform == "ios"
        # collected during the session for the reporter
        self.heal_log = []

    # ─── Find ─────────────────────────────────────────────────────────────────

    def _xpath_for_text(self, text):
        # HEALED 2026-05-23: UZIO RN controls expose their label via @content-desc
        # (e.g. the LOGIN button), not @text — include it in every text match.
        # Matches Android @text/@content-desc and iOS @name/@label/@value.
        return (f"//*[@text='{text}' or @content-desc='{text}' or @name='{text}' "
                f"or @label='{text}' or @value='{text}']")

    def _find_direct(self, text):
        try:
            els = self.driver.find_elements(AppiumBy.XPATH, self._xpath_for_text(text))
            return els[0] if els else None
        except WebDriverException:
            return None

    def find(self, text, context="tap"):
        """Find an element by text, healing if needed. Raises if not found."""
        el = self._find_direct(text)
        if el:
            return el
        result = element_healer.find(self.driver, text, context=context)
        self.heal_log.append(result)
        if not result.healed or result.element is None:
            raise NoSuchElementError(f"Element not found after healing: '{text}'. {result}")
        if not result.winning_strategy.startswith("S1"):
            print(f"[BasePage] {result}")
        return result.element

    # ─── Tap ──────────────────────────────────────────────────────────────────

    def tap(self, text):
        self.find(text, context="tap").click()
        print(f"[BasePage] tap: {text}")

    def tap_by_accessibility_id(self, acc_id):
        self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, acc_id).click()
        print(f"[BasePage] tap a11y: {acc_id}")

    def tap_exact(self, text):
        """
        Tap an element matching `text` EXACTLY (no partial/heal fallback). Raises if
        absent. Use for drawer/menu items where a partial match (e.g. 'Info' →
        'Account Information') would tap the wrong element and mis-navigate.
        """
        els = self.driver.find_elements(AppiumBy.XPATH, self._xpath_for_text(text))
        if not els:
            raise NoSuchElementError(f"Exact element not found: '{text}'")
        els[0].click()
        print(f"[BasePage] tap_exact: {text}")

    def text_in_source(self, text):
        """True if `text` appears anywhere in the current page source (off-screen too)."""
        try:
            return text in self.driver.page_source
        except WebDriverException:
            return False

    def tap_at(self, x, y):
        """Tap raw coordinates (W3C actions) — used for icon-only elements."""
        # HEALED 2026-05-23: Selenium 4 PointerInput takes a kind string from the
        # interaction module (POINTER_TOUCH), not a Java-style PointerInput.Kind enum.
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        actions = ActionBuilder(self.driver, mouse=finger)
        actions.pointer_action.move_to_location(x, y).pointer_down().pause(0.1).pointer_up()
        actions.perform()
        print(f"[BasePage] tap_at: ({x}, {y})")

    # ─── Input ──────────────────────────────────────────────────────────────

    def enter(self, field_text, value):
        """
        Type into a text field. field_text is the placeholder/label.
        On Android the EditText may be a sibling of the label; we try the
        nearest editable element.
        """
        el = self.find(field_text, context="input")
        try:
            el.clear()
        except WebDriverException:
            pass
        el.send_keys(value)
        print(f"[BasePage] enter '{value}' into '{field_text}'")

    def enter_by_index(self, index, value, field_class=None):
        """
        Enter into the Nth editable field (0-based). Used for login where both
        username and password share the same placeholder text.
        """
        cls = field_class or ("XCUIElementTypeTextField" if self.is_ios
                              else "android.widget.EditText")
        fields = self.driver.find_elements(AppiumBy.CLASS_NAME, cls)
        if index >= len(fields):
            # Try secure field for password on iOS
            if self.is_ios:
                fields += self.driver.find_elements(
                    AppiumBy.CLASS_NAME, "XCUIElementTypeSecureTextField")
        if index >= len(fields):
            raise NoSuchElementError(f"No editable field at index {index} (found {len(fields)})")
        fields[index].clear()
        fields[index].send_keys(value)
        print(f"[BasePage] enter '{value}' into field[{index}]")

    # ─── Verify ────────────────────────────────────────────────────────────

    def is_text_visible(self, text, timeout=None):
        timeout = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + timeout
        xp = (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
              f"or contains(@name,'{text}') or contains(@label,'{text}') "
              f"or contains(@value,'{text}')]")
        while time.time() < deadline:
            try:
                if self.driver.find_elements(AppiumBy.XPATH, xp):
                    return True
            except WebDriverException:
                pass
            time.sleep(0.5)
        return False

    def verify_visible(self, text, timeout=None):
        if not self.is_text_visible(text, timeout):
            # Last-ditch heal attempt
            result = element_healer.find(self.driver, text, context="verify")
            self.heal_log.append(result)
            if not result.healed:
                raise AssertionError(f"[VERIFY FAIL] Text not visible: '{text}'")
        print(f"[BasePage] verified visible: {text}")

    def verify_not_visible(self, text):
        xp = (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
              f"or contains(@name,'{text}') or contains(@label,'{text}')]")
        if self.driver.find_elements(AppiumBy.XPATH, xp):
            raise AssertionError(f"[VERIFY FAIL] Text should be absent but found: '{text}'")
        print(f"[BasePage] verified absent: {text}")

    # ─── Wait ────────────────────────────────────────────────────────────────

    def wait_for_text(self, text, timeout=None):
        timeout = timeout if timeout is not None else self.default_timeout
        if not self.is_text_visible(text, timeout):
            raise TimeoutException(f"'{text}' not visible after {timeout}s")
        print(f"[BasePage] appeared: {text}")

    def wait_for_text_gone(self, text, timeout=None):
        timeout = timeout if timeout is not None else self.default_timeout
        deadline = time.time() + timeout
        xp = (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
              f"or contains(@name,'{text}')]")
        while time.time() < deadline:
            if not self.driver.find_elements(AppiumBy.XPATH, xp):
                return
            time.sleep(0.5)
        raise TimeoutException(f"'{text}' still visible after {timeout}s")

    # ─── Popups ────────────────────────────────────────────────────────────

    def dismiss_popup_if_present(self, button_text, timeout=3):
        """Tap a popup dismiss button if it appears; no-op otherwise."""
        if self.is_text_visible(button_text, timeout):
            self.tap(button_text)
            print(f"[BasePage] dismissed popup: {button_text}")
            time.sleep(0.5)
            return True
        return False

    def dismiss_onboarding_if_present(self, rounds=4):
        """
        Dismiss the in-app onboarding / feature-walkthrough carousel that appears
        on first launch.

        HEALED 2026-05-24: the UZIO onboarding is a THREE-screen carousel before the
        login page. Reach login by either (a) tapping "Skip"/"Get Started", or
        (b) swiping through all 3 screens. We try the button first (fastest); if it's
        not present we swipe left to advance, re-checking for a button each time.
        Stops as soon as the LOGIN screen (or a real bottom-nav tab) appears.
        """
        skip_buttons = ["Skip", "SKIP", "Get Started", "GET STARTED", "Got it",
                        "Got It", "Done", "Next", "Finish", "Close", "Continue"]
        any_dismissed = False
        for _ in range(rounds + 3):   # extra rounds: up to 3 swipes for 3 screens
            # If we've reached the login page or the real app, stop.
            if self.is_text_visible("LOGIN", 1):
                break
            tapped = False
            for btn in skip_buttons:
                els = self.driver.find_elements(AppiumBy.XPATH,
                    f"//*[@text='{btn}' or @name='{btn}' or @content-desc='{btn}' or @label='{btn}']")
                if els:
                    els[0].click()
                    print(f"[BasePage] dismissed onboarding: {btn}")
                    any_dismissed = True
                    tapped = True
                    time.sleep(1.5)
                    break
            if tapped:
                continue
            # No button found this round — check if the carousel is still showing.
            # The first slide shows "Benefits" + a Skip area; if no button and no
            # carousel signal, assume we're past onboarding.
            on_carousel = (self.is_text_visible("Skip", 1)
                           or self.is_text_visible("enrollment", 1))
            if not on_carousel:
                break
            # Advance the carousel by swiping to the next screen.
            self.swipe_left()
            print("[BasePage] swiped carousel to next screen")
            any_dismissed = True
            time.sleep(1.0)
        return any_dismissed

    def dismiss_system_permissions(self, rounds=3):
        """
        Dismiss native OS permission dialogs that appear on launch and can block
        the app UI (e.g. Android 13 notification permission, location, etc.).
        Taps the 'grant' option so any push/notification tests still work.
        Safe to call repeatedly — no-op when no dialog is present.
        """
        # Grant-style buttons (exact text). Android system dialog button is "Allow";
        # newer Android uses "While using the app".
        # iOS (HEALED 2026-05-25) uses different labels: location = "Allow While Using
        # App" / "Allow Once"; notifications/ATT = "Allow"; generic = "OK".
        grant_buttons = [
            # Android
            "Allow", "ALLOW", "While using the app", "Only this time",
            "Allow all the time", "OK", "Continue",
            # iOS
            "Allow While Using App", "Allow While Using the App", "Allow Once",
        ]
        any_dismissed = False
        for _ in range(rounds):
            dismissed_this_round = False
            for btn in grant_buttons:
                # exact-match only so we hit the button, not a title that contains the word
                els = self.driver.find_elements(AppiumBy.XPATH,
                    f"//*[@text='{btn}' or @name='{btn}' or @label='{btn}']")
                if els:
                    els[0].click()
                    print(f"[BasePage] dismissed system permission: {btn}")
                    any_dismissed = True
                    dismissed_this_round = True
                    time.sleep(1)
                    break
            if not dismissed_this_round:
                break
        return any_dismissed

    # ─── App-foreground safety ─────────────────────────────────────────────────

    def current_package(self):
        try:
            return self.driver.current_package
        except Exception:
            return None

    def in_app(self, pkg=None):
        """True if the UZIO app is in the foreground (Android only; iOS assumes True)."""
        if self.is_ios:
            return True
        pkg = pkg or config.get("app.android.package")
        cur = self.current_package()
        return cur is None or cur == pkg

    def ensure_app_foreground(self, pkg=None):
        """If the app has drifted to the background/another app, bring it forward."""
        if self.is_ios:
            return
        pkg = pkg or config.get("app.android.package")
        if not self.in_app(pkg):
            drifted = self.current_package()
            try:
                self.driver.activate_app(pkg)
                print(f"[BasePage] app had drifted to '{drifted}' — reactivated {pkg}")
                time.sleep(2)
            except WebDriverException as e:
                print(f"[BasePage] activate_app failed: {e}")

    def safe_press_back(self, pkg=None):
        """
        Press BACK, but never leave the app: if BACK exits UZIO to the launcher /
        another app, immediately reactivate UZIO and return False so callers stop
        backing out further. Returns True if still safely inside the app.
        """
        pkg = pkg or config.get("app.android.package")
        self.press_back()
        time.sleep(0.6)
        if not self.in_app(pkg):
            print("[BasePage] BACK left the app — reactivating; will NOT back out further")
            self.ensure_app_foreground(pkg)
            return False
        return True

    # ─── Gestures ────────────────────────────────────────────────────────────

    def press_back(self):
        """Android hardware BACK; iOS nav-bar back button / edge-swipe fallback."""
        if not self.is_ios:
            try:
                self.driver.press_keycode(4)  # Android KEYCODE_BACK
                print("[BasePage] pressBack (Android keycode)")
                return
            except WebDriverException:
                pass
        # iOS has no hardware back. Try a nav-bar back button first (RN/iOS exposes
        # it as a 'Back'/chevron element), then fall back to the edge-swipe-from-left
        # gesture (the standard iOS "go back").
        backs = self.driver.find_elements(
            AppiumBy.XPATH, "//*[@name='Back' or @label='Back' or @name='chevron-back' "
                            "or contains(@name,'back') or contains(@label,'Back')]")
        if backs:
            backs[0].click()
            print("[BasePage] iOS back via nav-bar button")
            return
        # Edge swipe from left edge → right (iOS interactive pop gesture)
        try:
            size = self.driver.get_window_size()
            y = int(size["height"] * 0.5)
            finger = PointerInput(interaction.POINTER_TOUCH, "finger")
            actions = ActionBuilder(self.driver, mouse=finger)
            actions.pointer_action.move_to_location(2, y).pointer_down()
            actions.pointer_action.pause(0.2).move_to_location(int(size["width"] * 0.85), y).pointer_up()
            actions.perform()
            print("[BasePage] iOS back via edge-swipe")
        except WebDriverException:
            try:
                self.driver.back()
            except WebDriverException:
                pass

    def swipe_up(self):
        size = self.driver.get_window_size()
        x = size["width"] // 2
        start_y = int(size["height"] * 0.7)
        end_y = int(size["height"] * 0.3)
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        actions = ActionBuilder(self.driver, mouse=finger)
        actions.pointer_action.move_to_location(x, start_y).pointer_down()
        actions.pointer_action.pause(0.3).move_to_location(x, end_y).pointer_up()
        actions.perform()

    def swipe_down(self):
        """Swipe top-to-bottom — scrolls a list UP toward its top."""
        size = self.driver.get_window_size()
        x = size["width"] // 2
        start_y = int(size["height"] * 0.35)
        end_y = int(size["height"] * 0.75)
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        actions = ActionBuilder(self.driver, mouse=finger)
        actions.pointer_action.move_to_location(x, start_y).pointer_down()
        actions.pointer_action.pause(0.3).move_to_location(x, end_y).pointer_up()
        actions.perform()

    def swipe_left(self):
        """Swipe horizontally right-to-left to advance a carousel to the next screen."""
        size = self.driver.get_window_size()
        y = size["height"] // 2
        start_x = int(size["width"] * 0.85)
        end_x = int(size["width"] * 0.15)
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        actions = ActionBuilder(self.driver, mouse=finger)
        actions.pointer_action.move_to_location(start_x, y).pointer_down()
        actions.pointer_action.pause(0.3).move_to_location(end_x, y).pointer_up()
        actions.perform()

    def scroll_to_text(self, text, max_swipes=6):
        for _ in range(max_swipes):
            if self.is_text_visible(text, timeout=1):
                return
            self.swipe_up()
        print(f"[BasePage] scroll_to_text: '{text}' not found after {max_swipes} swipes")

    # ─── Screenshot ────────────────────────────────────────────────────────

    def screenshot_bytes(self):
        try:
            return self.driver.get_screenshot_as_png()
        except WebDriverException as e:
            print(f"[BasePage] screenshot failed: {e}")
            return b""


class NoSuchElementError(Exception):
    pass
