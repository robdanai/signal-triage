# 🚨 START HERE - Signal Triage Setup

## The Problem You Had

When you opened the dashboard, **nothing was connected** because:

1. ❌ No `.env` configuration file
2. ❌ API server not running
3. ❌ Dashboard not started
4. ❌ No clear startup instructions

## The Solution (3 Steps)

### Step 1: Verify Setup
```powershell
# Run this to check everything is configured:
powershell -ExecutionPolicy Bypass -File check_setup.ps1
```

### Step 2: Start Everything
```powershell
# Double-click this file OR run in terminal:
START_APP.bat
```

This will:
- ✅ Create `.env` file automatically
- ✅ Start API server on http://127.0.0.1:8000
- ✅ Start Dashboard on http://localhost:8501
- ✅ Open both in separate terminal windows

### Step 3: Access Dashboard
```
Open browser → http://localhost:8501
```

## What You Get

### Dashboard (Streamlit)
- **URL**: http://localhost:8501
- **Features**: Interactive waterfall analysis, LME detection, covenant forensics
- **Mode**: Select "Demo" → Click "Load Demo" for instant example

### API Server (FastAPI)
- **URL**: http://127.0.0.1:8000
- **Docs**: http://127.0.0.1:8000/docs (Interactive API documentation)
- **Health**: http://127.0.0.1:8000/health (Check if running)

## Troubleshooting

### "Port already in use"
```powershell
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Kill process (replace <PID>)
taskkill /PID <PID> /F
```

### "Module not found"
```powershell
# Activate virtual environment
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Can't find START_APP.bat"
```powershell
# Make sure you're in the project directory
cd "c:\Users\PGD\Distressed App\Signal-Triage"

# Then run
START_APP.bat
```

### Services won't start
```powershell
# Check setup
powershell -ExecutionPolicy Bypass -File check_setup.ps1

# If virtual environment missing:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Then try again
START_APP.bat
```

## Understanding the Architecture

### Current Setup (Simple)
```
Dashboard → Direct Imports → Analysis Modules
```
- Dashboard works **standalone**
- No API connection required
- Imports code directly

### With API Server (Optional for production)
```
Dashboard → HTTP → FastAPI → Modules → Database
```
- Job queue for async processing
- Database storage (PostgreSQL)
- Redis caching
- Multiple users

## Configuration Options

### Basic Setup (No API Keys Needed)
The app works immediately with:
- ✅ Local document analysis
- ✅ Demo mode
- ✅ Waterfall modeling
- ✅ LME detection
- ✅ Covenant forensics

### Advanced Setup (Optional API Keys)
Add these to `.env` for live market data:

```ini
# SEC Edgar (FREE - just need email)
SEC_USER_AGENT=YourCompany/1.0 (your.email@example.com)

# Treasury Rates (FREE with registration)
FRED_API_KEY=your_key_here

# Stock Data (FREE tier available)
ALPHAVANTAGE_API_KEY=your_key_here

# Commercial APIs (paid)
IEX_API_TOKEN=your_token_here
NINEFIN_API_KEY=your_key_here
BLOOMBERG_API_KEY=your_key_here
```

## Quick Test

### Test 1: Demo Mode
1. Open http://localhost:8501
2. Select "Demo" in sidebar
3. Click "Load Demo"
4. See instant analysis

### Test 2: Upload Document
1. Open http://localhost:8501
2. Select "Upload Document"
3. Upload a `.txt` or `.md` file
4. Click "Analyze"
5. Review results

### Test 3: API Health Check
1. Open http://127.0.0.1:8000/health
2. Should see: `{"status": "healthy", "version": "1.0.0", ...}`

## Next Steps

1. **Get familiar**: Try demo mode first
2. **Upload documents**: Test with your credit agreements
3. **Configure APIs**: Add API keys to `.env` for live data
4. **Read docs**: See `docs/` folder for advanced features
5. **Deploy**: See `docs/DEPLOYMENT.md` for production setup

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Detailed setup guide
- **[ROADMAP.md](docs/ROADMAP.md)** - Feature roadmap
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
- **[API_GUIDE.md](docs/API_GUIDE.md)** - API usage examples
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guide

## Support

If you're still having issues:

1. Run the verification script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File check_setup.ps1
   ```

2. Check the logs:
   ```powershell
   type logs\api.log
   type logs\dashboard.log
   ```

3. Verify Python version:
   ```powershell
   python --version  # Should be 3.10+
   ```

---

**TL;DR**: Run `START_APP.bat` → Open http://localhost:8501 → Select "Demo" → Click "Load Demo"
