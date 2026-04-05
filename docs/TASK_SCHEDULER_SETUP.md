# Windows Task Scheduler Setup Instructions

## Automated Upload Scheduler

### Manual Setup (GUI)

1. **Open Task Scheduler**:
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create New Task**:
   - Click "Create Basic Task"
   - Name: `Viral Clips Upload Scheduler`
   - Description: `Runs every 5 minutes to upload scheduled clips`

3. **Trigger**:
   - Select "Daily"
   - Start: Today at 00:00
   - Recur every: 1 day
   - Click "Repeat task every"
   - Select "5 minutes"
   - Duration: "Indefinitely"

4. **Action**:
   - Action: "Start a program"
   - Program/script: `C:\Users\jpima\Downloads\edumind---ai-learning-guide\scripts\run_scheduler.bat`
   - Start in: `C:\Users\jpima\Downloads\edumind---ai-learning-guide`

5. **Conditions**:
   - Uncheck "Start the task only if the computer is on AC power"
   - Check "Wake the computer to run this task"

6. **Settings**:
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Check "If the task fails, restart every": 1 minute, 3 times

7. **Environment Variables**:
   - Before clicking "Finish", go to "Actions" tab
   - Edit the action
   - Add to "Add arguments":
     ```
     --db-password YOUR_POSTGRES_PASSWORD_HERE
     ```

### PowerShell Auto-Setup

Alternatively, run this PowerShell script as Administrator:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\jpima\Downloads\edumind---ai-learning-guide\scripts\run_scheduler.bat"

$trigger = New-ScheduledTaskTrigger -Daily -At 00:00 -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "Viral Clips Upload Scheduler" -Action $action -Trigger $trigger -Settings $settings -Description "Automated upload scheduler for viral clips"
```

### Verify Task

```powershell
Get-ScheduledTask -TaskName "Viral Clips Upload Scheduler"
```

### Logging

Logs are stored in:
```
C:\Users\jpima\Downloads\edumind---ai-learning-guide\logs\uploads\scheduler_YYYYMMDD.log
```

Old logs are automatically deleted after 7 days.

### Troubleshooting

**Task not running?**
- Check Task Scheduler → "Task Status" should show "Running" or "Ready"
- View logs in `logs/uploads/`
- Ensure `POSTGRES_PASSWORD` environment variable is set

**Permission issues?**
- Run Task Scheduler as Administrator
- Ensure Python script has execute permissions

**Scheduler not finding clips?**
- Run manually: `python scripts/schedule_uploads.py --db-password PASSWORD`
- Check database for clips with `transcription_status = 'completed'`
