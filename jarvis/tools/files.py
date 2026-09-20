from pathlib import Path
import shutil
from jarvis.core.models import ToolResult
def create_file(path:str,content:str=""): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(content,encoding="utf-8"); return ToolResult(True,f"Created {path}.")
def read_file(path:str): return ToolResult(True,Path(path).read_text(encoding="utf-8"),{"path":path})
def write_file(path:str,content:str): Path(path).write_text(content,encoding="utf-8"); return ToolResult(True,f"Wrote {path}.")
def rename_file(source:str,destination:str): Path(source).rename(destination); return ToolResult(True,f"Renamed to {destination}.")
def move_file(source:str,destination:str): shutil.move(source,destination); return ToolResult(True,f"Moved to {destination}.")
def copy_file(source:str,destination:str): shutil.copy2(source,destination); return ToolResult(True,f"Copied to {destination}.")
def delete_file(path:str): Path(path).unlink(); return ToolResult(True,f"Deleted {path}.")
def list_directory(path:str="."): return ToolResult(True,"Directory listed.",{"entries":[p.name for p in Path(path).iterdir()]})
def find_file(pattern:str,path:str="."): return ToolResult(True,"Search completed.",{"matches":[str(p) for p in Path(path).rglob(pattern)][:100]})
