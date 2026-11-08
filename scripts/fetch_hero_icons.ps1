# Fetch Dota 2 hero icons + portrait cards into data/.
# Run this once from the project root (needs internet):
#   powershell -ExecutionPolicy Bypass -File scripts\fetch_hero_icons.ps1
# Pure ASCII on purpose: Windows PowerShell 5.1 reads non-ASCII .ps1 as ANSI.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = Split-Path -Parent $PSScriptRoot
$iconDir = Join-Path $root 'data\hero_icons'
$cardDir = Join-Path $root 'data\hero_cards'
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
New-Item -ItemType Directory -Force -Path $cardDir | Out-Null

$iconBase = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/icons/'
$cardBase = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/'

Write-Host 'Fetching hero list from dota2.com ...'
# Download to a file first: PS 5.1's Invoke-RestMethod can guess the wrong
# charset and garble the Chinese name_loc field.
$tmpJson = Join-Path $env:TEMP 'dota2_herolist.json'
Invoke-WebRequest -Uri 'https://www.dota2.com/datafeed/herolist?language=schinese' -OutFile $tmpJson -UseBasicParsing -UserAgent 'Mozilla/5.0' -TimeoutSec 60
$response = Get-Content -Path $tmpJson -Raw -Encoding UTF8 | ConvertFrom-Json

# The datafeed wraps everything: {"result":{"data":{"heroes":[...]}}}
$heroes = $null
if ($response.PSObject.Properties.Name -contains 'result') {
    if ($response.result.PSObject.Properties.Name -contains 'data') {
        $heroes = $response.result.data.heroes
    }
}
if (-not $heroes) { $heroes = $response.heroes }
if (-not $heroes) {
    Write-Host 'datafeed shape changed; falling back to OpenDota hero list (English names)'
    Invoke-WebRequest -Uri 'https://api.opendota.com/api/heroes' -OutFile $tmpJson -UseBasicParsing -UserAgent 'Mozilla/5.0' -TimeoutSec 60
    $fallback = Get-Content -Path $tmpJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $heroes = @($fallback | ForEach-Object {
        [pscustomobject]@{ id = $_.id; name = $_.name; name_loc = $_.localized_name }
    })
}
$heroes = @($heroes)
Write-Host ("Heroes in datafeed: " + $heroes.Count)
if ($heroes.Count -lt 50) {
    Write-Host 'ERROR: hero list is too small; aborting before touching data/.'
    exit 1
}

$table = [ordered]@{}
$failedIcons = @()
$failedCards = @()
$done = 0

foreach ($hero in $heroes) {
    $short = $hero.name -replace '^npc_dota_hero_', ''
    $table[[string]$hero.id] = [ordered]@{
        name = [string]$hero.name
        name_loc = [string]$hero.name_loc
        short = [string]$short
    }

    $iconPath = Join-Path $iconDir ($short + '.png')
    if (-not (Test-Path $iconPath)) {
        try {
            Invoke-WebRequest -Uri ($iconBase + $short + '.png') -OutFile $iconPath -UseBasicParsing -UserAgent 'Mozilla/5.0' -TimeoutSec 30
        } catch {
            $failedIcons += $short
            if (Test-Path $iconPath) { Remove-Item $iconPath -Force }
        }
    }

    $cardPath = Join-Path $cardDir ($short + '.png')
    if (-not (Test-Path $cardPath)) {
        try {
            Invoke-WebRequest -Uri ($cardBase + $short + '.png') -OutFile $cardPath -UseBasicParsing -UserAgent 'Mozilla/5.0' -TimeoutSec 30
        } catch {
            $failedCards += $short
            if (Test-Path $cardPath) { Remove-Item $cardPath -Force }
        }
    }

    $done++
    if ($done % 20 -eq 0) { Write-Host ("  " + $done + " / " + $heroes.Count) }
}

$jsonPath = Join-Path $root 'data\heroes.json'
$table | ConvertTo-Json -Depth 4 | Set-Content -Path $jsonPath -Encoding UTF8

$icons = (Get-ChildItem $iconDir -Filter *.png | Measure-Object).Count
$cards = (Get-ChildItem $cardDir -Filter *.png | Measure-Object).Count
Write-Host ''
Write-Host ('Icons : ' + $icons + ' -> ' + $iconDir)
Write-Host ('Cards : ' + $cards + ' -> ' + $cardDir)
Write-Host ('Table : ' + $jsonPath)
if ($failedIcons.Count -gt 0) { Write-Host ('Icon failures (' + $failedIcons.Count + '): ' + ($failedIcons -join ', ')) }
if ($failedCards.Count -gt 0) { Write-Host ('Card failures (' + $failedCards.Count + '): ' + ($failedCards -join ', ')) }
Write-Host 'Done.'
