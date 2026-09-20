"""Environment-backed configuration for JARVIS providers and desktop behavior."""
from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from pathlib import Path

if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=Path(".env"), override=False)


@dataclass(frozen=True)
class Settings:
    """Read provider values when a Settings object is created, not at module import."""

    api_key: str = field(default_factory=lambda: os.getenv("JARVIS_OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("JARVIS_MODEL", "gpt-4o-mini"))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", ""))
    stt_provider: str = field(default_factory=lambda: os.getenv("JARVIS_STT_PROVIDER", "speech_recognition"))
    tts_provider: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_PROVIDER", "pyttsx3"))
    tts_language_auto: bool = field(default_factory=lambda: os.getenv("JARVIS_TTS_LANGUAGE_AUTO", "true").lower() == "true")
    tts_english_voice: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_ENGLISH_VOICE", "en-IN-NeerjaNeural"))
    tts_hindi_voice: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_HINDI_VOICE", "hi-IN-SwaraNeural"))
    wake_phrase: str = field(default_factory=lambda: os.getenv("JARVIS_WAKE_PHRASE", "jarvis"))
    voice_enabled: bool = field(default_factory=lambda: os.getenv("JARVIS_VOICE_ENABLED", "true").lower() == "true")
    debug: bool = field(default_factory=lambda: os.getenv("JARVIS_DEBUG", "false").lower() == "true")
    memory_enabled: bool = field(default_factory=lambda: os.getenv("JARVIS_MEMORY_ENABLED", "true").lower() == "true")
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("JARVIS_DATA_DIR", "data")))
