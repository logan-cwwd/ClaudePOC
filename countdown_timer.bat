@echo off
:: Countdown Timer Launcher for Windows
:: Double-click to run, or pin this to your taskbar/start menu

:: Change to the script directory
cd /d "%~dp0"

:: Run the Python countdown timer (hidden console window)
pythonw countdown_timer.py

:: If pythonw is not found, try python
if errorlevel 1 (
    python countdown_timer.py
)
