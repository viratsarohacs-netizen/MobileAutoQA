"""
Fetch a Mailtrap API token by driving the Mailtrap web app with Playwright.

Uses creds from config/secrets.yaml (mailtrap.username + mailtrap.password),
logs in, navigates to the API Tokens settings page, copies an existing
"API" token if one is visible, otherwise creates a new one named
"MobileAutoQA". Writes the result back into secrets.yaml under
`mailtrap.api_token` and `mailtrap.account_id`.

Run:
    python -m scripts.fetch_mailtrap_token
"""

import re
import sys
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


SECRETS = Path("config/secrets.yaml")
SCREENSHOTS = Path(".tmp/mailtrap")
SCREENSHOTS.mkdir(parents=True, exist_ok=True)


def _load_secrets():
    with open(SECRETS, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_secrets(data):
    with open(SECRETS, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def _shot(page, label):
    out = SCREENSHOTS / f"{label}.png"
    try:
        page.screenshot(path=str(out), full_page=False)
        print(f"  [screenshot] {out}")
    except Exception as e:
        print(f"  [screenshot] failed {e}")


def fetch_token():
    secrets = _load_secrets()
    mt = secrets.get("mailtrap", {})
    user = mt.get("username")
    pwd = mt.get("password")
    if not user or not pwd:
        print("[mailtrap] secrets.yaml has no mailtrap.username/password — abort")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900},
                                  user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                                              "Chrome/119.0.0.0 Safari/537.36"))
        page = ctx.new_page()

        # Step 1 — Open signin
        print("[mailtrap] navigating to /signin")
        page.goto("https://mailtrap.io/signin", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("load", timeout=30000)
        _shot(page, "01-signin")

        # Mailtrap signin is a two-step flow:
        #   1. enter email -> click "Next"
        #   2. enter password -> click "Sign in"
        # The page also has a sticky header (google-optimize-header) that
        # intercepts pointer events, so use JS-driven fills + form submit.
        try:
            # Remove the intrusive header so clicks land
            page.evaluate("""() => {
                const h = document.querySelector('.google-optimize-header');
                if (h) h.remove();
                const hdr = document.querySelector('header.header--sticky');
                if (hdr) hdr.remove();
            }""")
            # Step A: email
            page.fill('#user_email', user)
            _shot(page, "02-email-filled")
            # Click Next (anchor styled as button)
            page.evaluate("""() => {
                const btn = document.querySelector('.login_next_button')
                          || Array.from(document.querySelectorAll('a,button'))
                                 .find(e => e.textContent.trim() === 'Next');
                if (btn) btn.click();
            }""")
            # Step B: password
            page.wait_for_selector('#user_password, input[type="password"]', timeout=20000)
            page.evaluate("""() => {
                const h = document.querySelector('.google-optimize-header');
                if (h) h.remove();
            }""")
            page.fill('#user_password, input[type="password"]', pwd)
            _shot(page, "03-pwd-filled")
            # Submit form via JS (avoids any overlay)
            page.evaluate("""() => {
                const f = document.querySelector('form');
                if (f) f.submit();
            }""")
        except PWTimeout as e:
            print(f"[mailtrap] couldn't drive login form: {e}")
            _shot(page, "ERR-no-form")
            browser.close()
            return None

        # Step 2 — Wait for login complete; multiple possible landings
        try:
            page.wait_for_url(re.compile(r"mailtrap\.io/(?!signin)"), timeout=30000)
        except PWTimeout:
            print("[mailtrap] login did not redirect — likely bad creds or 2FA")
            _shot(page, "ERR-no-redirect")
            print("[mailtrap] body text head:", page.content()[:500])
            browser.close()
            return None
        _shot(page, "03-after-login")
        print(f"[mailtrap] logged in, at {page.url}")

        # Try to detect account id from the URL (e.g., /accounts/<id>/...).
        m = re.search(r"/accounts/(\d+)", page.url)
        account_id = m.group(1) if m else None
        if not account_id:
            # Click through to API Tokens to capture the URL with account id
            pass

        # Step 3 — go to API tokens page
        print("[mailtrap] navigating to API tokens")
        # Common Mailtrap API tokens URL:
        page.goto("https://mailtrap.io/api/account/api-tokens", wait_until="networkidle")
        if "404" in page.title().lower() or page.url.endswith("/signin"):
            # Newer Mailtrap UI puts it under settings
            page.goto("https://mailtrap.io/settings/api-tokens", wait_until="networkidle")
        _shot(page, "04-api-tokens-page")
        print(f"[mailtrap] tokens page: {page.url}")

        # Extract account id from token page URL if not already
        if not account_id:
            m = re.search(r"/accounts?/(\d+)", page.url)
            account_id = m.group(1) if m else None

        # Step 4 — look for existing token row; click "Show" / "Copy" to reveal
        # Otherwise click "Add Token" / "Create Token".
        token_value = None
        try:
            # Try common patterns to reveal an existing token
            show_btn = page.locator("button:has-text('Show'), button:has-text('Reveal'), "
                                    "button:has-text('Copy')").first
            if show_btn.count() > 0:
                show_btn.click()
                time.sleep(1)
                # Token usually appears in a code/input element after click
                token_box = page.locator("input[readonly], code").first
                if token_box.count() > 0:
                    token_value = token_box.input_value() if token_box.evaluate(
                        "el => el.tagName") == "INPUT" else token_box.inner_text()
        except Exception:
            pass

        if not token_value:
            # Create a new token
            try:
                add_btn = page.locator("button:has-text('Add Token'), "
                                       "button:has-text('Create Token'), "
                                       "button:has-text('New Token')").first
                add_btn.wait_for(timeout=10000)
                add_btn.click()
                name_in = page.locator('input[name*="name" i], input[placeholder*="name" i]').first
                name_in.wait_for(timeout=10000)
                name_in.fill("MobileAutoQA")
                # Submit the create form
                page.locator("button:has-text('Save'), button:has-text('Create')").first.click()
                _shot(page, "05-created-token")
                time.sleep(2)
                # Token usually renders in a one-time-reveal box
                code_el = page.locator("input[readonly], code, pre").first
                code_el.wait_for(timeout=10000)
                token_value = (code_el.input_value()
                               if code_el.evaluate("el => el.tagName") == "INPUT"
                               else code_el.inner_text())
            except Exception as e:
                print(f"[mailtrap] could not create token: {e}")
                _shot(page, "ERR-create-token")

        browser.close()

        if not token_value or len(token_value.strip()) < 20:
            print(f"[mailtrap] no usable token captured (got: {token_value!r})")
            return None

        token_value = token_value.strip()
        print(f"[mailtrap] captured token: {token_value[:8]}... (len {len(token_value)})")
        secrets.setdefault("mailtrap", {})["api_token"] = token_value
        if account_id:
            secrets["mailtrap"]["account_id"] = account_id
            print(f"[mailtrap] account_id={account_id}")
        _save_secrets(secrets)
        print(f"[mailtrap] wrote token to {SECRETS}")

        # Step 5 — Find the 'teamadmin' sandbox inbox id (used by NRS Purple QA)
        if account_id:
            import requests as _r
            r = _r.get(f"https://mailtrap.io/api/accounts/{account_id}/projects",
                       headers={"Api-Token": token_value}, timeout=15)
            if r.status_code == 200:
                projects = r.json()
                inbox_id = None
                inbox_name = None
                for proj in projects:
                    for inb in proj.get("inboxes", []):
                        # Match anything containing 'teamadmin' (case-insensitive)
                        if "teamadmin" in (inb.get("name") or "").lower():
                            inbox_id = inb.get("id")
                            inbox_name = inb.get("name")
                            break
                    if inbox_id:
                        break
                if inbox_id:
                    secrets["mailtrap"]["inbox_id"] = inbox_id
                    secrets["mailtrap"]["inbox_name"] = inbox_name
                    _save_secrets(secrets)
                    print(f"[mailtrap] teamadmin inbox id={inbox_id} name={inbox_name!r}")
                else:
                    print("[mailtrap] no inbox matched 'teamadmin' — list of inboxes:")
                    for proj in projects:
                        for inb in proj.get("inboxes", []):
                            print(f"  - {inb.get('id')}: {inb.get('name')}")
            else:
                print(f"[mailtrap] /projects returned {r.status_code} {r.text[:200]}")
        return token_value


if __name__ == "__main__":
    tok = fetch_token()
    if not tok:
        sys.exit(1)
    print("[ok]")
