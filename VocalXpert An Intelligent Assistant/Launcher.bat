::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFChcQwWLPiuRDrQSqNjY08WJp2kPXfQ6RL/S2aCbMuUA1kT3Zp8+wntUjJlCBRhXHg==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSTk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJhZksaHGQ=
::ZQ05rAF9IBncCkqN+0xwdVsFAlTMbAs=
::ZQ05rAF9IAHYFVzEqQIGJxhVQDySOXmuZg==
::eg0/rx1wNQPfEVWB+kM9LVsJDDKNP2q2PqUZ+vyb
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQIRJlt9QhCHMGezAbAS/KjN4OOEpw08R/E2a5va1KDu
::dhA7uBVwLU+EWH+9xAJieEkFAVbSbj7a
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCqDJBHXoAsWEStrHlTQaFecP4Uj6u3v7tWxp18OXe0xRL/J1b6LI/RT3ErndJoVxn9IjIstAltxcAauYgM9rmtMoiSkJNSVoBvgRFy10EQzGmlMl2bCmGsabpNBlNcG3yy3+0jxi+Uxwmv2Tb0PG3fd96NrOcU47Q+mfAfNgrY1
::YB416Ek+ZW8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
REM ========================================
REM    VocalXpert AI Assistant Launcher
REM    Author: Shoaib Khan
REM ========================================

title VocalXpert AI Assistant

REM Change to script directory
cd /d "%~dp0"

echo.
echo ========================================
echo    VocalXpert AI Assistant
echo ========================================
echo.

REM Verify required files exist
if not exist "main.py" (
    echo [ERROR] main.py not found!
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

if not exist "modules\security.py" (
    echo [ERROR] modules\security.py not found!
    echo Please ensure the modules folder is intact.
    echo.
    pause
    exit /b 1
)

if not exist "Cascade\haarcascade_frontalface_default.xml" (
    echo [WARNING] Face detection model missing!
    echo Expected: Cascade\haarcascade_frontalface_default.xml
    echo Face recognition may not work properly.
    echo.
    timeout /t 3 >nul
)

REM Create required directories
if not exist "userData" mkdir userData
if not exist "userData\faceData" mkdir userData\faceData
if not exist "Downloads" mkdir Downloads
if not exist "Camera" mkdir Camera
if not exist "Files and Document" mkdir "Files and Document"

REM Check for critical Python modules
echo [INFO] Checking for required Python modules...
python -c "import cv2, numpy, PIL, psutil" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some Python modules are missing!
    echo [INFO] Installing required dependencies...
    echo.
    
    REM Upgrade pip first
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [ERROR] Failed to upgrade pip. Continuing anyway...
    )
    
    REM Install requirements
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install some dependencies!
        echo Please run: pip install -r requirements.txt
        echo Or install manually as listed in README.md
        echo.
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Dependencies installed successfully!
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating default...
    echo MAIL_USERNAME="your_email@gmail.com"> .env
    echo MAIL_PASSWORD="your_app_password">> .env
    echo [INFO] Please edit .env file with your email credentials.
    echo.
)

echo [INFO] Starting VocalXpert AI Assistant...
echo ========================================
echo.

REM Run the application
python main.py

REM Capture exit code
set EXITCODE=%ERRORLEVEL%

echo.
echo ========================================
if %EXITCODE% EQU 0 (
    echo [INFO] Application closed normally.
) else (
    echo [ERROR] Application exited with code: %EXITCODE%
    echo.
    echo Common Issues:
    echo  - Missing dependencies: pip install -r requirements.txt
    echo  - Camera not accessible: Check Windows privacy settings
    echo  - Microphone permissions: Enable in Windows settings
    echo  - Import errors: Verify all modules are installed
    echo.
)
echo ========================================
echo.
pause
