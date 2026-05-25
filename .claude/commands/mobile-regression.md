# Mobile Regression Agent

**Role:** Single-prompt **regression suite** orchestrator. Runs the full regression
suite (all core flows across feature areas), auto-heals, reports, and notifies.

Suite orchestrator chaining the core agents for the regression suite:
> (upload) → **Execution Agent** → **Self-Healing Agent** → **Reporting Agent**

The regression suite = everything under `tests/regression/` — the broad set of
core flows that must keep working every release (deeper than sanity).

---

## Usage

```
/mobile-regression                      ← newest APK, env=prod, Android, BrowserStack
/mobile-regression --env=qa
/mobile-regression --platform=ios
/mobile-regression --platform=both
/mobile-regression --local
/mobile-regression --area=time_tracking ← run only one area's regression file
/mobile-regression --skip-upload
```

---

## Step 0 — Infer & Confirm
Same build detection as `/mobile-sanity`. Build label = `Regression {date}`.
Regression is longer (15–45 min) — note that in the confirmation:
```
Regression run:
  Build    : apps/uzio-prod.apk
  Platform : Android · Samsung Galaxy S23 / Android 13
  Env      : prod
  Mode     : BrowserStack
  Scope    : full regression (~{N} tests, ~{est} min) | area={area}
  Label    : Regression 2026-05-22
Proceed? [y/n]
```

---

## Step 1 — Upload
Same as `/mobile-sanity` Step 1 (skip if `--skip-upload` / unchanged).

---

## Step 2 — Execute the regression suite
```bash
cd /c/code/master/MobileAutoQA && \
  MAQA_PLATFORM={android|ios} MAQA_ENVIRONMENT={prod|qa} \
  python -m pytest tests/regression --suite=regression --build="Regression {date}" \
  2>&1 | tee .tmp/regression-{date}.log
```
Single area:  `python -m pytest tests/regression/test_{area}.py --suite=regression`

**Run in background** — regression can take 15–45 min. Give periodic status updates
and avoid re-prompting; the suite is single-threaded (one BrowserStack session).

---

## Step 3 — Parse results
From `.tmp/regression-{date}.log`. Latest report:
`ls -t reports/regression/*/run-log.json | head -1`.

---

## Step 4 — Auto-heal failures
For any failures, invoke the **Self-Healing Agent**:
```
/self-healing-agent regression --from-run={run-log path}
```
Because regression covers more screens, expect a wider range of heals (label drift,
new popups, timing). Prefer fixing `core/locators.py` (helps all suites). Max 2
heal cycles per test; escalate feature-not-deployed failures rather than patching.

---

## Step 5 — Report & notify
`core/reporter.py` auto-writes `reports/regression/{ts}/report.html` + `run-log.json`
and posts a Google Chat card. Then print:

```
✅ Mobile Regression Complete
  Platform : {Android|iOS|both}
  Env      : {prod|qa}
  Scope    : full | area={area}
  Result   : Passed {N}  Failed {N}  Skipped {N}  ({rate}%)
  Healed   : {N}
  Duration : {Xm Ys}
  Report   : reports/regression/{ts}/report.html
  Chat     : posted to Mobile Dev-QA ✓
```

If failures remain after healing, list each (test id, one-line cause, screenshot path)
and suggest filing defects for genuine app bugs (not test issues).

---

## Step 6 — `--platform=both`
Run Android fully, then upload/confirm IPA, `MAQA_PLATFORM=ios`, repeat.

---

## Growing the regression suite
- Each new feature area gets `tests/regression/test_{area}.py` (e.g. `test_time_off.py`,
  `test_benefits.py`), reusing page objects in `pages/` and constants in `core/locators.py`.
- Per-JIRA tests that prove stable graduate from `tests/jira/{ID}/` into the
  regression suite — copy/promote the test and add it under `tests/regression/`.
- Keep regression deterministic: every test resets its own precondition
  (e.g. `tt.ensure_clocked_out()`), so order never matters.
```
