import sounddevice as sd
import numpy as np
import io, wave
import speech_recognition as sr

working_dev = 19
sr_rate = 44100

print(f"Testing 1.5-second record from Jabra WDM-KS (Device {working_dev})...")
audio_data = sd.rec(int(sr_rate * 1.5), samplerate=sr_rate, channels=1, dtype='int16', device=working_dev)
sd.wait()
max_amp = np.max(np.abs(audio_data))
print(f"Audio recorded successfully! Max Amplitude: {max_amp}")

wav_io = io.BytesIO()
with wave.open(wav_io, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr_rate)
    wf.writeframes(audio_data.tobytes())

wav_io.seek(0)
r = sr.Recognizer()
with sr.AudioFile(wav_io) as source:
    audio_sr = r.record(source)

print("Testing Google STT pipe...")
try:
    text = r.recognize_google(audio_sr)
    print(f"Recognized speech: '{text}'")
except sr.UnknownValueError:
    print("STT pipeline verified (ambient silence detected)!")
except Exception as e:
    print("STT Error:", e)
