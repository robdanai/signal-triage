"""
Database layer for Signal Triage.

Provides SQLAlchemy models and database session management for:
- Analysis history tracking
- Document version control
- Job queue management
- API audit logs
"""

from signal_triage.database.models import (
    Base,
    Document,
    Analysis,
    AnalysisJob,
    APIAuditLog,
    DocumentVersion,
    JobStatus,
)
from signal_triage.database.session import (
    get_engine,
    get_session,
    init_db,
    session_scope,
)

__all__ = [
    "Base",
    "Document",
    "Analysis",
    "AnalysisJob",
    "APIAuditLog",
    "DocumentVersion",
    "JobStatus",
    "get_engine",
    "get_session",
    "init_db",
    "session_scope",
]
