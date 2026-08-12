"""Meta Code Shield gate for agent write_file (optional dependency)."""

from __future__ import annotations

import asyncio
import sys
import types
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SECURITY_LOG = ROOT / "agent_logs" / "security.log"

_ready = False
_CodeShield: Any = None
_Language: Any = None


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _append_security_log(block: str) -> None:
    SECURITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SECURITY_LOG.open("a", encoding="utf-8") as f:
        f.write(block)
        if not block.endswith("\n"):
            f.write("\n")


def _register_shim() -> None:
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
    import codeshield.insecure_code_detector.oss as oss

    oss.INCLUDE_SEMGREP_PROJECT_ROOT_PARAMETER = False


def _ensure_loaded() -> tuple[Any, Any]:
    global _ready, _CodeShield, _Language
    if _ready:
        return _CodeShield, _Language

    for candidate in (ROOT / "vendor" / "PurpleLlama", ROOT.parent / "PurpleLlama"):
        if (candidate / "CodeShield" / "codeshield.py").is_file():
            sys.path.insert(0, str(candidate))
            from CodeShield.codeshield import CodeShield  # noqa: PLC0415
            from CodeShield.insecure_code_detector.languages import Language  # noqa: PLC0415

            _CodeShield, _Language = CodeShield, Language
            _ready = True
            return _CodeShield, _Language

    _register_shim()
    _apply_macos_semgrep_fix()
    from codeshield.cs import CodeShield  # noqa: PLC0415
    from codeshield.insecure_code_detector.languages import Language  # noqa: PLC0415

    _CodeShield, _Language = CodeShield, Language
    _ready = True
    return _CodeShield, _Language


def codeshield_available() -> bool:
    try:
        _ensure_loaded()
        return True
    except ImportError:
        return False


def _format_issues(issues: list[Any], limit: int = 5) -> str:
    lines: list[str] = []
    for issue in issues[:limit]:
        desc = getattr(issue, "description", None) or str(issue)
        cwe = getattr(issue, "cwe_id", "") or ""
        lines.append(f"  - {desc}" + (f" ({cwe})" if cwe else ""))
    extra = len(issues) - limit
    if extra > 0:
        lines.append(f"  - ... and {extra} more")
    return "\n".join(lines)


def scan_python_before_write(rel_path: str, content: str) -> tuple[bool, str]:
    """
    Run Code Shield on Python source. Returns (allow_write, agent_message_suffix).
    If allow_write is False, do not write the file; message explains why.
    """
    try:
        CodeShield, Language = _ensure_loaded()
    except ImportError:
        return True, ""

    try:
        result = asyncio.run(CodeShield.scan_code(content, language=Language.PYTHON))
    except Exception as exc:
        _append_security_log(
            f"\n[{_ts()}] SCAN_ERROR\n"
            f"Path: {rel_path}\n"
            f"Error: {exc}\n"
        )
        return True, ""

    issues = result.issues_found or []
    treatment = getattr(result.recommended_treatment, "value", str(result.recommended_treatment))
    block = (
        f"\n[{_ts()}] CODE_SHIELD\n"
        f"Path: {rel_path}\n"
        f"Insecure: {result.is_insecure}\n"
        f"Treatment: {treatment}\n"
        f"Issues: {len(issues)}\n"
    )
    if issues:
        block += _format_issues(issues) + "\n"
    _append_security_log(block)

    if not result.is_insecure:
        return True, " | codeshield: OK"

    msg = (
        "error: CODE_SHIELD blocked write — insecure Python detected\n"
        f"treatment: {treatment}\n"
        f"{_format_issues(issues)}\n"
        "Fix the security issues and call write_file again. File was not saved."
    )
    return False, msg
