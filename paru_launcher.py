"""
PARU Desktop Application Main Entry Point.
Packaged into Paru.exe for 1-click execution.
"""

import os
import sys
import time
import threading
import subprocess
import shutil
import requests
import uvicorn

# Fix for windowed mode
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

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

def get_browser():
    for p in CHROME_PATHS:
        if p and os.path.exists(p):
            return p
    return None

def kill_old_ports(port=8765):
    try:
        cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def run_server():
    try:
        srv_config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="error")
        server = uvicorn.Server(srv_config)
        server.run()
    except Exception:
        pass

def run_voice():
    try:
        paru_voice.main()
    except Exception:
        pass

def main():
    # 1. Clear old port locks
    kill_old_ports(8765)
    time.sleep(0.5)

    # 2. Start Server
    s_thread = threading.Thread(target=run_server, daemon=True)
    s_thread.start()

    # 3. Start Voice Listener
    v_thread = threading.Thread(target=run_voice, daemon=True)
    v_thread.start()

    # 4. Wait for server to respond
    server_ready = False
    for _ in range(25):
        try:
            r = requests.get("http://127.0.0.1:8765/api/status", timeout=1)
            if r.status_code == 200:
                server_ready = True
                break
        except Exception:
            time.sleep(0.3)

    # 5. Open Paru Application Window
    browser = get_browser()
    app_url = "http://127.0.0.1:8765"
    if browser:
        proc = subprocess.Popen([
            browser,
            f"--app={app_url}",
            "--window-size=1200,780",
            "--unsafely-treat-insecure-origin-as-secure=http://127.0.0.1:8765",
            "--use-fake-ui-for-media-stream",
            "--enable-features=SpeechRecognition"
        ])
        proc.wait()
    else:
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(0, "open", app_url, None, None, 1)
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()
