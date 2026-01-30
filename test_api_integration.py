#!/usr/bin/env python
"""
Test script for FastAPI integration with the analysis pipeline.

Demonstrates how to use the API endpoints to submit documents for analysis.

Usage:
    # Start the API server first:
    python run_api_server.py

    # Then in another terminal, run this test:
    python test_api_integration.py
"""

from __future__ import annotations

import json
import time
import requests
from pathlib import Path


API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = "your-api-key-here"  # Set this if API keys are configured


def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "=" * 70)
    print("Testing Health Check")
    print("=" * 70)
    
    response = requests.get(f"{API_BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed")


def test_analyze_url(url: str):
    """Test analyzing a document from a URL."""
    print("\n" + "=" * 70)
    print(f"Testing URL Analysis: {url}")
    print("=" * 70)
    
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    # Submit analysis job
    payload = {
        "document_url": url,
        "analysis_type": "full",
        "ticker": "TEST",
    }
    
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Submit Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Job ID: {job_id}")
    print(f"Initial Status: {job_data['status']}")
    
    # Poll for job completion
    print("\nPolling for job completion...")
    max_attempts = 60
    for attempt in range(max_attempts):
        time.sleep(2)
        
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error checking job status: {response.text}")
            return None
        
        job_status = response.json()
        status = job_status["status"]
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status}")
        
        if status == "completed":
            print("\n✓ Job completed successfully!")
            analysis_id = job_status["analysis_id"]
            
            # Fetch analysis results
            response = requests.get(
                f"{API_BASE_URL}/analyses/{analysis_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                analysis = response.json()
                print(f"\nAnalysis Results:")
                print(f"  Analysis ID: {analysis['analysis_id']}")
                print(f"  Distress Score: {analysis['distress_score']}")
                print(f"  Credit Opinion: {analysis['credit_opinion']}")
                print(f"  Execution Time: {analysis['execution_time_seconds']:.2f}s")
                print(f"\nKey Findings:")
                print(json.dumps(analysis['key_findings'], indent=2))
                
                return analysis
            else:
                print(f"Error fetching analysis: {response.text}")
                return None
        
        elif status == "failed":
            print(f"\n✗ Job failed: {job_status.get('error_message')}")
            return None
        
        elif status == "cancelled":
            print("\n✗ Job was cancelled")
            return None
    
    print(f"\n✗ Job did not complete within {max_attempts * 2} seconds")
    return None


def test_analyze_file(file_path: str | Path):
    """Test analyzing a document from a file upload."""
    print("\n" + "=" * 70)
    print(f"Testing File Upload Analysis: {file_path}")
    print("=" * 70)
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"✗ File not found: {file_path}")
        return None
    
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    # Submit analysis job with file upload
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        data = {
            "analysis_type": "full",
            "ticker": "TEST",
        }
        
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            data=data,
            files=files,
            headers=headers
        )
    
    print(f"Submit Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Job ID: {job_id}")
    print(f"Initial Status: {job_data['status']}")
    
    # Poll for job completion (similar to URL test)
    print("\nPolling for job completion...")
    max_attempts = 60
    for attempt in range(max_attempts):
        time.sleep(2)
        
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error checking job status: {response.text}")
            return None
        
        job_status = response.json()
        status = job_status["status"]
        print(f"  [{attempt + 1}/{max_attempts}] Status: {status}")
        
        if status == "completed":
            print("\n✓ Job completed successfully!")
            analysis_id = job_status["analysis_id"]
            
            # Fetch analysis results
            response = requests.get(
                f"{API_BASE_URL}/analyses/{analysis_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                analysis = response.json()
                print(f"\nAnalysis Results:")
                print(f"  Analysis ID: {analysis['analysis_id']}")
                print(f"  Distress Score: {analysis['distress_score']}")
                print(f"  Credit Opinion: {analysis['credit_opinion']}")
                print(f"  Execution Time: {analysis['execution_time_seconds']:.2f}s")
                
                return analysis
            else:
                print(f"Error fetching analysis: {response.text}")
                return None
        
        elif status == "failed":
            print(f"\n✗ Job failed: {job_status.get('error_message')}")
            return None
    
    print(f"\n✗ Job did not complete within {max_attempts * 2} seconds")
    return None


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Signal Triage API Integration Tests")
    print("=" * 70)
    print("\nMake sure the API server is running first:")
    print("  python run_api_server.py")
    print()
    
    try:
        # Test health check
        test_health_check()
        
        # Test URL analysis (example with a sample URL)
        # Replace with a real document URL for actual testing
        sample_url = "https://example.com/sample-document.pdf"
        print(f"\nTo test URL analysis, update the sample_url in the script")
        print(f"Current sample_url: {sample_url}")
        # Uncomment to test:
        # test_analyze_url(sample_url)
        
        # Test file upload (example with a sample file)
        # Replace with a real file path for actual testing
        sample_file = Path("sample_documents/test.pdf")
        if sample_file.exists():
            test_analyze_file(sample_file)
        else:
            print(f"\nTo test file upload, create a sample file at: {sample_file}")
        
        print("\n" + "=" * 70)
        print("Tests Complete!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("Make sure the server is running: python run_api_server.py")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
