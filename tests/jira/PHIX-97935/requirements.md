# PHIX-97935 — Requirements
# Source: Jira (fetched 2026-06-03)
# Type: Improvement
# Mobile screens: MyTimesheet (TimeSheet.tsx), Pay Period Selector modal

## Summary
The mobile "My Timesheet" screen previously displayed only pay periods that contained
at least one time entry. This ticket fixes that behavior so the mobile app shows ALL
pay periods — exactly as the web portal does — regardless of whether any entries exist.
When a pay period has no entries, the top-section total hours must display 0 and each
day row must also display 0 hours.

The backend fix was committed to TimesheetKit (master + int_branch). The mobile app
already calls the `/payPeriodList` API endpoint; the fix is entirely on the API response
— the server now returns all pay periods instead of only those with data.

## Functional Requirements
- FR-1: The "Select Pay Period" modal must list ALL pay periods returned by the API,
  not only those with time entries — screen: MyTimesheet (TimeSheet.tsx)
- FR-2: Selecting a pay period that has no time entries must render the timesheet detail
  view without crashing or showing an error state — screen: MyTimesheet
- FR-3: When a pay period has no time entries, the "Total Paid Hours" value in the top
  summary section must display 0 (e.g., "0h 0m" or "00:00") — screen: MyTimesheet
- FR-4: When a pay period has no time entries, each day row within the period must
  display 0 hours (not be absent or blank) — screen: MyTimesheet
- FR-5: Pay periods with existing time entries must continue to display their entries and
  correct hour totals (regression guard) — screen: MyTimesheet

## UI Elements Affected
- Pay period selector button — label: "Pay Period" (tap to open selector modal)
- Pay period selector modal — heading: "Select Pay Period"
- Confirm / close buttons — "Confirm" / "Close"
- Total hours section — label: "Total Paid Hours"
- Empty-period day rows — expected to show 0 hours per day
- "No time entries to display" empty-state message — shown inside a period with no entries

## Acceptance Criteria
- AC-1: Navigate to My Timesheet; tap "Pay Period" → the selector modal lists all pay
  periods matching the web portal (not filtered to only those with entries).
- AC-2: Select a pay period with no time entries → screen loads without an error or
  crash; "No time entries to display" message OR 0-hour rows are visible.
- AC-3: The "Total Paid Hours" summary for an empty pay period shows 0 hours (not blank,
  not a previous period's value).
- AC-4: Day-level hours for an empty pay period each show 0 (not absent).
- AC-5: Select a pay period that has existing entries → entries and totals render correctly
  (regression: prior behavior must be unchanged).

## Edge Cases & Conditional Behavior
- EC-1: First/most-recent pay period pre-selected on screen open → if that period is
  empty, FR-3 and FR-4 apply immediately without user interaction.
- EC-2: Employee with NO entries in ANY pay period → all periods still appear in selector;
  each shows 0 hours when selected.
- EC-3: Pay period list API returns empty array (`payPeriodList.length === 0`) → existing
  "PayPeriodNotDefined" empty state is shown (unchanged behavior — out of scope).
- EC-4: Network error during pay period list fetch → existing error handling applies
  (out of scope for this ticket).
- EC-5: Status codes `EE_NOT_ENABLED` or `PAY_PERIOD_NOT_FOUND` in pay period detail
  response → existing error handling applies (unchanged).

## Platform Notes
- Android-specific: none identified
- iOS-specific: none identified
- Feature flag: none (no `PERM_FEATURE_*` gate found in TimeSheet.tsx for this flow)
- Role: Employee (EE) self-service view. Manager approval view (isManagerApprovalPage)
  is out of scope — the ticket describes the employee "My Timesheet" screen only.

## New Locators Needed in core/locators.py → class MyTimesheet
- `PAY_PERIOD = "Pay Period"`  — pay period selector button label
- `SELECT_PAY_PERIOD = "Select Pay Period"` — selector modal heading
- `TOTAL_PAID_HOURS = "Total Paid Hours"` — summary section label
- `NO_TIME_ENTRIES_TO_DISPLAY = "No time entries to display"` — empty-period state text
- `CONFIRM = "Confirm"` — modal confirm button
- `CLOSE = "Close"` — modal close button

## API Reference
- Pay period list: `GET /app/timetracking/rest/mobile/timeTracking/payPeriodList`
  → `response.payPeriodList[]` — now returns all periods (fix in TimesheetKit)
- Pay period detail: `GET /app/timetracking/rest/mobile/timeTracking/payPeriodAttendance/{identifier}`
  → `response` — detail for a single period (unchanged endpoint)

## Out of Scope
- Team Timesheet / manager approval view (separate screen)
- Clock-in / clock-out flow on timesheetMainScreen
- Web portal — this ticket is mobile-only
- Pay period creation or configuration (employer admin)
- Behavior when `payPeriodList` is empty (PayPeriodNotDefined state — pre-existing)
