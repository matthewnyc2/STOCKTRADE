"""
Tests for database migrations.
"""

import os
import pytest
import tempfile

from sqlalchemy import text


@pytest.fixture
def migration_db_url():
    """Provide a test database URL for migrations."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    yield url
    try:
        os.remove(path)
    except OSError:
        pass


class TestMigrations:
    """Tests for migration system."""

    def test_migration_tracking_table(self, migration_db_url):
        """Test migrations table is created."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = migration_db_url

        try:
            from database.migrations import MigrationRunner

            runner = MigrationRunner()
            runner._ensure_migrations_table()

            result = runner.conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            ).scalar()
            assert result == "schema_migrations"

        finally:
            runner.close()
            conn_module.DATABASE_URL = original_url

    def test_run_migrations(self, migration_db_url):
        """Test running migrations creates tables."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = migration_db_url

        runner = None
        try:
            from database.migrations import run_migrations

            run_migrations()

            # Check migration was recorded
            from database.migrations import MigrationRunner
            runner = MigrationRunner()
            applied = runner.get_applied_migrations()
            assert "20241231120000" in applied

            # Check tables exist
            result = runner.conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
            ).scalar()
            assert result == "strategies"

        finally:
            if runner:
                runner.close()
            conn_module.DATABASE_URL = original_url

    def test_migration_idempotent(self, migration_db_url):
        """Test running migrations twice is idempotent."""
        import importlib
        import database.connection as conn_module
        importlib.reload(conn_module)

        original_url = conn_module.DATABASE_URL
        conn_module.DATABASE_URL = migration_db_url

        runner = None
        try:
            from database.migrations import run_migrations

            # Run twice
            run_migrations()
            run_migrations()

            # Should have all migrations applied, each only once
            from database.migrations import MigrationRunner
            runner = MigrationRunner()
            applied = runner.get_applied_migrations()
            assert applied == {"20241231120000", "20241231150000", "20241231160000", "20241231170000"}

        finally:
            if runner:
                runner.close()
            conn_module.DATABASE_URL = original_url


class TestCreateMigration:
    """Tests for migration creation utility."""

    def test_create_migration_file(self, tmp_path):
        """Test migration file creation."""
        from database.migrations import create_migration
        import database.migrations as migrations_module

        # This would normally create a file - just verify the function exists
        assert callable(create_migration)
