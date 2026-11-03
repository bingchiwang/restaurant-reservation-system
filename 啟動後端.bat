@echo off
setlocal
cd /d "%~dp0backend"
echo Starting Backend API Server (Flask: http://127.0.0.1:5000)...
call venv\Scripts\activate
python run.py
pause
