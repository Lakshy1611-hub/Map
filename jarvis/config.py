"""Runtime configuration for the JARVIS desktop assistant."""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv

    here = Path(__file__).resolve().parents[1]
    load_dotenv(here / ".env", override=False)
    if getattr(sys, "frozen", False):
        load_dotenv(Path(sys.executable).resolve().parent / ".env", override=False)


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Settings are resolved when a Settings instance is created."""

    api_key: str = field(default_factory=lambda: os.getenv("JARVIS_OPENAI_API_KEY", "").strip())
    model: str = field(default_factory=lambda: os.getenv("JARVIS_MODEL", "gemini-3.6-flash").strip())
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ).strip()
    )
    offline_provider: str = field(default_factory=lambda: os.getenv("JARVIS_OFFLINE_PROVIDER", "ollama").strip())
    offline_model: str = field(default_factory=lambda: os.getenv("JARVIS_OFFLINE_MODEL", "gemma4:4b").strip())
    ollama_url: str = field(default_factory=lambda: os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434").strip())
    thinking_level: str = field(default_factory=lambda: os.getenv("JARVIS_THINKING_LEVEL", "low").strip().lower())
    response_timeout: float = field(default_factory=lambda: float(os.getenv("JARVIS_RESPONSE_TIMEOUT", "25")))
    max_agent_steps: int = field(default_factory=lambda: max(1, min(6, int(os.getenv("JARVIS_MAX_AGENT_STEPS", "4"))))
    voice_enabled: bool = field(default_factory=lambda: _env_bool("JARVIS_VOICE_ENABLED", True))
    always_listening: bool = field(default_factory=lambda: _env_bool("JARVIS_ALWAYS_LISTENING", True))
    wake_phrase: str = field(default_factory=lambda: os.getenv("JARVIS_WAKE_PHRASE", "jarvis").strip())
    stt_provider: str = field(default_factory=lambda: os.getenv("JARVIS_STT_PROVIDER", "speech_recognition").strip())
    stt_primary_language: str = field(default_factory=lambda: os.getenv("JARVIS_STT_LANGUAGE", "en-IN").strip())
    tts_provider: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_PROVIDER", "edge_tts").strip())
    tts_language_auto: bool = field(default_factory=lambda: _env_bool("JARVIS_TTS_LANGUAGE_AUTO", True))
    tts_english_voice: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_ENGLISH_VOICE", "en-IN-NeerjaNeural").strip())
    tts_hindi_voice: str = field(default_factory=lambda: os.getenv("JARVIS_TTS_HINDI_VOICE", "hi-IN-SwaraNeural").strip())
    memory_enabled: bool = field(default_factory=lambda: _env_bool("JARVIS_MEMORY_ENABLED", True))
    auto_update_check: bool = field(default_factory=lambda: _env_bool("JARVIS_AUTO_UPDATE_CHECK", True))
    debug: bool = field(default_factory=lambda: _env_bool("JARVIS_DEBUG", False))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("JARVIS_DATA_DIR", str(Path.home() / ".jarvis"))))

    @property
    def app_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[1]

    @property
    def offline_enabled(self) -> bool:
        return self.offline_provider.lower() not in {"", "none", "disabled"}
