"""
Regenerate the Extent-styled HTML report from a stored run-log.json.

Useful when:
- You want to refresh the styling without re-running tests
- You're sharing an old report and want it in the latest look
- The original report.html was deleted but the run-log.json + screenshots remain

Usage:
    python -m utils.extent_report                                # most recent run
    python -m utils.extent_report reports/sanity/<ts>/run-log.json
"""
import glob
import json
import os
import sys
from pathlib import Path

from core.reporter import render_extent_html


def _most_recent_runlog():
    candidates = sorted(glob.glob("reports/*/*/run-log.json"),
                        key=os.path.getmtime, reverse=True)
    return candidates[0] if candidates else None


def main():
    if len(sys.argv) >= 2:
        path = sys.argv[1]
    else:
        path = _most_recent_runlog()
        if not path:
            raise SystemExit("No run-log.json found under reports/. Run a suite first.")
        print(f"[extent] using most recent: {path}")

    path = Path(path)
    if not path.exists():
        raise SystemExit(f"Not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    snap = {
        "suite":       data.get("suite", ""),
        "platform":    data.get("platform", "android"),
        "device":      data.get("device", "local"),
        "run_mode":    data.get("run_mode", ""),
        "environment": data.get("environment", ""),
        "build":       data.get("build", ""),
        "timestamp":   data.get("timestamp", ""),
        "duration":    data.get("duration_sec", 0),
        "total":       data.get("total", 0),
        "passed":      data.get("passed", 0),
        "failed":      data.get("failed", 0),
        "skipped":     data.get("skipped", 0),
        "pass_rate":   data.get("pass_rate", 0.0),
        "healed":      data.get("healed", 0),
        "results":     data.get("results", []),
        "generated":   "",
    }
    html = render_extent_html(snap)
    out = path.parent / "report.html"
    out.write_text(html, encoding="utf-8")
    print(f"[extent] wrote {out}  ({snap['passed']}/{snap['total']} passed, {snap['pass_rate']}%)")


if __name__ == "__main__":
    main()
