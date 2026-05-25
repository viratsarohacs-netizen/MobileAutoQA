"""
UZIO Mobile Sanity Suite.

Source spec: tests/sanity/sanity.test.md
Run:
    pytest tests/sanity --suite=sanity
    pytest tests/sanity -k clock_in       # single test
    MAQA_PLATFORM=ios pytest tests/sanity  # iOS run

Driver + login are provided by the `driver` fixture in conftest.py.
"""

import pytest
import allure

from core.locators import Login, BottomNav, TimeTracking
from pages.dashboard_page import DashboardPage
from pages.time_tracking_page import TimeTrackingPage


@allure.feature("Mobile Sanity — Core")
@pytest.mark.sanity
@pytest.mark.usefixtures("driver")
class TestSanity:

    # helper to tag the current test for the reporter + collect heal logs
    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []
        allure.dynamic.title(f"{test_id} · {name}")

    def _collect_heals(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    # ── MS-01: App launch + login landed ──────────────────────────────────────
    def test_ms01_app_launch_and_login(self):
        self._begin("MS-01", "App Launch & Login")
        dash = DashboardPage(self.driver)
        dash.verify_on_dashboard()
        self._collect_heals(dash)

    # ── MS-03: Bottom navigation ───────────────────────────────────────────────
    def test_ms03_bottom_navigation(self):
        self._begin("MS-03", "Bottom Navigation")
        dash = DashboardPage(self.driver)
        # Clear any OS permission dialog (e.g. location) covering the nav bar first
        dash.dismiss_blocking_dialogs()
        # Time Tracking is the default landing tab and always available with TT feature
        dash.tap(BottomNav.TIME_TRACKING)
        dash.wait_for_text(BottomNav.TIME_TRACKING, 10)
        # Time Off (if feature enabled)
        if dash.is_text_visible(BottomNav.TIME_OFF, 3):
            dash.tap(BottomNav.TIME_OFF)
        self._collect_heals(dash)

    # ── MS-04: Time Tracking screen loads ──────────────────────────────────────
    def test_ms04_time_tracking_screen(self):
        self._begin("MS-04", "Time Tracking Screen")
        dash = DashboardPage(self.driver)
        tt = dash.open_time_tracking()
        assert tt.is_clock_in_button_visible() or tt.is_clock_out_button_visible(), \
            "Neither Clock In nor Clock Out button is visible"
        self._collect_heals(dash, tt)

    # ── MS-09: Clock In ─────────────────────────────────────────────────────────
    def test_ms09_clock_in(self):
        self._begin("MS-09", "Clock In")
        dash = DashboardPage(self.driver)
        tt = dash.open_time_tracking()
        tt.ensure_clocked_out()       # clean precondition
        tt.clock_in()
        tt.wait_for_clocked_in(90)
        self._collect_heals(dash, tt)

    # ── MS-10: Clock Out (handles attestation modal) ───────────────────────────
    def test_ms10_clock_out(self):
        self._begin("MS-10", "Clock Out")
        dash = DashboardPage(self.driver)
        tt = dash.open_time_tracking()
        if not tt.is_clock_out_button_visible():
            # not clocked in — clock in first so we have something to clock out
            tt.clock_in()
            tt.wait_for_clocked_in(90)
        tt.clock_out()
        tt.wait_for_clocked_out(60)
        self._collect_heals(dash, tt)

    # ── MS-12: Logout (hamburger drawer, no confirm dialog) ────────────────────
    def test_ms12_logout(self):
        self._begin("MS-12", "Logout")
        dash = DashboardPage(self.driver)
        dash.logout()
        # Verify login screen returned
        from core.base_page import BasePage
        login_check = BasePage(self.driver)
        assert login_check.is_text_visible(Login.LOGIN_BUTTON, 15) \
            or login_check.is_text_visible(Login.USERNAME_PLACEHOLDER, 5), \
            "Login screen not shown after logout"
        self._collect_heals(dash)
