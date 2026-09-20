from __future__ import annotations
DANGEROUS_TOKENS=("rm -rf", "format ", "shutdown", "restart-computer", "remove-item -recurse", "del /s", "diskpart")
def needs_confirmation(tool: str, arguments: dict) -> bool:
    if tool == "delete_file": return True
    if tool in {"run_command", "run_powershell"}:
        return any(token in arguments.get("command", "").lower() for token in DANGEROUS_TOKENS)
    return False
