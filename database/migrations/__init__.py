"""
Migration system for Crypto Quant Laboratory.

Simple migration system for schema versioning and evolution.
Designed to work with both SQLite (development) and TimescaleDB/PostgreSQL (production).
"""

from database.migrations.runner import MigrationRunner, run_migrations, create_migration
from database.migrations.base import BaseMigration

__all__ = [
    "MigrationRunner",
    "run_migrations",
    "create_migration",
    "BaseMigration",
]
