from __future__ import annotations

import re
from typing import Callable

from jarvis.config import Settings
from jarvis.core.conversation import Conversation
from jarvis.core.models import AssistantState, ChatReply, ToolResult
from jarvis.llm.provider import LLMProvider
from jarvis.offline import OfflineProvider
from jarvis.security.permissions import needs_confirmation
from jarvis.tools import applications, automation, browser, files, screen, system, terminal, windows
from jarvis.tools.registry import ToolRegistry


class Assistant:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.state = AssistantState.IDLE
        self.conversation = Conversation()
        self.registry = ToolRegistry()
        self.pending: tuple[str, dict] | None = None
        self._register()
        self.llm = LLMProvider(self.settings)
        self.offline = OfflineProvider(self.settings)

    def _register(self) -> None:
        for module in (applications, automation, screen, browser, files, terminal, system, windows):
            for name, fn in vars(module).items():
                if callable(fn) and not name.startswith("_") and name not in {"ToolResult"}:
                    self.registry.register(name, fn)

    def _fallback(self, text: str) -> dict:
        low = text.lower().strip()

        if low in {"ruk", "ruk ja", "stop", "pause", "bas"}:
            return {"reply": "Theek hai bhai, ruk gaya.", "tool": None, "arguments": {}}

        if any(p in low for p in ("screen pe kya", "screen par kya", "screen dikha", "screen analyze", "analyze screen")):
            return {"reply": "", "tool": "inspect_screen", "arguments": {"question": text}}

        if any(p in low for p in ("screenshot", "screen shot", "screen capture")):
            return {"reply": "", "tool": "take_screenshot", "arguments": {}}

        match = re.search(
            r"(?:open|launch|start|kholo|khol do|khol|chalao|चलाओ|खोलो)\s+(?:the\s+)?(.+)$",
            text,
            re.I,
        )
        if match and match.group(1).strip():
            target = match.group(1).strip().rstrip(".")
            if target.lower().startswith(("http://", "https://", "www.")):
                return {"reply": "", "tool": "open_url", "arguments": {"url": target}}
            if target.lower().startswith(("youtube", "google", "github")) and "." not in target:
                url = {
                    "youtube": "https://youtube.com",
                    "google": "https://google.com",
                    "github": "https://github.com",
                }.get(target.lower())
                if url:
                    return {"reply": "", "tool": "open_url", "arguments": {"url": url}}
            return {"reply": "", "tool": "open_application", "arguments": {"application": target}}

        match = re.search(r"(?:close|band karo|band kar do|बंद करो)\s+(.+)$", text, re.I)
        if match:
            return {"reply": "", "tool": "close_application", "arguments": {"application": match.group(1).strip()}}

        match = re.search(r"(?:type|likho|likh do|टाइप करो)\s+(.+)", text, re.I)
        if match:
            return {"reply": "", "tool": "keyboard_type", "arguments": {"text": match.group(1).strip()}}

        match = re.search(r"(?:press|dabao|दबाओ)\s+(.+)$", text, re.I)
        if match:
            return {"reply": "", "tool": "keyboard_press", "arguments": {"key": match.group(1).strip()}}

        if re.search(r"(?:alt\+tab|switch window|window badlo|window change)", low):
            return {"reply": "", "tool": "keyboard_hotkey", "arguments": {"keys": ["alt", "tab"]}}

        if "youtube" in low and self.conversation.current_application in {"chrome", "google chrome"}:
            return {"reply": "", "tool": "open_url", "arguments": {"url": "https://youtube.com"}}

        if low.startswith(("search ", "google ")):
            query = re.sub(r"^(search|google)\s+", "", text, flags=re.I).strip()
            return {"reply": "", "tool": "search_web", "arguments": {"query": query}}

        if any(p in low for p in ("kya kya kar", "what can you do")):
            return {
                "reply": (
                    "Main chat, apps, browser, keyboard, mouse, screenshots, screen analysis, files, "
                    "PowerShell aur system tasks handle kar sakta hoon. Complex kaam ko steps mein plan bhi kar sakta hoon."
                ),
                "tool": None,
                "arguments": {},
            }

        if "kya haal" in low or "how are you" in low:
            return {"reply": "Badhiya bhai 😄 bata kya karna hai?", "tool": None, "arguments": {}}

        if "time" in low or "samay" in low:
            from datetime import datetime
            return {"reply": datetime.now().strftime("Abhi %I:%M %p hai."), "tool": None, "arguments": {}}

        return {"reply": "", "tool": None, "arguments": {}}

    def _looks_like_action(self, text: str) -> bool:
        low = text.lower()
        action_words = (
            "open", "launch", "start", "kholo", "khol", "chalao", "close", "band",
            "type", "likho", "press", "dabao", "click", "screenshot", "screen",
            "search", "download", "move", "copy", "delete", "rename", "create",
            "run", "execute", "shutdown", "restart", "settings",
        )
        return any(word in low for word in action_words)

    def _offline_reply(self, text: str) -> str:
        answer = self.offline.respond(text)
        return answer or "Net nahi hai, lekin local PC controls available hain. Jo local kaam karna hai bolo."

    def handle(
        self,
        text: str,
        confirmed: bool = False,
        on_delta: Callable[[str], None] | None = None,
    ) -> ChatReply:
        self.state = AssistantState.THINKING
        self.conversation.add("user", text)

        if self.pending and confirmed:
            tool, args = self.pending
            self.pending = None
            plan = {"reply": "", "tool": tool, "arguments": args}
        else:
            plan = self._fallback(text)
            if not plan["tool"] and not plan["reply"]:
                try:
                    if self._looks_like_action(text):
                        plan = self.llm.plan_tool(self.conversation.history(), self.registry.specs()) or plan
                    else:
                        streamed = self.llm.chat(self.conversation.history(), on_delta=on_delta)
                        if streamed:
                            plan["reply"] = streamed
                        else:
                            plan["reply"] = self._offline_reply(text)
                except Exception:
                    plan["reply"] = self._offline_reply(text)

        tool, args = plan.get("tool"), plan.get("arguments") or {}

        if tool and needs_confirmation(tool, args) and not confirmed:
            self.pending = (tool, args)
            reply = ChatReply("Ye action important hai. Pehle confirm karo, phir main continue karunga.")
            self.conversation.add("assistant", reply.text)
            self.state = AssistantState.IDLE
            return reply

        results: list[ToolResult] = []
        if tool:
            self.state = AssistantState.EXECUTING
            result = self.registry.execute(tool, **args)
            results = [result]
            if result.ok and tool == "open_application":
                self.conversation.current_application = str(args.get("application", ""))
            if result.ok:
                reply = plan.get("reply") or result.message
            else:
                reply = result.message
        else:
            reply = plan.get("reply", "")

        self.conversation.add("assistant", reply)
        self.state = AssistantState.SPEAKING
        self.state = AssistantState.IDLE
        return ChatReply(reply, AssistantState.IDLE, results)
