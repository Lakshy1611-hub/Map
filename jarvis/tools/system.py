import platform
from jarvis.core.models import ToolResult
def get_system_information(): return ToolResult(True,"System information retrieved.",{"system":platform.system(),"release":platform.release(),"machine":platform.machine()})
