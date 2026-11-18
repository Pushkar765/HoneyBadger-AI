import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MAX_VRAM_GB = float(os.getenv("MAX_VRAM_GB", "3.5"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY", "")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID", "")
SANER_API_KEY = os.getenv("SANER_API_KEY", "")
RECALL_API_KEY = os.getenv("RECALL_API_KEY", "")
HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://localhost:8123")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "")
OWNER_NAME = os.getenv("OWNER_NAME", "")

# Voice control
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
WAKE_WORD = os.getenv("WAKE_WORD", "wakeup daddy's home")
TTS_ENABLED = os.getenv("TTS_ENABLED", "false").lower() == "true"
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "")  # auto-detect if empty
