# MobileAutoQA

Autonomous agent-based mobile test automation for the **UZIO Mobile** app
(React Native). Built with **Appium + Python + pytest**, cross-platform
(**Android & iOS**), runs on **BrowserStack** cloud or local devices/simulators.

Modeled after the web project `uzio-ai-qa`, adapted for mobile.

---

## The 5 Agents

| # | Agent | Command | Role |
|---|-------|---------|------|
| 1 | **Requirements Agent** | `/requirements-agent PHIX-XXXXX` | Reads Jira ID and extracts requirements |
| 2 | **Test Generation Agent** | `/test-generation-agent PHIX-XXXXX` | Converts requirements into plain-English test cases + pytest classes |
| 3 | **Execution Agent** | `/execution-agent PHIX-XXXXX` | Runs tests on physical device / simulator (Android & iOS) or BrowserStack |
| 4 | **Self-Healing Agent** | `/self-healing-agent PHIX-XXXXX` | Auto-fixes failed tests by analyzing root cause |
| 5 | **Reporting Agent** | `/reporting-agent PHIX-XXXXX` | Generates reports with screenshots and emails the team |

Pipeline:
```
Requirements → Test Generation → Execution → Self-Healing → Reporting
```

### Suite Orchestrators (single-prompt)

Two convenience agents chain `Execution → Self-Healing → Reporting` for a whole
suite in one prompt (upload build → run → heal → report → notify):

| Agent | Command | Runs |
|-------|---------|------|
| **Mobile Sanity Agent** | `/mobile-sanity` | `tests/sanity/` — smoke suite (launch, login, nav, clock in/out, logout) |
| **Mobile Regression Agent** | `/mobile-regression` | `tests/regression/` — full core-flow regression |

Per-JIRA testing uses the 5-agent pipeline directly (`/requirements-agent` → … → `/reporting-agent`).

So the three goals map cleanly:
- **Sanity suite** → `/mobile-sanity`
- **Regression suite** → `/mobile-regression`
- **Individual JIRA ticket** → `/requirements-agent PHIX-XXXXX` → `/test-generation-agent` → `/execution-agent`

---

## Project Structure

```
MobileAutoQA/
├── core/
│   ├── config_loader.py     ← YAML config + secrets + env-var overrides
│   ├── driver_factory.py    ← Android/iOS × BrowserStack/local driver creation
│   ├── element_healer.py    ← 6-strategy runtime self-healing
│   ├── base_page.py         ← tap/enter/verify/wait/swipe + healing
│   ├── locators.py          ← REAL UzioMobile visible-text constants (no testIDs)
│   └── reporter.py          ← HTML report + screenshots + email + Google Chat
├── pages/
│   ├── login_page.py        ← login (fields by index — shared placeholder)
│   ├── dashboard_page.py    ← bottom nav, hamburger drawer, attestation, logout
│   ├── time_tracking_page.py← clock in/out/break, attestation modal handling
│   └── time_off_page.py
├── tests/
│   ├── sanity/              ← test_sanity.py + sanity.test.md
│   ├── regression/          ← test_time_tracking.py
│   └── jira/{JIRA-ID}/      ← AI-generated per-ticket tests
├── utils/
│   └── browserstack_upload.py
├── config/
│   ├── config.yaml          ← base config (committed)
│   ├── secrets.example.yaml ← template → copy to secrets.yaml (gitignored)
│   └── devices/             ← device profiles
├── reports/                 ← HTML + JSON + screenshots (gitignored)
├── apps/                    ← .apk / .ipa (gitignored)
├── conftest.py              ← pytest fixtures (driver, reporter, result hook)
├── pytest.ini
├── requirements.txt
└── .claude/commands/        ← the 5 agents
```

---

## Setup

```bash
cd C:\code\master\MobileAutoQA
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# Configure secrets
copy config\secrets.example.yaml config\secrets.yaml
# edit secrets.yaml: BrowserStack key, employee password, Google Chat webhook, email creds
```

---

## Quick Start

### Run sanity on BrowserStack (Android)
```bash
# 1. Upload the APK (one time per build)
python -m utils.browserstack_upload apps/uzio-prod.apk --custom-id UZIO_PROD
#    → paste the bs://... into config.yaml: app.android.browserstack_app

# 2. Run
python -m pytest tests/sanity --suite=sanity --build="PROD Sanity"
```

Or via the agent: `/execution-agent sanity`

### Test a Jira ticket end-to-end
```
/requirements-agent PHIX-97533
/test-generation-agent PHIX-97533
/execution-agent PHIX-97533
```
(Self-Healing and Reporting run automatically on failure / completion.)

### Run on iOS
```bash
MAQA_PLATFORM=ios python -m pytest tests/sanity --suite=sanity
```
(Upload the IPA first → `app.ios.browserstack_app`.)

### Run on a local device/simulator
```bash
appium &                              # start Appium server
MAQA_RUN_MODE=local python -m pytest tests/sanity
```

---

## Why text-based locators?

The UzioMobile app has **no `testID` / `accessibilityLabel` props** (verified
against the repo). All UI text comes from i18n keys in
`UzioMobile/src/i18n/locales/en.json`. So every locator is the **visible English
string**, centralized in `core/locators.py`. If a string changes (or for a
white-label flavor), update it in one place.

> Recommendation: adding `testID` props to key elements in UzioMobile would make
> locators far more stable than text. Until then, `core/locators.py` is the
> single source of truth and the Self-Healing Agent patches text drift.

---

## Self-Healing

**Runtime (automatic):** when a text locator misses, `element_healer.py` tries 6
strategies (wait/retry → case-insensitive → partial → accessibility-id →
widget-class → page-source scan) and logs what it healed.

**Code healing (Self-Healing Agent):** when a test still fails, the agent reads
the failure screenshot, diagnoses the cause (label change, new popup, timing,
crash), patches `core/locators.py` or the page object, and re-runs.

---

## Configuration cheat-sheet

Override any config value via env var `MAQA_<DOTTED_PATH_UPPER>`:
```bash
MAQA_PLATFORM=ios
MAQA_ENVIRONMENT=qa
MAQA_RUN_MODE=local
MAQA_BROWSERSTACK_ENABLED=false
```
