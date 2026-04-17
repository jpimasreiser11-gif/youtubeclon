param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CopilotArgs
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$bridge = Join-Path $root "tools\pixel_agents\copilot_hook_bridge.py"
$session = [guid]::NewGuid().ToString("N")

python $bridge session-start --session-id $session --cwd (Get-Location).Path | Out-Null
try {
  if ($CopilotArgs.Count -gt 0) {
    & copilot @CopilotArgs
  } else {
    & copilot
  }
  $exitCode = $LASTEXITCODE
  python $bridge stop --session-id $session | Out-Null
  python $bridge session-end --session-id $session --reason "exit" | Out-Null
  exit $exitCode
}
catch {
  python $bridge session-end --session-id $session --reason "error" | Out-Null
  throw
}
