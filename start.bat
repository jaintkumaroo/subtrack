@echo off
setlocal
cd /d "%~dp0"
title SubTrack launcher

if not exist venv\Scripts\activate.bat (
    echo Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)
if not exist .env (
    echo The .env file is missing. Run setup.bat first.
    pause
    exit /b 1
)

echo Starting the SubTrack backend (API)...
start "SubTrack Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && uvicorn app.main:app --reload"

echo Waiting for the backend to come up...
timeout /t 6 /nobreak >nul

echo Starting the SubTrack app (browser)...
start "SubTrack App" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && streamlit run frontend\app.py"

echo.
echo Two windows were opened. Keep both open while you use the app.
echo   App (opens by itself):  http://localhost:8501
echo   API documentation:      http://127.0.0.1:8000/docs
echo.
echo If the app shows a database error, read the "SubTrack Backend" window.
timeout /t 8 >nul
