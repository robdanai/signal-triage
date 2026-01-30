"""
SQLAlchemy Models for Signal Triage Database.

Production-grade models with:
- Relationship tracking
- Version history
- Audit logging
- Job queue management
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    JSON,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class JobStatus(PyEnum):
    """Status of analysis job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Document(Base):
    """
    Document record.
    
    Tracks uploaded/ingested documents for analysis.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Document metadata
    filename = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    content_type = Column(String(128))
    file_size_bytes = Column(Integer)
    
    # Source information
    source_url = Column(String(1024))
    source_type = Column(String(64))  # "upload", "url", "sec_filing", etc.
    
    # Company/issuer information
    company_name = Column(String(512))
    ticker = Column(String(16), index=True)
    cik = Column(String(16), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_documents_ticker_created", "ticker", "created_at"),
        Index("idx_documents_cik_created", "cik", "created_at"),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', ticker='{self.ticker}')>"


class DocumentVersion(Base):
    """
    Document version history.
    
    Tracks changes to documents over time.
    """
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    version_number = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    content_diff = Column(Text)  # Optional: store diffs for text documents
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(128))  # User/system that created version
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    
    __table_args__ = (
        Index("idx_document_versions_doc_version", "document_id", "version_number", unique=True),
    )
    
    def __repr__(self):
        return f"<DocumentVersion(doc_id={self.document_id}, version={self.version_number})>"


class Analysis(Base):
    """
    Analysis result record.
    
    Stores complete analysis output for a document.
    """
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Analysis metadata
    analysis_type = Column(String(64), nullable=False)  # "full", "quick", "forensic", etc.
    pipeline_version = Column(String(32))  # Version of analysis pipeline used
    
    # Results (stored as JSON for flexibility)
    signals = Column(JSON)  # Extracted signals
    distress_score = Column(Float)
    credit_opinion = Column(Text)
    key_findings = Column(JSON)  # List of key findings
    
    # Market data used
    market_data_sources = Column(JSON)  # List of market data sources consulted
    
    # Performance metrics
    execution_time_seconds = Column(Float)
    tokens_used = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    document = relationship("Document", back_populates="analyses")
    job = relationship("AnalysisJob", back_populates="analysis", uselist=False)
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, doc_id={self.document_id}, score={self.distress_score})>"


class AnalysisJob(Base):
    """
    Analysis job tracking.
    
    Manages asynchronous analysis jobs with webhook support.
    """
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Job metadata
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Request details
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    analysis_type = Column(String(64), nullable=False)
    request_params = Column(JSON)  # Additional request parameters
    
    # Results
    analysis_id = Column(Integer, ForeignKey("analyses.id"), index=True)
    error_message = Column(Text)
    
    # Webhook configuration
    webhook_url = Column(String(1024))
    webhook_secret = Column(String(128))  # Optional: for webhook authentication
    webhook_attempts = Column(Integer, default=0)
    webhook_last_attempt = Column(DateTime)
    webhook_delivered = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="job")
    
    __table_args__ = (
        Index("idx_jobs_status_created", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<AnalysisJob(job_id='{self.job_id}', status={self.status.value})>"


class APIAuditLog(Base):
    """
    API audit log.
    
    Tracks all API requests for monitoring and debugging.
    """
    __tablename__ = "api_audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Request details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    endpoint = Column(String(256), nullable=False, index=True)
    method = Column(String(16), nullable=False)
    
    # Request metadata
    request_id = Column(String(64), index=True)
    client_ip = Column(String(64))
    user_agent = Column(String(512))
    api_key_hash = Column(String(64))  # Hashed API key for tracking
    
    # Request/Response
    request_body = Column(Text)
    response_status = Column(Integer, index=True)
    response_time_ms = Column(Float)
    
    # Error tracking
    error_type = Column(String(128))
    error_message = Column(Text)
    
    __table_args__ = (
        Index("idx_audit_timestamp_endpoint", "timestamp", "endpoint"),
        Index("idx_audit_status", "response_status", "timestamp"),
    )
    
    def __repr__(self):
        return f"<APIAuditLog(endpoint='{self.endpoint}', status={self.response_status})>"
