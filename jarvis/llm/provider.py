"""OpenAI-compatible LLM provider used by JARVIS.

Gemini's OpenAI-compatible endpoint is selected entirely through OPENAI_BASE_URL.
"""
from __future__ import annotations

import json
from typing import Any

from jarvis.config import Settings


class LLMProvider:
    """Provider boundary: replace this class without changing assistant orchestration."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        """JARVIS uses its own key name; OPENAI_API_KEY is never consulted."""
        return bool(self.settings.api_key.strip())

    def create_client(self):
        """Create an OpenAI-compatible client for OpenAI or the configured Gemini URL."""
        from openai import OpenAI

        return OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url)

    def respond(self, messages: list[dict[str, str]], tool_names: list[str]) -> dict[str, Any] | None:
        if not self.is_configured:
            return None

        client = self.create_client()
        prompt = (
            "You are JARVIS, a concise friendly English/Hindi/Hinglish Windows assistant. "
            'For computer actions answer ONLY JSON: {"reply": str, "tool": tool_name, "arguments": object}. '
            f"Available explicit tools: {', '.join(tool_names)}. Never invent tools or execute shell directly. "
            "For normal conversation answer JSON with tool null. Use a tool only where it is needed."
        )
        result = client.chat.completions.create(
            model=self.settings.model,
            messages=[{"role": "system", "content": prompt}, *messages],
            response_format={"type": "json_object"},
        )
        content = result.choices[0].message.content
        if not content:
            raise RuntimeError("The configured AI provider returned an empty response.")
        return json.loads(content)
