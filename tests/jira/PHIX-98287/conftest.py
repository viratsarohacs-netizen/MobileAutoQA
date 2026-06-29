"""
Fixtures for PHIX-98287 — UzioLeftBorderedRowItem right-side card clipping.

The test posture mirrors PHIX-98315: noReset session, log in as the EE if
needed, then navigate to the screen under test inside each fixture. Skipping
(not failing) when an employer doesn't have the Schedule feature enabled.

Test data on TA env / mobile1@t.com (Virat Mobile1 Sr.) — assumed:
  - The EE has at least one Available Shift in Swap Shift today/this week
  - The EE has at least one Incoming Shift Request (Offer or Swap) — optional;
    cards-not-found tests `skip` if no data.
  - The employer has PERM_FEATURE_SHIFT_AND_SCHEDULE_MODULE enabled.

If the data is missing, the affected card-overflow tests skip with a clear
message rather than failing.
"""

import pytest

from core.config_loader import config
from core.locators import BottomNav, Schedule
from pages.dashboard_page import DashboardPage, ScreenUnavailable
from pages.login_page import LoginPage
from pages.shift_schedule_page import (
    ScheduleNavigator,
    ShiftRequestsPage,
    SwapShiftPage,
)


def _login_as_ee_if_needed(driver):
    dash = DashboardPage(driver)
    if any(dash.is_text_visible(t, 3) for t in dash.LANDING_INDICATORS):
        print("[phix-98287] Dashboard already up — skipping login")
        dash.dismiss_blocking_dialogs()
        return
    username = config.credential("employee_username") or "mobile1@t.com"
    password = config.credential("employee_password")
    if not password:
        raise RuntimeError(
            "[phix-98287] Missing employee_password in secrets.yaml (env=qa). "
            "Set credentials.qa.employee_password to the EE account."
        )
    print(f"[phix-98287] Logging in as {username}")
    LoginPage(driver).login(username=username, password=password)


@pytest.fixture(scope="class", autouse=True)
def ee_on_dashboard(driver):
    """Class-scoped: ensure the EE is logged in and on the dashboard."""
    _login_as_ee_if_needed(driver)
    yield


def _skip_unless_schedule_enabled(driver):
    dash = DashboardPage(driver)
    dash.dismiss_blocking_dialogs()
    if not dash.is_text_visible(BottomNav.SCHEDULE, 3):
        pytest.skip(
            "Schedule bottom tab not available for this employer "
            "(PERM_FEATURE_SHIFT_AND_SCHEDULE_MODULE off) — PHIX-98287 "
            "regression is N/A here."
        )


@pytest.fixture
def on_shift_requests(driver):
    _skip_unless_schedule_enabled(driver)
    nav = ScheduleNavigator(driver)
    try:
        page = nav.open_shift_requests()
    except ScreenUnavailable as e:
        pytest.skip(f"Shift Requests unreachable: {e}")
    yield page
    try:
        page.press_back()
    except Exception as e:
        print(f"[phix-98287] press_back during teardown skipped: {e}")


@pytest.fixture
def on_offer_tab(on_shift_requests: ShiftRequestsPage):
    on_shift_requests.open_offer_tab()
    yield on_shift_requests


@pytest.fixture
def on_swap_tab(on_shift_requests: ShiftRequestsPage):
    on_shift_requests.open_swap_tab()
    yield on_shift_requests


@pytest.fixture
def on_swap_shift(driver):
    _skip_unless_schedule_enabled(driver)
    nav = ScheduleNavigator(driver)
    try:
        page = nav.open_swap_shift()
    except ScreenUnavailable as e:
        pytest.skip(f"Swap Shift unreachable: {e}")
    yield page
    try:
        page.press_back()
    except Exception as e:
        print(f"[phix-98287] press_back during teardown skipped: {e}")


@pytest.fixture
def on_open_shifts(driver):
    _skip_unless_schedule_enabled(driver)
    nav = ScheduleNavigator(driver)
    try:
        nav.open_simple_tile(Schedule.OPEN_SHIFTS, anchors=("No Shift",))
    except ScreenUnavailable as e:
        pytest.skip(f"Open Shifts unreachable: {e}")
    yield nav
    try:
        nav.press_back()
    except Exception:
        pass


@pytest.fixture
def on_my_shifts(driver):
    _skip_unless_schedule_enabled(driver)
    nav = ScheduleNavigator(driver)
    try:
        nav.open_simple_tile(Schedule.MY_SHIFTS, anchors=("No Shift",))
    except ScreenUnavailable as e:
        pytest.skip(f"My Shifts unreachable: {e}")
    yield nav
    try:
        nav.press_back()
    except Exception:
        pass


@pytest.fixture
def on_time_tracking_home(driver):
    dash = DashboardPage(driver)
    dash.dismiss_blocking_dialogs()
    dash.open_tab(BottomNav.TIME_TRACKING,
                  verify_any=[BottomNav.TIME_TRACKING])
    yield dash


@pytest.fixture
def on_holiday_calendar(driver):
    dash = DashboardPage(driver)
    try:
        dash.open_drawer_and_tap(
            "Holiday Calendar", verify_any=["Holiday Calendar"])
    except ScreenUnavailable as e:
        pytest.skip(f"Holiday Calendar drawer item not available: {e}")
    yield dash
    try:
        dash.press_back()
    except Exception:
        pass


@pytest.fixture
def on_time_off_completed(driver):
    dash = DashboardPage(driver)
    dash.dismiss_blocking_dialogs()
    try:
        dash.open_tab(BottomNav.TIME_OFF,
                      verify_any=[BottomNav.TIME_OFF, "Completed", "Available"])
    except ScreenUnavailable as e:
        pytest.skip(f"Time Off tab not available: {e}")
    # Some Time Off home variants show a "Completed" accordion / sub-tab.
    try:
        dash.tap("Completed")
    except Exception:
        # Not present — the test will skip if no rows render.
        pass
    yield dash
