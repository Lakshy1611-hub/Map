from __future__ import annotations

from jarvis.core.models import ToolResult


def _pg():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui


def keyboard_type(text: str) -> ToolResult:
    """Type Unicode text into the focused application."""
    try:
        import pyperclip
        pg = _pg()
        pyperclip.copy(text)
        pg.hotkey("ctrl", "v")
        return ToolResult(True, "Typed the text into the focused application.")
    except Exception as exc:
        return ToolResult(False, f"Typing failed: {exc}")


def keyboard_press(key: str) -> ToolResult:
    """Press one keyboard key."""
    try:
        _pg().press(key.strip().lower())
        return ToolResult(True, f"Pressed {key}.")
    except Exception as exc:
        return ToolResult(False, f"Key press failed: {exc}")


def keyboard_hotkey(keys: list[str]) -> ToolResult:
    """Press a keyboard shortcut such as ['ctrl', 'l']."""
    try:
        _pg().hotkey(*[key.strip().lower() for key in keys])
        return ToolResult(True, "Pressed the keyboard shortcut.")
    except Exception as exc:
        return ToolResult(False, f"Keyboard shortcut failed: {exc}")


def mouse_move(x: int, y: int) -> ToolResult:
    """Move the mouse pointer to a screen coordinate."""
    try:
        _pg().moveTo(x, y, duration=0.15)
        return ToolResult(True, f"Moved the mouse to {x}, {y}.")
    except Exception as exc:
        return ToolResult(False, f"Mouse move failed: {exc}")


def mouse_click(x: int | None = None, y: int | None = None) -> ToolResult:
    """Click the mouse at the given coordinates or the current pointer."""
    try:
        _pg().click(x, y)
        return ToolResult(True, "Clicked the mouse.")
    except Exception as exc:
        return ToolResult(False, f"Mouse click failed: {exc}")


def mouse_double_click(x: int | None = None, y: int | None = None) -> ToolResult:
    """Double-click at coordinates or the current pointer."""
    try:
        _pg().doubleClick(x, y)
        return ToolResult(True, "Double-clicked the mouse.")
    except Exception as exc:
        return ToolResult(False, f"Double-click failed: {exc}")


def mouse_right_click(x: int | None = None, y: int | None = None) -> ToolResult:
    """Right-click at coordinates or the current pointer."""
    try:
        _pg().rightClick(x, y)
        return ToolResult(True, "Right-clicked the mouse.")
    except Exception as exc:
        return ToolResult(False, f"Right-click failed: {exc}")


def mouse_scroll(clicks: int) -> ToolResult:
    """Scroll vertically; positive is up, negative is down."""
    try:
        _pg().scroll(clicks)
        return ToolResult(True, "Scrolled the mouse.")
    except Exception as exc:
        return ToolResult(False, f"Mouse scroll failed: {exc}")
