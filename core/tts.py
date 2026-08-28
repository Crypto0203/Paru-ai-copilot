"""
PARU TTS - Multi-Language Neural Speech Engine.
Automatically detects script/language (Telugu, Hindi, Tamil, Kannada, English, etc.)
and speaks with matching ultra-realistic Microsoft Edge Neural voices.
"""

import asyncio
import os
import re
import time
import threading
from pathlib import Path
import config

LANGUAGE_VOICE_MAP = {
    "te": "te-IN-ShrutiNeural",       # Telugu
    "hi": "hi-IN-SwaraNeural",        # Hindi
    "ta": "ta-IN-PallaviNeural",      # Tamil
    "kn": "kn-IN-SapnaNeural",        # Kannada
    "ml": "ml-IN-SobhanaNeural",      # Malayalam
    "mr": "mr-IN-AarohiNeural",       # Marathi
    "bn": "bn-IN-TanishaaNeural",     # Bengali
    "gu": "gu-IN-DhwaniNeural",       # Gujarati
    "en": "en-IN-NeerjaNeural"        # Indian English
}

def detect_voice_for_text(text: str, default_voice: str = None) -> str:
    """Auto-detects language from text characters and maps to high quality neural voice."""
    if not text:
        return default_voice or config.DEFAULT_VOICE

    # Check for specific unicode ranges
    if re.search(r'[\u0C00-\u0C7F]', text):  # Telugu
        return "te-IN-ShrutiNeural"
    if re.search(r'[\u0900-\u097F]', text):  # Devanagari (Hindi/Marathi)
        return "hi-IN-SwaraNeural"
    if re.search(r'[\u0B80-\u0BFF]', text):  # Tamil
        return "ta-IN-PallaviNeural"
    if re.search(r'[\u0C80-\u0CFF]', text):  # Kannada
        return "kn-IN-SapnaNeural"
    if re.search(r'[\u0D00-\u0D7F]', text):  # Malayalam
        return "ml-IN-SobhanaNeural"
    if re.search(r'[\u0980-\u09FF]', text):  # Bengali
        return "bn-IN-TanishaaNeural"

    return default_voice or config.DEFAULT_VOICE


def _run_async_safe(coro):
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=15)
    except RuntimeError:
        return asyncio.run(coro)


async def _edge_tts_generate(text: str, voice: str, output_path: str) -> bool:
    try:
        import edge_tts
        clean_text = text.replace("*", "").replace("#", "").replace("`", "")
        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice,
            rate=config.SPEECH_RATE,
            pitch=config.SPEECH_PITCH
        )
        await communicate.save(output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"[Edge-TTS error] {e}")
        return False


def _pyttsx3_generate(text: str, output_path: str) -> bool:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"[pyttsx3 error] {e}")
        return False


def synthesize_speech(text: str, voice: str = None) -> str:
    """Main Multi-Language TTS Engine."""
    if not text or not text.strip():
        return ""

    matched_voice = detect_voice_for_text(text, voice)
    timestamp = int(time.time() * 1000)

    mp3_path = str(config.RECORDINGS_DIR / f"tts_{timestamp}.mp3")
    try:
        success = _run_async_safe(_edge_tts_generate(text, matched_voice, mp3_path))
        if success:
            return mp3_path
    except Exception as e:
        print(f"[TTS cloud unavailable] {e}")

    wav_path = str(config.RECORDINGS_DIR / f"tts_{timestamp}.wav")
    try:
        if _pyttsx3_generate(text, wav_path):
            return wav_path
    except Exception as e:
        print(f"[TTS offline failed] {e}")

    return ""


async def generate_speech_async(text: str, voice: str = None) -> str:
    if not text or not text.strip():
        return ""
    matched_voice = detect_voice_for_text(text, voice)
    timestamp = int(time.time() * 1000)
    mp3_path = str(config.RECORDINGS_DIR / f"tts_{timestamp}.mp3")

    success = await _edge_tts_generate(text, matched_voice, mp3_path)
    if success:
        return mp3_path

    loop = asyncio.get_running_loop()
    wav_path = str(config.RECORDINGS_DIR / f"tts_{timestamp}.wav")
    try:
        result = await loop.run_in_executor(None, _pyttsx3_generate, text, wav_path)
        if result:
            return wav_path
    except Exception as e:
        print(f"[Async TTS fallback error] {e}")

    return ""
