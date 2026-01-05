"""
Initial schema migration.

Creates all tables for the Crypto Quant Laboratory.
"""

from sqlalchemy import Connection, text

from database.migrations.base import BaseMigration


class Migration(BaseMigration):
    """Initial schema migration creating all tables."""

    version = "20241231120000"
    description = "Initial schema - create all tables"

    def upgrade(self, conn: Connection) -> None:
        """Apply the migration - create all tables."""

        # Strategies table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS strategies (
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

        # Strategy layers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS strategy_layers (
                id VARCHAR(50) PRIMARY KEY,
                strategy_id VARCHAR(50) NOT NULL,
                layer_order INTEGER DEFAULT 0,
                weight REAL DEFAULT 1.0,
                config JSON DEFAULT '{}',
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_strategy_layers_strategy_id ON strategy_layers(strategy_id)"))

        # Signals table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS signals (
                id VARCHAR(50) PRIMARY KEY,
                strategy_id VARCHAR(50) NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                confidence REAL NOT NULL,
                price NUMERIC(20, 8) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reasoning TEXT,
                layer_breakdown JSON DEFAULT '[]',
                meta JSON DEFAULT '{}'
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_signals_strategy_id ON signals(strategy_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)"))

        # Layer signals table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS layer_signals (
                id VARCHAR(50) PRIMARY KEY,
                layer_id VARCHAR(50) NOT NULL,
                signal_type VARCHAR(50) NOT NULL,
                confidence REAL NOT NULL,
                weight REAL DEFAULT 1.0,
                reasoning TEXT,
                meta JSON DEFAULT '{}'
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_layer_signals_layer_id ON layer_signals(layer_id)"))

        # Backtest results table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id VARCHAR(50) PRIMARY KEY,
                strategy_id VARCHAR(50) NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                initial_capital NUMERIC(20, 8) NOT NULL,
                final_capital NUMERIC(20, 8) NOT NULL,
                total_return NUMERIC(10, 4) NOT NULL,
                sharpe_ratio NUMERIC(10, 4),
                sortino_ratio NUMERIC(10, 4),
                max_drawdown NUMERIC(10, 4) NOT NULL,
                win_rate NUMERIC(5, 4) NOT NULL,
                profit_factor NUMERIC(10, 4),
                total_trades INTEGER NOT NULL
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_id ON backtest_results(strategy_id)"))

        # Equity points table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS equity_points (
                id VARCHAR(50) PRIMARY KEY,
                backtest_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                equity NUMERIC(20, 8) NOT NULL,
                drawdown NUMERIC(10, 4) NOT NULL,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_equity_points_backtest_id ON equity_points(backtest_id)"))

        # Trades table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id VARCHAR(50) PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                entry_date TIMESTAMP NOT NULL,
                exit_date TIMESTAMP NOT NULL,
                entry_price NUMERIC(20, 8) NOT NULL,
                exit_price NUMERIC(20, 8) NOT NULL,
                quantity NUMERIC(20, 8) NOT NULL,
                side VARCHAR(10) NOT NULL,
                pnl NUMERIC(20, 8) NOT NULL,
                pnl_percent NUMERIC(10, 4) NOT NULL,
                exit_reason VARCHAR(100),
                backtest_id VARCHAR(50) NOT NULL,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_backtest_id ON trades(backtest_id)"))

        # Portfolios table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id VARCHAR(50) PRIMARY KEY DEFAULT 'current',
                total_equity NUMERIC(20, 8) NOT NULL,
                starting_balance NUMERIC(20, 8) NOT NULL,
                total_pnl NUMERIC(20, 8) DEFAULT 0,
                total_pnl_percent NUMERIC(10, 4) DEFAULT 0,
                open_pnl NUMERIC(20, 8) DEFAULT 0,
                sharpe_ratio NUMERIC(10, 4),
                sortino_ratio NUMERIC(10, 4),
                max_drawdown NUMERIC(10, 4) DEFAULT 0,
                win_rate NUMERIC(5, 4) NOT NULL,
                profit_factor NUMERIC(10, 4),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Positions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS positions (
                id VARCHAR(50) PRIMARY KEY,
                portfolio_id VARCHAR(50) DEFAULT 'current',
                symbol VARCHAR(50) NOT NULL,
                side VARCHAR(10) NOT NULL,
                quantity NUMERIC(20, 8) NOT NULL,
                entry_price NUMERIC(20, 8) NOT NULL,
                current_price NUMERIC(20, 8) NOT NULL,
                unrealized_pnl NUMERIC(20, 8) NOT NULL,
                unrealized_pnl_percent NUMERIC(10, 4) NOT NULL,
                stop_loss NUMERIC(20, 8),
                take_profit NUMERIC(20, 8),
                entry_timestamp TIMESTAMP NOT NULL,
                meta JSON DEFAULT '{}',
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id)"))

        # Whales table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS whales (
                address VARCHAR(100) PRIMARY KEY,
                label VARCHAR(200),
                tier VARCHAR(50) NOT NULL,
                holdings_usd NUMERIC(20, 2) NOT NULL,
                holdings_24h_change NUMERIC(10, 4) NOT NULL,
                historical_accuracy NUMERIC(5, 4),
                pattern_type VARCHAR(50) NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferred_tokens JSON DEFAULT '[]',
                meta JSON DEFAULT '{}'
            )
        """))

        # Whale activities table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS whale_activities (
                id VARCHAR(50) PRIMARY KEY,
                whale_address VARCHAR(100) NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                amount_usd NUMERIC(20, 2) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_hash VARCHAR(200),
                meta JSON DEFAULT '{}'
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_whale_activities_whale_address ON whale_activities(whale_address)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_whale_activities_timestamp ON whale_activities(timestamp)"))

        # Whale constellations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS whale_constellations (
                id VARCHAR(50) PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                whale_addresses JSON NOT NULL,
                confidence NUMERIC(5, 4) NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                meta JSON DEFAULT '{}'
            )
        """))

        # ML models table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ml_models (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                features JSON DEFAULT '[]',
                training_start TIMESTAMP,
                training_end TIMESTAMP,
                accuracy NUMERIC(5, 4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) NOT NULL,
                parameters JSON DEFAULT '{}',
                metrics JSON DEFAULT '{}'
            )
        """))

        # Settings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS settings (
                id VARCHAR(50) PRIMARY KEY DEFAULT 'default',
                ui_mode VARCHAR(50) DEFAULT 'pro',
                risk_parameters JSON DEFAULT '{"max_position_size": 0.1, "max_daily_loss": 0.05, "stop_loss_enabled": true, "max_open_positions": 10}',
                notifications JSON DEFAULT '{"email_enabled": false, "slack_enabled": false, "alert_types": []}',
                timezone VARCHAR(50) DEFAULT 'UTC',
                currency VARCHAR(10) DEFAULT 'USD',
                meta JSON DEFAULT '{}'
            )
        """))

        # AI reasoning sessions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_reasoning_sessions (
                id VARCHAR(50) PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                reasoning_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                meta JSON DEFAULT '{}'
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_reasoning_sessions_session_id ON ai_reasoning_sessions(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_reasoning_sessions_created_at ON ai_reasoning_sessions(created_at)"))

        conn.commit()

    def downgrade(self, conn: Connection) -> None:
        """Rollback the migration - drop all tables."""

        # Drop tables in reverse order of creation (to handle foreign keys)
        tables = [
            "ai_reasoning_sessions",
            "settings",
            "ml_models",
            "whale_constellations",
            "whale_activities",
            "whales",
            "positions",
            "portfolios",
            "trades",
            "equity_points",
            "backtest_results",
            "layer_signals",
            "signals",
            "strategy_layers",
            "strategies",
        ]

        for table in tables:
            # Validate table name before using in SQL (prevent SQL injection)
            if not table.replace("_", "").isalnum():
                raise ValueError(f"Invalid table name: {table}")
            # Use validated table names (safe because we validated)
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
            conn.execute(text(f'DROP INDEX IF EXISTS "idx_{table}"'))

        conn.commit()
