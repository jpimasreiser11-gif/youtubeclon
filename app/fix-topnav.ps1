#!/usr/bin/env pwsh
# Script para quitar todas las importaciones y usos de TopNav

$files = @(
    "c:\Users\jpima\Downloads\edumind---ai-learning-guide\app\app\projects\page.tsx",
    "c:\Users\jpima\Downloads\edumind---ai-learning-guide\app\app\projects\[id]\page.tsx",
    "c:\Users\jpima\Downloads\edumind---ai-learning-guide\app\app\account\page.tsx",
    "c:\Users\jpima\Downloads\edumind---ai-learning-guide\app\app\analytics\page.tsx",
    "c:\Users\jpima\Downloads\edumind---ai-learning-guide\app\app\editor\[clipId]\page.tsx"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing: $file"
        
        # Read content
        $content = Get-Content $file -Raw
        
        # Remove import line
        $content = $content -replace "import { TopNav } from '@/components/topnav';\r?\n", ""
        
        # Remove <TopNav /> usage
        $content = $content -replace "\s*<TopNav\s*/>\r?\n?", ""
        
        # Write back
        Set-Content -Path $file -Value $content -NoNewline
        
        Write-Host "  ✓ Cleaned"
    }
}

Write-Host "✓ All files cleaned"
