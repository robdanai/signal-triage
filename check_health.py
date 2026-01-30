#!/usr/bin/env python3
"""
Quick health check script for Signal Triage API.

Usage:
    python check_health.py

Checks:
- API is running and responding
- Health endpoint returns 200
- Readiness check passes
- Basic metrics available
"""

import sys
import time
import requests
from typing import Dict, Any


def check_endpoint(url: str, name: str, timeout: int = 5) -> bool:
    """
    Check if an endpoint is responding.
    
    Args:
        url: Endpoint URL
        name: Friendly name for display
        timeout: Request timeout in seconds
    
    Returns:
        True if check passed, False otherwise
    """
    try:
        print(f"Checking {name}...", end=" ", flush=True)
        resp = requests.get(url, timeout=timeout)
        
        if resp.status_code == 200:
            print(f"✅ OK (HTTP {resp.status_code})")
            return True
        else:
            print(f"⚠️  HTTP {resp.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed (is the API running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout (>{timeout}s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_api_details(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Get API details from health endpoint.
    
    Args:
        base_url: Base URL of API
    
    Returns:
        API details dictionary or None if failed
    """
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def main():
    """Run all health checks."""
    print("\n" + "=" * 50)
    print("Signal Triage API Health Check")
    print("=" * 50 + "\n")
    
    base_url = "http://localhost:8000"
    dashboard_url = "http://localhost:8501"
    
    results = []
    
    # Check main health endpoint
    results.append(check_endpoint(f"{base_url}/health", "API Health"))
    
    # Check readiness
    results.append(check_endpoint(f"{base_url}/health/ready", "API Readiness"))
    
    # Check liveness
    results.append(check_endpoint(f"{base_url}/health/live", "API Liveness"))
    
    # Check metrics
    results.append(check_endpoint(f"{base_url}/metrics", "API Metrics"))
    
    # Check docs
    results.append(check_endpoint(f"{base_url}/docs", "API Documentation"))
    
    # Check Streamlit dashboard
    results.append(check_endpoint(dashboard_url, "Streamlit Dashboard", timeout=10))
    
    # Get API details
    print("\n" + "-" * 50)
    details = check_api_details(base_url)
    if details:
        print("API Details:")
        print(f"  Status: {details.get('status', 'unknown')}")
        print(f"  Version: {details.get('version', 'unknown')}")
        print(f"  Service: {details.get('service', 'unknown')}")
        print(f"  Timestamp: {details.get('timestamp', 'unknown')}")
    else:
        print("Could not retrieve API details")
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 50 + "\n")
        print("API is healthy and ready to use!")
        return 0
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total} passed)")
        print("=" * 50 + "\n")
        print("Some services may not be running properly.")
        print("Check the logs: docker-compose logs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
