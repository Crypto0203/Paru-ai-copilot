# 🌌 PARU AI — Autonomous Desktop Copilot & Holographic Neural Interface

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-r128-cyan.svg)](https://threejs.org/)

**PARU** (*Personal Autonomous Real-time Unit*) is an ultra-fast, intelligent AI desktop copilot with native Windows OS control, a 3D Holographic Cyberpunk Neural Orb, zero-latency intent routing, multimodal screen vision, and bidirectional Telegram mobile remote bridging.

---

## 🌟 Key Highlights & Superpowers

- 🌐 **3D Holographic Particle Sphere**: 1,200 interactive node constellation rendering dynamic audio reactive waveforms and state shifts (Standby, Listening, Processing, Speaking).
- 🎙️ **Hands-Free Acoustic Wake Word Engine**: Continuous biometric stream listening for *"Hey Paru"* with high-tech acoustic synth chimes.
- ⚡ **Zero-Latency Intent Engine (<5ms)**: Instant deterministic routing across 200+ actions (volume, YouTube playback, Outlook MAPI emails, 40+ app launchers, screen vision).
- 🧠 **Human-Like Emotional Intelligence**: Powered by Gemini LLM multi-model cascading with conversational memory, personality adaptation, and empathy.
- 📧 **Outlook & Workplace Integration**: Native Windows COM MAPI bridge to read, filter, and speak inbox emails directly aloud.
- 📱 **Telegram Mobile Remote**: Control your entire desktop PC remotely from your phone (take screenshots, launch apps, send commands from anywhere).
- 📌 **Floating Mini-HUD Mode**: Pop out a compact, always-on-top desktop widget while working across multiple apps.

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/your-username/paru-ai-copilot.git
cd paru-ai-copilot
py -3.11 -m pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_optional_telegram_bot_token
DEFAULT_VOICE=en-US-JennyNeural
```

### 3. Launch Dashboard (1-Click)
Double-click `START_PARU.bat` or run:
```bash
py -3.11 -m uvicorn server:app --host 0.0.0.0 --port 8765
```
Open **`http://127.0.0.1:8765/`** in your browser.

---

## 🎮 Voice Commands Showcase

| Voice Command | Action |
|:---|:---|
| *"Hey Paru, open Teams and Outlook"* | Launches both desktop applications simultaneously in the foreground. |
| *"Hey Paru, open Outlook and read the first email"* | Accesses classic Outlook MAPI inbox, extracts sender/subject, and reads it aloud. |
| *"Hey Paru, play trending songs on YouTube"* | Launches YouTube video in foreground without duplicated tabs. |
| *"Hey Paru, stop the music"* | Sends hardware media stop signal to halt background audio. |
| *"Hey Paru, what is my battery level?"* | Reads live battery percentage, charging state, CPU & RAM telemetry. |
| *"Hey Paru, show yourself"* | Brings the PARU Holographic Dashboard straight to the front of your screen. |

---

## 🛠️ Tech Stack & Architecture
- **Backend Core**: Python 3.11, FastAPI, Uvicorn, WebSockets
- **AI / LLMs**: Google Gemini 2.5 / 3.0, Edge-TTS Neural Audio
- **Frontend HUD**: Three.js, Vanilla CSS Glassmorphism, Web Speech API
- **OS Control**: Win32 API, PyCaw, ctypes, psutil, Windows COM MAPI

---

## 📄 License
MIT License. Built with passion for autonomous AI agents.
