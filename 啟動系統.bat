@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Restaurant Reservation System - Quick Launcher
echo ========================================================
echo.

set "EXPO_NO_TELEMETRY=true"

:: 1. Build web bundle if not present
if not exist "frontend\dist\index.html" (
    echo [*] Generating web build, please wait a moment...
    cd frontend
    call npx expo export -p web
    cd ..
)

echo [1/2] Starting Backend API Server (Flask: http://127.0.0.1:5000)...
start "Restaurant Backend API" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && python run.py"

echo [2/2] Starting Frontend Web Server (http://127.0.0.1:8080)...
start "Restaurant Frontend Web" cmd /k "cd /d "%~dp0frontend\dist_web" && ..\..\backend\venv\Scripts\python.exe -m http.server 8080"

timeout /t 3 /nobreak >nul

echo Opening browser at http://127.0.0.1:8080 ...
start http://127.0.0.1:8080

echo.
echo ========================================================
echo  System is running!
echo  - Frontend Web: http://127.0.0.1:8080
echo  - Backend API:  http://127.0.0.1:5000
echo ========================================================
echo.
pause
