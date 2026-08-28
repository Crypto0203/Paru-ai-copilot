import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "audio"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# API Keys & Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Default AI Settings
DEFAULT_MODEL = "gemini-3.6-flash"  # High-quota ultra-fast model
MODEL_CASCADE = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash"
]
FALLBACK_MODEL = "gemini-flash-latest"

# Voice & Speech Settings
# Edge TTS Voices:
# en-US-JennyNeural (Female, natural warm)
# en-US-GuyNeural (Male, dynamic friendly)
# en-US-AriaNeural (Female, authoritative clear)
# en-GB-SoniaNeural (British female, JARVIS-like)
# en-GB-RyanNeural (British male, classic butler/JARVIS)
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "en-US-JennyNeural")
SPEECH_RATE = "+0%"
SPEECH_PITCH = "+0Hz"

# Server Settings
HOST = "0.0.0.0"
PORT = 8765
DEBUG = True
