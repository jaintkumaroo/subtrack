@echo off
setlocal
cd /d "%~dp0"
title SubTrack - database check

if not exist venv\Scripts\activate.bat (
    echo Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo.
python -m app.database.diagnose
echo.
pause
