@echo off
title GestureDrive AI — Camera-Controlled Car Racing
echo =======================================================
echo   GestureDrive AI: "Your Hands. Your Road. Your Race."
echo   College Tech Expo Edition
echo =======================================================
echo.

IF EXIST "venv\Scripts\python.exe" (
    echo Launching with virtual environment...
    venv\Scripts\python.exe main.py
) ELSE (
    echo Launching with system Python...
    python main.py
)

pause
