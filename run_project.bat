@echo off
title VitalGuard AI Launcher
echo ========================================================
echo          VITALGUARD AI SYSTEM LAUNCHER
echo ========================================================
echo.

:: 1. Start MongoDB local if not running
netstat -ano | findstr :27017 >nul
if %errorlevel% neq 0 (
    echo [1/3] Starting Local MongoDB Database...
    start "VitalGuard AI - MongoDB" cmd /k ""C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe" --dbpath "D:\MajorProject\agentic-ai-hospital-discharge-monitoring-system-main\data\db" --bind_ip 127.0.0.1"
    timeout /t 2 /nobreak >nul
) else (
    echo [1/3] MongoDB Database is already running.
)

:: 2. Start FastAPI Backend
echo [2/3] Starting FastAPI Backend (Port 8000)...
cd /d "D:\MajorProject\agentic-ai-hospital-discharge-monitoring-system-main"
start "VitalGuard AI - Backend" cmd /k ".\.venv310\Scripts\python.exe app.py"
timeout /t 3 /nobreak >nul

:: 3. Start React Frontend
echo [3/3] Starting React Vite Frontend (Port 5173)...
cd /d "D:\MajorProject\agentic-ai-hospital-discharge-monitoring-system-main\frontend_react"
start "VitalGuard AI - Frontend" cmd /k "npm run dev"

echo.
echo ========================================================
echo  VitalGuard AI System is now running!
echo  -------------------------------------------------------
echo  Frontend UI  : http://localhost:5173 (or http://localhost:5174)
echo  Backend API  : http://127.0.0.1:8000
echo  Swagger Docs : http://127.0.0.1:8000/docs
echo.
echo  Default Admin Credentials:
echo  Email    : admin@hospital.com
echo  Password : PHANI123@9999
echo ========================================================
echo.
pause
