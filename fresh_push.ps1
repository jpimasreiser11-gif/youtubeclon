param(
	[string]$RemoteUrl = "",
	[string]$Branch = "main",
	[string]$CommitMessage = "feat: fresh project update"
)

$git = "git"

if (-not (Test-Path ".git")) {
	& $git init
}

if ($RemoteUrl -ne "") {
	& $git remote remove origin 2>$null
	& $git remote add origin $RemoteUrl
}

Write-Host "Adding files..."
& $git add -A

Write-Host "Committing files..."
& $git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
	Write-Host "No hay cambios para commit o hubo un error de commit." -ForegroundColor Yellow
}

& $git branch -M $Branch

Write-Host "Configuring memory sizing for Git push..."
& $git config http.postBuffer 524288000
& $git config http.lowSpeedLimit 0
& $git config http.lowSpeedTime 999999

Write-Host "Pushing code to GitHub..." -ForegroundColor Cyan
& $git push -u origin $Branch
