[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$CardOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "missing .venv, run scripts\setup.ps1 first"
}

$version = & $python -m PyInstaller --version
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller not installed: python -m pip install -r requirements-build.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
}
Write-Host "PyInstaller $version"

if ($Clean -and (Test-Path (Join-Path $root "build"))) {
    Remove-Item -Recurse -Force (Join-Path $root "build")
}
if (Test-Path (Join-Path $root "dist")) {
    foreach ($name in @("Dota2Coach", "Dota2Coach-Card")) {
        $target = Join-Path $root "dist\$name"
        if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    }
}

$common = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--icon", "data\app.ico",
    "--version-file", "packaging\version_info.txt",
    "--onedir",
    "--paths", (Join-Path $root "src"),
    "--add-data", "config.toml;.",
    "--add-data", "docs;docs",
    "--exclude-module", "faster_whisper",
    "--exclude-module", "ctranslate2",
    "--exclude-module", "torch",
    "--exclude-module", "huggingface_hub",
    "--exclude-module", "tokenizers"
)

function Build-Target([string]$name, [string]$entry) {
    Write-Host "==> building $name"
    & $python -m PyInstaller @common --name $name $entry
    if ($LASTEXITCODE -ne 0) { throw "build failed: $name" }
    $target = Join-Path $root "dist\$name"
    if (-not (Test-Path (Join-Path $target "config.toml"))) {
        Copy-Item (Join-Path $root "config.toml") $target
    }
    Copy-Item (Join-Path $root "data") $target -Recurse -Force
    Copy-Item (Join-Path $root "docs\gsi.cfg") $target -Force
    Copy-Item (Join-Path $root "README.md") $target -Force
    Write-Host "    -> $target"
}

Build-Target "Dota2Coach" (Join-Path $root "packaging\entry_panel.py")
if (-not $CardOnly) {
    Build-Target "Dota2Coach-Card" (Join-Path $root "packaging\entry_card.py")
}

Write-Host ""
Write-Host "done. run dist\Dota2Coach\Dota2Coach.exe"
Write-Host "logs and config.toml live next to the exe; the settings page writes them back."
