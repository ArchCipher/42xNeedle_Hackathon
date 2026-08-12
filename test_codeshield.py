#!/usr/bin/env python3
"""Quick Code Shield smoke test.

pip install maps CodeShield -> codeshield (broken import names). This file applies
a small shim plus a macOS fix for Semgrep (--project-root / breaks temp files).

Run with the venv where codeshield is installed:
  source /path/to/.venv/bin/activate
  python3 test_codeshield.py
"""
from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path


def _register_codeshield_shim() -> None:
    import codeshield.insecure_code_detector as icd
    import codeshield.insecure_code_detector.issues as issues
    import codeshield.insecure_code_detector.languages as languages
    import codeshield.insecure_code_detector.usecases as usecases

    pkg = types.ModuleType("CodeShield")
    pkg.insecure_code_detector = icd
    sys.modules["CodeShield"] = pkg
    sys.modules["CodeShield.insecure_code_detector"] = icd
    sys.modules["CodeShield.insecure_code_detector.languages"] = languages
    sys.modules["CodeShield.insecure_code_detector.issues"] = issues
    sys.modules["CodeShield.insecure_code_detector.usecases"] = usecases


def _apply_macos_semgrep_fix() -> None:
    """Temp files under /var/... are absolute; --project-root / makes Semgrep return []."""
    import codeshield.insecure_code_detector.oss as oss

    oss.INCLUDE_SEMGREP_PROJECT_ROOT_PARAMETER = False


def _load_codeshield():
    root = Path(__file__).resolve().parent
    for candidate in (root / "vendor" / "PurpleLlama", root.parent / "PurpleLlama"):
        if (candidate / "CodeShield" / "codeshield.py").is_file():
            sys.path.insert(0, str(candidate))
            from CodeShield.codeshield import CodeShield  # noqa: PLC0415
            from CodeShield.insecure_code_detector.languages import Language  # noqa: PLC0415

            return CodeShield, Language

    _register_codeshield_shim()
    _apply_macos_semgrep_fix()
    from codeshield.cs import CodeShield  # noqa: PLC0415
    from codeshield.insecure_code_detector.languages import Language  # noqa: PLC0415

    return CodeShield, Language


async def main() -> None:
    try:
        CodeShield, Language = _load_codeshield()
    except ImportError as exc:
        print("Code Shield not available:", exc)
        print(f"Python in use: {sys.executable}")
        print()
        print("codeshield is NOT in this venv. Either:")
        print("  source /Users/kiru/Documents/CS/.venv/bin/activate   # if you installed there")
        print("  OR install here (needs Python 3.10+):")
        print("  pip install 'git+https://github.com/meta-llama/PurpleLlama.git#subdirectory=CodeShield'")
        sys.exit(1)

    # os.system("literal") is intentionally allowed by Meta's rules (not user-controlled).
    samples = [
        ("eval(input)", "should flag (code injection)"),
        ("eval('safe')", "usually OK — literal string excluded by rules"),
        ("import os\nos.system(user_cmd)", "should flag if non-literal"),
        ("x = 1", "benign"),
    ]
    print("Code Shield scan (Python only):\n")
    for code, note in samples:
        result = await CodeShield.scan_code(code, language=Language.PYTHON)
        n = len(result.issues_found or [])
        print(f"  {code[:36]!r}")
        print(f"    note: {note}")
        print(f"    insecure={result.is_insecure} treatment={result.recommended_treatment} issues={n}")
        if result.issues_found:
            for issue in result.issues_found[:2]:
                print(f"    - {issue.description} ({issue.cwe_id})")
        print()


if __name__ == "__main__":
    asyncio.run(main())
