param(
    [string]$DotaPath = "D:\SteamLibrary\steamapps\common\dota 2 beta"
)

# Copy the GSI config into the Dota 2 install. ASCII only.
# This writes outside the project folder; that is the point.

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "docs\gsi.cfg"

if (-not (Test-Path $source)) {
    throw "Missing $source"
}
if (-not (Test-Path $DotaPath)) {
    throw "Dota 2 folder not found: $DotaPath (edit -DotaPath)"
}

$cfgDir = Join-Path $DotaPath "game\dota\cfg\gamestate_integration"
if (-not (Test-Path $cfgDir)) {
    New-Item -ItemType Directory -Path $cfgDir -Force | Out-Null
    Write-Host "created: $cfgDir"
}

$dest = Join-Path $cfgDir "gamestate_integration_coach.cfg"
Copy-Item -LiteralPath $source -Destination $dest -Force

Write-Host "installed: $dest"
Write-Host ""
Write-Host "Now fully restart Dota 2 (GSI config is read at startup)."
Write-Host "Then run: powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -Probe"
