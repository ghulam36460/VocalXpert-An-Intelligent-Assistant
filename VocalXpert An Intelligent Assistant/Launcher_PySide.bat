@echo off
title VocalXpert - AI Voice Assistant
echo.
echo ========================================
echo     VocalXpert - AI Voice Assistant
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11 or later from python.org
    pause
    exit /b 1
)

REM Check for --skip-login argument
if "%1"=="--skip-login" (
    echo Starting in DEMO mode (no login)...
    python main_pyside.py --skip-login
) else if "%1"=="--old" (
    echo Starting OLD Tkinter interface...
    python main.py
) else (
    echo Starting with Face Recognition Login...
    echo.
    echo [TIP] Use "Launcher_PySide.bat --skip-login" to skip login
    echo [TIP] Use "Launcher_PySide.bat --old" for the old Tkinter UI
    echo.
    python main_pyside.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    echo Check vocalxpert.log for details.
    pause
)
