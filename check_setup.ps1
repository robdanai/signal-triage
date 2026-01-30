#!/usr/bin/env pwsh
# Signal Triage - Setup Verification Script
# Checks that everything is configured correctly

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  SIGNAL TRIAGE - SETUP VERIFICATION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: Virtual Environment
Write-Host "[1/7] Checking virtual environment..." -NoNewline
if (Test-Path "venv\Scripts\activate.bat") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "      Create with: python -m venv venv" -ForegroundColor Yellow
    $allGood = $false
}

# Check 2: .env file
Write-Host "[2/7] Checking .env file..." -NoNewline
if (Test-Path ".env") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "      Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "      Created! Edit .env to add API keys if needed." -ForegroundColor Green
}

# Check 3: Requirements
Write-Host "[3/7] Checking Python dependencies..." -NoNewline
if (Test-Path "venv\Lib\site-packages\fastapi") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING" -ForegroundColor Red
    Write-Host "      Install with: venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Yellow
    $allGood = $false
}

# Check 4: Database file (optional)
Write-Host "[4/7] Checking database..." -NoNewline
if (Test-Path "signal_triage.db") {
    Write-Host " EXISTS" -ForegroundColor Green
} else {
    Write-Host " NOT INITIALIZED (will be created on first run)" -ForegroundColor Yellow
}

# Check 5: Logs directory
Write-Host "[5/7] Checking logs directory..." -NoNewline
if (Test-Path "logs") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " CREATING" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "      Created logs directory" -ForegroundColor Green
}

# Check 6: Check if ports are available
Write-Host "[6/7] Checking port availability..." -NoNewline
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port8501 = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue

if ($port8000 -or $port8501) {
    Write-Host " PORTS IN USE" -ForegroundColor Yellow
    if ($port8000) {
        Write-Host "      Port 8000 (API) is already in use" -ForegroundColor Yellow
    }
    if ($port8501) {
        Write-Host "      Port 8501 (Dashboard) is already in use" -ForegroundColor Yellow
    }
    Write-Host "      This might be fine if services are already running" -ForegroundColor Cyan
} else {
    Write-Host " AVAILABLE" -ForegroundColor Green
}

# Check 7: Core files
Write-Host "[7/7] Checking core files..." -NoNewline
$coreFiles = @(
    "signal_triage\analyzer.py",
    "signal_triage\ui\dashboard.py",
    "run_api_server.py",
    "START_APP.bat"
)

$missingFiles = @()
foreach ($file in $coreFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING FILES" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "      Missing: $file" -ForegroundColor Red
    }
    $allGood = $false
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "  STATUS: READY TO START" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To start Signal Triage:" -ForegroundColor White
    Write-Host "  1. Run: START_APP.bat" -ForegroundColor Yellow
    Write-Host "  2. Open: http://localhost:8501" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
} else {
    Write-Host "  STATUS: SETUP INCOMPLETE" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Fix the issues above, then run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick fix commands:" -ForegroundColor White
    Write-Host "  python -m venv venv" -ForegroundColor Yellow
    Write-Host "  venv\Scripts\activate" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
