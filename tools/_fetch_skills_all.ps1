$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$langs = @("english", "tchinese", "french", "russian", "german", "brazilian", "spanish", "turkish")
foreach ($lang in $langs) {
    Write-Output "== $lang"
    & .\.venv\Scripts\python.exe scripts\fetch_hero_skills.py --language $lang --interval 0.12 2>&1 | Select-Object -Last 2
}
