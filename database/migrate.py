#!/usr/bin/env python3
"""
Database migration script for Crypto Quant Laboratory.

This script handles database schema migrations and updates for production deployments.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import init_db, get_db_context
from sqlalchemy import text
from database.base import BaseModel as Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Database migration manager."""

    def __init__(self):
        self.migrations_table = "schema_migrations"
        self.migrations = [
            {
                "version": "001_initial",
                "description": "Initial database schema creation",
                "apply": self._apply_initial_schema
            },
            {
                "version": "002_add_indexes",
                "description": "Add performance indexes",
                "apply": self._add_indexes
            },
            {
                "version": "003_add_hypertables",
                "description": "Convert time-series tables to hypertables",
                "apply": self._add_hypertables
            },
            {
                "version": "004_optimize_schema",
                "description": "Schema optimizations for production",
                "apply": self._optimize_schema
            }
        ]

    def create_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        logger.info("Creating migrations table...")

        # Validate migrations table name (prevent SQL injection)
        if not self.migrations_table.replace("_", "").isalnum():
            raise ValueError(f"Invalid migrations table name: {self.migrations_table}")

        with get_db_context() as session:
            # Check if table exists - use parameterized query
            result = session.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
                """),
                {"table_name": self.migrations_table}
            ).scalar()

            if not result:
                # Create migrations table - use validated table name (safe because we validated)
                # We need to use string formatting for table names but validated above
                session.execute(text(f"""
                    CREATE TABLE \"{self.migrations_table}\" (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))

                session.commit()
                logger.info("Migrations table created")
            else:
                logger.info("Migrations table already exists")

    def get_applied_migrations(self):
        """Get list of already applied migrations."""
        # Validate migrations table name (prevent SQL injection)
        if not self.migrations_table.replace("_", "").isalnum():
            raise ValueError(f"Invalid migrations table name: {self.migrations_table}")

        with get_db_context() as session:
            result = session.execute(
                text(f'SELECT version FROM "{self.migrations_table}" ORDER BY applied_at')
            ).fetchall()

            return [row[0] for row in result]

    def apply_migration(self, migration):
        """Apply a single migration."""
        logger.info(f"Applying migration {migration['version']}: {migration['description']}")

        # Validate migrations table name (prevent SQL injection)
        if not self.migrations_table.replace("_", "").isalnum():
            raise ValueError(f"Invalid migrations table name: {self.migrations_table}")

        try:
            # Apply migration
            migration['apply']()

            # Record migration - use validated table name (safe because we validated)
            with get_db_context() as session:
                session.execute(text(f"""
                    INSERT INTO \"{self.migrations_table}\" (version, description)
                    VALUES (:version, :description)
                """), {
                    'version': migration['version'],
                    'description': migration['description']
                })

            logger.info(f"Migration {migration['version']} applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply migration {migration['version']}: {str(e)}")
            raise

    def _apply_initial_schema(self):
        """Apply initial database schema using SQLAlchemy models."""
        logger.info("Applying initial schema...")

        # Initialize database (this will create all tables)
        init_db()

        # Create additional indexes and constraints
        with get_db_context() as session:
            # Add foreign key constraints that might be missing
            session.execute(text("""
                ALTER TABLE IF EXISTS signals
                ADD CONSTRAINT fk_signals_strategy
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            """))

            session.execute(text("""
                ALTER TABLE IF EXISTS backtests
                ADD CONSTRAINT fk_backtests_strategy
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            """))

            session.execute(text("""
                ALTER TABLE IF EXISTS portfolio
                ADD CONSTRAINT fk_portfolio_strategy
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE SET NULL
            """))

            session.commit()

    def _add_indexes(self):
        """Add performance indexes for common query patterns."""
        logger.info("Adding performance indexes...")

        with get_db_context() as session:
            # Index on signals table
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp
                ON signals(timestamp)
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_signals_symbol
                ON signals(symbol)
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_signals_type
                ON signals(type)
            """))

            # Index on strategies table
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_strategies_name
                ON strategies(name)
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_strategies_status
                ON strategies(status)
            """))

            # Index on market_data table (if it exists)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
                ON market_data(symbol, timestamp)
            """))

            session.commit()

    def _add_hypertables(self):
        """Convert time-series tables to TimescaleDB hypertables."""
        logger.info("Setting up TimescaleDB hypertables...")

        with get_db_context() as session:
            # Create extension if not exists
            session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))

            # Convert signals table to hypertable
            session.execute(text("""
                SELECT create_hypertable('signals', 'timestamp',
                    if_not_exists => true,
                    migrate_data => true
                )
            """))

            # Convert market_data table to hypertable
            session.execute(text("""
                SELECT create_hypertable('market_data', 'timestamp',
                    if_not_exists => true,
                    migrate_data => true
                )
            """))

            session.commit()

    def _optimize_schema(self):
        """Apply production schema optimizations."""
        logger.info("Applying schema optimizations...")

        with get_db_context() as session:
            # Add compression to time-series data
            session.execute(text("""
                ALTER TABLE signals SET (timescaledb.compress);
                SELECT add_compression_policy('signals', 'interval 7');
            """))

            # Add retention policies
            session.execute(text("""
                SELECT add_retention_policy('signals', INTERVAL '90 days', true);
                SELECT add_retention_policy('market_data', INTERVAL '30 days', true);
            """))

            # Create materialized views for common aggregations
            session.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS signals_daily_stats AS
                SELECT
                    DATE_TRUNC('day', timestamp) AS day,
                    symbol,
                    type,
                    COUNT(*) as signal_count,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price
                FROM signals
                GROUP BY DATE_TRUNC('day', timestamp), symbol, type;
            """))

            # Create refresh index
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_signals_daily_stats
                ON signals_daily_stats(day, symbol)
            """))

            session.commit()

    def run_migrations(self):
        """Run all pending migrations."""
        # Initialize database if needed
        init_db(drop_all=False)

        # Create migrations table
        self.create_migrations_table()

        # Get applied migrations
        applied_migrations = self.get_applied_migrations()
        logger.info(f"Applied migrations: {applied_migrations}")

        # Find and run pending migrations
        for migration in self.migrations:
            if migration['version'] not in applied_migrations:
                try:
                    self.apply_migration(migration)
                except Exception as e:
                    logger.error(f"Migration failed: {str(e)}")
                    raise
            else:
                logger.info(f"Migration {migration['version']} already applied")

    def rollback_migration(self, version):
        """Rollback to a specific migration version."""
        logger.warning(f"Rollback to version {version} is not implemented yet")
        # This would need to be implemented based on your rollback requirements
        raise NotImplementedError("Rollback functionality not implemented")

def main():
    """Main migration entry point."""
    try:
        # Initialize database connection
        init_db()

        # Create migrator and run migrations
        migrator = DatabaseMigrator()
        migrator.run_migrations()

        logger.info("All migrations completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()