from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
class AssistantState(str, Enum): IDLE="idle"; LISTENING="listening"; THINKING="thinking"; EXECUTING="executing"; SPEAKING="speaking"; PAUSED="paused"
@dataclass
class ToolResult:
    ok: bool; message: str; data: dict[str, Any] = field(default_factory=dict)
@dataclass
class ChatReply:
    text: str; state: AssistantState = AssistantState.IDLE; tool_results: list[ToolResult] = field(default_factory=list)
