<#
Setup and smoke-test script for Windows (PowerShell).
Runs: create venv, install requirements, build embeddings, start backend, run health and sample analyze, stop backend.

Usage: Run from project root in PowerShell (run as user with rights to create a venv).
  .\setup_all.ps1
#>

$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment..."
if (-Not (Test-Path .\venv)) {
    python -m venv venv
}

$py = Join-Path -Path (Get-Location) -ChildPath 'venv\Scripts\python.exe'
if (-Not (Test-Path $py)) {
    Write-Error "Python executable not found at $py. Ensure Python is installed and on PATH."
    exit 1
}

Write-Host "Upgrading pip and installing requirements..."
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt

Write-Host "Building embeddings (if dataset present)..."
try {
    & $py backend/emb_classifier.py --build
} catch {
    Write-Warning "Embedding build failed or dataset missing: $_"
}

Write-Host "Starting backend server..."
$env:FREE_MODE='1'
$proc = Start-Process -FilePath $py -ArgumentList 'backend/app.py' -NoNewWindow -PassThru

Write-Host "Waiting for /health..."
$url = 'http://127.0.0.1:5000/health'
$max = 30
for ($i = 0; $i -lt $max; $i++) {
    try {
        $r = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 5
        if ($r.status -eq 'ok') { Write-Host "Health OK"; break }
    } catch {
        Start-Sleep -Seconds 1
    }
    if ($i -eq $max-1) { Write-Error "Health check failed after waiting."; break }
}

Write-Host "Running smoke-test (backend/test_request.py)..."
try {
    & $py backend/test_request.py
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        Write-Host "Smoke tests passed (exit 0)."
    } else {
        Write-Warning "Smoke tests failed with exit code $code. See backend/test_request.py output above."
    }
} catch {
    Write-Warning "Failed to run smoke-test: $_"
}

Write-Host "Stopping backend (PID $($proc.Id))..."
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host "Done. You can start the server yourself with:`n  $env:FREE_MODE='1'; .\venv\Scripts\Activate.ps1; python backend/app.py"