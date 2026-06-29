# PHIX-97935 — Mobile Test Spec
# My Timesheet: Show all pay periods (not just those with existing entries)
# Type: Improvement | Priority: Major | Status: Ready for QA
# Screens: TimeSheet.tsx (My Timesheet — EE view)
# Backend fix: TimesheetKit — payPeriodList API now returns all pay periods

---

## SETUP (shared by all tests below)

```
SETUP:
  launch app
  dismiss permissions if present
  dismiss onboarding if present
  login as EE (mobile1@t.com)
  dismiss App Lock
  verify "Time Tracking" is visible         # dashboard loaded
```

```
NAVIGATE_TO_MY_TIMESHEET:
  open drawer
  open drawer item "My Timesheet"           # under TIME AND ATTENDANCE section
  verify "My Timesheet" is visible
  wait for pay period date-range chip to appear
```

---

## TC-01 — My Timesheet screen loads via drawer navigation [Sanity, P1]

```
SETUP: LOGGED_IN_EE

TEST:
  open drawer
  scroll to "My Timesheet" if needed
  tap "My Timesheet"
  verify "My Timesheet" is visible
  verify no error overlay is shown

EXPECTED:
  My Timesheet screen loads cleanly with heading visible
```

---

## TC-02 — Pay period date-range chip visible on screen load [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  verify a date-range chip (e.g. "May 01 - May 14") is visible in the sub-heading
  verify chip is not blank or indefinitely loading

EXPECTED:
  Pay period chip shows a valid date range immediately after screen load
```

---

## TC-03 — Pay period modal includes periods with no entries (core fix) [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  tap date-range chip
  verify "Select Pay Period" is visible
  scroll through the modal and count all listed period items
  compare count to UZIO web portal My Timesheet period count (same account)

EXPECTED:
  Mobile modal period count equals web portal count; includes empty periods
  NOTE: pre-fix, only periods with ≥1 entry were shown — post-fix all appear
```

---

## TC-04 — Select empty period via tab — no crash [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  swipe period tab left to navigate to an older/empty period
  repeat until "Total Paid Hours" shows "0h 00m" or "0h 0m"
  verify "My Timesheet" heading still visible (no navigation away)
  verify no error overlay or crash

EXPECTED:
  Screen remains on My Timesheet; no error for empty period
```

---

## TC-05 — Empty pay period: Total Paid Hours shows 0 [Functional, P1]
<!-- HEALED 2026-06-03: test skips (not fails) when no 0h 00m period found within 12 swipes.
     PROD account has 1-min entry in every period. Use QA env (mobile1@t.com) for full coverage. -->

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  navigate to a pay period with no time entries (swipe tab left to older period)
  locate "Total Paid Hours" label
  verify value below "Total Paid Hours" is "0h 00m" or "0h 0m"
  verify value is not blank and not a carryover from a previous period

EXPECTED:
  "Total Paid Hours" = "0h 00m" for a pay period with no entries
```

---

## TC-06 — Empty pay period: day rows display 0-hour duration [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  navigate to a pay period with no time entries
  scroll down past the summary card into the "Timesheet" section
  verify day rows are rendered (not absent)
  verify each visible day row shows "0h 00m" or "0h 0m" as duration

EXPECTED:
  Day rows present for each day of the period; each shows 0 hours
```

---

## TC-07 — Empty pay period: Regular hours shows "0h 00m" [Functional, P2]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → navigate to empty period

TEST:
  locate "Regular" row in the summary card
  verify "Regular" value = "0h 00m"

EXPECTED:
  "Regular" shows "0h 00m" for empty pay period
```

---

## TC-08 — Empty pay period: Overtime shows "0h 00m" [Functional, P2]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → navigate to empty period

TEST:
  locate "Overtime" row in the summary card
  verify "Overtime" value = "0h 00m"

EXPECTED:
  "Overtime" shows "0h 00m" for empty pay period
```

---

## TC-09 — Empty pay period: Paid Time Off shows "0h 00m" [Functional, P2]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → navigate to empty period

TEST:
  locate "Paid Time Off" row in the summary card
  verify "Paid Time Off" value = "0h 00m"

EXPECTED:
  "Paid Time Off" shows "0h 00m" for empty pay period
```

---

## TC-10 — "Select Pay Period" modal opens on chip tap [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET (≥2 pay periods so chip is tappable)

TEST:
  tap the date-range chip in the sub-heading
  verify "Select Pay Period" heading is visible
  verify a list of pay period items is rendered

EXPECTED:
  "Select Pay Period" modal opens showing scrollable pay period list
```

---

## TC-11 — Modal lists all pay periods including empty ones [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → tap date-range chip → verify "Select Pay Period" visible

TEST:
  scroll through "Select Pay Period" modal
  count all listed period items
  verify count ≥ employer's configured pay period count
  verify periods with no entries appear (not filtered out)

EXPECTED:
  All configured periods listed; count not filtered by entry presence
```

---

## TC-12 — Select empty period via modal + Confirm loads the period [Functional, P1]

```
SETUP: "Select Pay Period" modal is open

TEST:
  scroll to an older pay period item (likely empty)
  tap that period item
  tap "Confirm"
  verify modal closes
  verify "My Timesheet" heading is visible
  verify date-range chip shows the newly selected period's dates
  verify "Total Paid Hours" = "0h 00m"

EXPECTED:
  Modal closes; empty period loads; total hours = 0; no crash
```

---

## TC-13 — Modal "Close" dismisses without changing active period [Functional, P2]

```
SETUP: "Select Pay Period" modal is open; current period has entries

TEST:
  note the current date-range chip value before opening modal
  tap a different period item in the modal (do NOT tap Confirm)
  tap "Close"
  verify modal closes
  verify date-range chip shows the SAME period as before

EXPECTED:
  Close dismisses the modal; active period and hours unchanged
```

---

## TC-14 — Regression: Non-empty period displays time entry day rows [Regression, P1]
<!-- HEALED 2026-06-03: detection regex broadened to match "0h 01m" (non-zero minutes
     when hours = 0). PROD account may have small sub-hour entries counting as non-empty. -->

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → current period has ≥1 time entry

TEST:
  scroll down into "Timesheet" section
  verify at least one day row shows a non-zero hour value (e.g. "8h 00m")
  tap a day row
  verify navigation to day detail view

EXPECTED:
  Day rows with actual hours; tapping navigates to detail — regression safe
```

---

## TC-15 — Regression: Non-empty period Total Paid Hours is non-zero [Regression, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → current period has entries

TEST:
  locate "Total Paid Hours" label on the summary card
  verify value is NOT "0h 00m" (has actual hours)
  verify format is valid (Xh XXm)

EXPECTED:
  "Total Paid Hours" shows actual non-zero hours — regression safe
```

---

## TC-16 — Regression: Summary breakdown rows correct for non-empty period [Regression, P2]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → current period has regular entries

TEST:
  verify "Regular" row shows non-zero value
  verify "Overtime", "Double Overtime", "Paid Time Off", "Holiday",
         "Holiday Premium", "Break Premium" rows are all visible

EXPECTED:
  All breakdown rows visible; Regular shows actual hours — no UI regression
```

---

## TC-17 — Switch empty → non-empty: hours update correctly [Functional, P1]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → navigate to empty period (0h 00m)

TEST:
  verify "Total Paid Hours" = "0h 00m" on the empty period
  tap chip OR swipe tab right to a period with entries
  wait for new period to load
  verify "Total Paid Hours" is now non-zero
  verify day rows update to the new period's entries

EXPECTED:
  Switching from empty to non-empty updates total hours to actual value (>0)
```

---

## TC-18 — Switch non-empty → empty: total clears to 0 [Functional, P1]
<!-- HEALED 2026-06-03: same as TC-05 — skips gracefully when no 0h 00m period found. -->

```
SETUP: NAVIGATE_TO_MY_TIMESHEET → on a period with entries (hours > 0)

TEST:
  verify "Total Paid Hours" is non-zero
  open "Select Pay Period" modal OR swipe tab to an older empty period
  wait for empty period to load
  verify "Total Paid Hours" = "0h 00m"
  verify no stale value remains from the previous period

EXPECTED:
  Switching to empty period clears total to 0; no stale carryover
```

---

## TC-19 — Pre-selected period is empty: 0 shown immediately on screen open [Edge, P1]

```
SETUP: LOGGED_IN_EE (account's most-recent period has no entries)

TEST:
  open drawer → tap "My Timesheet"
  WITHOUT tapping any period selector, observe "Total Paid Hours"
  verify "Total Paid Hours" = "0h 00m"
  verify a valid date-range chip is shown

EXPECTED:
  Screen auto-loads most-recent period; if empty, 0 hours shown immediately
```

---

## TC-20 — Employee with no entries in any period: all periods appear in modal [Edge, P2]

```
SETUP: login as mobile3@t.com (no entries in recent periods)
       navigate to My Timesheet

TEST:
  tap date-range chip → verify "Select Pay Period" visible
  scroll through modal and count period items
  verify ≥2 periods are listed (not empty — all periods appear)
  select any period → tap "Confirm"
  verify "Total Paid Hours" = "0h 00m"

EXPECTED:
  All configured periods listed even with zero entries; each shows 0 hours
```

---

## TC-21 — PayPeriodNotDefined state: empty payPeriodList unchanged [Edge, P3]

```
SETUP: Use employer account with no payroll calendar configured
       Login → navigate to My Timesheet

TEST:
  verify "No time entries to display" is visible
  verify "Please reach out to your employer for more information." is visible
  verify NO date-range chip is shown

EXPECTED:
  Pre-existing empty state unchanged; fix did not break no-period-configured scenario
  NOTE: Manual only — requires special employer account
```

---

## TC-22 — Back navigation from My Timesheet returns to dashboard [Functional, P2]

```
SETUP: NAVIGATE_TO_MY_TIMESHEET

TEST:
  press back (Android hardware back / iOS back arrow or edge swipe)
  verify "My Timesheet" heading is no longer visible
  verify bottom nav bar is visible (Time Tracking / Time Off tabs)

EXPECTED:
  Back navigation returns to dashboard main shell without error
```

---

## TEARDOWN (shared)

```
TEARDOWN:
  recover to dashboard
  (no data cleanup required — no entries created in these tests)
```

---

## App Text / Locator Reference

| Locator constant | Exact i18n string | Source |
|---|---|---|
| `MyTimesheet.HEADING` | "My Timesheet" | `myTimeSheet.heading` |
| `MyTimesheet.PAY_PERIOD` | "Pay Period" | `timeSheet.payPeriod` |
| `MyTimesheet.SELECT_PAY_PERIOD` | "Select Pay Period" | `timeSheet.selectPayPeriod` |
| `MyTimesheet.TOTAL_PAID_HOURS` | "Total Paid Hours" | `timeSheet.totalPaidHours` |
| `MyTimesheet.NO_TIME_ENTRIES_TO_DISPLAY` | "No time entries to display" | `timeSheet.noTimeEntriesToDisplay` |
| `MyTimesheet.CONFIRM` | "Confirm" | `timeSheet.confirm` |
| `MyTimesheet.CLOSE` | "Close" | `timeSheet.close` |
| `Drawer.MY_TIMESHEET` | "My Timesheet" | `Drawer.MY_TIMESHEET` |
| (summary rows) | "Regular", "Overtime", "Double Overtime", "Paid Time Off", "Holiday", "Holiday Premium", "Break Premium" | `timeSheet.*` |
| (empty state sub) | "Please reach out to your employer for more information." | `timeSheet.reachOutEmployer` |
