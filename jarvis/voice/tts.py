"""Replaceable, non-blocking text-to-speech support for JARVIS.

Edge TTS is the preferred provider because its neural Hindi and Indian English
voices are considerably more natural than the system SAPI voices commonly
exposed through pyttsx3.  pyttsx3 remains a completely local fallback.
"""
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
_LATIN_WORD = re.compile(r"[A-Za-z]+")
_ROMAN_HINDI = {
    "aap": "आप", "ab": "अब", "accha": "अच्छा", "achha": "अच्छा", "aur": "और",
    "bata": "बता", "bhai": "भाई", "hai": "है", "haan": "हाँ", "hindi": "हिंदी",
    "jarvis": "जार्विस", "ji": "जी", "kar": "कर", "karo": "करो", "kholo": "खोलो",
    "kya": "क्या", "main": "मैं", "nahi": "नहीं", "nahin": "नहीं", "shukriya": "शुक्रिया",
    "theek": "ठीक", "tum": "तुम", "yaar": "यार", "zaroor": "ज़रूर",
}


@dataclass(frozen=True)
class SpeechSegment:
    text: str
    language: str


def clean_for_speech(text: str) -> str:
    """Remove formatting and machine payloads without changing the transcript."""
    candidate = text.strip()
    if not candidate or re.fullmatch(r"\{[\s\S]*\}", candidate):
        return ""
    candidate = re.sub(r"```[\s\S]*?```", "", candidate)
    candidate = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", candidate)
    candidate = re.sub(r"`[^`]*`", "", candidate)
    candidate = re.sub(r"(?m)^\s{0,3}(?:[-*+]\s+|#{1,6}\s+|\d+[.)]\s+)", "", candidate)
    candidate = re.sub(r"[*_~|>#]", "", candidate)
    candidate = re.sub(r"\b(?:tool_call|tool|arguments|json|internal status)\s*[:=].*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


def detect_language(text: str) -> str:
    devanagari = len(_DEVANAGARI.findall(text))
    latin_words = [word.lower() for word in _LATIN_WORD.findall(text)]
    roman_hindi = sum(word in _ROMAN_HINDI for word in latin_words)
    if devanagari and latin_words:
        return HINGLISH
    if devanagari:
        return HINDI
    if roman_hindi:
        return HINGLISH
    return ENGLISH


def prepare_speech(text: str, auto_language: bool = True) -> list[SpeechSegment]:
    """Make display text safe to say and separate Hindi from English where possible."""
    cleaned = clean_for_speech(text)
    if not cleaned:
        return []
    if not auto_language:
        return [SpeechSegment(cleaned, ENGLISH)]
    overall = detect_language(cleaned)
    if overall == ENGLISH:
        return [SpeechSegment(cleaned, ENGLISH)]

    # Transliterate only a deliberately small Hindi conversational vocabulary.
    # Brand/product words (Chrome, Windows, Google, etc.) are left English.
    pieces: list[SpeechSegment] = []
    current_language: str | None = None
    buffer = ""
    for part in re.findall(r"[\u0900-\u097f]+|[A-Za-z]+|[^\u0900-\u097fA-Za-z]+", cleaned):
        word = part.lower()
        if not _DEVANAGARI.search(part) and not _LATIN_WORD.search(part):
            language = current_language or overall
        else:
            language = HINDI if _DEVANAGARI.search(part) or word in _ROMAN_HINDI else ENGLISH
        rendered = _ROMAN_HINDI.get(word, part)
        if current_language is not None and language != current_language and buffer.strip():
            pieces.append(SpeechSegment(buffer.strip(), current_language))
            buffer = ""
        current_language = language
        buffer += rendered
    if buffer.strip():
        pieces.append(SpeechSegment(buffer.strip(), current_language or overall))
    return pieces


class EdgeTTSProvider:
    """Neural Microsoft Edge voices, rendered and played one language segment at a time."""

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
                target = Path(temp_dir) / f"segment-{index}.mp3"
                asyncio.run(edge_tts.Communicate(segment.text, voice=voice).save(str(target)))
                if cancelled.is_set():
                    return
                pygame.mixer.init()
                try:
                    pygame.mixer.music.load(str(target))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        if cancelled.wait(0.05):
                            pygame.mixer.music.stop()
                            return
                finally:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()


class Pyttsx3Provider:
    """Local fallback using the best matching installed SAPI voice when available."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None

    def _voice_id(self, language: str) -> str | None:
        voices = self._engine.getProperty("voices")
        desired = "hi" if language == HINDI else "en"
        for voice in voices:
            languages = " ".join(str(value) for value in getattr(voice, "languages", [])).lower()
            if desired in languages or desired in getattr(voice, "name", "").lower():
                return voice.id
        return None

    def speak(self, segments: list[SpeechSegment], cancelled: threading.Event) -> None:
        import pyttsx3

        self._engine = pyttsx3.init()
        try:
            for segment in segments:
                if cancelled.is_set():
                    return
                voice_id = self._voice_id(segment.language)
                if voice_id:
                    self._engine.setProperty("voice", voice_id)
                self._engine.say(segment.text)
                self._engine.runAndWait()
        finally:
            self._engine.stop()
            self._engine = None

    def stop(self) -> None:
        if self._engine is not None:
            self._engine.stop()


class TextToSpeech:
    """Provider selector with cancellable, non-blocking speech invocation."""

    def __init__(self, settings: Settings | None = None, provider_factory: Callable[[str], object] | None = None):
        self.settings = settings or Settings()
        self._provider_factory = provider_factory
        self._cancelled = threading.Event()
        self._provider: object | None = None
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
                # A network/audio failure in Edge TTS must not disable speech on a
                # machine that still has the local Windows SAPI fallback available.
                if isinstance(provider, EdgeTTSProvider) and not self._cancelled.is_set():
                    fallback = self._create_provider("pyttsx3")
                    if fallback is not None:
                        self._provider = fallback
                        fallback.speak(segments, self._cancelled)
                    else:
                        raise
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
