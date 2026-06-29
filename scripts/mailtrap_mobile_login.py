"""
Drive mobile Chrome on the connected phone (4ce254ab) to login to Mailtrap
and reach the Dev01/Teamadmin sandbox inbox.

After this completes, the phone Chrome holds a logged-in Mailtrap session
that PHIX-86688 email→deep-link tests can reuse without further login.

Run:
    python -m scripts.mailtrap_mobile_login
"""

import time
from pathlib import Path

import yaml
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


SHOTS = Path(".tmp/mt_mobile")
SHOTS.mkdir(parents=True, exist_ok=True)


def _shot(drv, label):
    try:
        path = SHOTS / f"{label}.png"
        drv.save_screenshot(str(path))
        print(f"  [shot] {path}")
    except Exception as e:
        print(f"  [shot fail] {e}")


def _creds():
    s = yaml.safe_load(open("config/secrets.yaml", encoding="utf-8"))
    mt = s.get("mailtrap", {})
    return mt.get("username"), mt.get("password")


def _find(drv, *selectors, timeout=10):
    """Find the first element matching ANY of the given (by, value) pairs."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for by, val in selectors:
            try:
                els = drv.find_elements(by, val)
                if els:
                    return els[0]
            except Exception:
                pass
        time.sleep(0.5)
    return None


def main():
    user, pwd = _creds()
    if not user or not pwd:
        raise SystemExit("No mailtrap creds in secrets.yaml")

    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.udid = "4ce254ab"
    opts.no_reset = True
    opts.app_package = "com.android.chrome"
    opts.app_activity = "com.google.android.apps.chrome.Main"
    opts.new_command_timeout = 120

    drv = webdriver.Remote("http://localhost:4723", options=opts)
    print("[ok] Chrome session started")
    time.sleep(2)

    try:
        # 1) Navigate to the Teamadmin sandbox messages URL directly.
        # If we already have a session, this loads. Otherwise it bounces to /signin.
        target = "https://mailtrap.io/sandboxes/2177958/messages"
        # Tap the URL bar and type the target
        url_bar = _find(drv,
                        (AppiumBy.ID, "com.android.chrome:id/url_bar"),
                        (AppiumBy.XPATH, "//*[contains(@resource-id,'url_bar')]"),
                        timeout=10)
        if not url_bar:
            print("[err] could not find URL bar")
            _shot(drv, "no-url-bar")
            return
        url_bar.click()
        time.sleep(1)
        # Clear + type
        url_bar.clear()
        url_bar.send_keys(target + "\n")
        time.sleep(4)
        _shot(drv, "01-after-nav")
        cur = url_bar.text or drv.current_activity
        print(f"  current url-bar text: {cur!r}")

        # 2) Detect whether we landed on signin or on the inbox.
        # The URL bar usually shows the short host, not full path. Read page text.
        page = drv.page_source or ""
        if "Sign in to your Mailtrap account" in page or "/signin" in page.lower() \
                or "Welcome to Mailtrap" in page:
            print("[note] not logged in — signin required")
            _shot(drv, "02-signin-page")

            # 3) Two-step login: enter email, tap Next, enter password, tap Sign in
            email_in = _find(drv,
                             (AppiumBy.XPATH,
                              "//android.widget.EditText[@text='Email' or contains(@hint,'mail')]"),
                             (AppiumBy.XPATH, "//android.widget.EditText"),
                             timeout=15)
            if email_in:
                email_in.click()
                email_in.clear()
                email_in.send_keys(user)
                _shot(drv, "03-email-typed")
                # Next button
                next_btn = _find(drv,
                                 (AppiumBy.XPATH,
                                  "//android.view.View[@text='Next']"),
                                 (AppiumBy.XPATH,
                                  "//android.widget.Button[@text='Next']"),
                                 timeout=5)
                if next_btn:
                    next_btn.click()
                    time.sleep(2)
                else:
                    # Press IME enter
                    drv.execute_script("mobile: performEditorAction", {"action": "go"})
                    time.sleep(2)

                # Password
                pwd_in = _find(drv,
                               (AppiumBy.XPATH,
                                "//android.widget.EditText[@password='true' or contains(@hint,'assword')]"),
                               (AppiumBy.XPATH,
                                "//android.widget.EditText"),
                               timeout=10)
                if pwd_in:
                    pwd_in.click()
                    pwd_in.clear()
                    pwd_in.send_keys(pwd)
                    _shot(drv, "04-pwd-typed")
                    drv.execute_script("mobile: performEditorAction", {"action": "go"})
                    time.sleep(5)
                    _shot(drv, "05-after-submit")
                else:
                    print("[err] password field not found")
                    _shot(drv, "ERR-no-pwd")
                    return
            else:
                print("[err] email field not found on signin")
                _shot(drv, "ERR-no-email")
                return

        # 4) Final state check
        time.sleep(3)
        _shot(drv, "06-final")
        url_bar_now = _find(drv,
                            (AppiumBy.ID, "com.android.chrome:id/url_bar"),
                            timeout=5)
        if url_bar_now:
            print(f"  final url-bar: {url_bar_now.text!r}")
        page = drv.page_source or ""
        if "captcha" in page.lower() or "robot" in page.lower():
            print("[WARN] reCAPTCHA gate encountered — manual tap required once")
        elif "messages" in page.lower() or "Dev01" in page:
            print("[ok] looks like inbox loaded — session is live")
        else:
            print("[unclear] inspect /tmp/mt_mobile/*.png screenshots")

    finally:
        try:
            drv.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
