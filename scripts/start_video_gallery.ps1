param(
  [switch]$Stop
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$pidFile = Join-Path $root "logs\video-gallery.pid"

if ($Stop) {
  if (Test-Path $pidFile) {
    $pidVal = [int](Get-Content $pidFile -Raw).Trim()
    if (Get-Process -Id $pidVal -ErrorAction SilentlyContinue) {
      Stop-Process -Id $pidVal -Force
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Video gallery parado."
  } else {
    Write-Host "No hay video gallery corriendo."
  }
  exit 0
}

New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
if (Test-Path $pidFile) {
  $oldPid = [int](Get-Content $pidFile -Raw).Trim()
  if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $oldPid -Force
  }
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$p = Start-Process python -ArgumentList "scripts\video_gallery_server.py" -WorkingDirectory $root -PassThru
Set-Content -Path $pidFile -Value $p.Id -Encoding ascii
Write-Host "Video gallery en http://localhost:3000 (PID $($p.Id))"

