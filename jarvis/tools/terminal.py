from __future__ import annotations

import platform
import subprocess

from jarvis.core.models import ToolResult


def run_command(command: str) -> ToolResult:
    """Run a local shell command and return its output."""
    if not command.strip():
        return ToolResult(False, "No command was provided.")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = (result.stdout or result.stderr or "").strip()
        return ToolResult(result.returncode == 0, output[-5000:] or f"Command exited with code {result.returncode}.", {"returncode": result.returncode})
    except subprocess.TimeoutExpired:
        return ToolResult(False, "The command timed out after 60 seconds.")
    except Exception as exc:
        return ToolResult(False, f"Command failed: {exc}")


def run_powershell(command: str) -> ToolResult:
    """Run a PowerShell command directly on Windows."""
    if platform.system() != "Windows":
        return ToolResult(False, "PowerShell execution is currently available on Windows only.")
    if not command.strip():
        return ToolResult(False, "No PowerShell command was provided.")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        output = (result.stdout or result.stderr or "").strip()
        return ToolResult(result.returncode == 0, output[-5000:] or f"PowerShell exited with code {result.returncode}.", {"returncode": result.returncode})
    except subprocess.TimeoutExpired:
        return ToolResult(False, "PowerShell timed out after 60 seconds.")
    except Exception as exc:
        return ToolResult(False, f"PowerShell failed: {exc}")
