"""
Generate / open / serve the Allure HTML report.

Results are written by pytest to  reports/allure-results  (via pytest.ini addopts).
This script turns them into the rich HTML report at  reports/allure-report.

Usage:
    python -m utils.allure_report              # generate, then open in browser
    python -m utils.allure_report --generate   # generate only (no open)
    python -m utils.allure_report --serve       # ephemeral serve (temp report)

History/trends: the previous report's `history/` is copied back into the results
before generating, so trend graphs accumulate across runs.

Requires the Allure CLI (npm i -g allure-commandline) and Java (JDK 11+).
"""

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "reports" / "allure-results"
REPORT = ROOT / "reports" / "allure-report"


def _run(cmd, **kw):
    # allure is an npm global shim (allure.cmd on Windows) — shell=True resolves it
    print(f"[Allure] $ {cmd}")
    return subprocess.run(cmd, shell=True, **kw)


def _preserve_history():
    prev = REPORT / "history"
    if prev.exists():
        dest = RESULTS / "history"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(prev, dest)
        print("[Allure] Preserved previous history for trends")


def generate(open_after=True):
    if not RESULTS.exists() or not any(RESULTS.iterdir()):
        raise SystemExit(f"No Allure results in {RESULTS}. Run the suite first.")
    _preserve_history()
    r = _run(f'allure generate "{RESULTS}" -o "{REPORT}" --clean')
    if r.returncode != 0:
        raise SystemExit("[Allure] generate failed")
    print(f"[Allure] Report generated -> {REPORT}")
    if open_after:
        # `allure open` starts a local web server and opens the browser (blocks).
        _run(f'allure open "{REPORT}"')


def serve():
    if not RESULTS.exists() or not any(RESULTS.iterdir()):
        raise SystemExit(f"No Allure results in {RESULTS}. Run the suite first.")
    _run(f'allure serve "{RESULTS}"')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true", help="generate only, do not open")
    ap.add_argument("--serve", action="store_true", help="ephemeral serve")
    args = ap.parse_args()
    if args.serve:
        serve()
    else:
        generate(open_after=not args.generate)
