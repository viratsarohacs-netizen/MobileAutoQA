"""
PHIX-86688 — UZIO White Label Partner | NRS Purple — Mobile App UI tests.

Scope (focused per developer instruction 2026-06-16):
    * NRS Purple flavor APK ONLY (com.uzioapp.nrspurple v6.4.13, build 12.4.4.3_1606)
    * UI changes ONLY — branding, theme, About Us copy, Login screen, Switch Accounts
      header, language picker, drawer placement
    * Credentials available:
        Employee         (ein@ch.com / Qwerty@12)  — Ein Lname
        Reportee-Manager (ale@ch.com / Qwerty@12) — Bale Lname  → approves Ein's requests
    * Run target: BrowserStack (bs://e6d554c8c8ddec416f7cd62d8571a40a0114eac6)

Out of scope (intentionally dropped from the earlier 37-case plan):
    * Cross-flavor regression (UZIO / TECHSERVE / TWENTYAI / ...) — separate builds
    * SSO failure path — no SSO test exchange wired for NRS Purple here
    * Network-log assertions (subdomain in POST) — BrowserStack Free plan has no network log
    * Kiosk consent text — no Kiosk-enabled role in the provided credentials
    * Server-unreachable path — out of UI scope

Run:
    python -m scripts.gen_phix86688_testcases
Output:
    reports/testcases/PHIX-86688_Testcases.xlsx
"""

from utils.testcase_excel import build_testcase_workbook

# ── Roles / accounts ────────────────────────────────────────────────────────
EE = "Employee — ein@ch.com (Ein Lname)"
MGR = "Reportee-Manager — ale@ch.com (Bale Lname)"
ANY = "Any role"
PRE = "Pre-login (fresh install / signed out)"

# ── Shared precondition blocks ──────────────────────────────────────────────

LAUNCH_NRSP = [
    "Launch the NRS Purple app from BrowserStack (bs://...0114eac6, v6.4.13)",
    "Wait for the loading / splash screen to render",
]

ON_LOGIN_NRSP = LAUNCH_NRSP + [
    "Dismiss notification permission if prompted (Allow / While using the app)",
    "Dismiss onboarding carousel if present (tap 'Skip' or swipe to 'Let's Begin')",
    "Verify Login screen heading 'Welcome to NRS Purple' is visible",
]

LOGGED_IN_EE_NRSP = ON_LOGIN_NRSP + [
    "Enter 'ein@ch.com' into field[0]",
    "Enter 'Qwerty@12' into field[1]",
    "Tap 'LOGIN'",
    "Dismiss 'Enable App Lock' prompt — tap \"I'll do it later\"",
    "Dismiss location permission if prompted",
    "Verify 'Time Tracking' tab (bottom nav) is visible = dashboard loaded",
]

LOGGED_IN_MGR_NRSP = [
    "Launch the NRS Purple app",
    "If signed in as someone else, logout via drawer first",
    "On Login screen, enter 'ale@ch.com' / 'Qwerty@12' and tap 'LOGIN'",
    "Dismiss App Lock and location permission prompts",
    "Verify dashboard loads",
]

ON_ABOUT_US_NRSP = LOGGED_IN_EE_NRSP + [
    "Open drawer (tap hamburger icon top-left)",
    "Scroll to 'About NRS Purple' (under HELP AND SUPPORT) if needed",
    "Tap 'About NRS Purple'",
    "Verify 'About NRS Purple' heading is visible",
]

# ── Test cases ──────────────────────────────────────────────────────────────

CASES = [

    # ════════════════════ BUILD / BRANDING ═════════════════════════════════

    dict(id="TC-01",
         title="App launches; OS launcher / task switcher shows 'NRS Purple' label",
         module="Build/Branding", platform="Android",
         type="Sanity", priority="P1", role=ANY,
         precondition="NRS Purple APK installed on the BrowserStack Samsung Galaxy S23",
         precondition_steps=LAUNCH_NRSP,
         steps=[
             "Verify the title bar / task switcher / cold-launch title reads 'NRS Purple'",
             "Verify the app reaches a renderable first screen without crashing",
         ],
         expected="App label 'NRS Purple' visible at launch; no crash",
         app_text="(launcher) NRS Purple",
         automation="Automated · TestNrsPurpleBuild.test_01_app_label_nrs_purple"),

    dict(id="TC-02",
         title="Loading splash shows the square NRS Purple logo",
         module="Build/Branding", platform="Android",
         type="Sanity", priority="P1", role=ANY,
         precondition="Cold launch the NRS Purple app",
         precondition_steps=LAUNCH_NRSP,
         steps=[
             "Capture a screenshot of the splash / loading screen before Login renders",
             "Visually verify the splash logo is the SQUARE NRS Purple logo (NrspurpleLogo.svg)",
             "Verify the splash background is the NRS Purple purple (#563d6e)",
         ],
         expected="Square NRS Purple logo on a purple splash, matching XD design",
         app_text="(splash) NrspurpleLogo.svg, theme #563d6e",
         automation="Automated · TestNrsPurpleBuild.test_02_splash_screenshot (visual check)"),

    dict(id="TC-03",
         title="App theme — safe-area / header colour is #563d6e",
         module="Build/Branding", platform="Android",
         type="Sanity", priority="P1", role=ANY,
         precondition="On the Login screen of the NRS Purple build",
         precondition_steps=ON_LOGIN_NRSP,
         steps=[
             "Capture a screenshot of the Login screen with the top safe-area visible",
             "Visually verify the top safe-area / header background is purple (#563d6e)",
             "After login, repeat on the dashboard to confirm the theme persists",
         ],
         expected="Header + safe-area = #563d6e on Login and on the dashboard",
         app_text="(theme) COLOR.SAFE_AREA_BACKGROUND_COLOR.NRSPURPLE",
         automation="Automated · TestNrsPurpleBranding.test_03_theme_color (screenshot artifact)"),

    # ════════════════════ LOGIN ════════════════════════════════════════════

    dict(id="TC-04",
         title="Login screen heading reads 'Welcome to NRS Purple'",
         module="Login", platform="Android",
         type="Functional", priority="P1", role=PRE,
         precondition="On Login screen of NRS Purple build",
         precondition_steps=ON_LOGIN_NRSP,
         steps=[
             "Verify text 'Welcome to NRS Purple' is visible on the Login screen",
             "Verify text 'Welcome to UZIO' is NOT visible",
         ],
         expected="Heading resolves from en_nrspurple.json → login.heading",
         app_text="login.heading = 'Welcome to NRS Purple'",
         automation="Automated · TestNrsPurpleLogin.test_04_login_heading"),

    dict(id="TC-05",
         title="Login screen — square NRS Purple logo + form fields reachable",
         module="Login", platform="Android",
         type="Functional", priority="P1", role=PRE,
         precondition="On Login screen of NRS Purple build",
         precondition_steps=ON_LOGIN_NRSP,
         steps=[
             "Verify the brand logo above the form renders (no broken image)",
             "Verify the 'Username (Email Address)' field is reachable",
             "Verify the 'Password' field is reachable",
             "Verify the 'LOGIN' button is reachable (not pushed off-screen)",
             "Capture a screenshot for visual review of logo placement (wp 55% / flex-start)",
         ],
         expected="Logo + form fields render; nothing clipped off-screen",
         app_text="Username (Email Address), Password, LOGIN",
         automation="Automated · TestNrsPurpleLogin.test_05_form_layout"),

    dict(id="TC-06",
         title="Valid NRS Purple employee can log in (ein@ch.com)",
         module="Login", platform="Android",
         type="Functional", priority="P1", role=EE,
         precondition="NRS Purple QA environment is up; ein@ch.com has access",
         precondition_steps=ON_LOGIN_NRSP,
         steps=[
             "Enter 'ein@ch.com' into field[0]",
             "Enter 'Qwerty@12' into field[1]",
             "Tap 'LOGIN'",
             "Dismiss App Lock + location permission if they appear",
             "Verify dashboard loads (bottom nav 'Time Tracking' visible)",
         ],
         expected="Login succeeds; dashboard renders",
         app_text="LOGIN, Time Tracking",
         automation="Automated · TestNrsPurpleLogin.test_06_valid_login_ee"),

    dict(id="TC-07",
         title="Invalid credentials show 'The username or password is incorrect.'",
         module="Login", platform="Android",
         type="Functional", priority="P2", role=PRE,
         precondition="On Login screen of NRS Purple build (signed out)",
         precondition_steps=ON_LOGIN_NRSP,
         steps=[
             "Enter 'ein@ch.com' into field[0]",
             "Enter 'WRONG_PASSWORD' into field[1]",
             "Tap 'LOGIN'",
             "Verify error 'The username or password is incorrect.' is visible",
             "Verify the user remains on the Login screen (no dashboard)",
         ],
         expected="Error message renders verbatim; no nav transition",
         app_text="login.incorrectCredentials = 'The username or password is incorrect.'",
         automation="Automated · TestNrsPurpleLogin.test_07_invalid_credentials"),

    # ════════════════════ ABOUT US ═════════════════════════════════════════

    dict(id="TC-08",
         title="Drawer → 'About NRS Purple' item is visible and opens the About screen",
         module="About Us", platform="Android",
         type="Functional", priority="P1", role=EE,
         precondition="Logged in as ein@ch.com",
         precondition_steps=LOGGED_IN_EE_NRSP,
         steps=[
             "Open drawer (tap hamburger icon top-left)",
             "Scroll to HELP AND SUPPORT section",
             "Verify 'About NRS Purple' drawer item is visible",
             "Tap 'About NRS Purple'",
             "Verify the About screen opens (heading 'About NRS Purple' visible)",
         ],
         expected="Drawer item is gated by appNames now including 'NRSPURPLE'",
         app_text="sliderTabsConfig appNames → NRSPURPLE; drawer label 'About NRS Purple'",
         automation="Automated · TestNrsPurpleAbout.test_08_drawer_opens_about"),

    dict(id="TC-09",
         title="About Us — heading 'About NRS Purple' + subheading 'NRS Purple'",
         module="About Us", platform="Android",
         type="Functional", priority="P1", role=EE,
         precondition="On About NRS Purple screen",
         precondition_steps=ON_ABOUT_US_NRSP,
         steps=[
             "Verify text 'About NRS Purple' is visible (heading)",
             "Verify text 'NRS Purple' (subheading) is visible",
             "Verify 'About UZIO' / 'UZIO' (UZIO copy) is NOT visible",
         ],
         expected="Heading + subheading match NRS Purple branding",
         app_text="aboutUs.heading = 'About NRS Purple'; aboutUs.subHeading = 'NRS Purple'",
         automation="Automated · TestNrsPurpleAbout.test_09_heading_and_subheading"),

    dict(id="TC-10",
         title="About Us — 'App v<version>' label visible",
         module="About Us", platform="Android",
         type="Functional", priority="P2", role=EE,
         precondition="On About NRS Purple screen",
         precondition_steps=ON_ABOUT_US_NRSP,
         steps=[
             "Locate the 'App v' label under the subheading",
             "Verify the label starts with 'App v' and contains a version number "
             "(e.g. App v6.4.13 per the installed APK)",
         ],
         expected="App version label is present and well-formed",
         app_text="'App v' + APP_VERSION (6.4.13)",
         automation="Automated · TestNrsPurpleAbout.test_10_app_version_label"),

    dict(id="TC-11",
         title="About Us — info paragraph references NRS Purple payroll + Employee Portal",
         module="About Us", platform="Android",
         type="Functional", priority="P2", role=EE,
         precondition="On About NRS Purple screen",
         precondition_steps=ON_ABOUT_US_NRSP,
         steps=[
             "Scroll the info paragraph into view",
             "Verify the paragraph contains 'NRS Purple provides payroll software'",
             "Verify the paragraph also contains 'The NRS Purple Employee Portal and mobile app'",
             "Verify NO 'UZIO is a SaaS-based online marketplace' (UZIO copy) is present",
         ],
         expected="Info copy is NRS-Purple-specific (en_nrspurple.aboutUs.info)",
         app_text="aboutUs.info — NRS Purple payroll software ...",
         automation="Automated · TestNrsPurpleAbout.test_11_info_paragraph"),

    dict(id="TC-12",
         title="About Us — footer reads 'Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved.'",
         module="About Us", platform="Android",
         type="Functional", priority="P2", role=EE,
         precondition="On About NRS Purple screen",
         precondition_steps=ON_ABOUT_US_NRSP,
         steps=[
             "Scroll to the bottom of the About screen",
             "Verify the footer text reads exactly: "
             "'Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved.'",
             "Verify the UZIO footer ('Uzio Technology, Inc. © 2026 UZIO. All rights reserved.') is NOT present",
         ],
         expected="Footer is NRS-Purple-branded",
         app_text="aboutUs.footer = 'Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved.'",
         automation="Automated · TestNrsPurpleAbout.test_12_footer"),

    # ════════════════════ SWITCH ACCOUNTS · LANGUAGE ═══════════════════════

    dict(id="TC-13",
         title="Switch Accounts — header reads 'NRS Purple' exactly",
         module="Switch Accounts", platform="Android",
         type="Functional", priority="P2", role=EE,
         precondition="Logged in as ein@ch.com",
         precondition_steps=LOGGED_IN_EE_NRSP + [
             "Open drawer; locate the SETTINGS section",
             "Tap 'Login Accounts' (Switch / Register Accounts screen)",
         ],
         steps=[
             "Locate the app-name label rendered above / next to the form",
             "Verify it reads exactly 'NRS Purple' (proper case, space between words)",
             "Verify it does NOT read 'Nrspurple' (the OLD title-case derivation)",
         ],
         expected="Header label resolves from i18n key t('APP_NAME') = 'NRS Purple'",
         app_text="t('APP_NAME') = 'NRS Purple'",
         automation="Automated · TestNrsPurpleSwitchAccounts.test_13_app_name_label"),

    dict(id="TC-14",
         title="Language picker — single 'English' option mapped to en_nrspurple",
         module="Language", platform="Android",
         type="Functional", priority="P2", role=EE,
         precondition="Logged in as ein@ch.com",
         precondition_steps=LOGGED_IN_EE_NRSP,
         steps=[
             "Open drawer → SETTINGS → 'Language'",
             "Verify exactly one option labelled 'English' is visible in the picker",
             "Select / re-select it",
             "Navigate to About NRS Purple and verify the heading still reads 'About NRS Purple'",
         ],
         expected="getLanguageArray() returns [{'English' → en_nrspurple}]",
         app_text="label.language.english = 'English'",
         automation="Automated · TestNrsPurpleLanguage.test_14_single_english_option"),

    # ════════════════════ SANITY (NRS Purple end-to-end UI) ════════════════

    dict(id="TC-15",
         title="NRS Purple — bottom navigation tabs are reachable",
         module="Sanity", platform="Android",
         type="Sanity", priority="P1", role=EE,
         precondition="Logged in as ein@ch.com",
         precondition_steps=LOGGED_IN_EE_NRSP,
         steps=[
             "Verify 'Time Tracking' tab is visible (default landing tab)",
             "Tap each visible bottom tab in turn — verify each renders without crash:",
             "  Benefits / Schedule / Time Tracking / Time Off / Inbox",
             "Skip-not-fail: tabs gated off by employer feature flag should be absent, not crash",
         ],
         expected="Every gated tab opens; non-enabled tabs are silently absent",
         app_text="Benefits, Schedule, Time Tracking, Time Off, Inbox",
         automation="Automated · TestNrsPurpleSanity.test_15_bottom_nav"),

    dict(id="TC-16",
         title="NRS Purple — Logout via hamburger drawer works",
         module="Sanity", platform="Android",
         type="Sanity", priority="P1", role=EE,
         precondition="Logged in as ein@ch.com",
         precondition_steps=LOGGED_IN_EE_NRSP,
         steps=[
             "Open drawer (hamburger top-left)",
             "Scroll to the bottom of the drawer; tap 'Logout'",
             "Verify the Login screen heading 'Welcome to NRS Purple' is visible",
         ],
         expected="Logout returns to the NRS Purple Login screen",
         app_text="Logout, Welcome to NRS Purple",
         automation="Automated · TestNrsPurpleSanity.test_16_logout"),

    dict(id="TC-17",
         title="NRS Purple — drawer section structure (HELP AND SUPPORT contains About)",
         module="Sanity", platform="Android",
         type="Sanity", priority="P2", role=EE,
         precondition="Logged in as ein@ch.com; drawer open",
         precondition_steps=LOGGED_IN_EE_NRSP + ["Open drawer"],
         steps=[
             "Scroll the drawer top → bottom",
             "Verify the SETTINGS section header is visible",
             "Verify the HELP AND SUPPORT section header is visible",
             "Verify 'About NRS Purple' appears exactly once, under HELP AND SUPPORT",
         ],
         expected="Drawer structure is unchanged; 'About NRS Purple' is in the right section",
         app_text="HELP AND SUPPORT → About NRS Purple",
         automation="Automated · TestNrsPurpleSanity.test_17_drawer_structure"),

    # ════════════════════ E2E (Pattern E — manager approval) ═══════════════

    dict(id="E2E-01",
         title="EE submits Time Off → Manager (Bale) approves → EE sees Approved",
         module="E2E", platform="Android",
         type="E2E", priority="P1", role="Ein (EE) + Bale (Manager)",
         precondition="Ein has a Time Off policy assigned; Bale is Ein's manager",
         precondition_steps=LOGGED_IN_EE_NRSP + ["Tap bottom tab 'Time Off'"],
         steps=[
             "On Ein's session: tap 'Request Time Off'",
             "Tap 'Select Time Off Type' → choose any available type",
             "Pick Start Date and End Date (future date, non-holiday)",
             "Enter a valid hour increment > 0 (e.g. 8)",
             "Tap 'Submit for Approval'",
             "Verify 'Request Submitted Successfully' is visible",
             "Open drawer → tap 'Logout'",
             "Login as ale@ch.com / Qwerty@12 (Bale)",
             "Open drawer → MANAGE TEAM → 'Team Time Off'",
             "Verify Ein's pending request is listed",
             "Approve the request (Approve button on the request card)",
             "Logout Bale; login back as ein@ch.com",
             "Tap tab 'Time Off' → Pending / Completed",
             "Verify the request status reads 'Approved'",
         ],
         expected="Full Time Off request → approve cycle works on NRS Purple flavor",
         app_text="Request Time Off, Submit for Approval, Request Submitted Successfully, Team Time Off, Approve, Approved",
         automation="Automated · TestNrsPurpleE2E.test_e2e_01_time_off_request_approve"),

    dict(id="E2E-02",
         title="EE Clock In then Clock Out → Manager sees the time entry on Team Timesheet",
         module="E2E", platform="Android",
         type="E2E", priority="P1", role="Ein (EE) + Bale (Manager)",
         precondition="Ein has Time Tracking enabled; Bale supervises Ein",
         precondition_steps=LOGGED_IN_EE_NRSP + ["Verify 'Time Tracking' tab is visible"],
         steps=[
             "Tap 'Clock In'",
             "If 'You are Clocked In' modal appears, tap 'Close'",
             "Verify clocked-in state (Clock Out button OR 'Clocked In' sub-heading)",
             "Tap 'Clock Out'",
             "If attestation modal appears, complete it (tap 'Save and Clock Out')",
             "If 'You are Clocked Out' modal appears, tap 'Close'",
             "Logout Ein; login as Bale (ale@ch.com)",
             "Open drawer → MANAGE TEAM → 'Team Timesheet'",
             "Verify Ein's freshly created time entry is listed for today",
         ],
         expected="Time entry created on NRS Purple flavor and surfaces in Team Timesheet",
         app_text="Clock In, Clock Out, You are Clocked In, You are Clocked Out, Team Timesheet",
         automation="Automated · TestNrsPurpleE2E.test_e2e_02_clock_in_out_team_timesheet"),

]

# ── Workbook meta ───────────────────────────────────────────────────────────
META = dict(
    title="UZIO Mobile — PHIX-86688 NRS Purple — UI Test Cases",
    jira="PHIX-86688",
    generated_by="Test Generation Agent (MobileAutoQA)",
    environment="QA NRS Purple (BrowserStack — Samsung Galaxy S23 / Android 13)",
    app_build="12.4.4.3_1606_android_nrspurple_build.apk · v6.4.13 · com.uzioapp.nrspurple "
              "· bs://e6d554c8c8ddec416f7cd62d8571a40a0114eac6",
    notes=(
        "Focused UI scope per developer instruction 2026-06-16 — NRS Purple flavor only. "
        "Credentials in secrets.yaml under credentials.nrspurple: "
        "EE=ein@ch.com (Ein Lname), Manager=ale@ch.com (Bale Lname), shared password Qwerty@12. "
        "Run command: pytest tests/jira/PHIX-86688 -v --suite PHIX-86688. "
        "Dropped from this run: cross-flavor regression (UZIO/TECHSERVE/...), SSO error path, "
        "network-log subdomain assertions, Kiosk consent text, server-unreachable edge — "
        "all of those need either separate builds, a different role, or features we don't have "
        "on BrowserStack Free."
    ),
)


if __name__ == "__main__":
    out = build_testcase_workbook(
        "reports/testcases/PHIX-86688_Testcases.xlsx",
        META, CASES,
    )
    print(f"[ok] wrote {out}  ({len(CASES)} cases)")
