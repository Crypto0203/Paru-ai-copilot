"""
PARU Dedicated Hardware Voice Listener.
Continuous background listener with dynamic ambient noise calibration,
Wake-Word parsing ('Hey Paru', 'Paru'), and live WebSocket/REST broadcast to HUD.
"""

import os
import sys
import time
import re
import threading
import requests
import speech_recognition as sr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from core.brain import brain
from core.tts import synthesize_speech

WAKE_WORDS = [
    "hey paru", "hi paru", "ok paru", "okay paru", "hello paru",
    "hey peru", "hey pyro", "hey pard", "hey par",
    "paru", "paro", "peru", "pyro", "baru", "taru"
]

is_speaking = False

def speak_response(text: str):
    global is_speaking
    try:
        is_speaking = True
        path = synthesize_speech(text)
        if path and os.path.exists(path):
            try:
                import sounddevice as sd
                import soundfile as sf
                data, fs = sf.read(path, dtype="float32")
                sd.play(data, fs)
                sd.wait()
            except Exception:
                pass
    except Exception as e:
        print(f"[TTS Error] {e}")
    finally:
        time.sleep(0.4)
        is_speaking = False


def extract_command(raw_text: str) -> str:
    clean = raw_text.strip()
    lower = clean.lower()
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        if lower.startswith(w):
            clean = clean[len(w):].strip(" ,.!?")
            break
        elif w in lower:
            clean = re.sub(re.escape(w), "", clean, flags=re.IGNORECASE).strip(" ,.!?")
            break
    return clean if len(clean) > 1 else "wake_up_greeting"


def process_phrase(transcript: str):
    print(f"\n[Heard Phrase] '{transcript}'")
    lower = transcript.lower().strip()
    
    has_wake = any(w in lower for w in WAKE_WORDS)
    has_direct_command = bool(re.search(
        r"(?:open|play|song|music|youtube|volume|voice|sound|mute|lock|wifi|battery|brightness|shutdown|restart|outlook|spotify|downloads|documents|screenshot|search|google|status)",
        lower
    ))

    if not (has_wake or has_direct_command):
        return

    cmd = extract_command(transcript)
    if cmd == "wake_up_greeting":
        reply = "Yes Suresh, I am listening! How can I assist you?"
        tool_called = None
    else:
        result = brain.process_query(cmd)
        reply = result.get("text", "Done.")
        tool_called = result.get("tool_called")

    print(f"[PARU Responding] '{reply}'")

    # Broadcast to Web HUD
    try:
        requests.post("http://127.0.0.1:8765/api/broadcast_event", json={
            "user": transcript,
            "assistant": reply,
            "tool_called": tool_called
        }, timeout=1)
    except Exception:
        pass

    # Speak response in background
    threading.Thread(target=speak_response, args=(reply,), daemon=True).start()


def main():
    print("=" * 60)
    print("  PARU HARDWARE VOICE LISTENER — STANDBY")
    print("  Listening for 'Hey Paru' or direct desktop commands...")
    print("=" * 60)

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.5

    with sr.Microphone() as source:
        print("[Calibrating] Adjusting for ambient noise (1 second)...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print(f"[Calibrated] Energy threshold set to {recognizer.energy_threshold:.1f}")

    while True:
        if is_speaking:
            time.sleep(0.3)
            continue
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10.0)
                
            if is_speaking:
                continue

            try:
                # Fast Google STT with multi-language fallback
                text = None
                for lang in ["en-IN", "en-US", "te-IN", "hi-IN"]:
                    try:
                        text = recognizer.recognize_google(audio, language=lang)
                        if text:
                            break
                    except Exception:
                        pass
                
                if text and not is_speaking:
                    process_phrase(text)

            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[STT Request Error] {e}")

        except Exception as e:
            time.sleep(0.3)


if __name__ == "__main__":
    main()
