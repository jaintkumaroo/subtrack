@echo off
setlocal
cd /d "%~dp0"
title SubTrack - tests

if not exist venv\Scripts\activate.bat (
    echo Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
pip install -q -r requirements-dev.txt
python -m pytest -v
echo.
pause
