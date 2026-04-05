param(
	[string]$RemoteUrl = "",
	[string]$Branch = "main",
	[string]$CommitMessage = "chore: update project"
)

$git = "git"

# Ensure we're in the right place
$scriptPath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptPath
Set-Location $dir

if (-not (Test-Path ".git")) {
	& $git init
}

if ($RemoteUrl -ne "") {
	& $git remote remove origin 2>$null
	& $git remote add origin $RemoteUrl
}

& $git add -A
& $git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
	Write-Host "No hay cambios para commit o hubo un error de commit." -ForegroundColor Yellow
}

& $git branch -M $Branch
Write-Host "Pushing code to GitHub..." -ForegroundColor Cyan
& $git push -u origin $Branch
