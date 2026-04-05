# Script de Inicio Automatizado - EduMind
# Inicia Docker + DB + servidor web + worker evitando procesos duplicados.

Write-Host "🚀 Iniciando sistema EduMind..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $projectRoot "app"

function Stop-ExistingProcessByPattern {
    param([string]$Pattern)
    $procs = Get-CimInstance Win32_Process | Where-Object {
        ($_.CommandLine -match $Pattern) -and ($_.CommandLine -match "edumind---ai-learning-guide")
    }
    foreach ($p in $procs) {
        try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
}

# 1. Verificar/Iniciar Docker Desktop
Write-Host "`n[1/4] Verificando Docker Desktop..." -ForegroundColor Yellow
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "   Iniciando Docker Desktop..." -ForegroundColor Gray
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    # Esperar a que Docker esté listo
    $timeout = 60
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        $dockerRunning = docker info 2>$null
        if ($dockerRunning) {
            Write-Host "   ✓ Docker Desktop iniciado correctamente" -ForegroundColor Green
            break
        }
        Write-Host "   Esperando Docker... ($elapsed/$timeout s)" -ForegroundColor Gray
    }
    
    if (-not $dockerRunning) {
        Write-Host "   ✗ Error: Docker no se inició en el tiempo esperado" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "   ✓ Docker Desktop ya está corriendo" -ForegroundColor Green
}

# 2. Iniciar contenedor PostgreSQL
Write-Host "`n[2/4] Iniciando base de datos PostgreSQL..." -ForegroundColor Yellow
docker start edumind-db 2>$null
Start-Sleep -Seconds 3

$dbStatus = docker ps --filter "name=edumind-db" --format "{{.Status}}"
if ($dbStatus -like "Up*") {
    Write-Host "   ✓ PostgreSQL corriendo en localhost:5432" -ForegroundColor Green
}
else {
    Write-Host "   ✗ Error al iniciar PostgreSQL" -ForegroundColor Red
    exit 1
}

# 3. Iniciar servidor Next.js limpio
Write-Host "`n[3/5] Iniciando servidor Next.js..." -ForegroundColor Yellow
Stop-ExistingProcessByPattern "next\\dist\\server\\lib\\start-server.js|next dev --webpack"
Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", "Set-Location '$appDir'; npm run dev"

# Esperar respuesta HTTP en 3000 o 3001
$devReady = $false
$devUrl = ""
for ($i = 0; $i -lt 30; $i++) {
    foreach ($u in @("http://localhost:3000", "http://localhost:3001")) {
        try {
            $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
                $devReady = $true
                $devUrl = $u
                break
            }
        } catch {}
    }
    if ($devReady) { break }
    Start-Sleep -Seconds 1
}

if (-not $devReady) {
    Write-Host "   ✗ Next.js no respondió en puerto 3000/3001" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Next.js activo en $devUrl" -ForegroundColor Green

# 4. Iniciar worker limpio
Write-Host "`n[4/5] Iniciando worker..." -ForegroundColor Yellow
Stop-ExistingProcessByPattern "tsx scripts/run-worker.ts|scripts/run-worker.ts"
Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", "Set-Location '$appDir'; npm run worker"
Write-Host "   ✓ Worker iniciado" -ForegroundColor Green

# 5. Abrir navegador
Write-Host "`n[5/5] Abriendo aplicación en navegador..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process $devUrl
Write-Host "   ✓ Navegador abierto" -ForegroundColor Green

Write-Host "`n✅ Sistema completamente operativo!" -ForegroundColor Green
Write-Host "   - Aplicación: $devUrl" -ForegroundColor White
Write-Host "   - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "   - Worker: activo (terminal separada)" -ForegroundColor White
Write-Host "`nPuedes cerrar esta ventana." -ForegroundColor Gray
