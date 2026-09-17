"""Tests for database engine/session configuration.

Regression coverage for engine creation across pool classes. SQLite uses
NullPool, which does not accept ``pool_size``/``max_overflow``; passing those
kwargs raises ``TypeError`` at ``create_engine`` time.
"""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy.pool import NullPool, QueuePool


@pytest.fixture
def reset_engine():
    """Reset the module-level engine singleton around each test."""
    import signal_triage.database.session as session_mod

    session_mod._engine = None
    session_mod._SessionLocal = None
    yield session_mod
    session_mod._engine = None
    session_mod._SessionLocal = None


def test_sqlite_engine_uses_nullpool(monkeypatch, reset_engine, tmp_path):
    """SQLite databases must build a NullPool engine without pool sizing args."""
    db_path = tmp_path / "unit_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    import signal_triage.config as config_mod

    importlib.reload(config_mod)
    session_mod = reset_engine
    importlib.reload(session_mod)
    session_mod._engine = None
    session_mod._SessionLocal = None

    engine = session_mod.get_engine()

    assert isinstance(engine.pool, NullPool)

    session_mod.init_db()
    with session_mod.session_scope() as session:
        assert session is not None


def test_postgres_url_selects_queuepool(monkeypatch, reset_engine):
    """Non-SQLite URLs should select QueuePool with sizing options applied."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    import signal_triage.config as config_mod

    importlib.reload(config_mod)
    session_mod = reset_engine
    importlib.reload(session_mod)
    session_mod._engine = None
    session_mod._SessionLocal = None

    engine = session_mod.get_engine()

    assert isinstance(engine.pool, QueuePool)
