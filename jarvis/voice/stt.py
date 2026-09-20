from __future__ import annotations
class SpeechToText:
 def listen_once(self)->str:
  import speech_recognition as sr
  recognizer=sr.Recognizer()
  with sr.Microphone() as source:
   recognizer.adjust_for_ambient_noise(source,duration=.3); audio=recognizer.listen(source,timeout=8,phrase_time_limit=20)
  try: return recognizer.recognize_google(audio,language="en-IN")
  except sr.UnknownValueError: return ""
