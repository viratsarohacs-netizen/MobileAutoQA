"""
Diagnostic: full login, then dump what's on screen post-login.
Run: python -m utils.inspect_postlogin
"""
import time, re, io, sys
from core.driver_factory import create_driver
from core.locators import Login
from core.config_loader import config

# force utf-8 stdout to avoid cp1252 crashes on glyphs
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

drv = create_driver(build_name="DIAG postlogin")
try:
    from pages.login_page import LoginPage
    lp = LoginPage(drv)
    time.sleep(10)
    lp.dismiss_system_permissions()
    time.sleep(2)
    lp.dismiss_onboarding_if_present()
    time.sleep(3)
    # Manual login (don't rely on _wait_for_login_result)
    if lp.is_text_visible(Login.LOGIN_BUTTON, 20):
        lp.enter_by_index(0, config.credential("employee_username"))
        lp.enter_by_index(1, config.credential("employee_password"))
        lp.tap(Login.LOGIN_BUTTON)
        print("[postlogin] tapped LOGIN, waiting 20s...")
    time.sleep(20)
    # dump
    src = drv.page_source or ""
    with open(".tmp/postlogin_source.xml", "w", encoding="utf-8") as f:
        f.write(src)
    drv.get_screenshot_as_file(".tmp/postlogin.png")
    texts = set()
    for attr in ("text", "content-desc", "label", "value"):
        for m in re.findall(rf'{attr}="([^"]+)"', src):
            if m.strip():
                texts.add(f"[{attr}] {m.strip()}")
    print(f"[postlogin] source {len(src)} chars; screen -> .tmp/postlogin.png")
    print("[postlogin] ===== text/labels on screen post-login =====")
    for t in sorted(texts):
        print("  ", t)
finally:
    drv.quit()
    print("[postlogin] done")
