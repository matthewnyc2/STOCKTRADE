"""
Database connection management for Crypto Quant Laboratory.

Provides connection pooling and session management for SQLAlchemy.
Supports both SQLite (development) and TimescaleDB/PostgreSQL (production).
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool

# Database URL configuration
# Use SQLite for development, can switch to PostgreSQL/TimescaleDB in production
DEFAULT_SQLITE_URL = "sqlite:///./data/crypto_quant.db"
DEFAULT_POSTGRES_URL = "postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Environment-based database URL selection
DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL


def _sqlite_engine(url: str) -> Engine:
    """Create SQLite engine with appropriate settings."""
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _postgres_engine(url: str) -> Engine:
    """Create PostgreSQL/TimescaleDB engine with connection pooling."""
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )


def create_engine_for_url(url: str) -> Engine:
    """
    Create appropriate SQLAlchemy engine based on database URL.

    Args:
        url: Database connection URL

    Returns:
        Configured SQLAlchemy Engine
    """
    if url.startswith("sqlite"):
        # Ensure data directory exists for SQLite
        db_path = url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path and db_path != ":memory:":
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

        return _sqlite_engine(url)

    # PostgreSQL / TimescaleDB
    return _postgres_engine(url)


class DatabaseConnection:
    """
    Database connection manager.

    Manages engine lifecycle and provides session factory.
    Singleton pattern ensures single engine per application.
    """

    _instance: Optional["DatabaseConnection"] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._engine is None:
            self._engine = create_engine_for_url(DATABASE_URL)
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            )

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        return self._engine

    def get_session_factory(self) -> sessionmaker:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        return self._session_factory

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db.session() as session:
                # perform database operations
                session.commit()

        Yields:
            SQLAlchemy Session
        """
        session = self.get_session_factory()()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close the database engine and dispose of connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get the global database connection instance."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def get_db_session() -> Session:
    """
    Get a new database session.

    Note: Caller is responsible for closing the session.
    For automatic cleanup, use the session context manager instead.

    Returns:
        SQLAlchemy Session
    """
    return get_db_connection().get_session_factory()()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get a database session context manager with automatic commit/rollback.

    This is the preferred way to get a session for API endpoints.
    Automatically commits on success and rolls back on error.

    Usage:
        with get_db_context() as session:
            # perform database operations
            # auto-commit on success, auto-rollback on error

    Yields:
        SQLAlchemy Session
    """
    db = get_db_connection()
    with db.session() as session:
        yield session


def init_db(drop_all: bool = False) -> None:
    """
    Initialize database schema.

    Creates all tables. Use drop_all=True to reset the database.

    Args:
        drop_all: If True, drops all existing tables first
    """
    from database.models import BaseModel  # noqa: import to avoid circular

    engine = get_db_connection().engine

    if drop_all:
        BaseModel.metadata.drop_all(bind=engine)

    BaseModel.metadata.create_all(bind=engine)


def close_db() -> None:
    """Close database connections."""
    global _db_connection
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
