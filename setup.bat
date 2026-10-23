@echo off
setlocal
cd /d "%~dp0"
title SubTrack setup

echo.
echo ============================================
echo   SubTrack - one-time setup
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.10 or newer from python.org and tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist venv (
    echo [1/3] Creating the virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment already exists.
)

echo [2/3] Installing packages (this can take a few minutes)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package installation failed. Check your internet connection and run setup.bat again.
    pause
    exit /b 1
)

if not exist .env (
    echo [3/3] Creating the .env settings file...
    copy .env.example .env >nul
) else (
    echo [3/3] .env already exists, keeping it.
)

echo.
echo ============================================
echo   Setup finished.
echo ============================================
echo.
echo NEXT STEPS
echo   1. Open the file named ".env" and set MSSQL_SERVER to your SQL Server name.
echo      Use the same "Server name" that you type when you open SSMS.
echo   2. Double-click check_database.bat to confirm the connection works.
echo   3. Double-click start.bat to launch the app.
echo.
pause
