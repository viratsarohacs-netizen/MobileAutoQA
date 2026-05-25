"""
Diagnostic: launch the app on BrowserStack, wait, dump page source + screenshot.
Used by the Self-Healing Agent to see the real screen when locators miss.

Run: python -m utils.inspect_screen
"""
import time
from core.driver_factory import create_driver

drv = create_driver(build_name="DIAG inspect")
try:
    print("[inspect] waiting 12s for app to settle...")
    time.sleep(12)

    # Dismiss system permission dialogs first (notification permission, etc.)
    from pages.login_page import LoginPage
    lp = LoginPage(drv)
    lp.dismiss_system_permissions()
    time.sleep(2)
    lp.dismiss_onboarding_if_present()
    time.sleep(4)

    src = drv.page_source or ""
    with open(".tmp/page_source.xml", "w", encoding="utf-8") as f:
        f.write(src)
    print(f"[inspect] page source written ({len(src)} chars) -> .tmp/page_source.xml")

    drv.get_screenshot_as_file(".tmp/screen.png")
    print("[inspect] screenshot -> .tmp/screen.png")

    # Print all elements that carry visible text / labels
    import re
    texts = set()
    for attr in ("text", "content-desc", "label", "value", "name"):
        for m in re.findall(rf'{attr}="([^"]+)"', src):
            if m.strip():
                texts.add(f"[{attr}] {m.strip()}")
    print("\n[inspect] ===== visible text/labels on screen =====")
    for t in sorted(texts):
        print("  ", t)
finally:
    drv.quit()
    print("[inspect] driver quit")
