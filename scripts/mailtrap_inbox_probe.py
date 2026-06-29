"""
With the phone's Chrome already logged in to Mailtrap (manual), navigate to
the Dev01/Teamadmin sandbox and verify the session is live + capture the
top of the inbox list (subjects + recipients) so PHIX-86688 tests can
correlate emails with the actions that triggered them.

Run:
    python -m scripts.mailtrap_inbox_probe
"""

import re
import time
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


SHOTS = Path(".tmp/mt_mobile")
SHOTS.mkdir(parents=True, exist_ok=True)


def _shot(drv, label):
    p = SHOTS / f"{label}.png"
    try:
        drv.save_screenshot(str(p))
        print(f"  [shot] {p}")
    except Exception as e:
        print(f"  [shot fail] {e}")


def _url_bar(drv):
    try:
        els = drv.find_elements(AppiumBy.ID, "com.android.chrome:id/url_bar")
        if els:
            return els[0]
    except Exception:
        pass
    try:
        els = drv.find_elements(AppiumBy.XPATH,
                                 "//*[contains(@resource-id,'url_bar')]")
        if els:
            return els[0]
    except Exception:
        pass
    return None


def main():
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
        bar = _url_bar(drv)
        if not bar:
            print("[err] url bar not found")
            _shot(drv, "00-no-url-bar")
            return
        # Navigate to the sandbox messages URL
        bar.click()
        time.sleep(1)
        bar.clear()
        bar.send_keys("https://mailtrap.io/sandboxes/2177958/messages\n")
        time.sleep(6)
        _shot(drv, "10-after-nav")

        bar = _url_bar(drv)
        url_now = bar.text if bar else "?"
        print(f"  url-bar now: {url_now!r}")

        # If we ended up on signin / verification we're not in
        if "signin" in url_now.lower():
            print("[err] still not logged in — bounced to signin")
            return

        # Read the page text & try to enumerate the first few message rows.
        page = drv.page_source or ""
        # Mailtrap's mobile web uses h3/p text for subject + recipient. Pull the
        # top-N visible texts (everything is in compact list rows).
        # We'll capture all the @text values from native elements that look like
        # email rows (heuristic: short text containing 'Welcome' / 'Action' / 'Time' /
        # an email subject keyword, or 'to: <addr>').
        from xml.etree import ElementTree as ET
        try:
            root = ET.fromstring(page)
        except Exception:
            root = None

        # Crude: walk and collect non-empty @text strings
        seen = []
        if root is not None:
            for el in root.iter():
                t = (el.attrib.get("text") or "").strip()
                if 5 < len(t) < 120 and t not in seen:
                    seen.append(t)
        print(f"[ok] {len(seen)} visible text lines on screen — sample (first 30):")
        for i, s in enumerate(seen[:30]):
            print(f"  {i:2d}. {s}")

        # Look for the Dev01/Teamadmin breadcrumb to prove we're on the right inbox
        if any("Dev01" in s or "Teamadmin" in s.lower() for s in seen):
            print("[ok] Dev01/Teamadmin inbox confirmed loaded")
        else:
            print("[hmm] inbox marker not found — see screenshot")

        # Look for any "to: <email>" pattern hint
        to_lines = [s for s in seen if "@" in s and ("to:" in s.lower() or "@testdomain" in s.lower())]
        print(f"[recipients] candidate 'to:' lines: {len(to_lines)}")
        for l in to_lines[:10]:
            print(f"  -> {l}")
    finally:
        try:
            drv.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
