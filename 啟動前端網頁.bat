@echo off
setlocal
cd /d "%~dp0"
set "EXPO_NO_TELEMETRY=true"

if not exist "frontend\dist\index.html" (
    echo [*] Generating web build...
    cd frontend
    call npx expo export -p web
    cd ..
)

echo Starting Frontend Web Server (http://127.0.0.1:8080)...
start "Restaurant Frontend Web" cmd /k "cd /d "%~dp0frontend\dist" && ..\..\backend\venv\Scripts\python.exe -m http.server 8080"
timeout /t 2 /nobreak >nul
start http://127.0.0.1:8080
pause
