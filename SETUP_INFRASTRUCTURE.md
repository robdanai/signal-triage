# Infrastructure Setup Guide

**Status:** ✅ Files created, awaiting git initialization

This guide walks you through completing the infrastructure setup for Signal Triage.

## What Was Just Created

### Production Infrastructure (11 new files)

1. **Docker & Containerization**
   - `Dockerfile` - Multi-stage production image
   - `docker-compose.yml` - Full stack (API, DB, Redis, Dashboard)
   - `.dockerignore` - Optimized build context

2. **CI/CD Pipeline**
   - `.github/workflows/ci.yml` - Automated testing, linting, security scanning

3. **Code Quality**
   - `.pre-commit-config.yaml` - Pre-commit hooks (black, isort, flake8, bandit)
   - `.bandit` - Security scanner configuration
   - `Makefile` - Common development tasks

4. **Monitoring & Health**
   - `signal_triage/fastapi_app/health.py` - Health check endpoints
   - Updated `main.py` to include health router

5. **Documentation**
   - `CHANGELOG.md` - Version history
   - `CONTRIBUTING.md` - Developer guidelines (comprehensive)
   - `LICENSE` - MIT License
   - `docs/DEPLOYMENT.md` - Production deployment guide
   - `docs/MONITORING.md` - Observability setup
   - `.gitattributes` - Line ending handling

## Step 1: Install Git (Required)

### Windows

Download and install Git from: https://git-scm.com/download/win

Or use winget:
```powershell
winget install --id Git.Git -e --source winget
```

Verify installation:
```powershell
git --version
```

## Step 2: Initialize Git Repository

```powershell
# Navigate to project directory
cd "c:\Users\PGD\Distressed App\Signal-Triage"

# Initialize repository
git init

# Configure user (update with your info)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Stage all files
git add -A

# Create initial commit
git commit -m "chore: initialize repository with production infrastructure

Add comprehensive production-ready infrastructure:

Infrastructure:
- Docker and docker-compose configuration
- GitHub Actions CI/CD pipeline (test, lint, security, build)
- Health check endpoints (/health, /health/ready, /health/live)
- Pre-commit hooks for code quality
- Makefile for common tasks

Documentation:
- CHANGELOG.md with version history
- CONTRIBUTING.md with development guidelines
- DEPLOYMENT.md with production deployment guide
- MONITORING.md with observability setup
- LICENSE (MIT)

Configuration:
- .gitattributes for line ending handling
- .dockerignore for optimized builds
- .pre-commit-config.yaml for automated checks
- .bandit for security scanning config

This establishes the foundation for professional operations."
```

## Step 3: Connect to GitHub (Optional but Recommended)

### Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `signal-triage`
3. Description: "Forensic restructuring desk - Institutional-grade distressed debt analysis"
4. **Keep it Private** initially (contains proprietary analysis logic)
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)

### Push to GitHub

```powershell
# Add remote
git remote add origin https://github.com/yourusername/signal-triage.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 4: Install Development Tools

```powershell
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install development dependencies
pip install black flake8 isort pytest-cov safety bandit

# Verify setup
make help
```

## Step 5: Test Docker Setup

### Install Docker Desktop

Download from: https://www.docker.com/products/docker-desktop/

### Verify Installation

```powershell
docker --version
docker-compose --version
```

### Start Services

```powershell
# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# (Use notepad or your preferred editor)

# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Test health endpoint
curl http://localhost:8000/health

# Access services:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Dashboard: http://localhost:8501
```

## Step 6: Verify CI/CD Pipeline

Once pushed to GitHub:

1. Go to your repository on GitHub
2. Click "Actions" tab
3. You should see the CI pipeline run automatically
4. It will:
   - Run linting (black, flake8, isort)
   - Run all tests across Python 3.10, 3.11, 3.12
   - Run security scans (safety, bandit)
   - Build Docker image

## Step 7: Set Up Monitoring (Production)

### Option A: Basic (Free)

1. **UptimeRobot** (https://uptimerobot.com)
   - Monitor `/health` endpoint
   - Alert via email if down > 2 minutes

2. **Sentry** (https://sentry.io)
   - Free tier: 5,000 errors/month
   ```python
   # Add to requirements.txt
   sentry-sdk[fastapi]
   
   # Configure in main.py
   import sentry_sdk
   sentry_sdk.init(dsn="your-dsn-here")
   ```

### Option B: Full Stack (Self-hosted)

```powershell
# Start monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access dashboards:
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
```

See `docs/MONITORING.md` for complete setup.

## Step 8: Production Deployment

See `docs/DEPLOYMENT.md` for:
- AWS ECS deployment
- Google Cloud Run deployment
- Kubernetes deployment
- Nginx reverse proxy setup
- SSL/TLS configuration

## What's Fixed

Based on the infrastructure audit, here's what we addressed:

| Gap | Status | Solution |
|-----|--------|----------|
| **No Git Repository** | ✅ Ready | Run Step 2 above |
| **No CI/CD** | ✅ Fixed | GitHub Actions pipeline |
| **No Docker** | ✅ Fixed | Dockerfile + docker-compose |
| **No Monitoring** | ✅ Fixed | Health endpoints + docs |
| **No Deployment Guide** | ✅ Fixed | DEPLOYMENT.md |
| **No Contributing Guide** | ✅ Fixed | CONTRIBUTING.md |
| **No License** | ✅ Fixed | MIT License |
| **No Version Management** | ✅ Fixed | CHANGELOG.md |
| **No Pre-commit Hooks** | ✅ Fixed | .pre-commit-config.yaml |
| **No Security Scanning** | ✅ Fixed | Bandit + Safety in CI |

## What's Still TODO (Lower Priority)

1. **Load Testing**
   - Add Locust or k6 configuration
   - Benchmark API performance
   - Document capacity limits

2. **Live Market Data**
   - Wire Benchmarker to real APIs
   - See ROADMAP.md line 101

3. **Production Deployment**
   - Actually deploy to cloud
   - Set up monitoring
   - Configure backups

4. **Multi-tenancy**
   - Tenant isolation
   - Per-tenant rate limiting
   - Usage quotas

## Quick Commands

```powershell
# Run tests
make test

# Run linting
make lint

# Format code
make format

# Start Docker services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Run API locally (no Docker)
make run-api

# Run dashboard
make run-dashboard
```

## Verification Checklist

- [ ] Git installed and repository initialized
- [ ] Initial commit created
- [ ] (Optional) Pushed to GitHub
- [ ] Docker Desktop installed
- [ ] Docker compose works (`docker-compose up -d`)
- [ ] Health endpoint responds (`curl http://localhost:8000/health`)
- [ ] API docs accessible (http://localhost:8000/docs)
- [ ] Dashboard loads (http://localhost:8501)
- [ ] Pre-commit hooks installed (`pre-commit install`)
- [ ] Tests pass (`make test`)

## Need Help?

- **Docker issues:** Check `docker-compose logs api`
- **Test failures:** Run `pytest tests/ -v --tb=long`
- **Git questions:** See CONTRIBUTING.md
- **Deployment:** See docs/DEPLOYMENT.md
- **Monitoring:** See docs/MONITORING.md

## Next Steps

1. Complete Steps 1-2 above (install git, initialize repo)
2. Test Docker setup (Step 5)
3. Review and update `.env` with your API keys
4. (Optional) Push to GitHub and verify CI/CD
5. Start building! The infrastructure is ready.

---

**Ready for Production?** 

Once you complete these steps, Signal Triage will have:
- ✅ Version control
- ✅ Automated testing
- ✅ Containerization
- ✅ Health monitoring
- ✅ Production deployment path
- ✅ Professional operations

You've gone from "laptop project" to "institutional-grade infrastructure" in one session.
