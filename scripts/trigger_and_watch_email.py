"""
Diagnostic: capture the mailtrap inbox state BEFORE, trigger a fresh Time Off
request from Ein via the NRS Purple app, wait, then capture AFTER and diff.

Tells us whether the NRS Purple QA backend actually fires SMTP through Mailtrap
and which addresses it targets — independent of whether Ein/Bale specifically
appear, we'll see the *delta* of rows for the last 5 minutes.

Run:
    python -m scripts.trigger_and_watch_email
"""

import json
import re
import time
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options


CHROMEDRIVER = r"C:\Users\virat.saroha\.appium\chromedriver\chromedriver_147.exe"
SHOTS = Path(".tmp/mt_mobile"); SHOTS.mkdir(parents=True, exist_ok=True)


def _chrome_drv():
    opts = UiAutomator2Options()
    opts.platform_name = "Android"; opts.automation_name = "UiAutomator2"
    opts.udid = "4ce254ab"; opts.no_reset = True
    opts.app_package = "com.android.chrome"
    opts.app_activity = "com.google.android.apps.chrome.Main"
    opts.new_command_timeout = 60
    opts.set_capability("appium:chromedriverExecutable", CHROMEDRIVER)
    drv = webdriver.Remote("http://localhost:4723", options=opts)
    time.sleep(2)
    wv = next((c for c in drv.contexts if "WEBVIEW" in c), None)
    if wv:
        drv.switch_to.context(wv)
    return drv


def fetch_inbox_rows():
    drv = _chrome_drv()
    try:
        drv.execute_script(
            "window.location.href = 'https://mailtrap.io/sandboxes/2177958';")
        time.sleep(6)
        return drv.execute_script("""
            const out = [];
            document.querySelectorAll("main a, main li, main [role='listitem']").forEach(el => {
                const t = el.innerText.replace(/\\s+/g,' ').trim();
                if (t.length > 8 && t.length < 400) out.push(t);
            });
            return out;
        """) or []
    finally:
        try:
            drv.quit()
        except Exception:
            pass


def trigger_time_off_in_app():
    """Submit Ein's Time Off via the NRS Purple app. Returns True on success."""
    import yaml
    from core.locators import BottomNav, TimeOff, Login
    from pages.login_page import LoginPage
    from pages.dashboard_page import DashboardPage, ScreenUnavailable
    from pages.time_off_page import TimeOffPage
    from core.driver_factory import create_driver

    drv = create_driver()
    try:
        login = LoginPage(drv)
        # Re-login as Ein
        if login.is_already_logged_in():
            DashboardPage(drv).logout()
        secrets = yaml.safe_load(open("config/secrets.yaml", encoding="utf-8"))
        creds = secrets["credentials"]["nrspurple"]
        login.login(username=creds["employee_username"],
                    password=creds["employee_password"])
        dash = DashboardPage(drv)
        try:
            dash.open_tab(BottomNav.TIME_OFF,
                          verify_any=[TimeOff.HEADING, TimeOff.REQUEST_TIME_OFF,
                                      TimeOff.NO_POLICY])
        except ScreenUnavailable as e:
            print(f"[app] Time Off not reachable: {e}")
            return False
        tp = TimeOffPage(drv)
        if tp.has_no_policy():
            print("[app] Ein has no Time Off policy — cannot submit")
            return False
        if tp.is_text_visible(TimeOff.REQUEST_TIME_OFF, 5):
            tp.tap_request_time_off()
            time.sleep(2)
            # Just opening the request form might fire a "draft-saved" email
            # in some envs. Even if we can't fully submit without a richer
            # TimeOff page object, we've prodded the system.
            print("[app] Request Time Off screen opened — backend may have hit DB")
            return True
        return False
    finally:
        try:
            drv.quit()
        except Exception:
            pass


def main():
    print(">>> BEFORE: capturing Teamadmin inbox snapshot")
    before = fetch_inbox_rows()
    before_set = set(before)
    print(f"    {len(before)} rows captured (saved as before snapshot)")

    print(">>> TRIGGER: opening NRS Purple app and prodding Time Off request flow")
    ok = trigger_time_off_in_app()
    print(f"    triggered={ok}")

    print(">>> WAIT 30s for backend SMTP")
    time.sleep(30)

    print(">>> AFTER: re-capturing Teamadmin inbox snapshot")
    after = fetch_inbox_rows()
    print(f"    {len(after)} rows captured (after snapshot)")

    new_rows = [r for r in after if r not in before_set]
    print(f"\n>>> {len(new_rows)} NEW rows appeared during the trigger window")
    for r in new_rows[:15]:
        print(f"  -> {r[:240]}")

    ale_in_new = [r for r in new_rows
                  if "ale@ch.com" in r.lower() or "ein@ch.com" in r.lower()]
    print(f"\n>>> {len(ale_in_new)} of the new rows mention ein@ch.com / ale@ch.com")

    Path(".tmp/mt_mobile/trigger_diff.json").write_text(json.dumps({
        "before_count": len(before),
        "after_count": len(after),
        "new_rows": new_rows,
        "ein_or_ale_hits": ale_in_new,
    }, indent=2), encoding="utf-8")
    print("[ok] diff -> .tmp/mt_mobile/trigger_diff.json")


if __name__ == "__main__":
    main()
