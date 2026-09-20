"""Optional local/offline response provider using an already-installed Ollama server."""
from __future__ import annotations

import json
import urllib.request
from jarvis.config import Settings


class OfflineProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def respond(self, text: str) -> str:
        prompt = (
            "You are JARVIS, a concise friendly Windows assistant. "
            "Reply naturally in Hindi, English, or Hinglish. Keep it to 1-3 sentences. "
            f"User: {text}"
        )
        if self.settings.offline_provider.lower() != "ollama":
            return self._local_fallback(text)
        try:
            body = json.dumps({
                "model": self.settings.offline_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 120},
            }).encode("utf-8")
            req = urllib.request.Request(
                self.settings.ollama_url.rstrip("/") + "/api/chat",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
            answer = payload.get("message", {}).get("content", "").strip()
            return answer or self._local_fallback(text)
        except Exception:
            return self._local_fallback(text)

    @staticmethod
    def _local_fallback(text: str) -> str:
        low = text.lower()
        if "hello" in low or "hi" in low or "namaste" in low or "नमस्ते" in low:
            return "Hello bhai 😄 Main ready hoon. Bolo kya karna hai?"
        if "kya haal" in low or "how are you" in low:
            return "Badhiya bhai 😄 Main ready hoon."
        if "who are you" in low or "tum kaun" in low:
            return "Main JARVIS hoon — tumhara Windows personal assistant."
        return "Main abhi offline mode mein hoon. Local PC tasks main phir bhi handle kar sakta hoon."
