"""
Driver factory — creates Appium drivers for Android/iOS on BrowserStack or local.

Run-mode matrix (controlled by config.yaml + env vars):
    platform=android, run_mode=local         -> UiAutomator2 on local device/emulator
    platform=android, run_mode=browserstack  -> UiAutomator2 on BrowserStack cloud
    platform=ios,     run_mode=local         -> XCUITest on local device/simulator
    platform=ios,     run_mode=browserstack  -> XCUITest on BrowserStack cloud

Usage:
    from core.driver_factory import create_driver
    driver = create_driver(build_name="PROD Sanity")
"""

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from core.config_loader import config


def create_driver(build_name: str = None, session_name: str = None):
    """Create and return an Appium driver based on current config."""
    platform = config.platform
    if platform == "ios":
        return _create_ios_driver(build_name, session_name)
    return _create_android_driver(build_name, session_name)


# ─── Android ──────────────────────────────────────────────────────────────────

def _create_android_driver(build_name, session_name):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    options.new_command_timeout = 120

    if config.browserstack_enabled:
        _apply_browserstack_caps(options, "android", build_name, session_name)
        app = config.get("app.android.browserstack_app")
        if not app:
            raise RuntimeError("app.android.browserstack_app not set — upload APK first "
                               "(see utils/browserstack_upload.py)")
        options.set_capability("app", app)
        url = _browserstack_hub()
        print(f"[Driver] BrowserStack Android — {config.get('browserstack.android.device')} | app={app}")
    else:
        device = config.get("appium.android_device")
        if device:
            options.udid = device
        apk = config.get("app.android.apk_path")
        if apk:
            options.app = str(config.root / apk) if not apk.startswith("/") else apk
            print(f"[Driver] Local Android — installing {apk}")
        else:
            options.app_package = config.get("app.android.package")
            options.app_activity = config.get("app.android.activity")
            print(f"[Driver] Local Android — launching {options.app_package}")
        url = config.get("appium.server_url")

    return webdriver.Remote(url, options=options)


# ─── iOS ────────────────────────────────────────────────────────────────────

def _create_ios_driver(build_name, session_name):
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.automation_name = "XCUITest"
    options.no_reset = True
    options.new_command_timeout = 120

    if config.browserstack_enabled:
        _apply_browserstack_caps(options, "ios", build_name, session_name)
        app = config.get("app.ios.browserstack_app")
        if not app:
            raise RuntimeError("app.ios.browserstack_app not set — upload IPA first")
        options.set_capability("app", app)
        url = _browserstack_hub()
        print(f"[Driver] BrowserStack iOS — {config.get('browserstack.ios.device')} | app={app}")
    else:
        device = config.get("appium.ios_device")
        if device:
            options.udid = device
        ipa = config.get("app.ios.ipa_path")
        if ipa:
            options.app = str(config.root / ipa) if not ipa.startswith("/") else ipa
            print(f"[Driver] Local iOS — installing {ipa}")
        else:
            options.bundle_id = config.get("app.ios.bundle_id")
            print(f"[Driver] Local iOS — launching {options.bundle_id}")
        url = config.get("appium.server_url")

    return webdriver.Remote(url, options=options)


# ─── BrowserStack helpers ─────────────────────────────────────────────────────

def _apply_browserstack_caps(options, platform, build_name, session_name):
    bstack = {
        "userName": config.get("browserstack.username"),
        "accessKey": config.get("browserstack.access_key"),
        "projectName": config.get("browserstack.project", "UZIO Mobile"),
        "buildName": build_name or config.get("browserstack.build", "MobileAutoQA"),
        "sessionName": session_name or f"{platform} test",
    }
    # Advanced logging caps are paid-only on BrowserStack. Only include them when
    # explicitly enabled, otherwise NEW_SESSION fails on Free-plan accounts.
    if config.get("browserstack.debug", False):
        bstack["debug"] = True
    if config.get("browserstack.network_logs", False):
        bstack["networkLogs"] = True
    if config.get("browserstack.device_logs", False):
        bstack["deviceLogs"] = True
    if platform == "android":
        bstack["deviceName"] = config.get("browserstack.android.device", "Samsung Galaxy S23")
        bstack["osVersion"] = config.get("browserstack.android.os_version", "13.0")
    else:
        bstack["deviceName"] = config.get("browserstack.ios.device", "iPhone 15")
        bstack["osVersion"] = config.get("browserstack.ios.os_version", "17.0")

    options.set_capability("bstack:options", bstack)


def _browserstack_hub() -> str:
    user = config.get("browserstack.username")
    key = config.get("browserstack.access_key")
    if not user or not key:
        raise RuntimeError("BrowserStack username/access_key missing — set them in secrets.yaml")
    return f"https://{user}:{key}@hub-cloud.browserstack.com/wd/hub"
