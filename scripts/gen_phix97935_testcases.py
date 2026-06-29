"""
PHIX-97935 — My Timesheet: Show all pay periods (not just those with entries).

Generate test-case Excel workbook (Summary + Detail Test Cases + Regression Checklist).

Run:
    python -m scripts.gen_phix97935_testcases
Output:
    reports/testcases/PHIX-97935_Testcases.xlsx
"""

from utils.testcase_excel import build_testcase_workbook

# ── Shared precondition blocks ────────────────────────────────────────────────

LOGGED_IN_EE = [
    "Launch UZIO app on the device / BrowserStack",
    "Dismiss notification permission if prompted (Allow / While using the app)",
    "Dismiss onboarding carousel if present (tap 'Skip' or swipe to 'Let's Begin')",
    "Enter mobile1@t.com into field[0] and password into field[1]",
    "Tap 'LOGIN'",
    "Dismiss 'Enable App Lock' prompt — tap \"I'll do it later\"",
    "Dismiss location permission if prompted",
    "Verify 'Time Tracking' tab (bottom nav) is visible = dashboard loaded",
]

ON_MY_TIMESHEET = LOGGED_IN_EE + [
    "Open drawer (tap hamburger icon top-left)",
    "Scroll to 'My Timesheet' under 'TIME AND ATTENDANCE' section if needed",
    "Tap 'My Timesheet'",
    "Verify 'My Timesheet' heading is visible",
    "Wait for pay period tab (date-range chip) to appear",
]

ON_MY_TIMESHEET_MODAL_OPEN = ON_MY_TIMESHEET + [
    "Tap the visible date-range chip (pay period selector button)",
    "Verify 'Select Pay Period' modal heading is visible",
]

EE = "Employee — mobile1@t.com"
EE_MOD = "Reportee/EE — mobile3@t.com"

# ── Test cases ────────────────────────────────────────────────────────────────

CASES = [

    # ── SANITY ────────────────────────────────────────────────────────────────

    dict(id="TC-01",
         title="My Timesheet screen loads via drawer navigation",
         module="My Timesheet",
         platform="Both",
         type="Sanity",
         priority="P1",
         role=EE,
         precondition="Logged in as mobile1@t.com; on dashboard (bottom nav visible)",
         precondition_steps=LOGGED_IN_EE,
         steps=[
             "Open drawer (tap hamburger icon top-left)",
             "Scroll to 'My Timesheet' under TIME AND ATTENDANCE if needed",
             "Tap 'My Timesheet'",
             "Verify 'My Timesheet' heading is visible",
             "Verify the screen does not show an error or crash",
         ],
         expected="My Timesheet screen loads; 'My Timesheet' heading visible; no error",
         app_text="My Timesheet",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_my_timesheet_screen_loads"),

    # ── FUNCTIONAL — CORE FIX ─────────────────────────────────────────────────

    dict(id="TC-02",
         title="Pay period date-range chip is visible on screen load",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="Logged in; My Timesheet screen open",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Observe the sub-heading area below 'My Timesheet' header",
             "Verify a date-range chip (e.g. 'May 01 - May 14') is visible",
             "Verify the chip is not blank or loading indefinitely",
         ],
         expected="A pay period date-range chip is visible (not empty); period selector is available",
         app_text="Pay Period (date-range chip showing startDate - endDate)",
         automation="Planned · pages/timesheet_page.py — MyTimesheetPage.verify_pay_period_chip_visible()"),

    dict(id="TC-03",
         title="Pay period modal includes periods with no time entries (main fix)",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="Logged in; My Timesheet screen open; employer has ≥2 pay periods on record",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Tap the date-range chip to open 'Select Pay Period' modal",
             "Verify 'Select Pay Period' heading is visible",
             "Count all period items listed in the modal",
             "Navigate to the UZIO web portal My Timesheet for the same account and count periods there",
             "Verify the mobile modal period count matches the web portal count (no filtering by entry presence)",
             "Note: pre-fix, only periods with ≥1 entry were shown; post-fix all periods appear",
         ],
         expected="Modal shows ALL pay periods matching the web portal, including empty periods",
         app_text="Select Pay Period, Confirm, Close",
         automation="Planned · requires web-vs-mobile parity comparison; see manual verification note"),

    dict(id="TC-04",
         title="Select pay period with no entries via tab — no crash or error",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; ≥2 pay periods shown; at least one period has no time entries",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Swipe the pay period tab left to navigate to an older/earlier pay period",
             "Repeat until a period with 0 hours is found (total shows '0h 00m' or '0h 0m')",
             "Verify the screen remains on 'My Timesheet' — no crash, no navigation away",
             "Verify no error toast or error overlay appears",
             "Verify the 'Total Paid Hours' card section is visible",
         ],
         expected="Screen stays on My Timesheet; no error; summary card visible for empty period",
         app_text="My Timesheet, Total Paid Hours",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_empty_period_no_crash"),

    dict(id="TC-05",
         title="Empty pay period: Total Paid Hours displays 0",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; navigated to a pay period with no time entries",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to a pay period with no time entries (swipe tab left to older period)",
             "Locate the 'Total Paid Hours' label on the summary card",
             "Verify the hours value directly below 'Total Paid Hours' shows '0h 00m' or '0h 0m'",
             "Verify the value is NOT blank and NOT a value carried over from a previous period",
         ],
         expected="'Total Paid Hours' shows 0 (e.g. '0h 00m') for an empty pay period",
         app_text="Total Paid Hours, 0h 00m",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_empty_period_zero_total_hours"),

    dict(id="TC-06",
         title="Empty pay period: day rows present with 0-hour duration",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; navigated to a pay period with no time entries",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to a pay period with no time entries",
             "Scroll down past the summary card into the Timesheet section",
             "Verify day rows are rendered (one row per day of the period)",
             "Verify each visible day row shows '0h 00m' or '0h 0m' as its duration",
             "Verify day rows are NOT absent (the FlatList is not empty)",
         ],
         expected="Day rows exist for every day of the period; each shows 0 hours duration",
         app_text="Timesheet, 0h 00m (per-day duration)",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_empty_period_day_rows_shown"),

    dict(id="TC-07",
         title="Empty pay period: Regular hours breakdown shows '0h 00m'",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P2",
         role=EE,
         precondition="My Timesheet open; on an empty pay period (0 total hours)",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to an empty pay period",
             "Locate the 'Regular' row in the summary card",
             "Verify 'Regular' value shows '0h 00m'",
         ],
         expected="Regular hours row shows '0h 00m' for an empty pay period",
         app_text="Regular, 0h 00m",
         automation="Planned · MyTimesheetPage.verify_summary_row('Regular', '0h 00m')"),

    dict(id="TC-08",
         title="Empty pay period: Overtime breakdown shows '0h 00m'",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P2",
         role=EE,
         precondition="My Timesheet open; on an empty pay period",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to an empty pay period",
             "Locate the 'Overtime' row in the summary card",
             "Verify 'Overtime' value shows '0h 00m'",
         ],
         expected="Overtime row shows '0h 00m' for an empty pay period",
         app_text="Overtime, 0h 00m",
         automation="Planned · MyTimesheetPage.verify_summary_row('Overtime', '0h 00m')"),

    dict(id="TC-09",
         title="Empty pay period: Paid Time Off breakdown shows '0h 00m'",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P2",
         role=EE,
         precondition="My Timesheet open; on an empty pay period",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to an empty pay period",
             "Locate the 'Paid Time Off' row in the summary card",
             "Verify 'Paid Time Off' value shows '0h 00m'",
         ],
         expected="Paid Time Off row shows '0h 00m' for an empty pay period",
         app_text="Paid Time Off, 0h 00m",
         automation="Planned · MyTimesheetPage.verify_summary_row('Paid Time Off', '0h 00m')"),

    # ── FUNCTIONAL — PAY PERIOD SELECTOR MODAL ───────────────────────────────

    dict(id="TC-10",
         title="'Select Pay Period' modal opens when date-range chip is tapped",
         module="My Timesheet — Pay Period Selector",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; ≥2 pay periods available (chip is tappable)",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Tap the date-range chip in the sub-heading (pay period selector button)",
             "Verify 'Select Pay Period' modal heading appears",
             "Verify a list of pay period date ranges is rendered in the modal",
         ],
         expected="'Select Pay Period' modal opens showing a scrollable list of pay periods",
         app_text="Select Pay Period, Confirm, Close",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_select_pay_period_modal_opens"),

    dict(id="TC-11",
         title="Modal lists pay periods including those with no entries",
         module="My Timesheet — Pay Period Selector",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="'Select Pay Period' modal is open",
         precondition_steps=ON_MY_TIMESHEET_MODAL_OPEN,
         steps=[
             "Scroll through the 'Select Pay Period' modal",
             "Count the total number of pay period items listed",
             "Verify the count is ≥ the number of pay periods configured in the employer's payroll calendar",
             "Verify periods appear for dates well before the employee's first time entry",
         ],
         expected="All configured pay periods are listed; not filtered to only those with existing entries",
         app_text="Select Pay Period",
         automation="Planned · requires count-assertion against employer payroll calendar"),

    dict(id="TC-12",
         title="Select empty period via modal + Confirm loads that period",
         module="My Timesheet — Pay Period Selector",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="'Select Pay Period' modal is open; at least one empty period exists in list",
         precondition_steps=ON_MY_TIMESHEET_MODAL_OPEN,
         steps=[
             "Scroll to an older pay period item (likely empty — no prior entries)",
             "Tap that pay period item to select it",
             "Tap 'Confirm'",
             "Verify the modal closes",
             "Verify 'My Timesheet' heading is visible",
             "Verify the date-range chip updates to the selected period's dates",
             "Verify 'Total Paid Hours' shows 0 (not a stale value from the previous period)",
         ],
         expected="Modal closes; selected empty period loads; total hours = 0; no crash",
         app_text="Select Pay Period, Confirm, My Timesheet, Total Paid Hours",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_select_empty_period_via_modal"),

    dict(id="TC-13",
         title="Modal 'Close' button dismisses without changing the active period",
         module="My Timesheet — Pay Period Selector",
         platform="Both",
         type="Functional",
         priority="P2",
         role=EE,
         precondition="'Select Pay Period' modal is open; current period has entries",
         precondition_steps=ON_MY_TIMESHEET_MODAL_OPEN,
         steps=[
             "Note the date range shown in the chip before opening the modal",
             "Tap a different pay period item in the modal (do NOT tap Confirm)",
             "Tap 'Close'",
             "Verify the modal closes",
             "Verify the date-range chip shows the same period as before the modal was opened",
             "Verify the Total Paid Hours value has not changed",
         ],
         expected="Modal closes; active pay period unchanged; hours unchanged",
         app_text="Select Pay Period, Close",
         automation="Planned · MyTimesheetPage.close_pay_period_modal_without_confirming()"),

    # ── REGRESSION ────────────────────────────────────────────────────────────

    dict(id="TC-14",
         title="Regression: Period with existing entries displays time entry cards",
         module="My Timesheet — Regression",
         platform="Both",
         type="Regression",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; current or recent pay period has ≥1 time entry",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "On My Timesheet, ensure the current period is selected (most recent, has entries)",
             "Scroll down into the Timesheet section",
             "Verify at least one day row shows a non-zero hour value (e.g. '8h 00m')",
             "Verify the day row is tappable (navigates to day detail on tap)",
         ],
         expected="Day rows with actual hours visible; tapping navigates to day entry detail",
         app_text="Timesheet, (non-zero hour value per day row)",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_regression_nonempty_period_shows_entries"),

    dict(id="TC-15",
         title="Regression: Period with entries shows correct Total Paid Hours (non-zero)",
         module="My Timesheet — Regression",
         platform="Both",
         type="Regression",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; current period has ≥1 time entry",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "On My Timesheet current period (has entries)",
             "Locate 'Total Paid Hours' label on the summary card",
             "Verify the hours value is NOT '0h 00m' (has actual hours)",
             "Verify the value is a valid time format (Xh XXm)",
         ],
         expected="'Total Paid Hours' shows a non-zero value matching the employee's actual hours",
         app_text="Total Paid Hours, (non-zero, e.g. 40h 00m)",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_regression_nonempty_period_total_hours"),

    dict(id="TC-16",
         title="Regression: Hour breakdown rows (Regular, Overtime) correct for non-empty period",
         module="My Timesheet — Regression",
         platform="Both",
         type="Regression",
         priority="P2",
         role=EE,
         precondition="My Timesheet open; current period has regular time entries",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "On My Timesheet current period with regular entries",
             "Verify 'Regular' row shows a non-zero value",
             "Verify 'Overtime', 'Double Overtime', 'Paid Time Off', 'Holiday', 'Holiday Premium', 'Break Premium' rows are visible",
         ],
         expected="All summary breakdown rows visible; Regular shows actual hours; no UI regression",
         app_text="Regular, Overtime, Double Overtime, Paid Time Off, Holiday, Holiday Premium, Break Premium",
         automation="Planned · MyTimesheetPage.verify_all_summary_rows_visible()"),

    # ── FUNCTIONAL — PERIOD SWITCHING ─────────────────────────────────────────

    dict(id="TC-17",
         title="Switch from empty period to non-empty period — hours update correctly",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; navigated to an empty pay period (0h 00m)",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Navigate to an empty pay period (verify 'Total Paid Hours' = 0)",
             "Swipe the period tab right OR tap the chip and select a period with entries",
             "Wait for the new period to load",
             "Verify 'Total Paid Hours' now shows a non-zero value",
             "Verify day rows update to show the entries of the newly selected period",
         ],
         expected="Switching from empty to non-empty period updates total hours to actual value (>0)",
         app_text="Total Paid Hours, My Timesheet",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_switch_empty_to_nonempty"),

    dict(id="TC-18",
         title="Switch from non-empty period to empty period — total clears to 0",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P1",
         role=EE,
         precondition="My Timesheet open; on a non-empty pay period (hours > 0)",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Verify current period has hours > 0 ('Total Paid Hours' is non-zero)",
             "Open 'Select Pay Period' modal OR swipe tab to navigate to an older empty period",
             "Wait for the empty period to load",
             "Verify 'Total Paid Hours' now shows '0h 00m' or '0h 0m'",
             "Verify the hours value is not a stale carryover from the previous period",
         ],
         expected="Switching to an empty period clears total hours to 0; no stale value persists",
         app_text="Total Paid Hours, 0h 00m",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_switch_nonempty_to_empty"),

    # ── EDGE CASES ────────────────────────────────────────────────────────────

    dict(id="TC-19",
         title="Pre-selected period is empty on screen open — 0 shown immediately",
         module="My Timesheet — Edge",
         platform="Both",
         type="Edge",
         priority="P1",
         role=EE,
         precondition="Account's most-recent pay period has no time entries; or use an account whose first visible period has no entries",
         precondition_steps=LOGGED_IN_EE,
         steps=[
             "Open drawer → tap 'My Timesheet' (without pre-navigating to any period)",
             "Verify 'My Timesheet' heading is visible",
             "WITHOUT tapping any period selector, observe the 'Total Paid Hours' value",
             "Verify 'Total Paid Hours' shows '0h 00m' (auto-selected period has no entries)",
             "Verify the pay period chip displays a valid date range",
         ],
         expected="My Timesheet auto-loads with the most recent period; if empty, 0 hours shown immediately without user interaction",
         app_text="My Timesheet, Total Paid Hours, 0h 00m",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_preselected_empty_period_zero_hours"),

    dict(id="TC-20",
         title="Employee with no entries in any period: all periods appear in selector",
         module="My Timesheet — Edge",
         platform="Both",
         type="Edge",
         priority="P2",
         role=EE_MOD,
         precondition="mobile3@t.com has no time entries in recent pay periods; employer has ≥2 configured periods",
         precondition_steps=[
             "Launch UZIO app on the device / BrowserStack",
             "Dismiss notification permission if prompted",
             "Dismiss onboarding carousel if present",
             "Enter mobile3@t.com into field[0] and password into field[1]",
             "Tap 'LOGIN'",
             "Dismiss 'Enable App Lock' prompt — tap \"I'll do it later\"",
             "Verify dashboard loaded",
         ],
         steps=[
             "Open drawer → tap 'My Timesheet'",
             "Verify 'My Timesheet' heading visible",
             "Tap the date-range chip to open 'Select Pay Period' modal",
             "Verify 'Select Pay Period' heading visible",
             "Scroll through the modal and count visible pay period items",
             "Verify ≥2 pay periods are listed even though no entries exist in any period",
             "Select any period and tap 'Confirm'",
             "Verify screen loads with '0h 00m' total hours",
         ],
         expected="All configured pay periods listed in modal; each shows 0 hours when selected — not filtered out",
         app_text="My Timesheet, Select Pay Period, Confirm, Total Paid Hours, 0h 00m",
         automation="Planned · requires account with guaranteed-empty periods across all pay periods"),

    dict(id="TC-21",
         title="PayPeriodNotDefined state: empty payPeriodList shows pre-existing empty state",
         module="My Timesheet — Edge",
         platform="Both",
         type="Edge",
         priority="P3",
         role="Employee on employer with no payroll calendar",
         precondition="Account belongs to an employer with no pay periods configured (no payroll calendar); payPeriodList API returns empty []",
         precondition_steps=[
             "Use a test account on an employer that has no payroll calendar configured",
             "Login and navigate to My Timesheet",
         ],
         steps=[
             "Open drawer → tap 'My Timesheet'",
             "Verify 'My Timesheet' heading visible",
             "Verify 'No time entries to display' message is shown",
             "Verify 'Please reach out to your employer for more information.' sub-text is shown",
             "Verify NO pay period chip is shown (no periods to select)",
         ],
         expected="Pre-existing empty state unchanged: 'No time entries to display' + employer contact message; no regression from fix",
         app_text="No time entries to display, Please reach out to your employer for more information.",
         automation="Manual — requires special employer account without payroll calendar"),

    dict(id="TC-22",
         title="Back navigation from My Timesheet returns to dashboard",
         module="My Timesheet",
         platform="Both",
         type="Functional",
         priority="P2",
         role=EE,
         precondition="My Timesheet screen is open",
         precondition_steps=ON_MY_TIMESHEET,
         steps=[
             "Tap the back button (top-left arrow on Android; edge-swipe or back button on iOS)",
             "Verify 'My Timesheet' heading is no longer visible",
             "Verify the bottom navigation bar (Time Tracking / Time Off / etc.) is visible",
         ],
         expected="Back navigation returns to the dashboard main shell; bottom nav visible",
         app_text="Time Tracking (bottom nav tab)",
         automation="Automated · tests/jira/PHIX-97935/test_phix_97935.py::TestPhix97935::test_back_navigation"),
]

# ── Meta ──────────────────────────────────────────────────────────────────────

META = dict(
    title="UZIO Mobile — PHIX-97935: My Timesheet Pay Period Parity",
    jira="PHIX-97935",
    generated_by="Test Generation Agent (MobileAutoQA)",
    environment="PROD (mobile1@t.com / mobile3@t.com)",
    app_build="PROD build — bs://6bba9b275c18350bb27e40f7db2ea1c689004420 (22-05-2026)",
    notes=(
        "Backend fix in TimesheetKit: payPeriodList API now returns ALL pay periods regardless of entry presence. "
        "Test accounts: mobile1@t.com = EE (primary), mobile3@t.com = EE-modify (EC-2). "
        "Roles: Employee only — Manager/Team Timesheet view is out of scope. "
        "Security: No sensitive data entry; payment / tax screens not tested here. "
        "Feature gate: None detected for EE pay-period list flow in TimeSheet.tsx. "
        "TC-21 is Manual — requires employer account with no payroll calendar configured."
    ),
)

if __name__ == "__main__":
    out = build_testcase_workbook(
        "reports/testcases/PHIX-97935_Testcases.xlsx", META, CASES)
    print(f"OK  Workbook written -> {out}  ({len(CASES)} cases)")
