from __future__ import annotations

import os
import platform
import re
import subprocess
from jarvis.core.models import ToolResult

ALIASES = {"chrome": "chrome", "google chrome": "chrome", "edge": "msedge", "microsoft edge": "msedge", "notepad": "notepad", "calculator": "calc", "calc": "calc", "settings": "ms-settings:", "file explorer": "explorer", "explorer": "explorer", "powershell": "powershell", "terminal": "wt", "windows terminal": "wt", "vs code": "code", "vscode": "code", "visual studio code": "code"}
WINDOWS_COMMANDS = {"chrome": ["cmd", "/c", "start", "", "chrome"], "msedge": ["cmd", "/c", "start", "", "msedge"], "notepad": ["notepad.exe"], "calc": ["calc.exe"], "explorer": ["explorer.exe"], "code": ["code.cmd"], "powershell": ["powershell.exe", "-NoProfile"], "wt": ["wt.exe"]}

def _safe_target(value: str) -> bool:
    return bool(value) and len(value) <= 180 and not re.search(r"[&|<>`;$]", value)

def open_application(application: str) -> ToolResult:
    """Open a Windows app by friendly name or registered application name."""
    target = application.strip()
    if not _safe_target(target):
        return ToolResult(False, "I can’t safely open that application name.")
    app = ALIASES.get(target.lower(), target)
    if platform.system() != "Windows":
        return ToolResult(False, "Application launching is implemented for Windows in this build.")
    try:
        if app == "ms-settings:":
            os.startfile("ms-settings:")
        elif app in WINDOWS_COMMANDS:
            subprocess.Popen(WINDOWS_COMMANDS[app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "Start-Process", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ToolResult(True, f"Opened {target}.", {"application": target})
    except (OSError, subprocess.SubprocessError) as exc:
        return ToolResult(False, f"I couldn’t open {target}: {exc}")

def close_application(application: str) -> ToolResult:
    """Close a named Windows application by process image."""
    if platform.system() != "Windows":
        return ToolResult(False, "Closing applications is currently Windows-only.")
    target = ALIASES.get(application.strip().lower(), application.strip())
    images = {"chrome": "chrome.exe", "msedge": "msedge.exe", "notepad": "notepad.exe", "calc": "CalculatorApp.exe", "code": "Code.exe"}
    image = images.get(target, target if target.endswith(".exe") else target + ".exe")
    result = subprocess.run(["taskkill", "/IM", image, "/F"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode == 0:
        return ToolResult(True, f"Closed {application}.")
    return ToolResult(False, result.stderr.strip() or f"{application} was not running.")
