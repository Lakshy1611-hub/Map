$ErrorActionPreference = "Stop"

Write-Host "JARVIS Windows build"
Write-Host "Creating/updating virtual environment..."

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pytest -q
& ".\.venv\Scripts\python.exe" -m compileall -q jarvis main.py
& ".\.venv\Scripts\pyinstaller.exe" --noconfirm --clean jarvis.spec

Write-Host ""
Write-Host "Build complete: dist\JARVIS.exe"
