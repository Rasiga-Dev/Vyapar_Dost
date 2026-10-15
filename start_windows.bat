@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 (echo Installation failed. Check Python and internet connection. & pause & exit /b 1)
py app.py
pause
