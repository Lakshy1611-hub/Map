from __future__ import annotations
import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv

    load_dotenv()

@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("JARVIS_OPENAI_API_KEY", "")
    model: str = os.getenv("JARVIS_MODEL", "gpt-4o-mini")
    stt_provider: str = os.getenv("JARVIS_STT_PROVIDER", "speech_recognition")
    tts_provider: str = os.getenv("JARVIS_TTS_PROVIDER", "pyttsx3")
    wake_phrase: str = os.getenv("JARVIS_WAKE_PHRASE", "jarvis")
    voice_enabled: bool = os.getenv("JARVIS_VOICE_ENABLED", "true").lower() == "true"
    debug: bool = os.getenv("JARVIS_DEBUG", "false").lower() == "true"
    memory_enabled: bool = os.getenv("JARVIS_MEMORY_ENABLED", "true").lower() == "true"
    data_dir: Path = Path(os.getenv("JARVIS_DATA_DIR", "data"))
