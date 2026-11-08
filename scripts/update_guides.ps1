# Refresh the local guide knowledge base from Bilibili.
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\update_guides.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\update_guides.ps1 -Asr base

param(
    [string]$Asr = "off",
    [switch]$AllHeroes,
    [int]$PerHero = 2,
    [int]$HeroMinPlay = 1000,
    [int]$Limit = 6,
    [switch]$NoLlm
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "venv not found. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONPATH = "src"
$logDir = Join-Path (Get-Location) "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "guides.log"

if ($AllHeroes) {
    $cmd = @("scripts\fetch_guides.py", "--asr", $Asr, "--all-heroes", "--per-hero-tips", "$PerHero", "--hero-min-play", "$HeroMinPlay")
} else {
    $cmd = @("scripts\fetch_guides.py", "--asr", $Asr, "--limit", "$Limit")
}
if ($NoLlm) { $cmd += "--no-llm" }

Write-Host ("Running: " + $python + " " + ($cmd -join " "))
& $python @cmd 2>&1 | Tee-Object -FilePath $logFile -Append
exit $LASTEXITCODE
