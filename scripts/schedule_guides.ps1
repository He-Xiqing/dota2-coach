# Register (or remove) a weekly Windows Scheduled Task that refreshes guides.
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\schedule_guides.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\schedule_guides.ps1 -Remove

param(
    [switch]$Remove,
    [string]$Time = "03:00",
    [switch]$Asr
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$taskName = "Dota2Coach-FetchGuides"
if ($Remove) {
    schtasks /Delete /TN $taskName /F 2>$null
    Write-Host "Removed task $taskName"
    exit 0
}

$root = (Get-Location).Path
$scriptPath = Join-Path $root "scripts\update_guides.ps1"
$asrArg = if ($Asr) { " -Asr base" } else { "" }
$command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -AllHeroes$asrArg"

schtasks /Create /TN $taskName /SC WEEKLY /D SUN /ST $Time /TR $command /F
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to register task. Try running as the same user, not elevated." -ForegroundColor Red
    exit 1
}
Write-Host "Task $taskName registered: every Sunday $Time" -ForegroundColor Green
Write-Host "Test now:  schtasks /Run /TN $taskName"
