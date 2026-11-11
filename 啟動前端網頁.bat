@echo off
setlocal
cd /d "%~dp0"
echo [*] Frontend is now unified and served by the Backend Server at http://127.0.0.1:5000
start http://127.0.0.1:5000
pause
