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

        return OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            timeout=self.settings.response_timeout,
        )

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are JARVIS, a fast, friendly personal Windows assistant. "
            "Speak naturally in the user's language: Hindi, English, or Hinglish. "
            "Keep ordinary replies concise (usually 1-3 sentences). "
            "Never pretend an action happened if a tool result did not confirm it. "
            "For actions use only the registered tools supplied by the application."
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        if not self.is_configured:
            return ""

        client = self.create_client()
        stream = client.chat.completions.create(
            model=self.settings.model,
            messages=[{"role": "system", "content": self._system_prompt()}, *messages],
            stream=True,
        )
        parts: list[str] = []
        for chunk in stream:
            delta = getattr(chunk.choices[0], "delta", None) if chunk.choices else None
            text = getattr(delta, "content", None) if delta else None
            if text:
                parts.append(text)
                if on_delta:
                    on_delta(text)
        return "".join(parts).strip()

    def plan_tool(
        self,
        messages: list[dict[str, str]],
        tool_specs: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not self.is_configured:
            return None

        client = self.create_client()
        result = client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        self._system_prompt()
                        + " Return exactly one JSON object with keys "
                        "reply, tool, and arguments. tool must be null or one of "
                        "the registered tools. Use the smallest number of actions needed."
                    ),
                },
                *messages,
            ],
            response_format={"type": "json_object"},
        )
        content = result.choices[0].message.content
        if not content:
            return None
        data = json.loads(content)
        if data.get("tool") is not None and not isinstance(data.get("arguments"), dict):
            data["arguments"] = {}
        return data
