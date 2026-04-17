param(
  [switch]$Stop
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$pidFile = Join-Path $root "logs\office.pid"

function Stop-IfExists([int]$pidToStop) {
  if ($pidToStop -gt 0 -and (Get-Process -Id $pidToStop -ErrorAction SilentlyContinue)) {
    Stop-Process -Id $pidToStop -Force
  }
}

function Stop-ProjectServerOn7700 {
  $listener = Get-NetTCPConnection -LocalPort 7700 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $listener) { return }
  $ownerId = [int]$listener.OwningProcess
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId" -ErrorAction SilentlyContinue
  if (-not $proc) { return }
  $cmd = [string]$proc.CommandLine
  $isProjectServer = ($cmd -like "*dashboard_server.py*" -or $cmd -like "*office\\server.py*")
  if ($isProjectServer) {
    Stop-IfExists -pidToStop $ownerId
  }
}

if ($Stop) {
  if (Test-Path $pidFile) {
    $pidVal = [int](Get-Content $pidFile -Raw).Trim()
    Stop-IfExists -pidToStop $pidVal
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Office server parado."
  } else {
    Write-Host "No hay office server corriendo."
  }
  Stop-ProjectServerOn7700
  exit 0
}

New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
if (Test-Path $pidFile) {
  $oldPid = [int](Get-Content $pidFile -Raw).Trim()
  Stop-IfExists -pidToStop $oldPid
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}
Stop-ProjectServerOn7700
$p = Start-Process python -ArgumentList "office\server.py" -WorkingDirectory $root -PassThru
Set-Content -Path $pidFile -Value $p.Id -Encoding ascii
Start-Sleep -Seconds 2
Write-Host "Oficina visual arrancada en http://localhost:7700 (PID $($p.Id))"
