"""Structured logging for hackathon agent_logs/ (see templates in agent_logs/)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "agent_logs"


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


@dataclass
class AgentLogger:
    log_dir: Path = field(default_factory=lambda: LOG_DIR)

    def __post_init__(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _append(self, filename: str, block: str) -> None:
        path = self.log_dir / filename
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
            if not block.endswith("\n"):
                f.write("\n")

    def user_prompt(
        self,
        prompt: str,
        *,
        context: str = "",
        expected_action: str = "",
    ) -> None:
        block = (
            f"\n[{_ts()}] USER_PROMPT\n"
            f"Prompt: {prompt}\n"
            f"Context: {context}\n"
            f"Expected agent action: {expected_action}\n"
        )
        self._append("prompts.log", block)

    def decision(
        self,
        decision: str,
        *,
        reason: str = "",
        evidence: str = "",
        next_action: str = "",
    ) -> None:
        block = (
            f"\n[{_ts()}] DECISION\n"
            f"Decision: {decision}\n"
            f"Reason: {reason}\n"
            f"Evidence/input used: {evidence}\n"
            f"Next action: {next_action}\n"
        )
        self._append("decisions.log", block)

    def command(
        self,
        command: str,
        *,
        exit_code: int | None = None,
        output: str = "",
        run_by: str = "agent",
    ) -> None:
        exit_str = "n/a" if exit_code is None else str(exit_code)
        block = (
            f"\n[{_ts()}] COMMAND\n"
            f"Run by: {run_by}\n"
            f"Command: {command}\n"
            f"Exit code: {exit_str}\n"
            f"Output summary: {output[:2000]}\n"
        )
        self._append("commands.log", block)

    def test_run(
        self,
        command: str,
        *,
        score: str = "",
        exit_code: int | None = None,
        failures: str = "",
        notes: str = "",
    ) -> None:
        exit_str = "n/a" if exit_code is None else str(exit_code)
        block = (
            f"\n[{_ts()}] TEST_RUN\n"
            f"Command: {command}\n"
            f"Score: {score}\n"
            f"Exit code: {exit_str}\n"
            f"Failure categories: {failures}\n"
            f"Notes: {notes}\n"
        )
        self._append("test_runs.log", block)

    def error(
        self,
        summary: str,
        *,
        details: str = "",
        recovery: str = "",
    ) -> None:
        block = (
            f"\n[{_ts()}] ERROR\n"
            f"Summary: {summary}\n"
            f"Details: {details}\n"
            f"Recovery attempt: {recovery}\n"
        )
        self._append("errors.log", block)

    def human_intervention(
        self,
        intervention_type: str,
        *,
        what: str,
        why: str = "",
        files_affected: str = "",
        touched_final_code: bool = False,
        notes: str = "",
    ) -> None:
        block = (
            f"\n[{_ts()}] {intervention_type}\n"
            f"What happened: {what}\n"
            f"Why: {why}\n"
            f"Files or settings affected: {files_affected}\n"
            f"Touched final task code directly: {'yes' if touched_final_code else 'no'}\n"
            f"Notes: {notes}\n"
        )
        self._append("human_interventions.log", block)
