from jarvis.config import Settings
from jarvis.voice.stt import SpeechToText


def test_wake_phrase_is_removed_case_insensitively():
    assert SpeechToText.strip_wake_phrase("Jarvis, chrome kholo", "jarvis") == "chrome kholo"
    assert SpeechToText.strip_wake_phrase("hey JARVIS open notepad", "jarvis") == "open notepad"


def test_unrelated_text_is_not_accepted_as_wake_command():
    assert SpeechToText.strip_wake_phrase("chrome kholo", "jarvis") == "chrome kholo"


def test_default_voice_settings_enable_wake_mode():
    settings = Settings(always_listening=True, wake_phrase="jarvis")
    assert settings.always_listening is True
    assert settings.wake_phrase == "jarvis"
