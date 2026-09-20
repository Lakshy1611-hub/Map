from jarvis.config import Settings
from jarvis.core.assistant import Assistant
from jarvis.core.models import ToolResult


class FakeRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, **args):
        self.calls.append((name, args))
        return ToolResult(True, "ok")

    def names(self):
        return ["open_application", "open_url", "keyboard_type", "take_screenshot"]


def make():
    assistant = Assistant(Settings(api_key=""))
    assistant.registry = FakeRegistry()
    return assistant


def test_hinglish_opens_chrome_without_network():
    assistant = make()
    assistant.handle("bhai chrome kholo")
    assert assistant.registry.calls == [("open_application", {"application": "chrome"})]


def test_typing_selects_explicit_tool_without_network():
    assistant = make()
    assistant.handle("type Hello bhai")
    assert assistant.registry.calls == [("keyboard_type", {"text": "Hello bhai"})]


def test_context_youtube_after_chrome_without_network():
    assistant = make()
    assistant.handle("Chrome open kar")
    assistant.handle("ab YouTube pe ja")
    assert assistant.registry.calls[-1] == ("open_url", {"url": "https://youtube.com"})


def test_conversation_has_friend_response_without_network():
    assert "Badhiya" in make().handle("bhai kya haal hai?").text


def test_delete_requires_confirmation():
    assistant = make()
    assistant.llm.plan_tool = lambda *_: {
        "reply": "",
        "tool": "delete_file",
        "arguments": {"path": "x"},
    }
    reply = assistant.handle("delete x")
    assert "confirm" in reply.text.lower()
    assert not assistant.registry.calls


def test_unconfigured_normal_chat_uses_offline_provider():
    assistant = make()
    answer = assistant.handle("hello bhai").text
    assert "Hello bhai" in answer or "offline" in answer.lower()
