# Signal Triage API Guide

## Overview

The Signal Triage API provides programmatic access to the full document analysis pipeline. Submit documents via URL or file upload, track analysis jobs asynchronously, and retrieve comprehensive results including distress scoring, covenant analysis, and recovery waterfall calculations.

## Quick Start

### 1. Start the API Server

```bash
# Development mode (auto-reload)
python run_api_server.py

# Production mode (4 workers, optimized)
python run_api_server.py --production

# Custom configuration
python run_api_server.py --host 0.0.0.0 --port 8080 --workers 4
```

### 2. Access API Documentation

Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/

## Authentication

API authentication is optional but recommended for production use.

### Configuring API Keys

Add API keys to your `config.yaml`:

```yaml
fastapi:
  api_keys:
    - "your-secret-api-key-1"
    - "your-secret-api-key-2"
  api_key_header: "X-API-Key"
```

### Using API Keys

Include the API key in request headers:

```bash
curl -H "X-API-Key: your-secret-api-key-1" \
     http://localhost:8000/analyze
```

```python
import requests

headers = {"X-API-Key": "your-secret-api-key-1"}
response = requests.post(
    "http://localhost:8000/analyze",
    json=payload,
    headers=headers
)
```

## API Endpoints

### Health Check

**GET /**

Check API health and available data providers.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "available_providers": {
    "yfinance": true,
    "fred": true,
    "sec_edgar": true
  }
}
```

### Submit Analysis Job

**POST /analyze**

Submit a document for analysis. Supports both URL ingestion and file upload.

**Request Body (URL):**
```json
{
  "document_url": "https://example.com/document.pdf",
  "ticker": "ABC",
  "cik": "0001234567",
  "analysis_type": "full",
  "webhook_url": "https://your-app.com/webhook",
  "webhook_secret": "your-webhook-secret"
}
```

**Request Body (File Upload):**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@document.pdf" \
  -F "ticker=ABC" \
  -F "analysis_type=full"
```

**Parameters:**
- `document_url` (string, optional): URL to document (alternative to file upload)
- `file` (file, optional): File upload (alternative to document_url)
- `ticker` (string, optional): Company ticker symbol
- `cik` (string, optional): Company CIK number
- `analysis_type` (string, default: "full"): Analysis type
  - `full`: Complete analysis with all agents
  - `quick`: Faster analysis with key metrics only
  - `forensic`: Deep-dive analysis with enhanced scrutiny
- `webhook_url` (string, optional): Webhook URL for async notification
- `webhook_secret` (string, optional): Webhook secret for HMAC authentication

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-01-29T12:00:00Z"
}
```

**Status Codes:**
- `200`: Job created successfully
- `400`: Invalid request (missing file/URL)
- `401`: Invalid or missing API key
- `500`: Internal server error

### Check Job Status

**GET /jobs/{job_id}**

Check the status of an analysis job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-29T12:00:00Z",
  "started_at": "2026-01-29T12:00:01Z",
  "completed_at": "2026-01-29T12:01:30Z",
  "analysis_id": 42,
  "error_message": null
}
```

**Job Status Values:**
- `pending`: Job queued, not yet started
- `running`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered an error
- `cancelled`: Job was cancelled

### Get Analysis Results

**GET /analyses/{analysis_id}**

Retrieve complete analysis results.

**Response:**
```json
{
  "analysis_id": 42,
  "document_id": 10,
  "distress_score": 0.73,
  "credit_opinion": "TIER 2: STRESSED",
  "key_findings": {
    "tier": "TIER 2: STRESSED",
    "signals_detected": [
      "Liquidity_Squeeze",
      "Covenant_Headroom_Thin"
    ],
    "covenant_score": 0.65,
    "financial_score": 0.78,
    "market_score": 0.81
  },
  "signals": {
    "librarian": {
      "baskets": [...],
      "covenants": [...]
    },
    "quant": {
      "recoveries": [...],
      "ev_used": 500000000
    },
    "benchmarker": {
      "market_multiples": {...},
      "precedent_recoveries": [...]
    },
    "auditor": {
      "passed": true,
      "variance_flags": []
    }
  },
  "created_at": "2026-01-29T12:01:30Z",
  "execution_time_seconds": 89.5
}
```

### Get Document Details

**GET /documents/{document_id}**

Retrieve document metadata and analysis history.

**Response:**
```json
{
  "document_id": 10,
  "filename": "document.pdf",
  "ticker": "ABC",
  "cik": "0001234567",
  "created_at": "2026-01-29T12:00:00Z",
  "analyses_count": 2,
  "analyses": [
    {
      "analysis_id": 42,
      "distress_score": 0.73,
      "created_at": "2026-01-29T12:01:30Z"
    }
  ]
}
```

## Webhooks

Configure webhooks to receive notifications when analysis jobs complete.

### Webhook Payload

When an analysis completes, the API will POST to your webhook URL:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "analysis_id": 42,
  "timestamp": "2026-01-29T12:01:30Z"
}
```

### Webhook Authentication

If you provide a `webhook_secret`, the API will include an HMAC signature in the `X-Webhook-Signature` header:

```python
import hmac
import hashlib
import json

def verify_webhook(payload: dict, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        secret.encode(),
        json.dumps(payload).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Python Client Example

```python
import time
import requests

class SignalTriageClient:
    """Python client for Signal Triage API."""
    
    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def health_check(self) -> dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    def analyze_url(
        self, 
        document_url: str,
        ticker: str | None = None,
        analysis_type: str = "full",
        webhook_url: str | None = None,
    ) -> dict:
        """Submit document URL for analysis."""
        payload = {
            "document_url": document_url,
            "analysis_type": analysis_type,
        }
        if ticker:
            payload["ticker"] = ticker
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        response = requests.post(
            f"{self.base_url}/analyze",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_file(
        self,
        file_path: str,
        ticker: str | None = None,
        analysis_type: str = "full",
    ) -> dict:
        """Submit file for analysis."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"analysis_type": analysis_type}
            if ticker:
                data["ticker"] = ticker
            
            response = requests.post(
                f"{self.base_url}/analyze",
                data=data,
                files=files,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    def get_job_status(self, job_id: str) -> dict:
        """Get job status."""
        response = requests.get(
            f"{self.base_url}/jobs/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_analysis(self, analysis_id: int) -> dict:
        """Get analysis results."""
        response = requests.get(
            f"{self.base_url}/analyses/{analysis_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict:
        """Wait for job to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if status["status"] == "completed":
                return self.get_analysis(status["analysis_id"])
            elif status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error_message')}")
            elif status["status"] == "cancelled":
                raise Exception("Job was cancelled")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job did not complete within {timeout}s")


# Usage example
client = SignalTriageClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Submit analysis
job = client.analyze_url(
    document_url="https://example.com/document.pdf",
    ticker="ABC"
)

# Wait for completion
analysis = client.wait_for_job(job["job_id"])

print(f"Distress Score: {analysis['distress_score']}")
print(f"Credit Opinion: {analysis['credit_opinion']}")
```

## Configuration

### FastAPI Settings

Configure the API in `config.yaml`:

```yaml
fastapi:
  # API server settings
  host: "127.0.0.1"
  port: 8000
  workers: 1
  
  # Security
  api_keys:
    - "key1"
    - "key2"
  api_key_header: "X-API-Key"
  
  # CORS (for browser-based clients)
  cors_origins:
    - "http://localhost:3000"
    - "https://your-app.com"
  
  # Webhooks
  webhook_timeout: 10
  webhook_retry_attempts: 3
```

## Performance Considerations

### Analysis Time

Typical analysis times:
- **Quick Analysis**: 30-60 seconds
- **Full Analysis**: 60-120 seconds
- **Forensic Analysis**: 120-300 seconds

Factors affecting performance:
- Document length
- Market data freshness (caching helps)
- Server resources (CPU, memory)
- Number of concurrent jobs

### Rate Limiting

The API uses background task queues to handle concurrent requests efficiently. However, consider:
- Each analysis is CPU and memory intensive
- Recommended: 1-4 concurrent analyses per worker
- Production: Use multiple workers (`--workers 4`)

### Caching

The pipeline caches:
- Market data queries (configurable TTL)
- URL/EDGAR document fetches
- Benchmark corpus data

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "detail": "Either file or document_url required"
}
```

**401 Unauthorized**
```json
{
  "detail": "Invalid or missing API key"
}
```

**404 Not Found**
```json
{
  "detail": "Job not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error: <error message>"
}
```

### Retry Strategy

For transient errors (network, timeout), implement exponential backoff:

```python
import time

def retry_with_backoff(func, max_attempts=3):
    """Retry with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
```

## Monitoring

### Audit Logs

All API requests are logged to the database (`api_audit_logs` table):
- Endpoint and method
- Response status and time
- Client IP and user agent
- API key hash (for tracking)

Query audit logs:
```sql
SELECT 
    endpoint,
    method,
    response_status,
    AVG(response_time_ms) as avg_time_ms,
    COUNT(*) as request_count
FROM api_audit_logs
WHERE timestamp >= NOW() - INTERVAL '1 day'
GROUP BY endpoint, method, response_status
ORDER BY request_count DESC;
```

### Health Monitoring

Monitor API health:
```bash
curl http://localhost:8000/
```

Check for:
- Database connectivity
- Available market data providers
- Recent API response times

## Deployment

### Production Checklist

- [ ] Configure API keys
- [ ] Set up proper CORS origins
- [ ] Configure webhook timeout and retries
- [ ] Enable JSON logging (`--production`)
- [ ] Use multiple workers (`--workers 4`)
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Document backup strategy

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run_api_server.py", "--production", "--host", "0.0.0.0"]
```

```bash
docker build -t signal-triage-api .
docker run -p 8000:8000 signal-triage-api
```

## Support

For issues, questions, or feature requests:
- Check API documentation: http://localhost:8000/docs
- Review logs: `logs/api.log`
- Inspect database: `signal_triage.db`
- Test with: `python test_api_integration.py`
