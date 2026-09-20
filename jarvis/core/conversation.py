from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class Conversation:
    messages: list[dict[str,str]] = field(default_factory=list)
    current_application: str | None = None
    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        del self.messages[:-16]
    def history(self) -> list[dict[str,str]]: return self.messages.copy()
