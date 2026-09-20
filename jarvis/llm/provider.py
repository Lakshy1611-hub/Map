from __future__ import annotations
import json
from jarvis.config import Settings
class LLMProvider:
    """Provider boundary: replace this class without changing assistant orchestration."""
    def __init__(self, settings: Settings): self.settings=settings
    def respond(self, messages, tool_names):
        if not self.settings.api_key: return None
        from openai import OpenAI
        client=OpenAI(api_key=self.settings.api_key)
        prompt=("You are JARVIS, a concise friendly English/Hindi/Hinglish Windows assistant. "
        "For computer actions answer ONLY JSON: {\"reply\": str, \"tool\": tool_name, \"arguments\": object}. "
        f"Available explicit tools: {', '.join(tool_names)}. Never invent tools or execute shell directly. "
        "For normal conversation answer JSON with tool null. Use a tool only where it is needed.")
        result=client.chat.completions.create(model=self.settings.model,messages=[{"role":"system","content":prompt},*messages],response_format={"type":"json_object"})
        return json.loads(result.choices[0].message.content)
