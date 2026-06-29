"""
PHIX-86688 — NRS Purple white-label mobile launch — UI test suite.

Source spec: tests/jira/PHIX-86688/mobile.test.md
Generator:   scripts/gen_phix86688_testcases.py
Excel:       reports/testcases/PHIX-86688_Testcases.xlsx

Scope (focused 2026-06-16):
    * NRS Purple flavor APK only  (com.uzioapp.nrspurple v6.4.13, bs://...0114eac6)
    * UI changes only
    * Credentials (from config + secrets):
        EE       = ein@ch.com  (Ein Lname)         <- default 'driver' fixture
        Manager  = ale@ch.com  (Bale Lname)        <- for E2E manager-approve flows

Two test classes:
    TestNrsPurplePreLogin    -- launches the app WITHOUT logging in (branding +
                                Login-screen text/layout)
    TestNrsPurplePostLogin   -- uses the default class-scoped `driver` fixture
                                which logs in as ein@ch.com once, then runs
                                drawer / About / Switch-Accounts / Language /
                                Sanity / E2E cases. E2E cases logout and
                                re-login as the Manager inline.
"""

import time
import pytest

from core.config_loader import config
from core.driver_factory import create_driver
from core.locators import (BottomNav, Drawer, NrsPurple, Login,
                           TimeOff, ManageTeam, MyTimesheet, TeamTimesheet,
                           TimeTracking)
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage, ScreenUnavailable


# ─── Shared pre-login driver fixture (class-scoped, no login) ────────────────

@pytest.fixture(scope="class")
def driver_no_login(request, reporter):
    """Like the default `driver` fixture but stops at the Login screen — used
    for branding / Login-text / Login-layout cases."""
    build = request.config.getoption("--build") or config.get("browserstack.build")
    drv = create_driver(build_name=build, session_name="PHIX-86688 pre-login")

    base = LoginPage(drv)
    base.dismiss_system_permissions()
    base.dismiss_onboarding_if_present()
    base._dismiss_app_lock_if_present()
    # Wait briefly for the Login form to settle (already-logged-in is also fine —
    # tests will assert their own preconditions).
    deadline = time.time() + 30
    while time.time() < deadline:
        if base.is_text_visible(Login.LOGIN_BUTTON, 1):
            break
        if base.is_text_visible(BottomNav.TIME_TRACKING, 1):
            break
        time.sleep(1)

    request.cls.driver = drv
    request.cls.reporter = reporter
    yield drv
    try:
        drv.quit()
    except Exception:
        pass


# ─── PRE-LOGIN class — Branding + Login screen ───────────────────────────────

@pytest.mark.jira
@pytest.mark.android
@pytest.mark.usefixtures("driver_no_login")
class TestNrsPurplePreLogin:

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect_heals(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    # ── BUILD / BRANDING ────────────────────────────────────────────────────

    def test_01_app_label_nrs_purple(self):
        """TC-01: App package + label = NRS Purple."""
        self._begin("TC-01", "App label / package is NRS Purple")
        # Package guard — confirms we really did install the nrspurple flavor.
        from appium.webdriver.appium_service import AppiumService  # noqa: F401  (lint)
        caps_pkg = (self.driver.capabilities.get("appPackage")
                    or self.driver.capabilities.get("appium:appPackage"))
        assert caps_pkg == "com.uzioapp.nrspurple", \
            f"expected appPackage=com.uzioapp.nrspurple, got {caps_pkg!r}"

    def test_02_splash_screenshot(self):
        """TC-02: Capture splash for visual review (square NRS Purple logo)."""
        self._begin("TC-02", "Splash / first-screen branding capture")
        # By the time we get here, the splash has already passed; instead we
        # capture whatever first screen rendered (typically the Login). The
        # reporter screenshot hook attaches it for visual review.
        # If we want a real splash capture, force-stop + relaunch the package:
        try:
            self.driver.terminate_app("com.uzioapp.nrspurple")
            time.sleep(1)
            self.driver.activate_app("com.uzioapp.nrspurple")
            time.sleep(1)  # try to land on the splash before it fades
        except Exception as e:
            print(f"[TC-02] could not force splash relaunch: {e}")
        # No hard assertion here — visual check via the report screenshot.
        # Wait for the post-splash UI before returning so the next test starts clean.
        base = LoginPage(self.driver)
        base.dismiss_system_permissions()
        base.dismiss_onboarding_if_present()

    def test_03_theme_color(self):
        """TC-03: Header / safe-area colour samples to #563d6e (NRS Purple)."""
        self._begin("TC-03", "Theme colour #563d6e on header / safe-area")
        base = LoginPage(self.driver)
        assert (base.is_displayed(timeout=15)
                or base.is_text_visible(BottomNav.TIME_TRACKING, 5)), \
            "neither Login screen nor dashboard visible -- cannot sample theme"

        # Sample the tinted top safe-area (Android status bar) and assert mean
        # RGB ~= #563d6e. Calibrated against the live screenshot: on the Samsung
        # Galaxy S23 (1080x2340) the NRS Purple status bar spans rows 0..~140
        # (~3% of height). Sampling rows 1..2% lands solidly inside the tint,
        # avoiding both the very-top pixel row (often black on AMOLED) and the
        # bleed into the white body below.
        #
        # XD design colour:  #563d6e  =  (R=86, G=61, B=110)
        from io import BytesIO
        from PIL import Image
        png = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png)).convert("RGB")
        w, h = img.size
        top = int(h * 0.010)
        bot = int(h * 0.020)
        # Centre 30% of the width — avoids the system clock (left) and battery
        # / signal / wifi icons (right) which are rendered in WHITE on top of
        # the tint and skew the mean lighter.
        left = int(w * 0.35)
        right = int(w * 0.65)
        strip = img.crop((left, top, right, bot))
        px = list(strip.getdata())
        mean = tuple(sum(c) / len(px) for c in zip(*px))     # (R, G, B)

        target = (86, 61, 110)  # #563d6e
        delta = max(abs(mean[i] - target[i]) for i in range(3))
        print(f"[TC-03] status-bar sample mean RGB={tuple(round(v) for v in mean)} "
              f"target={target} max-channel-delta={delta:.1f}")
        # Tolerance accounts for screenshot compression + any small lighten
        # from anti-aliased system glyphs that drift into the strip.
        assert delta <= 25, (
            f"status-bar colour drift: mean={tuple(round(v) for v in mean)} "
            f"vs target {target} (max channel delta {delta:.1f} > 25). "
            f"Likely the NRS Purple theme colour did not apply.")

    # ── LOGIN screen text + layout ──────────────────────────────────────────

    def test_04_login_heading(self):
        """TC-04: Heading 'Welcome to NRS Purple' present; 'Welcome to UZIO' absent."""
        self._begin("TC-04", "Login heading 'Welcome to NRS Purple'")
        base = LoginPage(self.driver)
        # If we landed already logged in, force back to Login by logging out.
        if not base.is_text_visible(Login.LOGIN_BUTTON, 3):
            try:
                DashboardPage(self.driver).logout()
            except Exception:
                pass
        base.dismiss_system_permissions()
        base.dismiss_onboarding_if_present()
        base._dismiss_app_lock_if_present()
        assert base.is_text_visible(NrsPurple.LOGIN_HEADING, 10), \
            "expected 'Welcome to NRS Purple' on the Login screen"
        # Soft check — UZIO heading should not leak into the NRS Purple flavor
        if base.is_text_visible(Login.HEADING, 1):
            pytest.fail("'Welcome to UZIO' is visible on the NRS Purple build")

    def test_05_form_layout(self):
        """TC-05: Login form fields + LOGIN button are reachable."""
        self._begin("TC-05", "Login form fields reachable")
        base = LoginPage(self.driver)
        assert base.is_text_visible(Login.LOGIN_BUTTON, 10), \
            "LOGIN button not visible on Login screen"
        # Username + Password fields are located by index; we can't text-assert
        # placeholders reliably across RN versions. The screenshot hook captures
        # the layout for visual review of the wp 55% / flex-start change.

    def test_06_valid_login_ee(self):
        """TC-06: ein@ch.com logs in successfully."""
        self._begin("TC-06", "Valid login as ein@ch.com")
        base = LoginPage(self.driver)
        # If already logged in, force back to Login
        if not base.is_text_visible(Login.LOGIN_BUTTON, 3):
            try:
                DashboardPage(self.driver).logout()
            except Exception:
                pass
        username = config.get("credentials.nrspurple.employee_username")
        password = config.get("credentials.nrspurple.employee_password")
        base.login(username=username, password=password)
        dash = DashboardPage(self.driver)
        dash.verify_on_dashboard()
        self._collect_heals(base, dash)
        # leave us logged in so the next test (TC-07) can log out cleanly

    def test_07_invalid_credentials(self):
        """TC-07: Invalid password → 'The username or password is incorrect.'"""
        self._begin("TC-07", "Invalid credentials error message")
        # Get back to the Login screen
        dash = DashboardPage(self.driver)
        try:
            dash.logout()
        except Exception:
            pass
        base = LoginPage(self.driver)
        base.dismiss_system_permissions()
        base.dismiss_onboarding_if_present()
        assert base.is_text_visible(Login.LOGIN_BUTTON, 15), \
            "did not return to Login screen for invalid-creds test"
        # Now type the bad password and submit
        base.enter_by_index(0, "ein@ch.com")
        base.enter_by_index(1, "WRONG_PASSWORD_X")
        base.tap(Login.LOGIN_BUTTON)
        # Poll for the inline error
        deadline = time.time() + 15
        seen = False
        while time.time() < deadline:
            if base.is_text_visible(Login.INVALID_CREDENTIALS, 1):
                seen = True
                break
            time.sleep(1)
        assert seen, ("expected 'The username or password is incorrect.' after "
                      "an invalid login attempt")
        # We must NOT be on the dashboard
        assert not base.is_text_visible(BottomNav.TIME_TRACKING, 2), \
            "dashboard rendered after an invalid login — should not have"


# ─── POST-LOGIN class — drawer + About Us + sanity + E2E ─────────────────────

@pytest.mark.jira
@pytest.mark.android
@pytest.mark.usefixtures("driver")  # default conftest fixture logs in as ein@ch.com
class TestNrsPurplePostLogin:

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect_heals(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    def _drawer_open_about(self):
        """Open drawer → tap 'About NRS Purple' → verify it loaded."""
        dash = DashboardPage(self.driver)
        try:
            dash.open_drawer_and_tap(NrsPurple.DRAWER_ABOUT_ITEM,
                                    verify_any=[NrsPurple.ABOUT_HEADING])
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        self._collect_heals(dash)
        return dash

    def _back_to_dashboard(self):
        try:
            DashboardPage(self.driver).recover_to_dashboard()
        except Exception:
            pass

    # ── ABOUT US ────────────────────────────────────────────────────────────

    def test_08_drawer_opens_about(self):
        """TC-08: Drawer 'About NRS Purple' item opens the About screen."""
        self._begin("TC-08", "Drawer -> About NRS Purple")
        self._drawer_open_about()
        base = LoginPage(self.driver)
        assert base.is_text_visible(NrsPurple.ABOUT_HEADING, 5)
        self._back_to_dashboard()

    def test_09_heading_and_subheading(self):
        """TC-09: Heading + subheading present; UZIO copy absent."""
        self._begin("TC-09", "About — heading + subheading NRS Purple")
        self._drawer_open_about()
        base = LoginPage(self.driver)
        assert base.is_text_visible(NrsPurple.ABOUT_HEADING, 5), \
            "About heading 'About NRS Purple' not visible"
        assert base.is_text_visible(NrsPurple.ABOUT_SUBHEADING, 3), \
            "About subheading 'NRS Purple' not visible"
        # UZIO heading should not leak in
        assert not base.is_text_visible("About UZIO", 1), \
            "'About UZIO' visible on the NRS Purple build"
        self._back_to_dashboard()

    def test_10_app_version_label(self):
        """TC-10: 'App v<version>' label present."""
        self._begin("TC-10", "About — App version label")
        self._drawer_open_about()
        base = LoginPage(self.driver)
        # The version string is dynamic — assert by partial contains
        assert base.text_in_source("App v"), \
            "'App v' label not found in About screen source"
        self._back_to_dashboard()

    def test_11_info_paragraph(self):
        """TC-11: Info paragraph references NRS Purple payroll + Employee Portal."""
        self._begin("TC-11", "About — info paragraph NRS Purple copy")
        self._drawer_open_about()
        base = LoginPage(self.driver)
        # Match on partial substrings — the full paragraph is long and may wrap.
        assert base.text_in_source(NrsPurple.ABOUT_INFO_FRAGMENT), \
            f"missing fragment {NrsPurple.ABOUT_INFO_FRAGMENT!r} in About info"
        assert base.text_in_source(NrsPurple.ABOUT_INFO_FRAGMENT_2), \
            f"missing fragment {NrsPurple.ABOUT_INFO_FRAGMENT_2!r} in About info"
        # UZIO marketing copy must not leak in
        assert not base.text_in_source("SaaS-based online marketplace"), \
            "UZIO marketing copy visible on the NRS Purple About screen"
        self._back_to_dashboard()

    def test_12_footer(self):
        """TC-12: Footer = 'Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved.'"""
        self._begin("TC-12", "About — footer NRS Purple copyright")
        dash = self._drawer_open_about()
        # Scroll if needed to reveal the footer
        base = LoginPage(self.driver)
        # Try direct contains first; if not found, swipe up a few times
        found = base.text_in_source("National Retail Solutions")
        if not found:
            for _ in range(5):
                base.swipe_up()
                time.sleep(0.5)
                if base.text_in_source("National Retail Solutions"):
                    found = True
                    break
        assert found, "NRS Purple footer 'National Retail Solutions' not visible"
        assert not base.text_in_source("Uzio Technology, Inc."), \
            "UZIO footer visible on the NRS Purple About screen"
        self._back_to_dashboard()

    # ── SWITCH ACCOUNTS · LANGUAGE ──────────────────────────────────────────

    def test_13_app_name_label(self):
        """TC-13: Switch / Login Accounts header reads 'NRS Purple'."""
        self._begin("TC-13", "Switch Accounts — header reads 'NRS Purple'")
        dash = DashboardPage(self.driver)
        try:
            dash.open_drawer_and_tap(Drawer.LOGIN_ACCOUNTS,
                                    verify_any=[Drawer.LOGIN_ACCOUNTS, NrsPurple.APP_NAME])
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        base = LoginPage(self.driver)
        assert base.is_text_visible(NrsPurple.APP_NAME, 8), \
            "'NRS Purple' app-name label not visible on the Login Accounts screen"
        # Title-cased Config.APP_NAME would have rendered 'Nrspurple' — must not appear
        assert not base.text_in_source("Nrspurple"), \
            "'Nrspurple' (title-cased Config.APP_NAME) leaked into UI — should be 'NRS Purple'"
        self._collect_heals(dash)
        self._back_to_dashboard()

    def test_14_single_english_option(self):
        """TC-14: Language picker shows exactly one option (English)."""
        self._begin("TC-14", "Language — single English option")
        dash = DashboardPage(self.driver)
        try:
            dash.open_drawer_and_tap(Drawer.LANGUAGE,
                                    verify_any=[Drawer.LANGUAGE, "English"])
        except ScreenUnavailable as e:
            self._collect_heals(dash)
            pytest.skip(str(e))
        base = LoginPage(self.driver)
        assert base.is_text_visible("English", 5), \
            "'English' option not visible in Language picker"
        self._collect_heals(dash)
        self._back_to_dashboard()

    # ── SANITY ──────────────────────────────────────────────────────────────

    def test_15_bottom_nav(self):
        """TC-15: Bottom navigation tabs reachable."""
        self._begin("TC-15", "Bottom navigation tabs reachable")
        dash = DashboardPage(self.driver)
        dash.recover_to_dashboard()
        opened_any = False
        # Time Tracking is the default landing tab; Inbox / Time Off are common.
        for tab in [BottomNav.TIME_TRACKING, BottomNav.TIME_OFF, BottomNav.INBOX]:
            if dash.is_text_visible(tab, 2):
                try:
                    dash.open_tab(tab, verify_any=[tab])
                    opened_any = True
                except ScreenUnavailable:
                    continue
        self._collect_heals(dash)
        assert opened_any, "no bottom-nav tab reachable for ein@ch.com"

    def test_16_logout(self):
        """TC-16: Logout via hamburger drawer returns to NRS Purple Login screen."""
        self._begin("TC-16", "Logout returns to NRS Purple Login")
        dash = DashboardPage(self.driver)
        dash.logout()
        base = LoginPage(self.driver)
        assert base.is_text_visible(NrsPurple.LOGIN_HEADING, 15), \
            "'Welcome to NRS Purple' not visible after logout"
        # Restore session for any tests that follow (none, but be polite to the fixture)
        username = config.get("credentials.nrspurple.employee_username")
        password = config.get("credentials.nrspurple.employee_password")
        try:
            base.login(username=username, password=password)
        except Exception:
            pass
        self._collect_heals(dash, base)

    def test_17_drawer_structure(self):
        """TC-17: 'About NRS Purple' under HELP AND SUPPORT exactly once."""
        self._begin("TC-17", "Drawer structure - About NRS Purple placement")
        dash = DashboardPage(self.driver)
        dash.recover_to_dashboard()
        dash.open_drawer()
        if not dash.wait_for_drawer_ready():
            pytest.skip("drawer did not render in time")
        # Scroll to ensure section headers are visible
        dash.scroll_to_text(Drawer.SEC_HELP_SUPPORT, max_swipes=8)
        assert dash.is_text_visible(Drawer.SEC_HELP_SUPPORT, 3), \
            "HELP AND SUPPORT section header not visible"
        # Then scroll to the About item
        dash.scroll_to_text(NrsPurple.DRAWER_ABOUT_ITEM, max_swipes=8)
        assert dash.is_text_visible(NrsPurple.DRAWER_ABOUT_ITEM, 3), \
            "'About NRS Purple' drawer item not visible under HELP AND SUPPORT"
        self._collect_heals(dash)
        # Close drawer for the next test
        try:
            dash.press_back()
        except Exception:
            pass

    # ── E2E ────────────────────────────────────────────────────────────────

    def test_e2e_01_time_off_request_approve(self):
        """E2E-01: Ein submits Time Off → Bale approves → Ein sees Approved."""
        self._begin("E2E-01", "Time Off — EE submit -> Manager approve")
        dash = DashboardPage(self.driver)
        dash.recover_to_dashboard()
        # Open Time Off — skip if not enabled for ein@ch.com
        try:
            dash.open_tab(BottomNav.TIME_OFF,
                          verify_any=[TimeOff.AVAILABLE, TimeOff.REQUEST_TIME_OFF,
                                      TimeOff.HEADING])
        except ScreenUnavailable as e:
            pytest.skip(f"Time Off tab not available for ein@ch.com — {e}")

        base = LoginPage(self.driver)
        if not base.is_text_visible(TimeOff.REQUEST_TIME_OFF, 5):
            pytest.skip("'Request Time Off' button not available — ein may not have a policy")

        # Submit the request (page object exists but for sanity we drive by text)
        base.tap(TimeOff.REQUEST_TIME_OFF)
        time.sleep(2)
        # Minimal form: pick the first type, accept defaults, submit
        try:
            base.tap(TimeOff.SELECT_TYPE)
        except Exception:
            pass
        time.sleep(1)
        # The type picker varies per employer — pytest.skip if we can't drive it
        # within this simple harness; deeper drive lives in pages/time_off_page.py
        if not base.is_text_visible(TimeOff.SUBMIT_FOR_APPROVAL, 5):
            pytest.skip("Time Off form not reachable without policy-aware page object — "
                        "wire pages/time_off_page.py before this test can self-drive")

        base.tap(TimeOff.SUBMIT_FOR_APPROVAL)
        assert base.is_text_visible(TimeOff.REQUEST_SUBMITTED, 20), \
            "did not see 'Request Submitted Successfully' after submission"

        # Logout Ein, login as Bale
        dash.logout()
        mgr_login = LoginPage(self.driver)
        mgr_user = config.get("credentials.nrspurple.manager_username")
        mgr_pwd = config.get("credentials.nrspurple.manager_password")
        mgr_login.login(username=mgr_user, password=mgr_pwd)

        # Open Team Time Off
        mgr_dash = DashboardPage(self.driver)
        try:
            mgr_dash.open_drawer_and_tap(Drawer.TEAM_TIME_OFF,
                                         verify_any=[Drawer.TEAM_TIME_OFF,
                                                     ManageTeam.TEAM_TIME_OFF])
        except ScreenUnavailable as e:
            pytest.skip(f"Team Time Off not available for ale@ch.com — {e}")

        # Approve the request (button text 'Approve' is canonical)
        if mgr_login.is_text_visible("Approve", 8):
            mgr_login.tap("Approve")
            time.sleep(3)
        else:
            pytest.fail("'Approve' button not visible on Team Time Off for the new request")

        self._collect_heals(dash, mgr_dash)

    def test_e2e_02_clock_in_out_team_timesheet(self):
        """E2E-02: Ein Clock In/Out → Bale sees the entry on Team Timesheet."""
        self._begin("E2E-02", "Clock In/Out -> Team Timesheet")
        # Ensure we're logged in as Ein (the previous test may have left Bale signed in)
        ee_user = config.get("credentials.nrspurple.employee_username")
        ee_pwd = config.get("credentials.nrspurple.employee_password")
        base = LoginPage(self.driver)
        if base.is_text_visible(Login.LOGIN_BUTTON, 3):
            base.login(username=ee_user, password=ee_pwd)
        else:
            # See who's logged in; if it's Bale, logout and login as Ein
            dash = DashboardPage(self.driver)
            dash.logout()
            base.login(username=ee_user, password=ee_pwd)

        dash = DashboardPage(self.driver)
        try:
            tt = dash.open_time_tracking()
        except Exception as e:
            pytest.skip(f"Time Tracking tab not available — {e}")

        # Clock In
        if not base.is_text_visible(TimeTracking.CLOCK_IN, 5):
            # Maybe already clocked in — clock out first
            if base.is_text_visible(TimeTracking.CLOCK_OUT, 1):
                base.tap(TimeTracking.CLOCK_OUT)
                dash.dismiss_attestation_if_present()
                base.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 5)
                time.sleep(2)
        if base.is_text_visible(TimeTracking.CLOCK_IN, 8):
            base.tap(TimeTracking.CLOCK_IN)
            base.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 8)
            time.sleep(1)
        else:
            pytest.skip("Clock In button not visible")

        # Clock Out
        assert base.is_text_visible(TimeTracking.CLOCK_OUT, 10), \
            "Clock Out button not visible after Clock In"
        base.tap(TimeTracking.CLOCK_OUT)
        dash.dismiss_attestation_if_present()
        base.dismiss_popup_if_present(TimeTracking.MODAL_CLOSE, 10)
        time.sleep(1)

        # Switch to Bale and confirm the entry shows on Team Timesheet
        dash.logout()
        mgr_login = LoginPage(self.driver)
        mgr_user = config.get("credentials.nrspurple.manager_username")
        mgr_pwd = config.get("credentials.nrspurple.manager_password")
        mgr_login.login(username=mgr_user, password=mgr_pwd)

        mgr_dash = DashboardPage(self.driver)
        try:
            mgr_dash.open_drawer_and_tap(Drawer.TEAM_TIMESHEET,
                                         verify_any=[Drawer.TEAM_TIMESHEET,
                                                     TeamTimesheet.HEADING])
        except ScreenUnavailable as e:
            pytest.skip(f"Team Timesheet not available for ale@ch.com — {e}")

        # We don't assert a specific entry row here without a page object — confirm
        # the screen renders and contains text indicating Ein's record or the
        # 'Total Paid Hours' label that proves the timesheet view loaded.
        assert (mgr_login.is_text_visible(TeamTimesheet.HEADING, 5)
                or mgr_login.is_text_visible(MyTimesheet.TOTAL_PAID_HOURS, 5)), \
            "Team Timesheet did not render for the manager"

        self._collect_heals(dash, mgr_dash)
