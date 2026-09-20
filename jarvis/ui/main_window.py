"""Premium PySide6 desktop UI for JARVIS."""
from __future__ import annotations

import os
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Qt, QRectF, QPointF
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSystemTrayIcon,
    QTextEdit, QVBoxLayout, QWidget
)

from jarvis.config import Settings
from jarvis.core.assistant import Assistant
from jarvis.core.models import AssistantState
from jarvis.voice.stt import SpeechToText
from jarvis.voice.tts import TextToSpeech

BG = "#050913"
PANEL = "#0a1220"
PANEL_2 = "#0d1929"
BORDER = "#17324a"
TEXT = "#ecf7ff"
MUTED = "#7d94a6"
ACCENT = "#49efe1"
ACCENT_2 = "#78a7ff"


class Orb(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.phase = 0.0
        self.state = AssistantState.IDLE
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(32)
        self.setMinimumHeight(260)

    def set_state(self, state: AssistantState) -> None:
        self.state = state
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 - 4
        self.phase += 0.055
        speed = 1.0 if self.state == AssistantState.IDLE else 1.8
        pulse = 10 + (1 + __import__('math').sin(self.phase * speed)) * (9 if self.state == AssistantState.IDLE else 18)
        outer = min(w, h) * 0.37
        grad = QRadialGradient(QPointF(cx, cy), outer + pulse)
        grad.setColorAt(0.0, QColor("#dffffd"))
        grad.setColorAt(0.12, QColor(ACCENT))
        grad.setColorAt(0.45, QColor("#103f55"))
        grad.setColorAt(1.0, QColor(BG))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), outer + pulse, outer + pulse)
        for i in range(3):
            radius = outer * (0.78 + i * 0.11) + pulse * (0.3 + i * 0.2)
            pen = QPen(QColor(ACCENT if i < 2 else ACCENT_2), 1.5)
            pen.setStyle(Qt.SolidLine)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), radius, radius)
        core = outer * 0.48 + pulse * 0.22
        p.setBrush(QColor("#b9fffa"))
        p.setPen(QPen(QColor(ACCENT), 2))
        p.drawEllipse(QPointF(cx, cy), core, core)
        p.setPen(QPen(QColor(BG), 2))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRectF(cx - 90, cy - 11, 180, 24), Qt.AlignCenter, "J A R V I S")
        p.setPen(QColor(MUTED))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(cx - 100, h - 34, 200, 22), Qt.AlignCenter, self.state.value.upper())


class Signals(QObject):
    started = Signal(str)
    delta = Signal(str)
    done = Signal(object)
    error = Signal(str)
    voice_state = Signal(bool)
    voice_error = Signal(str)
    tts_finished = Signal()


class CommandWorker(QRunnable):
    def __init__(self, assistant: Assistant, text: str, signals: Signals):
        super().__init__()
        self.assistant, self.text, self.signals = assistant, text, signals

    def run(self) -> None:
        try:
            self.signals.started.emit(self.text)
            reply = self.assistant.handle(self.text, on_delta=self.signals.delta.emit)
            self.signals.done.emit(reply)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class SettingsDialog(QDialog):
    saved = Signal()

    def __init__(self, settings: Settings, parent: QWidget | None = None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("JARVIS Settings")
        self.setModal(True)
        self.resize(520, 360)
        self.setStyleSheet("QDialog { background:#08111e; color:#ecf7ff; } QLabel { color:#a9bfce; } QLineEdit { background:#0e1b2b; color:#ecf7ff; border:1px solid #1d4058; padding:9px; }")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.model = QLineEdit(settings.model)
        self.base_url = QLineEdit(settings.base_url)
        self.key = QLineEdit(settings.api_key)
        self.key.setEchoMode(QLineEdit.Password)
        self.voice = QCheckBox("Enable spoken replies")
        self.voice.setChecked(settings.voice_enabled)
        self.wake = QCheckBox("Start background wake-word listening")
        self.wake.setChecked(settings.always_listening)
        form.addRow("Model", self.model)
        form.addRow("Gemini/OpenAI Base URL", self.base_url)
        form.addRow("API key", self.key)
        form.addRow("", self.voice)
        form.addRow("", self.wake)
        layout.addLayout(form)
        hint = QLabel("Changes are saved to the local .env file. API keys are never written to the repository.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#6f8ba0")
        layout.addWidget(hint)
        buttons = QHBoxLayout()
        save = QPushButton("SAVE")
        close = QPushButton("CANCEL")
        save.clicked.connect(self.save)
        close.clicked.connect(self.reject)
        buttons.addStretch(1); buttons.addWidget(close); buttons.addWidget(save)
        layout.addLayout(buttons)

    def save(self) -> None:
        env_path = Settings().app_dir / ".env"
        lines = []
        existing = {}
        if env_path.exists():
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                if "=" in raw and not raw.lstrip().startswith("#"):
                    key, value = raw.split("=", 1)
                    existing[key.strip()] = value
        existing.update({
            "JARVIS_OPENAI_API_KEY": self.key.text().strip(),
            "JARVIS_MODEL": self.model.text().strip(),
            "OPENAI_BASE_URL": self.base_url.text().strip(),
            "JARVIS_VOICE_ENABLED": "true" if self.voice.isChecked() else "false",
            "JARVIS_ALWAYS_LISTENING": "true" if self.wake.isChecked() else "false",
        })
        env_path.write_text("\n".join(f"{k}={v}" for k, v in existing.items()) + "\n", encoding="utf-8")
        QMessageBox.information(self, "Saved", "Settings saved. Restart JARVIS if you changed the model or API key.")
        self.saved.emit()
        self.accept()


class JarvisWindow(QMainWindow):
    def __init__(self, assistant: Assistant):
        super().__init__()
        self.assistant = assistant
        self.settings = assistant.settings
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(4)
        self.signals = Signals()
        self.voice = SpeechToText(self.settings)
        self.tts = TextToSpeech(self.settings)
        self.typing_mode = False
        self.quitting = False
        self._stream_started = False
        self.tray = QSystemTrayIcon(self._make_icon(), self)
        self._configure_window()
        self._build_ui()
        self._connect_signals()
        self._set_state(AssistantState.IDLE, "Haan bhai, JARVIS online hai. Bolo kya karna hai.")
        if self.settings.voice_enabled:
            self.tts.speak_async("Haan bhai, JARVIS online hai. Bolo kya karna hai.")
        if self.settings.always_listening and self.settings.voice_enabled:
            self.start_voice()

    def _configure_window(self) -> None:
        self.setWindowTitle("JARVIS — Personal AI Assistant")
        self.resize(1180, 820)
        self.setMinimumSize(900, 680)
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background:{BG}; color:{TEXT}; }}
            QLabel {{ color:{TEXT}; }}
            QLineEdit, QTextEdit {{ background:{PANEL_2}; border:1px solid {BORDER}; border-radius:14px; color:{TEXT}; padding:12px; selection-background-color:#22556b; }}
            QPushButton {{ background:#0d2030; color:{TEXT}; border:1px solid #1e465c; border-radius:12px; padding:11px 16px; font-weight:600; }}
            QPushButton:hover {{ background:#123248; border-color:{ACCENT}; }}
            QPushButton:checked {{ background:#114e51; border-color:{ACCENT}; }}
            QScrollBar:vertical {{ background:transparent; width:10px; }}
            QScrollBar::handle:vertical {{ background:#173b50; border-radius:5px; }}
        """)

    def _make_icon(self) -> QIcon:
        from PySide6.QtGui import QPixmap
        pm = QPixmap(64, 64); pm.fill(QColor(BG))
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(ACCENT)); p.setPen(QPen(QColor("#dffffd"), 2)); p.drawEllipse(8, 8, 48, 48); p.end()
        return QIcon(pm)

    def _card(self) -> QWidget:
        card = QWidget(); card.setStyleSheet(f"background:{PANEL}; border:1px solid {BORDER}; border-radius:20px;"); return card

    def _build_ui(self) -> None:
        root = QWidget(); self.setCentralWidget(root); outer = QVBoxLayout(root); outer.setContentsMargins(24,20,24,20); outer.setSpacing(16)
        top = QHBoxLayout()
        brand = QLabel("J A R V I S"); brand.setFont(QFont("Segoe UI", 25, QFont.Bold)); brand.setStyleSheet(f"color:{TEXT};")
        sub = QLabel("PERSONAL AI • WINDOWS CONTROL"); sub.setStyleSheet(f"color:{ACCENT}; letter-spacing:2px;")
        top.addWidget(brand); top.addWidget(sub); top.addStretch(1)
        self.status_badge = QLabel("READY"); self.status_badge.setStyleSheet(f"background:#10372f;color:{ACCENT};padding:8px 12px;border-radius:10px;font-weight:700;")
        top.addWidget(self.status_badge)
        self.settings_btn = QPushButton("⚙"); self.settings_btn.setFixedWidth(46); top.addWidget(self.settings_btn)
        outer.addLayout(top)

        dash = QHBoxLayout(); dash.setSpacing(16)
        orb_card = self._card(); orb_layout = QVBoxLayout(orb_card); orb_layout.setContentsMargins(12,12,12,14)
        self.orb = Orb(); orb_layout.addWidget(self.orb);
        self.mic_label = QLabel("MIC OFF"); self.mic_label.setAlignment(Qt.AlignCenter); self.mic_label.setStyleSheet(f"color:{MUTED};font-weight:600;"); orb_layout.addWidget(self.mic_label)
        dash.addWidget(orb_card, 4)

        info = self._card(); info_l = QVBoxLayout(info); info_l.setContentsMargins(20,20,20,20)
        small=QLabel("CURRENT ACTIVITY"); small.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:2px;"); info_l.addWidget(small)
        self.activity=QLabel("Awaiting your instruction"); self.activity.setWordWrap(True); self.activity.setFont(QFont("Segoe UI", 18, QFont.DemiBold)); info_l.addWidget(self.activity)
        self.online=QLabel("● ONLINE AI   ● TOOLS READY   ● VOICE READY"); self.online.setStyleSheet(f"color:{ACCENT};margin-top:12px;"); info_l.addWidget(self.online)
        self.help=QLabel("Try: “Jarvis, Chrome kholo”, “screen pe kya hai?”, “type hello bhai”, or “search latest Android phones”."); self.help.setWordWrap(True); self.help.setStyleSheet(f"color:{MUTED};line-height:1.3;margin-top:10px;"); info_l.addWidget(self.help)
        info_l.addStretch(1)
        dash.addWidget(info, 6); outer.addLayout(dash)

        convo=self._card(); convo_l=QVBoxLayout(convo); convo_l.setContentsMargins(16,14,16,14)
        label=QLabel("LIVE CONVERSATION"); label.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:2px;"); convo_l.addWidget(label)
        self.chat=QTextEdit(); self.chat.setReadOnly(True); self.chat.setMinimumHeight(250); self.chat.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); convo_l.addWidget(self.chat); outer.addWidget(convo, 1)

        composer=self._card(); comp=QHBoxLayout(composer); comp.setContentsMargins(12,12,12,12); comp.setSpacing(8)
        self.input=QLineEdit(); self.input.setPlaceholderText("Type anything… or use the wake phrase ‘Jarvis’"); self.input.returnPressed.connect(self.submit); comp.addWidget(self.input,1)
        self.send=QPushButton("SEND"); self.send.clicked.connect(self.submit); comp.addWidget(self.send)
        self.talk=QPushButton("● TALK"); self.talk.setCheckable(True); self.talk.clicked.connect(self.toggle_talk); comp.addWidget(self.talk)
        self.type_btn=QPushButton("TYPE MODE"); self.type_btn.setCheckable(True); self.type_btn.clicked.connect(self.toggle_typing); comp.addWidget(self.type_btn)
        self.stop_btn=QPushButton("STOP"); self.stop_btn.clicked.connect(self.stop_all); comp.addWidget(self.stop_btn)
        outer.addWidget(composer)

    def _connect_signals(self) -> None:
        self.signals.started.connect(lambda text: self._set_state(AssistantState.THINKING, f"Understanding: {text}"))
        self.signals.voice_state.connect(self._voice_state_gui)
        self.signals.voice_error.connect(self._voice_error_gui)
        self.signals.tts_finished.connect(self._speech_done)
        self.signals.delta.connect(self._append_stream)
        self.signals.done.connect(self._finish_reply)
        self.signals.error.connect(lambda error: self._finish_text(f"I hit an error: {error}"))
        self.signals.voice_state.connect(self._voice_state_gui)
        self.signals.voice_error.connect(self._voice_error_gui)
        self.signals.tts_finished.connect(self._speech_done)
        self.settings_btn.clicked.connect(self.open_settings)

    def _set_state(self, state: AssistantState, activity: str) -> None:
        self.orb.set_state(state); self.status_badge.setText(state.value.upper()); self.activity.setText(activity)
        if state == AssistantState.LISTENING:
            self.mic_label.setText("● MIC ACTIVE • WAKE WORD ON")
            self.mic_label.setStyleSheet(f"color:{ACCENT};font-weight:700;")
        elif state == AssistantState.SPEAKING:
            self.mic_label.setText("◉ SPEAKING")
        else:
            self.mic_label.setText("MIC OFF" if not self.voice.enabled else "● MIC READY • say Jarvis")

    def _append_stream(self, chunk: str) -> None:
        if not hasattr(self, "_stream_started") or not self._stream_started:
            self._stream_started=True
            self.chat.append("<b style='color:#49efe1'>JARVIS</b>")
            self._stream_cursor = self.chat.textCursor(); self._stream_cursor.movePosition(self._stream_cursor.MoveOperation.End)
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)
        self.chat.insertPlainText(chunk)
        self.chat.ensureCursorVisible()
        self._set_state(AssistantState.SPEAKING, "Responding…")

    def _finish_reply(self, reply) -> None:
        if getattr(self, "_stream_started", False):
            self.chat.append("")
            self._stream_started=False
        else:
            self._append_message("JARVIS", reply.text)
        self._busy=False
        self._set_state(AssistantState.SPEAKING, reply.text)
        if self.settings.voice_enabled:
            self.tts.speak_async(reply.text, lambda: self.signals.tts_finished.emit())
        else:
            self._speech_done()

    def _finish_text(self, text: str) -> None:
        self._busy=False; self._append_message("JARVIS", text); self._set_state(AssistantState.IDLE,text)

    def _speech_done(self) -> None:
        self._busy=False
        if self.voice.enabled:
            self._set_state(AssistantState.LISTENING,"Haan, bolo. Main sun raha hoon…")
        else:
            self._set_state(AssistantState.IDLE,"Awaiting your instruction")

    def _append_message(self, role: str, text: str) -> None:
        color = ACCENT if role == "JARVIS" else ACCENT_2
        safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        self.chat.append(f"<div style='margin-top:8px;color:{color};font-weight:700'>{role}</div><div style='color:{TEXT};margin-bottom:8px'>{safe}</div>")

    def submit(self) -> None:
        text=self.input.text().strip()
        if not text: return
        self.input.clear(); self._append_message("YOU",text); self.process(text)

    def process(self, text: str) -> None:
        if text.lower() in {"stop","ruk","ruk ja","bas"}: self.stop_all(); return
        if self._busy: return
        self._busy=True; self._stream_started=False; self._set_state(AssistantState.THINKING,"Thinking…")
        self.pool.start(CommandWorker(self.assistant,text,self.signals))

    def start_voice(self) -> None:
        if self.voice.enabled: return
        self.voice.start_background(self._voice_command, self._voice_state, self._voice_error, self._wake_detected)
        self.talk.setChecked(True)
        self._set_state(AssistantState.LISTENING,"Haan, bolo. Main sun raha hoon…")

    def stop_voice(self) -> None:
        self.voice.stop_background(); self.talk.setChecked(False); self._set_state(AssistantState.IDLE,"Voice listening is off")

    def toggle_talk(self) -> None:
        if self.talk.isChecked(): self.start_voice()
        else: self.stop_voice()

    def _wake_detected(self) -> None:
        self.signals.voice_state.emit(True)
        self.voice.arm_session(18.0)
        self.tts.speak_async("Haan bhai, bolo. Main sun raha hoon.")
    def _voice_state(self, active: bool) -> None:
        self.signals.voice_state.emit(active)

    def _voice_state_gui(self, active: bool) -> None:
        self._set_state(AssistantState.LISTENING if active else AssistantState.IDLE, "Haan, bolo. Main sun raha hoon…" if active else "Voice listening is off")

    def _voice_command(self, text: str) -> None:
        def ui():
            self._append_message("YOU", text)
            if self.typing_mode:
                low=text.lower().strip()
                if low in {"typing band", "typing mode off", "stop typing"}:
                    self.toggle_typing(False); self._set_state(AssistantState.LISTENING,"Typing mode off"); return
                if low in {"new paragraph","new line","enter"}:
                    from jarvis.tools.automation import keyboard_press; keyboard_press("enter"); return
                from jarvis.tools.automation import keyboard_type; keyboard_type(text)
            else:
                self.process(text)
        QTimer.singleShot(0, ui)

    def _voice_error(self, error: str) -> None:
        self.signals.voice_error.emit(error)

    def _voice_error_gui(self, error: str) -> None:
        self.talk.setChecked(False)
        self._finish_text(f"Voice input is unavailable: {error}")

    def toggle_typing(self, checked: bool | None = None) -> None:
        active=self.type_btn.isChecked() if checked is None else checked; self.typing_mode=active; self.type_btn.setChecked(active)
        self._set_state(AssistantState.LISTENING if self.voice.enabled else AssistantState.IDLE, "Typing mode ON — voice will type into the focused app" if active else "Typing mode OFF")

    def stop_all(self) -> None:
        self.tts.stop(); self._busy=False; self._stream_started=False; self._set_state(AssistantState.IDLE,"Stopped")

    def open_settings(self) -> None:
        dlg=SettingsDialog(self.settings,self); dlg.exec()

    def closeEvent(self,event) -> None:
        if self.quitting:
            self.voice.stop_background(); self.tts.stop(); self.tray.hide(); event.accept(); return
        self.hide(); self.tray.show(); event.ignore()

    def quit_app(self) -> None:
        self.quitting=True; self.close()

    def setup_tray(self) -> None:
        self.tray.setToolTip("JARVIS — Personal AI Assistant")
        menu=self.tray.contextMenu()
        if menu is None:
            from PySide6.QtWidgets import QMenu
            menu=QMenu(self)
        menu.clear()
        open_action=QAction("Open JARVIS",self); open_action.triggered.connect(self.show_window)
        toggle=QAction("Toggle listening",self); toggle.triggered.connect(lambda: self.stop_voice() if self.voice.enabled else self.start_voice())
        exit_action=QAction("Exit",self); exit_action.triggered.connect(self.quit_app)
        menu.addAction(open_action); menu.addAction(toggle); menu.addSeparator(); menu.addAction(exit_action); self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None); self.tray.show()

    def show_window(self) -> None:
        self.show(); self.raise_(); self.activateWindow()

    def run(self) -> None:
        self.setup_tray(); self.show()