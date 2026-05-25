"""
Login screen page object.

UzioMobile login (src/screens/Login/Login.tsx):
  - Username field placeholder: "Username (Email Address)"
  - Password field placeholder: "Password"  (same placeholder pattern — locate by index)
  - Login button: "LOGIN" (uppercased)
  - No testIDs — both fields share placeholder text, so we enter by field index.
"""

import time
from core.base_page import BasePage
from core.config_loader import config
from core.locators import Login


class LoginPage(BasePage):

    def is_displayed(self, timeout=10):
        return (self.is_text_visible(Login.LOGIN_BUTTON, timeout)
                or self.is_text_visible(Login.HEADING, 2)
                or self.is_text_visible(Login.USERNAME_PLACEHOLDER, 2))

    def is_already_logged_in(self):
        """
        True only if we're past the login screen AND on the real app shell.
        HEALED 2026-05-24: the onboarding carousel has a slide titled "Benefits"
        that collides with BottomNav.BENEFITS, causing a false "logged in" result.
        Guard against it: if the LOGIN button is visible we are NOT logged in.
        Also require a tab that does NOT appear as carousel slide text.
        """
        # If the login form is on screen, we are definitely not logged in.
        if self.is_text_visible(Login.LOGIN_BUTTON, 1):
            return False
        from core.locators import BottomNav
        # Inbox / Time Off / Time Tracking are real tabs, not carousel slide titles.
        indicators = [BottomNav.TIME_TRACKING, BottomNav.TIME_OFF, BottomNav.INBOX]
        for ind in indicators:
            if self.is_text_visible(ind, 2):
                print(f"[LoginPage] Already logged in (saw tab: {ind})")
                return True
        return False

    def login(self, username=None, password=None):
        username = username or config.credential("employee_username")
        password = password or config.credential("employee_password")
        if not username or not password:
            raise RuntimeError(f"Missing credentials for env={config.environment} "
                               f"(check config.yaml + secrets.yaml)")

        print(f"[LoginPage] Logging in as {username}")
        # HEALED 2026-05-23: app shows a native notification-permission dialog on
        # launch ("Allow Uzio to send you notifications?") that blocks the login
        # screen. Dismiss any system permission dialogs before locating LOGIN.
        self.dismiss_system_permissions()

        # HEALED 2026-05-23: after the permission dialog the app shows a one-time
        # feature-walkthrough carousel (Benefits/… slides with a "Skip" button).
        # With no_reset=true the session is retained, so the user is already logged
        # in behind the walkthrough — skip it, then go straight to the dashboard.
        self.dismiss_onboarding_if_present()

        # HEALED 2026-05-24: a cold start (esp. after a force-stop) can take 10-15s
        # to render, and a logged-in session may surface the "Enable App Lock" prompt
        # + location permission first. Rather than check once and then commit to
        # waiting for LOGIN, POLL for EITHER outcome — dashboard (already logged in)
        # OR the login screen — clearing prompts each iteration. No BACK presses here
        # (those risk exiting the app); ensure_app_foreground keeps UZIO in front.
        from pages.dashboard_page import DashboardPage
        deadline = time.time() + max(60, config.timeout("login"))
        while time.time() < deadline:
            self.ensure_app_foreground()
            self.dismiss_system_permissions(rounds=1)
            self._dismiss_app_lock_if_present()
            self.dismiss_onboarding_if_present(rounds=1)
            if self.is_already_logged_in():
                print("[LoginPage] Already logged in — on dashboard")
                return DashboardPage(self.driver)
            if self.is_text_visible(Login.LOGIN_BUTTON, 1):
                break
            time.sleep(1)
        else:
            raise TimeoutError(
                "[LoginPage] Neither dashboard nor login screen appeared after wait")

        # Both fields share the placeholder; enter by index (0=username, 1=password)
        try:
            self.enter_by_index(0, username)
            self.enter_by_index(1, password)
        except Exception:
            # Fallback: try placeholder-based entry
            self.enter(Login.USERNAME_PLACEHOLDER, username)
            self.enter(Login.PASSWORD_PLACEHOLDER, password)

        self.tap(Login.LOGIN_BUTTON)
        self._wait_for_login_result()

        from pages.dashboard_page import DashboardPage
        return DashboardPage(self.driver)

    def _dismiss_app_lock_if_present(self):
        """
        HEALED 2026-05-24: after login the app shows an "Enable App Lock" prompt.
        Tap "I'll do it later" to dismiss and reach the dashboard.

        Match on apostrophe-free substrings via contains() — a literal "I'll do it
        later" in an XPath breaks the parser because the ' terminates the string.
        Substrings like "do it later" sidestep the apostrophe entirely.
        """
        # apostrophe-free fragments that uniquely identify the dismiss button
        fragments = ["do it later", "Do it later", "Not now", "Not Now",
                     "Maybe later", "Later", "Skip"]
        for frag in fragments:
            els = self.driver.find_elements(
                "xpath",
                f"//*[contains(@text,\"{frag}\") or contains(@content-desc,\"{frag}\") "
                f"or contains(@name,\"{frag}\") or contains(@label,\"{frag}\")]")
            if els:
                els[0].click()
                print(f"[LoginPage] dismissed App Lock prompt (matched: '{frag}')")
                time.sleep(1)
                return True
        return False

    def _wait_for_login_result(self):
        from core.locators import BottomNav
        deadline = time.time() + config.timeout("login")
        while time.time() < deadline:
            if self.is_text_visible(Login.INVALID_CREDENTIALS, 1):
                raise AssertionError("[LoginPage] Login failed — invalid credentials message shown")
            # HEALED 2026-05-23: a location-permission dialog ("Allow Uzio to access
            # this device's location?") and post-login coachmarks appear AFTER login
            # and block the bottom-nav tabs. Clear them while polling for the landing.
            self.dismiss_system_permissions(rounds=1)
            # HEALED 2026-05-24: "Enable App Lock" prompt appears post-login.
            self._dismiss_app_lock_if_present()
            self.dismiss_onboarding_if_present(rounds=1)
            if (self.is_text_visible(BottomNav.TIME_TRACKING, 1)
                    or self.is_text_visible(BottomNav.BENEFITS, 1)
                    or self.is_text_visible(BottomNav.TIME_OFF, 1)
                    or self.is_text_visible(BottomNav.INBOX, 1)
                    or self.is_text_visible(BottomNav.SCHEDULE, 1)):
                print("[LoginPage] Login successful")
                return
            time.sleep(1)
        raise TimeoutError("[LoginPage] No landing screen detected after login")
