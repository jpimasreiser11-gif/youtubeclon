@echo off
REM Upload Scheduler Wrapper for Windows Task Scheduler
REM Runs every 5 minutes

cd /d "C:\Users\jpima\Downloads\edumind---ai-learning-guide"

SET PYTHON_PATH=venv_sovereign\Scripts\python.exe
SET SCRIPT_PATH=scripts\upload_scheduler.py
SET LOG_DIR=logs\uploads
SET LOG_FILE=%LOG_DIR%\scheduler_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM Create logs directory if not exists
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Run orchestrator to auto-queue clips from enabled projects
echo [%date% %time%] Running daily orchestrator... >> "%LOG_FILE%"
"%PYTHON_PATH%" scripts\automation_orchestrator.py >> "%LOG_FILE%" 2>&1

REM Run scheduler to execute pending uploads
echo [%date% %time%] Running upload executor... >> "%LOG_FILE%"
"%PYTHON_PATH%" "%SCRIPT_PATH%" --db-password "n8n" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [%date% %time%] ERROR: Scheduler failed >> "%LOG_FILE%"
) else (
    echo [%date% %time%] Scheduler completed successfully >> "%LOG_FILE%"
)

REM Cleanup old logs (keep last 7 days)
forfiles /p "%LOG_DIR%" /s /m *.log /d -7 /c "cmd /c del @path" 2>nul

exit /b 0
