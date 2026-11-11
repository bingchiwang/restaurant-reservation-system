@echo off
setlocal
cd /d "%~dp0backend"
echo Starting Unified Backend & Admin Console (Port 5000)...
echo - Customer Frontend : http://127.0.0.1:5000
echo - Backend Admin UI  : http://127.0.0.1:5000/admin
call venv\Scripts\activate
python run.py
pause
