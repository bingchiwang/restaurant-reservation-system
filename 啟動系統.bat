@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Restaurant Reservation System - Unified Launcher
echo ========================================================
echo.

set "EXPO_NO_TELEMETRY=true"

:: Build customer web bundle into frontend\dist_web if missing
if not exist "frontend\dist_web\index.html" (
    echo [*] Building customer web frontend, please wait...
    cd frontend
    call npx expo export -p web --output-dir dist_web
    cd ..
)

echo [*] Starting Unified Server (Customer Web + Backend API + Admin Console)...
start "Restaurant System Server (Port 5000)" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && python run.py"

timeout /t 3 /nobreak >nul

echo [*] Opening Customer Web at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000

echo.
echo ========================================================
echo  Unified Server is running on Port 5000!
echo  - Customer Frontend : http://127.0.0.1:5000
echo  - Backend Admin UI  : http://127.0.0.1:5000/admin
echo  - Backend API       : http://127.0.0.1:5000/api/v1
echo ========================================================
echo.
pause
