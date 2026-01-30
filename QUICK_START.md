# Signal Triage - Quick Start Guide

## The Problem You're Experiencing

When you open the dashboard, **NO APIs are connected** because:

1. **No `.env` file exists** - Only `.env.example` was present
2. **Services aren't running** - FastAPI server and dashboard need to be started
3. **Dashboard works standalone** - It doesn't require API connection (imports modules directly)

## Instant Solution (2 commands)

### Windows
```powershell
# Double-click this file OR run in terminal:
START_APP.bat
```

### Linux/Mac
```bash
chmod +x START_APP.sh
./START_APP.sh
```

This will:
- ✅ Create `.env` file from template
- ✅ Start FastAPI server on http://127.0.0.1:8000
- ✅ Start Streamlit dashboard on http://localhost:8501
- ✅ Open API docs at http://127.0.0.1:8000/docs

## Manual Setup (If you want control)

### Step 1: Create Configuration
```powershell
# Copy template
copy .env.example .env

# Edit .env and add your API keys (optional for basic usage)
notepad .env
```

### Step 2: Start API Server
```powershell
# Terminal 1
python run_api_server.py --host 127.0.0.1 --port 8000
```

### Step 3: Start Dashboard
```powershell
# Terminal 2 (separate window)
streamlit run signal_triage\ui\dashboard.py --server.port=8501
```

### Step 4: Access Services
- **Dashboard**: http://localhost:8501
- **API Docs**: http://127.0.0.1:8000/docs
- **API Health**: http://127.0.0.1:8000/health

## Docker Setup (Alternative)

If you prefer Docker:

```powershell
# Start all services (PostgreSQL + Redis + API + Dashboard)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

Docker URLs:
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Understanding the Architecture

### Current Setup (Working)
```
Dashboard (Streamlit) → Direct Import → Analysis Modules
```
- Dashboard **doesn't use API**
- Works standalone
- No API connection required

### API-Driven Setup (Available but not required)
```
Dashboard → HTTP Requests → FastAPI Server → Analysis Modules
                              ↓
                         PostgreSQL + Redis
```
- Use this for production
- Enables async job processing
- Database-backed results
- Multiple concurrent users

## Why APIs Seem "Not Connected"

The dashboard **doesn't connect to APIs** - it works standalone by importing the analysis modules directly. This is by design for simplicity.

### If you want API-driven dashboard:
You'd need to modify `signal_triage/ui/dashboard.py` to make HTTP requests to the FastAPI endpoints instead of direct imports.

## Configuration Files

### `.env` (Local configuration)
```ini
DATABASE_URL=sqlite:///signal_triage.db
API_HOST=127.0.0.1
API_PORT=8000
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
LOG_LEVEL=INFO
```

### `docker-compose.yml` (Docker configuration)
Already configured with:
- PostgreSQL database
- Redis cache
- FastAPI API server
- Streamlit dashboard

## Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different port
python run_api_server.py --port 8001
```

### Import Errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

### Dashboard Won't Start
```powershell
# Check if Streamlit is installed
streamlit --version

# Reinstall if needed
pip install streamlit --upgrade
```

### API Key Warnings
These are **optional**. The app works without external API keys:
- FRED_API_KEY (for Treasury rates)
- ALPHAVANTAGE_API_KEY (for stock prices)
- IEX_API_TOKEN (for company financials)

For basic analysis, you don't need any external APIs.

## Next Steps

1. **Start the app**: Run `START_APP.bat` (Windows) or `START_APP.sh` (Mac/Linux)
2. **Open dashboard**: http://localhost:8501
3. **Try demo mode**: Select "Demo" in sidebar → Click "Load Demo"
4. **Upload document**: Upload a credit agreement or 10-K filing
5. **Review analysis**: See distress score, LME signals, waterfall analysis

## API Usage (Optional)

If you want to use the API programmatically:

```python
import requests

# Upload document for analysis
files = {"file": open("credit_agreement.txt", "rb")}
response = requests.post(
    "http://127.0.0.1:8000/analyze",
    files=files,
    json={"analysis_type": "full"}
)
job = response.json()
print(f"Job ID: {job['job_id']}")

# Check status
status = requests.get(f"http://127.0.0.1:8000/jobs/{job['job_id']}")
print(status.json())

# Get results
results = requests.get(f"http://127.0.0.1:8000/analyses/{job['analysis_id']}")
print(results.json())
```

## Support

- **Documentation**: `docs/` folder
- **Examples**: `examples/` folder
- **API Reference**: http://127.0.0.1:8000/docs (when running)
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Monitoring Guide**: `docs/MONITORING.md`

---

**TL;DR**: Run `START_APP.bat` → Open http://localhost:8501 → Select "Demo" mode → Click "Load Demo"
