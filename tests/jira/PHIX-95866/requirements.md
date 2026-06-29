# PHIX-95866 — Requirements
# Source: Jira (fetched 2026-05-26)
# Type: Improvement (Critical)
# Mobile screens: My Timesheet, Team Timesheet, Time Tracking (Clock In/Out), Time Entry History

## Summary

This story adds employer/manager (ER) ability to **accept or reject** time entry modifications
submitted by employees (EE) on the mobile app. When an employee adds a new time entry or edits
an existing one, it becomes a "proposed entry" (change request) that a manager must review.
The manager sees an Accept and a Reject button directly on the time entry card in My Timesheet
or Team Timesheet. The reject flow opens a modal where the manager can optionally enter a reason
and choose to send an email notification to the employee. Employees see a "Cancel Request" button
(not Accept/Reject) on their own pending entries and can cancel their own modifications. If a
pending modification exists, the employee is blocked from clocking out or adding new time until
the manager resolves it (or the employee cancels the request).

## Functional Requirements

- FR-1: Proposed new time entry card displays "Manual Entry Pending for Approval" as its header label — screen: My Timesheet / Team Timesheet
- FR-2: Proposed/modification entry card shows "Accept" and "Reject" action buttons for manager (ER) — screen: My Timesheet / Team Timesheet
- FR-3: Proposed/modification entry card shows "Cancel Request" button for employee (EE) — screen: My Timesheet
- FR-4: Tapping "Reject" opens a "Reject Time Entry" modal with an optional reason field, a "Send email notification to employee" checkbox, and a warning message — screen: My Timesheet / Team Timesheet
- FR-5: Reject modal warning text for a new (proposed) entry: "Rejecting this entry will permanently delete this time entry." — screen: Reject modal
- FR-6: Reject modal warning text for a pending modification: "If rejected, the modifications will be discarded and the time entry will be reverted to its previous state." — screen: Reject modal
- FR-7: Manager submits rejection via "Reject" button in modal; entry is deleted (new) or reverted (modification) — screen: My Timesheet / Team Timesheet
- FR-8: Manager accepts entry via "Accept" button; entry is applied — screen: My Timesheet / Team Timesheet
- FR-9: Employee cancels pending modification via "Cancel Request"; a confirmation dialog appears before discarding — screen: My Timesheet
- FR-10: EE who has a pending CR is blocked from clocking out with message "You have pending modifications on this time entry that are awaiting manager approval…" — screen: Time Tracking
- FR-11: EE with pending CR is blocked from adding new time with message "Time cannot be added while modifications are pending manager approval or rejection." — screen: My Timesheet
- FR-12: ER attempting to edit a pending new entry sees message: "This time entry is currently pending your approval and cannot be edited at this time." — screen: My Timesheet / Team Timesheet
- FR-13: ER attempting to edit a pending modification sees message: "This time entry modification is currently pending your approval and cannot be edited further at this time." — screen: My Timesheet / Team Timesheet
- FR-14: Time Entry History records "Time Entry Accepted", "Modifications Accepted", "Time Entry Rejected", or "Modifications Rejected" events — screen: Time Entry History

## UI Elements Affected

- "Manual Entry Pending for Approval" — card header label on proposed/new entry cards
- "Accept" — action button on proposed entry card (ER view)
- "Reject" — action button on proposed entry card (ER view)
- "Cancel Request" — action button on pending entry card (EE view)
- "Reject Time Entry" — modal title when rejecting
- "Enter reason for rejection (optional)" — placeholder text in reject reason field
- "Send email notification to employee" — checkbox label in reject modal
- "Rejecting this entry will permanently delete this time entry." — warning in modal for new entries
- "If rejected, the modifications will be discarded and the time entry will be reverted to its previous state." — warning in modal for modifications
- "Your pending changes will be discarded, and the time entry will revert to its previous state. Do you want to continue?" — cancel confirmation dialog
- "Awaiting acceptance." — notice shown to EE on their own pending entry
- "You have pending modifications on this time entry that are awaiting manager approval. You cannot clock out until the modifications are resolved. Please ask your manager to accept or reject your changes, or cancel your modifications now and clock out." — clock-out block message
- "Time cannot be added while modifications are pending manager approval or rejection. You can add time once the manager takes action." — add time block message
- "Time Entry Accepted", "Modifications Accepted", "Time Entry Rejected", "Modifications Rejected", "Time Entry Cancelled" — history event labels

## Acceptance Criteria

- AC-1: A manager (ER) can view proposed new time entries and pending modification requests in My Timesheet / Team Timesheet
- AC-2: Proposed entry card shows "Manual Entry Pending for Approval" header
- AC-3: Manager sees "Accept" and "Reject" buttons; employee sees "Cancel Request" button on the same cards
- AC-4: Tapping "Reject" opens the Reject Time Entry modal with reason field and email checkbox
- AC-5: Reject modal shows correct warning text: permanent delete for new entries, revert for modifications
- AC-6: On reject submission, new entry is permanently deleted; modification is discarded and entry reverts
- AC-7: On accept, the proposed entry / modification is applied to the attendance record
- AC-8: Employee can cancel their own pending modification via "Cancel Request"; confirmation shown
- AC-9: Employee with pending CR is blocked from clocking out until CR is resolved or cancelled
- AC-10: Employee with pending CR is blocked from adding new time entries
- AC-11: ER cannot edit a pending entry until it is accepted or rejected (edit disabled with message)
- AC-12: Time Entry History reflects the correct action label after each operation

## Edge Cases & Conditional Behavior

- EC-1: Reject modal shows different warning text depending on whether the entry is new (proposed add) vs. a modification (proposed edit)
- EC-2: Reject reason is optional — modal can be submitted without entering any reason
- EC-3: "Send email notification to employee" checkbox is unchecked by default; toggling it sends a rejection email to the EE
- EC-4: Cancel modifications confirmation dialog ("Your pending changes will be discarded…") appears before the change is discarded; user can cancel the cancel
- EC-5: Clock-out block is shown as a popup message (pendingCRClockOutBlocked), not a silent failure
- EC-6: Multiple pending CRs on the same entry: ER must resolve all before EE can clock out

## Platform Notes

- Android-specific: none noted
- iOS-specific: none noted; both platforms use identical i18n strings

## Out of Scope

- Amazon SFTP report output verification (backend/reporting)
- Kiosk portal pending CR block (kiosk-specific UI)
- Web portal accept/reject flows
- ZayZoon integration impact
- Payroll recalculation after rejection
