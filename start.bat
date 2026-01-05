@echo off
setlocal enabledelayedexpansion

REM Default ports
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

REM Kill existing processes on the ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% "') do (
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% "') do (
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

REM Start backend in background, all output to log
start /b "" cmd /c "venv\Scripts\activate.bat && uvicorn api.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload >backenderrors.log 2>&1"

timeout /t 2 /nobreak >nul

REM Start frontend in background, all output to log
start /b "" cmd /c "cd frontend && npm run dev -- -p %FRONTEND_PORT% >..\frontenderrors.log 2>&1"

echo Services running in background.
echo Backend: http://localhost:%BACKEND_PORT%
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Run stop.bat to kill all services.
