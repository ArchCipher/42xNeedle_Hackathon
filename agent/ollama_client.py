"""Ollama HTTP client — free local models only (no paid APIs)."""

from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from typing import Any

TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
    re.DOTALL,
)


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._get("/api/tags")

    def ensure_model(self) -> None:
        tags = self.health()
        names = {m.get("name", "") for m in tags.get("models", [])}
        bases = {n.split(":")[0] for n in names}
        if self.model not in names and self.model.split(":")[0] not in bases:
            raise OllamaError(
                f"Model '{self.model}' not found locally. Run: ollama pull {self.model}"
            )

    def warmup(self) -> None:
        """Load the model with a tiny request so the first real call is faster."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Reply with OK"}],
            "stream": False,
            "options": {"num_predict": 8, "temperature": 0},
        }
        self._post("/api/chat", payload)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        num_predict: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if num_predict is not None:
            payload["options"] = {"num_predict": num_predict, "temperature": 0.2}
        if tools:
            payload["tools"] = tools
        return self._post("/api/chat", payload)

    def _get(self, path: str) -> dict[str, Any]:
        req = urllib.request.Request(f"{self.base_url}{path}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise OllamaError(
                f"Cannot reach Ollama at {self.base_url}. Install and run: ollama serve"
            ) from exc

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except socket.timeout as exc:
            raise OllamaError(
                f"Ollama timed out after {self.timeout}s. "
                "First run on CPU can take many minutes — try: "
                f"ollama run {self.model} (warm up), increase request_timeout_seconds in "
                "agent/config.yaml, or use agent/agent.py run --skip-setup."
            ) from exc
        except TimeoutError as exc:
            raise OllamaError(
                f"Ollama timed out after {self.timeout}s. Warm up the model or raise "
                "request_timeout_seconds in agent/config.yaml."
            ) from exc
        except urllib.error.URLError as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc


def _tool_input_from_payload(data: dict[str, Any]) -> dict[str, Any]:
    if "input" in data and isinstance(data["input"], dict):
        return data["input"]
    if "arguments" in data and isinstance(data["arguments"], dict):
        return data["arguments"]
    return {}


def _append_tool_call(tool_calls: list[dict[str, Any]], name: str, inputs: dict[str, Any]) -> None:
    if name:
        tool_calls.append({"name": name, "input": inputs})


def parse_assistant_response(message: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    content = (message.get("content") or "").strip()
    tool_calls: list[dict[str, Any]] = []

    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args) if args else {}
            _append_tool_call(tool_calls, fn.get("name", ""), args if isinstance(args, dict) else {})
        return content, tool_calls

    for match in TOOL_CALL_RE.finditer(content):
        try:
            data = json.loads(match.group(1))
            _append_tool_call(tool_calls, data["name"], _tool_input_from_payload(data))
        except (json.JSONDecodeError, KeyError):
            continue

    if not tool_calls and content.startswith("{"):
        try:
            data = json.loads(content)
            if isinstance(data, dict) and data.get("name"):
                _append_tool_call(tool_calls, data["name"], _tool_input_from_payload(data))
                content = ""
        except json.JSONDecodeError:
            pass

    if tool_calls and content:
        content = TOOL_CALL_RE.sub("", content).strip()
    return content, tool_calls
