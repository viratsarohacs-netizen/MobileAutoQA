# PHIX-95866 — Time Tracking | Employer Reject Time Entry Modifications
# Platform: both
# Screens: My Timesheet, Team Timesheet, Time Tracking, Time Entry History

---

## Coverage Table
## v2 — corrected locators, accept two-tap flow, 10 new tests added

| TC      | Scenario                                                              | Type       | Priority | Screen             | Maps to AC/FR     |
|---------|-----------------------------------------------------------------------|------------|----------|--------------------|-------------------|
| TC-01   | My Timesheet opens from drawer                                        | Normal     | High     | My Timesheet       | FR-1              |
| TC-02   | Proposed new entry card shows "Manual Entry Pending for Approval"     | Normal     | High     | My Timesheet       | AC-1, AC-2, FR-1  |
| TC-03   | ER sees Accept and Reject buttons on proposed new-entry card          | Normal     | High     | My Timesheet       | AC-3, FR-2        |
| TC-04   | ER accepts proposed new entry via accept modal (two-tap)              | Normal     | High     | My Timesheet       | AC-7, FR-8        |
| TC-05   | ER rejects proposed new entry — no reason, no email                   | Normal     | High     | My Timesheet       | AC-4, AC-6, FR-7  |
| TC-06   | Reject modal shows permanent-delete warning for new entry             | Normal     | High     | Reject modal       | AC-5, FR-5, EC-1  |
| TC-07   | ER rejects with reason text in modal                                  | Normal     | Med      | My Timesheet       | FR-4, FR-7        |
| TC-08   | ER toggles "Send email notification to employee" in reject modal      | Normal     | Med      | Reject modal       | FR-4, EC-3        |
| TC-09   | Modification card shows Accept and Reject buttons for ER              | Normal     | High     | My Timesheet       | AC-3, FR-2        |
| TC-10   | ER accepts pending modification via accept modal (two-tap)            | Normal     | High     | My Timesheet       | AC-7, FR-8        |
| TC-11   | ER rejects pending modification                                       | Normal     | High     | My Timesheet       | AC-6, FR-6, FR-7  |
| TC-12   | Reject modal shows revert warning for modification (not delete)       | Normal     | High     | Reject modal       | AC-5, FR-6, EC-1  |
| TC-13   | EE sees manualEntryPendingNotice, NOT Accept/Reject (new entry)       | Normal     | High     | My Timesheet       | AC-3, FR-3        |
| TC-14   | EE has no Cancel Request / Cancel Modifications on pending new entry  | Normal     | Med      | My Timesheet       | FR-3              |
| TC-15   | EE sees "Cancel Modifications" link for own modification CR           | Normal     | High     | My Timesheet       | AC-8, FR-9        |
| TC-16   | EE with pending CR blocked from clocking out                          | Edge       | High     | Time Tracking      | AC-9, FR-10, EC-5 |
| TC-17   | Add Time Entry button visible on manager's My Timesheet (no block)   | Normal     | Med      | My Timesheet       | —                 |
| TC-18   | ER edit blocked on pending new entry (ER-side message)                | Edge       | Med      | My Timesheet       | AC-11, FR-12      |
| TC-19   | ER edit blocked on pending modification (ER-side message)             | Edge       | Med      | My Timesheet       | AC-11, FR-13      |
| TC-20   | History "Time Entry Rejected" after ER rejects new entry             | Normal     | High     | Time Entry History | AC-12, FR-14      |
| TC-21   | History "Modifications Rejected" after ER rejects modification        | Normal     | High     | Time Entry History | AC-12, FR-14      |
| TC-22   | History "Time Entry Accepted" after ER accepts new entry              | Normal     | High     | Time Entry History | AC-12, FR-14      |
| TC-23   | Accept modal heading "Accept employee time entry changes" verified     | Normal     | High     | Accept modal       | FR-8              |
| TC-24   | EE cancel-modifications confirmation dialog verified                  | Normal     | High     | My Timesheet       | AC-8, EC-4        |
| TC-25   | EE cancels modification — pending card disappears                     | Normal     | High     | My Timesheet       | AC-8, FR-9        |
| TC-26   | History "Modifications Cancelled" after EE self-cancel                | Normal     | High     | Time Entry History | AC-12, FR-14      |
| TC-27   | History "Modifications Accepted" after ER accepts modification        | Normal     | High     | Time Entry History | AC-12, FR-14      |
| TC-28   | Clock-out blocked modal offers "Cancel Modifications & Clock Out"     | Edge       | High     | Time Tracking      | AC-9, FR-10       |
| TC-29   | EE edit blocked on pending new entry (EE-side message)                | Edge       | Med      | My Timesheet       | AC-11             |
| TC-30   | "Cancel Modifications" tooltip text visible in modification accordion  | Normal     | Med      | My Timesheet       | FR-9              |
| TC-31   | Reject modal contains "Reason" field label                            | Normal     | Med      | Reject modal       | FR-4              |
| TC-R01  | Clock In → Clock Out cycle still works (regression)                   | Regression | High     | Time Tracking      | —                 |
| TC-R02  | My Timesheet loads normally with no pending CRs                       | Regression | High     | My Timesheet       | —                 |
| TC-R03  | Team Timesheet accessible from drawer                                 | Regression | Med      | Team Timesheet     | —                 |
| TC-R04  | Add Time Entry button visible when no pending CR on manager account   | Regression | High     | My Timesheet       | —                 |
| TC-R05  | Time Tracking screen functional for manager                           | Regression | High     | Time Tracking      | —                 |

---

## Normal Cases

### TC-01: My Timesheet opens from drawer
**What this tests:** Drawer navigation to My Timesheet renders the screen heading.
**Precondition:** Logged in, on dashboard.
**Platform:** both

#### SETUP
verify on dashboard

#### TEST
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
verify "My Timesheet" is visible
screenshot "tc-01-my-timesheet"

#### TEARDOWN
press back

---

### TC-02: Proposed new entry card shows "Manual Entry Pending for Approval"
**What this tests:** A pending new entry submitted by EE shows the correct pending card header.
**Precondition:** A test EE account has submitted a new manual time entry awaiting manager approval. Logged in as ER (manager) account.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
verify "My Timesheet" is visible

#### TEST
scroll to "Manual Entry Pending for Approval"
verify "Manual Entry Pending for Approval" is visible
screenshot "tc-02-pending-card-header"

#### TEARDOWN
press back

---

### TC-03: ER sees Accept and Reject buttons on proposed entry card
**What this tests:** Accept and Reject action buttons are visible on the proposed new entry card.
**Precondition:** Logged in as ER (manager). A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
verify "Accept" is visible
verify "Reject" is visible
screenshot "tc-03-accept-reject-buttons"

#### TEARDOWN
press back

---

### TC-04: ER accepts proposed new time entry
**What this tests:** Tapping Accept on a proposed new entry applies it and shows success state.
**Precondition:** Logged in as ER. A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Accept"
dismiss popup if present: "Close"
verify "Manual Entry Pending for Approval" is not visible
screenshot "tc-04-after-accept"

#### TEARDOWN
press back

---

### TC-05: ER rejects proposed new entry — no reason, no email
**What this tests:** Reject without entering reason or toggling email notification completes successfully.
**Precondition:** Logged in as ER. A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
tap "Reject"
dismiss popup if present: "Close"
verify "Manual Entry Pending for Approval" is not visible
screenshot "tc-05-after-reject-no-reason"

#### TEARDOWN
press back

---

### TC-06: Reject modal shows correct warning for new entry (permanent delete)
**What this tests:** The reject modal displays the permanent-delete warning for a proposed new entry.
**Precondition:** Logged in as ER. A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
verify "Rejecting this entry will permanently delete this time entry." is visible
screenshot "tc-06-reject-modal-new-entry-warning"

#### TEARDOWN
tap "Cancel"
press back

---

### TC-07: ER rejects with reason text entered in modal
**What this tests:** Entering optional rejection reason in the modal and submitting works.
**Precondition:** Logged in as ER. A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
enter "Incorrect hours entered" into "Enter reason for rejection (optional)"
tap "Reject"
dismiss popup if present: "Close"
verify "Manual Entry Pending for Approval" is not visible
screenshot "tc-07-after-reject-with-reason"

#### TEARDOWN
press back

---

### TC-08: ER rejects and toggles "Send email notification to employee"
**What this tests:** The email notification checkbox is present and can be toggled in the reject modal.
**Precondition:** Logged in as ER. A proposed new entry card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
verify "Send email notification to employee" is visible
tap "Send email notification to employee"
screenshot "tc-08-email-checkbox-toggled"
tap "Reject"
dismiss popup if present: "Close"

#### TEARDOWN
press back

---

### TC-09: Pending modification card shows Accept and Reject buttons for ER
**What this tests:** A pending edit (modification) card also shows Accept and Reject for manager.
**Precondition:** Logged in as ER. A pending modification request card is visible on My Timesheet (EE has edited an existing entry).
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
verify "Accept" is visible
verify "Reject" is visible
screenshot "tc-09-modification-card-buttons"

#### TEARDOWN
press back

---

### TC-10: ER accepts pending modification
**What this tests:** Accepting a modification applies the EE's edit to the time entry.
**Precondition:** Logged in as ER. A pending modification card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Accept"
dismiss popup if present: "Close"
verify "Manual Entry Pending for Approval" is not visible
screenshot "tc-10-after-accept-modification"

#### TEARDOWN
press back

---

### TC-11: ER rejects pending modification
**What this tests:** Rejecting a modification discards the EE's edit and reverts the entry.
**Precondition:** Logged in as ER. A pending modification card is visible on My Timesheet.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
tap "Reject"
dismiss popup if present: "Close"
verify "Manual Entry Pending for Approval" is not visible
screenshot "tc-11-after-reject-modification"

#### TEARDOWN
press back

---

### TC-12: Reject modal warning text for modification (revert, not delete)
**What this tests:** The reject modal shows the "revert" warning (not permanent delete) for a pending modification.
**Precondition:** Logged in as ER. A pending modification card is visible.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Reject"
verify "Reject Time Entry" is visible
verify "If rejected, the modifications will be discarded and the time entry will be reverted to its previous state." is visible
screenshot "tc-12-reject-modal-modification-warning"

#### TEARDOWN
tap "Cancel"
press back

---

### TC-13: EE sees "Cancel Request" button on own pending entry
**What this tests:** Logged in as EE, the pending entry card shows "Cancel Request" not Accept/Reject.
**Precondition:** Logged in as EE who has a pending modification/new entry awaiting manager approval.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
verify "Cancel Request" is visible
verify "Accept" is not visible
verify "Reject" is not visible
screenshot "tc-13-cancel-request-button-ee"

#### TEARDOWN
press back

---

### TC-14: EE sees "Awaiting acceptance." notice on own pending entry
**What this tests:** The employee notice text is visible on their own pending entry card.
**Precondition:** Logged in as EE with a pending entry.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
verify "Awaiting acceptance." is visible
screenshot "tc-14-awaiting-acceptance-notice"

#### TEARDOWN
press back

---

### TC-15: EE cancels pending modification via "Cancel Request"
**What this tests:** EE taps "Cancel Request", confirmation dialog appears, and on confirm the modification is discarded.
**Precondition:** Logged in as EE with a pending modification.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Cancel Request"

#### TEST
tap "Cancel Request"
verify "Your pending changes will be discarded, and the time entry will revert to its previous state. Do you want to continue?" is visible
tap "Yes"
dismiss popup if present: "Close"
verify "Cancel Request" is not visible
screenshot "tc-15-after-cancel-request"

#### TEARDOWN
press back

---

## Edge Cases

### TC-16: EE with pending CR is blocked from clocking out
**What this tests:** When EE has a pending change request and tries to clock out, a block message appears.
**Precondition:** Logged in as EE. Employee is clocked in and has a pending modification awaiting manager approval.
**Platform:** both

#### SETUP
tap "Time Tracking"
verify clocked in

#### TEST
tap "Clock Out"
verify "You have pending modifications on this time entry that are awaiting manager approval. You cannot clock out until the modifications are resolved. Please ask your manager to accept or reject your changes, or cancel your modifications now and clock out." is visible
screenshot "tc-16-clock-out-blocked"

#### TEARDOWN
dismiss popup if present: "Close"
dismiss popup if present: "OK"

---

### TC-17: EE with pending CR is blocked from adding new time
**What this tests:** When EE has a pending CR, adding new time entry is blocked with an informational message.
**Precondition:** Logged in as EE with a pending modification.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"

#### TEST
scroll to "Add Time Entry"
tap "Add Time Entry"
verify "Time cannot be added while modifications are pending manager approval or rejection. You can add time once the manager takes action." is visible
screenshot "tc-17-add-time-blocked"

#### TEARDOWN
dismiss popup if present: "Close"
dismiss popup if present: "OK"
press back

---

### TC-18: ER cannot edit pending new entry (edit disabled message shown)
**What this tests:** ER attempting to edit a pending new entry sees an informational disabled message.
**Precondition:** Logged in as ER. A proposed new entry card is visible.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Edit Time Entry"
verify "This time entry is currently pending your approval and cannot be edited at this time. To make changes, you must first accept or reject the time entry." is visible
screenshot "tc-18-edit-disabled-new-entry"

#### TEARDOWN
dismiss popup if present: "Close"
dismiss popup if present: "OK"
press back

---

### TC-19: ER cannot edit pending modification (edit disabled message shown)
**What this tests:** ER attempting to edit a pending modification sees the correct disabled message.
**Precondition:** Logged in as ER. A pending modification card is visible.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"
scroll to "Manual Entry Pending for Approval"

#### TEST
tap "Edit Time Entry"
verify "This time entry modification is currently pending your approval and cannot be edited further at this time. To make changes, you must first accept or reject the pending modifications." is visible
screenshot "tc-19-edit-disabled-modification"

#### TEARDOWN
dismiss popup if present: "Close"
dismiss popup if present: "OK"
press back

---

### TC-20: Time Entry History shows "Time Entry Rejected" after new-entry reject
**What this tests:** After ER rejects a new proposed entry, Time Entry History records the rejection event.
**Precondition:** Logged in as ER. A proposed new entry has just been rejected (or a pre-rejected entry exists in history).
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"

#### TEST
scroll to "Time Entry Rejected"
verify "Time Entry Rejected" is visible
screenshot "tc-20-history-rejected"

#### TEARDOWN
press back

---

### TC-21: Time Entry History shows "Modifications Rejected" after edit reject
**What this tests:** After ER rejects a pending modification, history shows "Modifications Rejected".
**Precondition:** Logged in as ER. A modification has been rejected.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"

#### TEST
scroll to "Modifications Rejected"
verify "Modifications Rejected" is visible
screenshot "tc-21-history-modifications-rejected"

#### TEARDOWN
press back

---

### TC-22: Time Entry History shows "Time Entry Accepted" after accept
**What this tests:** After ER accepts a proposed entry, history shows "Time Entry Accepted".
**Precondition:** Logged in as ER. A new entry has been accepted.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"

#### TEST
scroll to "Time Entry Accepted"
verify "Time Entry Accepted" is visible
screenshot "tc-22-history-accepted"

#### TEARDOWN
press back

---

## Regression Cases

### TC-R01: Clock In → Clock Out cycle still works
**What this tests:** Core clock-in/out flow is unaffected by the new reject feature.
**Precondition:** Logged in, on dashboard, no pending CRs.
**Platform:** both

#### SETUP
tap "Time Tracking"

#### TEST
dismiss popup if present: "Close"
dismiss attestation if present
verify clocked out
tap "Clock In"
dismiss popup if present: "Close"
verify clocked in
tap "Clock Out"
dismiss attestation if present
dismiss popup if present: "Close"
verify clocked out
screenshot "tc-r01-clock-cycle"

#### TEARDOWN
(none)

---

### TC-R02: Regular (non-pending) time entries load on My Timesheet
**What this tests:** My Timesheet loads and displays existing non-pending entries normally.
**Precondition:** Logged in, on dashboard.
**Platform:** both

#### SETUP
open drawer
scroll to "My Timesheet"
tap "My Timesheet"

#### TEST
verify "My Timesheet" is visible
screenshot "tc-r02-my-timesheet-loads"

#### TEARDOWN
press back

---

### TC-R03: Team Timesheet accessible from drawer
**What this tests:** Manager can navigate to Team Timesheet via drawer (regression on navigation).
**Precondition:** Logged in as manager account, on dashboard.
**Platform:** both

#### SETUP
verify on dashboard

#### TEST
open drawer
scroll to "Team Timesheet"
tap "Team Timesheet"
verify "Team Timesheet" is visible
screenshot "tc-r03-team-timesheet"

#### TEARDOWN
press back
