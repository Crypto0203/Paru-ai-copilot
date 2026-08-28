"""
PARU PRO - VantagePoint Desktop Terminal HUD
Interactive CLI application with Acoustic Echo Suppression, Direct Intent Routing, and Multi-Language (Telugu/Hindi/English) support.
"""

import os
import sys
import time
import io
import re
import wave
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from core.brain import brain
from core.tts import synthesize_speech
from tools.web_tools import play_youtube, search_web, open_website

WAKE_WORDS = [
    "hey paru", "paru", "hi paru", "ok paru", "okay paru",
    "hey peru", "hey para", "hey pyro", "hey baru",
    "paro", "peru", "para", "pyro", "baru", "taru",
    "hey par", "paris", "hey"
]

is_speaking = False

def find_working_input_device():
    devices = sd.query_devices()
    for idx, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = sd.query_hostapis(d['hostapi'])['name']
            if "wdm-ks" in api_name.lower() and "jabra" in d['name'].lower():
                try:
                    sr_rate = int(d['default_samplerate'])
                    rec = sd.rec(int(sr_rate * 0.1), samplerate=sr_rate, channels=1, dtype='int16', device=idx)
                    sd.wait()
                    return idx, sr_rate, d['name']
                except Exception:
                    pass

    for idx, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = sd.query_hostapis(d['hostapi'])['name']
            if "wdm-ks" in api_name.lower():
                try:
                    sr_rate = int(d['default_samplerate'])
                    rec = sd.rec(int(sr_rate * 0.1), samplerate=sr_rate, channels=1, dtype='int16', device=idx)
                    sd.wait()
                    return idx, sr_rate, d['name']
                except Exception:
                    pass

    default_dev = sd.query_devices(kind='input')
    return None, int(default_dev['default_samplerate']), default_dev['name']


def play_audio(path: str):
    global is_speaking
    if not path or not os.path.exists(path):
        return
    try:
        is_speaking = True
        data, fs = sf.read(path, dtype="float32")
        sd.play(data, fs)
        sd.wait()
    except Exception:
        pass
    finally:
        time.sleep(0.5)
        is_speaking = False


def speak_async(text: str):
    try:
        path = synthesize_speech(text)
        if path:
            play_audio(path)
    except Exception:
        pass


def is_direct_intent(transcript: str) -> bool:
    t = transcript.lower()
    patterns = [
        r"(?:open|opening|play|playing|start|launch|search|look up)",
        r"(?:youtube|song|songs|music|video|facebook|google|chrome|instagram|spotify|whatsapp|amazon|netflix)",
        r"(?:screenshot|volume|battery|mute|lock)",
        r"(?:telugu|hindi|language|convert|speak in)"
    ]
    return any(re.search(p, t) for p in patterns)


def process_command(cmd_text: str):
    print(f"\n[⚡ PARU PROCESSING]: '{cmd_text}'", flush=True)
    clean_cmd = cmd_text
    for w in sorted(WAKE_WORDS, key=len, reverse=True):
        clean_cmd = clean_cmd.replace(w, "").strip(" ,.!?")
    if not clean_cmd:
        clean_cmd = "Paru, wake up and say hello."

    result = brain.process_query(clean_cmd)
    response_text = result.get("text", "Done.")
    tools = result.get("tool_called")

    print(f"[🤖 PARU RESPONSE]: {response_text}", flush=True)
    if tools:
        for t in tools:
            r = t.get('result', '')
            msg = r.get('message', str(r)) if isinstance(r, dict) else str(r)
            print(f"  🔧 Action Executed: {t['name']} -> {msg}", flush=True)

    # Speak response in background thread
    threading.Thread(target=speak_async, args=(response_text,), daemon=True).start()


def voice_listener_worker(dev_idx, sample_rate):
    global is_speaking
    recognizer = sr.Recognizer()
    chunk_duration = 3.5
    active_until = 0.0

    while True:
        try:
            if is_speaking:
                time.sleep(0.3)
                continue

            audio_data = sd.rec(
                int(sample_rate * chunk_duration),
                samplerate=sample_rate,
                channels=1,
                dtype='int16',
                device=dev_idx
            )
            sd.wait()

            if is_speaking:
                continue

            if np.max(np.abs(audio_data)) < 150:
                continue

            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

            wav_io.seek(0)
            with sr.AudioFile(wav_io) as source:
                audio_sr = recognizer.record(source)

            transcript = recognizer.recognize_google(audio_sr, language="en-IN").lower().strip()
            if not transcript or is_speaking:
                continue

            print(f"\n[🎙️ Mic Captured]: '{transcript}'", flush=True)

            has_wake = any(w in transcript for w in WAKE_WORDS)
            has_intent = is_direct_intent(transcript)
            in_window = time.time() < active_until

            if has_wake or has_intent or in_window:
                active_until = time.time() + 10.0
                process_command(transcript)

        except sr.UnknownValueError:
            pass
        except Exception:
            time.sleep(0.3)


def main():
    os.system("color 0A")
    print("=" * 65)
    print("     🛡️  PARU PRO AI ASSISTANT - VANTAGEPOINT EDITION  🛡️")
    print("     Autonomous Desktop Agent • Voice • Autoplay • Telugu/English")
    print("=" * 65)

    dev_idx, sample_rate, dev_name = find_working_input_device()
    print(f"\n[STATUS] Connected to Microphone: {dev_name} ({sample_rate}Hz)")
    print("[STATUS] Hands-Free Voice Listener: ACTIVE")
    print("[STATUS] Multi-Language Engine: Telugu (తెలుగు) / Hindi (हिंदी) / English")
    print("[STATUS] Web Dashboard: http://127.0.0.1:8765")
    print("\n💡 You can SPEAK anytime (e.g. 'Play trending songs', 'Open Facebook', 'Speak in Telugu')")
    print("💡 Or TYPE any command below and press ENTER:\n")

    t = threading.Thread(target=voice_listener_worker, args=(dev_idx, sample_rate), daemon=True)
    t.start()

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Paru. Goodbye!")
                break
            process_command(user_input)
        except KeyboardInterrupt:
            print("\nParu stopped.")
            break


if __name__ == "__main__":
    main()
