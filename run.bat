@echo off
title Launcher - AI Medical Monitor
echo ===================================================
echo   Starting AI Medical Monitor System...
echo ===================================================
echo.

:: 1. Start Backend in a new window
echo Starting Backend Server on http://localhost:8000 ...
start "Backend Server" cmd /k "cd backend && .venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"

:: 2. Start Frontend in a new window
echo Starting Frontend Server on http://localhost:3000 ...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

:: 3. Wait a moment and open browser
echo Waiting for servers to initialize...
timeout /t 5 >nul
echo Opening web browser to http://localhost:3000 ...
start http://localhost:3000

echo.
echo ===================================================
echo   System is running!
echo   Close the popped-up command windows to stop.
echo ===================================================
