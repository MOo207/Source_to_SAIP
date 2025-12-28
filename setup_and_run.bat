@echo off
REM Simple Setup and Run Script for Source Code to PDF Generator

echo Source Code to PDF Generator - Quick Setup and Run
echo ================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install required packages if missing
python -c "import reportlab" >nul 2>&1
if errorlevel 1 (
    echo Installing ReportLab...
    python -m pip install reportlab
)

python -c "import chardet" >nul 2>&1
if errorlevel 1 (
    echo Installing chardet...
    python -m pip install chardet
)

REM Run the application
if [%1]==[] (
    REM No arguments provided, run GUI mode
    echo Starting Source Code to PDF Generator...
    python repo_to_saip.py
) else (
    REM Arguments provided, run command-line mode
    echo Starting Source Code to PDF Generator...
    python repo_to_saip.py %*
)

echo.
echo Application closed.
pause