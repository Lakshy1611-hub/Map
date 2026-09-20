from __future__ import annotations

import platform
import subprocess
from jarvis.core.models import ToolResult


def _windows_only() -> bool:
    return platform.system() == "Windows"


def get_active_window() -> ToolResult:
    if not _windows_only():
        return ToolResult(False, "Active-window information is currently Windows-only.")
    try:
        import ctypes
        import ctypes.wintypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        return ToolResult(True, title or "No active window title found.", {"title": title})
    except Exception as exc:
        return ToolResult(False, f"Could not read the active window: {exc}")


def minimize_window() -> ToolResult:
    if not _windows_only():
        return ToolResult(False, "Window control is currently Windows-only.")
    try:
        import pyautogui
        pyautogui.hotkey("alt", "space")
        pyautogui.press("n")
        return ToolResult(True, "Minimized the active window.")
    except Exception as exc:
        return ToolResult(False, f"Could not minimize the active window: {exc}")


def maximize_window() -> ToolResult:
    if not _windows_only():
        return ToolResult(False, "Window control is currently Windows-only.")
    try:
        import pyautogui
        pyautogui.hotkey("alt", "space")
        pyautogui.press("x")
        return ToolResult(True, "Maximized the active window.")
    except Exception as exc:
        return ToolResult(False, f"Could not maximize the active window: {exc}")


def show_desktop() -> ToolResult:
    if not _windows_only():
        return ToolResult(False, "Show desktop is currently Windows-only.")
    try:
        import pyautogui
        pyautogui.hotkey("win", "d")
        return ToolResult(True, "Showing the desktop.")
    except Exception as exc:
        return ToolResult(False, f"Could not show the desktop: {exc}")


def open_system_settings() -> ToolResult:
    if not _windows_only():
        return ToolResult(False, "Windows Settings is available only on Windows.")
    try:
        subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:"], creationflags=subprocess.CREATE_NO_WINDOW)
        return ToolResult(True, "Opened Windows Settings.")
    except Exception as exc:
        return ToolResult(False, f"Could not open Windows Settings: {exc}")
