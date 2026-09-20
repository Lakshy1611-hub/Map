from __future__ import annotations
import webbrowser
from urllib.parse import quote_plus
from jarvis.core.models import ToolResult
def open_url(url:str)->ToolResult:
    if not url.startswith(("http://","https://")): url="https://"+url
    return ToolResult(webbrowser.open(url),f"Opened {url}.",{"url":url})
def search_web(query:str)->ToolResult: return open_url("https://www.google.com/search?q="+quote_plus(query))
