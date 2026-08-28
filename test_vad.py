import io
import time
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr

def record_full_sentence(dev_idx, sample_rate, silence_duration=1.0, max_duration=12.0):
    """
    Listens continuously and returns audio ONLY after the user has finished speaking.
    Does NOT cut off mid-sentence.
    """
    block_size = int(sample_rate * 0.2)  # 200ms chunks
    frames = []
    has_spoken = False
    silence_start = None
    t0 = time.time()
    
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='int16',
        device=dev_idx,
        blocksize=block_size
    )
    
    with stream:
        while time.time() - t0 < max_duration:
            chunk, _ = stream.read(block_size)
            max_amp = np.max(np.abs(chunk))
            
            # If sound detected (> 250 amp)
            if max_amp > 250:
                has_spoken = True
                silence_start = None
                frames.append(chunk)
            elif has_spoken:
                frames.append(chunk)
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= silence_duration:
                    # User stopped talking for 1 full second - sentence complete!
                    break
            else:
                # Keep last 0.5s of pre-speech buffer
                frames.append(chunk)
                if len(frames) > 3:
                    frames.pop(0)

    if not has_spoken or not frames:
        return None

    audio_bytes = b"".join(f.tobytes() for f in frames)
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    wav_io.seek(0)
    return wav_io

if __name__ == "__main__":
    from core.mic_listener import find_working_input_device
    idx, sr_rate, name = find_working_input_device()
    print(f"Testing dynamic VAD on {name} ({sr_rate}Hz)... Speak a long sentence and pause:")
    wav = record_full_sentence(idx, sr_rate)
    if wav:
        r = sr.Recognizer()
        with sr.AudioFile(wav) as src:
            aud = r.record(src)
        try:
            txt = r.recognize_google(aud, language="en-IN")
            print("Captured Complete Sentence:", txt)
        except Exception as e:
            print("STT:", e)
    else:
        print("No speech detected.")
