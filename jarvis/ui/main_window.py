"""Responsive Tk desktop shell for JARVIS. It owns presentation, not assistant logic."""
from __future__ import annotations

import importlib.util
import math
import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import TYPE_CHECKING

from jarvis.core.assistant import Assistant
from jarvis.core.models import AssistantState
from jarvis.ui.tray import TrayController

if TYPE_CHECKING:
    from jarvis.core.models import ChatReply

BACKGROUND = "#06101d"
SURFACE = "#0b1b2e"
SURFACE_ALT = "#10263d"
TEXT = "#e9f7ff"
MUTED = "#91a9ba"
ACCENT = "#31e0da"
STATE_COLORS = {
    AssistantState.IDLE: "#47dfb5",
    AssistantState.LISTENING: "#42dfff",
    AssistantState.THINKING: "#a987ff",
    AssistantState.EXECUTING: "#ffd166",
    AssistantState.SPEAKING: "#ff8ecc",
    AssistantState.PAUSED: "#91a9ba",
}


class JarvisWindow:
    """A real desktop window with keyboard input, voice capture, TTS, and tray hiding."""

    def __init__(self, assistant: Assistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.root.title("JARVIS — Desktop AI Assistant")
        self.root.geometry("920x760")
        self.root.minsize(700, 600)
        self.root.configure(bg=BACKGROUND)
        self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
        self.root.bind("<Control-Return>", lambda _event: self.submit())
        self.status = tk.StringVar(value="READY")
        self.action = tk.StringVar(value="Awaiting your instruction")
        self.mic_text = tk.StringVar(value="MIC OFF — click Talk to speak")
        self._phase = 0.0
        self._state = AssistantState.IDLE
        self._busy = False
        self.tts = None
        self._tray = TrayController(self.show, self.pause, self.quit)
        self._build()
        self._set_state(AssistantState.IDLE, "Awaiting your instruction")
        self._animate()

    def _build(self) -> None:
        header = tk.Frame(self.root, bg=BACKGROUND)
        header.pack(fill="x", padx=34, pady=(24, 8))
        tk.Label(header, text="J A R V I S", font=("Segoe UI", 27, "bold"), fg=TEXT, bg=BACKGROUND).pack(side="left")
        tk.Label(header, text="PHASE 1  •  DESKTOP AI", font=("Segoe UI", 9, "bold"), fg=ACCENT, bg=BACKGROUND).pack(side="left", padx=15, pady=11)
        self.state_badge = tk.Label(header, textvariable=self.status, font=("Segoe UI", 9, "bold"), padx=12, pady=5, bg=STATE_COLORS[AssistantState.IDLE], fg=BACKGROUND)
        self.state_badge.pack(side="right")

        dashboard = tk.Frame(self.root, bg=BACKGROUND)
        dashboard.pack(fill="x", padx=34)
        dashboard.columnconfigure(0, weight=1)
        dashboard.columnconfigure(1, weight=2)

        orb_card = tk.Frame(dashboard, bg=SURFACE, highlightbackground="#1e4960", highlightthickness=1)
        orb_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.orb = tk.Canvas(orb_card, width=270, height=230, bg=SURFACE, highlightthickness=0)
        self.orb.pack(expand=True, fill="both", padx=14, pady=(12, 0))
        tk.Label(orb_card, textvariable=self.mic_text, bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(0, 14))

        status_card = tk.Frame(dashboard, bg=SURFACE, highlightbackground="#1e4960", highlightthickness=1)
        status_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(status_card, text="CURRENT ACTIVITY", bg=SURFACE, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(22, 4))
        tk.Label(status_card, textvariable=self.action, bg=SURFACE, fg=TEXT, font=("Segoe UI", 16, "bold"), wraplength=460, justify="left").pack(anchor="w", padx=22)
        tk.Label(status_card, text="Conversation stays on this device unless you configure an AI provider.", bg=SURFACE, fg=MUTED, font=("Segoe UI", 9), wraplength=460, justify="left").pack(anchor="w", padx=22, pady=(12, 18))
        self.waveform = tk.Canvas(status_card, height=74, bg=SURFACE, highlightthickness=0)
        self.waveform.pack(fill="x", padx=20, pady=(0, 15))

        transcript_label = tk.Frame(self.root, bg=BACKGROUND)
        transcript_label.pack(fill="x", padx=34, pady=(19, 5))
        tk.Label(transcript_label, text="LIVE CONVERSATION", bg=BACKGROUND, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(transcript_label, text="Ctrl+Enter to send", bg=BACKGROUND, fg=MUTED, font=("Segoe UI", 9)).pack(side="right")
        self.transcript = scrolledtext.ScrolledText(self.root, height=14, bg="#081827", fg=TEXT, insertbackground=TEXT, relief="flat", borderwidth=0, font=("Segoe UI", 10), wrap="word", padx=16, pady=14)
        self.transcript.pack(fill="both", expand=True, padx=34)
        self.transcript.configure(state="disabled")

        composer = tk.Frame(self.root, bg=BACKGROUND)
        composer.pack(fill="x", padx=34, pady=20)
        self.entry = tk.Entry(composer, bg=SURFACE_ALT, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=12)
        self.entry.bind("<Return>", lambda _event: self.submit())
        self.send = self._button(composer, "SEND", self.submit, "#176d99")
        self.send.pack(side="left", padx=8)
        self.talk = self._button(composer, "◉  TALK", self.listen, "#128a7d")
        self.talk.pack(side="left")
        self.stop_button = self._button(composer, "STOP", self.stop_speech, "#6a3554")
        self.stop_button.pack(side="left", padx=(8, 0))
        self.root.bind("<Escape>", lambda _event: self.stop_speech())
        self.entry.focus_set()

    def _button(self, parent: tk.Widget, label: str, command, color: str) -> tk.Button:
        return tk.Button(parent, text=label, command=command, bg=color, fg="white", activebackground=ACCENT, activeforeground=BACKGROUND, relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=11, cursor="hand2")

    def _set_state(self, state: AssistantState, action: str) -> None:
        self._state = state
        self.status.set(state.value.upper())
        self.action.set(action)
        self.state_badge.configure(bg=STATE_COLORS[state])
        if state is AssistantState.LISTENING:
            self.mic_text.set("MIC ACTIVE — listening for one request")
        elif state is AssistantState.PAUSED:
            self.mic_text.set("MIC PAUSED")
        else:
            self.mic_text.set("MIC OFF — click Talk to speak")

    def _animate(self) -> None:
        self._phase += 0.15
        color = STATE_COLORS[self._state]
        pulse = 8 + (math.sin(self._phase) + 1) * (12 if self._state != AssistantState.IDLE else 4)
        cx, cy = 135, 108
        self.orb.delete("all")
        for radius, stipple in ((90 + pulse, "gray25"), (72 + pulse / 2, "gray50")):
            self.orb.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill=color, outline="", stipple=stipple)
        self.orb.create_oval(61, 34, 209, 182, fill="#0d3750", outline=color, width=3)
        self.orb.create_oval(83, 56, 187, 160, fill=color, outline="")
        self.orb.create_oval(105, 78, 165, 138, fill="#dffeff", outline="")
        self.orb.create_text(cx, 205, text=self._state.value.upper(), fill=color, font=("Segoe UI", 10, "bold"))
        self.waveform.delete("all")
        width = max(self.waveform.winfo_width(), 500)
        intensity = 5 if self._state is AssistantState.IDLE else 20
        for index in range(34):
            x = 10 + index * (width - 20) / 33
            height = 6 + abs(math.sin(self._phase + index * 0.52)) * intensity
            self.waveform.create_line(x, 37-height, x, 37+height, fill=color, width=3)
        self.root.after(45, self._animate)

    def append(self, role: str, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{role}\n", ("role",))
        self.transcript.insert("end", f"{text}\n\n")
        self.transcript.tag_configure("role", foreground=ACCENT, font=("Segoe UI", 9, "bold"))
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def submit(self) -> None:
        text = self.entry.get().strip()
        if text.lower() in {"stop", "ruk", "ruk ja"}:
            self.entry.delete(0, "end")
            self.stop_speech()
            return
        if text and not self._busy:
            self.entry.delete(0, "end")
            self.process(text)

    def process(self, text: str) -> None:
        self._busy = True
        self.send.configure(state="disabled")
        self.talk.configure(state="disabled")
        self.append("YOU", text)
        self._set_state(AssistantState.THINKING, "Understanding your request…")
        self.root.after(180, self._show_executing_if_busy)
        threading.Thread(target=self._work, args=(text,), daemon=True).start()

    def _show_executing_if_busy(self) -> None:
        if self._busy and self._state is AssistantState.THINKING:
            self._set_state(AssistantState.EXECUTING, "Executing requested tool…")

    def _work(self, text: str) -> None:
        reply = self.assistant.handle(text)
        self.root.after(0, lambda: self._finish(reply))

    def _finish(self, reply: ChatReply) -> None:
        self.append("JARVIS", reply.text)
        self._set_state(AssistantState.SPEAKING, reply.text)
        self._speak(reply.text)

    def _speak(self, text: str) -> None:
        if not self.assistant.settings.voice_enabled:
            self._ready()
            return
        from jarvis.voice.tts import TextToSpeech

        try:
            self.tts = TextToSpeech(self.assistant.settings)
            self.tts.speak_async(text, lambda: self.root.after(0, self._speech_finished))
        except Exception:
            self._ready()

    def _speech_finished(self) -> None:
        if self._state is AssistantState.SPEAKING:
            self._ready()

    def stop_speech(self) -> None:
        """Interrupt audio immediately; Escape is a keyboard shortcut for this action."""
        if self.tts is not None:
            self.tts.stop()
        if self._state is AssistantState.SPEAKING:
            self.append("JARVIS", "Speech stopped.")
            self._ready()

    def _ready(self) -> None:
        self._busy = False
        self.send.configure(state="normal")
        self.talk.configure(state="normal")
        self._set_state(AssistantState.IDLE, "Awaiting your instruction")

    def listen(self) -> None:
        if self._busy:
            return
        self._set_state(AssistantState.LISTENING, "Listening… microphone is active only for this request.")
        self._busy = True
        self.talk.configure(state="disabled")
        threading.Thread(target=self._listen_work, daemon=True).start()

    def _listen_work(self) -> None:
        if importlib.util.find_spec("speech_recognition") is None:
            self.root.after(0, lambda: self._voice_error("SpeechRecognition is not installed."))
            return
        from jarvis.voice.stt import SpeechToText

        try:
            text = SpeechToText().listen_once()
            self.root.after(0, lambda: self._handle_voice_text(text))
        except Exception as exc:
            self.root.after(0, lambda: self._voice_error(str(exc)))

    def _handle_voice_text(self, text: str) -> None:
        self._busy = False
        if text:
            self.process(text)
        else:
            self._voice_empty()

    def _voice_empty(self) -> None:
        self.append("JARVIS", "I didn't catch that. Please try again.")
        self._ready()

    def _voice_error(self, error: str) -> None:
        self.append("JARVIS", f"Voice input is unavailable: {error}")
        self._ready()

    def show(self) -> None:
        self.root.after(0, lambda: (self.root.deiconify(), self.root.lift(), self.root.focus_force()))

    def pause(self) -> None:
        self.root.after(0, lambda: self._set_state(AssistantState.PAUSED, "Assistant paused"))

    def _minimize_to_tray(self) -> None:
        if self._tray.start():
            self.root.withdraw()
        else:
            self.root.iconify()

    def quit(self) -> None:
        self._tray.stop()
        self.root.after(0, self.root.destroy)

    def run(self) -> None:
        self._tray.start()
        self.root.mainloop()
