from __future__ import annotations
import re
from jarvis.config import Settings
from jarvis.core.models import AssistantState, ChatReply, ToolResult
from jarvis.core.conversation import Conversation
from jarvis.llm.provider import LLMProvider
from jarvis.security.permissions import needs_confirmation
from jarvis.tools.registry import ToolRegistry
from jarvis.tools import applications, automation, screen, browser, files, terminal, system
class Assistant:
 def __init__(self,settings:Settings|None=None):
  self.settings=settings or Settings(); self.state=AssistantState.IDLE; self.conversation=Conversation(); self.registry=ToolRegistry(); self.pending=None; self._register(); self.llm=LLMProvider(self.settings)
 def _register(self):
  for module in (applications,automation,screen,browser,files,terminal,system):
   for name, fn in vars(module).items():
    if callable(fn) and not name.startswith("_") and name not in {"ToolResult","Path"}: self.registry.register(name,fn)
 def _fallback(self,text):
  low=text.lower().strip()
  if low in {"ruk","ruk ja","stop","pause"}: return {"reply":"The current task has been paused.","tool":None,"arguments":{}}
  m=re.search(r"(?:open|launch|start|kholo|khol do|kholde)\s+(?:the\s+)?(google chrome|chrome|notepad|vs code|vscode)",low)
  if not m: m=re.search(r"(google chrome|chrome|notepad|vs code|vscode)\s+(?:kholo|open kar|start kar)",low)
  if m: return {"reply":"","tool":"open_application","arguments":{"application":m.group(1)}}
  m=re.search(r"(?:type|likho|likh do)\s+(.+)",text,re.I)
  if m: return {"reply":"","tool":"keyboard_type","arguments":{"text":m.group(1)}}
  if any(p in low for p in ("screenshot","screen shot","screen capture")): return {"reply":"","tool":"take_screenshot","arguments":{}}
  if "youtube" in low and self.conversation.current_application in {"chrome","google chrome"}: return {"reply":"","tool":"open_url","arguments":{"url":"youtube.com"}}
  if "kya kya kar" in low or "what can you do" in low: return {"reply":"Main normal conversation kar sakta hoon, Chrome/Notepad jaise apps khol sakta hoon, focused app mein type kar sakta hoon, mouse/keyboard control aur screenshots le sakta hoon. API key set karne par LLM natural multi-step tool selection bhi karta hai.","tool":None,"arguments":{}}
  if "kya haal" in low or "how are you" in low: return {"reply":"Badhiya bhai 😄 bata kya karna hai?","tool":None,"arguments":{}}
  return {"reply":"Main ready hoon. Aap conversationally bol sakte ho—jaise ‘Chrome kholo’, ‘type Hello bhai’, ya ‘screenshot lo’. Configure an AI API key for richer answers and dynamic tool planning.","tool":None,"arguments":{}}
 def handle(self,text:str,confirmed=False)->ChatReply:
  self.state=AssistantState.THINKING; self.conversation.add("user",text)
  if self.pending and confirmed:
   tool,args=self.pending; self.pending=None; plan={"reply":"","tool":tool,"arguments":args}
  else:
   try: plan=self.llm.respond(self.conversation.history(),self.registry.names()) or self._fallback(text)
   except Exception as exc: plan={"reply":f"AI provider error: {exc}. I can still handle basic local commands.","tool":None,"arguments":{}}
  tool,args=plan.get("tool"),plan.get("arguments") or {}
  if tool and needs_confirmation(tool,args) and not confirmed:
   self.pending=(tool,args); self.state=AssistantState.IDLE; reply=ChatReply("That action can be destructive. Please confirm before I continue."); self.conversation.add("assistant",reply.text); return reply
  results=[]
  if tool:
   self.state=AssistantState.EXECUTING; result=self.registry.execute(tool,**args); results=[result]
   if result.ok and tool=="open_application": self.conversation.current_application=args.get("application")
   reply=plan.get("reply") or result.message
  else: reply=plan.get("reply","")
  self.state=AssistantState.SPEAKING; self.conversation.add("assistant",reply); self.state=AssistantState.IDLE
  return ChatReply(reply,AssistantState.IDLE,results)
