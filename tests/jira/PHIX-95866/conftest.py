"""
Test data fixtures for PHIX-95866.

Account roles (QA environment)
──────────────────────────────
  mobile2@t.com  (employee_username / employee_password)
      → MANAGER (ER) — approves / rejects entries.  Default login from root conftest.

  mobile1@t.com  (ee_manual_username / ee_manual_password)
      → EE for NEW MANUAL ENTRY cases.
        Creates isProposedEntry=true CRs via "Add Time Entry".
        Reject modal shows: "Rejecting this entry will permanently delete this time entry."

  mobile3@t.com  (ee_modify_username / ee_modify_password)
      → EE for MODIFICATION cases.
        Creates isProposedEntry=false + changeRequestIdentifier CRs by editing.
        Reject modal shows: "If rejected, the modifications will be discarded…"

Fixture catalogue
─────────────────
  pending_new_entry      Manager stays logged in; mobile1 CR visible on My Timesheet.
  pending_modification   Manager stays logged in; mobile3 CR visible on My Timesheet.
  ee_with_new_entry      Driver left as mobile1 (EE perspective for new-entry tests).
  ee_with_modification   Driver left as mobile3, clocked in (EE perspective / clock-out block).

All "destructive" tests (accept / reject consume the entry) declare their own
fixture so a fresh CR is created for each test.
"""

import time
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from core.config_loader import config
from core.locators import Drawer, MyTimesheet, TimeTracking
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.time_tracking_page import TimeTrackingPage
from pages.timesheet_page import MyTimesheetPage


# ─── Low-level helpers (no page-object dependency) ───────────────────────────

def _xp_text(text):
    return (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
            f"or contains(@name,'{text}') or contains(@label,'{text}')]")


def _visible(driver, text, timeout=5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if driver.find_elements(AppiumBy.XPATH, _xp_text(text)):
            return True
        time.sleep(0.4)
    return False


def _tap(driver, text) -> bool:
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


# ─── Account switching ────────────────────────────────────────────────────────

def _login_as(driver, cred_key: str):
    """
    Logout the current user and login with credentials identified by cred_key.
    cred_key examples: 'employee', 'ee_manual', 'ee_modify'
    Looks up {cred_key}_username and {cred_key}_password from config.
    """
    try:
        DashboardPage(driver).logout()
    except Exception as e:
        print(f"[phix-95866] logout before switch skipped: {e}")

    username = config.credential(f"{cred_key}_username")
    password = config.credential(f"{cred_key}_password")
    if not username or not password:
        raise RuntimeError(
            f"[phix-95866] Credentials for '{cred_key}' not configured "
            f"(env={config.environment}). Set {cred_key}_username / {cred_key}_password."
        )
    print(f"[phix-95866] Logging in as {username} ({cred_key})")
    return LoginPage(driver).login(username=username, password=password)


def _back_to_manager(driver):
    _login_as(driver, "employee")
    print("[phix-95866] Back to manager (mobile2@t.com)")


# ─── CR creation helpers ──────────────────────────────────────────────────────

def _open_my_timesheet(driver) -> MyTimesheetPage:
    DashboardPage(driver).open_drawer_and_tap(
        Drawer.MY_TIMESHEET, verify_any=[MyTimesheet.HEADING])
    ts = MyTimesheetPage(driver)
    ts.verify_loaded()
    return ts


def _has_pending_card(driver) -> bool:
    return _visible(driver, MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, 5)


# ── New manual entry (mobile1) ────────────────────────────────────────────────

def _create_new_manual_entry(driver):
    """
    mobile1 (EE) adds a brand-new manual time entry via Add Time Entry.

    The Add Time Entry form defaults both clock-in and clock-out to moment()
    (current time).  We must advance clock-out by ≥1 hour or the
    clockInBeforeClockOut validator rejects the save.

    Strategy: tap Add Time Entry → advance clock-out hour drum via swipe-up
    on the hour column → Save.
    """
    ts = _open_my_timesheet(driver)

    # Add Time Entry appears at the bottom of the timesheet list. After multiple test
    # runs the QA account accumulates entries, making the list long. Scroll down
    # aggressively (swipe up × 15) before giving up.
    ts.scroll_to_text(MyTimesheet.ADD_TIME_ENTRY, max_swipes=15)

    if not _visible(driver, MyTimesheet.ADD_TIME_ENTRY, 4):
        # Dump page source for diagnostics so we can see what's on screen
        try:
            import os
            os.makedirs('.tmp', exist_ok=True)
            with open('.tmp/mytimesheet_ps_mobile1.xml', 'w', encoding='utf-8', errors='replace') as f:
                f.write(driver.page_source)
            print("[phix-95866] Dumped My Timesheet page source to .tmp/mytimesheet_ps_mobile1.xml")
        except Exception as dump_err:
            print(f"[phix-95866] Page source dump failed: {dump_err}")
        raise RuntimeError("[phix-95866] 'Add Time Entry' button not found after 15 swipes")

    _tap(driver, MyTimesheet.ADD_TIME_ENTRY)
    time.sleep(2)   # wait for form animation

    _advance_hour_on_clockout_drum(driver)

    # Tap Save
    saved = any(_tap(driver, lbl) for lbl in ("Save", "SAVE", "Submit"))
    if not saved:
        raise RuntimeError("[phix-95866] Save button not found in Add Time Entry form")
    time.sleep(3)
    _dismiss_any(driver, "Close", "OK", "Done")

    # Scroll back to top and verify the pending card appeared
    for _ in range(4):
        ts.swipe_down()
    if not _visible(driver, MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, 8):
        raise RuntimeError(
            "[phix-95866] New entry CR card not visible after Add Time Entry save. "
            "The form may have failed validation (equal clock-in/clock-out times)."
        )
    print("[phix-95866] New manual entry CR created (mobile1)")
    ts.press_back()


def _advance_hour_on_clockout_drum(driver):
    """
    In the Add/Edit Time Entry form, swipe the Clock Out hour drum upward
    by 2+ hours so clock-out > clock-in.

    Three strategies in order. Each performs 2 swipes of 200px (dy=200, pause=0.4s)
    to ensure the drum advances enough even on high-DPI BrowserStack devices.
    """
    _visible(driver, "Clock Out time", 6)
    time.sleep(1.0)   # extra wait for form animation to complete on slow cloud devices

    from selenium.webdriver.common.actions.pointer_input import PointerInput
    from selenium.webdriver.common.actions.action_builder import ActionBuilder
    from selenium.webdriver.common.actions import interaction

    def swipe_drum_up(x, y, dy=200, pause=0.4):
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        ab = ActionBuilder(driver, mouse=finger)
        ab.pointer_action.move_to_location(x, y + dy).pointer_down()
        ab.pointer_action.pause(pause).move_to_location(x, y - dy).pointer_up()
        ab.perform()
        time.sleep(0.9)

    screen = driver.get_window_size()
    W, H = screen["width"], screen["height"]

    # Strategy 1: locate "Clock Out time" label, derive drum position from it
    try:
        labels = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Clock Out time' or @content-desc='Clock Out time' "
            "or @name='Clock Out time']")
        if labels:
            loc = labels[0].location
            sz  = labels[0].size
            drum_x = loc["x"] + sz["width"] // 4      # left quarter = hour drum
            drum_y = loc["y"] + sz["height"] + int(H * 0.09)
            swipe_drum_up(drum_x, drum_y)
            swipe_drum_up(drum_x, drum_y)   # second swipe — ensures ≥2 h advancement
            print("[phix-95866] Drum S1 (label-relative, 2× swipe): hour +2")
            return
    except Exception as e:
        print(f"[phix-95866] Drum S1 failed: {e}")

    # Strategy 2: page-source search for bounds of "Clock Out time" label
    try:
        src = driver.page_source
        idx = src.find("Clock Out time")
        if idx > 0:
            chunk = src[max(0, idx - 200): idx + 200]
            import re
            bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', chunk)
            if bounds:
                x1, y1, x2, y2 = (int(v) for v in bounds.groups())
                cx = x1 + (x2 - x1) // 4
                cy = y2 + int(H * 0.09)
                swipe_drum_up(cx, cy)
                swipe_drum_up(cx, cy)
                print("[phix-95866] Drum S2 (bounds from source, 2× swipe): hour +2")
                return
    except Exception as e:
        print(f"[phix-95866] Drum S2 failed: {e}")

    # Strategy 3: generic lower-left coordinates (hour drum typical position)
    try:
        drum_x = int(W * 0.20)
        drum_y = int(H * 0.62)
        swipe_drum_up(drum_x, drum_y)
        swipe_drum_up(drum_x, drum_y)
        swipe_drum_up(drum_x, drum_y)   # 3× for safety
        print("[phix-95866] Drum S3 (generic, 3× swipe): hour +3 attempt")
    except Exception as e:
        print(f"[phix-95866] Drum S3 failed: {e}")
        raise RuntimeError(f"[phix-95866] All hour drum swipe strategies failed: {e}")


# ── Modification CR (mobile3) ─────────────────────────────────────────────────

def _create_modification_cr(driver):
    """
    mobile3 (EE):
      1. Clock in → clock out  →  creates a real attendance entry.
      2. Go to My Timesheet → Edit that entry.
      3. Swipe the clock-out minute drum +1  →  a change is detected.
      4. Save  →  modification CR (isProposedEntry=false + changeRequestIdentifier).
    """
    dash = DashboardPage(driver)

    # Seed a real attendance record
    tt = dash.open_time_tracking()
    tt.ensure_clocked_out()
    tt.clock_in()
    tt.wait_for_clocked_in(90)
    time.sleep(6)       # entry needs non-zero duration
    tt.clock_out()
    tt.wait_for_clocked_out(60)
    print("[phix-95866] mobile3 clocked in → out, real entry seeded")

    # Open My Timesheet and find Edit on the freshest entry.
    # Scroll down up to 15× — QA account accumulates entries across runs.
    ts = _open_my_timesheet(driver)
    ts.scroll_to_text(MyTimesheet.EDIT_TIME_ENTRY, max_swipes=15)

    if not _visible(driver, MyTimesheet.EDIT_TIME_ENTRY, 4):
        raise RuntimeError("[phix-95866] 'Edit Time Entry' not found on My Timesheet after clock-out")

    _tap(driver, MyTimesheet.EDIT_TIME_ENTRY)
    time.sleep(2)

    _advance_minute_on_clockout_drum(driver)

    saved = any(_tap(driver, lbl) for lbl in ("Save", "SAVE"))
    if not saved:
        raise RuntimeError("[phix-95866] Save button not found in Edit Time Entry form")
    time.sleep(3)
    _dismiss_any(driver, "Close", "OK", "Done")

    for _ in range(4):
        ts.swipe_down()
    if not _visible(driver, MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, 8):
        raise RuntimeError(
            "[phix-95866] Modification CR card not visible after edit save. "
            "The form may not have detected a change (minute drum swipe may have missed)."
        )
    print("[phix-95866] Modification CR created (mobile3)")
    ts.press_back()


def _advance_minute_on_clockout_drum(driver):
    """Advance the Clock Out minute drum by +1 in the Edit Time Entry form."""
    _visible(driver, "Clock Out time", 6)
    time.sleep(1.0)

    from selenium.webdriver.common.actions.pointer_input import PointerInput
    from selenium.webdriver.common.actions.action_builder import ActionBuilder
    from selenium.webdriver.common.actions import interaction

    def swipe_drum_up(x, y, dy=200, pause=0.4):
        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        ab = ActionBuilder(driver, mouse=finger)
        ab.pointer_action.move_to_location(x, y + dy).pointer_down()
        ab.pointer_action.pause(pause).move_to_location(x, y - dy).pointer_up()
        ab.perform()
        time.sleep(0.9)

    screen = driver.get_window_size()
    W, H = screen["width"], screen["height"]

    try:
        labels = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Clock Out time' or @content-desc='Clock Out time' "
            "or @name='Clock Out time']")
        if labels:
            loc = labels[0].location
            sz  = labels[0].size
            drum_x = loc["x"] + int(sz["width"] * 0.42)   # center column = minute drum
            drum_y = loc["y"] + sz["height"] + int(H * 0.09)
            swipe_drum_up(drum_x, drum_y)
            swipe_drum_up(drum_x, drum_y)   # 2× to ensure change is detected
            print("[phix-95866] Minute drum S1 (label-relative, 2×): +2 min")
            return
    except Exception as e:
        print(f"[phix-95866] Minute drum S1 failed: {e}")

    try:
        drum_x = int(W * 0.40)
        drum_y = int(H * 0.62)
        swipe_drum_up(drum_x, drum_y)
        swipe_drum_up(drum_x, drum_y)
        print("[phix-95866] Minute drum S2 (generic, 2×): +2 min")
    except Exception as e:
        print(f"[phix-95866] Minute drum S2 failed: {e}")
        raise RuntimeError(f"[phix-95866] All minute drum swipe strategies failed: {e}")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def pending_new_entry(driver):
    """
    Ensures a NEW MANUAL ENTRY CR is visible on My Timesheet for the manager.
    mobile1@t.com adds the entry; manager (mobile2) is restored for the test.
    """
    dash = DashboardPage(driver)
    try:
        dash.recover_to_dashboard()
    except Exception as e:
        print(f"[phix-95866] WARNING recover_to_dashboard at fixture start: {e}")

    # Skip creation if card already present (e.g., previous test did not consume it)
    try:
        dash.open_drawer_and_tap(Drawer.MY_TIMESHEET, verify_any=[MyTimesheet.HEADING])
        already = _has_pending_card(driver)
        MyTimesheetPage(driver).press_back()
    except Exception:
        already = False

    if not already:
        print("[phix-95866] pending_new_entry: no card found — creating via mobile1")
        try:
            _login_as(driver, "ee_manual")
            _create_new_manual_entry(driver)
        except Exception as e:
            print(f"[phix-95866] WARNING pending_new_entry creation failed: {e}")
        try:
            _back_to_manager(driver)
        except Exception as e:
            print(f"[phix-95866] WARNING manager restore failed: {e}")
    else:
        print("[phix-95866] pending_new_entry: card already present, skipping creation")

    yield

    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def pending_modification(driver):
    """
    Ensures a MODIFICATION CR is visible on My Timesheet for the manager.
    mobile3@t.com creates the CR; manager (mobile2) is restored for the test.
    """
    dash = DashboardPage(driver)
    try:
        dash.recover_to_dashboard()
    except Exception as e:
        print(f"[phix-95866] WARNING recover_to_dashboard at fixture start: {e}")

    try:
        dash.open_drawer_and_tap(Drawer.MY_TIMESHEET, verify_any=[MyTimesheet.HEADING])
        already = _has_pending_card(driver)
        MyTimesheetPage(driver).press_back()
    except Exception:
        already = False

    if not already:
        print("[phix-95866] pending_modification: no card found — creating via mobile3")
        try:
            _login_as(driver, "ee_modify")
            _create_modification_cr(driver)
        except Exception as e:
            print(f"[phix-95866] WARNING pending_modification creation failed: {e}")
        try:
            _back_to_manager(driver)
        except Exception as e:
            print(f"[phix-95866] WARNING manager restore failed: {e}")
    else:
        print("[phix-95866] pending_modification: card already present, skipping creation")

    yield

    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def ee_with_new_entry(driver):
    """
    Driver stays as mobile1 (EE) with a fresh new-entry CR pending.
    Used for TC-13/14/15 (EE perspective: Cancel Request, Awaiting acceptance).
    Teardown: switch back to manager.
    """
    print("[phix-95866] ee_with_new_entry: logging in as mobile1 and creating new entry")
    try:
        _login_as(driver, "ee_manual")
        _create_new_manual_entry(driver)
    except Exception as e:
        print(f"[phix-95866] WARNING ee_with_new_entry setup failed: {e}")

    yield   # test runs as mobile1 (EE)

    try:
        _back_to_manager(driver)
    except Exception:
        pass
    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def ee_with_modification(driver):
    """
    Driver stays as mobile3 (EE) — clocked IN with a modification CR pending.
    Used for TC-16 (clock-out blocked) and TC-17 (add-time blocked).
    Teardown: clock out if still in, switch back to manager.
    """
    print("[phix-95866] ee_with_modification: logging in as mobile3, clocking in + creating CR")
    try:
        _login_as(driver, "ee_modify")

        dash = DashboardPage(driver)
        tt   = dash.open_time_tracking()
        tt.ensure_clocked_out()
        tt.clock_in()
        tt.wait_for_clocked_in(90)
        time.sleep(6)

        # Add a new manual entry for a different window (past slot) while clocked in
        # This creates a pending CR without interfering with the active clock-in session
        ts = _open_my_timesheet(driver)
        for _ in range(4):
            if _visible(driver, MyTimesheet.ADD_TIME_ENTRY, 2):
                break
            ts.swipe_up()
        if _visible(driver, MyTimesheet.ADD_TIME_ENTRY, 3):
            _tap(driver, MyTimesheet.ADD_TIME_ENTRY)
            time.sleep(2)
            _advance_hour_on_clockout_drum(driver)
            any(_tap(driver, lbl) for lbl in ("Save", "SAVE"))
            time.sleep(3)
            _dismiss_any(driver, "Close", "OK")
        ts.press_back()

        # Return to Time Tracking (where TC-16 will tap Clock Out)
        dash.open_time_tracking()

    except Exception as e:
        print(f"[phix-95866] WARNING ee_with_modification setup failed: {e}")

    yield   # test runs as mobile3 (EE), clocked in

    # Teardown: clock out if still in, then back to manager
    try:
        tt2 = TimeTrackingPage(driver)
        if tt2.is_clock_out_button_visible():
            tt2.tap("Clock Out")
            _dismiss_any(driver, "Close", "OK", "Yes")
    except Exception:
        pass
    try:
        _back_to_manager(driver)
    except Exception:
        pass
    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def ee_manual_after_action(driver):
    """
    Yields the driver logged in as mobile1 (EE) so tests can verify
    what EE sees after the manager has acted on their entry (accepted/rejected).
    The fixture itself does NOT create a CR — caller is responsible for that
    (via pending_new_entry earlier in the same test, or pre-existing data).
    Teardown: switch back to manager.
    """
    try:
        _login_as(driver, "ee_manual")
    except Exception as e:
        print(f"[phix-95866] WARNING ee_manual_after_action login failed: {e}")

    yield

    try:
        _back_to_manager(driver)
    except Exception:
        pass
    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def ee_modify_after_action(driver):
    """
    Same as ee_manual_after_action but for mobile3 (EE modification account).
    """
    try:
        _login_as(driver, "ee_modify")
    except Exception as e:
        print(f"[phix-95866] WARNING ee_modify_after_action login failed: {e}")

    yield

    try:
        _back_to_manager(driver)
    except Exception:
        pass
    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass


@pytest.fixture(scope="function")
def ee_has_modification_cr(driver):
    """
    Driver stays as mobile3 (EE) with a fresh modification CR pending —
    but EE is NOT actively clocked in (so they can freely navigate to My Timesheet).

    Used for:
      TC-24 (EE sees Cancel Modifications link)
      TC-25 (EE cancels via Cancel Modifications — confirm dialog)
      TC-26 (EE cancels — entry no longer pending)
      TC-30 (Cancel Modifications tooltip visible)
      TC-31 (History Modifications Cancelled)

    Teardown: switch back to manager.
    """
    print("[phix-95866] ee_has_modification_cr: logging in as mobile3, creating modification CR")
    try:
        _login_as(driver, "ee_modify")
        _create_modification_cr(driver)
        # _create_modification_cr ends with ts.press_back() — we're on dashboard
    except Exception as e:
        print(f"[phix-95866] WARNING ee_has_modification_cr setup failed: {e}")

    yield   # test runs as mobile3 (EE), NOT clocked in

    try:
        _back_to_manager(driver)
    except Exception:
        pass
    try:
        DashboardPage(driver).recover_to_dashboard()
    except Exception:
        pass
