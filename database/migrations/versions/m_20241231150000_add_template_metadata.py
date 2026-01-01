"""
Add template metadata to strategies table.

Adds Game Mode metadata, Pro Mode metadata, and backtest metrics columns.
"""

from sqlalchemy import Connection, text

from database.migrations.base import BaseMigration


class Migration(BaseMigration):
    """Add template metadata columns to strategies table."""

    version = "20241231150000"
    description = "Add template metadata columns to strategies table"

    def upgrade(self, conn: Connection) -> None:
        """Apply the migration - add template metadata columns."""

        # Game Mode metadata columns
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN game_mode_display_name VARCHAR(200)
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN game_mode_stars INTEGER
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN game_mode_flavor_text TEXT
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN game_mode_emoji VARCHAR(50)
        """))

        # Pro Mode metadata columns
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN pro_mode_technical_name VARCHAR(200)
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN pro_mode_category VARCHAR(100)
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN pro_mode_complexity VARCHAR(50)
        """))

        # Backtest metrics columns
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_total_return REAL
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_sharpe_ratio REAL
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_max_drawdown REAL
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_win_rate REAL
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_profit_factor REAL
        """))
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN backtest_total_trades INTEGER
        """))

        # is_template flag
        conn.execute(text("""
            ALTER TABLE strategies
            ADD COLUMN is_template BOOLEAN DEFAULT FALSE
        """))

        conn.commit()

    def downgrade(self, conn: Connection) -> None:
        """Rollback the migration - remove template metadata columns."""

        # Drop columns (SQLite doesn't support DROP COLUMN directly,
        # but we'll recreate the table without these columns)
        conn.execute(text("""
            CREATE TABLE strategies_new (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                type VARCHAR(50) NOT NULL,
                parameters JSON DEFAULT '{}',
                layers JSON DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Copy data
        conn.execute(text("""
            INSERT INTO strategies_new (id, name, description, type, parameters, layers, status, created_at, updated_at)
            SELECT id, name, description, type, parameters, layers, status, created_at, updated_at
            FROM strategies
        """))

        # Drop old table and rename new one
        conn.execute(text("DROP TABLE strategies"))
        conn.execute(text("ALTER TABLE strategies_new RENAME TO strategies"))

        conn.commit()
