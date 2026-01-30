@echo off
REM Signal Triage - Quick Start Script for Windows
REM This script starts both the API server and Dashboard

echo ================================================================
echo   SIGNAL TRIAGE - RESTRUCTURING COMMAND CENTER
echo ================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate.bat
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found. Creating from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env to add your API keys if needed
    echo.
)

echo [1/3] Starting FastAPI Server on http://127.0.0.1:8000
echo.

REM Start API server in a new window
start "Signal Triage API" cmd /k "venv\Scripts\activate.bat && python run_api_server.py --host 127.0.0.1 --port 8000"

REM Wait for API to start
echo Waiting for API server to start...
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Starting Streamlit Dashboard on http://localhost:8501
echo.

REM Start dashboard in a new window (multi-page app)
start "Signal Triage Dashboard" cmd /k "venv\Scripts\activate.bat && streamlit run signal_triage\ui\Home.py --server.port=8501 --server.address=localhost"

echo.
echo [3/3] Startup Complete!
echo.
echo ================================================================
echo   SIGNAL TRIAGE IS NOW RUNNING
echo ================================================================
echo.
echo API Server:       http://127.0.0.1:8000/docs
echo Dashboard:        http://localhost:8501
echo.
echo Press any key to stop all services...
echo ================================================================
pause >nul

REM Kill both windows
taskkill /FI "WindowTitle eq Signal Triage API*" /F >nul 2>&1
taskkill /FI "WindowTitle eq Signal Triage Dashboard*" /F >nul 2>&1

echo.
echo All services stopped.
echo.
pause
