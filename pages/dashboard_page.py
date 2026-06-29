"""
Dashboard / main-shell page object.

UzioMobile has NO Home or Profile bottom tab. The bottom nav is feature-gated:
  Benefits | Schedule | Time Tracking (default landing) | Time Off | Inbox

Profile/account actions (including Logout) live in a SIDE DRAWER opened by the
hamburger icon (Ionicon 'menu-sharp') in the top-left of the header bar.
Logout fires immediately — there is NO confirmation dialog.
"""

import time
from appium.webdriver.common.appiumby import AppiumBy
from core.base_page import BasePage
from core.locators import BottomNav, Attestation, Drawer


class ScreenUnavailable(Exception):
    """Raised when a tab/drawer screen isn't present for the current employer
    (feature-gated). Tests catch this and skip rather than fail."""


class DashboardPage(BasePage):

    LANDING_INDICATORS = [BottomNav.TIME_TRACKING, BottomNav.BENEFITS, BottomNav.TIME_OFF]

    # ─── Navigation ───────────────────────────────────────────────────────────

    def dismiss_blocking_dialogs(self):
        """
        HEALED 2026-05-25: on BrowserStack the location-permission dialog ("Allow Uzio
        to access this device's location? / While using the app") appears AFTER login
        completes (lazily, when the Time Tracking screen requests location) and covers
        the bottom nav bar — so the 'Time Tracking' tab can't be found. Dismiss OS
        permission dialogs + lingering modals at every nav entry point, not just login.
        """
        self.dismiss_system_permissions(rounds=2)   # location: While using the app / Allow
        self.dismiss_popup_if_present("Close", 1)

    def open_time_tracking(self):
        # HEALED 2026-05-23: close any lingering confirmation modal ("You are
        # Clocked In/Out" → "Close") that could overlay the bottom nav.
        self.dismiss_blocking_dialogs()
        self.dismiss_attestation_if_present()
        self.tap(BottomNav.TIME_TRACKING)
        self.wait_for_text(BottomNav.TIME_TRACKING, 10)
        from pages.time_tracking_page import TimeTrackingPage
        return TimeTrackingPage(self.driver)

    def open_time_off(self):
        self.tap(BottomNav.TIME_OFF)
        from pages.time_off_page import TimeOffPage
        return TimeOffPage(self.driver)

    def open_benefits(self):
        self.tap(BottomNav.BENEFITS)

    def open_inbox(self):
        self.tap(BottomNav.INBOX)

    def open_schedule(self):
        self.tap(BottomNav.SCHEDULE)

    def verify_on_dashboard(self):
        self.dismiss_blocking_dialogs()
        for ind in self.LANDING_INDICATORS:
            if self.is_text_visible(ind, 5):
                print(f"[DashboardPage] On dashboard (saw: {ind})")
                return
        raise AssertionError("[DashboardPage] Landing screen not detected")

    # ─── Generic navigation helpers (sanity screen-load smoke) ──────────────────

    # Stable anchors that prove the drawer list has finished rendering.
    DRAWER_ANCHORS = ["Logout", "MANAGE TEAM", "TIME AND ATTENDANCE", "PAY",
                      "Pay Stubs", "My Timesheet", "Contact Support"]

    def open_tab(self, tab_text, verify_any=None, timeout=10):
        """
        Recover to the shell, tap a bottom-nav tab, and verify the screen loaded.

        verify_any: list of texts — pass if ANY is visible (screens vary by data,
        e.g. an empty Time Off may show "Request Time Off" but no balances).
        Raises ScreenUnavailable if the tab isn't present (feature-gated → test skips).
        """
        if not self.recover_to_dashboard():
            raise ScreenUnavailable("could not reach main shell to open tab")
        self.dismiss_popup_if_present("Close", 1)
        if not self.is_text_visible(tab_text, 3):
            raise ScreenUnavailable(f"tab '{tab_text}' not available for this employer")
        self.tap(tab_text)
        time.sleep(1.5)
        checks = verify_any or [tab_text]
        for txt in checks:
            if self.is_text_visible(txt, timeout):
                print(f"[DashboardPage] tab '{tab_text}' loaded (saw: {txt})")
                return True
        raise AssertionError(
            f"[DashboardPage] tab '{tab_text}' did not load. Expected any of: {checks}")

    def wait_for_drawer_ready(self, timeout=8):
        """Poll until the drawer list has rendered (a known anchor is visible)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            for anchor in self.DRAWER_ANCHORS:
                if self.is_text_visible(anchor, 1):
                    return True
            time.sleep(0.5)
        return False

    def open_drawer_and_tap(self, item_text, verify_any=None, max_swipes=10, timeout=15):
        """
        Recover to the shell, open the drawer, wait for it to fully render, scroll to
        the menu item, tap it EXACTLY, and verify the destination loaded.

        - Waits for render BEFORE scrolling (avoids scrolling past upper items while
          the list is still lazy-loading).
        - Uses tap_exact so a missing item never partial-heals to the wrong element.
        - Raises ScreenUnavailable if the item isn't in the drawer (feature-gated →
          the test skips instead of failing), and closes the drawer first.
        """
        if not self.recover_to_dashboard():
            raise ScreenUnavailable("could not reach main shell to open drawer")
        self.dismiss_popup_if_present("Close", 1)
        self.open_drawer()
        if not self.wait_for_drawer_ready():
            # Retry once: maybe the drawer half-opened. safe_press_back closes it
            # without risking an app exit.
            print("[DashboardPage] drawer not ready — closing and retrying once")
            self.safe_press_back()
            time.sleep(1)
            if not self.recover_to_dashboard():
                raise ScreenUnavailable("could not reach main shell to open drawer")
            self.open_drawer()
            if not self.wait_for_drawer_ready():
                raise AssertionError("[DashboardPage] drawer did not render in time")
        # HEALED 2026-05-24: the drawer RETAINS its scroll position between opens, so
        # an item near the top (e.g. Team Timesheet) may be scrolled out of view when
        # reopened. Reset to the top first, then scroll down to find the item.
        for _ in range(4):
            self.swipe_down()
        time.sleep(0.5)
        # Scroll the item into view (no-op if already visible at top).
        self.scroll_to_text(item_text, max_swipes=max_swipes)
        if not self.is_text_visible(item_text, 1):
            # Not present for this employer — close the drawer and signal skip.
            self.press_back()
            raise ScreenUnavailable(
                f"drawer item '{item_text}' not available for this employer")
        self.tap_exact(item_text)
        time.sleep(1.5)
        checks = verify_any or [item_text]
        for txt in checks:
            if self.is_text_visible(txt, timeout):
                print(f"[DashboardPage] drawer item '{item_text}' loaded (saw: {txt})")
                return True
        raise AssertionError(
            f"[DashboardPage] drawer item '{item_text}' did not load. "
            f"Expected any of: {checks}")

    # ─── Drawer (hamburger menu) ──────────────────────────────────────────────

    def open_drawer(self):
        """
        Open the side drawer via the hamburger icon. The icon has no text label,
        so we try several locator strategies.
        """
        # Try by accessibility / content-desc first (works on both platforms).
        # iOS exposes RN accessibilityLabel as @name/@label; Android as @content-desc.
        candidates = [
            (AppiumBy.ACCESSIBILITY_ID, "menu-sharp"),
            (AppiumBy.ACCESSIBILITY_ID, "menu"),
            (AppiumBy.ACCESSIBILITY_ID, "Menu"),
            (AppiumBy.ACCESSIBILITY_ID, "Open navigation menu"),
            (AppiumBy.XPATH, "//*[@content-desc='menu' or @content-desc='Menu' "
                             "or @content-desc='Open navigation menu' "
                             "or contains(@content-desc,'menu')]"),
            # iOS: name/label variants for the Ionicon hamburger
            (AppiumBy.XPATH, "//*[@name='menu-sharp' or @name='menu' or @name='Menu' "
                             "or @label='menu-sharp' or @label='menu' or @label='Menu' "
                             "or contains(@name,'menu')]"),
        ]
        for by, val in candidates:
            try:
                els = self.driver.find_elements(by, val)
                if els:
                    els[0].click()
                    print(f"[DashboardPage] Opened drawer via {by}={val}")
                    time.sleep(1.5)
                    return
            except Exception:
                continue
        # Fallback: tap top-left header region where the hamburger sits.
        # HEALED 2026-05-23: page source shows hamburger at ~11% width, ~10% height
        # (bounds [68,173][177,239] on Samsung Galaxy S23 1080x2115 canvas).
        # Previous 7%/6% landed above the icon — bumped up to 11%/10%.
        # SAFETY (HEALED 2026-05-24): NEVER blind-tap coordinates unless we're inside
        # UZIO on the main shell — otherwise the tap can hit a launcher icon / another
        # app (e.g. it once launched a weather app). Refuse and signal recovery failure.
        if not self.in_app():
            self.ensure_app_foreground()
            raise ScreenUnavailable("not in UZIO app — refusing blind hamburger tap")
        if not self._on_main_shell():
            raise ScreenUnavailable(
                "hamburger not available (not on main shell) — refusing blind tap")
        size = self.driver.get_window_size()
        # Platform-aware hamburger position. Android (Samsung S23) measured at
        # 11%/10%. iOS (HEALED 2026-05-25): iPhone uses point-based logical coords
        # (not pixels) and the nav bar sits below the notch/Dynamic Island safe area,
        # so the icon is higher in % terms — ~7%/7%. CALIBRATE on first iOS run via
        # the drawer page-source dump (.tmp/drawer_page_source.xml) like we did for
        # Android; override here or in config.app.hamburger.* if needed.
        if self.is_ios:
            hx, hy = 0.07, 0.07
        else:
            hx, hy = 0.11, 0.10
        self.tap_at(int(size["width"] * hx), int(size["height"] * hy))
        print(f"[DashboardPage] Opened drawer via top-left tap fallback "
              f"({'iOS' if self.is_ios else 'Android'} {hx:.0%}/{hy:.0%})")
        time.sleep(1.5)
        # Diagnostic: dump page source to a tmp file so we can inspect drawer contents
        try:
            src = self.driver.page_source
            import pathlib
            dump_path = pathlib.Path(".tmp") / "drawer_page_source.xml"
            dump_path.parent.mkdir(exist_ok=True)
            # Write as UTF-8 bytes — avoids Windows cp1252 codec issues
            dump_path.write_bytes(src.encode("utf-8", errors="replace"))
            print(f"[DashboardPage] Drawer page source dumped -> {dump_path} ({len(src)} chars)")
        except Exception as e:
            print(f"[DashboardPage] Page source dump failed: {e}")

    def logout(self):
        self.dismiss_attestation_if_present()
        # HEALED 2026-05-24: ensure we're on the main shell first — the hamburger
        # only exists there; on a pushed sub-screen the top-left is a back arrow.
        self.recover_to_dashboard()
        self.open_drawer()
        # Try several logout label variants used across PROD/QA builds
        logout_candidates = [
            Drawer.LOGOUT,         # "Logout"
            "Log Out",
            "Log out",
            "LOG OUT",
            "Sign Out",
            "Sign out",
        ]
        # Search without swiping first (avoid accidentally closing the drawer)
        tapped = False
        for label in logout_candidates:
            if self.is_text_visible(label, 3):
                self.tap(label)
                tapped = True
                print(f"[DashboardPage] Tapped logout via label: '{label}'")
                break
        if not tapped:
            # Not visible yet — scroll down within drawer then retry.
            # QA build drawer is long (Manage Team / Pay / W-2 …); Logout sits at the
            # very bottom, so allow more swipes.
            for _ in range(6):
                self.swipe_up()
                for label in logout_candidates:
                    if self.is_text_visible(label, 1):
                        self.tap(label)
                        tapped = True
                        print(f"[DashboardPage] Tapped logout (after scroll) via label: '{label}'")
                        break
                if tapped:
                    break
        if not tapped:
            raise AssertionError(
                f"[DashboardPage] Logout button not found in drawer. "
                f"Tried: {logout_candidates}. Check .tmp/drawer_page_source.xml")
        # HEALED 2026-05-24: a logout confirmation dialog may appear; confirm it.
        # Check specific dialog buttons first so we don't re-tap the drawer's Logout.
        for confirm in ["Yes", "Confirm", "OK", "Log Out", "Logout"]:
            if self.dismiss_popup_if_present(confirm, 1):
                break
        # HEALED 2026-05-24: after logout the QA build returns to the 3-screen
        # onboarding carousel (not directly to LOGIN). Dismiss it, then wait.
        self.dismiss_onboarding_if_present()
        # Wait for the login screen (logout makes a network call + carousel re-render).
        from core.locators import Login
        self.wait_for_text(Login.LOGIN_BUTTON, 30)
        print("[DashboardPage] Logged out")
        from pages.login_page import LoginPage
        return LoginPage(self.driver)

    # ─── Attestation / popup handling ──────────────────────────────────────────

    def dismiss_attestation_if_present(self):
        """
        Handle the MissedBreakSelectModal (time-attestation popup) if present.
        Fills the confirmation and submits so the flow can continue.
        """
        present = any(self.is_text_visible(ind, 1) for ind in Attestation.INDICATORS)
        if not present:
            return False
        print("[DashboardPage] Attestation modal detected — resolving")
        # Try to tap the confirmation checkbox. The element may not be directly tappable
        # (RN custom checkbox where the label is a separate text node from the toggle).
        # Tolerate any failure — the submit button is what actually completes the dismissal.
        try:
            if self.is_text_visible(Attestation.CONFIRM_CHECKBOX, 1):
                self.tap(Attestation.CONFIRM_CHECKBOX)
        except Exception as e:
            print(f"[DashboardPage] Attestation checkbox tap failed (ignoring): {e}")
        # Pick the 'freely chose not to take break' option if present
        try:
            self.dismiss_popup_if_present(Attestation.OPTION_FREELY_CHOSE, 1)
        except Exception:
            pass
        # Submit
        if self.is_text_visible(Attestation.SAVE_AND_CLOCK_OUT, 2):
            self.tap(Attestation.SAVE_AND_CLOCK_OUT)
            print("[DashboardPage] Attestation submitted (Save and Clock Out)")
        time.sleep(1)
        return True

    # Bottom-nav tab labels — 2+ visible together means we're on the main shell
    # (the nav bar), not a pushed sub-screen (which has a back arrow, no nav bar).
    _NAV_TABS = ["Benefits", "Schedule", "Time Tracking", "Time Off", "Inbox"]

    def _on_main_shell(self):
        """True if the bottom nav bar is present (>=2 tab labels in the page source).

        A single landing-indicator can appear as a heading inside a sub-screen, so
        we require multiple tabs together to reliably distinguish the main shell.
        """
        try:
            src = self.driver.page_source
        except Exception:
            return False
        return sum(1 for t in self._NAV_TABS if t in src) >= 2

    def recover_to_dashboard(self, max_presses=4):
        """Return to the main tab shell (where the hamburger lives) by closing any
        pushed sub-screen / open drawer with BACK until the bottom nav bar is shown.

        SAFETY: never backs out of the UZIO app. Uses safe_press_back, which detects
        if BACK exited to the launcher/another app, reactivates UZIO, and stops."""
        self.ensure_app_foreground()
        self.dismiss_attestation_if_present()
        self.dismiss_blocking_dialogs()   # clear location/permission dialogs covering nav
        for i in range(max_presses):
            if self._on_main_shell():
                if i:
                    print(f"[DashboardPage] Back on main shell after {i} presses")
                return True
            if not self.safe_press_back():
                # BACK left the app; we've reactivated it. Don't keep backing out —
                # dismiss any blocker the relaunch surfaced and re-check once.
                self.dismiss_system_permissions(rounds=1)
                self.dismiss_popup_if_present("Close", 1)
                break
            time.sleep(0.6)
        ok = self._on_main_shell()
        if not ok:
            print(f"[DashboardPage] Could not reach main shell after {max_presses} presses")
        return ok
