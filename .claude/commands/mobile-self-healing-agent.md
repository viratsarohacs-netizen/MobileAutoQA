# Self-Healing Agent

**Role:** Auto-fixes failed tests by analyzing the root cause, patching the test
or page object, and re-running.

This is **Agent 4 of 5**:
> Requirements Agent → Test Generation Agent → Execution Agent → **Self-Healing Agent** → Reporting Agent

---

## Usage

```
/mobile-self-healing-agent sanity
/mobile-self-healing-agent PHIX-97533
/mobile-self-healing-agent sanity --test=test_ms09_clock_in
/mobile-self-healing-agent PHIX-97533 --from-run=reports/PHIX-97533/2026-05-22_14-30-00/run-log.json
```

---

## Two Layers of Healing

1. **Runtime healing (already automatic):** `core/element_healer.py` applies 6
   text-matching strategies during the run. Heals are logged to each test's
   `_heal_log` and surface in the report. You don't trigger this — it's built in.

2. **Code healing (this agent):** When a test still FAILS after runtime healing,
   this agent diagnoses WHY from the screenshot + log, then patches the Python
   code so the fix is permanent.

---

## Step 0 — Load Failure Context

Read the run-log:
```bash
cat $(ls -t reports/{TARGET}/*/run-log.json | head -1)
```

For each `"status": "FAIL"` result, gather:
- `test_id`, `name`
- `message` (assertion/exception text)
- `screenshot` (path — **open and look at it**)
- `heals` (what runtime healing already tried)

**Open the run's `report.html` (Extent-styled HTML)** — every test card has an
inline screenshot and the self-healing log. The screenshot is the ground truth
for what the app actually showed (this is exactly how the location-dialog and
weather-app-launch bugs were diagnosed). Path:
```
reports/<suite>/<latest-timestamp>/report.html
```
Or read the raw PNGs / `run-log.json` directly under that same folder.

Read the failing test file and the page objects it uses.

---

## Step 1 — Diagnose (root-cause table)

| Symptom in message / screenshot | Root cause | Fix |
|---------------------------------|------------|-----|
| `Element not found after healing: 'X'` + screenshot shows the element with different text | Label changed (i18n / white-label / `.toUpperCase()`) | Update the constant in `core/locators.py` |
| `Element not found` + screenshot shows a dialog/sheet on top | New popup blocking flow | Add `dismiss_popup_if_present(...)` / `dismiss_attestation_if_present()` before the step |
| `Clocked-in state not shown after 90s` + screenshot shows attestation modal | Attestation modal not handled at this point | Call `dashboard.dismiss_attestation_if_present()` in the page method |
| `Clocked-in state not shown` + screenshot shows a NEW status word | Clocked-in indicator changed | Add the new word to `TimeTracking.CLOCKED_IN_INDICATORS` in `core/locators.py` |
| `'X' not visible after Ns` + screenshot shows spinner | Timing/slow network | Increase the timeout for that step |
| `NoSuchSessionException` | BrowserStack session died | Infra, not a code bug — re-run; advise increasing session timeout |
| Element correct in ticket but absent in app | Feature not deployed | **Do NOT patch.** Escalate to developer |

**Always open the failure screenshot before deciding.** The screenshot is the
ground truth for what the app actually showed.

---

## Step 2 — Apply the Patch

Edit the smallest possible surface:

- **Label changed** → edit `core/locators.py` only:
  ```python
  # HEALED 2026-05-22: button text changed CLOCK_OUT "Clock Out" -> "End Shift"
  CLOCK_OUT = "End Shift"
  ```

- **New blocking popup** → edit the page object method, not the test:
  ```python
  def clock_out(self):
      self.tap(TimeTracking.CLOCK_OUT)
      self._dashboard().dismiss_attestation_if_present()   # already present
      self.dismiss_popup_if_present("New Consent", 3)      # HEALED 2026-05-22
      ...
  ```

- **New clocked-in indicator** → edit `core/locators.py`:
  ```python
  CLOCKED_IN_INDICATORS = ["Clock Out", "Clocked In", "You are Clocked In",
                           "Shift Active"]   # HEALED 2026-05-22
  ```

- **Timing** → edit the test or page wait:
  ```python
  tt.wait_for_clocked_in(120)   # HEALED: increased from 90s (slow on BrowserStack)
  ```

**Rules:**
- Add a `# HEALED <date>: <reason>` comment on every change
- Never change `test_id`, test names, or assertions' intent
- Prefer fixing `core/locators.py` (one place, helps all tests) over per-test hacks
- If a page object lacks a needed step, add a method there

---

## Step 3 — Re-run Failed Tests Only

```bash
cd /c/code/master/MobileAutoQA && \
  MAQA_PLATFORM={platform} \
  python -m pytest {test_file} -k "{failed_test_name}" \
    --suite={TARGET} 2>&1 | tee .tmp/heal-{TARGET}.log
```

---

## Step 4 — Also Update the Plain-English Spec

Keep `mobile.test.md` (or `sanity.test.md`) in sync so future regeneration is correct:

```markdown
# Before:
tap "Clock Out"
verify clocked out

# After:
dismiss popup if present: "New Consent"   ← HEALED 2026-05-22: consent popup added
tap "Clock Out"
verify clocked out
```

---

## Step 5 — Report Outcome

```
🔧 Healed: MS-09 (test_ms09_clock_in)
   Root cause : Attestation modal appeared after Clock In
   Fix        : added dismiss_attestation_if_present() in TimeTrackingPage.clock_in()
   Re-run     : PASSED ✅

🔧 Healed: MS-10 (test_ms10_clock_out)
   Root cause : "Clock Out" label changed to "End Shift" in new build
   Fix        : core/locators.py TimeTracking.CLOCK_OUT
   Re-run     : PASSED ✅

🚨 Escalated: TC-07 (team timesheet visibility)
   Root cause : feature appears not deployed in this build
   Action     : confirm PHIX-97533 is in the tested APK — not a test bug
```

Pass results to the Reporting Agent so heals appear in the final report.

---

## Guardrails — Do NOT Auto-Patch
- Feature-not-deployed failures (escalate)
- Failures where the app behavior is wrong (that's a real defect — escalate, suggest filing)
- Anything requiring credentials or data you don't have
