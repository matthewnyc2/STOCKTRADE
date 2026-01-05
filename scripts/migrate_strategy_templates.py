"""
Migration script to add template-related columns to strategies table.

Run this script to update the database schema for strategy templates support.

Usage:
    python -m scripts.migrate_strategy_templates
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from database.connection import get_db_connection


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_database():
    """
    Add template-related columns to the strategies table.

    This migration adds:
    - is_template (boolean, indexed)
    - game_mode_* columns for Game Mode metadata
    - pro_mode_* columns for Pro Mode metadata
    - backtest_* columns for template backtest metrics
    """
    statements = [
        # Add is_template column if not exists
        """ALTER TABLE strategies ADD COLUMN is_template BOOLEAN DEFAULT 0 NOT NULL""",
        # Create index on is_template
        """CREATE INDEX IF NOT EXISTS idx_strategies_is_template ON strategies(is_template)""",

        # Template relations and enhanced fields
        """ALTER TABLE strategies ADD COLUMN template_id VARCHAR(50)""",
        """ALTER TABLE strategies ADD COLUMN parent_id VARCHAR(50)""",
        """ALTER TABLE strategies ADD COLUMN tags JSON DEFAULT '[]'""",
        """ALTER TABLE strategies ADD COLUMN risk_level VARCHAR(20)""",
        """ALTER TABLE strategies ADD COLUMN performance_summary JSON""",

        # Create indexes
        """CREATE INDEX IF NOT EXISTS idx_strategies_template_id ON strategies(template_id)""",
        """CREATE INDEX IF NOT EXISTS idx_strategies_parent_id ON strategies(parent_id)""",

        # Game Mode metadata columns
        """ALTER TABLE strategies ADD COLUMN game_mode_display_name VARCHAR(200)""",
        """ALTER TABLE strategies ADD COLUMN game_mode_stars INTEGER""",
        """ALTER TABLE strategies ADD COLUMN game_mode_flavor_text TEXT""",
        """ALTER TABLE strategies ADD COLUMN game_mode_emoji VARCHAR(50)""",

        # Pro Mode metadata columns
        """ALTER TABLE strategies ADD COLUMN pro_mode_technical_name VARCHAR(200)""",
        """ALTER TABLE strategies ADD COLUMN pro_mode_category VARCHAR(100)""",
        """ALTER TABLE strategies ADD COLUMN pro_mode_complexity VARCHAR(50)""",

        # Backtest metrics columns
        """ALTER TABLE strategies ADD COLUMN backtest_total_return FLOAT""",
        """ALTER TABLE strategies ADD COLUMN backtest_sharpe_ratio FLOAT""",
        """ALTER TABLE strategies ADD COLUMN backtest_max_drawdown FLOAT""",
        """ALTER TABLE strategies ADD COLUMN backtest_win_rate FLOAT""",
        """ALTER TABLE strategies ADD COLUMN backtest_profit_factor FLOAT""",
        """ALTER TABLE strategies ADD COLUMN backtest_total_trades INTEGER""",
    ]

    engine = get_db_connection().engine

    with engine.connect() as conn:
        for statement in statements:
            try:
                logger.info(f"Executing: {statement[:80]}...")
                conn.execute(text(statement))
                conn.commit()
                logger.info("  Success")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info(f"  Column already exists, skipping")
                else:
                    logger.error(f"  Error: {e}")
                    # Continue with other statements

    logger.info("Migration complete!")


def main():
    """Main entry point for the migration script."""
    try:
        migrate_database()
        return 0
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
