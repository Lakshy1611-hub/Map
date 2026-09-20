from __future__ import annotations
class TextToSpeech:
 def __init__(self):
  import pyttsx3; self.engine=pyttsx3.init()
 def say(self,text:str): self.engine.say(text); self.engine.runAndWait()
