"""
Migration runner for applying and rolling back migrations.
"""

import os
from typing import Optional

from sqlalchemy import Connection, text

from database.connection import get_db_connection
from database.migrations.base import BaseMigration


class MigrationRunner:
    """
    Migration runner for managing database schema migrations.

    Tracks applied migrations and applies new ones in order.
    """

    def __init__(self) -> None:
        """Initialize migration runner."""
        self._conn: Optional[Connection] = None

    @property
    def conn(self) -> Connection:
        """Get or create database connection."""
        if self._conn is None:
            engine = get_db_connection().engine
            self._conn = engine.connect()
        return self._conn

    def _ensure_migrations_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist."""
        self.conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(20) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        )
        self.conn.commit()

    def get_applied_migrations(self) -> set[str]:
        """
        Get set of applied migration versions.

        Returns:
            Set of applied migration version strings
        """
        self._ensure_migrations_table()

        result = self.conn.execute(text("SELECT version FROM schema_migrations"))
        return {row[0] for row in result}

    def record_migration(self, version: str) -> None:
        """
        Record a migration as applied.

        Args:
            version: Migration version string
        """
        self.conn.execute(
            text("INSERT INTO schema_migrations (version) VALUES (:version)"),
            {"version": version},
        )
        self.conn.commit()

    def remove_migration_record(self, version: str) -> None:
        """
        Remove a migration record (for rollback).

        Args:
            version: Migration version string
        """
        self.conn.execute(
            text("DELETE FROM schema_migrations WHERE version = :version"),
            {"version": version},
        )
        self.conn.commit()

    def apply_migration(self, migration: BaseMigration) -> None:
        """
        Apply a single migration.

        Args:
            migration: Migration to apply
        """
        applied = self.get_applied_migrations()
        if migration.version in applied:
            print(f"Migration {migration.version} already applied, skipping")
            return

        print(f"Applying migration {migration.version}: {migration.description}")
        migration.upgrade(self.conn)
        self.record_migration(migration.version)
        print(f"Migration {migration.version} applied successfully")

    def rollback_migration(self, migration: BaseMigration) -> None:
        """
        Rollback a single migration.

        Args:
            migration: Migration to rollback
        """
        applied = self.get_applied_migrations()
        if migration.version not in applied:
            print(f"Migration {migration.version} not applied, cannot rollback")
            return

        print(f"Rolling back migration {migration.version}: {migration.description}")
        migration.downgrade(self.conn)
        self.remove_migration_record(migration.version)
        print(f"Migration {migration.version} rolled back successfully")

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def run_migrations(rollback: bool = False, target_version: Optional[str] = None) -> None:
    """
    Run pending migrations.

    Args:
        rollback: If True, rollback migrations instead of applying
        target_version: Specific version to migrate to/from
    """
    # Import migrations here to avoid circular imports
    from database.migrations import versions

    runner = MigrationRunner()

    try:
        # Get all migrations, sorted by version
        migrations = []
        for attr_name in dir(versions):
            attr = getattr(versions, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseMigration)
                and attr is not BaseMigration
            ):
                migrations.append(attr())

        migrations.sort(key=lambda m: m.version)

        if rollback:
            # Rollback in reverse order
            for migration in reversed(migrations):
                if target_version is None or migration.version > target_version:
                    runner.rollback_migration(migration)
                else:
                    break
        else:
            # Apply in order
            for migration in migrations:
                if target_version is None or migration.version <= target_version:
                    runner.apply_migration(migration)
                else:
                    break

    finally:
        runner.close()


def create_migration(name: str) -> str:
    """
    Create a new migration file.

    Args:
        name: Name/description for the migration

    Returns:
        Path to the created migration file
    """
    from datetime import datetime

    # Generate version from timestamp
    version = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # Create migration file content
    content = f'''"""
Migration: {name}

Version: {version}
"""

from sqlalchemy import Connection
from database.migrations.base import BaseMigration


class Migration(BaseMigration):
    """Migration: {name}."""

    version = "{version}"
    description = "{name}"

    def upgrade(self, conn: Connection) -> None:
        """Apply the migration."""
        # Add your migration SQL here
        pass

    def downgrade(self, conn: Connection) -> None:
        """Rollback the migration."""
        # Add your rollback SQL here
        pass
'''

    # Write migration file
    migrations_dir = os.path.dirname(__file__)
    versions_dir = os.path.join(migrations_dir, "versions")
    os.makedirs(versions_dir, exist_ok=True)

    filename = f"m_{version}_{name.lower().replace(' ', '_').replace('-', '_')}.py"
    filepath = os.path.join(versions_dir, filename)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Created migration: {filepath}")
    return filepath
