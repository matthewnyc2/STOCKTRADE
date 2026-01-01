"""
Base migration class.

All migrations inherit from BaseMigration and implement upgrade() and downgrade().
"""

from abc import ABC, abstractmethod

from sqlalchemy import Connection


class BaseMigration(ABC):
    """
    Base class for database migrations.

    All migrations must inherit from this class and implement
    the upgrade and downgrade methods.
    """

    # Migration version in format: YYYYMMDDHHMMSS (e.g., 20241231120000)
    version: str

    # Human-readable description of the migration
    description: str

    @abstractmethod
    def upgrade(self, conn: Connection) -> None:
        """
        Apply the migration.

        Args:
            conn: SQLAlchemy connection
        """
        pass

    @abstractmethod
    def downgrade(self, conn: Connection) -> None:
        """
        Rollback the migration.

        Args:
            conn: SQLAlchemy connection
        """
        pass
