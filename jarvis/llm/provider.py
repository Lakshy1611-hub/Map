"""Fast Gemini/OpenAI-compatible text and tool-planning provider."""
from __future__ import annotations

import json
from typing import Any, Callable

from jarvis.config import Settings


class LLMProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.api_key)

    def create_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url, timeout=self.settings.response_timeout)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are JARVIS, a fast, friendly personal Windows assistant. "
            "Speak naturally in the user's language: Hindi, English, or Hinglish. "
            "Keep ordinary replies concise. Never claim an action happened unless its tool result confirms it. "
            "You may use only the explicit tools provided by the application."
        )

    def chat(self, messages: list[dict[str, str]], on_delta: Callable[[str], None] | None = None) -> str:
        if not self.is_configured:
            return ""
        client = self.create_client()
        stream = client.chat.completions.create(
            model=self.settings.model,
            messages=[{"role": "system", "content": self._system_prompt()}, *messages],
            stream=True,
            reasoning_effort=self.settings.thinking_level,
        )
        parts: list[str] = []
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = getattr(chunk.choices[0], "delta", None)
            text = getattr(delta, "content", None) if delta else None
            if text:
                parts.append(text)
                if on_delta:
                    on_delta(text)
        return "".join(parts).strip()

    def plan_tool(self, messages: list[dict[str, str]], tool_specs: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not self.is_configured:
            return None
        client = self.create_client()
        specs = json.dumps(tool_specs, ensure_ascii=False, separators=(",", ":"))
        system = (
            self._system_prompt()
            + " For an action, return ONLY valid JSON with keys reply, tool, arguments. "
            + "tool must be null or exactly match one of these registered tools. "
            + "arguments must match the tool parameter names. Tool catalog: "
            + specs
        )
        result = client.chat.completions.create(
            model=self.settings.model,
            messages=[{"role": "system", "content": system}, *messages],
            response_format={"type": "json_object"},
            reasoning_effort=self.settings.thinking_level,
        )
        content = result.choices[0].message.content
        if not content:
            return None
        data = json.loads(content)
        return {"reply": str(data.get("reply", "")), "tool": data.get("tool"), "arguments": data.get("arguments") or {}}