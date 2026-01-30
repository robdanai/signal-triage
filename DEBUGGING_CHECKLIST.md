# Signal Triage Debugging Checklist
**Date:** January 30, 2026  
**Status:** 🔴 Critical Issues Found

## Executive Summary

Infrastructure implementation is complete but has **7 critical issues** that prevent deployment. This checklist identifies all issues and provides fixes.

---

## 🔴 CRITICAL ISSUES (Must Fix Before Deployment)

### 1. Docker Not Installed
**Severity:** CRITICAL  
**Impact:** Cannot run docker-compose stack, no containerization possible

**Problem:**
```powershell
docker : The term 'docker' is not recognized...
```

**Fix:**
```powershell
# Install Docker Desktop for Windows
winget install Docker.DockerDesktop

# OR download from: https://www.docker.com/products/docker-desktop/

# After installation, verify:
docker --version
docker-compose --version
```

**Verification:**
- [ ] `docker --version` returns version number
- [ ] `docker-compose --version` returns version number
- [ ] Docker Desktop is running

---

### 2. Git Not Installed/Configured
**Severity:** CRITICAL  
**Impact:** No version control, cannot push to GitHub, CI/CD won't work

**Problem:**
- Git command fails with sandbox errors
- No .git directory exists (per workspace info: "Is directory a git repo: No")

**Fix:**
```powershell
# Install Git
winget install --id Git.Git -e --source winget

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Initialize repository
cd "c:\Users\PGD\Distressed App\Signal-Triage"
git init
git add -A
git commit -m "chore: initialize repository with production infrastructure"
```

**Verification:**
- [ ] `git --version` returns version number
- [ ] `.git` directory exists in workspace root
- [ ] `git status` runs without errors

---

### 3. Database Configuration Mismatch
**Severity:** CRITICAL  
**Impact:** Docker stack will fail, API cannot connect to database

**Problem:**
- `.env` file uses SQLite: `DATABASE_URL=sqlite:///signal_triage.db`
- `docker-compose.yml` expects PostgreSQL connection
- SQLite is file-based, won't work in Docker containers

**Current (.env line 5):**
```bash
DATABASE_URL=sqlite:///signal_triage.db
```

**Fix:**
Update `.env` file to use PostgreSQL for production:
```bash
# For Docker/Production (PostgreSQL)
DATABASE_URL=postgresql://signaltriage:changeme@postgres:5432/signal_triage

# For Local Development (SQLite - optional)
# DATABASE_URL=sqlite:///signal_triage.db
```

**Additional Fix:**
Add `POSTGRES_PASSWORD` to `.env`:
```bash
# Add after DATABASE_URL
POSTGRES_PASSWORD=changeme_use_secure_password_in_production
```

**Verification:**
- [ ] `.env` contains PostgreSQL connection string
- [ ] `POSTGRES_PASSWORD` is set in `.env`
- [ ] Password matches between `DATABASE_URL` and `POSTGRES_PASSWORD`

---

### 4. Cache Class Missing in health.py
**Severity:** HIGH  
**Impact:** Health check endpoints will crash on startup

**Problem:**
`signal_triage/fastapi_app/health.py` line 109 imports:
```python
from signal_triage.infrastructure.cache import Cache
```

But `signal_triage/infrastructure/cache.py` only exports:
- `CacheBackend` (abstract class)
- `MemoryCacheBackend`
- `FileCacheBackend`
- `RedisCacheBackend`
- `CacheManager` (not `Cache`)

**Fix Option 1 (Recommended):**
Update `health.py` line 109:
```python
# OLD:
from signal_triage.infrastructure.cache import Cache

# NEW:
from signal_triage.infrastructure.cache import get_cache_manager
```

Update `_check_cache()` function (lines 111-112):
```python
# OLD:
cache = Cache()

# NEW:
cache = get_cache_manager()
```

**Fix Option 2 (Alternative):**
Add alias to `cache.py`:
```python
# Add at end of cache.py
Cache = CacheManager  # Backward compatibility alias
```

**Verification:**
- [ ] Import statement matches exported class name
- [ ] Health check endpoint doesn't crash on startup

---

### 5. Async/Await Mismatch in Health Check
**Severity:** HIGH  
**Impact:** Health check will fail at runtime

**Problem:**
`health.py` lines 116-117 use `await` with sync methods:
```python
await cache.set(test_key, "ok", ttl=5)
result = await cache.get(test_key)
```

But `CacheManager.set()` and `CacheManager.get()` are **synchronous** (not async).

**Fix:**
Update `_check_cache()` function to remove `await`:
```python
# Lines 116-117 - Remove await keywords
cache.set(test_key, "ok", ttl=5)  # Remove 'await'
result = cache.get(test_key)      # Remove 'await'
```

**Verification:**
- [ ] No `await` used with sync cache methods
- [ ] Health check runs without AsyncIO errors

---

### 6. Missing session_scope in Database Exports
**Severity:** MEDIUM  
**Impact:** FastAPI main.py cannot import session_scope

**Problem:**
`signal_triage/fastapi_app/main.py` line 28 imports:
```python
from signal_triage.database import (
    init_db,
    session_scope,  # ← Not exported by database/__init__.py
    # ...
)
```

But `signal_triage/database/__init__.py` only exports:
```python
__all__ = [
    "Base", "Document", "Analysis", "AnalysisJob", "APIAuditLog", 
    "DocumentVersion", "get_engine", "get_session", "init_db"
]
```

**Fix:**
Update `signal_triage/database/__init__.py`:
```python
# Add import
from signal_triage.database.session import (
    get_engine,
    get_session,
    init_db,
    session_scope,  # ← Add this import
)

# Add to __all__
__all__ = [
    "Base",
    "Document",
    "Analysis",
    "AnalysisJob",
    "APIAuditLog",
    "DocumentVersion",
    "get_engine",
    "get_session",
    "init_db",
    "session_scope",  # ← Add this export
]
```

**Verification:**
- [ ] `from signal_triage.database import session_scope` works
- [ ] FastAPI app starts without ImportError

---

### 7. Missing SessionLocal Export
**Severity:** MEDIUM  
**Impact:** Health check cannot access database session factory

**Problem:**
`health.py` line 84 imports:
```python
from signal_triage.database.session import SessionLocal
```

But `session.py` defines `_SessionLocal` (private) and only exports:
- `get_engine()`
- `get_session_factory()` (returns SessionLocal)
- `get_session()`
- `session_scope()`
- `init_db()`
- `drop_all_tables()`

**Fix Option 1 (Recommended):**
Update `health.py` line 87 to use exported function:
```python
# OLD:
db = SessionLocal()

# NEW:
db = get_session()
```

**Fix Option 2 (Alternative):**
Export `SessionLocal` from `session.py`:
```python
# Add after get_session_factory() function
SessionLocal = get_session_factory()
```

**Verification:**
- [ ] Health check can create database sessions
- [ ] No ImportError for SessionLocal

---

## 🟡 MEDIUM PRIORITY ISSUES

### 8. setup.py Incomplete Dependencies
**Severity:** MEDIUM  
**Impact:** Missing production dependencies in package manifest

**Problem:**
`setup.py` only lists `pypdf>=4.0.0` as a dependency, but `requirements.txt` has 45+ packages.

**Fix:**
Update `setup.py` to include all required dependencies:
```python
install_requires=[
    "pypdf>=4.0.0",
    "pdfplumber>=0.10.0",
    "requests>=2.28.0",
    "streamlit>=1.30.0",
    "pandas>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "redis>=5.0.0",
    # ... add others from requirements.txt
],
```

**Verification:**
- [ ] `pip install -e .` installs all dependencies
- [ ] No missing module errors at runtime

---

### 9. Environment Variables Not Documented in INFRASTRUCTURE_SUMMARY
**Severity:** LOW  
**Impact:** User confusion about required vs optional variables

**Problem:**
`.env` has 64 lines of configuration but `INFRASTRUCTURE_SUMMARY.md` doesn't document which are required.

**Fix:**
Add section to `INFRASTRUCTURE_SUMMARY.md`:
```markdown
## Required Environment Variables

### Critical (Must Set):
- `DATABASE_URL` - PostgreSQL connection string
- `POSTGRES_PASSWORD` - Database password
- `SEC_USER_AGENT` - Contact email (SEC requirement)

### Optional (API Features):
- `FRED_API_KEY` - Treasury yields
- `ALPHAVANTAGE_API_KEY` - Stock prices
- (etc.)
```

**Verification:**
- [ ] Documentation clearly states which variables are required
- [ ] New developers can set up environment quickly

---

### 10. No .env.docker for Docker-Specific Overrides
**Severity:** LOW  
**Impact:** Users must manually edit .env when switching between local/Docker

**Problem:**
`.env` file works for local development (SQLite) but needs different values for Docker (PostgreSQL).

**Fix:**
Create `.env.docker`:
```bash
# Docker-specific overrides
DATABASE_URL=postgresql://signaltriage:changeme@postgres:5432/signal_triage
POSTGRES_PASSWORD=changeme
CACHE_BACKEND=redis
REDIS_HOST=redis
REDIS_PORT=6379
API_HOST=0.0.0.0
```

Update `docker-compose.yml` to use it:
```yaml
services:
  api:
    env_file:
      - .env
      - .env.docker  # Overrides local settings
```

**Verification:**
- [ ] Can run locally with SQLite
- [ ] Can run in Docker with PostgreSQL without editing files

---

## 🟢 NICE-TO-HAVE IMPROVEMENTS

### 11. Add Healthcheck Script
**Severity:** LOW  
**Impact:** Easier verification of setup

**Recommendation:**
Create `check_health.py`:
```python
#!/usr/bin/env python3
"""Quick health check script."""
import requests

def check_api():
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        resp.raise_for_status()
        print("✅ API is healthy")
        return True
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False

if __name__ == "__main__":
    check_api()
```

---

### 12. Add Pre-Deployment Checklist Script
**Severity:** LOW  
**Impact:** Catch issues before docker-compose up

**Recommendation:**
Create `pre_deploy_check.ps1`:
```powershell
# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not installed" -ForegroundColor Red
} else {
    Write-Host "✅ Docker installed" -ForegroundColor Green
}

# Check Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git not installed" -ForegroundColor Red
} else {
    Write-Host "✅ Git installed" -ForegroundColor Green
}

# Check .env
if (-not (Test-Path .env)) {
    Write-Host "❌ .env file missing" -ForegroundColor Red
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}
```

---

## 📋 VERIFICATION CHECKLIST

### Before Starting Docker Stack
- [ ] Docker Desktop installed and running
- [ ] Git installed and configured
- [ ] `.env` file configured with PostgreSQL
- [ ] `POSTGRES_PASSWORD` set in `.env`
- [ ] All code fixes applied (issues #4-7)

### After Docker Stack Starts
- [ ] `docker-compose up -d` succeeds
- [ ] All 4 containers running (postgres, redis, api, dashboard)
- [ ] `http://localhost:8000/health` returns 200
- [ ] `http://localhost:8000/health/ready` returns 200
- [ ] `http://localhost:8501` loads Streamlit dashboard
- [ ] Database tables created (check logs)

### After Git Setup
- [ ] `.git` directory exists
- [ ] Initial commit created
- [ ] `.gitignore` excludes sensitive files
- [ ] Ready to push to GitHub

---

## 🚀 QUICK FIX SCRIPT (PowerShell)

Run this to fix issues #3-7 automatically:

```powershell
# Issue #3: Fix DATABASE_URL in .env
(Get-Content .env) | ForEach-Object {
    if ($_ -match '^DATABASE_URL=sqlite') {
        'DATABASE_URL=postgresql://signaltriage:changeme@postgres:5432/signal_triage'
    } else {
        $_
    }
} | Set-Content .env

# Add POSTGRES_PASSWORD if missing
if (-not (Select-String -Path .env -Pattern 'POSTGRES_PASSWORD')) {
    Add-Content .env "`nPOSTGRESS_PASSWORD=changeme_use_secure_password_in_production"
}

Write-Host "✅ Database configuration fixed" -ForegroundColor Green
```

---

## 📊 ISSUE SUMMARY

| Priority | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 7 | Must fix before deployment |
| 🟡 Medium | 3 | Should fix soon |
| 🟢 Low | 2 | Nice to have |
| **Total** | **12** | **Issues identified** |

---

## 📝 NEXT STEPS

### Immediate (Do Now)
1. Install Docker Desktop
2. Install Git
3. Fix database configuration (.env)
4. Apply code fixes (issues #4-7)
5. Verify with `docker-compose up`

### This Week
6. Initialize Git repository
7. Push to GitHub
8. Verify CI/CD pipeline runs
9. Set up monitoring

### This Month
10. Production deployment
11. Load testing
12. Security hardening

---

## 🔗 RELATED DOCUMENTS

- `INFRASTRUCTURE_SUMMARY.md` - What was built
- `SETUP_INFRASTRUCTURE.md` - Setup guide (needs updating with these fixes)
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/MONITORING.md` - Monitoring and observability

---

**Status:** Ready to fix issues and proceed with deployment once resolved.
