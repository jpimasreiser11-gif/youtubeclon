# Enterprise Storage Cleanup Script
# Deletes files older than 48 hours in the data directory

$Days = 2
$TargetFolder = Join-Path $PSScriptRoot ".." "data"
$ExtensionList = "*.mp4", "*.mp3", "*.json", "*.ass"

Write-Host "🧹 Starting Storage Cleanup in: $TargetFolder" -ForegroundColor Cyan

if (Test-Path $TargetFolder) {
    foreach ($ext in $ExtensionList) {
        Get-ChildItem -Path $TargetFolder -Filter $ext -Recurse | Where-Object { 
            $_.LastWriteTime -lt (Get-Date).AddDays(-$Days) 
        } | ForEach-Object {
            Write-Host "🗑️ Deleting: $($_.Name) (Old: $($_.LastWriteTime))" -ForegroundColor Yellow
            Remove-Item $_.FullName -Force
        }
    }
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Target folder not found." -ForegroundColor Red
}
