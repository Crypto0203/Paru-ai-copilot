@echo off
title PARU AI Desktop Copilot
cd /d "%~dp0"
echo ===================================================
echo           PARU AI - AUTONOMOUS COPILOT
echo ===================================================
echo [1/2] Launching Background Neural Core...
start /b py -3.11 -m uvicorn server:app --host 0.0.0.0 --port 8765
timeout /t 2 /nobreak >nul
echo [2/2] Launching Holographic Dashboard...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="http://127.0.0.1:8765/" --window-size=1280,820
exit
