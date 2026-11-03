@echo off
chcp 65001 >nul
title 餐廳預約系統 - 啟動前端網頁
cd /d "%~dp0frontend"
echo 正在啟動前端網頁 (Expo Web: http://localhost:8081)...
npm run web
pause
