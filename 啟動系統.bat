@echo off
chcp 65001 >nul
title 餐廳預約系統 - 一鍵啟動 (前後端)

echo ========================================================
echo        餐廳預約與點餐系統 - 一鍵啟動精靈
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] 正在啟動後端 API 伺服器 (Flask: http://127.0.0.1:5000)...
start "餐廳後端 API (Flask:5000)" cmd /k "chcp 65001 >nul && cd backend && call venv\Scripts\activate && python run.py"

timeout /t 2 /nobreak >nul

echo [2/2] 正在啟動前端網頁伺服器 (Expo Web: http://localhost:8081)...
start "餐廳前端網頁 (Expo Web)" cmd /k "chcp 65001 >nul && cd frontend && npm run web"

echo.
echo ========================================================
echo  已在獨立視窗中成功啟動後端與前端網頁！
echo  - 後端 API: http://127.0.0.1:5000
echo  - 前端網頁: http://localhost:8081 (將自動於瀏覽器開啟)
echo ========================================================
echo.
pause
