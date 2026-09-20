from __future__ import annotations

import inspect
from typing import Any, Callable, get_type_hints, get_origin

from jarvis.core.models import ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        self._tools[name] = fn

    def execute(self, name: str, **args) -> ToolResult:
        fn = self._tools.get(name)
        if fn is None:
            return ToolResult(False, f"Tool '{name}' is not available.")
        try:
            return fn(**args)
        except Exception as exc:
            return ToolResult(False, f"{name} failed: {exc}")

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for name, fn in sorted(self._tools.items()):
            signature = inspect.signature(fn)
            try:
                hints = get_type_hints(fn)
            except Exception:
                hints = {}
            properties: dict[str, Any] = {}
            required: list[str] = []
            for parameter in signature.parameters.values():
                if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
                    continue
                annotation = hints.get(parameter.name, parameter.annotation)
                origin = get_origin(annotation)
                if annotation is int:
                    kind = "integer"
                elif annotation is float:
                    kind = "number"
                elif annotation is bool:
                    kind = "boolean"
                elif origin is list or annotation is list:
                    kind = "array"
                else:
                    kind = "string"
                properties[parameter.name] = {"type": kind}
                if parameter.default is inspect.Parameter.empty:
                    required.append(parameter.name)
            specs.append({
                "name": name,
                "description": inspect.getdoc(fn) or f"JARVIS tool: {name}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            })
        return specs
