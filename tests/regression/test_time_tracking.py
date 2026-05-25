"""
Time Tracking Regression Suite.

Core time-tracking flows that must pass every release. AI-generated per-ticket
tests live under tests/jira/.

Run: pytest tests/regression --suite=regression
"""

import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.regression
@pytest.mark.usefixtures("driver")
class TestTimeTrackingRegression:

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    def test_r_tt_01_clock_in_out_cycle(self):
        self._begin("R-TT-01", "Clock In → Clock Out cycle")
        dash = DashboardPage(self.driver)
        tt = dash.open_time_tracking()
        tt.ensure_clocked_out()
        tt.clock_in()
        tt.wait_for_clocked_in(90)
        tt.clock_out()
        tt.wait_for_clocked_out(60)
        self._collect(dash, tt)

    def test_r_tt_02_break_flow(self):
        self._begin("R-TT-02", "Break flow")
        dash = DashboardPage(self.driver)
        tt = dash.open_time_tracking()
        tt.ensure_clocked_out()
        tt.clock_in()
        tt.wait_for_clocked_in(90)
        tt.start_break()
        # restore
        tt.clock_out()
        tt.wait_for_clocked_out(60)
        self._collect(dash, tt)
