"""Cerebras cloud client using the official cerebras.cloud.sdk."""

from __future__ import annotations

import json
import os
from typing import Any

from ollama_client import OllamaError  # reuse same error class


class CerebrasClient:
    def __init__(self, api_key: str, model: str, timeout: int = 120) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        try:
            from cerebras.cloud.sdk import Cerebras
            self._sdk = Cerebras(api_key=api_key)
        except ImportError as exc:
            raise OllamaError(
                "cerebras-cloud-sdk not installed. Run: pip install cerebras-cloud-sdk"
            ) from exc

    def health(self) -> dict[str, Any]:
        return {"status": "ok"}

    def ensure_model(self) -> None:
        pass  # Cerebras validates model at first call; skip pre-check

    def warmup(self) -> None:
        pass

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        num_predict: int | None = None,
    ) -> dict[str, Any]:
        normalized = _inject_tool_call_ids(messages)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": normalized,
            "stream": False,
            "temperature": 0.2,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if num_predict is not None:
            kwargs["max_completion_tokens"] = num_predict

        try:
            completion = self._sdk.chat.completions.create(**kwargs)
        except Exception as exc:
            raise OllamaError(f"Cerebras API error: {exc}") from exc

        msg = completion.choices[0].message

        # Normalize to Ollama-style dict {"message": {...}} that agent.py expects
        message: dict[str, Any] = {
            "role": msg.role,
            "content": msg.content or "",
        }
        if msg.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return {"message": message}


def _inject_tool_call_ids(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add tool_call_id to tool-result messages that are missing one (OpenAI requirement)."""
    out: list[dict[str, Any]] = []
    pending_ids: list[str] = []
    result_idx = 0

    for msg in messages:
        msg = dict(msg)

        if msg.get("role") == "assistant":
            tcs = msg.get("tool_calls") or []
            pending_ids = [tc.get("id", f"call_{i}") for i, tc in enumerate(tcs)]
            result_idx = 0

        if msg.get("role") == "tool" and "tool_call_id" not in msg:
            msg["tool_call_id"] = (
                pending_ids[result_idx]
                if result_idx < len(pending_ids)
                else f"call_auto_{result_idx}"
            )
            result_idx += 1

        out.append(msg)

    return out
