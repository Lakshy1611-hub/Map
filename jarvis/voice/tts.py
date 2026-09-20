"""Non-blocking multilingual speech for JARVIS."""
from __future__ import annotations

import asyncio
import importlib.util
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from jarvis.config import Settings

ENGLISH = "english"
HINDI = "hindi"
HINGLISH = "hinglish"
_DEVANAGARI = re.compile(r"[\u0900-\u097f]")
_WORD = re.compile(r"[A-Za-z]+")
_ROMAN_HINDI = {
    "aap": "आप", "ab": "अब", "accha": "अच्छा", "achha": "अच्छा", "aur": "और",
    "bata": "बता", "bhai": "भाई", "hai": "है", "haan": "हाँ", "ho": "हो",
    "jarvis": "जार्विस", "kar": "कर", "karo": "करो", "kholo": "खोलो",
    "kya": "क्या", "main": "मैं", "mein": "में", "nahi": "नहीं", "nahin": "नहीं",
    "shukriya": "शुक्रिया", "theek": "ठीक", "tum": "तुम", "yaar": "यार",
    "zaroor": "ज़रूर", "ruk": "रुक", "gaya": "गया", "ruko": "रुको",
    "haanji": "हाँ जी", "bolo": "बोलो", "bol": "बोल", "chalo": "चलो",
}

@dataclass(frozen=True)
class SpeechSegment:
    text: str
    language: str


def clean_for_speech(text: str) -> str:
    value = text.strip()
    if not value or re.fullmatch(r"\{[\s\S]*\}", value):
        return ""
    value = re.sub(r"```[\s\S]*?```", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"(?m)^\s{0,3}(?:[-*+]\s+|#{1,6}\s+|\d+[.)]\s+)", "", value)
    value = re.sub(r"[*_~|>#]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def detect_language(text: str) -> str:
    devanagari = len(_DEVANAGARI.findall(text))
    words = [w.lower() for w in _WORD.findall(text)]
    roman_hindi = sum(w in _ROMAN_HINDI for w in words)
    if devanagari and words:
        return HINGLISH
    if devanagari:
        return HINDI
    return HINGLISH if roman_hindi >= 2 else ENGLISH


def _roman_hindi_to_devanagari(text: str) -> str:
    parts = re.split(r"(\s+|[^A-Za-z]+)", text)
    return "".join(_ROMAN_HINDI.get(part.lower(), part) for part in parts)


def prepare_speech(text: str, auto_language: bool = True) -> list[SpeechSegment]:
    cleaned = clean_for_speech(text)
    if not cleaned:
        return []
    if not auto_language:
        return [SpeechSegment(cleaned, ENGLISH)]
    language = detect_language(cleaned)
    if language == HINDI:
        return [SpeechSegment(cleaned, HINDI)]
    if language == HINGLISH:
        return [SpeechSegment(_roman_hindi_to_devanagari(cleaned), HINDI)]
    return [SpeechSegment(cleaned, ENGLISH)]


class EdgeTTSProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def speak(self, segments: list[SpeechSegment], cancelled: threading.Event) -> None:
        import edge_tts
        import pygame

        with tempfile.TemporaryDirectory(prefix="jarvis-tts-") as temp_dir:
            for index, segment in enumerate(segments):
                if cancelled.is_set():
                    return
                voice = self.settings.tts_hindi_voice if segment.language == HINDI else self.settings.tts_english_voice
                target = Path(temp_dir) / f"speech-{index}.mp3"
                asyncio.run(edge_tts.Communicate(segment.text, voice=voice, rate="+5%", volume="+0%").save(str(target)))
                if cancelled.is_set():
                    return
                pygame.mixer.init()
                try:
                    pygame.mixer.music.load(str(target))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        if cancelled.wait(0.04):
                            pygame.mixer.music.stop()
                            return
                finally:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()


class Pyttsx3Provider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None

    def speak(self, segments: list[SpeechSegment], cancelled: threading.Event) -> None:
        import pyttsx3
        self._engine = pyttsx3.init()
        try:
            for segment in segments:
                if cancelled.is_set():
                    return
                self._engine.say(segment.text)
                self._engine.runAndWait()
        finally:
            self._engine.stop()
            self._engine = None

    def stop(self) -> None:
        if self._engine is not None:
            self._engine.stop()


class TextToSpeech:
    def __init__(self, settings: Settings | None = None, provider_factory: Callable[[str], object] | None = None):
        self.settings = settings or Settings()
        self._provider_factory = provider_factory
        self._cancelled = threading.Event()
        self._provider = None
        self._thread: threading.Thread | None = None

    def _create_provider(self, name: str):
        if self._provider_factory:
            return self._provider_factory(name)
        if name == "edge_tts" and importlib.util.find_spec("edge_tts") and importlib.util.find_spec("pygame"):
            return EdgeTTSProvider(self.settings)
        if importlib.util.find_spec("pyttsx3"):
            return Pyttsx3Provider(self.settings)
        return None

    def say(self, text: str) -> None:
        segments = prepare_speech(text, self.settings.tts_language_auto)
        if not segments:
            return
        provider = self._create_provider(self.settings.tts_provider)
        if provider is None:
            return
        self._provider = provider
        try:
            try:
                provider.speak(segments, self._cancelled)
            except Exception:
                if isinstance(provider, EdgeTTSProvider) and not self._cancelled.is_set():
                    fallback = self._create_provider("pyttsx3")
                    if fallback is not None:
                        self._provider = fallback
                        fallback.speak(segments, self._cancelled)
                    else:
                        raise
        finally:
            self._provider = None

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> threading.Thread:
        self.stop()
        self._cancelled = threading.Event()
        def work() -> None:
            try:
                self.say(text)
            finally:
                if on_complete:
                    on_complete()
        self._thread = threading.Thread(target=work, name="jarvis-tts", daemon=True)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        self._cancelled.set()
        stop = getattr(self._provider, "stop", None)
        if callable(stop):
            stop()