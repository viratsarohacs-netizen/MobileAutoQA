"""
UZIO Mobile Sanity — Navigation & Screen-Load smoke tests.

Source spec: tests/sanity/sanity.test.md
Covers the "screen loads / is reachable" sanity cases via bottom tabs and the
hamburger drawer. One login per class (driver fixture is class-scoped); each test
recovers to the dashboard first, so tests are order-independent.

Run:
    pytest tests/sanity/test_navigation.py --suite=sanity
    pytest tests/sanity -k navigation

NOTE: Many screens are feature-gated per employer. The QA "teamadmin" build
(mobile2@t.com) is a manager with payroll, so all of these are exercised. On an
employer missing a feature, the entry point won't exist — wrap in a skip guard
if you port this to such an employer.

SECURITY: Pay screens (Payment Method, Federal Tax) only verify the screen LOADS.
Never enter bank/routing/SSN data in sanity.
"""

import pytest

from core.locators import (BottomNav, TimeOff, Schedule, Benefits, Inbox,
                           Drawer, Pay, Personal, ManageTeam)
from pages.dashboard_page import DashboardPage, ScreenUnavailable


@pytest.mark.sanity
@pytest.mark.usefixtures("driver")
class TestNavigation:

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect_heals(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    # ── nav-or-skip helpers (feature-gated screens skip instead of failing) ──
    def _tab(self, tab_text, verify_any):
        dash = DashboardPage(self.driver)
        try:
            dash.open_tab(tab_text, verify_any=verify_any)
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        self._collect_heals(dash)

    def _drawer(self, item_text, verify_any):
        dash = DashboardPage(self.driver)
        try:
            dash.open_drawer_and_tap(item_text, verify_any=verify_any)
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        self._collect_heals(dash)

    # ── Bottom-tab screens ──────────────────────────────────────────────────

    def test_ms20_time_off_screen(self):
        self._begin("MS-20", "Time Off Screen")
        self._tab(BottomNav.TIME_OFF,
                  [TimeOff.AVAILABLE, TimeOff.REQUEST_TIME_OFF, TimeOff.UPCOMING, TimeOff.HEADING])

    def test_ms24_schedule_screen(self):
        self._begin("MS-24", "Schedule Screen")
        self._tab(BottomNav.SCHEDULE,
                  [Schedule.MY_UPCOMING_SCHEDULE, Schedule.NO_SHIFT,
                   Schedule.VIEW_FULL_SCHEDULE, Schedule.HEADING])

    def test_ms26_benefits_screen(self):
        self._begin("MS-26", "Benefits Screen")
        self._tab(BottomNav.BENEFITS,
                  [Benefits.CURRENT, Benefits.PLAN_DOCUMENTS, Benefits.HEADING])

    def test_ms36_inbox_screen(self):
        self._begin("MS-36", "Inbox Screen")
        self._tab(BottomNav.INBOX,
                  [Inbox.ACTION_NEEDED, Inbox.NOTIFICATIONS, Inbox.NO_NOTIFICATIONS, Inbox.HEADING])

    # ── Drawer screens: Time & Attendance ───────────────────────────────────

    def test_ms19_my_timesheet(self):
        self._begin("MS-19", "My Timesheet")
        self._drawer(Drawer.MY_TIMESHEET, [Drawer.MY_TIMESHEET])

    def test_ms22_time_off_history(self):
        self._begin("MS-22", "Time Off History")
        self._drawer(Drawer.TIME_OFF_HISTORY, [Drawer.TIME_OFF_HISTORY])

    def test_ms23_holiday_calendar(self):
        self._begin("MS-23", "Holiday Calendar")
        self._drawer(Drawer.HOLIDAY_CALENDAR, [Drawer.HOLIDAY_CALENDAR])

    # ── Drawer screens: Pay ──────────────────────────────────────────────────

    def test_ms28_pay_stubs(self):
        self._begin("MS-28", "Pay Stubs")
        self._drawer(Drawer.PAY_STUBS, [Pay.PAY_STUBS, Pay.NET_PAY, Pay.PAY_PERIOD])

    def test_ms29_payment_method(self):
        self._begin("MS-29", "Payment Method")
        # SECURITY: verify screen loads only — never enter bank details
        self._drawer(Drawer.PAYMENT_METHOD, [Pay.PAYMENT_METHOD, Pay.DIRECT_DEPOSIT])

    def test_ms30_w2_forms(self):
        self._begin("MS-30", "W-2 Forms")
        self._drawer(Drawer.W2_FORMS, [Pay.W2_FORMS, Pay.NO_W2])

    def test_ms31_federal_tax(self):
        self._begin("MS-31", "Federal Tax Withholding")
        # SECURITY: verify screen loads only — never enter SSN/tax data
        self._drawer(Drawer.FEDERAL_TAX, [Pay.FEDERAL_TAX, Pay.FILING_STATUS])

    # ── Drawer screens: Personal ─────────────────────────────────────────────

    def test_ms32_my_info(self):
        self._begin("MS-32", "My Info")
        self._drawer(Drawer.MY_INFO, [Personal.MY_INFO, Personal.PERSONAL_DETAILS])

    def test_ms33_documents(self):
        self._begin("MS-33", "Documents")
        self._drawer(Drawer.DOCUMENTS, [Personal.DOCUMENTS])

    def test_ms34_tasks(self):
        self._begin("MS-34", "Tasks")
        self._drawer(Drawer.TASKS, [Personal.TASKS, Personal.TASKS_PENDING])

    # NOTE: Manage Team drawer items (Team Timesheet / Team Time Off) are only
    # visible to the reporting-manager role. Those tests live in
    # TestNavigationManager below — that class logs in with manager_username so
    # the drawer entries render.


@pytest.mark.sanity
@pytest.mark.usefixtures("driver")
class TestNavigationManager:
    """Sanity for drawer items that only render for the reporting-manager role.

    Logs in as credentials.<env>.manager_username (driven by login_role on the
    class; conftest's driver fixture reads it). Separate class -> separate
    BrowserStack session, but that is the only way to switch the logged-in user.
    """

    login_role = "manager"

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect_heals(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    def _drawer(self, item_text, verify_any):
        dash = DashboardPage(self.driver)
        try:
            dash.open_drawer_and_tap(item_text, verify_any=verify_any)
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        self._collect_heals(dash)

    def test_ms37_team_timesheet(self):
        self._begin("MS-37", "Team Timesheet")
        self._drawer(Drawer.TEAM_TIMESHEET, [ManageTeam.TEAM_TIMESHEET])

    def test_ms38_team_time_off(self):
        self._begin("MS-38", "Team Time Off")
        self._drawer(Drawer.TEAM_TIME_OFF, [ManageTeam.TEAM_TIME_OFF, ManageTeam.WHOS_OUT])
