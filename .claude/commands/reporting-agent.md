# Reporting Agent

**Role:** Generates reports with screenshots and emails the team (and posts to
Google Chat). Aggregates results across runs and platforms.

This is **Agent 5 of 5**:
> Requirements Agent → Test Generation Agent → Execution Agent → Self-Healing Agent → **Reporting Agent**

---

## Usage

```
/reporting-agent sanity                    ← report on latest sanity run
/reporting-agent PHIX-97533                ← report on a ticket's run(s)
/reporting-agent --all                     ← aggregate all suites
/reporting-agent sanity --email            ← also email the team
/reporting-agent sanity --no-chat          ← suppress Google Chat post
```

---

## What's Already Automatic

`core/reporter.py` runs in the pytest session teardown and ALWAYS produces, per run:
- `reports/{suite}/{timestamp}/report.html` — self-contained HTML (inline screenshots, heal log, badge)
- `reports/{suite}/{timestamp}/run-log.json` — machine-readable
- `*.png` screenshots (pass + fail, per config)
- A Google Chat card (if `reporting.google_chat.enabled` + webhook in secrets.yaml)
- An email (if `reporting.email.enabled` + SMTP creds in secrets.yaml)

This agent is for **aggregation, re-delivery, and richer summaries** beyond the
single-run auto-report.

---

## Step 1 — Discover Run Logs

```bash
find reports -name run-log.json | sort -r
```
Filter by `--suite` / ticket / `--all`. Parse each into a RunResult.

---

## Step 2 — Compute Aggregate Stats

- Overall: total tests, pass rate, healed count
- Per suite/ticket/platform: pass rate, duration
- **Flaky tests:** same test PASS in one run, FAIL in another (needs >1 run)
- **Failure categories:** locator / timeout / assertion / crash / infra
- Health badge: 🟢 ≥90% · 🟡 70–89% · 🔴 <70%
- Android vs iOS comparison (if both ran)

---

## Step 3 — Generate Aggregate HTML

Write `reports/summary-{timestamp}.html` (self-contained, no CDN, `<details>` for
collapse). Sections:
1. Header + generation time + health badge
2. Summary cards: Total / Passed / Failed / Healed / Pass-rate
3. Per-suite table (suite, platform, device, date, passed, failed, rate, link)
4. **Failed tests** (prominent, expanded) with screenshot thumbnails
5. Android vs iOS comparison (if applicable)
6. Auto-healed tests table (test, original → healed, strategy)
7. Flaky tests (if >1 run)
8. Footer

Reuse the styling from `core/reporter.py` `_render_html()` for visual consistency.

---

## Step 4 — Email the Team

The Reporter already has `send_email()`. To send/re-send an aggregate:

```bash
cd /c/code/master/MobileAutoQA && python -c "
from core.reporter import Reporter
# Build a Reporter from an existing run-log, or call send_email on the run dir's html
"
```

Or, for the simple per-run case, ensure in `config.yaml`:
```yaml
reporting:
  email:
    enabled: true
    to_addrs: ["mobile-dev-qa@uzio.com"]
```
and SMTP creds in `secrets.yaml` (`from_addr`, `password` = Gmail app password).

**Email contents:**
- Subject: `[MobileAutoQA] {suite} PASSED|FAILED — {passed}/{total} ({rate}%)`
- Body: the HTML report inline
- Attachments: failure screenshots

**SAFETY:** Email sending is an explicit-permission action. Before sending to
real recipients, show the developer the recipient list + subject and ask
"Send this report to {recipients}? [y/n]". Never email without confirmation.

---

## Step 5 — Google Chat

The per-run card posts automatically. For an aggregate summary card, post a
textual rollup to the Mobile Dev-QA space:

```bash
WEBHOOK=$(python -c "from core.config_loader import config; print(config.get('reporting.google_chat.webhook_url'))")
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"text":"📊 *MobileAutoQA Summary*\n\nSanity: 31/33 (93.9%) 🟡 · Android\nPHIX-97533: 20/20 (100%) 🟢 · Both\n\nHealed: 3 · Report: reports/summary-{ts}.html"}' \
  "$WEBHOOK"
```

---

## Step 6 — Output

```
✅ Report delivered

Suites      : {N}
Total tests : {N} ({rate}%)
Health      : 🟢|🟡|🔴
Healed      : {N}

Aggregate report: reports/summary-{timestamp}.html
Email           : sent to {recipients}  (or "skipped")
Google Chat     : posted ✓  (or "skipped")
```

---

## Notes
- Keep reports self-contained so they can be opened from email or shared drives.
- Screenshots are embedded as base64 in the HTML and attached to email.
- Never expose credentials or webhook URLs in report output.
