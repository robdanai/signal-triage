# Deployment Guide

This guide covers deploying Signal Triage to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Security](#security)

## Prerequisites

### Required
- Docker 20.10+ and docker-compose 2.0+
- PostgreSQL 15+ (or use docker-compose)
- 4GB+ RAM recommended
- SSL/TLS certificate for HTTPS

### Optional
- Redis for caching (included in docker-compose)
- Reverse proxy (nginx, Traefik, Caddy)
- Container orchestration (Kubernetes, ECS, Cloud Run)

## Docker Deployment

### Quick Start (Development)

```bash
# Clone repository
git clone https://github.com/yourusername/signal-triage.git
cd signal-triage

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Access services
# API: http://localhost:8000
# Dashboard: http://localhost:8501
# API Docs: http://localhost:8000/docs
```

### Production Deployment

1. **Update environment variables**

```bash
# .env file for production
ENVIRONMENT=production
DEBUG=false

# Strong database password
POSTGRES_PASSWORD=<strong-password-here>

# Database URL
DATABASE_URL=postgresql://signaltriage:<strong-password>@postgres:5432/signal_triage

# API Keys (comma-separated)
API_KEYS=key1_production,key2_production

# CORS (restrict to your domain)
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Market Data APIs
SEC_USER_AGENT=YourCompany/1.0 (contact@yourcompany.com)
FRED_API_KEY=your_fred_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key
# ... other API keys
```

2. **Start services**

```bash
docker-compose up -d
```

3. **Verify health**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

4. **Set up reverse proxy** (nginx example)

```nginx
# /etc/nginx/sites-available/signal-triage

upstream signal_triage_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # API proxy
    location / {
        proxy_pass http://signal_triage_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running analyses
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health checks (no auth required)
    location /health {
        proxy_pass http://signal_triage_api;
        access_log off;
    }
}
```

### Docker Compose Override for Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    # Production PostgreSQL settings
    command: postgres -c max_connections=200 -c shared_buffers=256MB
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 2G
    
  api:
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G
      replicas: 2
    environment:
      LOG_LEVEL: INFO
      ENVIRONMENT: production
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### AWS ECS

1. **Build and push image**

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t signal-triage:latest .
docker tag signal-triage:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/signal-triage:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/signal-triage:latest
```

2. **Create ECS task definition** (example)

```json
{
  "family": "signal-triage",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "signal-triage-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/signal-triage:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "API_KEYS", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/signal-triage",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

3. **Use RDS for PostgreSQL**
   - Create RDS PostgreSQL 15 instance
   - Use secrets manager for credentials
   - Configure security groups

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy signal-triage \
  --image gcr.io/your-project/signal-triage:latest \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-secrets="DATABASE_URL=signal-triage-db:latest,API_KEYS=signal-triage-keys:latest"
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: signal-triage-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: signal-triage-api
  template:
    metadata:
      labels:
        app: signal-triage-api
    spec:
      containers:
      - name: api
        image: signal-triage:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: signal-triage-secrets
              key: database-url
        - name: ENVIRONMENT
          value: production
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: signal-triage-api-service
spec:
  selector:
    app: signal-triage-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options.

**Critical Settings:**

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `production` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `API_KEYS` | Comma-separated keys | `key1,key2,key3` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed origins | `https://yourdomain.com` |

### Scaling Configuration

**API Workers:**
```bash
# Adjust based on CPU cores
API_WORKERS=4  # 2 × CPU cores recommended
```

**Database Connections:**
```python
# In code or environment
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=10
```

**Redis Cache:**
```bash
CACHE_BACKEND=redis
REDIS_MAX_CONNECTIONS=50
```

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Readiness (checks dependencies)
curl http://localhost:8000/health/ready

# Liveness
curl http://localhost:8000/health/live

# Metrics
curl http://localhost:8000/metrics
```

### Logging

**View logs:**
```bash
# Docker
docker-compose logs -f api

# Follow specific service
docker logs -f signal-triage-api

# Kubernetes
kubectl logs -f deployment/signal-triage-api
```

**Log levels:**
- `DEBUG`: Verbose (development only)
- `INFO`: Normal operations (production default)
- `WARNING`: Important events
- `ERROR`: Errors only

### Application Performance Monitoring (APM)

**Add Sentry (recommended):**

```bash
pip install sentry-sdk[fastapi]
```

```python
# In signal_triage/fastapi_app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()]
)
```

## Backup & Recovery

### Database Backups

**Automated backups (PostgreSQL):**

```bash
# Backup script (backup.sh)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="signal_triage_backup_${TIMESTAMP}.sql.gz"

docker exec signal-triage-db pg_dump -U signaltriage signal_triage | gzip > /backups/$BACKUP_FILE

# Retain last 7 days
find /backups -name "signal_triage_backup_*.sql.gz" -mtime +7 -delete
```

**Cron job:**
```cron
0 2 * * * /path/to/backup.sh
```

**Restore:**
```bash
gunzip -c backup.sql.gz | docker exec -i signal-triage-db psql -U signaltriage signal_triage
```

### Redis Backups

Redis uses AOF (append-only file) by default in our docker-compose:

```yaml
redis:
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

### Document Storage

If using file storage for uploaded documents:

```bash
# Backup uploads directory
rsync -av --delete /app/data/ /backups/data/
```

## Security

### SSL/TLS

**Let's Encrypt with Certbot:**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal (cron)
0 0 * * * certbot renew --quiet
```

### Secrets Management

**Never commit:**
- API keys
- Database passwords
- JWT secrets
- Service credentials

**Use:**
- AWS Secrets Manager / Parameter Store
- Google Secret Manager
- HashiCorp Vault
- Kubernetes Secrets

### Rate Limiting

Add nginx rate limiting:

```nginx
# /etc/nginx/nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    
    server {
        location /analyze {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://signal_triage_api;
        }
    }
}
```

### Security Headers

Already included in nginx config above:
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`

### Firewall

```bash
# UFW example
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Maintenance

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Check health
curl http://localhost:8000/health/ready
```

### Database Migrations

If using Alembic:

```bash
docker-compose exec api alembic upgrade head
```

### Monitoring Disk Usage

```bash
# Check volumes
docker system df -v

# Clean old images
docker image prune -a

# Clean old containers
docker container prune
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Check resource limits
docker stats

# Verify environment
docker-compose config
```

### Database connection errors

```bash
# Test database connectivity
docker-compose exec api python -c "from signal_triage.database.session import SessionLocal; db = SessionLocal(); db.execute('SELECT 1'); print('OK')"

# Check PostgreSQL logs
docker-compose logs postgres
```

### High memory usage

```bash
# Reduce API workers
API_WORKERS=2

# Limit container memory
docker-compose.yml:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Health endpoint: `/health/ready`
- Review CONTRIBUTING.md for development setup
- Open issue on GitHub with deployment details
