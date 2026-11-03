@echo off
chcp 65001 >nul
title 餐廳預約系統 - 啟動後端
cd /d "%~dp0backend"
echo 正在啟動後端 API (Flask: http://127.0.0.1:5000)...
call venv\Scripts\activate
python run.py
pause
