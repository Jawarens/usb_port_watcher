@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    echo Virtual environment not found. Running with default python...
    start "" pythonw main.py
)
