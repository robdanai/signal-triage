"""
FastAPI Application for Signal Triage.

Production-grade REST API with:
- Document analysis endpoints
- Async job processing
- Webhook delivery
- Rate limiting and authentication
"""

from signal_triage.fastapi_app.main import create_app

__all__ = ["create_app"]
