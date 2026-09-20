from __future__ import annotations
import os, platform, shutil, subprocess
from jarvis.core.models import ToolResult
ALIASES={"chrome":"chrome", "google chrome":"chrome", "notepad":"notepad", "vs code":"code", "vscode":"code", "visual studio code":"code"}
def open_application(application: str) -> ToolResult:
    app=ALIASES.get(application.strip().lower(), application.strip())
    if platform.system() == "Windows":
        commands={"chrome":["cmd","/c","start","","chrome"],"notepad":["notepad"],"code":["code"]}; cmd=commands.get(app,[app])
    elif app == "notepad": cmd=[os.getenv("EDITOR", "nano")]
    else: cmd=[app]
    if platform.system() != "Windows" and not shutil.which(cmd[0]): return ToolResult(False, f"I couldn't open {application} because it wasn't found on this system.")
    try: subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return ToolResult(True, f"Opened {application}.", {"application":application})
    except OSError as e: return ToolResult(False, f"I couldn't open {application}: {e}")
def close_application(application: str) -> ToolResult:
    if platform.system() != "Windows": return ToolResult(False,"Closing applications is currently implemented for Windows only.")
    p=subprocess.run(["taskkill","/IM",f"{ALIASES.get(application.lower(),application)}.exe","/F"],capture_output=True,text=True)
    return ToolResult(p.returncode==0, "Closed "+application if p.returncode==0 else p.stderr.strip())
