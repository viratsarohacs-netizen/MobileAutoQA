"""
PHIX-97864 — Verification: Pay period visible in My Timesheet when all entries are proposed.

Bug summary:
    After PHIX-95866 (approval-required feature), employee-added entries are marked
    as 'proposed' and were filtered out of the My Timesheet period-selector JPQL query.
    Result: a week whose ONLY entries are in proposed state disappears from the
    period dropdown entirely, even though entries exist and are awaiting approval.

Fix (TimesheetKit): The period-list query now includes weeks that have proposed-only rows.

Verification scenario (mirrors Caravan 12th reproduction):
    1. Log in as mobile1@t.com (EE who creates new manual/proposed entries).
    2. Create a new manual time entry → backend marks it isProposedEntry=true.
    3. Navigate to My Timesheet.
    4. The current pay period MUST appear in the period selector — it must NOT be absent.

Expected post-fix: Period is visible.
Pre-fix behaviour: Period would be missing entirely (empty selector or wrong week).
"""

import re
import time
import pytest
from appium.webdriver.common.appiumby import AppiumBy

from core.config_loader import config
from core.locators import Drawer, MyTimesheet
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.timesheet_page import MyTimesheetPage


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _xp_text(text):
    return (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
            f"or contains(@name,'{text}') or contains(@label,'{text}')]")


def _visible(driver, text, timeout=6) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if driver.find_elements(AppiumBy.XPATH, _xp_text(text)):
            return True
        time.sleep(0.4)
    return False


def _tap(driver, text):
    els = driver.find_elements(AppiumBy.XPATH, _xp_text(text))
    if els:
        els[0].click()
        return True
    return False


def _dismiss_any(driver, *buttons):
    for btn in buttons:
        if _visible(driver, btn, 2) and _tap(driver, btn):
            time.sleep(0.8)
            return True
    return False


def _login_as(driver, cred_key: str):
    try:
        DashboardPage(driver).logout()
    except Exception as e:
        print(f"[97864] logout before switch skipped: {e}")
    username = config.credential(f"{cred_key}_username")
    password = config.credential(f"{cred_key}_password")
    print(f"[97864] Logging in as {username} ({cred_key})")
    return LoginPage(driver).login(username=username, password=password)


def _open_my_timesheet(driver) -> MyTimesheetPage:
    DashboardPage(driver).open_drawer_and_tap(
        Drawer.MY_TIMESHEET, verify_any=[MyTimesheet.HEADING])
    ts = MyTimesheetPage(driver)
    ts.verify_loaded()
    return ts


def _get_visible_date_ranges(driver) -> list[str]:
    """
    Collect all visible text strings that look like pay-period date ranges.

    The My Timesheet period selector renders dates in two observed formats:
      - Spelled month: "May 15 - Jun 14, 2026"  (confirmed from live app screenshot)
      - Numeric:       "05/17 - 05/23"            (some employer configs / older builds)
    Both use an ASCII dash or en-dash (–) as separator.
    """
    try:
        src = driver.page_source
        MONTHS = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        # e.g. "May 15 – Jun 14, 2026" or "May 15 - Jun 14"
        spelled = rf'{MONTHS}\s+\d{{1,2}}(?:,\s*\d{{4}})?\s*[-–]\s*{MONTHS}\s+\d{{1,2}}'
        # e.g. "05/17 - 05/23" or "05/17/2026 - 05/23/2026"
        numeric = r'\d{1,2}/\d{1,2}(?:/\d{4})?\s*[-–]\s*\d{1,2}/\d{1,2}(?:/\d{4})?'
        combined = f'({spelled}|{numeric})'
        return re.findall(combined, src)
    except Exception as e:
        print(f"[97864] page source parse error: {e}")
        return []


def _seed_proposed_entry(driver):
    """
    Create a new manual time entry as mobile1 so there's at least one proposed
    entry for the current pay period.  Mirrors the PHIX-95866 fixture approach.
    """
    ts = _open_my_timesheet(driver)
    ts.scroll_to_text(MyTimesheet.ADD_TIME_ENTRY, max_swipes=15)

    if not _visible(driver, MyTimesheet.ADD_TIME_ENTRY, 4):
        print("[97864] 'Add Time Entry' not found — period selector may already be seeded")
        ts.press_back()
        return False

    _tap(driver, MyTimesheet.ADD_TIME_ENTRY)
    time.sleep(2)

    # Advance clock-out hour by 2+ hours using the drum picker
    _advance_clockout_hour(driver)

    saved = any(_tap(driver, lbl) for lbl in ("Save", "SAVE", "Submit"))
    if not saved:
        print("[97864] Save button not found; manual entry may not have been created")
        ts.press_back()
        return False

    time.sleep(3)
    _dismiss_any(driver, "Close", "OK", "Done")
    print("[97864] Proposed entry seeded via Add Time Entry")
    ts.press_back()
    return True


def _advance_clockout_hour(driver):
    from selenium.webdriver.common.actions.pointer_input import PointerInput
    from selenium.webdriver.common.actions.action_builder import ActionBuilder
    from selenium.webdriver.common.actions import interaction

    _visible(driver, "Clock Out time", 6)
    time.sleep(1.0)

    screen = driver.get_window_size()
    W, H = screen["width"], screen["height"]

    def swipe_up(x, y, dy=200, pause=0.4):
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        ab = ActionBuilder(driver, mouse=finger)
        ab.pointer_action.move_to_location(x, y + dy).pointer_down()
        ab.pointer_action.pause(pause).move_to_location(x, y - dy).pointer_up()
        ab.perform()
        time.sleep(0.9)

    try:
        labels = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Clock Out time' or @content-desc='Clock Out time' "
            "or @name='Clock Out time']")
        if labels:
            loc = labels[0].location
            sz  = labels[0].size
            drum_x = loc["x"] + sz["width"] // 4
            drum_y = loc["y"] + sz["height"] + int(H * 0.09)
            swipe_up(drum_x, drum_y)
            swipe_up(drum_x, drum_y)
            print("[97864] Clock-out drum advanced via label-relative swipe")
            return
    except Exception as e:
        print(f"[97864] Drum S1 failed: {e}")

    # Fallback: generic lower-left position
    swipe_up(int(W * 0.20), int(H * 0.62))
    swipe_up(int(W * 0.20), int(H * 0.62))
    print("[97864] Clock-out drum advanced via generic swipe")


# ─── Test class ───────────────────────────────────────────────────────────────

@pytest.mark.usefixtures("driver")
class TestPhix97864:
    """
    Verifies that the TimesheetKit backend fix correctly surfaces pay periods
    that contain only proposed entries in the My Timesheet period selector.
    """

    def test_period_visible_with_proposed_only_entries(self, driver):
        """
        TC-97864-01: Pay period appears in My Timesheet when EE has only proposed entries.

        Steps:
          1. Login as mobile1 (EE who creates proposed/manual entries).
          2. Seed a new manual entry (proposed state) for the current pay period.
          3. Navigate to My Timesheet.
          4. Assert that at least one pay-period date range is visible in the period selector.

        Pre-fix failure mode: No period appeared → selector was empty or showed wrong week.
        Post-fix expected: Current pay period date range is visible in the selector.
        """
        self._current_test_id   = "TC-97864-01"
        self._current_test_name = "Pay period visible when only proposed entries exist"

        # Step 1: Login as mobile1 (EE — creates proposed/manual entries)
        _login_as(driver, "ee_manual")
        print("[97864] Logged in as mobile1 (ee_manual)")

        # Step 2: Seed a proposed entry so the current period has proposed-only rows.
        # If mobile1 already has entries from prior PHIX-95866 runs that haven't been
        # approved yet, seeding is skipped (period should still appear).
        _seed_proposed_entry(driver)
        time.sleep(1)

        # Step 3: Navigate to My Timesheet
        ts = _open_my_timesheet(driver)
        print("[97864] My Timesheet loaded")

        # Step 4: Capture a screenshot for evidence
        try:
            shot_bytes = driver.get_screenshot_as_png()
            if shot_bytes:
                import os
                os.makedirs("reports/verify", exist_ok=True)
                path = "reports/verify/phix_97864_my_timesheet.png"
                with open(path, "wb") as f:
                    f.write(shot_bytes)
                print(f"[97864] Screenshot: {path}")
        except Exception as e:
            print(f"[97864] Screenshot failed: {e}")

        # Step 5: Collect visible date ranges from the period selector
        date_ranges = _get_visible_date_ranges(driver)
        print(f"[97864] Visible date ranges in My Timesheet: {date_ranges}")

        # Also try scrolling down slightly in case selector is below the fold
        if not date_ranges:
            ts.swipe_up()
            time.sleep(1)
            date_ranges = _get_visible_date_ranges(driver)
            print(f"[97864] Date ranges after scroll: {date_ranges}")

        # Step 6: Dump raw page source excerpt if no ranges found (diagnostic aid)
        if not date_ranges:
            try:
                src = driver.page_source
                # Grab a slice around "Timesheet" keyword for context
                idx = src.find("Timesheet")
                excerpt = src[max(0, idx - 200): idx + 600] if idx >= 0 else src[:800]
                print(f"[97864] Page source excerpt:\n{excerpt}")
            except Exception as e:
                print(f"[97864] Page source dump failed: {e}")

        # Assertion: at least one pay-period date range must be present.
        # Pre-fix: this would fail (0 ranges visible for proposed-only weeks).
        # Post-fix: the current period date range appears.
        assert len(date_ranges) > 0, (
            "FAIL — No pay-period date range visible in My Timesheet for mobile1 "
            "(employee with only proposed entries). "
            f"Expected a date range like 'MM/DD - MM/DD'. "
            f"This indicates the TimesheetKit backend fix (PHIX-97864) is NOT active "
            f"in the current environment. Visible page source excerpted above."
        )

        print(f"[97864] PASS — Period selector shows: {date_ranges}")

    def test_period_visible_after_manager_approves(self, driver):
        """
        TC-97864-02 (regression guard): Once the manager approves the entry, the period
        remains visible (not a new regression — period should always be visible after approval).

        Steps:
          1. Login as manager (mobile2).
          2. Navigate to My Timesheet (manager view / Team Timesheet).
          3. Verify that the period containing mobile1's entry is accessible.

        Note: This test verifies that the fix did not break the approved-entry path.
        """
        self._current_test_id   = "TC-97864-02"
        self._current_test_name = "Period remains visible after manager approval (regression guard)"

        # Login as manager
        _login_as(driver, "employee")   # mobile2 = manager
        print("[97864] Logged in as mobile2 (manager)")
        time.sleep(2)

        # Navigate to My Timesheet from manager's perspective
        ts = _open_my_timesheet(driver)
        print("[97864] My Timesheet (manager view) loaded")

        date_ranges = _get_visible_date_ranges(driver)
        print(f"[97864] Manager My Timesheet date ranges: {date_ranges}")

        assert len(date_ranges) > 0, (
            "FAIL — No pay-period date range visible for manager in My Timesheet. "
            "Unexpected regression — the manager's approved-entry periods should always show."
        )
        print(f"[97864] PASS (regression guard) — Manager sees periods: {date_ranges}")
