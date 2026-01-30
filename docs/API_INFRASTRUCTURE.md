# Signal Triage API Infrastructure

## Overview

This document describes the production-grade market data and API infrastructure for Signal Triage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ POST /analyze│  │ GET /jobs/:id│  │ GET /analyses│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌────────▼──────────┐
│  Database Layer │                    │ Market Data Clients│
│  (SQLAlchemy)   │                    │  (Production-Grade)│
│                 │                    │                    │
│ - Documents     │                    │ - SEC EDGAR        │
│ - Analyses      │                    │ - FRED             │
│ - Jobs          │                    │ - Alpha Vantage    │
│ - Audit Logs    │                    │ - IEX Cloud        │
└─────────────────┘                    └────────┬───────────┘
                                                │
                    ┌───────────────────────────┴──────────┐
                    │                                      │
            ┌───────▼────────┐                  ┌─────────▼────────┐
            │ Infrastructure  │                  │  External APIs   │
            │                 │                  │                  │
            │ - Rate Limiter  │                  │ - SEC.gov        │
            │ - Cache Manager │                  │ - FRED           │
            │ - Circuit Breaker│                 │ - Alpha Vantage  │
            │ - Retry Logic   │                  │ - IEX Cloud      │
            └─────────────────┘                  └──────────────────┘
```

## Components

### 1. Configuration Management (`signal_triage/config.py`)

Centralized configuration with environment-based settings:

```python
from signal_triage.config import get_config

config = get_config()
print(config.api.sec_rate_limit)  # 10 requests/second
print(config.cache.backend)  # "file", "redis", or "memory"
```

**Environment Variables:**
- `FRED_API_KEY`: FRED API key for Treasury yields
- `ALPHAVANTAGE_API_KEY`: Alpha Vantage API key
- `IEXCLOUD_API_TOKEN`: IEX Cloud API token
- `DATABASE_URL`: Database connection string (default: SQLite)
- `CACHE_BACKEND`: Cache backend ("file", "redis", "memory")
- `API_KEYS`: Comma-separated API keys for authentication

### 2. Infrastructure Components

#### Rate Limiter (`signal_triage/infrastructure/rate_limiter.py`)

Token bucket rate limiter for API compliance:

```python
from signal_triage.infrastructure import get_rate_limiter

limiter = get_rate_limiter()
limiter.acquire("sec_edgar")  # Blocks until token available
```

#### Cache Manager (`signal_triage/infrastructure/cache.py`)

Multi-backend cache with TTL:

```python
from signal_triage.infrastructure import get_cache_manager

cache = get_cache_manager()
key = cache.make_key("sec_edgar", "filings", cik="0001652044")
cache.set(key, data, ttl=3600)
cached = cache.get(key)
```

**Backends:**
- **File**: Persistent cache on disk (default)
- **Redis**: Distributed cache (requires Redis server)
- **Memory**: In-memory cache (fast, non-persistent)

#### Circuit Breaker (`signal_triage/infrastructure/circuit_breaker.py`)

Fault tolerance for failing services:

```python
from signal_triage.infrastructure import get_circuit_breaker

breaker = get_circuit_breaker("sec_edgar")
result = breaker.call(api_function, *args)
```

**States:**
- **CLOSED**: Normal operation
- **OPEN**: Service failing, requests blocked
- **HALF_OPEN**: Testing recovery

#### Retry Strategy (`signal_triage/infrastructure/retry.py`)

Exponential backoff with jitter:

```python
from signal_triage.infrastructure import get_retry_strategy

retry = get_retry_strategy()
result = retry.call(api_function, *args)
```

### 3. Market Data Clients

#### SEC EDGAR Client (`signal_triage/api/sec_edgar.py`)

```python
from signal_triage.api import SECEdgarClient

client = SECEdgarClient()

# Lookup CIK by ticker
cik = client.lookup_cik("AAPL")  # "0000320193"

# Get company info
info = client.get_company_info(cik)

# Get filings
filings = client.get_filings(cik, form_type="10-K", limit=5)

# Get financials (XBRL data)
financials = client.get_company_financials(cik)

# Detect 8-K distress events
events = client.detect_8k_distress_events(cik, limit=10)

# Get recent 8-K comparables
comparables = client.get_recent_8k_comparables(limit=20)
```

#### Market Pricing Client (`signal_triage/api/market_pricing.py`)

Switchable provider (Alpha Vantage, IEX Cloud, FRED):

```python
from signal_triage.api import MarketPricingClient

client = MarketPricingClient()  # Auto-selects best provider

# Get stock price
price = client.get_stock_price("AAPL")

# Get Treasury yield
yield_data = client.get_treasury_yield("10Y")

# Calculate yield spread
spread = client.calculate_yield_spread(target_yield=12.5, treasury_maturity="10Y")

# Get company financials (IEX Cloud only)
financials = client.get_company_financials("AAPL")
```

### 4. Database Layer

#### Models (`signal_triage/database/models.py`)

- **Document**: Uploaded/ingested documents
- **Analysis**: Analysis results
- **AnalysisJob**: Job tracking with webhook support
- **DocumentVersion**: Version history
- **APIAuditLog**: API request audit log

#### Session Management (`signal_triage/database/session.py`)

```python
from signal_triage.database import session_scope, Document

with session_scope() as session:
    doc = Document(filename="test.pdf", file_hash="abc123")
    session.add(doc)
    # Auto-commits on success, rolls back on exception
```

### 5. FastAPI Application

#### Start Server

```bash
# Development
python -m uvicorn signal_triage.fastapi_app.main:create_app --factory --reload

# Production
python -m uvicorn signal_triage.fastapi_app.main:create_app --factory \
    --host 0.0.0.0 --port 8000 --workers 4
```

#### Endpoints

**POST /analyze**
Submit document for analysis (async):

```bash
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F 'request={"ticker":"TSLA","analysis_type":"full"}'
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2024-01-15T12:00:00Z"
}
```

**GET /jobs/{job_id}**
Check job status:

```bash
curl http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000 \
  -H "X-API-Key: your-api-key"
```

**GET /analyses/{analysis_id}**
Get analysis results:

```bash
curl http://localhost:8000/analyses/42 \
  -H "X-API-Key: your-api-key"
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/signal_triage

# Optional: Market Data APIs
FRED_API_KEY=your_fred_api_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key
IEXCLOUD_API_TOKEN=your_iexcloud_token

# Optional: Cache
CACHE_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional: API Security
API_KEYS=key1,key2,key3
```

### 3. Initialize Database

```python
from signal_triage.database import init_db
init_db()
```

Or use Alembic for migrations:

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### 4. Start Application

```bash
python -m uvicorn signal_triage.fastapi_app.main:create_app --factory --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## Production Deployment

### PostgreSQL Setup

```sql
CREATE DATABASE signal_triage;
CREATE USER signal_triage_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE signal_triage TO signal_triage_user;
```

### Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
redis-server
```

### Systemd Service

Create `/etc/systemd/system/signal-triage-api.service`:

```ini
[Unit]
Description=Signal Triage API
After=network.target

[Service]
User=signal-triage
WorkingDirectory=/opt/signal-triage
Environment="DATABASE_URL=postgresql://user:pass@localhost/signal_triage"
Environment="CACHE_BACKEND=redis"
ExecStart=/opt/signal-triage/venv/bin/uvicorn signal_triage.fastapi_app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable signal-triage-api
sudo systemctl start signal-triage-api
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.signal-triage.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/
```

Response includes:
- API status
- Database connectivity
- Available market data providers

### Logs

Configure logging in `signal_triage/logging_config.py`:

```python
from signal_triage.logging_config import setup_logging

setup_logging(
    log_level="INFO",
    log_file="/var/log/signal-triage/api.log",
    json_format=True
)
```

### Metrics

Query audit logs:

```python
from signal_triage.database import session_scope, APIAuditLog

with session_scope() as session:
    # Request count by endpoint
    logs = session.query(APIAuditLog).filter_by(endpoint="/analyze").count()
    
    # Average response time
    avg_time = session.query(func.avg(APIAuditLog.response_time_ms)).scalar()
```

## Testing

```bash
# Run tests
pytest tests/

# Test with coverage
pytest --cov=signal_triage tests/

# Test specific module
pytest tests/test_market_data_client.py -v
```

## Troubleshooting

### Rate Limiting

If hitting rate limits:

```python
from signal_triage.infrastructure import get_rate_limiter

limiter = get_rate_limiter()
print(limiter.get_available_tokens("sec_edgar"))
```

### Circuit Breaker

Check circuit breaker status:

```python
from signal_triage.infrastructure import get_circuit_breaker

breaker = get_circuit_breaker("sec_edgar")
print(breaker.get_stats())
```

### Cache Issues

Clear cache:

```python
from signal_triage.infrastructure import get_cache_manager

cache = get_cache_manager()
cache.clear()
```

## Next Steps

1. **Integrate with existing pipeline**: Connect FastAPI endpoints to `signal_triage.pipeline`
2. **Add authentication**: Implement JWT tokens or OAuth2
3. **Monitoring & Alerting**: Set up Prometheus/Grafana
4. **Load balancing**: Deploy multiple workers behind load balancer
5. **Add more providers**: Integrate Bloomberg, 9fin, S&P Capital IQ
