param(
  [int]$PollSeconds = 2,
  [int]$MaxMinutes = 20,
  [switch]$Follow
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$statePath = Join-Path $root "logs\agents-state.json"
$deadline = (Get-Date).AddMinutes($MaxMinutes)

function Read-State {
  if (-not (Test-Path $statePath)) {
    return $null
  }
  try {
    return (Get-Content $statePath -Raw -Encoding UTF8 | ConvertFrom-Json)
  } catch {
    return $null
  }
}

function Agent-Signature($agent) {
  return "{0}|{1}|{2}|{3}|{4}|{5}" -f $agent.agent_file, $agent.status, $agent.action, $agent.last_result, $agent.last_error, $agent.finished_at
}

Write-Output "=== AGENTS LIVE MONITOR ==="
Write-Output ("State file: {0}" -f $statePath)
Write-Output ("Polling every {0}s" -f $PollSeconds)
Write-Output ""

$lastCycle = $null
$lastRunning = $null
$reportedFinalCycle = $null
$seen = @{}

while ((Get-Date) -lt $deadline) {
  $state = Read-State
  if ($null -eq $state) {
    Start-Sleep -Seconds $PollSeconds
    continue
  }

  if ($lastCycle -ne $state.cycle) {
    Write-Output ("--- Cycle {0} ---" -f $state.cycle)
    $lastCycle = $state.cycle
    $seen = @{}
  }

  if ($lastRunning -ne $state.running) {
    if ($state.running) {
      Write-Output ("[{0}] TEAM STATUS: RUNNING" -f (Get-Date).ToString("HH:mm:ss"))
    } else {
      Write-Output ("[{0}] TEAM STATUS: IDLE" -f (Get-Date).ToString("HH:mm:ss"))
    }
    $lastRunning = $state.running
  }

  foreach ($agent in $state.agents) {
    $sig = Agent-Signature $agent
    if (-not $seen.ContainsKey($agent.agent_file) -or $seen[$agent.agent_file] -ne $sig) {
      $seen[$agent.agent_file] = $sig
      $detail = if ($agent.status -eq "done") { $agent.last_result } elseif ($agent.status -eq "error") { $agent.last_error } else { "in progress" }
      Write-Output ("[{0}] {1} | {2} | {3} | {4} | {5}ms" -f (Get-Date).ToString("HH:mm:ss"), $agent.agent_file, $agent.status.ToUpper(), $agent.action, $detail, $agent.duration_ms)
    }
  }

  if (-not $state.running -and $reportedFinalCycle -ne $state.cycle) {
    $reportedFinalCycle = $state.cycle
    $doneCount = @($state.agents | Where-Object { $_.status -eq "done" }).Count
    $errorCount = @($state.agents | Where-Object { $_.status -eq "error" }).Count
    Write-Output ""
    Write-Output ("=== FINAL CYCLE {0} ===" -f $state.cycle)
    Write-Output ("Started:  {0}" -f $state.cycle_started)
    Write-Output ("Finished: {0}" -f $state.cycle_finished)
    Write-Output ("Result:   done={0}, error={1}" -f $doneCount, $errorCount)
    Write-Output ""
    Write-Output "Per-agent conclusions:"
    foreach ($agent in $state.agents) {
      if ($agent.status -eq "done") {
        Write-Output (" - {0}: OK | {1} | {2}" -f $agent.agent_file, $agent.action, $agent.last_result)
      } elseif ($agent.status -eq "error") {
        Write-Output (" - {0}: ERROR | {1} | {2}" -f $agent.agent_file, $agent.action, $agent.last_error)
      } else {
        Write-Output (" - {0}: {1} | {2}" -f $agent.agent_file, $agent.status.ToUpper(), $agent.action)
      }
    }
    Write-Output ""
    if (-not $Follow) {
      break
    }
  }

  Start-Sleep -Seconds $PollSeconds
}

