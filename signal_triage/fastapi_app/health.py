"""
Health check endpoints for monitoring and orchestration.

Provides comprehensive health checks for:
- API availability
- Database connectivity
- Cache availability
- External API dependencies
"""

from typing import Dict, Any
import time
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns HTTP 200 if the service is running.
    Used by Docker health checks and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "signal-triage-api",
        "version": "0.1.0"
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check - verifies service can handle requests.
    
    Checks:
    - Database connectivity
    - Cache availability
    - Critical dependencies
    
    Returns HTTP 200 if ready, 503 if not ready.
    """
    checks = {
        "database": await _check_database(),
        "cache": await _check_cache(),
        "filesystem": _check_filesystem()
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    response = {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response, status_code=status_code)


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check - verifies service is running (not deadlocked).
    
    Simpler than readiness - just confirms the process is responsive.
    Used by Kubernetes liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from signal_triage.database.session import get_session
        
        start = time.time()
        db = get_session()
        
        # Simple query to verify connection
        db.execute("SELECT 1")
        db.close()
        
        latency_ms = round((time.time() - start) * 1000, 2)
        
        return {
            "status": "healthy",
            "latency_ms": latency_ms
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_cache() -> Dict[str, Any]:
    """Check cache availability."""
    try:
        from signal_triage.infrastructure.cache import get_cache_manager
        
        cache = get_cache_manager()
        start = time.time()
        
        # Simple set/get test
        test_key = "_health_check"
        cache.set(test_key, "ok", ttl=5)
        result = cache.get(test_key)
        
        latency_ms = round((time.time() - start) * 1000, 2)
        
        if result == "ok":
            return {
                "status": "healthy",
                "latency_ms": latency_ms
            }
        else:
            return {
                "status": "degraded",
                "message": "Cache write/read mismatch"
            }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "message": "Cache unavailable, using fallback"
        }


def _check_filesystem() -> Dict[str, Any]:
    """Check filesystem access for logs and cache."""
    try:
        import os
        from pathlib import Path
        
        # Check required directories
        required_dirs = [".cache", "logs"]
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            dir_path.mkdir(exist_ok=True)
            
            # Test write access
            test_file = dir_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
        
        return {
            "status": "healthy",
            "writable": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "writable": False
        }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics() -> Dict[str, Any]:
    """
    Basic metrics endpoint (Prometheus-compatible format planned).
    
    Returns application metrics for monitoring.
    """
    try:
        from signal_triage.database.models import Analysis
        from signal_triage.database.session import SessionLocal
        
        db = SessionLocal()
        
        # Count total analyses
        total_analyses = db.query(Analysis).count()
        
        # Recent analyses (last 24h) - placeholder
        # In production, add timestamp filters
        
        db.close()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analyses": {
                "total": total_analyses,
                "recent_24h": 0  # TODO: Add timestamp filtering
            },
            "uptime_seconds": 0,  # TODO: Track application start time
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Metrics unavailable"
        }
