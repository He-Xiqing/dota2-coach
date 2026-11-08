param(
    [string]$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple",
    [string]$Python = "python"
)

# dota2-coach: create venv and install dependencies.
# ASCII only on purpose: Windows PowerShell 5.1 misreads non-BOM UTF-8 scripts.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== dota2-coach setup =="
Write-Host "project: $root"

$found = Get-Command $Python -ErrorAction SilentlyContinue
if (-not $found) {
    throw "Python not found. Install Python 3.12 from https://www.python.org/downloads/windows/ and tick 'Add python.exe to PATH'."
}

$version = & $Python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to run '$Python --version'. Is it the Microsoft Store stub?"
}
Write-Host "python version: $version"
if ($version -ne "3.12" -and $version -ne "3.11") {
    Write-Warning "Python $version detected. 3.12 is recommended (better wheels for opencv/bettercam)."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "creating virtual environment .venv ..."
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
}
$venvPy = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "upgrading pip ..."
& $venvPy -m pip install --upgrade pip -i $Mirror
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed (network? try another mirror -Mirror <url>)" }

Write-Host "installing core requirements ..."
& $venvPy -m pip install -r requirements-core.txt -i $Mirror
if ($LASTEXITCODE -ne 0) { throw "core requirements failed" }

foreach ($file in @("requirements-vision.txt", "requirements-ui.txt")) {
    Write-Host "installing $file ..."
    & $venvPy -m pip install -r $file -i $Mirror
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$file failed to install. You can retry later: .venv\Scripts\python.exe -m pip install -r $file -i $Mirror"
    }
}

Write-Host ""
Write-Host "Quick check:"
$env:PYTHONPATH = Join-Path $root "src"
& $venvPy -m dota2coach --version

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1) powershell -ExecutionPolicy Bypass -File scripts\copy_gsi.ps1"
Write-Host "  2) powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -Probe"
Write-Host "  3) start Dota 2, play one bot match, then press Ctrl+C in the probe"
