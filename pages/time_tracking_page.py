"""
Time Tracking page object.

UzioMobile (src/screens/timesheetScreens/timesheetMainScreen.tsx):
  - Buttons: "Clock In", "Clock Out", "Break Time"
  - Clocked-in sub-heading label: "Clocked In"
  - Confirmation modals: "You are Clocked In" / "You are Clocked Out" with "Close" button
  - Clock Out may trigger the attestation modal (HTTP 428) — handled via DashboardPage.
"""

import time
from core.base_page import BasePage
from core.locators import TimeTracking
from pages.dashboard_page import DashboardPage


class TimeTrackingPage(BasePage):

    def _dashboard(self):
        return DashboardPage(self.driver)

    # ─── State queries ────────────────────────────────────────────────────────

    def is_clocked_in(self):
        for ind in TimeTracking.CLOCKED_IN_INDICATORS:
            if self.is_text_visible(ind, 2):
                print(f"[TimeTracking] clocked_in=True (saw: {ind})")
                return True
        print("[TimeTracking] clocked_in=False")
        return False

    def is_clock_in_button_visible(self):
        return self.is_text_visible(TimeTracking.CLOCK_IN, 2)

    def is_clock_out_button_visible(self):
        return self.is_text_visible(TimeTracking.CLOCK_OUT, 2)

    # ─── Clock In ─────────────────────────────────────────────────────────────

    def clock_in(self):
        self.tap(TimeTracking.CLOCK_IN)
        # Confirmation modal "You are Clocked In" with a Close button appears (can
        # take a few seconds). HEALED 2026-05-23: wait longer + close it reliably so
        # it doesn't linger and block the next screen/test.
        if self.is_text_visible(TimeTracking.YOU_ARE_CLOCKED_IN, 10) or \
                self.is_text_visible(TimeTracking.MODAL_CLOSE, 2):
            self.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 3)
            print("[TimeTracking] Closed clock-in confirmation modal")
        self._dashboard().dismiss_attestation_if_present()
        print("[TimeTracking] Clock In done")

    def wait_for_clocked_in(self, timeout=90):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_clocked_in():
                return
            self._dashboard().dismiss_attestation_if_present()
            self.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 1)
            time.sleep(1)
        raise AssertionError(f"[TimeTracking] Clocked-in state not shown after {timeout}s")

    # ─── Clock Out ────────────────────────────────────────────────────────────

    def clock_out(self):
        if not self.is_clock_out_button_visible():
            print("[TimeTracking] clock_out: Clock Out not visible — likely already clocked out")
            return False
        self.tap(TimeTracking.CLOCK_OUT)
        # Attestation modal may appear (missed-break / time attestation, HTTP 428)
        self._dashboard().dismiss_attestation_if_present()
        # Confirmation modal "You are Clocked Out" with a Close button
        if self.is_text_visible(TimeTracking.YOU_ARE_CLOCKED_OUT, 10) or \
                self.is_text_visible(TimeTracking.MODAL_CLOSE, 2):
            self.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 3)
            print("[TimeTracking] Closed clock-out confirmation modal")
        print("[TimeTracking] Clock Out done")
        return True

    def wait_for_clocked_out(self, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_clock_in_button_visible():
                return
            self._dashboard().dismiss_attestation_if_present()
            self.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 1)
            time.sleep(1)
        raise AssertionError(f"[TimeTracking] Clocked-out state not shown after {timeout}s")

    # ─── Break ────────────────────────────────────────────────────────────────

    def start_break(self):
        self.tap(TimeTracking.BREAK_TIME)
        self.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 5)
        print("[TimeTracking] Break started")

    # ─── Convenience ──────────────────────────────────────────────────────────

    def ensure_clocked_out(self):
        """Reset to a clocked-out state for a clean test precondition."""
        if self.is_clock_out_button_visible():
            self.clock_out()
            self.wait_for_clocked_out(60)
