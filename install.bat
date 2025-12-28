@echo off
REM Windows batch script to set up the Source Code to PDF Generator environment

echo Source Code to PDF Generator - Windows Setup
echo ============================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher and ensure it's in your PATH
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2,3 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% lss 3 (
    echo Error: Python 3.6 or higher is required. Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 6 (
    echo Error: Python 3.6 or higher is required. Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo ✓ Python version %PYTHON_VERSION% is compatible

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists. Removing...
    rmdir /s /q "venv"
)

python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment created successfully

REM Upgrade pip in the virtual environment
echo.
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo Warning: Failed to upgrade pip, continuing anyway
)

REM Install requirements
echo.
echo Installing required packages...
if exist "requirements.txt" (
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo requirements.txt not found, installing default packages...
    venv\Scripts\python.exe -m pip install reportlab chardet
)

if errorlevel 1 (
    echo Error: Failed to install required packages
    pause
    exit /b 1
)

echo ✓ Required packages installed successfully

REM Verify installation
echo.
echo Verifying installation...
venv\Scripts\python.exe -c "import reportlab; import chardet; import tkinter; print('✓ All required packages are available')"
if errorlevel 1 (
    echo Error: Verification failed - some packages are not properly installed
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo To use the Source Code to PDF Generator:
echo 1. Run this command to activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Then run the application:
echo    python repo_to_saip.py
echo.
echo You can also run without activating by using the full path:
echo    venv\Scripts\python.exe repo_to_saip.py
echo.
pause