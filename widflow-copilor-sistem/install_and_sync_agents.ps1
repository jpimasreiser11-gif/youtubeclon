param(
  [string]$SourceDir = "sistema-10-agentes",
  [string]$TargetDir = ".github/agents"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceDir)) {
  throw "Source directory not found: $SourceDir"
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$files = Get-ChildItem -Path $SourceDir -Filter "*.agent.md" -File | Sort-Object Name
if (-not $files) {
  throw "No .agent.md files found in $SourceDir"
}

foreach ($file in $files) {
  $dest = Join-Path $TargetDir $file.Name
  Copy-Item -Path $file.FullName -Destination $dest -Force
}

Write-Output "Installed $($files.Count) agents into $TargetDir"
