@echo off
echo Starting EduMind Upload Scheduler...
echo Press Ctrl+C to stop.
:loop
python scripts/schedule_uploads.py
if errorlevel 1 (
    echo Scheduler crashed or stopped. Restarting in 10 seconds...
    timeout /t 10
    goto loop
)
pause
