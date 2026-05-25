"""
Time Off page object.

UzioMobile (src/screens/TimeOffSceens/TimeOffHome.tsx):
  heading "Time Off"; tabs "Available" / "Upcoming";
  primary button "Request Time Off"; "Holiday Calendar", "Team Time Off";
  empty state "No Policy Assigned".
"""

from core.base_page import BasePage
from core.locators import TimeOff


class TimeOffPage(BasePage):

    def verify_on_time_off(self):
        self.verify_visible(TimeOff.HEADING)

    def tap_request_time_off(self):
        self.tap(TimeOff.REQUEST_TIME_OFF)

    def open_holiday_calendar(self):
        self.tap(TimeOff.HOLIDAY_CALENDAR)

    def open_team_time_off(self):
        self.tap(TimeOff.TEAM_TIME_OFF)

    def has_no_policy(self):
        return self.is_text_visible(TimeOff.NO_POLICY, 3)
