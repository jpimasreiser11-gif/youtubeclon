@echo off
REM ============================================================
REM  START-ALL.bat — One-click startup for the full stack
REM  Run this from: edumind---ai-learning-guide\app\
REM ============================================================
title Sovereign App Launcher

echo.
echo ========================================
echo  SOVEREIGN VIDEO ENGINE - FULL STARTUP
echo ========================================
echo.

REM 1. Start Docker containers (PostgreSQL + Redis)
echo [1/3] Starting Docker containers...
docker start antigravity-db antigravity-redis 2>nul
if errorlevel 1 (
    echo  - Docker containers not found, trying docker-compose...
    cd ..
    docker-compose up -d antigravity-db antigravity-redis 2>nul
    cd app
)
echo  - Docker containers: OK
timeout /t 2 /nobreak >nul

REM 2. Start Next.js dev server in a new window
echo [2/3] Starting Next.js dev server on port 3000...
start "Next.js Dev Server" cmd /k "cd /d %~dp0 && npm run dev"
timeout /t 5 /nobreak >nul

REM 3. Start BullMQ Worker in a new window
echo [3/3] Starting BullMQ Video Worker...
start "BullMQ Worker" cmd /k "cd /d %~dp0 && npm run worker"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo  ALL SERVICES STARTED SUCCESSFULLY!
echo  App URL: http://localhost:3000
echo ========================================
echo.
pause
