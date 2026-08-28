import os
import io
import json
import asyncio
import speech_recognition as sr
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from core.brain import brain
from core.tts import generate_speech_async
from core.vision import analyze_screen_with_gemini
from core.memory import memory
from core.mic_listener import mic_listener
from tools.system_tools import get_system_status, get_wifi_info

app = FastAPI(title="PARU AI Desktop Assistant", version="1.0.0")

# Enable CORS for frontend interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start Telegram Remote Bridge on startup
@app.on_event("startup")
def startup_event():
    try:
        from core.telegram_bridge import telegram_bridge
        telegram_bridge.start()
    except Exception as e:
        print(f"[Telegram Bridge Notice] {e}")

# Static file mounts
UI_DIR = config.BASE_DIR / "ui"
app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")
app.mount("/audio", StaticFiles(directory=str(config.RECORDINGS_DIR)), name="audio")
app.mount("/screenshots", StaticFiles(directory=str(config.SCREENSHOTS_DIR)), name="screenshots")


class QueryRequest(BaseModel):
    query: str
    voice: str = config.DEFAULT_VOICE
    enable_tts: bool = True

class TTSRequest(BaseModel):
    text: str
    voice: str = config.DEFAULT_VOICE

class SettingsRequest(BaseModel):
    gemini_api_key: str = ""
    voice: str = ""
    user_name: str = ""
    telegram_bot_token: str = ""


import socket
import mss
from PIL import Image, ImageGrab, ImageDraw
from fastapi.responses import FileResponse, JSONResponse, Response

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@app.get("/")
async def get_index():
    """Serves the main HUD UI."""
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="HUD UI not found.")
    return FileResponse(str(index_file))


@app.get("/remote")
async def get_remote_page():
    """Serves the Mobile Remote Dashboard."""
    remote_file = UI_DIR / "remote.html"
    if not remote_file.exists():
        raise HTTPException(status_code=404, detail="Remote UI not found.")
    return FileResponse(str(remote_file))


@app.get("/api/screen_frame")
async def get_screen_frame():
    """Captures instant JPEG screenshot of current laptop screen for mobile streaming."""
    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            s_img = sct.grab(mon)
            img = Image.frombytes("RGB", s_img.size, s_img.bgra, "raw", "BGRX")
            img.thumbnail((1280, 720))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=65)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
    except Exception:
        try:
            from PIL import ImageDraw
            img = Image.new("RGB", (1280, 720), color=(10, 14, 23))
            draw = ImageDraw.Draw(img)
            draw.text((460, 330), "🛡️ PARU SECURE LIVE REMOTE", fill=(0, 242, 254))
            draw.text((430, 370), "Laptop Screen Connected • Ready for Remote Commands", fill=(140, 160, 190))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=65)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Returns current system and assistant status."""
    sys_status = get_system_status()
    facts = memory.get_all_facts()
    reminders = memory.get_active_reminders()
    local_ip = get_local_ip()
    return {
        "status": "online",
        "name": "PARU",
        "has_api_key": bool(config.GEMINI_API_KEY),
        "voice": config.DEFAULT_VOICE,
        "system": sys_status,
        "local_ip": local_ip,
        "remote_url": f"http://{local_ip}:8765/remote",
        "facts_count": len(facts),
        "reminders_count": len(reminders)
    }


@app.post("/api/chat")
async def handle_chat(req: QueryRequest):
    """Processes user voice/text query, runs tool execution, and generates TTS asynchronously."""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, brain.process_query, req.query)
        
        audio_url = None
        if req.enable_tts and result.get("text"):
            audio_file = await generate_speech_async(result["text"], voice=req.voice or config.DEFAULT_VOICE)
            if audio_file:
                audio_filename = Path(audio_file).name
                audio_url = f"/audio/{audio_filename}"

        return {
            "response": result.get("text", ""),
            "tool_called": result.get("tool_called"),
            "audio_url": audio_url,
            "status": result.get("status", "success")
        }
    except Exception as e:
        return {
            "response": f"Paru encountered an error: {str(e)}",
            "tool_called": None,
            "audio_url": None,
            "status": "error"
        }


@app.post("/api/voice_upload")
async def handle_voice_upload(file: UploadFile = File(...)):
    """Transcribes browser-recorded WAV audio directly with speech_recognition and executes command."""
    try:
        audio_bytes = await file.read()
        wav_io = io.BytesIO(audio_bytes)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        transcript = None
        for lang_code in ["en-IN", "te-IN", "hi-IN", "en-US"]:
            try:
                transcript = recognizer.recognize_google(audio_data, language=lang_code)
                if transcript:
                    break
            except Exception:
                pass

        if not transcript:
            return {
                "transcript": "",
                "response": "వినబడలేదు సురేష్ గారు, దయచేసి మళ్ళీ చెప్పండి. (I couldn't hear clearly, please speak again.)",
                "tool_called": None,
                "audio_url": None,
                "status": "unrecognized"
            }

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, brain.process_query, transcript)

        audio_url = None
        if result.get("text"):
            speech_path = await generate_speech_async(result["text"], voice=config.DEFAULT_VOICE)
            if speech_path:
                audio_url = f"/audio/{Path(speech_path).name}"

        return {
            "transcript": transcript,
            "response": result.get("text", ""),
            "tool_called": result.get("tool_called"),
            "audio_url": audio_url,
            "status": "success"
        }
    except Exception as e:
        return {
            "transcript": "",
            "response": f"Voice processing error: {str(e)}",
            "tool_called": None,
            "audio_url": None,
            "status": "error"
        }


@app.post("/api/tts")
async def handle_tts(req: TTSRequest):
    """Direct TTS generation endpoint."""
    try:
        audio_file = await generate_speech_async(req.text, voice=req.voice or config.DEFAULT_VOICE)
        if audio_file:
            audio_filename = Path(audio_file).name
            return {"audio_url": f"/audio/{audio_filename}", "status": "success"}
        return JSONResponse(status_code=500, content={"error": "Failed to synthesize speech."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/vision")
async def handle_vision(req: QueryRequest):
    """Direct Screen Vision trigger."""
    loop = asyncio.get_running_loop()
    analysis = await loop.run_in_executor(None, analyze_screen_with_gemini, req.query or "Describe what is on my screen right now.")
    
    audio_url = None
    if req.enable_tts and analysis:
        audio_file = await generate_speech_async(analysis, voice=req.voice or config.DEFAULT_VOICE)
        if audio_file:
            audio_filename = Path(audio_file).name
            audio_url = f"/audio/{audio_filename}"

    return {
        "response": analysis,
        "audio_url": audio_url,
        "status": "success"
    }


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    """Updates API key, voice, or user name in memory/config."""
    env_file = config.BASE_DIR / ".env"
    env_data = {}
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env_data[k] = v

    if req.gemini_api_key:
        brain.update_api_key(req.gemini_api_key)
        env_data["GEMINI_API_KEY"] = req.gemini_api_key

    if req.voice:
        config.DEFAULT_VOICE = req.voice
        env_data["DEFAULT_VOICE"] = req.voice
        memory._memory["preferences"]["voice"] = req.voice
        memory._save()

    if req.user_name:
        memory._memory["user_name"] = req.user_name
        memory._save()

    if req.telegram_bot_token:
        env_data["TELEGRAM_BOT_TOKEN"] = req.telegram_bot_token
        from core.telegram_bridge import telegram_bridge
        telegram_bridge.bot_token = req.telegram_bot_token
        telegram_bridge.start()

    with open(env_file, "w", encoding="utf-8") as f:
        for k, v in env_data.items():
            f.write(f"{k}={v}\n")

    return {"status": "success", "message": "Settings updated successfully for Paru."}


active_websockets = set()

@app.post("/api/broadcast_event")
async def broadcast_event_endpoint(req: dict):
    """Broadcasts a voice/action event from background listener to all connected HUD windows."""
    for ws in list(active_websockets):
        try:
            await ws.send_json({"type": "native_event", "data": req})
        except Exception:
            active_websockets.discard(ws)
    return {"status": "success"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional WebSocket connection for HUD."""
    await websocket.accept()
    active_websockets.add(websocket)
    loop = asyncio.get_running_loop()

    try:
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            action = data.get("action")

            if action == "query":
                query_text = data.get("query", "")
                await websocket.send_json({"type": "state", "state": "thinking"})
                
                result = await loop.run_in_executor(None, brain.process_query, query_text)
                
                tool_called = result.get("tool_called")
                if tool_called:
                    await websocket.send_json({"type": "tool_executed", "tools": tool_called})

                await websocket.send_json({"type": "state", "state": "speaking"})
                audio_file = await generate_speech_async(result.get("text", ""), voice=config.DEFAULT_VOICE)
                audio_url = f"/audio/{Path(audio_file).name}" if audio_file else None

                await websocket.send_json({
                    "type": "response",
                    "text": result.get("text", ""),
                    "audio_url": audio_url,
                    "tool_called": tool_called
                })
                await websocket.send_json({"type": "state", "state": "idle"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket Error] {e}")
