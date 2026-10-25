"""
Database Engine & Session Management
Provides managed connection pooling, declarative session generation,
atomic transaction context management, and non-blocking connectivity verification.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from backend.rakshagrid.config import rakshagrid_settings

logger = logging.getLogger("rakshagrid.database")

Base = declarative_base()

_engine = None
_SessionFactory = None


def get_engine(custom_url: Optional[str] = None):
    """Lazily initializes and caches the SQLAlchemy database engine."""
    global _engine
    if custom_url is not None:
        return _create_engine_for_url(custom_url)
    if _engine is None:
        db_url = rakshagrid_settings.effective_database_url
        _engine = _create_engine_for_url(db_url)
    return _engine


def _create_engine_for_url(db_url: str):
    """Helper to configure connection pool based on dialect."""
    if db_url.startswith("sqlite"):
        # In-memory or file-based SQLite configuration
        connect_args = {"check_same_thread": False}
        if ":memory:" in db_url:
            return create_engine(
                db_url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(db_url, connect_args=connect_args)

    # PostgreSQL connection configuration
    return create_engine(
        db_url,
        pool_size=rakshagrid_settings.DB_POOL_SIZE,
        max_overflow=rakshagrid_settings.DB_MAX_OVERFLOW,
        pool_timeout=rakshagrid_settings.DB_POOL_TIMEOUT_SECONDS,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def reset_engine(custom_url: Optional[str] = None):
    """Resets cached engine and session factory (primarily used for test fixture isolation)."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
    if custom_url:
        _engine = _create_engine_for_url(custom_url)
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory():
    """Lazily creates and returns the sessionmaker instance."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionFactory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def transactional_session() -> Generator[Session, None, None]:
    """
    Context manager guaranteeing atomic commit or rollback.
    Usage:
        with transactional_session() as db:
            db.add(incident)
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connectivity() -> Dict[str, Any]:
    """
    Safely tests connection to PostgreSQL without crashing if service is unreachable.
    Returns status metadata conforming to Phase 1 and 2 diagnostic reporting.
    """
    configured = rakshagrid_settings.is_database_configured
    host = rakshagrid_settings.POSTGRES_HOST
    port = rakshagrid_settings.POSTGRES_PORT
    database = rakshagrid_settings.POSTGRES_DB

    result = {
        "configured": configured,
        "host": host,
        "port": port,
        "database": database,
        "status": "unverified",
        "connection": False,
        "latency_ms": None,
        "detail": None,
    }

    try:
        import time
        engine = get_engine()
        t0 = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = round((time.time() - t0) * 1000, 2)
        result["status"] = "connected"
        result["connection"] = True
        result["latency_ms"] = latency
        result["detail"] = f"Successfully connected to PostgreSQL at {host}:{port}/{database}"
    except Exception as e:
        err_msg = str(e)
        if "could not connect to server" in err_msg or "Connection refused" in err_msg or "timeout" in err_msg.lower():
            result["status"] = "service_unavailable"
            result["detail"] = (
                f"PostgreSQL service unreachable on {host}:{port}. "
                "Phase 2 schema, migrations, and ORM models prepared; local PostgreSQL instance required for live persistent data."
            )
        elif "password authentication failed" in err_msg:
            result["status"] = "auth_failed"
            result["detail"] = "PostgreSQL authentication failed; please update POSTGRES_PASSWORD in .env."
        else:
            result["status"] = "disconnected"
            result["detail"] = f"Database connectivity check deferred: {err_msg[:120]}"

    return result
