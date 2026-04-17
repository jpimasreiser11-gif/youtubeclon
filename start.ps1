param(
  [string]$Mode = "--once"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if ($args.Count -gt 0 -and $args[0] -match '^--') {
  $Mode = $args[0]
}

$null = New-Item -ItemType Directory -Force -Path "logs", "briefings", "research", ".copilot\agents"

switch ($Mode) {
  "--status" {
    python scripts\agent_status.py --once
    break
  }
  "--stop" {
    if (Test-Path "logs\master.pid") {
      $masterPid = (Get-Content "logs\master.pid" -Raw).Trim()
      if ($masterPid -and (Get-Process -Id $masterPid -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $masterPid
        Remove-Item "logs\master.pid" -Force -ErrorAction SilentlyContinue
        Write-Host "Sistema parado (PID $masterPid)"
      } else {
        Remove-Item "logs\master.pid" -Force -ErrorAction SilentlyContinue
        Write-Host "El proceso ya no estaba corriendo."
      }
    } else {
      Write-Host "No hay sistema corriendo."
    }
    break
  }
  "--auto" {
    Write-Host "Verificando APIs..."
    python scripts\check_apis.py
    if ($LASTEXITCODE -ne 0) {
      Write-Host "Continuo igualmente con modo fallback/local."
    }

    if (Test-Path "logs\master.pid") {
      $existing = (Get-Content "logs\master.pid" -Raw).Trim()
      if ($existing -and (Get-Process -Id $existing -ErrorAction SilentlyContinue)) {
        Write-Host "Ya estaba corriendo (PID $existing)."
        break
      }
    }

    $p = Start-Process powershell -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","scripts\run_agents.ps1" -WorkingDirectory $PSScriptRoot -PassThru
    Set-Content "logs\master.pid" $p.Id -Encoding ascii
    Start-Sleep -Seconds 3

    Write-Host "Sistema arrancado (PID $($p.Id))"
    Write-Host "Estado: python scripts\agent_status.py --once"
    Write-Host "Monitor: python scripts\agent_status.py"
    Write-Host "Parar: powershell -ExecutionPolicy Bypass -File .\start.ps1 --stop"
    if (Test-Path "logs\master.log") {
      Get-Content "logs\master.log" -Tail 10
    }
    break
  }
  "--once" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_agents.ps1 -Once
    python scripts\agent_status.py --once
    break
  }
  "--office" {
    powershell -NoProfile -ExecutionPolicy Bypass -File office\start_office.ps1
    break
  }
  "--schedule" {
    $env:PYTHONPATH = $PSScriptRoot
    Write-Host "Iniciando monitor de agenda (scheduler)..."
    python -m backend.scheduler
    break
  }
  "--office-stop" {
    powershell -NoProfile -ExecutionPolicy Bypass -File office\start_office.ps1 -Stop
    break
  }
  "--videos" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_video_gallery.ps1
    break
  }
  "--videos-stop" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_video_gallery.ps1 -Stop
    break
  }
  "--cleanup" {
    Get-Content "prompts\CLEANUP_PROMPT.md" -Raw | gh copilot suggest -t shell -
    break
  }
  "--master" {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm"
    $statusContent = @"
# Estado del Sistema - $now
**Iteracion actual**: #1
**Criterios completados**: 0/10
**Trabajando en**: Iniciando analisis del proyecto
**Proxima tarea**: Revisar estado actual y crear backlog de mejoras
**Bloqueantes**: Ninguno detectado aun
"@
    Set-Content "STATUS.md" $statusContent -Encoding UTF8

    if (-not (Test-Path "research\improvement_backlog.md")) {
      $backlog = @"
# Backlog de Mejoras - VidFlow AI

## Por hacer
- [ ] Pipeline sin pantalla negra
- [ ] 7 dias de scripts por canal
- [ ] 10 checks de calidad al 100%
- [ ] Dashboard web funcional
- [ ] GitHub Actions configurado
- [ ] Tests automaticos
- [ ] 3 afiliados activos por canal
- [ ] Sistema trending topics
- [ ] Documentacion final
"@
      Set-Content "research\improvement_backlog.md" $backlog -Encoding UTF8
    }

    $instructions = if (Test-Path ".github\copilot-instructions.md") { Get-Content ".github\copilot-instructions.md" -Raw } else { "" }
    $masterPrompt = Get-Content "prompts\MASTER_AUTONOMOUS_PROMPT.md" -Raw
    $status = Get-Content "STATUS.md" -Raw
    $fullPrompt = @"
$instructions

---

$masterPrompt

---

ESTADO ACTUAL DEL PROYECTO:
$status

Lee el archivo research/improvement_backlog.md para ver que queda por hacer.
Empieza por lo mas critico y trabaja en orden de prioridad.
"@
    $fullPrompt | gh copilot suggest -t shell -
    break
  }
}
