@echo off
title Installation Script - AI Medical Monitor
echo ===================================================
echo   Installing AI Medical Monitor System
echo ===================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python is installed.

:: 2. Check Node.js & NPM
npm -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / NPM is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js and NPM are installed.

:: 3. Setup Backend Environment
echo.
echo Installing Backend Dependencies...
cd backend
if not exist .venv (
    echo Creating python virtual environment (.venv)...
    python -m venv .venv
)
call .venv\Scripts\activate
echo Upgrading pip...
python -m pip install --upgrade pip
echo Installing requirements...
pip install -r requirements.txt
echo Seeding database...
python seed_patients.py
call .venv\Scripts\deactivate
cd ..
echo [OK] Backend installed successfully.

:: 4. Setup Frontend Environment
echo.
echo Installing Frontend Dependencies...
cd frontend
echo Running npm install...
call npm install
cd ..
echo [OK] Frontend installed successfully.

echo.
echo ===================================================
echo   Installation Completed Successfully!
echo   Double-click run.bat to start the system.
echo ===================================================
pause
