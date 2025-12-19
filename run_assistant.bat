@echo off
echo Starting Voice Assistant...
cd /d "%~dp0"
call .venv\Scripts\activate
python modern_gui.py
pause
