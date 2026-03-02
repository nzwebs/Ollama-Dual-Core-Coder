# DUAL CORE - Parallel Ollama Coding Engine (PowerShell launcher)

Write-Host ""
Write-Host "  ==========================================================" -ForegroundColor Cyan
Write-Host "    DUAL CORE - Parallel Ollama Coding Engine" -ForegroundColor Cyan
Write-Host "  ==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "    Running two AI models simultaneously for better code..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "  Activating Python 3.13.12 environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Verify Python
Write-Host "  Verifying Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  Using: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check dependencies
Write-Host "  Checking dependencies..." -ForegroundColor Yellow
python -c "import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to install requirements" -ForegroundColor Red
        Read-Host "  Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "  Make sure you have TWO Ollama servers running:" -ForegroundColor Yellow
Write-Host "    Terminal 1: ollama serve" -ForegroundColor Gray
Write-Host "    Terminal 2: OLLAMA_HOST=0.0.0.0:11435 ollama serve" -ForegroundColor Gray
Write-Host ""

Write-Host "  Launching DUAL CORE..." -ForegroundColor Green
Write-Host ""

# Launch app
python app.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Application failed to start" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}
