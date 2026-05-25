"""
pytest fixtures and hooks for MobileAutoQA.

Provides:
  - session-scoped `reporter` (one HTML/JSON report per suite run)
  - class-scoped `driver` (Appium session per test class, with login)
  - automatic screenshot + heal-log capture into the report
  - test result recording via the pytest_runtest_makereport hook

Suite name is derived from the test path: tests/sanity -> "sanity",
tests/jira/PHIX-97533 -> "PHIX-97533". Override with -Dsuite or --suite.
"""

import time
import pytest
import allure

from core.config_loader import config
from core.driver_factory import create_driver
from core.reporter import Reporter
from pages.login_page import LoginPage


def pytest_addoption(parser):
    parser.addoption("--suite", action="store", default=None,
                     help="Report suite name (default: derived from test path)")
    parser.addoption("--build", action="store", default=None,
                     help="BrowserStack build name")


def _suite_name(request):
    explicit = request.config.getoption("--suite")
    if explicit:
        return explicit
    path = str(request.node.fspath)
    if "jira" in path:
        # tests/jira/PHIX-97533/test_*.py -> PHIX-97533
        parts = path.replace("\\", "/").split("/")
        for i, p in enumerate(parts):
            if p == "jira" and i + 1 < len(parts):
                return parts[i + 1]
    if "regression" in path:
        return "regression"
    return "sanity"


def _write_allure_environment(suite):
    """Write environment.properties so the Allure report shows run context."""
    try:
        from pathlib import Path
        results = Path("reports/allure-results")
        results.mkdir(parents=True, exist_ok=True)
        dev = config.get(f"browserstack.{config.platform}.device", "local") \
            if config.browserstack_enabled else "local-device"
        lines = [
            f"Platform={config.platform}",
            f"RunMode={config.run_mode}",
            f"Environment={config.environment}",
            f"Device={dev}",
            f"Build={config.get('browserstack.build', '')}",
            f"AppId={config.get('app.android.package', '')}",
            f"Suite={suite}",
        ]
        (results / "environment.properties").write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"[conftest] allure environment write skipped: {e}")


@pytest.fixture(scope="session")
def reporter(request):
    suite = _suite_name(request)
    rep = Reporter(suite)
    _write_allure_environment(suite)
    print(f"\n[conftest] Reporter initialized — suite={suite}, dir={rep.run_dir}")
    yield rep
    rep.finish()


@pytest.fixture(scope="class")
def driver(request, reporter):
    build = request.config.getoption("--build") or config.get("browserstack.build")
    drv = create_driver(build_name=build)

    # Login once per class
    login = LoginPage(drv)
    if login.is_already_logged_in():
        print("[conftest] Already logged in")
    else:
        login.login()

    # Expose to test class
    request.cls.driver = drv
    request.cls.reporter = reporter
    yield drv

    # Teardown
    try:
        from pages.dashboard_page import DashboardPage
        DashboardPage(drv).logout()
    except Exception as e:
        print(f"[conftest] logout skipped: {e}")
    finally:
        try:
            drv.quit()
        except Exception:
            pass


# ─── Result capture hook ─────────────────────────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    # Find reporter + driver on the test instance
    instance = getattr(item, "instance", None)
    reporter = getattr(instance, "reporter", None)
    driver = getattr(instance, "driver", None)
    if reporter is None:
        return

    test_id = getattr(instance, "_current_test_id", item.name)
    test_name = getattr(instance, "_current_test_name", item.name)
    duration = getattr(report, "duration", 0.0)

    # Collect heal log from page objects used in the test
    heals = [str(h) for h in getattr(instance, "_heal_log", [])]

    if report.passed:
        shot = _safe_shot(driver) if config.get("reporting.screenshot_on_pass", True) else None
        reporter.record(test_id, test_name, "PASS", duration=duration,
                        screenshot_bytes=shot, heals=heals)
        _attach_allure(shot, heals)
    elif report.failed:
        shot = _safe_shot(driver) if config.get("reporting.screenshot_on_fail", True) else None
        msg = str(report.longrepr.reprcrash.message) if report.longrepr else "failed"
        reporter.record(test_id, test_name, "FAIL", message=msg, duration=duration,
                        screenshot_bytes=shot, heals=heals)
        _attach_allure(shot, heals)
    elif report.skipped:
        reporter.record(test_id, test_name, "SKIP", duration=duration, heals=heals)
        _attach_allure(None, heals)


def _attach_allure(shot, heals):
    """Attach the screenshot + self-healing log to the current Allure test."""
    try:
        if shot:
            allure.attach(shot, name="screenshot",
                          attachment_type=allure.attachment_type.PNG)
        if heals:
            allure.attach("\n".join(heals), name="self-healing log",
                          attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass  # never let reporting break a test result


def _safe_shot(driver):
    if driver is None:
        return None
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        return None
