import sys
from types import ModuleType

from jarvis.config import Settings
from jarvis.llm.provider import LLMProvider


def test_settings_reads_jarvis_gemini_environment(monkeypatch):
    monkeypatch.setenv("JARVIS_OPENAI_API_KEY", "jarvis-key")
    monkeypatch.setenv("JARVIS_MODEL", "gemini-3.8-flash")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings()

    assert settings.api_key == "jarvis-key"
    assert settings.model == "gemini-3.8-flash"
    assert settings.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_provider_is_configured_by_jarvis_key_not_openai_key(monkeypatch):
    monkeypatch.setenv("JARVIS_OPENAI_API_KEY", "jarvis-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert LLMProvider(Settings()).is_configured is True


def test_provider_initializes_openai_client_with_configured_gemini_values(monkeypatch):
    calls = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    fake_openai = ModuleType("openai")
    fake_openai.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    settings = Settings(
        api_key="jarvis-key",
        model="gemini-3.8-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    provider = LLMProvider(settings)
    provider.create_client()

    assert calls == [{"api_key": "jarvis-key", "base_url": settings.base_url, "timeout": settings.response_timeout}]
