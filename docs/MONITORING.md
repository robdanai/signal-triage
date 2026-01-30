# Monitoring & Observability Guide

Production monitoring setup for Signal Triage.

## Table of Contents

- [Health Checks](#health-checks)
- [Logging](#logging)
- [Metrics](#metrics)
- [Alerting](#alerting)
- [Distributed Tracing](#distributed-tracing)
- [Cost Monitoring](#cost-monitoring)

## Health Checks

### Built-in Endpoints

Signal Triage provides three health check endpoints:

#### 1. Basic Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T10:00:00Z",
  "service": "signal-triage-api",
  "version": "0.1.0"
}
```

**Use:** Docker healthcheck, basic uptime monitoring

#### 2. Readiness Check
```bash
GET /health/ready
```

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2026-01-29T10:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5.2
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 1.3
    },
    "filesystem": {
      "status": "healthy",
      "writable": true
    }
  }
}
```

**Use:** Load balancer health checks, Kubernetes readiness probes

#### 3. Liveness Check
```bash
GET /health/live
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2026-01-29T10:00:00Z"
}
```

**Use:** Kubernetes liveness probes (detect deadlock)

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

### Docker Healthcheck

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## Logging

### Structured Logging

Signal Triage uses structured JSON logging in production:

```python
from signal_triage.logging_config import setup_logging

# Setup logging
setup_logging(
    log_level="INFO",
    log_file="/app/logs/signal-triage.log",
    json_format=True  # JSON for production
)
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Development only | Variable values, function calls |
| INFO | Normal operations | Request received, analysis complete |
| WARNING | Important events | Cache miss, API rate limit approaching |
| ERROR | Error conditions | Database connection failed, API timeout |

### Log Format (JSON)

```json
{
  "timestamp": "2026-01-29T10:00:00Z",
  "level": "INFO",
  "logger": "signal_triage.pipeline",
  "message": "Pipeline completed successfully",
  "request_id": "abc123",
  "duration_ms": 1523.4,
  "document_id": 42
}
```

### Centralized Logging

#### AWS CloudWatch

```python
# Install watchtower
pip install watchtower

# Configure
import watchtower
import logging

logger = logging.getLogger()
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group="/ecs/signal-triage",
    stream_name="api"
))
```

#### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

**Logstash config:**
```conf
# logstash.conf
input {
  file {
    path => "/app/logs/*.log"
    codec => json
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "signal-triage-%{+YYYY.MM.dd}"
  }
}
```

## Metrics

### Basic Metrics Endpoint

```bash
GET /metrics
```

**Response:**
```json
{
  "timestamp": "2026-01-29T10:00:00Z",
  "analyses": {
    "total": 1234,
    "recent_24h": 45
  },
  "uptime_seconds": 3600
}
```

### Prometheus Integration

**Add prometheus-client:**

```bash
pip install prometheus-client
```

**Instrument code:**

```python
# signal_triage/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
analysis_requests = Counter(
    'signal_triage_analysis_requests_total',
    'Total analysis requests',
    ['status']
)

analysis_duration = Histogram(
    'signal_triage_analysis_duration_seconds',
    'Analysis duration in seconds',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

active_analyses = Gauge(
    'signal_triage_active_analyses',
    'Number of currently running analyses'
)

lme_flags_detected = Counter(
    'signal_triage_lme_flags_total',
    'Total LME flags detected',
    ['category']
)

# Endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Usage in pipeline:**

```python
from signal_triage.monitoring.metrics import (
    analysis_requests,
    analysis_duration,
    active_analyses
)

@analysis_duration.time()
def run_analysis():
    active_analyses.inc()
    try:
        # Run analysis
        analysis_requests.labels(status='success').inc()
    except Exception:
        analysis_requests.labels(status='error').inc()
    finally:
        active_analyses.dec()
```

**Prometheus scrape config:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'signal-triage'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboards

**Docker compose addition:**

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

**Key metrics to monitor:**

- **Request Rate:** Requests per second
- **Error Rate:** % of failed requests
- **Response Time:** p50, p95, p99 latency
- **Active Analyses:** Currently running
- **Queue Depth:** Pending jobs
- **Database Connections:** Active pool usage
- **Cache Hit Rate:** % cache hits
- **API Cost:** $ spent on external APIs

## Alerting

### Alertmanager (Prometheus)

```yaml
# alertmanager.yml
route:
  receiver: 'team-email'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'alerts@yourcompany.com'
        from: 'alertmanager@yourcompany.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@yourcompany.com'
        auth_password: 'your-app-password'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
```

**Alert rules:**

```yaml
# prometheus-alerts.yml
groups:
  - name: signal_triage_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(signal_triage_analysis_requests_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(signal_triage_analysis_duration_seconds_bucket[5m])) > 60
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow analysis response time"
          description: "p95 response time is {{ $value }}s"

      # Service down
      - alert: ServiceDown
        expr: up{job="signal-triage"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Signal Triage API is down"
          description: "Service has been down for 2 minutes"

      # High memory usage
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="signal-triage-api"} / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Database connection pool exhausted
      - alert: DatabasePoolExhausted
        expr: signal_triage_db_connections_active == signal_triage_db_connections_max
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
```

### Uptime Monitoring

**Recommended services:**
- UptimeRobot (free tier available)
- Pingdom
- StatusCake
- AWS CloudWatch Alarms

**Monitor:**
- `/health` endpoint every 1-5 minutes
- Alert if down for > 2 minutes
- Alert if response time > 5 seconds

## Distributed Tracing

### OpenTelemetry Integration

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

```python
# signal_triage/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument FastAPI
def instrument_app(app):
    FastAPIInstrumentor.instrument_app(app)
```

**Jaeger (docker-compose):**

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"  # Jaeger UI
      - "14268:14268"
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
```

## Cost Monitoring

### API Cost Tracking

Track costs for external APIs:

```python
# Track API usage
api_costs = {
    'edgar': 0,  # Free
    'fred': 0,   # Free
    'alphavantage': 0.02,  # per call
    '9fin': 5.00,  # per query
    'bloomberg': 10.00,  # per query
}

def log_api_cost(provider: str, cost: float):
    """Log API cost for monitoring."""
    with session_scope() as session:
        session.execute(
            "INSERT INTO api_costs (provider, cost, timestamp) VALUES (:p, :c, :t)",
            {'p': provider, 'c': cost, 't': datetime.utcnow()}
        )
```

### Cost Dashboard

**Monthly cost query:**

```sql
SELECT 
    provider,
    COUNT(*) as calls,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost_per_call
FROM api_costs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY provider
ORDER BY total_cost DESC;
```

### Budget Alerts

```python
# Set monthly budget
MONTHLY_BUDGET = 1000  # $1000/month

# Check budget
def check_budget():
    current_spend = get_month_to_date_spend()
    if current_spend > MONTHLY_BUDGET * 0.8:
        send_alert(f"80% of monthly budget used: ${current_spend}")
    if current_spend > MONTHLY_BUDGET:
        send_alert(f"Budget exceeded: ${current_spend}")
```

## Best Practices

### 1. Monitor These Key Metrics

- **Golden Signals:**
  - Latency (response time)
  - Traffic (requests per second)
  - Errors (error rate %)
  - Saturation (resource usage %)

### 2. Set SLOs (Service Level Objectives)

Example SLOs:
- 99.9% uptime (43 minutes downtime/month)
- p95 response time < 5 seconds
- Error rate < 0.1%

### 3. Alert Fatigue Prevention

- Alert only on actionable issues
- Use severity levels (critical, warning, info)
- Implement alert grouping and deduplication
- Set appropriate thresholds (don't alert on transient spikes)

### 4. Regular Review

- Weekly: Review dashboards and trends
- Monthly: Analyze cost and performance
- Quarterly: Update alerts and SLOs

## Quick Start Monitoring Stack

```bash
# Start full monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
# Kibana: http://localhost:5601
```

## Troubleshooting

### High CPU Usage

```bash
# Check processes
docker stats

# Profile code
pip install py-spy
py-spy record -o profile.svg -- python run_api_server.py
```

### Memory Leaks

```bash
# Install memory profiler
pip install memory-profiler

# Profile
python -m memory_profiler script.py
```

### Database Slow Queries

```sql
-- PostgreSQL slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)
