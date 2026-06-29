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


@pytest.fixture(scope="session")
def reporter(request):
    suite = _suite_name(request)
    rep = Reporter(suite)
    print(f"\n[conftest] Reporter initialized — suite={suite}, dir={rep.run_dir}")
    yield rep
    rep.finish()


@pytest.fixture(scope="class")
def driver(request, reporter):
    build = request.config.getoption("--build") or config.get("browserstack.build")
    drv = create_driver(build_name=build)

    # Login once per class. Test classes can set `login_role = "manager"` to log
    # in as the reporting manager (drawer items like Team Timesheet / Team Time
    # Off are only visible to that role); default is the employee account.
    role = getattr(request.cls, "login_role", "employee")
    username = config.credential(f"{role}_username")
    password = config.credential(f"{role}_password")
    login = LoginPage(drv)
    if login.is_already_logged_in():
        print(f"[conftest] Already logged in (role={role})")
    else:
        login.login(username=username, password=password)

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
    elif report.failed:
        shot = _safe_shot(driver) if config.get("reporting.screenshot_on_fail", True) else None
        msg = str(report.longrepr.reprcrash.message) if report.longrepr else "failed"
        reporter.record(test_id, test_name, "FAIL", message=msg, duration=duration,
                        screenshot_bytes=shot, heals=heals)
    elif report.skipped:
        reporter.record(test_id, test_name, "SKIP", duration=duration, heals=heals)


def _safe_shot(driver):
    if driver is None:
        return None
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        return None
