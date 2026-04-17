param(
  [switch]$InstallDaemon
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if ($InstallDaemon) {
  npx openclaw@latest onboard --install-daemon
}

Write-Output "=== OpenClaw runtime status ==="
openclaw gateway status
