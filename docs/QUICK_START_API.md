# Quick Start: Signal Triage Production API

## 🚀 5-Minute Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and add at least one API key (optional but recommended)
# Minimum: No API keys needed for SEC EDGAR (free)
# Recommended: Add FRED_API_KEY for Treasury yields
```

### 3. Initialize Database

```bash
python -c "from signal_triage.database import init_db; init_db()"
```

### 4. Start API Server

```bash
# Development mode (auto-reload)
python run_api_server.py

# Production mode
python run_api_server.py --production
```

### 5. Test the API

Open http://localhost:8000/docs in your browser for interactive API documentation.

Or use curl:

```bash
# Health check
curl http://localhost:8000/

# Analyze a document
curl -X POST http://localhost:8000/analyze \
  -F "file=@your_document.pdf" \
  -F 'request={"ticker":"TSLA","analysis_type":"full"}'
```

## 📊 Using Market Data Clients

### SEC EDGAR (No API Key Required)

```python
from signal_triage.api import SECEdgarClient

client = SECEdgarClient()

# Lookup CIK by ticker
cik = client.lookup_cik("AAPL")
print(f"Apple CIK: {cik}")

# Get company financials
financials = client.get_company_financials(cik)
print(f"Revenue: ${financials['revenue']:,}")
print(f"Total Debt: ${financials['total_debt']:,}")

# Get recent 8-K filings
filings = client.get_recent_8k_comparables(limit=10)
for filing in filings:
    print(f"{filing['name']} - {filing['filing_date']}")
```

### Market Pricing (Requires API Key)

```python
from signal_triage.api import MarketPricingClient

# Auto-selects best available provider (IEX Cloud > Alpha Vantage > FRED)
client = MarketPricingClient()

# Get stock price
price = client.get_stock_price("AAPL")
print(f"AAPL: ${price['price']}")

# Get Treasury yield
treasury = client.get_treasury_yield("10Y")
print(f"10Y Treasury: {treasury['yield_pct']}%")

# Calculate yield spread
spread = client.calculate_yield_spread(target_yield=12.5, treasury_maturity="10Y")
print(f"Spread: {spread['spread_bps']} bps over Treasury")
```

## 🔑 API Key Setup

### FRED (Free, Recommended)

1. Register at https://fred.stlouisfed.org/
2. Get API key from https://fred.stlouisfed.org/docs/api/api_key.html
3. Add to `.env`:
   ```
   FRED_API_KEY=your_key_here
   ```

### Alpha Vantage (Free Tier: 25 calls/day)

1. Register at https://www.alphavantage.co/support/#api-key
2. Add to `.env`:
   ```
   ALPHAVANTAGE_API_KEY=your_key_here
   ```

### IEX Cloud (Commercial)

1. Register at https://iexcloud.io/
2. Add to `.env`:
   ```
   IEXCLOUD_API_TOKEN=your_token_here
   ```

## 📁 Project Structure

```
signal_triage/
├── api/                    # Production-grade API clients
│   ├── sec_edgar.py       # SEC EDGAR client
│   └── market_pricing.py  # Market pricing client
├── infrastructure/         # Core infrastructure
│   ├── rate_limiter.py    # Rate limiting
│   ├── cache.py           # Caching
│   ├── circuit_breaker.py # Circuit breaker
│   └── retry.py           # Retry logic
├── database/              # Database layer
│   ├── models.py          # SQLAlchemy models
│   └── session.py         # Session management
├── fastapi_app/           # FastAPI application
│   └── main.py            # API endpoints
├── config.py              # Configuration management
└── logging_config.py      # Logging setup
```

## 🛠️ Configuration

### Environment Variables

```bash
# Database (SQLite by default)
DATABASE_URL=sqlite:///signal_triage.db

# Cache backend
CACHE_BACKEND=file  # Options: file, redis, memory

# Market data API keys (all optional)
FRED_API_KEY=your_key
ALPHAVANTAGE_API_KEY=your_key
IEXCLOUD_API_TOKEN=your_token

# API security
API_KEYS=key1,key2  # Leave empty for open access
```

### Cache Backends

**File Cache (Default)**
- Persistent across restarts
- No additional setup required
- Location: `.cache/` directory

**Redis Cache**
```bash
# Install Redis
sudo apt-get install redis-server

# Configure
CACHE_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Memory Cache**
- Fastest, but non-persistent
- Good for development
```bash
CACHE_BACKEND=memory
```

## 📊 Database

### SQLite (Default)

No setup required. Database file: `signal_triage.db`

### PostgreSQL (Production)

```bash
# Create database
createdb signal_triage

# Configure
DATABASE_URL=postgresql://user:pass@localhost:5432/signal_triage

# Initialize
python -c "from signal_triage.database import init_db; init_db()"
```

## 🔍 Testing

```bash
# Run all tests
pytest tests/

# Test specific module
pytest tests/test_market_data_client.py -v

# Test with coverage
pytest --cov=signal_triage tests/
```

## 📝 API Endpoints

### POST /analyze

Submit document for analysis:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F 'request={"ticker":"TSLA","analysis_type":"full","webhook_url":"https://your-webhook.com/callback"}'
```

Returns:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-15T12:00:00Z"
}
```

### GET /jobs/{job_id}

Check job status:

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

### GET /analyses/{analysis_id}

Get analysis results:

```bash
curl http://localhost:8000/analyses/42
```

## 🐛 Troubleshooting

### Rate Limiting

If you see "Rate limit exceeded":

```python
from signal_triage.infrastructure import get_rate_limiter

limiter = get_rate_limiter()
print(f"Available tokens: {limiter.get_available_tokens('sec_edgar')}")
```

### Circuit Breaker

If service is unavailable:

```python
from signal_triage.infrastructure import get_circuit_breaker

breaker = get_circuit_breaker("sec_edgar")
stats = breaker.get_stats()
print(f"Circuit state: {stats['state']}")
print(f"Failures: {stats['failure_count']}")
```

### Cache Issues

Clear cache:

```python
from signal_triage.infrastructure import get_cache_manager

cache = get_cache_manager()
cache.clear()
```

## 📚 Next Steps

1. **Read Full Documentation**: See `docs/API_INFRASTRUCTURE.md`
2. **Configure Production Database**: Use PostgreSQL for production
3. **Add More API Keys**: Enable more data sources
4. **Deploy**: See production deployment guide
5. **Monitor**: Set up logging and monitoring

## 🆘 Support

For issues or questions:
1. Check `docs/API_INFRASTRUCTURE.md` for detailed documentation
2. Review logs in `logs/api.log` (production mode)
3. Check database: `sqlite3 signal_triage.db` and run `.tables`
