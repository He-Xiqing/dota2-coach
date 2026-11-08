# Refresh the offline data files used by the coach card.
# Safe to run any time; every step overwrites only its own data file.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\update_data.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\update_data.ps1 -SkipIcons -Guides
#
# Notes:
#   - Icons need internet and take a few minutes (127 heroes, 2 images each).
#   - Popularity and matchups use OpenDota over plain HTTP; no API key needed,
#     but they throttle (about 1 request/second).
#   - Item names are read from the local Dota 2 VPK (no internet).
#   - Guides need DEEPSEEK_API_KEY in .env and cost one LLM call per video.

[CmdletBinding()]
param(
    [switch]$SkipIcons,
    [switch]$SkipMatchups,
    [switch]$Guides,
    [switch]$Asr,
    [int]$Limit = 4
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Python venv not found: $Python"
    Write-Host "Run scripts\setup.ps1 first."
    exit 1
}

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null
$Log = Join-Path $Root "logs\update_data.log"

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    $stamp = Get-Date -Format "HH:mm:ss"
    Write-Host ""
    Write-Host "== [$stamp] $Name =="
    Add-Content -Path $Log -Value "[$stamp] $Name"
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) {
            Add-Content -Path $Log -Value "[$stamp] $Name failed (exit $LASTEXITCODE)"
            Write-Host "   step failed, continue with next one"
        }
    } catch {
        Add-Content -Path $Log -Value "[$stamp] $Name error: $_"
        Write-Host "   step error: $_"
    }
}

if (-not $SkipIcons) {
    Invoke-Step "hero icons + Chinese names" {
        powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\fetch_hero_icons.ps1")
    }
} else {
    Write-Host "skip icons"
}

Invoke-Step "hero roles and win rates (OpenDota heroStats)" {
    & $Python (Join-Path $Root "scripts\fetch_hero_stats.py")
}

Invoke-Step "item popularity (OpenDota itemPopularity)" {
    & $Python (Join-Path $Root "scripts\fetch_popularity.py") --force
}

Invoke-Step "item table (local constants)" {
    & $Python (Join-Path $Root "scripts\build_item_table.py")
}

Invoke-Step "item Chinese names (local VPK)" {
    & $Python (Join-Path $Root "scripts\build_item_names.py")
}

if (-not $SkipMatchups) {
    Invoke-Step "matchups (OpenDota, full refresh)" {
        & $Python (Join-Path $Root "scripts\fetch_matchups.py")
    }
} else {
    Write-Host "skip matchups"
}

if ($Guides) {
    $guideArgs = @((Join-Path $Root "scripts\fetch_guides.py"), "--limit", "$Limit")
    if ($Asr) {
        $guideArgs += @("--asr", "base", "--asr-max-videos", "2")
    }
    Invoke-Step "bilibili guides -> data/guides" {
        & $Python $guideArgs
    }
} else {
    Write-Host "skip guides (use -Guides; add -Asr to transcribe audio)"
}

Write-Host ""
Write-Host "done. log: $Log"
