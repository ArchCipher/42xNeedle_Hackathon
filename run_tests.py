#!/usr/bin/env python3
"""Test runner entry point.

Usage:
    python run_tests.py               # run all tests against dummy stub
    KNIT_TARGET=knit.py python run_tests.py   # run against real knit.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "agent_logs"
TEST_RUN_LOG = LOG_DIR / "test_runs.log"
ERROR_LOG = LOG_DIR / "errors.log"
REPORT_TMP = ROOT / ".pytest_json_report.json"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(text + "\n")


def _write_test_log(report: dict) -> None:
    summary = report.get("summary", {})
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    errored = summary.get("error", 0)
    total = summary.get("total", 0)
    duration = report.get("duration", 0.0)
    knit_target = __import__("os").environ.get("KNIT_TARGET", "tests/dummy_knit.py")

    failures = [t for t in report.get("tests", []) if t.get("outcome") in ("failed", "error")]

    if failures:
        categories = []
        for t in failures:
            node = t.get("nodeid", "unknown")
            call = t.get("call") or t.get("setup") or {}
            longrepr = call.get("longrepr", "") if isinstance(call, dict) else str(call)

            # Extract the most useful signal lines from the longrepr.
            detail_lines = []
            for line in str(longrepr).splitlines():
                stripped = line.strip()
                if stripped.startswith("E ") or stripped.startswith("AssertionError"):
                    detail_lines.append(stripped)

            # If assertion rewriting produced E-lines, use those; otherwise fall back to full longrepr.
            if detail_lines:
                detail = " | ".join(detail_lines)
            else:
                # Collapse to last meaningful non-empty line (usually the error message)
                non_empty = [l.strip() for l in str(longrepr).splitlines() if l.strip()]
                detail = non_empty[-1] if non_empty else longrepr

            # Subprocess exit code embedded in our assert messages (e.g. "got 1")
            exit_code_hint = ""
            for line in str(longrepr).splitlines():
                if "exit" in line.lower() or "returncode" in line.lower():
                    exit_code_hint = f" [{line.strip()}]"
                    break

            categories.append(f"  - {node}{exit_code_hint}\n    detail: {detail}")

        failing_block = "\n".join(categories)
        next_step = "Investigate failures above. Each detail line shows what was expected vs. returned."
    else:
        failing_block = "  (none)"
        next_step = "All tests passing. No action needed."

    score = f"{passed}/{total} passed" + (f", {failed} failed" if failed else "") + (f", {errored} error(s)" if errored else "")
    score += f" | duration: {duration:.2f}s"

    entry = (
        f"\n[{_now()}] TEST_RUN\n"
        f"Run by: run_tests.py (automated)\n"
        f"Command: {sys.executable} run_tests.py {' '.join(sys.argv[1:])}\n"
        f"Suite: tests/ | target: {knit_target}\n"
        f"Score/result: {score}\n"
        f"Main failing categories:\n{failing_block}\n"
        f"Agent response/next step: {next_step}"
    )
    _append(TEST_RUN_LOG, entry)


def _write_error_log(exc: BaseException, context: str) -> None:
    tb_lines = traceback.format_exc().strip().splitlines()
    tb_indented = "\n".join(f"  {l}" for l in tb_lines)
    entry = (
        f"\n[{_now()}] ERROR\n"
        f"Type: RUNNER_{type(exc).__name__.upper()}\n"
        f"What happened: {context} — {type(exc).__name__}: {exc}\n"
        f"Impact: Test run may not have completed; results may be missing from test_runs.log.\n"
        f"Action taken: See traceback below.\n"
        f"{tb_indented}\n"
        f"Resolved: no"
    )
    _append(ERROR_LOG, entry)


def _ensure_json_report() -> bool:
    try:
        import pytest_jsonreport  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-json-report", "-q"],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        _write_error_log(e, "installing pytest-json-report")
        return False


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    has_plugin = _ensure_json_report()

    pytest_cmd = [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-v"]
    if has_plugin:
        pytest_cmd += ["--json-report", f"--json-report-file={REPORT_TMP}"]
    pytest_cmd += sys.argv[1:]

    try:
        result = subprocess.run(pytest_cmd, cwd=ROOT)
    except Exception as e:
        _write_error_log(e, "launching pytest subprocess")
        return 1

    if has_plugin:
        try:
            if REPORT_TMP.exists():
                with open(REPORT_TMP) as f:
                    report = json.load(f)
                REPORT_TMP.unlink(missing_ok=True)
                _write_test_log(report)
        except Exception as e:
            _write_error_log(e, "parsing pytest JSON report")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
