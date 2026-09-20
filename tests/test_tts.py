from jarvis.config import Settings
from jarvis.voice.tts import ENGLISH, HINDI, HINGLISH, TextToSpeech, clean_for_speech, detect_language, prepare_speech

def test_english_text_keeps_product_words():
    segments = prepare_speech("Open Chrome and search Google.")
    assert len(segments) == 1
    assert segments[0].language == ENGLISH
    assert "Chrome" in segments[0].text
    assert "Google" in segments[0].text

def test_hindi_text_uses_hindi_voice():
    segments = prepare_speech("नमस्ते भाई, आप कैसे हैं?")
    assert len(segments) == 1
    assert segments[0].language == HINDI
    assert "नमस्ते" in segments[0].text

def test_hinglish_uses_hindi_voice_and_preserves_product_names():
    segments = prepare_speech("Bhai Chrome kholo aur YouTube open karo")
    assert detect_language("Bhai Chrome kholo") == HINGLISH
    assert len(segments) == 1
    assert segments[0].language == HINDI
    assert "भाई" in segments[0].text
    assert "Chrome" in segments[0].text
    assert "YouTube" in segments[0].text

def test_speech_cleaning_strips_machine_content():
    cleaned = clean_for_speech("**Done.** `internal()`")
    assert cleaned == "Done. internal()"
    assert clean_for_speech('{"tool":"open_application","arguments":{}}') == ""

def test_tts_provider_can_fall_back_to_local_engine(monkeypatch):
    import jarvis.voice.tts as tts
    monkeypatch.setattr(tts.importlib.util, "find_spec", lambda name: object() if name == "pyttsx3" else None)
    speaker = TextToSpeech(Settings(tts_provider="edge_tts"))
    assert speaker._create_provider("edge_tts").__class__.__name__ == "Pyttsx3Provider"

def test_tts_settings_are_loaded():
    settings = Settings(tts_provider="edge_tts", tts_language_auto=True, tts_english_voice="en-IN-NeerjaNeural", tts_hindi_voice="hi-IN-SwaraNeural")
    assert settings.tts_provider == "edge_tts"
    assert settings.tts_language_auto is True

def test_tts_is_non_blocking():
    import threading
    import time
    started = threading.Event()
    finished = threading.Event()
    class SlowProvider:
        def speak(self, segments, cancelled):
            started.set()
            time.sleep(0.15)
            finished.set()
    speaker = TextToSpeech(Settings(), provider_factory=lambda _name: SlowProvider())
    started_at = time.monotonic()
    worker = speaker.speak_async("Hello bhai")
    assert time.monotonic() - started_at < 0.05
    assert started.wait(0.1)
    assert worker.is_alive()
    worker.join(1)
    assert finished.is_set()