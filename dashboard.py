"""
MobileAutoQA — Web Dashboard (Core Runner)
==========================================

A localhost Streamlit console to trigger the sanity/regression suites on a local
device or BrowserStack, with live log streaming and a link to the HTML report.

Run it:
    cd C:\\code\\master\\MobileAutoQA
    streamlit run dashboard.py

IMPORTANT: this must run on the machine that has adb, the Appium server, the
physical device, and config/secrets.yaml — it shells out to `python -m pytest`
with MAQA_* environment overrides (no edits to config.yaml).
"""

import os
import re
import subprocess
import sys
import time
from glob import glob
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

# ─── Static catalogs ──────────────────────────────────────────────────────────

SUITES = {
    "Sanity": "tests/sanity",
    "Regression": "tests/regression",
}

# Friendly labels for known tests (fallback: the raw method name)
TEST_LABELS = {
    "test_ms01_app_launch_and_login": "MS-01 · App launch & login",
    "test_ms03_bottom_navigation": "MS-03 · Bottom navigation",
    "test_ms04_time_tracking_screen": "MS-04 · Time Tracking screen",
    "test_ms09_clock_in": "MS-09 · Clock In",
    "test_ms10_clock_out": "MS-10 · Clock Out",
    "test_ms12_logout": "MS-12 · Logout",
    "test_r_tt_01_clock_in_out_cycle": "R-TT-01 · Clock in/out cycle",
    "test_r_tt_02_break_flow": "R-TT-02 · Break flow",
}

BROWSERSTACK_DEVICES = {
    "android": [
        ("Samsung Galaxy S23", "13.0"),
        ("Samsung Galaxy S22", "12.0"),
        ("Google Pixel 7", "13.0"),
        ("OnePlus 9", "11.0"),
    ],
    "ios": [
        ("iPhone 15", "17.0"),
        ("iPhone 14", "16.0"),
        ("iPhone 13", "15.0"),
    ],
}


# ─── Helpers ────────────────────────────────────────────────────────────────

def list_adb_devices():
    """Return list of authorized local Android device serials."""
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    devices = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def appium_running(url="http://localhost:4723/status"):
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


@st.cache_data(show_spinner=False, ttl=30)
def collect_tests(suite_path):
    """Discover test node IDs in a suite via pytest --collect-only.

    `-o addopts=` clears pytest.ini's `-v` so `-q` yields flat node IDs
    (path::Class::method) instead of the verbose tree.
    """
    try:
        out = subprocess.run(
            [PYTHON, "-m", "pytest", suite_path, "--collect-only", "-q",
             "-o", "addopts=", "-p", "no:cacheprovider"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=60,
        ).stdout
    except Exception:
        return []
    return [ln.strip() for ln in out.splitlines()
            if "::" in ln and "test_" in ln]


def label_for(node_id):
    method = node_id.split("::")[-1]
    return TEST_LABELS.get(method, method)


def latest_report(suite_name):
    pattern = str(ROOT / "reports" / suite_name / "*" / "report.html")
    files = glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


# ─── Page ──────────────────────────────────────────────────────────────────

st.set_page_config(page_title="MobileAutoQA Runner", page_icon="📱", layout="wide")
st.title("📱 MobileAutoQA — Test Runner")

# Pre-flight status row
c1, c2, c3 = st.columns(3)
appium_ok = appium_running()
adb_devices = list_adb_devices()
c1.metric("Appium server", "🟢 Up" if appium_ok else "🔴 Down", help="http://localhost:4723")
c2.metric("Local devices", f"{len(adb_devices)} connected",
          help=", ".join(adb_devices) if adb_devices else "Run: adb devices")
secrets_ok = (ROOT / "config" / "secrets.yaml").exists()
c3.metric("secrets.yaml", "🟢 Present" if secrets_ok else "🔴 Missing")

st.divider()

# ─── Configuration controls ───────────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.subheader("Target")
    platform = st.radio("Platform", ["android", "ios"], horizontal=True)
    run_mode = st.radio("Run mode", ["local", "browserstack"], horizontal=True)
    environment = st.radio("Environment", ["qa", "prod"], horizontal=True)

    device_udid = ""
    bs_device = ""
    bs_os = ""
    if run_mode == "local":
        if platform == "android":
            if adb_devices:
                device_udid = st.selectbox("Local device (adb)", adb_devices)
            else:
                st.warning("No authorized Android devices. Plug in & accept USB-debugging.")
        else:
            device_udid = st.text_input("iOS device UDID (blank = first simulator)", "")
    else:
        opts = BROWSERSTACK_DEVICES[platform]
        idx = st.selectbox("BrowserStack device", range(len(opts)),
                           format_func=lambda i: f"{opts[i][0]} (Android {opts[i][1]})"
                           if platform == "android" else f"{opts[i][0]} (iOS {opts[i][1]})")
        bs_device, bs_os = opts[idx]

with right:
    st.subheader("Tests")
    suite_name = st.selectbox("Suite", list(SUITES.keys()))
    suite_path = SUITES[suite_name]
    node_ids = collect_tests(suite_path)
    if node_ids:
        run_all = st.checkbox("Run entire suite", value=True)
        selected = node_ids
        if not run_all:
            chosen = st.multiselect(
                "Select tests", node_ids,
                default=node_ids, format_func=label_for)
            selected = chosen
    else:
        st.warning(f"No tests discovered in {suite_path}")
        selected = []
    default_build = f"{suite_name} {environment.upper()} {time.strftime('%d-%m-%Y')}"
    build_label = st.text_input("Build / label", default_build)

# ─── Build the command preview ─────────────────────────────────────────────
def build_env():
    env = os.environ.copy()
    env["MAQA_PLATFORM"] = platform
    env["MAQA_RUN_MODE"] = run_mode
    env["MAQA_ENVIRONMENT"] = environment
    if run_mode == "local" and device_udid:
        key = "MAQA_APPIUM_ANDROID_DEVICE" if platform == "android" else "MAQA_APPIUM_IOS_DEVICE"
        env[key] = device_udid
    if run_mode == "browserstack":
        env[f"MAQA_BROWSERSTACK_{platform.upper()}_DEVICE"] = bs_device
        env[f"MAQA_BROWSERSTACK_{platform.upper()}_OS_VERSION"] = bs_os
    env["PYTHONUNBUFFERED"] = "1"
    return env


def build_cmd():
    targets = selected if selected else [suite_path]
    return [PYTHON, "-m", "pytest", *targets,
            "--suite", suite_name.lower(), "--build", build_label,
            "-v", "--color=no", "-p", "no:cacheprovider"]


st.divider()
cmd = build_cmd()
with st.expander("Command preview"):
    st.code(" ".join(f'"{c}"' if " " in c else c for c in cmd), language="bash")
    overrides = {k: v for k, v in build_env().items() if k.startswith("MAQA_")}
    st.json(overrides)

# Pre-run validation
warnings = []
if run_mode == "local" and platform == "android" and not adb_devices:
    warnings.append("No local Android device connected.")
if run_mode == "local" and not appium_ok:
    warnings.append("Appium server is not running on :4723.")
if not selected:
    warnings.append("No tests selected.")
for w in warnings:
    st.warning("⚠️ " + w)

# ─── Run ──────────────────────────────────────────────────────────────────
run_disabled = bool(warnings)
if st.button("▶️ Start run", type="primary", disabled=run_disabled, use_container_width=True):
    st.session_state["last_suite"] = suite_name.lower()
    log_box = st.empty()
    status = st.status("Running pytest…", expanded=True)
    lines = []
    t0 = time.time()
    proc = subprocess.Popen(
        cmd, env=build_env(), cwd=str(ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in proc.stdout:
        lines.append(line.rstrip("\n"))
        log_box.code("\n".join(lines[-500:]), language="text")
    proc.wait()
    dur = round(time.time() - t0)

    # Parse the pytest summary line
    summary = next((l for l in reversed(lines)
                    if "passed" in l or "failed" in l or "error" in l), "")
    if proc.returncode == 0:
        status.update(label=f"✅ Passed in {dur}s — {summary}", state="complete")
    else:
        status.update(label=f"❌ Finished in {dur}s (exit {proc.returncode}) — {summary}",
                      state="error")

# ─── Allure report (primary) ─────────────────────────────────────────────────
st.divider()
st.subheader("📊 Allure report")
allure_results = ROOT / "reports" / "allure-results"
has_results = allure_results.exists() and any(allure_results.iterdir())
ac1, ac2 = st.columns([1, 1])
if ac1.button("Generate & open Allure report", type="primary",
              disabled=not has_results, use_container_width=True):
    with st.spinner("Generating Allure report…"):
        # generate (preserves history) then open in a detached server
        subprocess.run([PYTHON, "-m", "utils.allure_report", "--generate"],
                       cwd=str(ROOT))
        subprocess.Popen('allure open "%s"' % (ROOT / "reports" / "allure-report"),
                         shell=True, cwd=str(ROOT))
    st.success("Allure report generated and opened in your browser.")
if ac2.button("Serve Allure (ephemeral)", disabled=not has_results,
              use_container_width=True):
    subprocess.Popen([PYTHON, "-m", "utils.allure_report", "--serve"], cwd=str(ROOT))
    st.info("Allure serve started — it will open in your browser shortly.")
if not has_results:
    st.caption("Run a suite first — pytest writes Allure results to reports/allure-results.")

# ─── Custom HTML report (legacy) ─────────────────────────────────────────────
with st.expander("Legacy HTML report"):
    report_suite = st.session_state.get("last_suite", suite_name.lower())
    report = latest_report(report_suite)
    if report:
        st.caption(report)
        with open(report, "rb") as f:
            st.download_button("⬇️ Download report.html", f, file_name="report.html",
                               mime="text/html", use_container_width=True)
        if st.toggle("View inline"):
            with open(report, "r", encoding="utf-8") as f:
                components.html(f.read(), height=700, scrolling=True)
    else:
        st.info(f"No legacy report yet for suite '{report_suite}'.")
