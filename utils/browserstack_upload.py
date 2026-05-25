"""
Upload an APK/IPA to BrowserStack App Automate and print the bs:// URL.

Usage:
    python -m utils.browserstack_upload apps/uzio-prod.apk
    python -m utils.browserstack_upload apps/uzio-prod.ipa --custom-id UZIO_PROD

The returned bs:// URL goes into config.yaml:
    app.android.browserstack_app   (for .apk)
    app.ios.browserstack_app       (for .ipa)
"""

import sys
import argparse
import requests

from core.config_loader import config


def upload(file_path: str, custom_id: str = None) -> str:
    user = config.get("browserstack.username")
    key = config.get("browserstack.access_key")
    if not user or not key:
        raise SystemExit("BrowserStack username/access_key missing — set them in secrets.yaml")

    url = "https://api-cloud.browserstack.com/app-automate/upload"
    data = {}
    if custom_id:
        data["custom_id"] = custom_id

    print(f"[Upload] Uploading {file_path} to BrowserStack ... (this can take 1-3 min)")
    with open(file_path, "rb") as f:
        resp = requests.post(url, auth=(user, key),
                             files={"file": f}, data=data, timeout=600)
    resp.raise_for_status()
    app_url = resp.json().get("app_url")
    print(f"[Upload] Done → {app_url}")
    print(f"[Upload] Put this in config.yaml under app.<platform>.browserstack_app")
    return app_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to .apk or .ipa")
    parser.add_argument("--custom-id", default=None)
    args = parser.parse_args()
    upload(args.file, args.custom_id)
