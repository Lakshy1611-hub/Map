# JARVIS — Phase 1 Windows Desktop Assistant

JARVIS is a **real Python Windows desktop application**, not a browser mock-up or a script-only prompt demo. `main.py` creates a native Tk window, manages its event loop, supports minimize-to-tray when the optional tray dependency is installed, and connects conversation decisions to concrete OS automation tools.

## Current architecture

| Area | Responsibility |
| --- | --- |
| `main.py` | Desktop application entry point. |
| `jarvis/config.py` | `.env` configuration for model, voice, privacy and debug behavior. |
| `jarvis/core/` | Conversation context, assistant state machine, plan execution and response models. |
| `jarvis/llm/` | Replaceable model provider. The model can select only names exposed by the tool registry. |
| `jarvis/tools/` | Concrete application, keyboard/mouse, screen, browser, file, terminal and system tools. |
| `jarvis/voice/` | Provider boundary for one-request speech recognition and TTS. |
| `jarvis/security/` | Confirmation rule for deletions and dangerous commands. |
| `jarvis/storage/` | SQLite preference store, intentionally separate from conversation history. |
| `jarvis/ui/` | Responsive native window, animated orb/waveform, microphone state and optional tray integration. |
| `jarvis/logging/` | Privacy-conscious structured event logging boundary. |
| `tests/` | Fast non-destructive core behavior tests. |

## Phase 1 features that work

- Native dark desktop UI with responsive transcript, animated AI core and waveform, and visible **READY / LISTENING / THINKING / EXECUTING / SPEAKING / PAUSED** status.
- Text conversation, contextual follow-up (`Chrome open kar` then `ab YouTube pe ja`), and common English/Hinglish local handling when no model key is configured.
- Optional OpenAI model integration for dynamic natural-language selection among registered explicit tools; no model output can execute directly.
- Windows application launching for Chrome, Notepad and VS Code; PyAutoGUI keyboard, mouse and screenshot controls; browser URL/search; file, terminal and system tools.
- One-request microphone input and TTS output behind replaceable provider modules. The microphone is only opened after **TALK** is pressed.
- System tray UI with Open, Pause and Exit actions when `pystray` and Pillow are installed. Closing the window minimizes it to the tray instead of exiting.
- Confirmation for deletion and known destructive command patterns.

## Windows setup

Use Python 3.11 or 3.12 (64-bit recommended) in **PowerShell**:

```powershell
cd path\to\Map
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python main.py
```

Set `JARVIS_OPENAI_API_KEY` in `.env` for AI-powered dynamic planning. Without it, the intentional local fallback handles the Phase 1 examples but is not a replacement for an LLM.

### Windows prerequisites

- **Chrome / VS Code:** install normally and ensure they are available through Windows App Paths or `PATH`.
- **Microphone:** permit desktop microphone access in Windows Privacy & security settings. `PyAudio` is installed on Windows by the requirements file; if a compiler-wheel mismatch occurs, install a PyAudio wheel matching your Python architecture first, then rerun the requirements command.
- **PyAutoGUI safety:** move the pointer to the top-left screen corner to trigger its failsafe during automation.

## Main workflow test

1. Run `python main.py`; a resizable 920×760 JARVIS window and tray icon should appear.
2. Send `bhai kya haal hai?`; verify a conversational reply in the transcript.
3. Send `Chrome open kar`; confirm Chrome launches and JARVIS reports success or a useful error.
4. Send `open Notepad`, focus the Notepad window, then send `type Hello bhai`; verify text is typed into the focused window.
5. Send `take a screenshot`; verify a timestamped PNG appears under `screenshots/`.
6. Click **TALK**, say `Jarvis, Chrome kholo`, and confirm the microphone status returns to off after the request.
7. Close the window; use the JARVIS tray icon to restore it, pause it, or exit.

## Remaining Phase 1 environment limitations

This repository can run and be validated on a Windows desktop. The current CI container is Linux, lacks a graphical `$DISPLAY`, Windows APIs, microphone hardware, and has a package-index proxy restriction; it therefore cannot launch or validate the native Windows window/automation end-to-end here. These are environment limitations, not deliberate mock implementations.

## Explicitly deferred to later phases

Continuous wake word/VAD, interruption cancellation of already-started work, dictation mode, Playwright sessions, vision-model screen analysis, multi-step browser/desktop planning, Windows startup registration, and persistent user-preference UI remain future work. `inspect_screen` safely captures a screenshot today but does not send images to an LLM yet.
