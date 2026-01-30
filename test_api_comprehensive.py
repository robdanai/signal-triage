#!/usr/bin/env python
"""
Comprehensive API test suite for Signal Triage FastAPI.

Tests all advanced features including:
- Advanced analysis parameters
- Job management (list, cancel, retry)
- Metrics endpoint
- Forensic analysis integration
- Error handling
"""

from __future__ import annotations

import json
import time
import requests
from pathlib import Path
from typing import Optional


API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = ""  # Set if API keys are configured


class APITestSuite:
    """Comprehensive test suite for Signal Triage API."""
    
    def __init__(self, base_url: str = API_BASE_URL, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.test_results = []
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append((name, passed, message))
        print(f"  [{status}] {name}")
        if message:
            print(f"      {message}")
    
    def test_health_check(self):
        """Test 1: Health check endpoint."""
        print("\n" + "=" * 70)
        print("TEST 1: Health Check")
        print("=" * 70)
        
        try:
            response = requests.get(f"{self.base_url}/")
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                data.get("status") == "healthy" and
                "available_providers" in data
            )
            
            self.log_test(
                "Health check endpoint",
                passed,
                f"Status: {data.get('status')}, Database: {data.get('database')}"
            )
            
            print(f"\n  Available providers:")
            for provider, available in data.get("available_providers", {}).items():
                symbol = "✓" if available else "✗"
                print(f"    [{symbol}] {provider}")
            
            return passed
            
        except Exception as e:
            self.log_test("Health check endpoint", False, str(e))
            return False
    
    def test_advanced_analysis(self):
        """Test 2: Advanced analysis with all parameters."""
        print("\n" + "=" * 70)
        print("TEST 2: Advanced Analysis Parameters")
        print("=" * 70)
        
        try:
            # Submit analysis with advanced parameters
            payload = {
                "document_url": "https://httpbin.org/html",  # Sample URL
                "ticker": "TEST",
                "analysis_type": "full",
                "industry": "technology",
                "geography": "north_america",
                "require_audit_gate": False,
                "include_tornado": True,
                "covenant_params": {
                    "reported_ebitda": 100_000_000,
                    "addbacks": 15_000_000,
                    "total_debt": 500_000_000,
                    "leverage_covenant": 5.0,
                    "fccr_covenant": 2.0
                },
                "ch11_params": {
                    "going_concern_ev": 300_000_000,
                    "tangible_asset_pct": 0.5,
                    "secured_debt": 250_000_000,
                    "total_debt": 500_000_000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_test(
                    "Submit advanced analysis",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
            
            job = response.json()
            job_id = job["job_id"]
            
            self.log_test(
                "Submit advanced analysis",
                True,
                f"Job ID: {job_id}"
            )
            
            print(f"\n  Submitted with parameters:")
            print(f"    Industry: {payload['industry']}")
            print(f"    Geography: {payload['geography']}")
            print(f"    Covenant analysis: Enabled")
            print(f"    Chapter 11 analysis: Enabled")
            print(f"    Tornado analysis: {payload['include_tornado']}")
            
            return job_id
            
        except Exception as e:
            self.log_test("Submit advanced analysis", False, str(e))
            return None
    
    def test_list_jobs(self):
        """Test 3: List jobs with filtering."""
        print("\n" + "=" * 70)
        print("TEST 3: List Jobs")
        print("=" * 70)
        
        try:
            # List all jobs
            response = requests.get(
                f"{self.base_url}/jobs",
                params={"limit": 10},
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_test("List all jobs", False, response.text)
                return False
            
            data = response.json()
            total_jobs = data.get("total", 0)
            
            self.log_test(
                "List all jobs",
                True,
                f"Found {total_jobs} jobs, showing {len(data.get('jobs', []))}"
            )
            
            # List by status
            for status in ["pending", "running", "completed", "failed"]:
                response = requests.get(
                    f"{self.base_url}/jobs",
                    params={"status": status, "limit": 5},
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("total", 0)
                    print(f"    {status}: {count} jobs")
            
            return True
            
        except Exception as e:
            self.log_test("List jobs", False, str(e))
            return False
    
    def test_metrics(self):
        """Test 4: Metrics endpoint."""
        print("\n" + "=" * 70)
        print("TEST 4: Metrics & Statistics")
        print("=" * 70)
        
        try:
            response = requests.get(
                f"{self.base_url}/metrics",
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_test("Get metrics", False, response.text)
                return False
            
            metrics = response.json()
            
            self.log_test("Get metrics", True)
            
            print(f"\n  System Metrics:")
            print(f"    Total jobs: {metrics.get('total_jobs', 0)}")
            print(f"    Completed: {metrics.get('completed_jobs', 0)}")
            print(f"    Failed: {metrics.get('failed_jobs', 0)}")
            print(f"    Running: {metrics.get('running_jobs', 0)}")
            print(f"    Pending: {metrics.get('pending_jobs', 0)}")
            
            if metrics.get('avg_execution_time_seconds'):
                print(f"    Avg execution time: {metrics['avg_execution_time_seconds']:.2f}s")
            
            print(f"\n  Data:")
            print(f"    Total documents: {metrics.get('total_documents', 0)}")
            print(f"    Total analyses: {metrics.get('total_analyses', 0)}")
            
            # Calculate success rate
            total = metrics.get('total_jobs', 0)
            completed = metrics.get('completed_jobs', 0)
            if total > 0:
                success_rate = (completed / total) * 100
                print(f"\n  Success rate: {success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            self.log_test("Get metrics", False, str(e))
            return False
    
    def test_job_management(self, job_id: Optional[str] = None):
        """Test 5: Job management (cancel, retry)."""
        print("\n" + "=" * 70)
        print("TEST 5: Job Management")
        print("=" * 70)
        
        if not job_id:
            print("  Skipping: No job ID available")
            return False
        
        try:
            # Get job status
            response = requests.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_test("Get job status", False, response.text)
                return False
            
            job = response.json()
            self.log_test(
                "Get job status",
                True,
                f"Status: {job['status']}"
            )
            
            # Try to cancel if still pending/running
            if job['status'] in ['pending', 'running']:
                response = requests.post(
                    f"{self.base_url}/jobs/{job_id}/cancel",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    self.log_test("Cancel job", True, "Job cancelled")
                else:
                    self.log_test("Cancel job", False, response.text)
            else:
                print(f"  [SKIP] Cancel job (status: {job['status']})")
            
            # Try to retry if failed
            if job['status'] == 'failed':
                response = requests.post(
                    f"{self.base_url}/jobs/{job_id}/retry",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        "Retry failed job",
                        True,
                        f"New job: {data['new_job_id']}"
                    )
                else:
                    self.log_test("Retry failed job", False, response.text)
            else:
                print(f"  [SKIP] Retry job (status: {job['status']})")
            
            return True
            
        except Exception as e:
            self.log_test("Job management", False, str(e))
            return False
    
    def test_complete_workflow(self):
        """Test 6: Complete workflow (submit, poll, retrieve)."""
        print("\n" + "=" * 70)
        print("TEST 6: Complete Workflow")
        print("=" * 70)
        
        try:
            # Submit simple analysis
            payload = {
                "document_url": "https://httpbin.org/html",
                "ticker": "WORKFLOW_TEST",
                "analysis_type": "quick"
            }
            
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code != 200:
                self.log_test("Submit job", False, response.text)
                return False
            
            job = response.json()
            job_id = job["job_id"]
            
            self.log_test("Submit job", True, f"Job ID: {job_id}")
            
            # Poll for completion (with timeout)
            print(f"\n  Polling for completion...")
            max_attempts = 30  # 60 seconds max
            for attempt in range(max_attempts):
                time.sleep(2)
                
                response = requests.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    continue
                
                job_status = response.json()
                status = job_status["status"]
                print(f"    [{attempt + 1}/{max_attempts}] Status: {status}")
                
                if status == "completed":
                    self.log_test("Job completion", True, f"Completed in {attempt * 2}s")
                    
                    # Retrieve analysis
                    analysis_id = job_status["analysis_id"]
                    response = requests.get(
                        f"{self.base_url}/analyses/{analysis_id}",
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        analysis = response.json()
                        self.log_test(
                            "Retrieve analysis",
                            True,
                            f"Analysis ID: {analysis_id}"
                        )
                        
                        print(f"\n  Analysis Results:")
                        print(f"    Distress Score: {analysis.get('distress_score')}")
                        print(f"    Credit Opinion: {analysis.get('credit_opinion')}")
                        print(f"    Execution Time: {analysis.get('execution_time_seconds', 0):.2f}s")
                        print(f"    Pipeline Version: {analysis.get('pipeline_version')}")
                        
                        if analysis.get('warnings'):
                            print(f"\n  Warnings:")
                            for warning in analysis['warnings']:
                                print(f"    - {warning}")
                        
                        return True
                    else:
                        self.log_test("Retrieve analysis", False, response.text)
                        return False
                
                elif status == "failed":
                    self.log_test(
                        "Job completion",
                        False,
                        f"Failed: {job_status.get('error_message')}"
                    )
                    return False
            
            self.log_test("Job completion", False, "Timeout after 60s")
            return False
            
        except Exception as e:
            self.log_test("Complete workflow", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, p, _ in self.test_results if p)
        total = len(self.test_results)
        
        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print(f"\nFailed tests:")
            for name, passed, message in self.test_results:
                if not passed:
                    print(f"  ✗ {name}")
                    if message:
                        print(f"    {message}")
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 70)
        print("Signal Triage API - Comprehensive Test Suite")
        print("=" * 70)
        print(f"\nServer: {self.base_url}")
        print(f"API Key: {'Configured' if self.headers.get('X-API-Key') else 'Not configured'}")
        
        # Test 1: Health check
        if not self.test_health_check():
            print("\n✗ Health check failed - server may not be running")
            print("  Start server with: python run_api_server.py")
            return
        
        # Test 2: Advanced analysis
        job_id = self.test_advanced_analysis()
        
        # Test 3: List jobs
        self.test_list_jobs()
        
        # Test 4: Metrics
        self.test_metrics()
        
        # Test 5: Job management
        if job_id:
            self.test_job_management(job_id)
        
        # Test 6: Complete workflow
        self.test_complete_workflow()
        
        # Print summary
        self.print_summary()


def main():
    """Main entry point."""
    test_suite = APITestSuite(base_url=API_BASE_URL, api_key=API_KEY)
    
    try:
        test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("  Make sure the server is running: python run_api_server.py")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
