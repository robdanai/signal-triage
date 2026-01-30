#!/bin/bash
# Signal Triage - Quick Start Script for Linux/Mac
# This script starts both the API server and Dashboard

set -e

echo "================================================================"
echo "  SIGNAL TRIAGE - RESTRUCTURING COMMAND CENTER"
echo "================================================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Creating from template..."
    cp .env.example .env
    echo
    echo "IMPORTANT: Edit .env to add your API keys if needed"
    echo
fi

echo "[1/3] Starting FastAPI Server on http://127.0.0.1:8000"
echo

# Start API server in background
python run_api_server.py --host 127.0.0.1 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

# Wait for API to start
echo "Waiting for API server to start..."
sleep 5

echo
echo "[2/3] Starting Streamlit Dashboard on http://localhost:8501"
echo

# Start dashboard in background (multi-page app)
streamlit run signal_triage/ui/Home.py --server.port=8501 --server.address=localhost > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard PID: $DASHBOARD_PID"

echo
echo "[3/3] Startup Complete!"
echo
echo "================================================================"
echo "  SIGNAL TRIAGE IS NOW RUNNING"
echo "================================================================"
echo
echo "API Server:       http://127.0.0.1:8000/docs"
echo "Dashboard:        http://localhost:8501"
echo
echo "To stop services, run: kill $API_PID $DASHBOARD_PID"
echo "Or press Ctrl+C"
echo "================================================================"

# Wait for Ctrl+C
trap "kill $API_PID $DASHBOARD_PID 2>/dev/null; echo; echo 'Services stopped.'; exit" INT
wait
