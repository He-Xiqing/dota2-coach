[CmdletBinding()]
param(
    [switch]$Probe,
    [switch]$Card,
    [switch]$TestVoice,
    [switch]$TestSound,
    [string]$Config = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "missing .venv, run scripts\setup.ps1 first"
}

$env:PYTHONPATH = Join-Path $root "src"
$env:PYTHONUNBUFFERED = "1"
$env:QT_LOGGING_RULES = "qt.qpa.window=false;qt.qpa.screen=false"

$argsList = @("-m", "dota2coach")
if ($Probe) { $argsList += "--probe" }
if ($Card) { $argsList += "--legacy" }
if ($TestVoice) { $argsList += "--test-voice" }
if ($TestSound) { $argsList += "--test-sound" }
if ($Config) { $argsList += @("--config", $Config) }

& $python @argsList 2>&1 | Tee-Object -FilePath (Join-Path $root "logs\run.log")
