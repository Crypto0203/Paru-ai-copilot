@echo off
title PARU PRO AI - VantagePoint
color 0A
cls

echo.
echo  ==============================================================
echo     PARU PRO AI ASSISTANT - VANTAGEPOINT EDITION
echo     Multi-Language (Telugu / Hindi / English) - Gemini 3.6 Flash
echo  ==============================================================
echo.

cd /d "%~dp0"

echo  [*] Checking system port status...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8765') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo  [1/2] Starting Background Server and Telegram Bot...
start "PARU Server" /B py -3.11 -m uvicorn server:app --host 0.0.0.0 --port 8765

timeout /t 2 /nobreak >nul

echo  [2/2] Launching Interactive Terminal HUD...
echo.

py -3.11 paru_terminal.py

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8765') do (
    taskkill /F /PID %%a >nul 2>&1
)
