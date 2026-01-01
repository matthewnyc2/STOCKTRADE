"""
Tests for database connection and initialization.
"""

import os
import pytest
import tempfile
from pathlib import Path

from sqlalchemy import text


@pytest.fixture
def test_db_url():
    """Provide a test database URL using a temporary file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    yield url
    # Cleanup
    try:
        os.remove(path)
    except OSError:
        pass


class TestDatabaseConnection:
    """Tests for database connection management."""

    def test_connection_creation(self, test_db_url):
        """Test database connection can be created."""
        # Import after setting test URL
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        # Override URL for test
        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = test_db_url

        try:
            from database.connection import DatabaseConnection

            db = DatabaseConnection()
            assert db is not None
            assert db.engine is not None

        finally:
            conn_module.DATABASE_URL = original_url

    def test_session_factory(self, test_db_url):
        """Test session factory works."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = test_db_url

        try:
            from database.connection import get_db_connection

            db = get_db_connection()
            factory = db.get_session_factory()
            assert factory is not None

        finally:
            conn_module.DATABASE_URL = original_url

    def test_context_manager(self, test_db_url):
        """Test session context manager."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = test_db_url

        try:
            from database.connection import get_db_connection

            db = get_db_connection()
            with db.session() as session:
                result = session.execute(text("SELECT 1")).scalar()
                assert result == 1

        finally:
            conn_module.DATABASE_URL = original_url


class TestDatabaseInit:
    """Tests for database initialization."""

    def test_init_db_creates_tables(self, test_db_url):
        """Test database initialization creates all tables via migrations."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = test_db_url

        try:
            from database.connection import get_db_connection
            from database.migrations import run_migrations

            # Run migrations
            run_migrations()

            # Check tables exist
            db = get_db_connection()
            with db.session() as session:
                result = session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()

                table_names = {row[0] for row in result}

                # Check key tables exist
                expected_tables = {
                    "strategies",
                    "strategy_layers",
                    "signals",
                    "layer_signals",
                    "backtest_results",
                    "equity_points",
                    "trades",
                    "portfolios",
                    "positions",
                    "whales",
                    "whale_activities",
                    "whale_constellations",
                    "ml_models",
                    "settings",
                    "ai_reasoning_sessions",
                    "schema_migrations",
                }

                assert expected_tables.issubset(table_names)

        finally:
            conn_module.DATABASE_URL = original_url

    def test_migrations_idempotent(self, test_db_url):
        """Test running migrations multiple times is safe."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = test_db_url

        try:
            from database.connection import get_db_connection
            from database.migrations import run_migrations

            # Run migrations twice
            run_migrations()
            run_migrations()

            # Check tables still exist and are intact
            db = get_db_connection()
            with db.session() as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM strategies")
                ).scalar()
                # Should not error, count should be 0
                assert result == 0

        finally:
            conn_module.DATABASE_URL = original_url
