"""
Walk every Mailtrap sandbox visible in 'Softwares (shared)' workspace via
mobile Chrome WebView, grep visible message rows for ein@ch.com or ale@ch.com,
and report the first sandbox that holds NRS Purple emails (if any).
"""

import json
import re
import time
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options

SHOTS = Path(".tmp/mt_mobile"); SHOTS.mkdir(parents=True, exist_ok=True)
CHROMEDRIVER = r"C:\Users\virat.saroha\.appium\chromedriver\chromedriver_147.exe"
TARGETS = ["ein@ch.com", "ale@ch.com", "Ein Lname", "Bale Lname"]


def _driver():
    opts = UiAutomator2Options()
    opts.platform_name = "Android"; opts.automation_name = "UiAutomator2"
    opts.udid = "4ce254ab"; opts.no_reset = True
    opts.app_package = "com.android.chrome"
    opts.app_activity = "com.google.android.apps.chrome.Main"
    opts.new_command_timeout = 90
    opts.set_capability("appium:chromedriverExecutable", CHROMEDRIVER)
    drv = webdriver.Remote("http://localhost:4723", options=opts)
    time.sleep(2)
    ctxs = drv.contexts
    wv = next((c for c in ctxs if "WEBVIEW" in c), None)
    drv.switch_to.context(wv)
    return drv


def _grab_rows(drv):
    return drv.execute_script("""
        const out = [];
        const cands = document.querySelectorAll(
          "main a, main li, main [role='listitem'], main [class*='message' i]");
        cands.forEach(el => {
          const t = el.innerText.replace(/\\s+/g,' ').trim();
          if (t.length > 8 && t.length < 400) out.push(t);
        });
        return out;
    """) or []


def _list_sandboxes(drv):
    """From the sandboxes list page, extract { name, sandbox_id }."""
    drv.execute_script("window.location.href = 'https://mailtrap.io/sandboxes';")
    time.sleep(5)
    return drv.execute_script("""
        const out = [];
        document.querySelectorAll("a[href*='/sandboxes/']").forEach(a => {
          const m = a.href.match(/\\/sandboxes\\/(\\d+)/);
          if (m) {
            const name = a.innerText.replace(/\\s+/g,' ').trim();
            if (name && name.length < 80) out.push({id: m[1], name: name});
          }
        });
        // de-dup
        const seen = {};
        return out.filter(x => seen[x.id] ? false : (seen[x.id] = true));
    """) or []


def main():
    drv = _driver()
    try:
        boxes = _list_sandboxes(drv)
        print(f"[ok] found {len(boxes)} sandboxes:")
        for b in boxes:
            print(f"  - id={b['id']:<10} name={b['name']!r}")

        results = []
        for b in boxes:
            url = f"https://mailtrap.io/sandboxes/{b['id']}"
            drv.execute_script(f"window.location.href = '{url}';")
            time.sleep(5)
            rows = _grab_rows(drv)
            hits = [r for r in rows
                    if any(t.lower() in r.lower() for t in TARGETS)]
            print(f"  [scan] {b['name']:30s} ({b['id']}) rows={len(rows):>3} hits={len(hits)}")
            if hits:
                for h in hits[:5]:
                    print(f"      -> {h[:240]}")
            results.append({"id": b["id"], "name": b["name"],
                            "rows": len(rows), "hits": hits})

        Path(".tmp/mt_mobile/sandbox_sweep.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8")
        print("\n[ok] sweep dump -> .tmp/mt_mobile/sandbox_sweep.json")

        match = next((r for r in results if r["hits"]), None)
        if match:
            print(f"\n✅ NRS Purple emails are in: {match['name']!r} (id {match['id']})")
        else:
            print("\n❌ No sandbox holds emails to ein@ch.com / ale@ch.com")
    finally:
        try:
            drv.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
