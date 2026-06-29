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

    # ─── HTML rendering — Extent-styled, self-contained (inline CSS+JS+images) ─

    def _render_html(self, duration):
        return render_extent_html(self.snapshot(duration))

    def snapshot(self, duration):
        """Bundle everything needed to render the Extent report — also used by
        utils/extent_report.py to regenerate from a run-log.json."""
        return {
            "suite": self.suite,
            "platform": config.platform,
            "device": config.get(f"browserstack.{config.platform}.device", "local"),
            "run_mode": config.run_mode,
            "environment": config.environment,
            "build": config.get("browserstack.build", ""),
            "timestamp": self.timestamp,
            "duration": duration,
            "total": self.total, "passed": self.passed,
            "failed": self.failed, "skipped": self.skipped,
            "pass_rate": self.pass_rate, "healed": self.healed,
            "results": self.results,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

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


# ─── Extent-styled HTML rendering (module-level so utils/extent_report can reuse) ─
# Single self-contained file: inline CSS + minimal vanilla JS + base64-embedded
# screenshots. No CDN, no external assets. Open by double-clicking — works offline.

_EXTENT_CSS = """
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:#0d1117;color:#c9d1d9;margin:0;font-size:14px;line-height:1.45}
.layout{display:flex;min-height:100vh}
.sidebar{width:220px;background:#161b22;border-right:1px solid #30363d;
         display:flex;flex-direction:column;flex-shrink:0}
.brand{padding:18px 22px;font-weight:700;font-size:15px;color:#fff;
       border-bottom:1px solid #30363d}
.brand .sub{font-size:11px;color:#8b949e;font-weight:400;margin-top:2px}
.nav{padding:10px 0;flex:1}
.nav a{display:flex;align-items:center;gap:10px;padding:10px 22px;color:#c9d1d9;
       text-decoration:none;font-size:13px;border-left:3px solid transparent;cursor:pointer}
.nav a:hover{background:#1f2937}
.nav a.active{border-left-color:#4FB3F9;background:#1c2230;color:#fff;font-weight:600}
.nav .icon{width:14px;text-align:center}
.env{padding:14px 22px;color:#8b949e;font-size:11px;line-height:1.7;
     border-top:1px solid #30363d}
.env div{margin-bottom:2px}
main{flex:1;min-width:0}
.topbar{padding:16px 28px;background:#161b22;border-bottom:1px solid #30363d;
        display:flex;justify-content:space-between;align-items:center;gap:18px}
.topbar h1{margin:0;font-size:19px;color:#fff;font-weight:600}
.topbar .meta{font-size:12px;color:#8b949e;margin-top:2px}
.badge{padding:7px 16px;border-radius:18px;font-weight:700;font-size:12px;
       letter-spacing:.5px;text-transform:uppercase;color:#fff}
.tab{padding:24px 28px;display:none}
.tab.active{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
       gap:12px;margin-bottom:20px}
.card{background:#1c2230;border:1px solid #30363d;border-radius:10px;
      padding:16px 18px}
.card .n{font-size:30px;font-weight:700;line-height:1.1}
.card .l{color:#8b949e;font-size:11px;margin-top:4px;
         text-transform:uppercase;letter-spacing:.5px}
.dash-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
@media (max-width:980px){.dash-row{grid-template-columns:1fr}}
.panel{background:#1c2230;border:1px solid #30363d;border-radius:10px;padding:18px 20px}
.panel h3{margin:0 0 14px;font-size:12px;color:#c9d1d9;font-weight:600;
          text-transform:uppercase;letter-spacing:.5px}
.donut-wrap{display:flex;align-items:center;gap:24px;flex-wrap:wrap}
.donut{position:relative}
.donut .center{position:absolute;inset:0;display:flex;flex-direction:column;
               align-items:center;justify-content:center;pointer-events:none}
.donut .center .pct{font-size:28px;font-weight:700;color:#fff;line-height:1}
.donut .center .lbl{font-size:10px;color:#8b949e;margin-top:3px;
                    text-transform:uppercase;letter-spacing:.5px}
.legend{display:flex;flex-direction:column;gap:8px;font-size:13px;color:#c9d1d9}
.legend .row{display:flex;align-items:center;gap:10px}
.legend .dot{width:11px;height:11px;border-radius:50%}
.legend .n{margin-left:auto;color:#8b949e;font-variant-numeric:tabular-nums}
table.env-table{width:100%;font-size:13px;border-collapse:collapse}
table.env-table td{padding:7px 0;border-bottom:1px solid #30363d}
table.env-table tr:last-child td{border-bottom:none}
table.env-table td:first-child{color:#8b949e;width:38%}
table.env-table td:last-child{color:#c9d1d9}
.gauge{margin-top:6px}
.gauge .bar{height:8px;background:#30363d;border-radius:4px;overflow:hidden}
.gauge .fill{height:100%;background:linear-gradient(90deg,#3FB950,#4FB3F9)}
.gauge .gmeta{display:flex;justify-content:space-between;font-size:11px;
              color:#8b949e;margin-top:6px}
.filters{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.filter{padding:7px 14px;background:#1c2230;border:1px solid #30363d;
        border-radius:16px;color:#c9d1d9;cursor:pointer;font-size:12px;
        font-weight:500}
.filter:hover{background:#1f2937}
.filter.active{background:#4FB3F9;color:#0d1117;border-color:#4FB3F9;font-weight:700}
.filter .n{margin-left:6px;opacity:.85}
.tests{display:flex;flex-direction:column;gap:7px}
.test{background:#1c2230;border:1px solid #30363d;border-radius:8px;overflow:hidden}
.test[open]{border-color:#4FB3F9}
.test summary{padding:11px 16px;cursor:pointer;display:flex;gap:14px;
              align-items:center;list-style:none;user-select:none}
.test summary::-webkit-details-marker{display:none}
.test summary::before{content:"▸";color:#8b949e;font-size:10px;
                      transition:transform .15s}
.test[open] summary::before{transform:rotate(90deg)}
.pill{padding:3px 10px;border-radius:11px;color:#fff;font-size:10px;
      font-weight:700;letter-spacing:.4px;min-width:46px;text-align:center}
.tid{color:#8b949e;font-family:ui-monospace,Menlo,monospace;font-size:11px;
     min-width:60px}
.tname{flex:1;font-size:13px;color:#c9d1d9}
.tdur{color:#8b949e;font-size:11px;font-variant-numeric:tabular-nums}
.body{padding:14px 18px;border-top:1px solid #30363d;background:#161b22}
.msg{background:#0d1117;border:1px solid #f8514922;border-left:3px solid #F85149;
     border-radius:5px;padding:9px 12px;font-family:ui-monospace,monospace;
     font-size:11px;color:#F85149;white-space:pre-wrap;word-break:break-word;
     margin:0 0 12px;overflow-x:auto}
.heals{margin:0 0 12px}
.heals summary{color:#D29922;cursor:pointer;font-size:12px;padding:4px 0;
               list-style:none}
.heals summary::-webkit-details-marker{display:none}
.heals summary::before{content:"▸ ";color:#D29922;font-size:9px}
.heals[open] summary::before{content:"▾ "}
.heals ul{list-style:none;padding:0;margin:6px 0 4px;font-size:12px}
.heals li{padding:3px 0 3px 14px;color:#c9d1d9}
.shot img{max-width:100%;max-height:480px;border-radius:6px;
          border:1px solid #30363d;display:block;margin-top:4px}
.empty{padding:48px;text-align:center;color:#8b949e;font-size:13px}
"""

_EXTENT_JS = """
document.querySelectorAll('.nav a').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const tab = el.dataset.tab;
    document.querySelectorAll('.nav a').forEach(n => n.classList.toggle('active', n === el));
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.id === tab));
  });
});
document.querySelectorAll('.filter').forEach(el => {
  el.addEventListener('click', () => {
    const f = el.dataset.filter;
    document.querySelectorAll('.filter').forEach(b => b.classList.toggle('active', b === el));
    document.querySelectorAll('.test').forEach(t => {
      t.style.display = (f === 'all' || t.dataset.status === f) ? '' : 'none';
    });
  });
});
"""


def _esc(s):
    """Minimal HTML-escape for user-controlled strings."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))


def _donut_svg(passed, failed, skipped, total):
    """Render the dashboard donut as a pure SVG (no JS chart lib)."""
    import math
    r = 64; cx = cy = 84; sw = 24
    C = 2 * math.pi * r
    def arc(pct, color, off):
        dash = max(0.0, pct / 100 * C)
        return (f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}" stroke-dasharray="{dash:.2f} {C:.2f}" '
                f'stroke-dashoffset="-{off:.2f}" transform="rotate(-90 {cx} {cy})"/>')
    if total == 0:
        return f'<circle r="{r}" cx="{cx}" cy="{cy}" fill="none" stroke="#30363d" stroke-width="{sw}"/>'
    p = passed / total * 100
    f_ = failed / total * 100
    s = skipped / total * 100
    return (arc(p, "#3FB950", 0)
            + arc(f_, "#F85149", p / 100 * C)
            + arc(s, "#8B949E", (p + f_) / 100 * C))


def _test_card_html(r):
    status = r["status"]
    color = {"PASS": "#3FB950", "FAIL": "#F85149", "SKIP": "#8B949E"}[status]
    # Inline screenshot
    img_html = ""
    shot = r.get("screenshot") or ""
    if shot and os.path.exists(shot):
        with open(shot, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        img_html = (f'<div class="shot"><img src="data:image/png;base64,{b64}" '
                    f'alt="screenshot for {_esc(r["test_id"])}"/></div>')
    # Self-healing log (collapsible)
    heals_html = ""
    heals = r.get("heals") or []
    if heals:
        items = "".join(f"<li>🔧 {_esc(h)}</li>" for h in heals)
        heals_html = (f'<details class="heals"><summary>Self-healing log '
                      f'({len(heals)})</summary><ul>{items}</ul></details>')
    msg_html = (f'<pre class="msg">{_esc(r.get("message", "") or "")}</pre>'
                if r.get("message") else "")
    return f"""<details class="test" data-status="{status}">
  <summary>
    <span class="pill" style="background:{color}">{status}</span>
    <span class="tid">{_esc(r['test_id'])}</span>
    <span class="tname">{_esc(r['name'])}</span>
    <span class="tdur">{r.get('duration', 0)}s</span>
  </summary>
  <div class="body">{msg_html}{heals_html}{img_html}</div>
</details>"""


def render_extent_html(snap):
    """Render the full Extent-styled HTML from a Reporter snapshot dict."""
    p, f_, s, t = snap["passed"], snap["failed"], snap["skipped"], snap["total"]
    pct = snap["pass_rate"]
    badge_label, badge_color = (
        ("Healthy", "#3FB950") if pct >= 90 else
        ("Degraded", "#D29922") if pct >= 70 else
        ("Failing", "#F85149"))
    cards = "".join(_test_card_html(r) for r in snap["results"]) or \
            '<div class="empty">No tests recorded.</div>'
    env_rows = "".join(
        f"<tr><td>{k}</td><td>{_esc(v)}</td></tr>"
        for k, v in [
            ("Suite", snap["suite"]),
            ("Platform", snap["platform"].title()),
            ("Run mode", snap["run_mode"]),
            ("Environment", snap["environment"]),
            ("Device", snap["device"]),
            ("Build", snap["build"] or "—"),
            ("Started", snap["timestamp"]),
            ("Duration", f"{round(snap['duration'])}s"),
        ])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>MobileAutoQA · {_esc(snap['suite'])}</title>
<style>{_EXTENT_CSS}</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">📱 MobileAutoQA
      <div class="sub">{_esc(snap['suite'])}</div>
    </div>
    <nav class="nav">
      <a class="active" data-tab="dashboard"><span class="icon">⭕</span>Dashboard</a>
      <a data-tab="tests"><span class="icon">🧪</span>Tests</a>
    </nav>
    <div class="env">
      <div>{_esc(snap['platform'].title())} · {_esc(snap['device'])}</div>
      <div>{_esc(snap['environment'])} · {_esc(snap['run_mode'])}</div>
      <div>{_esc(snap['timestamp'])}</div>
    </div>
  </aside>
  <main>
    <header class="topbar">
      <div>
        <h1>{_esc(snap['suite'])}</h1>
        <div class="meta">{_esc(snap['platform'].title())} · {_esc(snap['device'])}
            · {_esc(snap['environment'])} · {round(snap['duration'])}s</div>
      </div>
      <span class="badge" style="background:{badge_color}">{badge_label} · {pct}%</span>
    </header>

    <section id="dashboard" class="tab active">
      <div class="cards">
        <div class="card"><div class="n">{t}</div><div class="l">Total</div></div>
        <div class="card"><div class="n" style="color:#3FB950">{p}</div><div class="l">Passed</div></div>
        <div class="card"><div class="n" style="color:#F85149">{f_}</div><div class="l">Failed</div></div>
        <div class="card"><div class="n" style="color:#8B949E">{s}</div><div class="l">Skipped</div></div>
        <div class="card"><div class="n" style="color:#D29922">{snap['healed']}</div><div class="l">Heals</div></div>
      </div>
      <div class="dash-row">
        <div class="panel">
          <h3>Test Distribution</h3>
          <div class="donut-wrap">
            <div class="donut" style="width:168px;height:168px">
              <svg width="168" height="168" viewBox="0 0 168 168">{_donut_svg(p, f_, s, t)}</svg>
              <div class="center"><div class="pct">{pct}%</div><div class="lbl">Pass rate</div></div>
            </div>
            <div class="legend">
              <div class="row"><span class="dot" style="background:#3FB950"></span>Passed <span class="n">{p}</span></div>
              <div class="row"><span class="dot" style="background:#F85149"></span>Failed <span class="n">{f_}</span></div>
              <div class="row"><span class="dot" style="background:#8B949E"></span>Skipped <span class="n">{s}</span></div>
            </div>
          </div>
          <div class="gauge">
            <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
            <div class="gmeta"><span>Build health</span><span>{pct}%</span></div>
          </div>
        </div>
        <div class="panel">
          <h3>Environment</h3>
          <table class="env-table"><tbody>{env_rows}</tbody></table>
        </div>
      </div>
    </section>

    <section id="tests" class="tab">
      <div class="filters">
        <button class="filter active" data-filter="all">All <span class="n">{t}</span></button>
        <button class="filter" data-filter="PASS">Passed <span class="n">{p}</span></button>
        <button class="filter" data-filter="FAIL">Failed <span class="n">{f_}</span></button>
        <button class="filter" data-filter="SKIP">Skipped <span class="n">{s}</span></button>
      </div>
      <div class="tests">{cards}</div>
    </section>
  </main>
</div>
<script>{_EXTENT_JS}</script>
</body></html>"""
