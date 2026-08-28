"""
PARU PRO - VantagePoint Native Desktop App Launcher.
Spawns background server, voice listener, opens native app window,
and stays alive in background.
"""

import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import time
import threading
import subprocess
import shutil
import uvicorn
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from server import app
import paru_voice

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    shutil.which("chrome"),
    shutil.which("msedge")
]

def get_browser_bin():
    for p in CHROME_PATHS:
        if p and os.path.exists(p):
            return p
    return None


def run_voice_listener():
    try:
        paru_voice.main()
    except Exception:
        pass


def open_ui_window():
    """Waits for server then opens native borderless HUD app window."""
    for _ in range(30):
        try:
            r = requests.get("http://127.0.0.1:8765/api/status", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.3)

    browser_bin = get_browser_bin()
    app_url = "http://127.0.0.1:8765"
    if browser_bin:
        subprocess.Popen([
            browser_bin,
            f"--app={app_url}",
            "--window-size=1200,780",
            "--unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8765",
            "--use-fake-ui-for-media-stream",
            "--enable-features=SpeechRecognition"
        ])
    else:
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(0, "open", app_url, None, None, 1)


def main():
    # 1. Start Voice Listener Thread
    voice_thread = threading.Thread(target=run_voice_listener, daemon=True)
    voice_thread.start()

    # 2. Start UI opener in background thread (waits until server is healthy)
    ui_thread = threading.Thread(target=open_ui_window, daemon=True)
    ui_thread.start()

    # 3. Run Uvicorn Server on main thread (keeps process alive indefinitely)
    srv_config = uvicorn.Config(app, host="0.0.0.0", port=8765, log_level="warning")
    server = uvicorn.Server(srv_config)
    server.run()


if __name__ == "__main__":
    main()
