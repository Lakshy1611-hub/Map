"""Voice input with wake-word and short conversational sessions."""
from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable

from jarvis.config import Settings


class SpeechToText:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = False
        self._session_until = 0.0

    def listen_once(self) -> str:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        for language in (self.settings.stt_primary_language, "hi-IN", "en-US"):
            try:
                return recognizer.recognize_google(audio, language=language).strip()
            except (sr.UnknownValueError, sr.RequestError):
                continue
        return ""

    @staticmethod
    def strip_wake_phrase(text: str, wake_phrase: str) -> str:
        pattern = r"^\s*(?:hey\s+)?" + re.escape(wake_phrase) + r"[\s,;:.-]*"
        return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    def start_background(
        self,
        on_command: Callable[[str], None],
        on_listening: Callable[[bool], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_wake: Callable[[], None] | None = None,
    ) -> None:
        if self._thread and self._thread.is_alive():
            self._enabled = True
            return
        self._stop.clear()
        self._enabled = True

        def loop() -> None:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = True
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.35)
                    if on_listening:
                        on_listening(True)
                    while not self._stop.is_set():
                        try:
                            audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=7)
                        except sr.WaitTimeoutError:
                            continue
                        heard = ""
                        for language in (self.settings.stt_primary_language, "hi-IN", "en-US"):
                            try:
                                heard = recognizer.recognize_google(audio, language=language).strip()
                                if heard:
                                    break
                            except (sr.UnknownValueError, sr.RequestError):
                                continue
                        if not heard:
                            continue

                        if self.settings.always_listening:
                            command = self.strip_wake_phrase(heard, self.settings.wake_phrase)
                            if not command:
                                if on_wake:
                                    on_wake()
                                self._session_until = time.monotonic() + 18.0
                                continue
                            if time.monotonic() >= self._session_until and command == heard:
                                continue
                        else:
                            command = heard

                        if command:
                            on_command(command)
                            self._session_until = time.monotonic() + 18.0
            except Exception as exc:
                if on_error:
                    on_error(str(exc))
            finally:
                self._enabled = False
                if on_listening:
                    on_listening(False)

        self._thread = threading.Thread(target=loop, name="jarvis-stt", daemon=True)
        self._thread.start()

    def arm_session(self, seconds: float = 18.0) -> None:
        self._session_until = time.monotonic() + max(1.0, min(60.0, seconds))

    def stop_background(self) -> None:
        self._enabled = False
        self._session_until = 0.0
        self._stop.set()

    @property
    def enabled(self) -> bool:
        return self._enabled and not self._stop.is_set()