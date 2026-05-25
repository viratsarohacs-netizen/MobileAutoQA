"""
Reporter — collects test results, screenshots, heal logs; renders an HTML report;
optionally emails the team and posts a card to Google Chat.

Used by conftest.py (pytest hooks) so every run produces:
    reports/<suite>/<timestamp>/report.html
    reports/<suite>/<timestamp>/run-log.json
    reports/<suite>/<timestamp>/*.png

The Reporting Agent (.claude/commands/reporting-agent.md) drives email/chat
delivery and can aggregate multiple run-logs.
"""

import base64
import json
import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path

import requests

from core.config_loader import config


class Reporter:
    def __init__(self, suite: str):
        self.suite = suite
        self.start = time.time()
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.run_dir = Path(config.get("reporting.output_dir", "reports")) / suite / self.timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.results = []   # list of dicts: {test_id, name, status, message, duration, screenshot, heals}
        self.bs_session_url = ""

    # ─── Recording ────────────────────────────────────────────────────────────

    def record(self, test_id, name, status, message="", duration=0.0,
               screenshot_bytes=None, heals=None):
        shot_path = ""
        if screenshot_bytes:
            shot_path = str(self.run_dir / f"{test_id}_{status}.png")
            with open(shot_path, "wb") as f:
                f.write(screenshot_bytes)
        self.results.append({
            "test_id": test_id,
            "name": name,
            "status": status,           # PASS | FAIL | SKIP
            "message": message,
            "duration": round(duration, 1),
            "screenshot": shot_path,
            "heals": heals or [],
        })

    # ─── Stats ────────────────────────────────────────────────────────────────

    @property
    def passed(self):  return sum(1 for r in self.results if r["status"] == "PASS")
    @property
    def failed(self):  return sum(1 for r in self.results if r["status"] == "FAIL")
    @property
    def skipped(self): return sum(1 for r in self.results if r["status"] == "SKIP")
    @property
    def total(self):   return len(self.results)
    @property
    def healed(self):  return sum(len(r["heals"]) for r in self.results)
    @property
    def pass_rate(self):
        return round(100 * self.passed / self.total, 1) if self.total else 0.0

    # ─── Finalize ──────────────────────────────────────────────────────────────

    def finish(self):
        duration = time.time() - self.start
        self._write_json(duration)
        html_path = self._write_html(duration)
        print(f"[Reporter] {self.suite}: {self.passed} passed, {self.failed} failed, "
              f"{self.skipped} skipped ({self.pass_rate}%)  -> {html_path}")
        # Notifications
        if config.get("reporting.google_chat.enabled", False):
            self._post_google_chat(duration, html_path)
        if config.get("reporting.email.enabled", False):
            self.send_email(html_path)
        return html_path

    def _write_json(self, duration):
        data = {
            "suite": self.suite,
            "platform": config.platform,
            "environment": config.environment,
            "run_mode": config.run_mode,
            "device": config.get(f"browserstack.{config.platform}.device", "local"),
            "build": config.get("browserstack.build", ""),
            "timestamp": self.timestamp,
            "duration_sec": round(duration, 1),
            "total": self.total, "passed": self.passed,
            "failed": self.failed, "skipped": self.skipped,
            "pass_rate": self.pass_rate, "healed": self.healed,
            "bs_session_url": self.bs_session_url,
            "results": self.results,
        }
        with open(self.run_dir / "run-log.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _write_html(self, duration):
        html_path = self.run_dir / "report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self._render_html(duration))
        return html_path

    # ─── HTML rendering (self-contained, no CDN) ────────────────────────────────

    def _render_html(self, duration):
        badge = ("🟢 HEALTHY" if self.pass_rate >= 90 else
                 "🟡 DEGRADED" if self.pass_rate >= 70 else "🔴 FAILING")
        rows = []
        for r in self.results:
            color = {"PASS": "#22c55e", "FAIL": "#ef4444", "SKIP": "#94a3b8"}[r["status"]]
            img = ""
            if r["screenshot"] and os.path.exists(r["screenshot"]):
                with open(r["screenshot"], "rb") as imgf:
                    b64 = base64.b64encode(imgf.read()).decode()
                img = (f'<details><summary>screenshot</summary>'
                       f'<img src="data:image/png;base64,{b64}" style="max-width:320px"/></details>')
            heals = ""
            if r["heals"]:
                heals = "<br>".join(f"🔧 {h}" for h in r["heals"])
            rows.append(f"""
              <tr>
                <td>{r['test_id']}</td>
                <td>{r['name']}</td>
                <td style="color:{color};font-weight:bold">{r['status']}</td>
                <td>{r['duration']}s</td>
                <td>{r['message']}{('<br>'+heals) if heals else ''}{img}</td>
              </tr>""")

        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>MobileAutoQA · {self.suite}</title>
<style>
  body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px}}
  h1{{margin:0 0 4px}} .sub{{color:#94a3b8;margin-bottom:20px}}
  .cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
  .card{{background:#1e293b;border-radius:10px;padding:16px 22px;min-width:90px}}
  .card .n{{font-size:28px;font-weight:bold}} .card .l{{color:#94a3b8;font-size:12px}}
  .badge{{display:inline-block;padding:6px 14px;border-radius:20px;background:#1e293b;font-weight:bold;margin-bottom:20px}}
  table{{width:100%;border-collapse:collapse;background:#1e293b;border-radius:10px;overflow:hidden}}
  th,td{{text-align:left;padding:10px 14px;border-bottom:1px solid #334155;vertical-align:top}}
  th{{background:#334155}} img{{border-radius:6px;margin-top:6px}}
  details summary{{cursor:pointer;color:#60a5fa}}
</style></head><body>
  <h1>MobileAutoQA · {self.suite}</h1>
  <div class="sub">{config.platform.title()} · {config.get(f'browserstack.{config.platform}.device','local')}
       · {config.environment} · {self.timestamp} · {round(duration)}s</div>
  <span class="badge">{badge} — {self.pass_rate}%</span>
  <div class="cards">
    <div class="card"><div class="n">{self.total}</div><div class="l">TOTAL</div></div>
    <div class="card"><div class="n" style="color:#22c55e">{self.passed}</div><div class="l">PASSED</div></div>
    <div class="card"><div class="n" style="color:#ef4444">{self.failed}</div><div class="l">FAILED</div></div>
    <div class="card"><div class="n" style="color:#94a3b8">{self.skipped}</div><div class="l">SKIPPED</div></div>
    <div class="card"><div class="n" style="color:#f59e0b">{self.healed}</div><div class="l">HEALED</div></div>
  </div>
  <table>
    <tr><th>ID</th><th>Test</th><th>Status</th><th>Time</th><th>Details</th></tr>
    {''.join(rows)}
  </table>
  <p class="sub" style="margin-top:20px">MobileAutoQA · {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</body></html>"""

    # ─── Google Chat ─────────────────────────────────────────────────────────

    def _post_google_chat(self, duration, html_path):
        url = config.get("reporting.google_chat.webhook_url")
        if not url:
            print("[Reporter] Google Chat enabled but webhook_url missing — skipping")
            return
        all_pass = self.failed == 0
        emoji = "✅" if all_pass else "❌"
        status = "PASSED" if all_pass else "FAILED"
        summary = f"Passed: {self.passed}  Failed: {self.failed}  Skipped: {self.skipped}  ({self.pass_rate}%)"
        details = (f"Suite: {self.suite} | {config.platform.title()} | "
                   f"{config.get(f'browserstack.{config.platform}.device','local')} | "
                   f"{round(duration)}s | Healed: {self.healed}")
        buttons = ""
        if self.bs_session_url:
            buttons = (',{"buttonList":{"buttons":[{"text":"BrowserStack",'
                       '"onClick":{"openLink":{"url":"' + self.bs_session_url + '"}}}]}}')
        body = ('{"cardsV2":[{"cardId":"maqa","card":{'
                '"header":{"title":"' + f"{emoji} MobileAutoQA · {self.suite}" + '",'
                '"subtitle":"' + status + '"},'
                '"sections":[{"widgets":['
                '{"textParagraph":{"text":"<b>' + summary + '</b>"}},'
                '{"textParagraph":{"text":"' + details + '"}}'
                + buttons +
                ']}]}}]}')
        try:
            resp = requests.post(url, data=body.encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=UTF-8"},
                                 timeout=10)
            if resp.status_code // 100 == 2:
                print("[Reporter] Posted result card to Google Chat")
            else:
                print(f"[Reporter] Google Chat returned HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Reporter] Google Chat post failed: {e}")

    # ─── Email ───────────────────────────────────────────────────────────────

    def send_email(self, html_path):
        ecfg = config.get("reporting.email", {}) or {}
        from_addr = config.get("reporting.email.from_addr")
        password = config.get("reporting.email.password")
        to_addrs = config.get("reporting.email.to_addrs", []) or []
        if not (from_addr and password and to_addrs):
            print("[Reporter] Email enabled but from_addr/password/to_addrs missing — skipping")
            return

        all_pass = self.failed == 0
        status = "PASSED ✅" if all_pass else "FAILED ❌"
        prefix = config.get("reporting.email.subject_prefix", "[MobileAutoQA]")
        subject = f"{prefix} {self.suite} {status} — {self.passed}/{self.total} ({self.pass_rate}%)"

        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        with open(html_path, "r", encoding="utf-8") as f:
            html_body = f.read()
        msg.attach(MIMEText(html_body, "html"))

        # Attach failure screenshots inline
        for r in self.results:
            if r["status"] == "FAIL" and r["screenshot"] and os.path.exists(r["screenshot"]):
                with open(r["screenshot"], "rb") as imgf:
                    img = MIMEImage(imgf.read())
                    img.add_header("Content-Disposition", "attachment",
                                   filename=f"{r['test_id']}_fail.png")
                    msg.attach(img)

        try:
            host = config.get("reporting.email.smtp_host", "smtp.gmail.com")
            port = int(config.get("reporting.email.smtp_port", 587))
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(from_addr, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
            print(f"[Reporter] Emailed report to {to_addrs}")
        except Exception as e:
            print(f"[Reporter] Email send failed: {e}")
