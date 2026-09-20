from __future__ import annotations
from datetime import datetime
from pathlib import Path
from jarvis.core.models import ToolResult
def take_screenshot(directory: str="screenshots") -> ToolResult:
    import pyautogui
    target=Path(directory); target.mkdir(parents=True,exist_ok=True); path=target/f"jarvis-{datetime.now():%Y%m%d-%H%M%S}.png"
    pyautogui.screenshot(str(path)); return ToolResult(True,f"Screenshot saved to {path}.",{"path":str(path)})
def inspect_screen() -> ToolResult:
    r=take_screenshot(); return ToolResult(r.ok, "I captured the screen. Configure a vision-capable LLM to analyze it.",r.data)
