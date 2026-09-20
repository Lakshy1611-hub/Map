from __future__ import annotations
from jarvis.core.models import ToolResult
def _pg():
    import pyautogui; pyautogui.FAILSAFE=True; return pyautogui
def keyboard_type(text: str) -> ToolResult: _pg().write(text, interval=0.015); return ToolResult(True,"Typed text into the focused application.")
def keyboard_press(key: str) -> ToolResult: _pg().press(key); return ToolResult(True,f"Pressed {key}.")
def keyboard_hotkey(*keys: str) -> ToolResult: _pg().hotkey(*keys); return ToolResult(True,"Pressed keyboard shortcut.")
def mouse_move(x:int,y:int) -> ToolResult: _pg().moveTo(x,y,duration=.2); return ToolResult(True,f"Moved mouse to {x}, {y}.")
def mouse_click(x:int|None=None,y:int|None=None) -> ToolResult: _pg().click(x,y); return ToolResult(True,"Clicked mouse.")
def mouse_double_click(x:int|None=None,y:int|None=None) -> ToolResult: _pg().doubleClick(x,y); return ToolResult(True,"Double-clicked mouse.")
def mouse_right_click(x:int|None=None,y:int|None=None) -> ToolResult: _pg().rightClick(x,y); return ToolResult(True,"Right-clicked mouse.")
def mouse_scroll(clicks:int) -> ToolResult: _pg().scroll(clicks); return ToolResult(True,"Scrolled mouse.")
