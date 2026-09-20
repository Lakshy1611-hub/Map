from __future__ import annotations
from typing import Callable
from jarvis.core.models import ToolResult
class ToolRegistry:
    def __init__(self): self._tools: dict[str, Callable] = {}
    def register(self, name: str, fn: Callable): self._tools[name]=fn
    def execute(self,name: str, **args) -> ToolResult:
        if name not in self._tools: return ToolResult(False, f"Tool '{name}' is not available.")
        try: return self._tools[name](**args)
        except Exception as exc: return ToolResult(False, f"{name} failed: {exc}")
    def names(self): return sorted(self._tools)
