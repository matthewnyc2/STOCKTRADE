"""
Migration to add prices table for storing OHLCV market data.

Stores historical price data for technical analysis and backtesting.
"""

from sqlalchemy import Connection, text

from database.migrations.base import BaseMigration


class Migration(BaseMigration):
    """Migration to create prices table."""

    version = "20241231170000"
    description = "Add prices table for OHLCV market data"

    def upgrade(self, conn: Connection) -> None:
        """Apply the migration - create prices table."""

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prices (
                id VARCHAR(50) PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open NUMERIC(20, 8) NOT NULL,
                high NUMERIC(20, 8) NOT NULL,
                low NUMERIC(20, 8) NOT NULL,
                close NUMERIC(20, 8) NOT NULL,
                volume NUMERIC(20, 8) NOT NULL,
                timeframe VARCHAR(10),
                source VARCHAR(50)
            )
        """))

        # Create indexes for efficient queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp
            ON prices(symbol, timestamp)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prices_timestamp
            ON prices(timestamp)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prices_symbol
            ON prices(symbol)
        """))

        conn.commit()

    def downgrade(self, conn: Connection) -> None:
        """Rollback the migration - drop prices table."""

        conn.execute(text("DROP INDEX IF EXISTS idx_prices_symbol_timestamp"))
        conn.execute(text("DROP INDEX IF NOT EXISTS idx_prices_timestamp"))
        conn.execute(text("DROP INDEX IF NOT EXISTS idx_prices_symbol"))
        conn.execute(text("DROP TABLE IF EXISTS prices"))

        conn.commit()
