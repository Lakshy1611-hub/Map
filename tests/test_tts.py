import threading
import time

from jarvis.config import Settings
from jarvis.voice.tts import ENGLISH, HINDI, HINGLISH, TextToSpeech, clean_for_speech, detect_language, prepare_speech


def test_english_text_keeps_brand_words_for_natural_english_voice():
    segments = prepare_speech("Open Chrome and search Google in the browser.")

    assert len(segments) == 1
    assert segments[0].language == ENGLISH
    assert "Chrome" in segments[0].text
    assert "Google" in segments[0].text


def test_hindi_text_uses_hindi_voice_segment():
    segments = prepare_speech("नमस्ते भाई, आप कैसे हैं?")

    assert all(segment.language == HINDI for segment in segments)
    assert "नमस्ते" in " ".join(segment.text for segment in segments)


def test_hinglish_transliterates_known_hindi_words_and_preserves_english():
    segments = prepare_speech("Bhai Chrome kholo aur YouTube open karo")

    assert detect_language("Bhai Chrome kholo") == HINGLISH
    assert "भाई" in " ".join(segment.text for segment in segments)
    assert any(segment.language == ENGLISH and "Chrome" in segment.text for segment in segments)
    assert any(segment.language == HINDI for segment in segments)


def test_speech_cleaning_removes_markdown_code_and_tool_data():
    cleaned = clean_for_speech("**Done.** `internal()`\n```json\n{\"tool\": \"open_application\"}\n```")

    assert cleaned == "Done."
    assert clean_for_speech('{"tool":"open_application","arguments":{}}') == ""


def test_edge_selection_falls_back_to_pyttsx3_when_edge_is_unavailable(monkeypatch):
    import jarvis.voice.tts as tts

    monkeypatch.setattr(tts.importlib.util, "find_spec", lambda name: object() if name == "pyttsx3" else None)
    speaker = TextToSpeech(Settings(tts_provider="edge_tts"))

    assert speaker._create_provider("edge_tts").__class__.__name__ == "Pyttsx3Provider"


def test_tts_configuration_reads_provider_language_mode_and_voice_preferences(monkeypatch):
    monkeypatch.setenv("JARVIS_TTS_PROVIDER", "edge_tts")
    monkeypatch.setenv("JARVIS_TTS_LANGUAGE_AUTO", "false")
    monkeypatch.setenv("JARVIS_TTS_ENGLISH_VOICE", "en-US-AvaNeural")
    monkeypatch.setenv("JARVIS_TTS_HINDI_VOICE", "hi-IN-MadhurNeural")

    settings = Settings()

    assert settings.tts_provider == "edge_tts"
    assert settings.tts_language_auto is False
    assert settings.tts_english_voice == "en-US-AvaNeural"
    assert settings.tts_hindi_voice == "hi-IN-MadhurNeural"


def test_speech_invocation_is_non_blocking_and_delivers_prepared_segments():
    delivered = []
    started = threading.Event()

    class SlowProvider:
        def speak(self, segments, cancelled):
            started.set()
            time.sleep(0.15)
            delivered.extend(segments)

    speaker = TextToSpeech(Settings(), provider_factory=lambda _name: SlowProvider())
    started_at = time.monotonic()
    worker = speaker.speak_async("Hello bhai")

    assert time.monotonic() - started_at < 0.05
    assert started.wait(0.1)
    assert worker.is_alive()
    worker.join(1)
    assert delivered[0].text == "Hello"
