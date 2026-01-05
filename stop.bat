@echo off
setlocal enabledelayedexpansion

REM Default ports
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

echo Stopping STOCKTRADE services...

REM Kill processes on backend port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% "') do (
    echo Killing backend process %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill processes on frontend port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% "') do (
    echo Killing frontend process %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo All STOCKTRADE services stopped.
