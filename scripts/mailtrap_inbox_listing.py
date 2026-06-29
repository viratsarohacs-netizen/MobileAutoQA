"""
Drive mobile Chrome (already-logged-in to Mailtrap) into the Dev01/Teamadmin
sandbox, dump the first page of email rows (subject + recipient + timestamp)
and search specifically for emails sent to ale@ch.com (Bale - reportee manager).
"""

import json
import time
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

SHOTS = Path(".tmp/mt_mobile"); SHOTS.mkdir(parents=True, exist_ok=True)
CHROMEDRIVER = r"C:\Users\virat.saroha\.appium\chromedriver\chromedriver_147.exe"


def _shot(drv, label):
    p = SHOTS / f"{label}.png"
    try:
        drv.save_screenshot(str(p))
    except Exception:
        pass


def main():
    opts = UiAutomator2Options()
    opts.platform_name = "Android"; opts.automation_name = "UiAutomator2"
    opts.udid = "4ce254ab"; opts.no_reset = True
    opts.app_package = "com.android.chrome"
    opts.app_activity = "com.google.android.apps.chrome.Main"
    opts.new_command_timeout = 90
    opts.set_capability("appium:chromedriverExecutable", CHROMEDRIVER)

    drv = webdriver.Remote("http://localhost:4723", options=opts)
    print("[ok] session")
    time.sleep(2)

    try:
        ctxs = drv.contexts
        wv = next((c for c in ctxs if "WEBVIEW" in c), None)
        if not wv:
            print("[err] no webview"); return
        drv.switch_to.context(wv)
        print(f"[ok] in {wv}")

        # Drive the WebView's window to the messages URL.
        drv.execute_script(
            "window.location.href = 'https://mailtrap.io/sandboxes/2177958';")
        # Poll until URL is settled and the email list renders
        deadline = time.time() + 45
        rows_text = []
        while time.time() < deadline:
            try:
                # Heuristic: Mailtrap email rows render with subject + recipient text.
                # We grab everything in <main> that looks list-like.
                rows_text = drv.execute_script("""
                    const out = [];
                    // Collect anchor/list-item nodes that look like message previews
                    const cands = document.querySelectorAll(
                      "main a, main li, main [role='listitem'], main [class*='message' i], main [class*='Message']");
                    cands.forEach(el => {
                      const t = el.innerText.replace(/\\s+/g,' ').trim();
                      if (t.length > 8 && t.length < 400) out.push(t);
                    });
                    return out;
                """) or []
                if rows_text and len(rows_text) > 2:
                    break
            except Exception:
                pass
            time.sleep(1.5)

        print(f"[ok] {len(rows_text)} candidate email rows")
        ale = [r for r in rows_text if "ale@ch.com" in r.lower() or "bale" in r.lower()]
        print(f"\n>>> Hits for ale@ch.com / Bale: {len(ale)}")
        for h in ale[:15]:
            print(f"   {h[:240]}")
        print("\n>>> First 15 rows (any recipient):")
        for r in rows_text[:15]:
            print(f"   {r[:240]}")

        # Dump full list to a file for downstream tests to grep
        Path(".tmp/mt_mobile/inbox_dump.json").write_text(
            json.dumps(rows_text, indent=2), encoding="utf-8")
        print(f"\n[ok] full dump -> .tmp/mt_mobile/inbox_dump.json")

        # Switch back to native for screenshot
        drv.switch_to.context("NATIVE_APP")
        _shot(drv, "21-inbox-listing")
    finally:
        try:
            drv.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
