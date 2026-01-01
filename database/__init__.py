"""
Database package for Crypto Quant Laboratory.

Provides SQLAlchemy ORM models, repository pattern, and migration system.
Designed to support both SQLite (development) and TimescaleDB/PostgreSQL (production).
"""

from database.connection import DatabaseConnection, get_db_session, init_db
from database.base import BaseRepository

__all__ = [
    "DatabaseConnection",
    "get_db_session",
    "init_db",
    "BaseRepository",
]
