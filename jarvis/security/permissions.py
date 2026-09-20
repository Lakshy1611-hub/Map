from __future__ import annotations

DANGEROUS_TOKENS = (
    "rm -rf", "format ", "shutdown", "restart-computer", "remove-item -recurse",
    "del /s", "diskpart", "clear-disk", "stop-computer", "erase",
)

SENSITIVE_CLICK_WORDS = (
    "delete", "remove", "purchase", "buy", "pay", "send", "submit", "confirm",
    "publish", "post", "logout", "sign out",
)


def needs_confirmation(tool: str, arguments: dict) -> bool:
    if tool in {"delete_file", "move_file"}:
        return True
    if tool == "visual_click":
        target = str(arguments.get("target", "")).lower()
        return any(token in target for token in SENSITIVE_CLICK_WORDS)
    if tool in {"run_command", "run_powershell"}:
        command = str(arguments.get("command", "")).lower()
        return any(token in command for token in DANGEROUS_TOKENS)
    return False
