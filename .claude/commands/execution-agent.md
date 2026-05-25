# Execution Agent

**Role:** Runs tests on a physical device or simulator (Android & iOS), or on
BrowserStack cloud. Monitors the run and hands failures to the Self-Healing Agent.

This is **Agent 3 of 5**:
> Requirements Agent → Test Generation Agent → **Execution Agent** → Self-Healing Agent → Reporting Agent

---

## Usage

```
/execution-agent PHIX-97533                 ← run a ticket's tests
/execution-agent sanity                      ← run sanity suite
/execution-agent regression                  ← run regression suite
/execution-agent PHIX-97533 --platform=ios   ← iOS
/execution-agent PHIX-97533 --platform=both  ← Android then iOS
/execution-agent sanity --local              ← local device/simulator
/execution-agent sanity -k clock_in          ← single test by keyword
```

---

## Step 0 — Pre-flight

1. **Verify tests exist:**
   ```bash
   ls tests/jira/{JIRA-ID}/test_*.py     # or tests/sanity / tests/regression
   ```
   If missing: "No tests for {JIRA-ID}. Run `/test-generation-agent {JIRA-ID}` first."

2. **Verify Python env:**
   ```bash
   cd /c/code/master/MobileAutoQA && python -c "import appium, pytest, yaml, requests" \
     || pip install -r requirements.txt
   ```

3. **Verify secrets:**
   ```bash
   ls config/secrets.yaml || echo "MISSING — copy config/secrets.example.yaml"
   ```

4. **Resolve run target:**
   - **BrowserStack** (default): ensure `app.<platform>.browserstack_app` is set in config.yaml.
     If blank, upload first:
     ```bash
     python -m utils.browserstack_upload apps/{newest}.apk --custom-id UZIO_PROD
     ```
     Then write the returned `bs://...` into config.yaml.
   - **Local** (`--local`): ensure an Appium server is running (`appium` on :4723) and a
     device/emulator/simulator is connected (`adb devices` / `xcrun simctl list`).

5. **Confirm with developer:**
   ```
   Run target:
     Suite/Ticket : {target}
     Platform     : {android | ios}
     Run mode     : BrowserStack | Local
     Device       : {device}
     Environment  : {prod | qa}
     Test count   : {N}
   Proceed? [y/n]
   ```

---

## Step 1 — Run

**BrowserStack / single platform:**
```bash
cd /c/code/master/MobileAutoQA && \
  MAQA_PLATFORM={android|ios} \
  MAQA_ENVIRONMENT={prod|qa} \
  python -m pytest tests/jira/{JIRA-ID} \
    --suite={JIRA-ID} \
    --build="{JIRA-ID} {date}" \
    2>&1 | tee .tmp/run-{JIRA-ID}.log
```

For sanity:  `python -m pytest tests/sanity --suite=sanity --build="Sanity {date}"`
For regression: `python -m pytest tests/regression --suite=regression`

**Run in background** — runs take 3–15 min. Status update:
> "Tests running on {platform}/{mode} — {target}. Watching for completion."

---

## Step 2 — Local Device Notes

When `--local`:
- **Android:** `appium` server + `adb devices` shows the device. Set
  `MAQA_RUN_MODE=local MAQA_APPIUM_ANDROID_DEVICE=<serial>`.
- **iOS simulator:** `xcrun simctl list devices` for the UDID. Requires Xcode +
  `appium driver install xcuitest`. Set `MAQA_RUN_MODE=local`.
- **iOS physical device:** needs WebDriverAgent signing — note this is a one-time setup.

---

## Step 3 — Parse Results

After pytest exits, read `.tmp/run-{target}.log`:
- pytest summary line: `=== N passed, M failed, K skipped in Xs ===`
- Exit code 0 = all passed; non-zero = failures
- Find the report: `ls -t reports/{target}/*/run-log.json | head -1`

Parse `run-log.json` for per-test status, messages, screenshots, and heal entries.

---

## Step 4 — On Failure → Self-Healing Agent

If any test failed, automatically invoke:
```
/self-healing-agent {target} --from-run={run-log path}
```
Pass the failure messages, screenshots, and heal logs. After the healer patches
and re-runs, collect the updated result.

**Max heal cycles:** 2. If still failing, mark as a real failure and continue to reporting.

---

## Step 5 — Platform=both

When `--platform=both`:
1. Run Android, collect result
2. Ensure `app.ios.browserstack_app` set (upload IPA if needed)
3. Run iOS with `MAQA_PLATFORM=ios`
4. Both runs produce separate run-logs under the same suite name

---

## Step 6 — Handoff to Reporting

```
✅ Execution complete — {target}
   Platform : {android|ios|both}
   Passed   : {N}   Failed: {N}   Skipped: {N}
   Healed   : {N}
   Run log  : reports/{target}/{timestamp}/run-log.json

Next: /reporting-agent {target}   (or it auto-runs)
```

Note: The Reporter (`core/reporter.py`) already writes the HTML report and posts
to Google Chat in the pytest session teardown. The Reporting Agent adds email
delivery and cross-run aggregation.

---

## Error Handling

| Failure | Action |
|---------|--------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| BrowserStack 401 | Check `browserstack.access_key` in secrets.yaml |
| `app.*.browserstack_app` blank | Upload via utils/browserstack_upload.py |
| No local device | `adb devices` / start emulator; for iOS check `xcrun simctl` |
| All skipped | Device/OS combo unavailable on BrowserStack — try fallback device |
| Session timeout (NoSuchSession) | Re-run; known BrowserStack flakiness |
| Attestation modal blocks clock-out | Healer adds `dismiss_attestation_if_present()` |
