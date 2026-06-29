"""
Fixtures for PHIX-98315 — Time Entries: Add Hours on No Show shift.

Test data assumed (created manually on TA env on 2026-06-26):
  EE "Virat Mobile1 Sr." (mobile1@t.com) has multiple unclocked scheduled
  shifts on TODAY that will surface as No Show on the mobile app's
  Time Entries day view:
    - 04:00-07:30  USB01-USB1   ← pre-10AM start (covers EC-1 / AC-4)
    - 08:00-08:30                ← second No Show on same day (covers AC-3)
    - 08:30-09:30                ← third No Show on same day

Test posture
────────────
The user runs this against a real device with the UZIO app ALREADY INSTALLED.
The session uses noReset=True via the root driver factory's normal path. If
the app is already at the dashboard we keep that state; if at login we log in
as the EE (mobile1@t.com) using the configured `qa` credentials block.
"""

import pytest

from core.config_loader import config
from core.locators import BottomNav, Drawer
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


def _login_as_ee_if_needed(driver):
    """If we're not already on the dashboard, log in as the No Show EE."""
    dash = DashboardPage(driver)
    if any(dash.is_text_visible(t, 3) for t in dash.LANDING_INDICATORS):
        print("[phix-98315] Dashboard already up — skipping login")
        dash.dismiss_blocking_dialogs()
        return
    username = config.credential("ee_manual_username") or "mobile1@t.com"
    password = config.credential("ee_manual_password")
    if not password:
        raise RuntimeError(
            "[phix-98315] Missing ee_manual_password in secrets.yaml (env=qa). "
            "Set credentials.qa.ee_manual_password to mobile1@t.com's password."
        )
    print(f"[phix-98315] Logging in as {username} (No Show EE)")
    LoginPage(driver).login(username=username, password=password)


@pytest.fixture(scope="class", autouse=True)
def ee_on_dashboard(driver):
    """Class-scoped: ensure mobile1@t.com is logged in and on the dashboard."""
    _login_as_ee_if_needed(driver)
    yield


@pytest.fixture
def on_time_entries_today_with_no_show(driver):
    """
    Navigate to My Timesheet → Time Entries day view for TODAY.

    Today (2026-06-26) is expected to have multiple No Show shifts on
    mobile1@t.com (Virat Mobile1 Sr.), per the test data set up on TA env.
    The fixture yields the open day-view page object; cleanup presses back.
    """
    from pages.time_entries_page import TimeEntriesDayPage

    dash = DashboardPage(driver)
    dash.open_drawer_and_tap(Drawer.MY_TIMESHEET, verify_any=["My Timesheet"])
    # Tap today's date chip — the day strip typically defaults to today; if not,
    # the EE will need to swipe. We try a few common labels first.
    page = TimeEntriesDayPage(driver)
    # The day view should already be reachable from My Timesheet by tapping
    # any date chip. The user's setup placed No Shows on TODAY so the default
    # day-strip selection should land us on a date with No Show cards.
    if not page.is_no_show_visible(timeout=5):
        # Try tapping "Today" if the chip exists, otherwise the first date chip.
        for label in ("Today", "TODAY"):
            if page.is_text_visible(label, 1):
                page.tap(label)
                break
    page.verify_loaded(timeout=15)
    yield page
    try:
        page.press_back()
    except Exception as e:
        print(f"[phix-98315] press_back during teardown skipped: {e}")
