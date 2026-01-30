# Signal Triage Quick Fix Guide

**Time to Fix:** 10-15 minutes  
**Date:** January 30, 2026

## 🎯 What Was Fixed

Fixed **7 critical bugs** that prevented Docker deployment:
- Database configuration mismatch
- Import errors in health checks
- Async/await bugs
- Missing module exports
- Incomplete package dependencies

## 📋 Quick Start (3 Steps)

### Step 1: Install Requirements (5 min)

```powershell
# Install Docker Desktop
winget install Docker.DockerDesktop

# Install Git
winget install --id Git.Git -e --source winget

# Restart PowerShell after installation
```

### Step 2: Verify Setup (1 min)

```powershell
# Run pre-deployment check
.\pre_deploy_check.ps1
```

**Expected output:**
```
✅ ALL CHECKS PASSED
Ready to run: docker-compose up -d
```

If you see errors, see [Troubleshooting](#troubleshooting) below.

### Step 3: Start Application (2 min)

```powershell
# Start all services
docker-compose up -d

# Wait 30 seconds, then check health
python check_health.py
```

**Success looks like:**
```
✅ ALL CHECKS PASSED (6/6)
API is healthy and ready to use!
```

**Access the application:**
- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501

---

## 🔧 What Changed

### Files Modified (4)
1. **`.env`** - Fixed database configuration
2. **`signal_triage/fastapi_app/health.py`** - Fixed imports and async bugs
3. **`signal_triage/database/__init__.py`** - Added missing exports
4. **`setup.py`** - Added all dependencies

### Files Created (4)
1. **`DEBUGGING_CHECKLIST.md`** - Comprehensive issue documentation
2. **`pre_deploy_check.ps1`** - Automated verification script
3. **`check_health.py`** - Health check verification
4. **`.env.docker`** - Docker-specific configuration

---

## 🐛 Troubleshooting

### Docker Not Installed
```
❌ Docker not installed
```

**Fix:**
```powershell
winget install Docker.DockerDesktop
# Restart PowerShell
```

### Git Not Installed
```
❌ Git not installed
```

**Fix:**
```powershell
winget install --id Git.Git -e --source winget
# Restart PowerShell
```

### Docker Not Running
```
⚠️ Docker installed but not running
```

**Fix:**
- Start Docker Desktop from Windows Start menu
- Wait for Docker icon in system tray to show "Docker Desktop is running"

### SQLite in .env
```
⚠️ DATABASE_URL uses SQLite (Docker needs PostgreSQL)
```

**Fix:**
This was already fixed in `.env`. If you see this error:
```powershell
# Open .env and ensure PostgreSQL line is uncommented:
DATABASE_URL=postgresql://signaltriage:changeme@postgres:5432/signal_triage

# Ensure SQLite line is commented:
# DATABASE_URL=sqlite:///signal_triage.db
```

### Port Already in Use
```
Error: port is already allocated
```

**Fix:**
```powershell
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Stop conflicting service or change port in docker-compose.yml
```

### Container Won't Start
```powershell
# Check logs
docker-compose logs api

# Common fixes:
docker-compose down
docker-compose up -d --build
```

---

## 📚 Detailed Documentation

For more information, see:
- **DEBUGGING_CHECKLIST.md** - All issues and fixes
- **FIXES_APPLIED.md** - What was changed
- **SETUP_INFRASTRUCTURE.md** - Full setup guide
- **docs/DEPLOYMENT.md** - Production deployment

---

## ⚡ One-Liner Quick Check

```powershell
.\pre_deploy_check.ps1 && docker-compose up -d && timeout /t 30 && python check_health.py
```

This will:
1. Run pre-deployment checks
2. Start Docker containers
3. Wait 30 seconds
4. Verify health

---

## 🚀 After Docker is Running

### Initialize Git Repository
```powershell
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
git add -A
git commit -m "chore: initialize repository with production infrastructure"
```

### Create GitHub Repository
```powershell
# Create repo on GitHub, then:
git remote add origin https://github.com/yourusername/Signal-Triage.git
git branch -M main
git push -u origin main
```

### Change Default Password
Edit `.env` and replace `changeme_use_secure_password_in_production` with a secure password.

---

## 📊 System Requirements

| Component | Version | Status |
|-----------|---------|--------|
| Windows | 10/11 | ✅ Met |
| Docker Desktop | 20.10+ | 🔴 Install required |
| Git | 2.x | 🔴 Install required |
| Python | 3.10-3.12 | ✅ Met (if venv exists) |
| PowerShell | 5.1+ | ✅ Met |

---

## 🎉 Success Indicators

### Docker Stack Running
```powershell
docker-compose ps
```
Should show 4 services running:
- signal-triage-db (postgres)
- signal-triage-redis
- signal-triage-api
- signal-triage-dashboard

### Health Checks Pass
- http://localhost:8000/health → `{"status": "healthy"}`
- http://localhost:8000/health/ready → `{"status": "ready"}`
- http://localhost:8501 → Streamlit dashboard loads

### API Documentation
- http://localhost:8000/docs → Interactive API docs

---

## 🆘 Getting Help

If issues persist:

1. **Check logs:**
   ```powershell
   docker-compose logs -f api
   ```

2. **Review checklist:**
   ```powershell
   notepad DEBUGGING_CHECKLIST.md
   ```

3. **Restart everything:**
   ```powershell
   docker-compose down
   docker-compose up -d --build
   ```

4. **Verify environment:**
   ```powershell
   .\pre_deploy_check.ps1
   ```

---

**Status:** Ready to deploy! Follow the 3 steps above to get started.
