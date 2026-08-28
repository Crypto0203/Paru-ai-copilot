"""
PARU Hardware Microphone Listener.
Direct action intent execution + Wake-word detection.
"""

import os
import io
import time
import wave
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import config
from core.brain import brain
from core.tts import synthesize_speech

WAKE_WORDS = [
    "hey paru", "paru", "hi paru", "ok paru", "okay paru",
    "hey peru", "hey para", "hey pyro", "hey baru",
    "paro", "peru", "para", "pyro", "baru", "taru",
    "hey par", "paris", "hey"
]

DIRECT_INTENT_TRIGGERS = [
    "open youtube", "play youtube", "play music", "play song", "play songs",
    "open chrome", "open browser", "search google", "search",
    "open facebook", "open instagram", "open amazon", "open netflix",
    "open spotify", "open notepad", "open calculator", "open vs code",
    "take a screenshot", "take screenshot", "capture screen",
    "set volume", "mute volume", "lock pc", "lock workstation", "battery"
]

def find_working_input_device():
    """Finds the optimal working hardware input device on Windows (prioritizing WDM-KS Jabra/Realtek)."""
    devices = sd.query_devices()
    # First priority: WDM-KS Jabra
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

    # Second priority: any WDM-KS input
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


class NativeMicListener:
    """Hardware microphone listener with rolling buffer, dynamic noise gating, and follow-up window."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_running = False
        self.is_processing = False
        self.active_until = 0.0
        self.thread = None
        self.broadcast_callback = None
        self.dev_idx = None
        self.sample_rate = 44100

    def set_broadcast_callback(self, callback):
        self.broadcast_callback = callback

    def _play_audio(self, audio_file_path: str):
        try:
            data, fs = sf.read(audio_file_path, dtype='float32')
            sd.play(data, fs)
            sd.wait()
        except Exception:
            pass

    def start(self):
        if self.is_running:
            return
        self.dev_idx, self.sample_rate, dev_name = find_working_input_device()
        print(f"[PARU] 🎙️ Direct Hardware Mic Stream: {dev_name} ({self.sample_rate}Hz)", flush=True)
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False

    def _execute_query(self, user_text: str):
        self.is_processing = True
        print(f"[PARU] ⚡ Executing Voice Command: '{user_text}'", flush=True)
        result = brain.process_query(user_text)
        response_text = result.get("text", "")
        print(f"[PARU] 💬 Spoken Response: {response_text}", flush=True)

        if self.broadcast_callback:
            try:
                self.broadcast_callback({
                    "user": user_text,
                    "assistant": response_text,
                    "tool_called": result.get("tool_called")
                })
            except Exception:
                pass

        audio_path = synthesize_speech(response_text)
        if audio_path and os.path.exists(audio_path):
            self._play_audio(audio_path)

        self.is_processing = False

    def _listen_loop(self):
        chunk_duration = 3.5
        while self.is_running:
            if self.is_processing:
                time.sleep(0.3)
                continue

            try:
                audio_data = sd.rec(
                    int(self.sample_rate * chunk_duration),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='int16',
                    device=self.dev_idx
                )
                sd.wait()

                # Sensitive noise gate
                max_amp = np.max(np.abs(audio_data))
                if max_amp < 150:
                    continue

                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())

                wav_io.seek(0)
                with sr.AudioFile(wav_io) as source:
                    audio_sr = self.recognizer.record(source)

                transcript = self.recognizer.recognize_google(audio_sr, language="en-IN").lower().strip()
                if not transcript:
                    continue

                print(f"[Hardware Mic Captured]: '{transcript}'", flush=True)

                has_wake = any(w in transcript for w in WAKE_WORDS)
                has_intent = any(intent in transcript for intent in DIRECT_INTENT_TRIGGERS)
                in_conversation = time.time() < self.active_until

                if has_wake or has_intent or in_conversation:
                    self.active_until = time.time() + 10.0
                    clean_cmd = transcript
                    for w in sorted(WAKE_WORDS, key=len, reverse=True):
                        clean_cmd = clean_cmd.replace(w, "").strip()

                    if not clean_cmd or len(clean_cmd) < 2:
                        self._execute_query("Paru, wake up and say hello.")
                    else:
                        self._execute_query(clean_cmd)

            except sr.UnknownValueError:
                pass
            except Exception:
                time.sleep(0.3)

mic_listener = NativeMicListener()
