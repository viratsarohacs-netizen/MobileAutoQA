# PHIX-98315 — Requirements
# Source: Jira (fetched 2026-06-26)
# Type: Defect
# Priority: Major
# Status: QA In Progress
# Fix Versions: neuron-13.0, neuron-12.4.11
# Sprint: neuron-13.0 Sprint 8
# Mobile screens: Time Tracking → Time Entries (DayStatisticsV2)
# White-label build observed on: NRS Purple Mobile (PHIX-86688)

## Summary
On the **Time Entries** day view, the per-shift kebab action **Add Hours** on a
**No Show** shift card is broken: tapping it collapses the popup and never opens
the time-entry form, so the employee cannot log actual hours against the missed
shift. Fix lands in `src/screens/timesheetScreens/DayStatisticsV2.tsx`
(commit 6b432df0 on master). After the fix, tapping **Add Hours** must open the
**Add Edit Time Entry** screen pre-filled with the No Show shift's clock-in /
clock-out times, and Saving must convert the No Show entry into a regular time
entry.

## Functional Requirements
- FR-1: On a **No Show** shift card in Time Entries, tapping the 3-dot kebab menu must show the action **Add Hours** — screen: Time Tracking → Time Entries (DayStatisticsV2)
- FR-2: Tapping **Add Hours** must navigate to the **Add Edit Time Entry** form (route `AddEditTimeEntryV2`) — screen: Time Entries → Add Edit Time Entry
- FR-3: The form opens **pre-filled** with the No Show shift's scheduled clock-in and clock-out times (derived from `shiftInTime` / `shiftOutTime` of that specific card)
- FR-4: When multiple No Show shifts exist on the same day, tapping **Add Hours** on a *specific* card must open the form pre-filled with **that** card's times — not the first No Show card on the date
- FR-5: Saving the time-entry form converts the No Show entry into a regular time entry (status no longer "No Show")
- FR-6: The date-level bottom CTA **Add Time Entry** remains unaffected (out of scope for this defect)

## UI Elements Affected
- Kebab menu item label: `"Add Hours"` (i18n key `dayStatistics.addHours`) — present on No Show shift cards only
- Shift status label on the card: `"No Show"` (i18n key `timeEntries.noShow`) — backing source value `MISSED_SHIFT`
- Screen heading: `"Time Entries"` (i18n key `timeEnteries` — note: deliberate misspelling in en.json)
- Target screen on tap: `AddEditTimeEntryV2` (clock-in / clock-out / job inputs)
- Sibling kebab items on the same popup (must not regress): `"Check Photos"`, `"Attest Time Entry"`
- Unaffected control on screen: bottom CTA `"Add Time Entry"` (date-level)

## Acceptance Criteria
- AC-1: As an employee with **one** No Show shift on the selected date, tapping the 3-dot menu → **Add Hours** opens the Add Edit Time Entry form
- AC-2: The opened form is pre-filled with the No Show shift's scheduled clock-in and clock-out times
- AC-3: As an employee with **multiple** No Show shifts on the same date (e.g., 9:00–12:30 and 13:00–17:00 on Wed Jun 17, 2026), tapping **Add Hours** on the **second** No Show card opens the form pre-filled with the **second** card's times — not the first card's
- AC-4: As an employee whose No Show shift **starts before 10:00 AM** (e.g., 9:00, 8:30, 7:15), tapping **Add Hours** still opens the form (the previous length-≥-5 check no longer rejects 4-character "H:MM" times)
- AC-5: The popup does **not** collapse silently — either the form opens or, if a retro-action restriction applies, the existing `restrictOlderEntriesPopup` is shown
- AC-6: Saving the form updates the entry status away from **No Show**
- AC-7: The date-level **Add Time Entry** CTA continues to work on the same screen

## Edge Cases & Conditional Behavior
- EC-1: No Show shift starting **before 10:00 AM** (single-digit hour → `H:MM` time string of length 4) → **Add Hours** must open the form (regression from previous `timeStr.length >= 5` gate)
- EC-2: No Show shift starting **at or after 10:00 AM** (double-digit hour → `HH:MM` length 5) → must continue to work
- EC-3: **Multiple** No Show shifts on the same calendar date → each card's **Add Hours** opens its **own** pre-filled times (fix passes the full card item to the handler instead of looking up the first match by `entryIdentifier`)
- EC-4: Retro-action restriction (`item.restrictRetroActions === true`) → the `restrictOlderEntriesPopup` is shown instead of navigating
- EC-5: Non-No-Show card (`source !== 'MISSED_SHIFT'`) → handler returns early (defensive guard); **Add Hours** is not even rendered on those cards in normal flow
- EC-6: Saving the form must convert the entry from No Show to a regular time entry — verify on the Time Entries card list (status no longer reads "No Show")

## Platform Notes
- Defect was reproduced and verified fixed on **Android simulator** (per QA Comments field on the ticket)
- iOS: same React Native source, no platform-specific code in the diff — assume the same behavior; spot-check on iOS if available
- White-label: defect observed on **NRS Purple Mobile** (PHIX-86688 white-label build) — the underlying RN code is shared, so the fix applies across white-label flavors

## Out of Scope
- The date-level bottom CTA **Add Time Entry** (separate flow, not part of this defect)
- Other kebab actions on the same popup (Check Photos, Attest Time Entry) — verify only as non-regression, not as primary assertions
- Web (Phix) Time Entries — this defect is mobile-only
- Backend / API behavior — no service changes; the diff is entirely in `DayStatisticsV2.tsx`

## New Locators Needed (for core/locators.py)
Existing classes already cover Time Tracking basics but **none** of the
Time-Entries-day-view strings used by this test. Add a new class — proposed
shape:

```python
class TimeEntries:
    HEADING = "Time Entries"             # i18n key: timeEnteries (sic)
    NO_SHOW_STATUS = "No Show"           # i18n: timeEntries.noShow ; source=MISSED_SHIFT
    ADD_HOURS = "Add Hours"              # i18n: dayStatistics.addHours — kebab item
    ADD_TIME_ENTRY_CTA = "Add Time Entry"  # bottom CTA, date-level (non-regression)
    # Sibling kebab items on the same popup — only used for non-regression checks
    CHECK_PHOTOS = "Check Photos"
    ATTEST_TIME_ENTRY = "Attest Time Entry"
    # Form screen reached after Add Hours
    ADD_EDIT_FORM_ROUTE = "AddEditTimeEntryV2"   # route name, not visible text
```

The 3-dot kebab on each card has no visible text — locate it via the card row
+ the popup item ("Add Hours") that appears on tap.

## Reference — Fix Commits (UzioMobile)
- `6b432df0` — master — `PHIX-98315 [Mobile] Time Entries — tapping 'Add Hours' on a No Show shift collapses the popup; time-entry form never opens`
- `36f6e141` — PHIX_12.4.4.3 — same fix on the 12.4.4.3 release branch
- `ed0a4b7d` — PHIX_12.4.4.3 — **revert** of `36f6e141` (release-branch revert; the master fix `6b432df0` stands)

## Reference — Root Cause (per developer notes on ticket)
The pre-fix `handleAddHoursPressed(entryIdentifier)` had two bugs:
1. **Time-string length gate too strict** — `if (timeStr && timeStr.length >= 5)` rejected single-digit-hour times like "9:00", "8:30", "7:15" (length 4 in `H:MM`), so shifts starting before 10:00 AM never produced a pre-filled time array and the handler bailed.
2. **Wrong card lookup with duplicates** — the handler looked the card up via `trackingInfos.find(item => item.entryIdentifier === entryIdentifier && item.source === 'MISSED_SHIFT')`, which returned the **first** matching No Show entry on the day regardless of which kebab was tapped.

Fix passes the full `item` (the card itself) into the handler and relaxes the
length check to `>= 4`.
