import sys
import os
import time
import threading
from pathlib import Path
import uvicorn

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config

def start_server():
    """Starts FastAPI uvicorn server."""
    uvicorn.run(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="warning"
    )

def main():
    print("=" * 65)
    print("  🚀 PARU PRO - CONFIDENTIAL AUTONOMOUS DESKTOP COPILOT")
    print("=" * 65)
    print(f" • Server Endpoint: http://{config.HOST}:{config.PORT}")
    print(f" • Mode: Native Desktop App + Secret Voice Wake Word")
    print("=" * 65)

    # 1. Start Server in Background Daemon Thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.2)

    # 2. Try launching Native Desktop Window via pywebview
    try:
        import webview
        print("[PARU] Launching Native Desktop Window...")
        window = webview.create_window(
            title="PARU PRO | Autonomous Desktop Copilot",
            url=f"http://{config.HOST}:{config.PORT}",
            width=1280,
            height=850,
            min_size=(900, 600),
            background_color="#080b11"
        )
        webview.start()
    except Exception as e:
        print(f"[PARU Notice] Opening default browser window ({e})...")
        import webbrowser
        webbrowser.open(f"http://{config.HOST}:{config.PORT}")
        # Keep process alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[PARU] Shutting down.")

if __name__ == "__main__":
    main()
