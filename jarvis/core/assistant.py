from __future__ import annotations

import re
from datetime import datetime
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

        visual = re.search(r"(?:click|press|dabao|दबाओ).{0,20}(?:button|btn|icon)|(.{0,30})(?:button|btn) pe click", text, re.I)
        if visual:
            target = text.strip()
            return {"reply": "", "tool": "visual_click", "arguments": {"target": target}}

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
            if target.lower() in {"youtube", "google", "github"}:
                url = {"youtube": "https://youtube.com", "google": "https://google.com", "github": "https://github.com"}[target.lower()]
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

        if "refresh" in low or "page reload" in low:
            return {"reply": "", "tool": "keyboard_press", "arguments": {"key": "f5"}}

        if "go back" in low or "peeche ja" in low or "back ja" in low:
            return {"reply": "", "tool": "keyboard_hotkey", "arguments": {"keys": ["alt", "left"]}}

        if "scroll down" in low or "neeche scroll" in low:
            return {"reply": "", "tool": "mouse_scroll", "arguments": {"clicks": -6}}

        if "scroll up" in low or "upar scroll" in low:
            return {"reply": "", "tool": "mouse_scroll", "arguments": {"clicks": 6}}

        if "youtube" in low and self.conversation.current_application in {"chrome", "google chrome"}:
            return {"reply": "", "tool": "open_url", "arguments": {"url": "https://youtube.com"}}

        if low.startswith(("search ", "google ")):
            query = re.sub(r"^(search|google)\s+", "", text, flags=re.I).strip()
            return {"reply": "", "tool": "search_web", "arguments": {"query": query}}

        if "kya kya kar" in low or "what can you do" in low:
            return {
                "reply": "Main chat, apps, browser, keyboard, mouse, screenshots, screen analysis, files, PowerShell aur multi-step desktop tasks handle kar sakta hoon.",
                "tool": None,
                "arguments": {},
            }

        if "kya haal" in low or "how are you" in low:
            return {"reply": "Badhiya bhai 😄 bata kya karna hai?", "tool": None, "arguments": {}}

        if "time" in low or "samay" in low:
            return {"reply": f"Abhi {datetime.now():%I:%M %p} hai.", "tool": None, "arguments": {}}

        return {"reply": "", "tool": None, "arguments": {}}

    def _looks_like_action(self, text: str) -> bool:
        low = text.lower()
        action_words = (
            "open", "launch", "start", "kholo", "khol", "chalao", "close", "band",
            "type", "likho", "press", "dabao", "click", "screenshot", "screen",
            "search", "download", "move", "copy", "delete", "rename", "create",
            "run", "execute", "shutdown", "restart", "settings", "scroll", "refresh",
        )
        return any(word in low for word in action_words)

    def _is_multi_step(self, text: str) -> bool:
        low = text.lower()
        return any(token in low for token in (" and ", " then ", " after ", " phir ", " fir ", " uske baad ", " karke "))

    def _offline_reply(self, text: str) -> str:
        return self.offline.respond(text) or "Net nahi hai, lekin local PC controls available hain. Jo local kaam karna hai bolo."

    def _execute_tool(self, tool: str, args: dict) -> ToolResult:
        self.state = AssistantState.EXECUTING
        return self.registry.execute(tool, **args)

    def handle(self, text: str, confirmed: bool = False, on_delta: Callable[[str], None] | None = None) -> ChatReply:
        self.state = AssistantState.THINKING
        self.conversation.add("user", text)

        if self.pending and confirmed:
            tool, args = self.pending
            self.pending = None
            result = self._execute_tool(tool, args)
            reply = result.message
            self.conversation.add("assistant", reply)
            self.state = AssistantState.IDLE
            return ChatReply(reply, AssistantState.IDLE, [result])

        plan = self._fallback(text)
        if not plan["tool"] and not plan["reply"]:
            try:
                if self._looks_like_action(text):
                    plan = self.llm.plan_tool(self.conversation.history(), self.registry.specs()) or plan
                else:
                    response = self.llm.chat(self.conversation.history(), on_delta=on_delta)
                    plan["reply"] = response or self._offline_reply(text)
            except Exception:
                plan["reply"] = self._offline_reply(text)

        executed: list[ToolResult] = []
        seen_tools: set[str] = set()
        for step in range(self.settings.max_agent_steps):
            tool, args = plan.get("tool"), plan.get("arguments") or {}
            if not tool:
                break
            if tool in seen_tools and not self._is_multi_step(text):
                break
            if needs_confirmation(tool, args) and not confirmed:
                self.pending = (tool, args)
                reply = ChatReply("Ye action important hai. Pehle confirm karo, phir main continue karunga.")
                self.conversation.add("assistant", reply.text)
                self.state = AssistantState.IDLE
                return reply

            seen_tools.add(tool)
            result = self._execute_tool(tool, args)
            executed.append(result)
            if tool == "open_application" and result.ok:
                self.conversation.current_application = str(args.get("application", ""))
            if not result.ok:
                plan = {"reply": result.message, "tool": None, "arguments": {}}
                break

            if not self._is_multi_step(text):
                plan = {"reply": result.message, "tool": None, "arguments": {}}
                break

            self.conversation.add("user", f"Tool result for {tool}: {result.message}")
            try:
                plan = self.llm.plan_tool(self.conversation.history(), self.registry.specs()) or {
                    "reply": result.message,
                    "tool": None,
                    "arguments": {},
                }
            except Exception:
                plan = {"reply": result.message, "tool": None, "arguments": {}}

        reply_text = str(plan.get("reply") or (executed[-1].message if executed else "Done."))
        self.conversation.add("assistant", reply_text)
        self.state = AssistantState.IDLE
        return ChatReply(reply_text, AssistantState.IDLE, executed)
