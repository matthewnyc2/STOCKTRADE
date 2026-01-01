"""
Migration: Add logic_gate field to strategies table

Version: 20241231160000
"""

from sqlalchemy import Connection, text
from database.migrations.base import BaseMigration


class Migration(BaseMigration):
    """Migration: Add logic_gate field to strategies table."""

    version = "20241231160000"
    description = "Add logic_gate field to strategies table"

    def upgrade(self, conn: Connection) -> None:
        """Apply the migration."""
        conn.execute(
            text("""
            ALTER TABLE strategies
            ADD COLUMN logic_gate VARCHAR(50) DEFAULT 'none'
            """)
        )

    def downgrade(self, conn: Connection) -> None:
        """Rollback the migration."""
        # SQLite doesn't support DROP COLUMN directly
        # Need to recreate table without the column
        conn.execute(text("""
            CREATE TABLE strategies_backup (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                type VARCHAR(50) NOT NULL,
                parameters JSON DEFAULT '{}',
                layers JSON DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'draft',
                game_mode_display_name VARCHAR(200),
                game_mode_stars INTEGER,
                game_mode_flavor_text TEXT,
                game_mode_emoji VARCHAR(50),
                pro_mode_technical_name VARCHAR(200),
                pro_mode_category VARCHAR(100),
                pro_mode_complexity VARCHAR(50),
                backtest_total_return FLOAT,
                backtest_sharpe_ratio FLOAT,
                backtest_max_drawdown FLOAT,
                backtest_win_rate FLOAT,
                backtest_profit_factor FLOAT,
                backtest_total_trades INTEGER,
                is_template BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        )
        conn.execute(text("""
            INSERT INTO strategies_backup (
                id, name, description, type, parameters, layers, status,
                game_mode_display_name, game_mode_stars, game_mode_flavor_text, game_mode_emoji,
                pro_mode_technical_name, pro_mode_category, pro_mode_complexity,
                backtest_total_return, backtest_sharpe_ratio, backtest_max_drawdown,
                backtest_win_rate, backtest_profit_factor, backtest_total_trades,
                is_template, created_at, updated_at
            )
            SELECT
                id, name, description, type, parameters, layers, status,
                game_mode_display_name, game_mode_stars, game_mode_flavor_text, game_mode_emoji,
                pro_mode_technical_name, pro_mode_category, pro_mode_complexity,
                backtest_total_return, backtest_sharpe_ratio, backtest_max_drawdown,
                backtest_win_rate, backtest_profit_factor, backtest_total_trades,
                is_template, created_at, updated_at
            FROM strategies
            """)
        )
        conn.execute(text("DROP TABLE strategies"))
        conn.execute(text("ALTER TABLE strategies_backup RENAME TO strategies"))
