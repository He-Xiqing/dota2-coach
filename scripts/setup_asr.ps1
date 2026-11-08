# Install optional speech-to-text (faster-whisper) for Bilibili guide videos.
# Run once:  powershell -ExecutionPolicy Bypass -File scripts\setup_asr.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "venv not found. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Installing faster-whisper (Tsinghua mirror) ..."
& $python -m pip install faster-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Check network / mirror." -ForegroundColor Red
    exit 1
}

# huggingface.co is often unreachable from mainland China; use the mirror.
$env:HF_ENDPOINT = "https://hf-mirror.com"
Write-Host "Downloading base model (~145MB) to logs\models ..."
& $python -c "from faster_whisper import WhisperModel; m = WhisperModel('base', device='cpu', compute_type='int8', download_root='logs/models'); print('base model ready')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "model download failed. Try again or set HF_ENDPOINT manually." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done. Now run: python scripts\fetch_guides.py --asr base" -ForegroundColor Green
