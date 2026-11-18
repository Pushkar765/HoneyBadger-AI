# HoneyBadger Run Guide

A step-by-step guide to set up and run the HoneyBadger assistant application.

> **Last updated:** June 1, 2026 — Verified working on Python 3.14 + Windows 11

---

## Prerequisites

- Python 3.14 (the only version currently installed)
- NVIDIA GPU with CUDA support (RTX 3050 4GB VRAM)
- Ollama installed — download from https://ollama.ai
- Models pulled: `phi4-mini` and `gemma3:4b`

---

## First-Time Setup (already done — skip if returning)

> These steps were completed during initial setup. You do **not** need to repeat them.

### 1. Create Virtual Environment

```powershell
python -m venv .venv
```

### 2. Install Dependencies

> ⚠️ Do NOT use `pip install -r requirements.txt` directly — some packages in
> `requirements.txt` are incompatible with Python 3.14. Install with this command instead:

```powershell
.\.venv\Scripts\pip install setuptools anthropic openai requests chromadb pyttsx3 sounddevice scipy duckduckgo-search Pillow flask python-dotenv pyautogui numpy beautifulsoup4 black scapy pandas schedule matplotlib cryptography paramiko openpyxl pyserial homeassistant-api PySide6 rich textblob wikipedia-api opencv-python vadersentiment transformers pynvml psutil "urllib3<2"
```

Then install the project itself:

```powershell
.\.venv\Scripts\pip install -e . --no-deps
```

### 3. Pull Ollama Models

```powershell
ollama pull phi4-mini
ollama pull gemma3:4b
```

Verify:
```powershell
ollama list
```

### 4. Configure `.env`

The `.env` file in the project root is already configured for local-only mode:

```env
OLLAMA_URL=http://localhost:11434
MAX_VRAM_GB=3.5
OWNER_NAME=your_name
```

No API keys are needed when using Ollama locally. Leave the `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY` fields as placeholders — they are only used as fallback if
Ollama is unavailable.

---

## Running the Application

### Easiest: Double-click the launcher

Double-click **`honeybadger.bat`** in the project root.

It will:
1. Start Ollama automatically (if not already running)
2. Wait 5 seconds for Ollama to be ready
3. Launch the HoneyBadger GUI

### Manual: Run from terminal

Make sure you are in the project root (`c:\PJ Things\HoneyBadger`), then:

```powershell
.\.venv\Scripts\python src\honeybadger\main.py
```

The GUI will open. Type a message and press **Send** to test.

---

## Voice Control

HoneyBadger supports **hands-free voice input** — speak commands instead of
typing. It uses **Vosk** for fully offline speech recognition (no internet
required after first setup).

### 1. Install Vosk (one-time)

```powershell
.\.venv\Scripts\pip install vosk
```

> This is already done if you followed the latest setup. Vosk is ~14 MB.

### 2. First Run — Model Download

On the **first launch** with voice enabled, HoneyBadger automatically downloads
the small English model (~40 MB) from the internet and saves it to
`configs\vosk-model\`. After this, voice works **100% offline**.

If you prefer to download manually:

```powershell
# Download and extract into configs\vosk-model\
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile vosk-model.zip
Expand-Archive vosk-model.zip -DestinationPath configs\_tmp
Move-Item configs\_tmp\vosk-model-small-en-us-0.15 configs\vosk-model
Remove-Item vosk-model.zip, configs\_tmp -Recurse
```

### 3. Voice Modes

Open the app and look at the **Voice Control** panel in the left sidebar.
There are three modes:

| Mode | How it works |
|---|---|
| **Off** (default) | Voice is disabled. Type commands as usual. |
| **Push-to-Talk** | Click the 🎤 mic button to start listening. Speak your command. It auto-sends when you finish speaking. Click again to stop early. |
| **Always-On (Wake Word)** | HoneyBadger listens continuously for the wake phrase **"Hey Badger"**. Once heard, it captures your command and sends it. No button press needed. |

**Visual feedback:**
- The 🎤 mic button **pulses red** when actively listening.
- Partial transcription appears **live** in the input box as you speak.
- The sidebar shows the current status: `Listening…`, `Waiting for "Hey Badger"…`, or `Idle`.

### 4. Text-to-Speech (TTS)

Enable **"Speak responses aloud"** in the Voice Control panel to have
HoneyBadger read its replies out loud using your system's text-to-speech
engine (via `pyttsx3`).

TTS is **off by default**. You can also set it to on by default in `.env`:

```env
TTS_ENABLED=true
```

### 5. Configuration (`.env`)

All voice settings are configurable in the `.env` file:

```env
# Voice control
VOICE_ENABLED=true          # Enable/disable voice features entirely
WAKE_WORD=hey badger        # Custom wake phrase for always-on mode
TTS_ENABLED=false           # Speak responses aloud by default
VOSK_MODEL_PATH=            # Leave empty for auto-detect (configs\vosk-model)
```

### 6. Voice Troubleshooting

**No microphone detected:**
- The mic button will be greyed out. Connect a microphone and restart the app.
- On Windows, check **Settings → System → Sound → Input** to verify your mic
  is recognized.

**Vosk model not downloading:**
- Check your internet connection (only needed the first time).
- Manually download the model (see step 2 above).
- Set `VOSK_MODEL_PATH` in `.env` to point to your extracted model folder.

**Voice is not recognizing my speech:**
- Speak clearly and at normal volume. Vosk works best at ~30 cm from the mic.
- The small model is optimized for English. Accents may reduce accuracy.
- For better accuracy, replace the model with a larger one from
  https://alphacephei.com/vosk/models (extract into `configs\vosk-model\`).

**Wake word keeps false-triggering:**
- Change `WAKE_WORD` in `.env` to a more unique phrase
  (e.g., `WAKE_WORD=activate honeybadger`).

---

## Expected Warnings (harmless — ignore these)

When the app starts you will see two warnings in the terminal. Both are harmless:

```
FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead.
```
→ `pynvml` still works fine. This is just a rename notice.

```
DeprecationWarning: 'exec_' will be removed in the future. Use 'exec' instead.
```
→ A minor PySide6 API change. Does not affect functionality.

---

## Troubleshooting

### Ollama is not running

**Symptom:** App shows "Ollama server is unavailable" or hangs on startup.

**Fix:** Open a separate terminal and run:
```powershell
ollama serve
```
Wait ~5 seconds, then launch the app again.

### Port 11434 already in use

**Cause:** Ollama is already running from a previous session — this is fine, just launch the app.

If you actually need to restart Ollama:
```powershell
tasklist /fi "imagename eq ollama.exe"    # Find process ID
taskkill /PID <PID> /F                    # Kill it
ollama serve                              # Start fresh
```

### Model not found (404 error)

**Cause:** Required model is not pulled.

**Fix:**
```powershell
ollama pull phi4-mini
ollama pull gemma3:4b
ollama list    # Confirm they appear
```

### VRAM warnings

If you see `VRAM usage is above 90%` in the terminal, the app will automatically
unload the current model from VRAM to free memory. This is normal on a 4GB GPU.

You can adjust the threshold in `.env`:
```env
MAX_VRAM_GB=3.5
```

### `ModuleNotFoundError: No module named 'honeybadger'`

The package is not installed in editable mode. Fix:
```powershell
.\.venv\Scripts\pip install -e . --no-deps
```

### `urllib3` import error / `No module named 'urllib3.contrib.anytls'`

A newer incompatible version of `urllib3` was installed. Fix:
```powershell
.\.venv\Scripts\pip install "urllib3<2" --force-reinstall
```

---

## Known Incompatible Packages (Python 3.14)

The following packages from `requirements.txt` do **not** support Python 3.14
and are intentionally not installed. They are not used by the core application.

| Package | Reason not installed |
|---|---|
| `python-nmap` | Broken build on Python 3.14 |
| `openai-whisper` | Requires `pkg_resources` (removed in Python 3.14) |
| `deepface` | Requires `tensorflow` (no Python 3.14 wheel) |
| `mediapipe` | Requires `tensorflow` (no Python 3.14 wheel) |
| `fer` | Not used in source code |
| `librosa` | Not used in source code |
| `opensmile` | Not used in source code |

> **Vision features** (`capture_analyze`) will return a graceful fallback message
> instead of crashing when `deepface`/`mediapipe` are unavailable.

---

## Model Routing

HoneyBadger automatically selects the right model based on the request type:

| Task Type | Model |
|---|---|
| General / Emotion / Fast | `phi4-mini` (2.5 GB) |
| Reasoning / Coding / Security | `gemma3:4b` (3.3 GB) |

The active model is shown in the UI under **Hardware Monitor → Current Model**.

---

## Common Commands

```powershell
# Activate venv manually (if needed)
.\.venv\Scripts\Activate.ps1

# Check installed models
ollama list

# Check Ollama is responding
curl http://localhost:11434/v1/models

# Check VRAM and running models
ollama ps

# Run tests
pytest tests/
```

---

## File Structure

```
HoneyBadger/
├── src/honeybadger/
│   ├── main.py                  # Entry point (GUI)
│   ├── config.py                # Configuration loader
│   ├── brain/
│   │   ├── ollama_brain.py      # Ollama API client + VRAM management
│   │   └── brain_router.py      # Model routing logic
│   ├── ui/
│   │   └── ui.py                # PySide6 GUI
│   ├── vision/
│   │   └── vision.py            # Camera + face emotion (optional)
│   ├── voice/
│   │   ├── voice.py             # Vosk speech-to-text listener
│   │   └── tts.py               # pyttsx3 text-to-speech wrapper
│   ├── emotion/
│   │   └── feelings.py          # Sentiment analysis (vaderSentiment)
│   ├── memory/
│   │   └── chromadb_memory.py   # Persistent memory (ChromaDB)
│   └── ... (other modules)
├── .env                         # Environment variables (local settings)
├── requirements.txt             # Full dependency list (some skip on Python 3.14)
├── honeybadger.bat              # One-click launcher (Windows)
└── RUNGUIDE.md                  # This file
```
