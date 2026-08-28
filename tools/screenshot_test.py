import pyaudio

p = pyaudio.PyAudio()
for api_type in [pyaudio.paDirectSound, pyaudio.paMME, pyaudio.paWASAPI]:
    try:
        api_info = p.get_host_api_info_by_type(api_type)
        api_name = api_info.get("name", "?")
        print(f"\nAPI: {api_name}")
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d.get("hostApi") == api_info.get("index") and d["maxInputChannels"] > 0:
                sr = int(d["defaultSampleRate"])
                name = d["name"]
                chunk = int(sr * 0.1)
                try:
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=sr,
                        input=True,
                        input_device_index=i,
                        frames_per_buffer=chunk
                    )
                    data = stream.read(chunk, exception_on_overflow=False)
                    stream.stop_stream()
                    stream.close()
                    print(f"  [{i}] {name} SR={sr} -> WORKS! ({len(data)} bytes)")
                except Exception as e:
                    print(f"  [{i}] {name} -> {str(e)[:70]}")
    except Exception as e:
        print(f"API type {api_type}: {e}")
p.terminate()
