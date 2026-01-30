# Comprehensive FastAPI Features Guide

## Overview

This guide covers the **complete** set of features available in the Signal Triage FastAPI integration, including advanced analysis parameters, job management, monitoring, and operational endpoints.

---

## Table of Contents

1. [Advanced Analysis Parameters](#advanced-analysis-parameters)
2. [Job Management Endpoints](#job-management-endpoints)
3. [Monitoring & Metrics](#monitoring--metrics)
4. [Error Handling & Warnings](#error-handling--warnings)
5. [Forensic Analysis Integration](#forensic-analysis-integration)
6. [Operational Features](#operational-features)
7. [Complete API Reference](#complete-api-reference)

---

## Advanced Analysis Parameters

### Full Analysis Request

```python
{
    # Basic parameters
    "document_url": "https://example.com/document.pdf",  # or file upload
    "ticker": "ABC",
    "cik": "0001234567",
    "analysis_type": "full",  # "full", "quick", or "forensic"
    
    # Webhook configuration
    "webhook_url": "https://your-app.com/webhook",
    "webhook_secret": "your-secret",
    
    # Advanced options
    "industry": "energy",  # Industry filter for benchmarking
    "geography": "north_america",  # Geography filter
    "require_audit_gate": false,  # Require auditor pass before publishing
    "include_tornado": true,  # Include tornado sensitivity analysis
    
    # Forensic analysis parameters
    "covenant_params": {
        "reported_ebitda": 100000000,
        "addbacks": 15000000,
        "total_debt": 500000000,
        "leverage_covenant": 5.0,
        "fccr_covenant": 2.0
    },
    "ch11_params": {
        "going_concern_ev": 300000000,
        "tangible_asset_pct": 0.5,
        "secured_debt": 250000000,
        "total_debt": 500000000
    }
}
```

### Parameter Descriptions

#### Analysis Type
- **`full`**: Complete analysis with all agents (Librarian, Quant, Benchmarker, Auditor)
- **`quick`**: Faster analysis with key metrics only
- **`forensic`**: Deep-dive analysis with enhanced scrutiny and forensic modules

#### Industry Filters (for Benchmarking)
- `energy`, `healthcare`, `technology`, `retail`, `manufacturing`, `financial_services`, etc.

#### Geography Filters (for Benchmarking)
- `north_america`, `europe`, `asia_pacific`, `latin_america`, `global`

#### Covenant Parameters (Optional)
- `reported_ebitda`: Company's reported EBITDA
- `addbacks`: Total EBITDA addbacks
- `total_debt`: Total debt outstanding
- `leverage_covenant`: Maximum leverage ratio (Total Debt / EBITDA)
- `fccr_covenant`: Minimum Fixed Charge Coverage Ratio

#### Chapter 11 Parameters (Optional)
- `going_concern_ev`: Going concern enterprise value
- `tangible_asset_pct`: Percentage of tangible assets (0-1)
- `secured_debt`: Total secured debt
- `total_debt`: Total debt outstanding
- `liquidation_value`: Optional, calculated if not provided

---

## Job Management Endpoints

### List Jobs

**GET /jobs**

Query and filter analysis jobs with pagination.

```python
import requests

response = requests.get(
    "http://localhost:8000/jobs",
    params={
        "status": "completed",  # Filter by status
        "limit": 50,  # Max results per page (max 100)
        "offset": 0  # Pagination offset
    }
)

data = response.json()
print(f"Total jobs: {data['total']}")
print(f"Page {data['page']}, showing {len(data['jobs'])} jobs")

for job in data['jobs']:
    print(f"Job {job['job_id']}: {job['status']}")
```

**Filter Options:**
- `status`: `pending`, `running`, `completed`, `failed`, `cancelled`
- `limit`: 1-100 (default 50)
- `offset`: For pagination

**Response:**
```json
{
    "jobs": [
        {
            "job_id": "uuid",
            "status": "completed",
            "created_at": "2026-01-29T12:00:00Z",
            "started_at": "2026-01-29T12:00:05Z",
            "completed_at": "2026-01-29T12:02:15Z",
            "analysis_id": 42,
            "error_message": null,
            "progress_pct": 100,
            "current_stage": "completed"
        }
    ],
    "total": 150,
    "page": 1,
    "page_size": 50
}
```

### Cancel Job

**POST /jobs/{job_id}/cancel**

Cancel a pending or running job.

```python
response = requests.post(
    f"http://localhost:8000/jobs/{job_id}/cancel"
)

print(response.json())
# {"message": "Job cancelled successfully", "job_id": "uuid"}
```

**Notes:**
- Only pending or running jobs can be cancelled
- Running jobs may not stop immediately
- Cancelled jobs are marked with status `cancelled`

### Retry Failed Job

**POST /jobs/{job_id}/retry**

Retry a failed job with the same parameters.

```python
response = requests.post(
    f"http://localhost:8000/jobs/{job_id}/retry"
)

data = response.json()
print(f"New job created: {data['new_job_id']}")
print(f"Original job: {data['original_job_id']}")
```

**Notes:**
- Only failed jobs can be retried
- Creates a new job with original parameters
- Original document must still exist
- File uploads cannot be retried (use URL instead)

---

## Monitoring & Metrics

### Metrics Endpoint

**GET /metrics**

Get comprehensive API usage statistics.

```python
response = requests.get("http://localhost:8000/metrics")
metrics = response.json()

print(f"Total jobs: {metrics['total_jobs']}")
print(f"Completed: {metrics['completed_jobs']}")
print(f"Failed: {metrics['failed_jobs']}")
print(f"Running: {metrics['running_jobs']}")
print(f"Pending: {metrics['pending_jobs']}")
print(f"Avg execution time: {metrics['avg_execution_time_seconds']:.2f}s")
print(f"Total documents: {metrics['total_documents']}")
print(f"Total analyses: {metrics['total_analyses']}")
```

**Response:**
```json
{
    "total_jobs": 250,
    "completed_jobs": 220,
    "failed_jobs": 10,
    "running_jobs": 2,
    "pending_jobs": 18,
    "avg_execution_time_seconds": 87.5,
    "total_documents": 180,
    "total_analyses": 230
}
```

**Use Cases:**
- Monitor system health
- Track success/failure rates
- Capacity planning
- Performance monitoring
- Dashboard integration

---

## Error Handling & Warnings

### Enhanced Analysis Response

The analysis response now includes warnings for non-fatal issues:

```json
{
    "analysis_id": 42,
    "distress_score": 0.73,
    "credit_opinion": "TIER 2: STRESSED",
    "warnings": [
        "Some market data sources unavailable, using cached data",
        "Report not published due to auditor gate failure",
        "LME risk scoring incomplete due to missing covenants"
    ],
    "key_findings": {...},
    "signals": {...}
}
```

### Warning Categories

1. **Data Quality Warnings**
   - Missing or incomplete data
   - Stale market data
   - Inferred values used

2. **Analysis Warnings**
   - Auditor gate failures
   - Critical variances detected
   - APR violations found

3. **Pipeline Warnings**
   - Agent execution issues
   - Incomplete extraction
   - Timeout warnings

---

## Forensic Analysis Integration

### Covenant Headroom Analysis

```python
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "document_url": "https://example.com/credit-agreement.pdf",
        "ticker": "ABC",
        "covenant_params": {
            "reported_ebitda": 100_000_000,
            "addbacks": 15_000_000,  # Aggressive addbacks
            "total_debt": 500_000_000,
            "leverage_covenant": 5.0,
            "fccr_covenant": 2.0
        }
    }
)
```

**Results in key_findings:**
```json
{
    "covenant_forensics": {
        "adjusted_ebitda": 105_000_000,  # After haircuts
        "leverage_ratio": 4.76,
        "leverage_headroom": 0.24,  # 24% headroom
        "leverage_headroom_pct": 5.05,
        "fccr": 2.15,
        "fccr_headroom": 0.15,
        "critical_distress": false,
        "warnings": ["Aggressive add-backs detected: 15% of reported EBITDA"]
    }
}
```

### Chapter 11 Feasibility

```python
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "document_url": "https://example.com/10k.pdf",
        "ticker": "ABC",
        "ch11_params": {
            "going_concern_ev": 300_000_000,
            "tangible_asset_pct": 0.5,
            "secured_debt": 250_000_000,
            "total_debt": 500_000_000
        }
    }
)
```

**Results in key_findings:**
```json
{
    "ch11_feasibility": {
        "liquidation_value": 150_000_000,
        "going_concern_premium": 1.0,  # 100% premium
        "secured_coverage": 0.6,  # 60% coverage
        "adequate_protection_required": 100_000_000,
        "feasible": false,
        "concerns": [
            "Secured debt exceeds liquidation value",
            "Going concern value depends on operational turnaround"
        ]
    }
}
```

---

## Operational Features

### Request Tracing

Every request is assigned a unique `request_id` for tracking:

```python
response = requests.post(...)
request_id = response.headers.get('X-Request-ID')  # Track requests
```

### Audit Logging

All API requests are logged to the database:

```sql
SELECT 
    timestamp,
    endpoint,
    method,
    response_status,
    response_time_ms,
    client_ip
FROM api_audit_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### Performance Monitoring

Track execution times for optimization:

```sql
SELECT 
    analysis_type,
    AVG(execution_time_seconds) as avg_time,
    MIN(execution_time_seconds) as min_time,
    MAX(execution_time_seconds) as max_time,
    COUNT(*) as count
FROM analyses
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY analysis_type;
```

---

## Complete API Reference

### All Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/` | GET | Health check | No |
| `/analyze` | POST | Submit analysis | Yes |
| `/jobs` | GET | List jobs | Yes |
| `/jobs/{job_id}` | GET | Get job status | Yes |
| `/jobs/{job_id}/cancel` | POST | Cancel job | Yes |
| `/jobs/{job_id}/retry` | POST | Retry failed job | Yes |
| `/analyses/{analysis_id}` | GET | Get analysis results | Yes |
| `/documents/{document_id}` | GET | Get document info | Yes |
| `/metrics` | GET | Get API metrics | Yes |
| `/docs` | GET | Swagger UI | No |
| `/redoc` | GET | ReDoc docs | No |

### Response Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Missing parameters, invalid values |
| 401 | Unauthorized | Invalid or missing API key |
| 404 | Not Found | Job, analysis, or document not found |
| 500 | Internal Error | Pipeline failure, database error |

---

## Python Client Example

Here's a comprehensive client that uses all features:

```python
import requests
import time
from typing import Optional, Dict, Any


class SignalTriageClient:
    """Comprehensive Python client for Signal Triage API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def analyze(
        self,
        document_url: Optional[str] = None,
        file_path: Optional[str] = None,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        analysis_type: str = "full",
        industry: Optional[str] = None,
        geography: Optional[str] = None,
        require_audit_gate: bool = False,
        include_tornado: bool = True,
        covenant_params: Optional[Dict] = None,
        ch11_params: Optional[Dict] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit comprehensive analysis request."""
        
        if file_path:
            # File upload
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "analysis_type": analysis_type,
                    "ticker": ticker or "",
                    "cik": cik or "",
                    "industry": industry or "",
                    "geography": geography or "",
                    "require_audit_gate": require_audit_gate,
                    "include_tornado": include_tornado,
                }
                
                response = requests.post(
                    f"{self.base_url}/analyze",
                    data=data,
                    files=files,
                    headers=self.headers
                )
        else:
            # URL analysis
            payload = {
                "document_url": document_url,
                "ticker": ticker,
                "cik": cik,
                "analysis_type": analysis_type,
                "industry": industry,
                "geography": geography,
                "require_audit_gate": require_audit_gate,
                "include_tornado": include_tornado,
                "covenant_params": covenant_params,
                "ch11_params": ch11_params,
                "webhook_url": webhook_url,
                "webhook_secret": webhook_secret,
            }
            
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                headers=self.headers
            )
        
        response.raise_for_status()
        return response.json()
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List jobs with filtering."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.base_url}/jobs",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        response = requests.get(
            f"{self.base_url}/jobs/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a job."""
        response = requests.post(
            f"{self.base_url}/jobs/{job_id}/cancel",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def retry_job(self, job_id: str) -> Dict[str, Any]:
        """Retry a failed job."""
        response = requests.post(
            f"{self.base_url}/jobs/{job_id}/retry",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        """Get analysis results."""
        response = requests.get(
            f"{self.base_url}/analyses/{analysis_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get API metrics."""
        response = requests.get(
            f"{self.base_url}/metrics",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Wait for job completion with optional progress callback."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            job = self.get_job(job_id)
            
            if callback:
                callback(job)
            
            if job["status"] == "completed":
                return self.get_analysis(job["analysis_id"])
            elif job["status"] == "failed":
                raise Exception(f"Job failed: {job.get('error_message')}")
            elif job["status"] == "cancelled":
                raise Exception("Job was cancelled")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job did not complete within {timeout}s")


# Usage example
if __name__ == "__main__":
    client = SignalTriageClient(api_key="your-api-key")
    
    # Submit comprehensive analysis
    job = client.analyze(
        document_url="https://example.com/credit-agreement.pdf",
        ticker="ABC",
        analysis_type="forensic",
        industry="energy",
        include_tornado=True,
        covenant_params={
            "reported_ebitda": 100_000_000,
            "addbacks": 15_000_000,
            "total_debt": 500_000_000,
            "leverage_covenant": 5.0,
        }
    )
    
    print(f"Job submitted: {job['job_id']}")
    
    # Wait with progress callback
    def progress_callback(job):
        print(f"Status: {job['status']}")
        if job.get('progress_pct'):
            print(f"Progress: {job['progress_pct']:.1f}%")
    
    analysis = client.wait_for_job(job['job_id'], callback=progress_callback)
    
    print(f"\nDistress Score: {analysis['distress_score']}")
    print(f"Credit Opinion: {analysis['credit_opinion']}")
    
    if analysis.get('warnings'):
        print(f"\nWarnings:")
        for warning in analysis['warnings']:
            print(f"  - {warning}")
    
    # Check metrics
    metrics = client.get_metrics()
    print(f"\nAPI Metrics:")
    print(f"  Success rate: {metrics['completed_jobs'] / metrics['total_jobs'] * 100:.1f}%")
    print(f"  Avg execution time: {metrics['avg_execution_time_seconds']:.1f}s")
```

---

## Next Steps

See also:
- [API_GUIDE.md](API_GUIDE.md) - Complete API reference
- [FASTAPI_INTEGRATION_SUMMARY.md](FASTAPI_INTEGRATION_SUMMARY.md) - Integration details
- `test_api_integration.py` - Working test examples

For production deployment, see the deployment section in the API Guide.
