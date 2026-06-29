"""
Driver search in the Mailtrap mobile UI for emails to ale@ch.com (Bale).
Validates that NRS Purple QA emails actually land in Mailtrap Teamadmin
and surface the latest few.
"""

import time
import re
from pathlib import Path
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

SHOTS = Path(".tmp/mt_mobile"); SHOTS.mkdir(parents=True, exist_ok=True)


def _shot(drv, label):
    p = SHOTS / f"{label}.png"
    drv.save_screenshot(str(p))
    print(f"  [shot] {p}")


def main():
    opts = UiAutomator2Options()
    opts.platform_name = "Android"; opts.automation_name = "UiAutomator2"
    opts.udid = "4ce254ab"; opts.no_reset = True
    opts.app_package = "com.android.chrome"
    opts.app_activity = "com.google.android.apps.chrome.Main"
    opts.new_command_timeout = 60
    # Point Appium at the chromedriver we downloaded that matches Chrome 147
    opts.set_capability("appium:chromedriverExecutable",
                        r"C:\Users\virat.saroha\.appium\chromedriver\chromedriver_147.exe")

    drv = webdriver.Remote("http://localhost:4723", options=opts)
    print("[ok] chrome session")
    time.sleep(2)

    try:
        # Switch to the Chrome WebView context so we can read DOM text
        contexts = drv.contexts
        print(f"  contexts: {contexts}")
        wv = next((c for c in contexts if "WEBVIEW" in c), None)
        if wv:
            try:
                drv.switch_to.context(wv)
                print(f"[ok] switched to {wv}")
            except Exception as e:
                print(f"[warn] could not switch to webview: {e}")
                wv = None

        if wv:
            # Use JS to extract email rows (subject + recipient)
            try:
                js = """
                  const rows = Array.from(document.querySelectorAll(
                    "[class*='Message'],[data-testid*='message'],li, article, tr"));
                  return rows.slice(0, 60).map(r => r.innerText.replace(/\\s+/g,' ').trim())
                             .filter(t => t.length > 5 && t.length < 300);
                """
                texts = drv.execute_script(js)
                print(f"[ok] {len(texts)} text rows from WebView")
                ale_hits = [t for t in texts if "ale@ch.com" in t.lower()]
                print(f"[ale@ch.com hits]: {len(ale_hits)}")
                for h in ale_hits[:10]:
                    print(f"  -> {h[:200]}")
                # Show first few rows regardless to see structure
                print("[first 12 rows shown]:")
                for t in texts[:12]:
                    print(f"  | {t[:180]}")
            except Exception as e:
                print(f"[err] webview JS failed: {e}")
        else:
            print("[note] no webview available — falling back to native screenshot only")
        _shot(drv, "20-search-state")
    finally:
        try:
            drv.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
