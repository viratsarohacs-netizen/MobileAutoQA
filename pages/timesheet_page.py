"""
My Timesheet and Team Timesheet page objects.

UzioMobile screens:
    src/screens/timesheetScreens/TimeSheet.tsx
    src/screens/timesheetScreens/TimeEntriesCards.tsx
    src/screens/timesheetScreens/TimeEntryHistory.tsx
    src/screens/manageTeam/TeamTimeSheet.tsx

These screens display time entry cards, including proposed/pending change-request
cards introduced by PHIX-95866. Managers (ER) see Accept/Reject buttons; employees
(EE) see Cancel Request on their own pending entries.
"""

import time
from core.base_page import BasePage
from core.locators import MyTimesheet, TimesheetHistory, TeamTimesheet


class MyTimesheetPage(BasePage):

    def verify_loaded(self):
        self.wait_for_text(MyTimesheet.HEADING, 10)

    # ─── Pending entry card detection ─────────────────────────────────────────

    def has_pending_entry(self, timeout=5):
        return self.is_text_visible(MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, timeout)

    def scroll_to_pending_entry(self, max_swipes=6):
        self.scroll_to_text(MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, max_swipes=max_swipes)

    # ─── ER actions ───────────────────────────────────────────────────────────

    def open_accept_modal(self):
        """Tap Accept on the card — opens the 'Accept employee time entry changes' modal."""
        self.tap(MyTimesheet.ACCEPT)
        self.wait_for_text(MyTimesheet.ACCEPT_MODAL_HEADING, 8)
        print("[MyTimesheet] Accept modal opened")

    def accept_entry(self):
        """
        Full accept flow:
          1. Tap Accept on the pending entry card → intermediate modal opens
             (heading: 'Accept employee time entry changes', button: 'Accept')
          2. Tap Accept inside the modal → entry accepted, card disappears
        """
        self.open_accept_modal()
        self.tap(MyTimesheet.ACCEPT)           # confirm inside the modal
        self.dismiss_popup_if_present("Close", 5)
        print("[MyTimesheet] Accepted entry")

    def open_reject_modal(self):
        self.tap(MyTimesheet.REJECT)
        self.wait_for_text(MyTimesheet.REJECT_MODAL_TITLE, 8)
        print("[MyTimesheet] Reject modal opened")

    def reject_entry(self, reason: str = "", send_email: bool = False):
        """Open the reject modal, optionally enter reason + email, then submit."""
        self.open_reject_modal()
        if reason:
            self.enter(MyTimesheet.REJECT_REASON_PLACEHOLDER, reason)
        if send_email:
            self.tap(MyTimesheet.SEND_EMAIL_NOTIFICATION)
        self.tap(MyTimesheet.REJECT)
        self.dismiss_popup_if_present("Close", 5)
        print(f"[MyTimesheet] Rejected entry (reason={reason!r}, send_email={send_email})")

    def cancel_reject_modal(self):
        self.dismiss_popup_if_present("Cancel", 3)

    # ─── EE actions ───────────────────────────────────────────────────────────

    def cancel_modification(self):
        """
        EE cancels a MODIFICATION CR via the 'Cancel Modifications' link
        visible inside the pending-modifications accordion.
        Confirms the 'Your pending changes will be discarded…' dialog.
        """
        self.scroll_to_text(MyTimesheet.CANCEL_MODIFICATIONS)
        self.tap(MyTimesheet.CANCEL_MODIFICATIONS)
        self.wait_for_text(MyTimesheet.CANCEL_CONFIRM_MESSAGE, 8)
        self.tap(MyTimesheet.CANCEL_CONFIRM_YES)
        self.dismiss_popup_if_present("Close", 5)
        print("[MyTimesheet] Cancelled pending modification")

    # ─── Add time ─────────────────────────────────────────────────────────────

    def tap_add_time_entry(self):
        self.scroll_to_text(MyTimesheet.ADD_TIME_ENTRY)
        self.tap(MyTimesheet.ADD_TIME_ENTRY)

    # ─── History helpers ──────────────────────────────────────────────────────

    def scroll_to_history_event(self, event_text: str, max_swipes=8):
        self.scroll_to_text(event_text, max_swipes=max_swipes)

    def is_history_event_visible(self, event_text: str, timeout=5):
        return self.is_text_visible(event_text, timeout)


class TeamTimesheetPage(BasePage):

    def verify_loaded(self):
        self.wait_for_text(TeamTimesheet.HEADING, 10)

    def has_pending_entry(self, timeout=5):
        return self.is_text_visible(MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, timeout)

    def scroll_to_pending_entry(self, max_swipes=6):
        self.scroll_to_text(MyTimesheet.MANUAL_ENTRY_PENDING_APPROVAL, max_swipes=max_swipes)

    def accept_entry(self):
        """Full accept flow: tap Accept on card → intermediate modal → tap Accept again."""
        self.tap(MyTimesheet.ACCEPT)
        self.wait_for_text(MyTimesheet.ACCEPT_MODAL_HEADING, 8)
        self.tap(MyTimesheet.ACCEPT)
        self.dismiss_popup_if_present("Close", 5)
        print("[TeamTimesheet] Accepted entry")

    def reject_entry(self, reason: str = "", send_email: bool = False):
        self.tap(MyTimesheet.REJECT)
        self.wait_for_text(MyTimesheet.REJECT_MODAL_TITLE, 8)
        if reason:
            self.enter(MyTimesheet.REJECT_REASON_PLACEHOLDER, reason)
        if send_email:
            self.tap(MyTimesheet.SEND_EMAIL_NOTIFICATION)
        self.tap(MyTimesheet.REJECT)
        self.dismiss_popup_if_present("Close", 5)
        print(f"[TeamTimesheet] Rejected entry (reason={reason!r})")
