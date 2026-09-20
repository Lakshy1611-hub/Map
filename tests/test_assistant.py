from jarvis.core.assistant import Assistant
from jarvis.core.models import ToolResult
class FakeRegistry:
 def __init__(self): self.calls=[]
 def execute(self,name,**args): self.calls.append((name,args)); return ToolResult(True,"ok")
 def names(self): return ["open_application","keyboard_type","take_screenshot"]
def make():
 a=Assistant(); a.registry=FakeRegistry(); return a
def test_hinglish_opens_chrome():
 a=make(); a.handle("bhai chrome kholo"); assert a.registry.calls==[("open_application",{"application":"chrome"})]
def test_typing_selects_explicit_tool():
 a=make(); a.handle("type Hello bhai"); assert a.registry.calls==[("keyboard_type",{"text":"Hello bhai"})]
def test_context_youtube_after_chrome():
 a=make(); a.handle("Chrome open kar"); a.handle("ab YouTube pe ja"); assert a.registry.calls[-1][0]=="open_url"
def test_conversation_has_friend_response(): assert "Badhiya" in make().handle("bhai kya haal hai?").text
def test_delete_requires_confirmation():
 a=make(); a.llm.respond=lambda *_:{"reply":"", "tool":"delete_file","arguments":{"path":"x"}}; assert "confirm" in a.handle("delete x").text.lower(); assert not a.registry.calls
