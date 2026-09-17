"""
Database Session Management.

Provides thread-safe database connection pooling and session management.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from signal_triage.config import get_config
from signal_triage.database.models import Base


logger = logging.getLogger(__name__)


# Global engine and session factory
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """
    Get SQLAlchemy engine (singleton).
    
    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine
    
    if _engine is None:
        config = get_config()
        db_url = config.database.database_url
        
        # Determine pool class based on database type
        engine_kwargs: dict = {
            "pool_pre_ping": True,  # Verify connections before using
            "echo": config.database.echo_sql,
        }
        if db_url.startswith("sqlite"):
            # SQLite: use NullPool (no connection pooling). NullPool does not
            # accept pool_size/max_overflow, so those must be omitted here.
            engine_kwargs["poolclass"] = NullPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}  # Allow multi-threading
        else:
            # PostgreSQL, MySQL, etc.: use QueuePool with sizing options.
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = config.database.pool_size
            engine_kwargs["pool_recycle"] = config.database.pool_recycle
            engine_kwargs["max_overflow"] = config.database.pool_max_overflow
            engine_kwargs["connect_args"] = {}
        
        _engine = create_engine(db_url, **engine_kwargs)
        
        logger.info(f"Database engine created: {db_url.split('://')[0]}")
    
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get session factory (singleton).
    
    Returns:
        SQLAlchemy sessionmaker.
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


def get_session() -> Session:
    """
    Get new database session.
    
    Returns:
        SQLAlchemy Session instance.
    
    Note:
        Caller is responsible for closing session.
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide transactional scope for database operations.
    
    Yields:
        SQLAlchemy Session instance.
    
    Usage:
        with session_scope() as session:
            doc = Document(filename="test.pdf")
            session.add(doc)
            # Automatically commits on success, rolls back on exception
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """
    Initialize database (create all tables).
    
    Should be called once at application startup.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def drop_all_tables():
    """
    Drop all tables (DANGER: for testing only).
    
    WARNING: This will delete all data!
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
