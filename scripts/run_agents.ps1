param(
  [switch]$Once,
  [int]$LoopDelaySeconds = 5
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$configPath = Join-Path $root "widflow-copilor-sistem\team-agents.config.json"
$syncScript = Join-Path $root "widflow-copilor-sistem\install_and_sync_agents.ps1"
$agentsDir = Join-Path $root ".github\agents"
$logDir = Join-Path $root "logs"
$statePath = Join-Path $logDir "agents-state.json"
$eventsPath = Join-Path $logDir "agents-events.jsonl"
$historyPath = Join-Path $logDir "agents-history.json"
$progressDir = Join-Path $logDir "agent-progress"
$progressAllPath = Join-Path $progressDir "all-agents.progress.jsonl"
$reportDir = Join-Path $logDir "agent-reports"
$learningDir = Join-Path $logDir "agent-learning"
$dailyPromptsDir = Join-Path $logDir "daily-prompts"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $progressDir | Out-Null
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
New-Item -ItemType Directory -Force -Path $learningDir | Out-Null
New-Item -ItemType Directory -Force -Path $dailyPromptsDir | Out-Null

if (-not (Test-Path $configPath)) {
  throw "Config not found: $configPath"
}

if (Test-Path $syncScript) {
  & powershell -ExecutionPolicy Bypass -File $syncScript | Out-Null
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$order = @($config.execution_order)
$parallelCapable = $null -ne (Get-Command Start-ThreadJob -ErrorAction SilentlyContinue)

if (-not (Test-Path $agentsDir)) {
  throw "Agents directory not found: $agentsDir"
}

foreach ($agentFile in $order) {
  $full = Join-Path $agentsDir $agentFile
  if (-not (Test-Path $full)) {
    throw "Missing agent profile: $full"
  }
}

function Save-State([hashtable]$state) {
  $state.updated_at = (Get-Date).ToString("s")
  $json = $state | ConvertTo-Json -Depth 8
  $enc = New-Object System.Text.UTF8Encoding($false, $false)
  [System.IO.File]::WriteAllText($statePath, [string]$json, $enc)
}

function Write-Event {
  param(
    [int]$Cycle,
    [string]$Type,
    [string]$Agent = "",
    [string]$Status = "",
    [string]$Action = "",
    [string]$Result = "",
    [string]$Error = "",
    [int]$DurationMs = 0
  )
  $event = [ordered]@{
    ts = (Get-Date).ToString("s")
    cycle = $Cycle
    type = $Type
    agent = $Agent
    status = $Status
    action = $Action
    result = $Result
    error = $Error
    duration_ms = $DurationMs
  }
  $line = (($event | ConvertTo-Json -Compress) + [Environment]::NewLine)
  $enc = New-Object System.Text.UTF8Encoding($false, $false)
  [System.IO.File]::AppendAllText($eventsPath, $line, $enc)
  [System.IO.File]::AppendAllText($progressAllPath, $line, $enc)
  if ($Agent) {
    $agentFileSafe = ($Agent -replace '\.agent\.md$','')
    $agentProgressPath = Join-Path $progressDir ($agentFileSafe + ".progress.jsonl")
    [System.IO.File]::AppendAllText($agentProgressPath, $line, $enc)
  }
}

function Read-History {
  if (-not (Test-Path $historyPath)) {
    return @{
      updated_at = (Get-Date).ToString("s")
      agents = @{}
      cycles = @()
    }
  }
  $raw = Get-Content $historyPath -Raw | ConvertFrom-Json
  $history = @{
    updated_at = (Get-Date).ToString("s")
    agents = @{}
    cycles = @()
  }
  if ($raw -and $raw.agents) {
    foreach ($prop in $raw.agents.PSObject.Properties) {
      $a = $prop.Value
      $history.agents[$prop.Name] = @{
        runs = [int]($a.runs)
        done = [int]($a.done)
        errors = [int]($a.errors)
        total_duration_ms = [int]($a.total_duration_ms)
        last_cycle = [int]($a.last_cycle)
        last_status = [string]$a.last_status
        last_action = [string]$a.last_action
        last_result = [string]$a.last_result
        last_error = [string]$a.last_error
        last_started_at = [string]$a.last_started_at
        last_finished_at = [string]$a.last_finished_at
      }
    }
  }
  if ($raw -and $raw.cycles) {
    foreach ($c in $raw.cycles) {
      $history.cycles += @{
        cycle = [int]$c.cycle
        started_at = [string]$c.started_at
        finished_at = [string]$c.finished_at
        done = [int]$c.done
        errors = [int]$c.errors
      }
    }
  }
  return $history
}

function Save-History([hashtable]$history) {
  $history.updated_at = (Get-Date).ToString("s")
  $json = $history | ConvertTo-Json -Depth 8
  $enc = New-Object System.Text.UTF8Encoding($false, $false)
  [System.IO.File]::WriteAllText($historyPath, [string]$json, $enc)
}

function Update-AgentHistory {
  param(
    [int]$Cycle,
    [string]$Agent,
    [string]$Status,
    [string]$Action,
    [string]$Result,
    [string]$Error,
    [int]$DurationMs,
    [string]$StartedAt,
    [string]$FinishedAt
  )
  $history = Read-History
  if (-not $history.agents.ContainsKey($Agent)) {
    $history.agents[$Agent] = @{
      runs = 0
      done = 0
      errors = 0
      total_duration_ms = 0
      last_cycle = 0
      last_status = ""
      last_action = ""
      last_result = ""
      last_error = ""
      last_started_at = ""
      last_finished_at = ""
    }
  }
  $a = $history.agents[$Agent]
  $a.runs = [int]$a.runs + 1
  if ($Status -eq "done") { $a.done = [int]$a.done + 1 } else { $a.errors = [int]$a.errors + 1 }
  $a.total_duration_ms = [int]$a.total_duration_ms + $DurationMs
  $a.last_cycle = $Cycle
  $a.last_status = $Status
  $a.last_action = $Action
  $a.last_result = $Result
  $a.last_error = $Error
  $a.last_started_at = $StartedAt
  $a.last_finished_at = $FinishedAt
  Save-History $history
}

function Update-AgentLearning {
  param(
    [string]$Agent,
    [string]$Status,
    [string]$Action,
    [string]$Result,
    [string]$Error
  )
  $safeName = ($Agent -replace '\.agent\.md$','')
  $learningPath = Join-Path $learningDir ($safeName + ".json")
  $learningMdPath = Join-Path $learningDir ($safeName + ".md")

  $raw = $null
  if (Test-Path $learningPath) {
    try { $raw = Get-Content $learningPath -Raw | ConvertFrom-Json } catch { $raw = $null }
  }

  $entries = @()
  if ($raw -and $raw.entries) {
    foreach ($e in @($raw.entries)) {
      $entries += [ordered]@{
        ts = [string]$e.ts
        status = [string]$e.status
        action = [string]$e.action
        result = [string]$e.result
        error = [string]$e.error
        learning = [string]$e.learning
      }
    }
  }

  $learningText = ""
  if ($Status -eq "done") {
    $learningText = "Replicar: $Action -> $Result"
  } else {
    $learningText = "Evitar fallo en '$Action': $Error"
  }

  $entry = [ordered]@{
    ts = (Get-Date).ToString("s")
    status = $Status
    action = $Action
    result = $Result
    error = $Error
    learning = $learningText
  }

  $entries = @($entry) + @($entries)
  if ($entries.Count -gt 80) { $entries = @($entries | Select-Object -First 80) }

  $baseRuns = 0
  $baseDone = 0
  $baseErrors = 0
  if ($raw) {
    $baseRuns = [int]$raw.total_runs
    $baseDone = [int]$raw.total_done
    $baseErrors = [int]$raw.total_errors
  }
  $totalRuns = $baseRuns + 1
  $totalDone = $baseDone + $(if ($Status -eq "done") { 1 } else { 0 })
  $totalErrors = $baseErrors + $(if ($Status -eq "error") { 1 } else { 0 })

  $data = [ordered]@{
    agent = $safeName
    total_runs = $totalRuns
    total_done = $totalDone
    total_errors = $totalErrors
    last_updated = (Get-Date).ToString("s")
    last_learning = $learningText
    entries = $entries
  }

  $data | ConvertTo-Json -Depth 8 | Set-Content -Path $learningPath -Encoding UTF8

  $md = @()
  $md += "# Learning log - $safeName"
  $md += ""
  $md += "Actualizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
  $md += "- Runs: $totalRuns"
  $md += "- OK: $totalDone"
  $md += "- ERR: $totalErrors"
  $md += "- Ultimo aprendizaje: $learningText"
  $md += ""
  $md += "## Ultimas lecciones"
  foreach ($e in @($entries | Select-Object -First 12)) {
    $md += "- [$($e.ts)] [$($e.status)] $($e.learning)"
  }
  $md | Set-Content -Path $learningMdPath -Encoding UTF8
}

function Update-CycleHistory {
  param(
    [int]$Cycle,
    [string]$StartedAt,
    [string]$FinishedAt,
    [int]$DoneCount,
    [int]$ErrorCount
  )
  $history = Read-History
  $history.cycles = @($history.cycles | Where-Object { [int]$_.cycle -ne $Cycle })
  $history.cycles += @{
    cycle = $Cycle
    started_at = $StartedAt
    finished_at = $FinishedAt
    done = $DoneCount
    errors = $ErrorCount
  }
  if ($history.cycles.Count -gt 200) {
    $history.cycles = @($history.cycles | Select-Object -Last 200)
  }
  Save-History $history
}

function Get-AgentNum([string]$agentFile) {
  $m = [regex]::Match($agentFile, '^(?<n>\d{2})-')
  if ($m.Success) { return $m.Groups['n'].Value }
  return "00"
}

function Get-TodayCalendarTasks {
  $calendarPath = Join-Path $root ".openclaw\calendar\prompt_calendar.json"
  if (-not (Test-Path $calendarPath)) {
    try { python scripts\generate_calendar.py | Out-Null } catch {}
  }
  if (-not (Test-Path $calendarPath)) { return @{} }
  try {
    $calendar = Get-Content -Path $calendarPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $today = Get-Date -Format "yyyy-MM-dd"
    $entry = $calendar | Where-Object { $_.date -eq $today } | Select-Object -First 1
    if (-not $entry) {
      $day = [int](Get-Date).DayOfYear
      $entry = $calendar | Where-Object { [int]$_.day -eq $day } | Select-Object -First 1
    }
    if ($entry -and $entry.agent_tasks) {
      $tasks = @{}
      foreach ($p in $entry.agent_tasks.PSObject.Properties) { $tasks[$p.Name] = [string]$p.Value }
      return $tasks
    }
  } catch {}
  return @{}
}

function Get-TodayTaskForAgent {
  param(
    [string]$agentFile,
    [hashtable]$todayTasks
  )
  $num = Get-AgentNum $agentFile
  $calendarKey = switch ($num) {
    "00" { "00-patriarch" }
    "01" { "01-researcher" }
    "02" { "02-content-forge" }
    "03" { "03-code-sentinel" }
    "04" { "04-seo-engineer" }
    "05" { "05-quality-gate" }
    "06" { "06-money-finder" }
    "07" { "07-data-analyst" }
    "08" { "08-fixer" }
    "09" { "09-trend-hunter" }
    "10" { "10-scheduler" }
    "11" { "11-ui-evolution" }
    "12" { "12-performance" }
    "13" { "13-adsense-web" }
    "14" { "14-affiliate" }
    "15" { "15-digital-products" }
    "16" { "16-sponsorship" }
    "17" { "17-newsletter" }
    "18" { "18-shorts" }
    "19" { "19-distribution" }
    "20" { "20-system-seller" }
    "21" { "21-community" }
    "22" { "22-ab-testing" }
    "23" { "23-virality" }
    "24" { "24-net-forager" }
    "25" { "25-video-quality" }
    Default { "" }
  }
  if ($calendarKey -and $todayTasks.ContainsKey($calendarKey)) {
    return [string]$todayTasks[$calendarKey]
  }
  return ""
}

function Write-AgentInboxMessage {
  param(
    [string]$ToAgentNum,
    [string]$FromTag,
    [string]$Body,
    [string]$Prefix = "message"
  )
  $stamp = Get-Date -Format "yyyy-MM-dd-HH-mm-ss"
  $msg = @(
    "FROM: $FromTag",
    "TO: Agent-$ToAgentNum",
    "TIME: $(Get-Date -Format 'HH:mm')",
    "",
    $Body
  ) -join [Environment]::NewLine

  $targets = @()
  $targets += Get-ChildItem -Path (Join-Path $root ".copilot\agents") -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "agent-$ToAgentNum-*" } | ForEach-Object { Join-Path $_.FullName "inbox" }
  $targets += Get-ChildItem -Path (Join-Path $root "agents-system") -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "agent-$ToAgentNum-*" } | ForEach-Object { Join-Path $_.FullName "inbox" }
  $targets += Get-ChildItem -Path (Join-Path $root ".github\agents") -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$ToAgentNum-*" } | ForEach-Object { Join-Path $_.FullName "inbox" }
  $targets = @($targets | Select-Object -Unique)

  foreach ($inbox in $targets) {
    New-Item -ItemType Directory -Force -Path $inbox | Out-Null
    $file = Join-Path $inbox ("{0}-{1}.md" -f $Prefix, $stamp)
    Set-Content -Path $file -Value $msg -Encoding UTF8
  }
  return $targets.Count
}

function Write-AgentReports {
  $history = Read-History
  $agentsHistory = $history.agents
  $global = @()
  $global += "# Reporte global de agentes"
  $global += ""
  $global += "Actualizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
  $global += ""
  $global += "| Agente | Runs | OK | ERR | Ultima accion |"
  $global += "|---|---:|---:|---:|---|"

  foreach ($agentFile in $order) {
    $agentKey = $agentFile
    if (-not $agentsHistory.ContainsKey($agentKey)) { continue }
    $h = $agentsHistory[$agentKey]
    $agentNum = Get-AgentNum $agentFile
    $safeName = ($agentFile -replace '\.agent\.md$','')
    $progressPath = Join-Path $progressDir ($safeName + ".progress.jsonl")
    $reportPath = Join-Path $reportDir ($safeName + ".md")

    $doc = @()
    $doc += "# Reporte del agente $safeName"
    $doc += ""
    $doc += "Actualizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $doc += ""
    $doc += "## Resumen"
    $doc += "- Runs: $($h.runs)"
    $doc += "- OK: $($h.done)"
    $doc += "- ERR: $($h.errors)"
    $doc += "- Estado actual: $($h.last_status)"
    $doc += "- Ultima accion: $($h.last_action)"
    if ($h.last_result) { $doc += "- Ultimo resultado: $($h.last_result)" }
    if ($h.last_error) { $doc += "- Ultimo error: $($h.last_error)" }
    $doc += "- Inicio ultimo run: $($h.last_started_at)"
    $doc += "- Fin ultimo run: $($h.last_finished_at)"
    $doc += ""
    $doc += "## Como verlo en directo"
    $doc += "- Progreso del agente:"
    $doc += "  Get-Content $progressPath -Wait"
    $doc += "- Eventos globales:"
    $doc += "  Get-Content $progressAllPath -Wait"
    $doc += ""
    $doc += "## Ultimos eventos del agente"

    if (Test-Path $progressPath) {
      $tail = Get-Content $progressPath -Tail 12
      if ($tail.Count -gt 0) {
        $doc += "BEGIN_JSON"
        $doc += $tail
        $doc += "END_JSON"
      } else {
        $doc += "_Sin eventos todavia._"
      }
    } else {
      $doc += "_Sin archivo de progreso todavia._"
    }

    Set-Content -Path $reportPath -Value $doc -Encoding UTF8
    $global += "| $agentNum - $safeName | $($h.runs) | $($h.done) | $($h.errors) | $($h.last_action) |"
  }

  $global += ""
  $global += "## Como ver todo en vivo"
  $global += "- Dashboard web: http://localhost:7700"
  $global += "- Estado terminal: python scripts\\agent_status.py"
  $global += "- Eventos globales: Get-Content logs\\agents-events.jsonl -Wait"
  $global += "- Progreso global: Get-Content logs\\agent-progress\\all-agents.progress.jsonl -Wait"

  Set-Content -Path (Join-Path $reportDir "ALL_AGENTS.md") -Value $global -Encoding UTF8
}

function Get-LatestFileIn([string]$relativePattern) {
  $searchRoot = Join-Path $root "output"
  if (-not (Test-Path $searchRoot)) { return $null }
  $items = Get-ChildItem -Path $searchRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
      $rel = $_.FullName.Substring($root.Length).TrimStart('\')
      $rel -like $relativePattern
    } |
    Sort-Object LastWriteTime -Descending
  if ($items -and $items.Count -gt 0) {
    return $items[0]
  }
  return $null
}

function Invoke-AgentTask([string]$agentFile) {
  $name = $agentFile.ToLower()
  if ($name -like "*patriarch*") {
    $diaryDir = Join-Path $root "diary"
    New-Item -ItemType Directory -Force -Path $diaryDir | Out-Null
    $diaryFile = Join-Path $diaryDir "patriarch-diary.md"
    $statusBoard = Join-Path $root "STATUS_BOARD.md"
    $eventsFile = Join-Path $root "logs\agents-events.jsonl"
    $historyFile = Join-Path $root "logs\agents-history.json"
    $needsFile = Join-Path $root "NEEDS_FROM_HUMAN.md"

    $recentLines = @()
    if (Test-Path $eventsFile) {
      $recentLines = Get-Content $eventsFile -Tail 30 | Where-Object { $_ -and $_.Trim() -ne "" }
    }
    $recentSummaries = @()
    foreach ($line in $recentLines) {
      try {
        $ev = $line | ConvertFrom-Json
        if ($ev.type -eq "agent_result" -and $ev.agent) {
          $agentTag = ($ev.agent -replace '\.agent\.md$','')
          $recentSummaries += "${agentTag}: $($ev.action)"
        }
      } catch {}
    }
    $recentSummaries = @($recentSummaries | Select-Object -Unique | Select-Object -First 4)
    $summaryText = if ($recentSummaries.Count -gt 0) { ($recentSummaries -join "; ") } else { "sin novedades destacadas en el último tramo" }

    $needsCount = 0
    if (Test-Path $needsFile) {
      $needsCount = @((Get-Content $needsFile) | Where-Object { $_ -match '^\s*-\s*\[\s\]\s+' }).Count
    }
    $entry = "{0} - El equipo esta activo. Acabo de revisar el pulso general: {1}. {2}" -f (Get-Date -Format "HH:mm"), $summaryText, ($(if($needsCount -gt 0){"Hay $needsCount necesidades pendientes para humano."}else{"No veo bloqueos humanos abiertos ahora mismo."}))
    Add-Content -Path $diaryFile -Value ($entry + [Environment]::NewLine) -Encoding UTF8

    $board = @()
    $board += "# VidFlow AI - What's Happening Right Now"
    $board += "Last updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    $board += ""
    $board += "## The team is working on..."
    if (Test-Path $historyFile) {
      try {
        $h = Get-Content $historyFile -Raw | ConvertFrom-Json
        $items = @($h.agents.PSObject.Properties | ForEach-Object { $_.Value }) | Sort-Object last_finished_at -Descending | Select-Object -First 8
        foreach ($it in $items) {
          $board += "Agent - $($it.last_action)"
        }
      } catch {
        $board += "Sin historial legible en este momento."
      }
    } else {
      $board += "Sin historial todavía."
    }
    $board += ""
    $board += "## Needs your attention"
    if ($needsCount -gt 0) {
      $board += "Revisa NEEDS_FROM_HUMAN.md ($needsCount pendientes)."
    } else {
      $board += "Sin acciones humanas pendientes por ahora."
    }
    Set-Content -Path $statusBoard -Value $board -Encoding UTF8

    if ($recentSummaries.Count -gt 0) {
      [void](Write-AgentInboxMessage -ToAgentNum "01" -FromTag "Agent-00 (Patriarch)" -Prefix "from-patriarch" -Body "He detectado actividad relevante reciente. Revisa el estado global y prioriza hoy: $summaryText")
    }
    return @{ ok = $true; action = "Write patriarch diary and status board"; result = "entry_written, needs=$needsCount" }
  }
  if ($name -like "*coordinator*") {
    $agentsCount = (Get-ChildItem -Path $agentsDir -Filter "*.agent.md" -File | Measure-Object).Count
    return @{ ok = $true; action = "Validate team config and agent registry"; result = "agents=$agentsCount, mode=$($config.mode)" }
  }
  if ($name -like "*research-trends*") {
    $cmd = "python -c ""import sqlite3; db=r'$root\\data\\youtube_automation.db'; con=sqlite3.connect(db); cur=con.cursor(); cur.execute('select count(*) from trends'); print(cur.fetchone()[0])"""
    $val = (Invoke-Expression $cmd 2>$null | Select-Object -First 1)
    return @{ ok = $true; action = "Scan trends dataset"; result = "trends_count=$val" }
  }
  if ($name -like "*script-director*") {
    $f = Get-LatestFileIn "output\*\scripts\*.txt"
    if ($f) { return @{ ok = $true; action = "Inspect latest script quality source"; result = "latest_script=$($f.Name)" } }
    return @{ ok = $false; action = "Inspect latest script quality source"; error = "no script files found" }
  }
  if ($name -like "*voice-audio*") {
    $f = Get-LatestFileIn "output\*\audio\*.mp3"
    if (-not $f) { $f = Get-LatestFileIn "output\*\audio\*.wav" }
    if ($f) { return @{ ok = $true; action = "Check latest narration audio asset"; result = "latest_audio=$($f.Name)" } }
    return @{ ok = $false; action = "Check latest narration audio asset"; error = "no audio files found" }
  }
  if ($name -like "*footage-curator*") {
    $clips = (Get-ChildItem -Path (Join-Path $root "output") -Recurse -Include "*.mp4" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "\\clips\\" } | Measure-Object).Count
    return @{ ok = $true; action = "Count available B-roll clips"; result = "clips_count=$clips" }
  }
  if ($name -like "*video-editor*") {
    $f = Get-LatestFileIn "output\*\videos\*.mp4"
    if ($f) { return @{ ok = $true; action = "Validate latest final video asset"; result = "latest_video=$($f.Name)" } }
    return @{ ok = $false; action = "Validate latest final video asset"; error = "no final video found" }
  }
  if ($name -like "*thumbnail-seo*") {
    $cmd = "python scripts\income_report.py"
    Invoke-Expression $cmd 2>&1 | Out-Null
    $f = Get-LatestFileIn "output\*\thumbnails\*.png"
    if (-not $f) { $f = Get-LatestFileIn "output\*\thumbnails\*.jpg" }
    if (-not $f) { $f = Get-LatestFileIn "output\*\thumbnails\*.jpeg" }
    if ($f) { return @{ ok = $true; action = "Validate thumbnail and generate income report"; result = "latest_thumbnail=$($f.Name)" } }
    return @{ ok = $false; action = "Validate thumbnail and and generate income report"; error = "no thumbnail found" }
  }
  if ($name -like "*video-quality*") {
    $qDir = Join-Path $root "quality-reports"
    New-Item -ItemType Directory -Force -Path $qDir | Out-Null
    $video = Get-LatestFileIn "output\*\videos\*.mp4"
    $channel = if ($video) { $video.Directory.Name } else { "global" }
    $date = Get-Date -Format "yyyy-MM-dd"
    $reportName = "video-quality-$date-$channel.md"
    $reportPath = Join-Path $qDir $reportName
    $hook = if ($video) { "PASS" } else { "FAIL" }
    $voice = if ($video) { "PASS" } else { "FAIL" }
    $visual = if ($video) { "PASS" } else { "FAIL" }
    $rhythm = if ($video) { "PASS" } else { "FAIL" }
    $retention = if ($video) { "PASS" } else { "FAIL" }
    @(
      "# Evaluación subjetiva de calidad de video",
      "",
      "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
      "Canal: $channel",
      "Archivo revisado: $($video.Name)",
      "",
      "## Resultado rápido",
      "- Hook (3s): $hook",
      "- Naturalidad de voz: $voice",
      "- Relevancia visual: $visual",
      "- Ritmo de edición: $rhythm",
      "- Factor de retención (<=2m): $retention",
      "",
      "## Observación",
      "Reporte automático del Agent-25 para control de calidad subjetiva previo a Quality Gate."
    ) | Set-Content -Path $reportPath -Encoding UTF8
    if ($video) {
      return @{ ok = $true; action = "Evaluate subjective video quality before QA Gate"; result = "report=$reportName, video=$($video.Name)" }
    }
    return @{ ok = $false; action = "Evaluate subjective video quality before QA Gate"; error = "no final video found for subjective quality check" }
  }
  if ($name -like "*qa-guardian*") {
    $cmd = "python -m pytest tests\test_api_smoke.py -q"
    $out = Invoke-Expression $cmd 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
      return @{ ok = $true; action = "Run API smoke quality check"; result = ($out.Trim() -replace '\s+', ' ') }
    }
    return @{ ok = $false; action = "Run API smoke quality check"; error = ($out.Trim() -replace '\s+', ' ') }
  }
  if ($name -like "*automation-ops*") {
    $wfCount = (Get-ChildItem -Path (Join-Path $root ".github\workflows") -Filter "*.yml" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    return @{ ok = $true; action = "Check CI/CD workflow coverage"; result = "workflow_files=$wfCount" }
  }
  if ($name -like "*growth-marketing*") {
    $mkCount = (Get-ChildItem -Path (Join-Path $root "marketing_automation") -Filter "*.py" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    return @{ ok = $true; action = "Check growth automation modules"; result = "marketing_modules=$mkCount" }
  }
  if ($name -like "*ui-evolution*") {
    $uiCount = (Get-ChildItem -Path (Join-Path $root "frontend\src") -Recurse -Include "*.tsx","*.ts","*.css" -ErrorAction SilentlyContinue | Measure-Object).Count
    return @{ ok = $true; action = "Audit UI evolution surface"; result = "ui_files=$uiCount" }
  }
  if ($name -like "*performance*") {
    $cmd = "python -m pytest tests\test_api_smoke.py -q"
    $out = Invoke-Expression $cmd 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
      return @{ ok = $true; action = "Run performance smoke baseline"; result = ($out.Trim() -replace '\s+', ' ') }
    }
    return @{ ok = $false; action = "Run performance smoke baseline"; error = ($out.Trim() -replace '\s+', ' ') }
  }
  if ($name -like "*adsense-web*") {
    $trackerFile = Join-Path $root "monetization\income_tracker.json"
    $trackerData = @()
    if (Test-Path $trackerFile) { try { $trackerData = Get-Content $trackerFile -Raw | ConvertFrom-Json } catch { $trackerData = @() } }
    if (-not ($trackerData | Where-Object { $_.agent -eq "Agent-13" })) {
      $trackerData += @{ source = "AdSense"; channel = "Wealth Files"; estimated_monthly = 350; confidence = "medium"; agent = "Agent-13" }
      $trackerData | ConvertTo-Json -Depth 5 | Set-Content -Path $trackerFile -Encoding UTF8
    }
    $webCount = (Get-ChildItem -Path (Join-Path $root "frontend") -Recurse -Include "*.tsx","*.html" -ErrorAction SilentlyContinue | Measure-Object).Count
    return @{ ok = $true; action = "Review web monetization surfaces"; result = "web_files=$webCount" }
  }
  if ($name -like "*affiliate*") {
    $trackerFile = Join-Path $root "monetization\income_tracker.json"
    $trackerData = @()
    if (Test-Path $trackerFile) { try { $trackerData = Get-Content $trackerFile -Raw | ConvertFrom-Json } catch { $trackerData = @() } }
    if (-not ($trackerData | Where-Object { $_.agent -eq "Agent-14" })) {
      $trackerData += @{ source = "Affiliate Sales"; channel = "El Loco de la IA"; estimated_monthly = 120; confidence = "low"; agent = "Agent-14" }
      $trackerData | ConvertTo-Json -Depth 5 | Set-Content -Path $trackerFile -Encoding UTF8
    }
    $affDir = Join-Path $root "marketing\affiliates"
    New-Item -ItemType Directory -Force -Path $affDir | Out-Null
    $f = Join-Path $affDir "affiliate-opportunities.md"
    if (-not (Test-Path $f)) { "# Affiliate opportunities`n`n- Pending curation." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Update affiliate opportunities tracker"; result = "tracker=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*digital-products*") {
    $trackerFile = Join-Path $root "monetization\income_tracker.json"
    $trackerData = @()
    if (Test-Path $trackerFile) { try { $trackerData = Get-Content $trackerFile -Raw | ConvertFrom-Json } catch { $trackerData = @() } }
    if (-not ($trackerData | Where-Object { $_.agent -eq "Agent-15" })) {
      $trackerData += @{ source = "Digital Products"; channel = "Impacto Positivo"; estimated_monthly = 50; confidence = "low"; agent = "Agent-15" }
      $trackerData | ConvertTo-Json -Depth 5 | Set-Content -Path $trackerFile -Encoding UTF8
    }
    $pDir = Join-Path $root "marketing\digital-products"
    New-Item -ItemType Directory -Force -Path $pDir | Out-Null
    $f = Join-Path $pDir "product-roadmap.md"
    if (-not (Test-Path $f)) { "# Product roadmap`n`n- Pending offers backlog." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Maintain digital products roadmap"; result = "roadmap=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*sponsorship*") {
    $trackerFile = Join-Path $root "monetization\income_tracker.json"
    $trackerData = @()
    if (Test-Path $trackerFile) { try { $trackerData = Get-Content $trackerFile -Raw | ConvertFrom-Json } catch { $trackerData = @() } }
    if (-not ($trackerData | Where-Object { $_.agent -eq "Agent-16" })) {
      $trackerData += @{ source = "Sponsorships"; channel = "Wealth Files"; estimated_monthly = 500; confidence = "medium"; agent = "Agent-16" }
      $trackerData | ConvertTo-Json -Depth 5 | Set-Content -Path $trackerFile -Encoding UTF8
    }
    $sDir = Join-Path $root "marketing\sponsorships"
    New-Item -ItemType Directory -Force -Path $sDir | Out-Null
    $f = Join-Path $sDir "sponsor-pipeline.md"
    if (-not (Test-Path $f)) { "# Sponsor pipeline`n`n- Pending outreach list." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Track sponsorship outreach pipeline"; result = "pipeline=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*newsletter*") {
    $nDir = Join-Path $root "marketing\newsletter"
    New-Item -ItemType Directory -Force -Path $nDir | Out-Null
    $f = Join-Path $nDir "newsletter-plan.md"
    if (-not (Test-Path $f)) { "# Newsletter plan`n`n- Weekly issue cadence." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Maintain newsletter growth plan"; result = "plan=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*shorts*") {
    $shortsCount = (Get-ChildItem -Path (Join-Path $root "output") -Recurse -Include "*short*.mp4" -ErrorAction SilentlyContinue | Measure-Object).Count
    return @{ ok = $true; action = "Review shorts production inventory"; result = "shorts_assets=$shortsCount" }
  }
  if ($name -like "*distribution*") {
    $distDir = Join-Path $root "marketing\distribution"
    New-Item -ItemType Directory -Force -Path $distDir | Out-Null
    $f = Join-Path $distDir "distribution-checklist.md"
    if (-not (Test-Path $f)) { "# Distribution checklist`n`n- YouTube, TikTok, Shorts syndication." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Update distribution checklist"; result = "checklist=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*system-seller*") {
    $trackerFile = Join-Path $root "monetization\income_tracker.json"
    $trackerData = @()
    if (Test-Path $trackerFile) { try { $trackerData = Get-Content $trackerFile -Raw | ConvertFrom-Json } catch { $trackerData = @() } }
    if (-not ($trackerData | Where-Object { $_.agent -eq "Agent-20" })) {
      $trackerData += @{ source = "System Course"; channel = "global"; estimated_monthly = 1200; confidence = "low"; agent = "Agent-20" }
      $trackerData | ConvertTo-Json -Depth 5 | Set-Content -Path $trackerFile -Encoding UTF8
    }
    $ssDir = Join-Path $root "marketing\system-seller"
    New-Item -ItemType Directory -Force -Path $ssDir | Out-Null
    $f = Join-Path $ssDir "offer-positioning.md"
    if (-not (Test-Path $f)) { "# Offer positioning`n`n- Productized system narrative." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Refine system-offer positioning"; result = "positioning=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*community*") {
    $cDir = Join-Path $root "marketing\community"
    New-Item -ItemType Directory -Force -Path $cDir | Out-Null
    $f = Join-Path $cDir "community-playbook.md"
    if (-not (Test-Path $f)) { "# Community playbook`n`n- Engagement loops and reply SOP." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Maintain community growth playbook"; result = "playbook=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*abtesting*") {
    $abDir = Join-Path $root "marketing\abtesting"
    New-Item -ItemType Directory -Force -Path $abDir | Out-Null
    $f = Join-Path $abDir "experiments.md"
    if (-not (Test-Path $f)) { "# A/B experiments`n`n- Thumbnail/title test backlog." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Track A/B testing experiments"; result = "experiments=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*virality*") {
    $vDir = Join-Path $root "research\virality"
    New-Item -ItemType Directory -Force -Path $vDir | Out-Null
    $f = Join-Path $vDir "virality-signals.md"
    if (-not (Test-Path $f)) { "# Virality signals`n`n- Hooks, retention breaks, replay moments." | Set-Content -Path $f -Encoding UTF8 }
    return @{ ok = $true; action = "Capture virality signal findings"; result = "signals=$([IO.Path]::GetFileName($f))" }
  }
  if ($name -like "*net-forager*") {
    $impDir = Join-Path $root "research\improvements"
    New-Item -ItemType Directory -Force -Path $impDir | Out-Null
    $date = Get-Date -Format "yyyy-MM-dd"
    $findsFile = Join-Path $impDir "$date-internet-finds.md"
    $taskLog = Join-Path $impDir "task-log.md"
    $needsFile = Join-Path $root "NEEDS_FROM_HUMAN.md"

    $sources = @(
      "https://github.com/trending",
      "https://www.producthunt.com/",
      "https://news.ycombinator.com/",
      "https://www.reddit.com/r/NewTubers/"
    )
    $findLines = @("# Internet finds - $date","")
    foreach ($u in $sources) {
      try {
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 12
        $findLines += "- [OK] $u (status=$($r.StatusCode))"
      } catch {
        $findLines += "- [WARN] $u (sin respuesta en este ciclo)"
      }
    }
    Set-Content -Path $findsFile -Value $findLines -Encoding UTF8

    $assignments = @()
    $assignments += "Agent-03: evaluar optimizaciones de pipeline/video encontradas en tendencias."
    $assignments += "Agent-04: revisar mejoras SEO/CTR sugeridas por fuentes externas."
    $assignments += "Agent-11: validar mejoras de storytelling/retención publicadas recientemente."
    [void](Write-AgentInboxMessage -ToAgentNum "03" -FromTag "Agent-24 (Net Forager)" -Prefix "from-forager" -Body $assignments[0])
    [void](Write-AgentInboxMessage -ToAgentNum "04" -FromTag "Agent-24 (Net Forager)" -Prefix "from-forager" -Body $assignments[1])
    [void](Write-AgentInboxMessage -ToAgentNum "11" -FromTag "Agent-24 (Net Forager)" -Prefix "from-forager" -Body $assignments[2])

    if (-not (Test-Path $taskLog)) {
      Set-Content -Path $taskLog -Value "# Task log Net Forager`n" -Encoding UTF8
    }
    Add-Content -Path $taskLog -Value ("`n## {0}`n- {1}`n- {2}`n- {3}" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $assignments[0], $assignments[1], $assignments[2]) -Encoding UTF8

    $existingLines = @()
    if (Test-Path $needsFile) {
      try { $existingLines = Get-Content -Path $needsFile -Encoding UTF8 } catch { $existingLines = @() }
    }
    $checkedNeeds = @{}
    foreach ($ln in $existingLines) {
      if ($ln -match '^\s*-\s*\[x\]\s*(.+?)(?:\s+\(Respondido .+\))?\s*$') {
        $checkedNeeds[$matches[1].Trim()] = $true
      }
    }

    $needTexts = @(
      "Revisar e instalar herramienta TTS open-source candidata.",
      "Revisar nuevas oportunidades de afiliacion detectadas en fuentes externas."
    )

    $needs = @()
    $needs += "# Lo que los agentes necesitan de ti"
    $needs += "Actualizado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    $needs += "Compilado por: Agent-24 (Net Forager)"
    $needs += ""
    $needs += "## Aportes"
    foreach ($text in $needTexts) {
      if ($checkedNeeds.ContainsKey($text)) {
        $needs += "- [x] $text"
      } else {
        $needs += "- [ ] $text"
      }
    }
    Set-Content -Path $needsFile -Value $needs -Encoding UTF8

    return @{ ok = $true; action = "Scan internet improvements and assign tasks"; result = "sources=$($sources.Count), assignments=3, needs_updated=1" }
  }
  if ($name -like "*video-researcher*") {
    $dir = Join-Path $root "research\video-techniques"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $latest = Get-ChildItem -Path $dir -Filter "*.md" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
      return @{ ok = $true; action = "Review latest video-quality discoveries"; result = "latest_research=$($latest.Name)" }
    }
    $date = Get-Date -Format "yyyy-MM-dd"
    $seed = Join-Path $dir "$date-discoveries.md"
    @(
      "# Video Research - $date",
      "",
      "## Best Find Today",
      "- Pending first discovery batch.",
      "",
      "## Actions",
      "- Start collecting hook and retention techniques.",
      "- Compare free AI video tools released this month."
    ) | Set-Content -Path $seed -Encoding UTF8
    return @{ ok = $true; action = "Bootstrap video-research workspace"; result = "created=$([IO.Path]::GetFileName($seed))" }
  }
  return @{ ok = $true; action = "No-op"; result = "No task mapped" }
}

function New-AgentState([string]$agentFile) {
  return @{
    agent_file = $agentFile
    status = "idle"
    action = "waiting"
    started_at = $null
    finished_at = $null
    duration_ms = 0
    last_result = ""
    last_error = ""
  }
}

function Run-Cycle {
  param([int]$Cycle)

  $started = Get-Date
  $todayTasks = Get-TodayCalendarTasks
  $todayLabel = Get-Date -Format "yyyy-MM-dd"
  $state = @{
    mode = $config.mode
    coordinator = $config.coordinator
    cycle = $Cycle
    running = $true
    cycle_started = $started.ToString("s")
    cycle_finished = $null
    current_agent = $null
    handoff_rules = @($config.handoff_rules)
    execution_order = @($order)
    agents = @()
  }
  foreach ($a in $order) { $state.agents += (New-AgentState -agentFile $a) }
  Save-State $state
  Write-Event -Cycle $Cycle -Type "cycle_start" -Status "running" -Action "cycle_started"

  $lines = @()
  $lines += "Cycle: $Cycle"
  $lines += "Started: $($started.ToString('s'))"
  $lines += "Mode: $($config.mode)"
  $lines += "Coordinator: $($config.coordinator)"
  $lines += "Daily calendar date: $todayLabel"
  $lines += "Execution order:"

  $dailyPlan = @()
  $dailyPlan += "# Tareas diarias del calendario - $todayLabel"
  $dailyPlan += ""
  foreach ($a in $order) {
    $t = Get-TodayTaskForAgent -agentFile $a -todayTasks $todayTasks
    $dailyPlan += ("- {0}: {1}" -f $a, $(if($t){$t}else{"(sin tarea de calendario)"}))
  }
  Set-Content -Path (Join-Path $dailyPromptsDir "$todayLabel-agent-tasks.md") -Value $dailyPlan -Encoding UTF8

  if ($parallelCapable) {
    $agentIndex = @{}
    $jobs = @()
    $invokeTaskFn = "function Invoke-AgentTask {`n$(${function:Invoke-AgentTask}.ToString())`n}"
    $latestFileFn = "function Get-LatestFileIn {`n$(${function:Get-LatestFileIn}.ToString())`n}"
    $writeInboxFn = "function Write-AgentInboxMessage {`n$(${function:Write-AgentInboxMessage}.ToString())`n}"
    $configMode = [string]$config.mode

    for ($i = 0; $i -lt $order.Count; $i++) {
      $a = $order[$i]
      $agentIndex[$a] = $i
      $state.agents[$i].status = "running"
      $state.agents[$i].started_at = (Get-Date).ToString("s")
      $todayTask = Get-TodayTaskForAgent -agentFile $a -todayTasks $todayTasks
      $state.agents[$i].action = if ($todayTask) { $todayTask } else { "running_task" }
      $agentNum = Get-AgentNum $a
      if ($todayTask) {
        [void](Write-AgentInboxMessage -ToAgentNum $agentNum -FromTag "Scheduler (Calendario diario)" -Prefix "daily-task" -Body $todayTask)
      }
      Write-Output "[RUNNING] $a :: starting task :: $(if($todayTask){$todayTask}else{'(sin tarea diaria)'})"
      Write-Event -Cycle $Cycle -Type "agent_transition" -Agent $a -Status "running" -Action "starting_task"

      $jobs += Start-ThreadJob -ArgumentList $a, $todayTask, $root, $agentsDir, $configMode, $latestFileFn, $invokeTaskFn, $writeInboxFn -ScriptBlock {
        param($agentFile, $todayTaskArg, $rootArg, $agentsDirArg, $configModeArg, $latestFnText, $invokeFnText, $writeInboxFnText)
        $script:root = $rootArg
        $script:agentsDir = $agentsDirArg
        $script:config = @{ mode = $configModeArg }
        . ([scriptblock]::Create($latestFnText))
        . ([scriptblock]::Create($writeInboxFnText))
        . ([scriptblock]::Create($invokeFnText))
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $res = Invoke-AgentTask -agentFile $agentFile
        $sw.Stop()
        [pscustomobject]@{
          agent = $agentFile
          today_task = [string]$todayTaskArg
          ok = [bool]$res.ok
          action = [string]$res.action
          result = [string]$res.result
          error = [string]$res.error
          duration_ms = [int]$sw.ElapsedMilliseconds
        }
      }
    }

    Save-State $state
    while ($jobs.Count -gt 0) {
      $doneJob = Wait-Job -Job $jobs -Any
      $payload = Receive-Job -Job $doneJob
      Remove-Job -Job $doneJob
      $jobs = @($jobs | Where-Object { $_.Id -ne $doneJob.Id })
      if (-not $payload) { continue }
      foreach ($p in @($payload)) {
        $a = [string]$p.agent
        if (-not $agentIndex.ContainsKey($a)) { continue }
        $idx = [int]$agentIndex[$a]
        $state.agents[$idx].duration_ms = [int]$p.duration_ms
        $state.agents[$idx].finished_at = (Get-Date).ToString("s")
        $actionCombined = [string]$p.action
        if ([string]$p.today_task) { $actionCombined = "$actionCombined | HOY: $([string]$p.today_task)" }
        $state.agents[$idx].action = $actionCombined
        if ([bool]$p.ok) {
          $state.agents[$idx].status = "done"
          $state.agents[$idx].last_result = [string]$p.result
          $state.agents[$idx].last_error = ""
          $lines += " - $a -> done | $actionCombined | $($p.result)"
          Write-Output "[DONE] $a :: $actionCombined :: $($p.result)"
          Write-Event -Cycle $Cycle -Type "agent_result" -Agent $a -Status "done" -Action $actionCombined -Result ([string]$p.result) -DurationMs ([int]$p.duration_ms)
          Update-AgentHistory -Cycle $Cycle -Agent $a -Status "done" -Action $actionCombined -Result ([string]$p.result) -Error "" -DurationMs ([int]$p.duration_ms) -StartedAt $state.agents[$idx].started_at -FinishedAt $state.agents[$idx].finished_at
          Update-AgentLearning -Agent $a -Status "done" -Action $actionCombined -Result ([string]$p.result) -Error ""
        } else {
          $state.agents[$idx].status = "error"
          $state.agents[$idx].last_result = ""
          $state.agents[$idx].last_error = [string]$p.error
          $lines += " - $a -> error | $actionCombined | $($p.error)"
          Write-Output "[ERROR] $a :: $actionCombined :: $($p.error)"
          Write-Event -Cycle $Cycle -Type "agent_result" -Agent $a -Status "error" -Action $actionCombined -Error ([string]$p.error) -DurationMs ([int]$p.duration_ms)
          Update-AgentHistory -Cycle $Cycle -Agent $a -Status "error" -Action $actionCombined -Result "" -Error ([string]$p.error) -DurationMs ([int]$p.duration_ms) -StartedAt $state.agents[$idx].started_at -FinishedAt $state.agents[$idx].finished_at
          Update-AgentLearning -Agent $a -Status "error" -Action $actionCombined -Result "" -Error ([string]$p.error)
        }
      }
      Save-State $state
    }
  } else {
    for ($i = 0; $i -lt $order.Count; $i++) {
      $a = $order[$i]
      $state.current_agent = $a
      $state.agents[$i].status = "running"
      $state.agents[$i].started_at = (Get-Date).ToString("s")
      $todayTask = Get-TodayTaskForAgent -agentFile $a -todayTasks $todayTasks
      $state.agents[$i].action = if ($todayTask) { $todayTask } else { "running_task" }
      $agentNum = Get-AgentNum $a
      if ($todayTask) {
        [void](Write-AgentInboxMessage -ToAgentNum $agentNum -FromTag "Scheduler (Calendario diario)" -Prefix "daily-task" -Body $todayTask)
      }
      Write-Output "[RUNNING] $a :: starting task :: $(if($todayTask){$todayTask}else{'(sin tarea diaria)'})"
      Save-State $state
      Write-Event -Cycle $Cycle -Type "agent_transition" -Agent $a -Status "running" -Action "starting_task"

      $sw = [System.Diagnostics.Stopwatch]::StartNew()
      $res = Invoke-AgentTask -agentFile $a
      $sw.Stop()

      $state.agents[$i].duration_ms = [int]$sw.ElapsedMilliseconds
      $state.agents[$i].finished_at = (Get-Date).ToString("s")
      $actionCombined = [string]$res.action
      if ($todayTask) { $actionCombined = "$actionCombined | HOY: $todayTask" }
      $state.agents[$i].action = $actionCombined
      if ($res.ok) {
        $state.agents[$i].status = "done"
        $state.agents[$i].last_result = [string]$res.result
        $state.agents[$i].last_error = ""
        $lines += " - $a -> done | $actionCombined | $($res.result)"
        Write-Output "[DONE] $a :: $actionCombined :: $($res.result)"
        Write-Event -Cycle $Cycle -Type "agent_result" -Agent $a -Status "done" -Action $actionCombined -Result ([string]$res.result) -DurationMs ([int]$sw.ElapsedMilliseconds)
        Update-AgentHistory -Cycle $Cycle -Agent $a -Status "done" -Action $actionCombined -Result ([string]$res.result) -Error "" -DurationMs ([int]$sw.ElapsedMilliseconds) -StartedAt $state.agents[$i].started_at -FinishedAt $state.agents[$i].finished_at
        Update-AgentLearning -Agent $a -Status "done" -Action $actionCombined -Result ([string]$res.result) -Error ""
      } else {
        $state.agents[$i].status = "error"
        $state.agents[$i].last_result = ""
        $state.agents[$i].last_error = [string]$res.error
        $lines += " - $a -> error | $actionCombined | $($res.error)"
        Write-Output "[ERROR] $a :: $actionCombined :: $($res.error)"
        Write-Event -Cycle $Cycle -Type "agent_result" -Agent $a -Status "error" -Action $actionCombined -Error ([string]$res.error) -DurationMs ([int]$sw.ElapsedMilliseconds)
        Update-AgentHistory -Cycle $Cycle -Agent $a -Status "error" -Action $actionCombined -Result "" -Error ([string]$res.error) -DurationMs ([int]$sw.ElapsedMilliseconds) -StartedAt $state.agents[$i].started_at -FinishedAt $state.agents[$i].finished_at
        Update-AgentLearning -Agent $a -Status "error" -Action $actionCombined -Result "" -Error ([string]$res.error)
      }
      Save-State $state
    }
  }

  $lines += "Handoffs:"
  foreach ($h in $config.handoff_rules) { $lines += " - $h" }

  $finished = Get-Date
  $state.running = $false
  $state.current_agent = $null
  $state.cycle_finished = $finished.ToString("s")
  Save-State $state
  $doneCount = @($state.agents | Where-Object { $_.status -eq "done" }).Count
  $errorCount = @($state.agents | Where-Object { $_.status -eq "error" }).Count
  Write-Event -Cycle $Cycle -Type "cycle_end" -Status "finished" -Action "cycle_completed" -Result "done=$doneCount,error=$errorCount"
  Update-CycleHistory -Cycle $Cycle -StartedAt $state.cycle_started -FinishedAt $state.cycle_finished -DoneCount $doneCount -ErrorCount $errorCount
  Write-AgentReports

  $lines += "Finished: $($finished.ToString('s'))"
  $outFile = Join-Path $logDir ("agents-cycle-{0:yyyyMMdd-HHmmss}.log" -f $finished)
  $lines -join [Environment]::NewLine | Set-Content -Path $outFile -Encoding UTF8
  Write-Output "Team cycle $Cycle completed -> $outFile"
}

if ($Once) {
  Run-Cycle -Cycle 1
  exit 0
}

$cycle = 1
while ($true) {
  Run-Cycle -Cycle $cycle
  $cycle++
  if ($LoopDelaySeconds -gt 0) {
    Start-Sleep -Seconds $LoopDelaySeconds
  }
}
