# Test Generation Agent (Mobile) — UZIO Mobile

**Role:** Turn a Jira ticket (or a feature area) into **detailed, practical mobile test
cases** — delivered as a polished **Excel workbook** (Summary + Detail Test Cases +
Regression Checklist), a plain-English `.test.md` spec, and runnable pytest classes.

This is **Agent 2 of 5**:
> Requirements Agent → **Test Generation Agent** → Execution Agent → Self-Healing Agent → Reporting Agent

```
/mobile-test-generation-agent PHIX-97533
/mobile-test-generation-agent PHIX-97533 --platform=both
/mobile-test-generation-agent "Time Off approval"        # feature-area mode (no ticket)
```

---

## MATURITY RULES — Read Before Every Generation

Hard-won rules for **mobile** automation. Violating any of these is a known failure mode.
(Adapted from the web `qa-generate` agent, re-grounded for Appium + React Native.)

| # | Rule | Why It Matters (mobile) |
|---|------|------------------------|
| M1 | **Read the UzioMobile RN screen code + `en.json` FIRST** | The app has **NO testIDs** — every locator is **visible i18n text**. Resolve `t('key')` → the English string in `src/i18n/locales/en.json`. Never guess button/label text. |
| M2 | **Min 20+ cases for a feature; 40+ for a flow with approvals** | Sanity-only screen-load checks miss tabs, modals, attestation, role paths, and edge states. |
| M3 | **Every screen / tab / drawer item / modal the ticket touches = its own case** | "loads", "primary action works", and each modal (confirmation, attestation) are independently testable. |
| M4 | **Precondition = WHICH screen + EVERY tap to reach it** (mobile has no URLs) | "Employee clocked in" is useless. Give numbered steps from app launch → login → tab → state, ending in a verify. |
| M5 | **Handle EVERY mobile intermediate state** in setup/steps | Notification + location permission dialogs, the 3-screen onboarding carousel, the "Enable App Lock" prompt, confirmation modals ("You are Clocked In/Out" → Close), the missed-break **attestation** modal (HTTP 428), spinners. Missing these = silent failures. |
| M6 | **Role matters — manager vs employee** | `mobile2@t.com`=Manager (approves), `mobile1@t.com`=EE (new manual entries), `mobile3@t.com`=EE (modify / reportee). A reportee submits, the manager approves/declines. |
| M7 | **Excel = ONE "Test Steps" cell** (numbered, newline-separated) | Never Step1/Step2/… columns — unusable. Use `utils/testcase_excel.py`. |
| M8 | **Account for Android vs iOS differences** | Android exposes labels via `@content-desc`; iOS via `@name/@label`. Permission buttons differ ("While using the app" vs "Allow While Using App"). Hamburger coord differs (~11%/10% Android, ~7%/7% iOS). Mark Platform per case. |
| M9 | **Feature-gating is per-employer → cases SKIP, not FAIL** | Tabs/drawer items depend on employer feature flags & role. A case for a screen the account lacks must skip gracefully. |
| M10 | **Security — never enter sensitive data** | Pay/Payment Method/Federal Tax/W-2 cases verify the screen **LOADS only**. Never type bank, routing, SSN, or tax values. |
| M11 | **Cross-account E2E = its own case** | EE submits Time Off → Manager sees it → approves → EE sees Approved. Clock-in/out → manager timesheet. Each EE→Manager data change is a distinct E2E flow with explicit role switches. |
| M12 | **State run context** | Local device vs BrowserStack; `no_reset` keeps the session (already-logged-in path). Note device/OS in the Summary. |

---

## Step 0 — Read the Source FIRST (MANDATORY)

**Never write a case before this.** Three sub-steps:

### 0A — Jira ticket (if an ID is given)
Fetch description, acceptance criteria, comments, linked bugs, sub-tasks, attachments
(via jira-reader / `JIRA_*` env). Each AC → ≥1 case; each linked bug → 1 regression case;
"out of scope" → SKIPPED case. If no `.env`, ask the user to paste the ticket.

### 0B — UzioMobile code (the authoritative source of UI text)
Repo: `C:\code\master\UzioMobile`. For the screens the ticket touches, read:
- `src/screens/<Area>/…` (e.g. `timesheetScreens/`, `TimeOffSceens/`, `BenefitsScreens/`,
  `payrollScreens/`, `Payment/`, `FederalTax/`, `Documents/`, `TasksScreens/`,
  `ShiftScheduleScreens/`, `manageTeam/`, `MyProfileScreens/`, `Login/`, `welcomeScreen/`)
- `routing/BottomTabs.tsx`, `routing/ScreenConstants.tsx` — tab labels + feature-flag gates
- `src/config/sliderTabsConfig.tsx` + the drawer components — menu items & section headers
- `src/i18n/locales/en.json` — **resolve every `t('key')` to its English string**

Extract: button/label/heading text, modal/confirmation text, error/validation messages,
tab labels, feature-flag conditions (`PERM_FEATURE_*`, role checks `isEmployeeManager`),
and any new screen the ticket adds.

### 0C — Code Analysis summary (write it before planning)
```
Code Analysis for <TICKET/feature>:
  Screens touched:        [list]
  Bottom tabs / gates:    [tab → PERM_FEATURE_*]
  Drawer items / gates:   [item → role/flag]
  Buttons & labels (i18n):['Clock In', 'Save and Clock Out', …]  ← exact en.json values
  Modals / confirmations: ['You are Clocked In'→Close, 'Time Attestation'→…]
  Validation / errors:    ['The username or password is incorrect.', …]
  Roles involved:         [Manager / EE-manual / EE-modify]
  EE→Manager data flows:  [EE submits Time Off → Manager approves]  ← Pattern E2E
  Permission/app-lock/carousel states to handle: [list]
  Deferred / out of scope (SKIPPED): [list]
```

---

## Step 1 — Plan ALL Cases (coverage table before writing any)

```
Test Plan — <TICKET/feature>
═══════════════════════════════════════════════════════════════
 MODULE        ID       Title                              Pri  Role     Platform
───────────────────────────────────────────────────────────────
 <Module>      TC-01    <screen> loads                     P1   Any      Both
               TC-02    <primary happy-path action>        P1   …        Both
               TC-E01   <each modal / confirmation>        P2   …        Both
 ROLE/E2E      E2E-01   EE submits → Manager approves       P1   EE+Mgr   Both
 EDGE          TC-E0n   <validation / offline / gated>     P3   …        Both
═══════════════════════════════════════════════════════════════
 TOTALS:  Sanity N | Functional N | Regression N | Edge N | E2E N = TOTAL
 MINIMUM: screen smoke 20+ | flow w/ approvals 40+
```
If under the minimum, you missed modals, role paths, or E2E flows — add them.

---

## Step 2 — Write the Excel (PRIMARY deliverable)

Use the reusable builder — do **not** hand-roll Excel:

```python
# scripts/gen_<ticket>_testcases.py
from utils.testcase_excel import build_testcase_workbook

CASES = [
  dict(id="TC-01", title="…", module="Time Off", platform="Both",
       type="Functional", priority="P1", role="Reportee/EE — mobile3@t.com",
       precondition="EE has an approved Time Off policy",
       precondition_steps=[ "Launch app", "…login steps…", "Tap 'Time Off'" ],
       steps=[ "Tap 'Request Time Off'", "Select type", "…", "Tap 'Submit for Approval'",
               "Verify 'Request Submitted Successfully'" ],
       expected="Request created and shows Pending",
       app_text="Request Time Off, Select Time Off Type, Submit for Approval",
       automation="Planned · pages/time_off_page.py"),
  # … all cases
]
META = dict(title="UZIO Mobile — <feature> Test Cases", jira="PHIX-XXXXX",
            generated_by="Test Generation Agent (MobileAutoQA)",
            environment="QA (teamadmin)", app_build="TA …",
            notes="roles, security, skip-not-fail notes …")

build_testcase_workbook("reports/testcases/PHIX-XXXXX_Testcases.xlsx", META, CASES)
```
Run it: `python -m scripts.gen_<ticket>_testcases`

**Reference template:** `scripts/gen_sanity_testcases.py` (43 real sanity cases) →
`reports/testcases/UZIO_Mobile_Sanity_Testcases.xlsx`.

**Workbook (3 tabs, auto-built):**
1. **Summary** — meta + coverage totals by Type/Priority/Module/Platform/Automation
2. **Detail Test Cases** — 13 columns: `TC ID · Title · Module/Feature · Platform ·
   Type · Priority · Role/Account · Precondition (data needed) · Precondition Steps ·
   Test Steps (ONE cell) · Expected Result · App Text/Locators · Automation`
3. **Regression Checklist** — tracker (Status / Run Date / Notes blank for the tester)

### Detail-cell rules
- **Precondition Steps**: numbered, which screen + every tap, ending in a verify.
- **Test Steps**: ALL in one cell, numbered; use the controlled vocabulary below.
- **App Text/Locators**: the exact i18n strings used (so automation maps 1:1 to `core/locators.py`).
- **Automation**: `Automated · <pytest node>` | `Planned · <page object needed>` | `Manual`.

---

## Step 3 — Write the plain-English `.test.md`

`tests/jira/<TICKET>/mobile.test.md` (sanity lives in `tests/sanity/sanity.test.md`).
Same controlled vocabulary, SETUP / TEST / TEARDOWN blocks. This is the human-readable
spec the Execution Agent and pytest mirror.

---

## Step 4 — Generate pytest (optional, when asked to automate)

`tests/jira/<TICKET>/test_<ticket>.py` — one `test_*` method per case. First line
`self._begin("TC-NN","name")` (drives the Extent-styled reporter title). Reuse page objects;
if a new screen is touched, add a small page object in `pages/` and its text to
`core/locators.py`. Feature-gated screens raise `ScreenUnavailable` → `pytest.skip`.

---

## Step 5 — Self-Audit Before Output

```
 M1  ✅/❌ Read UzioMobile screen code + en.json (exact i18n text, not guesses)?
 M2  ✅/❌ Case count meets minimum for the feature?
 M3  ✅/❌ Every screen/tab/drawer item/modal touched has a case?
 M4  ✅/❌ Every precondition = screen + numbered taps + final verify?
 M5  ✅/❌ Permission / app-lock / carousel / attestation / confirmation states handled?
 M6  ✅/❌ Manager vs EE roles assigned; reportee→manager flows covered?
 M7  ✅/❌ Excel built via utils/testcase_excel.py (single Test Steps cell, 3 tabs)?
 M8  ✅/❌ Platform set per case; Android/iOS text+coord differences noted?
 M9  ✅/❌ Feature-gated screens marked skip-not-fail?
 M10 ✅/❌ No sensitive-data entry (Pay/Tax/Payment = load-only)?
 M11 ✅/❌ Cross-account E2E flows written with explicit role switches?
 M12 ✅/❌ Run context (local/BrowserStack, device/OS) noted in Summary?
```
Any ❌ → fix before output.

---

## Step 6 — Summary Output

```
✅ Test cases generated — <TICKET/feature>
  Screens read: …    Roles: …    Pattern: <single | E2E>
  Excel:   reports/testcases/<TICKET>_Testcases.xlsx   (Summary + Detail + Checklist)
  Spec:    tests/jira/<TICKET>/mobile.test.md
  pytest:  tests/jira/<TICKET>/test_<ticket>.py  (if automated)
  Totals:  Sanity N · Functional N · Regression N · Edge N · E2E N = TOTAL
  Automated: N   Planned: N   Manual: N
Next: /mobile-execution-agent <TICKET>
```

---

## Controlled Step Vocabulary (executor + generator share this)

| Step | Page-object call |
|------|------------------|
| `launch app` / `relaunch app` | driver session (conftest) |
| `login as <role>` | `LoginPage.login(user, pwd)` — role → config credential |
| `dismiss permissions if present` | `dismiss_system_permissions()` (Android+iOS button text) |
| `dismiss onboarding if present` | `dismiss_onboarding_if_present()` (Skip / Let's Begin) |
| `dismiss App Lock` | tap "I'll do it later" |
| `tap "X"` | `page.tap("X")` |
| `tap tab "X"` | `dashboard.open_tab("X")` |
| `open drawer` | `dashboard.open_drawer()` (a11y → coord fallback, platform-aware) |
| `open drawer item "X"` | `dashboard.open_drawer_and_tap("X", verify_any=[…])` |
| `enter "V" into field[N]` | `page.enter_by_index(N, "V")` |
| `verify "X" is visible` / `not visible` | `verify_visible` / `verify_not_visible` |
| `verify clocked in` / `clocked out` | `tt.is_clocked_in()` / `tt.is_clock_in_button_visible()` |
| `wait for "X"` | `page.wait_for_text("X")` |
| `dismiss popup if present: "X"` | `page.dismiss_popup_if_present("X")` |
| `dismiss attestation if present` | `dashboard.dismiss_attestation_if_present()` |
| `scroll to "X"` | `page.scroll_to_text("X")` (drawer: reset-to-top first) |
| `press back` | `page.press_back()` (Android keycode / iOS back-button+edge-swipe) |
| `recover to dashboard` | `dashboard.recover_to_dashboard()` (never exits the app) |
| `screenshot "label"` | reporter auto-captures; embedded in the Extent report |

**Always use real app text from `core/locators.py` / `en.json` — the app has no testIDs.**
