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
    "--add-data", "config.example.toml;.",
    "--add-data", "docs;docs",
    "--exclude-module", "faster_whisper",
    "--exclude-module", "ctranslate2",
    "--exclude-module", "torch",
    "--exclude-module", "huggingface_hub",
    "--exclude-module", "tokenizers",
    "--exclude-module", "tkinter",
    "--exclude-module", "pydoc_data",
    "--exclude-module", "setuptools",
    "--exclude-module", "pip",
    "--exclude-module", "pytest",
    "--exclude-module", "IPython"
)

function Build-Target([string]$name, [string]$entry) {
    Write-Host "==> building $name"
    & $python -m PyInstaller @common --name $name $entry
    if ($LASTEXITCODE -ne 0) { throw "build failed: $name" }
    $target = Join-Path $root "dist\$name"
    Copy-Item (Join-Path $root "data") $target -Recurse -Force
    Copy-Item (Join-Path $root "docs\gsi.cfg") $target -Force
    Copy-Item (Join-Path $root "README.md") $target -Force
    Copy-Item (Join-Path $root "README.zh-CN.md") $target -Force
    Copy-Item (Join-Path $root "LICENSE") $target -Force
    Copy-Item (Join-Path $root "RELEASE_NOTES.md") $target -Force
    Copy-Item (Join-Path $root "config.example.toml") $target -Force

    # 裁剪用不到的二进制，保持功能不变
    $prune = @(
        "_internal\cv2\opencv_videoio_ffmpeg*.dll",
        "_internal\cv2\data",
        "_internal\PyQt6\Qt6\bin\opengl32sw.dll",
        "_internal\PyQt6\Qt6\translations",
        "_internal\PyQt6\Qt6\qml",
        "_internal\PyQt6\Qt6\plugins\sqldrivers",
        "_internal\PyQt6\Qt6\plugins\qmltooling",
        "_internal\PyQt6\Qt6\plugins\iconengines",
        "_internal\PyQt6\Qt6\plugins\imageformats\qpdf.*",
        "_internal\PyQt6\Qt6\plugins\imageformats\qtiff.*"
    )
    foreach ($pattern in $prune) {
        Get-ChildItem -Path (Join-Path $target $pattern) -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    # Valve 原始文本只在生成数据时用，运行时不需要
    Get-ChildItem -Path (Join-Path $target "data\*_schinese.txt") -ErrorAction SilentlyContinue | Remove-Item -Force
    Remove-Item (Join-Path $target "data\_items_raw.json") -Force -ErrorAction SilentlyContinue
    Write-Host "    -> $target"
}

Build-Target "Dota2Coach" (Join-Path $root "packaging\entry_panel.py")
if (-not $CardOnly) {
    Build-Target "Dota2Coach-Card" (Join-Path $root "packaging\entry_card.py")
}

Write-Host ""
Write-Host "done. run dist\Dota2Coach\Dota2Coach.exe"
Write-Host "logs and config.toml live next to the exe; the settings page writes them back."
