# JARVIS — Personal Windows AI Assistant

JARVIS is a native Windows desktop assistant designed for natural Hindi, English, and Hinglish interaction. The product combines a fast local command router, an online Gemini/OpenAI-compatible AI provider, optional local/offline AI, Windows automation, screen vision, multilingual speech, a futuristic Qt UI, and a system tray.

## What it can do

This branch is the candidate final desktop build; Windows CI is the release gate.
- Talk naturally in Hindi, English, and Hinglish.
- Type commands or use the microphone.
- Wake on **Jarvis** when background listening is enabled.
- Continue a short hands-free conversation without repeating the wake word after activation.
- Open and close applications such as Chrome, Edge, Notepad, Calculator, File Explorer, PowerShell, Windows Terminal, VS Code, and other resolvable Windows apps.
- Use keyboard and mouse controls, including Unicode-safe typing for Hindi/Hinglish.
- Open URLs, search the web, refresh, go back, switch windows, and scroll.
- Capture the screen and ask Gemini what is visible.
- Ask Gemini to locate and click a described screen element; sensitive targets require confirmation.
- Run PowerShell/terminal commands, with destructive patterns requiring confirmation.
- Execute bounded multi-step desktop tasks when the model can plan them.
- Speak responses with neural Indian-English/Hindi voices through Edge TTS, with local pyttsx3 fallback.
- Run a local/offline response provider through Ollama when it is installed and a model is available.
- Stay in the Windows system tray and restore from the tray.
- Use a premium animated PySide6 interface with status/orb/waveform states.
- Build to a single JARVIS.exe using the included PyInstaller configuration.

## Architecture
| Area | Responsibility |
| --- | --- |
| `main.py` | Qt application entrypoint. |
| `jarvis/config.py` | Environment-backed settings and frozen-EXE paths. |
| `jarvis/core/` | Conversation state, fallback routing, bounded agent execution. |
| `jarvis/llm/` | Online Gemini/OpenAI-compatible chat, streaming, and tool planning. |
| `jarvis/offline.py` | Optional local Ollama response provider and deterministic offline fallback. |
| `jarvis/tools/` | Windows apps, keyboard/mouse, browser, files, screen, terminal, system and window controls. |
| `jarvis/voice/` | Speech recognition and multilingual TTS. |
| `jarvis/ui/` | PySide6 UI, animated core, chat, settings and system tray. |
| `jarvis/security/` | Confirmation policy for destructive/sensitive actions. |
| `jarvis/storage/` | SQLite preference storage foundation. |
| `tests/` | Deterministic unit tests that do not consume remote model quota. |
| `jarvis.spec` | One-file PyInstaller build definition. |
| `build.ps1` | Reproducible Windows build script. |
| `.github/workflows/windows-build.yml` | Windows CI test plus EXE artifact build. |

## Windows setup
Use Python 3.11 or 3.12 (64-bit recommended) and PowerShell.

```powershell
cd C:\Projects\JARVIS
git clone -b codex/jarvis-final-product --single-branch https://github.com/Lakshy1611-hub/Map.git Map-codex-build-jarvis-ai-assistant-for-windows
cd Map-codex-build-jarvis-ai-assistant-for-windows
..\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python main.py
```

Put your Gemini key in `.env` as `JARVIS_OPENAI_API_KEY`. For Gemini's OpenAI-compatible endpoint use:

```text
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

The API key is never committed to Git because `.env` is ignored.

## Fast response behavior
Normal conversation uses a streaming model request, so text can appear as soon as the provider returns the first chunks instead of waiting for the entire answer. Common PC actions are handled by the local command router first, reducing unnecessary model calls.

Streaming improves time-to-first-visible-text; it does not make the network itself instantaneous. Online Gemini responses remain subject to network latency and quota.

## Voice
Default configuration:

```text
JARVIS_STT_PROVIDER=speech_recognition
JARVIS_STT_LANGUAGE=en-IN
JARVIS_TTS_PROVIDER=edge_tts
JARVIS_TTS_LANGUAGE_AUTO=true
JARVIS_TTS_ENGLISH_VOICE=en-IN-NeerjaNeural
JARVIS_TTS_HINDI_VOICE=hi-IN-SwaraNeural
JARVIS_WAKE_PHRASE=jarvis
JARVIS_VOICE_ENABLED=true
JARVIS_ALWAYS_LISTENING=true
```

The listening mode can be toggled from **TALK** or the tray. After a recognized wake-word command, JARVIS keeps a short 18-second wake-free conversation session before requiring the wake word again.

Speech recognition currently uses the Windows microphone plus the configured recognition service. Offline voice recognition is not included yet; offline text responses can use Ollama/local fallback.

## Screen understanding
`inspect_screen` captures the desktop and sends the image to the configured Gemini vision model. `visual_click` asks the vision model for coordinates and only clicks when confidence passes a safety threshold. Sensitive click targets require confirmation.

## Offline mode
When the internet is unavailable, JARVIS first uses its deterministic local router for PC actions and then tries an installed local Ollama model for conversational answers.

```text
JARVIS_OFFLINE_PROVIDER=ollama
JARVIS_OFFLINE_MODEL=gemma4:4b
JARVIS_OLLAMA_URL=http://127.0.0.1:11434
```

A local model can answer from its installed knowledge, but it cannot provide fresh internet data while offline.

## Building the EXE
On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\build.ps1
```

The result is:

```text
dist\JARVIS.exe
```

The EXE is windowed with no console. `.env` remains external local configuration; never embed API keys in the executable.

GitHub Actions also builds the executable on a Windows runner and uploads `dist/JARVIS.exe` as an artifact after tests pass.

## Safety model
JARVIS can control the PC, so destructive operations are not silently approved. File deletion, sensitive visual clicks, and recognized destructive terminal/system patterns require confirmation. The assistant should report failures rather than claiming an action succeeded.

## Updating the local clone
The final-product branch is `codex/jarvis-final-product`.

```powershell
git fetch origin
git switch codex/jarvis-final-product
git pull --ff-only
python -m pip install -r requirements.txt
python main.py
```

Your `.env` stays local because Git ignores it.

## Current boundaries
- Online Gemini responses remain subject to provider latency and quota.
- Offline voice recognition is not included yet.
- JARVIS does not silently rewrite or self-modify its own source code.
- Automatic software updates should be explicit, signed/versioned updates rather than unrestricted self-modification.
- Some third-party Windows applications may require custom aliases or UI-specific workflows.