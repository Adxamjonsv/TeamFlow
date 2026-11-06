@echo off
chcp 65001 > nul
title Telegram Vazifa Boti
cd /d "%~dp0"

echo ===================================================
echo   TELEGRAM VAZIFA BOTI — ISHGA TUSHIRISH
echo ===================================================

if exist venv\Scripts\python.exe (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

%PYTHON_EXEC% start.py

pause

