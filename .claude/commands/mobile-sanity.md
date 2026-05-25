# Mobile Sanity Agent

**Role:** Single-prompt **sanity suite** orchestrator. Detects the latest build,
uploads to BrowserStack, runs the sanity suite, auto-heals failures, generates the
report, and notifies the team — end to end.

This is a **suite orchestrator** that chains the 5 core agents for the sanity suite:
> (upload) → **Execution Agent** → **Self-Healing Agent** → **Reporting Agent**

The sanity suite = the smoke tests in `tests/sanity/` (app launch, login, bottom
nav, Time Tracking screen, Clock In, Clock Out incl. attestation, logout).

---

## Usage

```
/mobile-sanity                       ← newest APK, env=prod, Android, BrowserStack
/mobile-sanity --env=qa
/mobile-sanity --platform=ios        ← newest IPA on iPhone 15
/mobile-sanity --platform=both       ← Android then iOS sequentially
/mobile-sanity --local               ← local device/emulator/simulator
/mobile-sanity --skip-upload         ← reuse the bs:// already in config.yaml
```

---

## Step 0 — Infer & Confirm

Detect newest build:
```bash
ls -t /c/code/master/MobileAutoQA/apps/*.apk \
      /c/code/master/Mobile_testing_Framework/mobile/*.apk 2>/dev/null | head -5   # Android
ls -t /c/code/master/MobileAutoQA/apps/*.ipa 2>/dev/null | head -5                 # iOS
```

Infer: APK/IPA = newest by mtime · env = `prod` · build label = `Sanity {date}` · platform = `android`.

**Confirm before running** (real cloud infra + real chat post):
```
Sanity run:
  Build    : apps/uzio-prod.apk (5.2 MB, 2026-05-22 09:15)
  Platform : Android · Samsung Galaxy S23 / Android 13
  Env      : prod (shruti.singhal1@mailinator.com)
  Mode     : BrowserStack
  Label    : Sanity 2026-05-22
  Upload   : needed (APK newer than current bs:// URL) | skip
Proceed? [y/n]
```

---

## Step 1 — Upload (skip if `--skip-upload` or APK unchanged)

```bash
cd /c/code/master/MobileAutoQA && \
  python -m utils.browserstack_upload apps/{build} --custom-id UZIO_{ENV}_{date}
```
Run in background (uploads take 1–3 min). Write the returned `bs://...` into
`config.yaml` → `app.android.browserstack_app` (or `app.ios.browserstack_app`).

---

## Step 2 — Open the live dashboard (optional)
```bash
start "" "https://app-automate.browserstack.com/dashboard/v2/builds?keyword=Sanity%20{date}"
```

---

## Step 3 — Execute the sanity suite

```bash
cd /c/code/master/MobileAutoQA && \
  MAQA_PLATFORM={android|ios} MAQA_ENVIRONMENT={prod|qa} \
  python -m pytest tests/sanity --suite=sanity --build="Sanity {date}" \
  2>&1 | tee .tmp/sanity-{date}.log
```
Run in background (3–8 min). Status: "Sanity running on BrowserStack — Sanity {date}."

For `--local`: prepend `MAQA_RUN_MODE=local` and ensure Appium + device are up.

---

## Step 4 — Parse results
From `.tmp/sanity-{date}.log`: pytest summary `=== N passed, M failed ... ===`.
Latest report: `ls -t reports/sanity/*/run-log.json | head -1`.

---

## Step 5 — Auto-heal failures
If any test failed, invoke the **Self-Healing Agent**:
```
/self-healing-agent sanity --from-run={run-log path}
```
Known sanity failure modes and fixes:
- **MS-09 clock-in not confirmed** → attestation modal → `dismiss_attestation_if_present()` (already wired; verify it triggered)
- **MS-10 clock-out blocked** → attestation modal (HTTP 428) → confirm checkbox + `Save and Clock Out`
- **MS-12 logout** → hamburger icon locator drift → adjust `DashboardPage.open_drawer()` candidates
- **NoSuchSessionException** → BrowserStack session timeout → re-run
Max 2 heal cycles per test.

---

## Step 6 — Report & notify (automatic + summary)
`core/reporter.py` already writes `reports/sanity/{ts}/report.html` + `run-log.json`
and posts a Google Chat card on session teardown. Then print:

```
✅ Mobile Sanity Complete
  Platform : {Android|iOS|both}
  Env      : {prod|qa}
  Device   : Samsung Galaxy S23 (Android 13)
  Result   : Passed {N}  Failed {N}  Skipped {N}
  Healed   : {N}
  Duration : {Xm Ys}
  Report   : reports/sanity/{ts}/report.html
  Chat     : posted to Mobile Dev-QA ✓
```

---

## Step 7 — `--platform=both`
Run Android (Steps 1–6), then upload/confirm IPA, set `MAQA_PLATFORM=ios`, repeat.

---

## Halt / Cancel
If the developer says "stop"/"halt" (e.g. PROD deploy in progress):
1. Stop the background pytest process.
2. Post to chat:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"text":"⚠️ MobileAutoQA sanity HALTED. Reason: {reason}. Will resume."}' \
     "$(python -c "from core.config_loader import config; print(config.get('reporting.google_chat.webhook_url'))")"
   ```
3. Confirm halt to the developer.
