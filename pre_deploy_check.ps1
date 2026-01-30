# Pre-Deployment Checklist Script for Signal Triage
# Run this before executing docker-compose up

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Signal Triage Pre-Deployment Check" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$allGood = $true

# Check Docker
Write-Host "[1/6] Checking Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "  ❌ Docker not installed" -ForegroundColor Red
    Write-Host "     Install: winget install Docker.DockerDesktop" -ForegroundColor Gray
    $allGood = $false
} else {
    $dockerVersion = docker --version
    Write-Host "  ✅ Docker installed: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    try {
        docker ps | Out-Null
        Write-Host "  ✅ Docker daemon is running" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Docker installed but not running - start Docker Desktop" -ForegroundColor Yellow
        $allGood = $false
    }
}

# Check Docker Compose
Write-Host "`n[2/6] Checking Docker Compose..." -ForegroundColor Yellow
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "  ❌ docker-compose not found" -ForegroundColor Red
    Write-Host "     Install with Docker Desktop or separately" -ForegroundColor Gray
    $allGood = $false
} else {
    $composeVersion = docker-compose --version
    Write-Host "  ✅ Docker Compose installed: $composeVersion" -ForegroundColor Green
}

# Check Git
Write-Host "`n[3/6] Checking Git..." -ForegroundColor Yellow
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  ❌ Git not installed" -ForegroundColor Red
    Write-Host "     Install: winget install --id Git.Git -e --source winget" -ForegroundColor Gray
    $allGood = $false
} else {
    $gitVersion = git --version
    Write-Host "  ✅ Git installed: $gitVersion" -ForegroundColor Green
    
    # Check if repo initialized
    if (Test-Path .git) {
        Write-Host "  ✅ Git repository initialized" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Git repository not initialized (run: git init)" -ForegroundColor Yellow
    }
}

# Check .env file
Write-Host "`n[4/6] Checking .env configuration..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Write-Host "  ❌ .env file missing" -ForegroundColor Red
    Write-Host "     Copy .env.example to .env and configure" -ForegroundColor Gray
    $allGood = $false
} else {
    Write-Host "  ✅ .env file exists" -ForegroundColor Green
    
    # Check critical variables
    $envContent = Get-Content .env -Raw
    
    # Check DATABASE_URL
    if ($envContent -match 'DATABASE_URL=postgresql://') {
        Write-Host "  ✅ DATABASE_URL configured for PostgreSQL" -ForegroundColor Green
    } elseif ($envContent -match 'DATABASE_URL=sqlite://') {
        Write-Host "  ⚠️  DATABASE_URL uses SQLite (Docker needs PostgreSQL)" -ForegroundColor Yellow
        Write-Host "     See DEBUGGING_CHECKLIST.md issue #3" -ForegroundColor Gray
        $allGood = $false
    } else {
        Write-Host "  ❌ DATABASE_URL not configured" -ForegroundColor Red
        $allGood = $false
    }
    
    # Check POSTGRES_PASSWORD
    if ($envContent -match 'POSTGRES_PASSWORD=\w+') {
        Write-Host "  ✅ POSTGRES_PASSWORD is set" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  POSTGRES_PASSWORD not set" -ForegroundColor Yellow
        Write-Host "     Required for Docker PostgreSQL" -ForegroundColor Gray
        $allGood = $false
    }
    
    # Check SEC_USER_AGENT
    if ($envContent -match 'SEC_USER_AGENT=.*@.*') {
        Write-Host "  ✅ SEC_USER_AGENT configured with email" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  SEC_USER_AGENT should include contact email (SEC requirement)" -ForegroundColor Yellow
    }
}

# Check required files
Write-Host "`n[5/6] Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "main.py"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file missing" -ForegroundColor Red
        $missingFiles += $file
        $allGood = $false
    }
}

# Check Python environment
Write-Host "`n[6/6] Checking Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  ⚠️  Python not found in PATH" -ForegroundColor Yellow
} else {
    $pythonVersion = python --version
    Write-Host "  ✅ Python installed: $pythonVersion" -ForegroundColor Green
    
    # Check if virtual environment is activated
    if ($env:VIRTUAL_ENV) {
        Write-Host "  ✅ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  No virtual environment activated (optional for Docker)" -ForegroundColor Gray
    }
}

# Final summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "Ready to run: docker-compose up -d" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "❌ SOME CHECKS FAILED" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Cyan
    Write-Host "Please fix the issues above before running docker-compose" -ForegroundColor Yellow
    Write-Host "See DEBUGGING_CHECKLIST.md for detailed fixes`n" -ForegroundColor Gray
    exit 1
}
