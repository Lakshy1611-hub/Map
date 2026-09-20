import subprocess
from jarvis.core.models import ToolResult
def run_command(command:str)->ToolResult:
 p=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=60); return ToolResult(p.returncode==0,p.stdout[-4000:] or p.stderr[-4000:],{"returncode":p.returncode})
def run_powershell(command:str)->ToolResult: return run_command(f'powershell -NoProfile -Command "{command}"')
