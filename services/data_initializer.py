"""
Data Initialization Service.

Handles the initialization of reference data on first run including:
- Default exchanges (Binance, CoinGecko, etc.)
- Common crypto coins (BTC, ETH, SOL, etc.)
- Strategy templates
- All reference data required for the system to function
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db_context
from core.database import engine

logger = logging.getLogger(__name__)


# Default exchanges to initialize
DEFAULT_EXCHANGES = [
    {
        "id": "binance",
        "name": "Binance",
        "type": "cex",
        "enabled": True,
        "api_base": "https://api.binance.com",
        "ws_base": "wss://stream.binance.com:9443/ws",
        "supports_spot": True,
        "supports_futures": True,
        "rate_limit": 1200,
    },
    {
        "id": "coingecko",
        "name": "CoinGecko",
        "type": "aggregator",
        "enabled": True,
        "api_base": "https://api.coingecko.com/api/v3",
        "ws_base": None,
        "supports_spot": True,
        "supports_futures": False,
        "rate_limit": 50,
    },
    {
        "id": "kraken",
        "name": "Kraken",
        "type": "cex",
        "enabled": False,
        "api_base": "https://api.kraken.com",
        "ws_base": "wss://ws.kraken.com",
        "supports_spot": True,
        "supports_futures": True,
        "rate_limit": 600,
    },
]

# Default coins to initialize
DEFAULT_COINS = [
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin", "enabled": True},
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum", "enabled": True},
    {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana", "enabled": True},
    {"symbol": "BNB", "name": "Binance Coin", "coingecko_id": "binancecoin", "enabled": True},
    {"symbol": "XRP", "name": "XRP", "coingecko_id": "ripple", "enabled": True},
    {"symbol": "ADA", "name": "Cardano", "coingecko_id": "cardano", "enabled": True},
    {"symbol": "DOGE", "name": "Dogecoin", "coingecko_id": "dogecoin", "enabled": True},
    {"symbol": "MATIC", "name": "Polygon", "coingecko_id": "matic-network", "enabled": True},
    {"symbol": "DOT", "name": "Polkadot", "coingecko_id": "polkadot", "enabled": True},
    {"symbol": "AVAX", "name": "Avalanche", "coingecko_id": "avalanche-2", "enabled": True},
    {"symbol": "LINK", "name": "Chainlink", "coingecko_id": "chainlink", "enabled": True},
    {"symbol": "UNI", "name": "Uniswap", "coingecko_id": "uniswap", "enabled": True},
    {"symbol": "ATOM", "name": "Cosmos", "coingecko_id": "cosmos", "enabled": True},
    {"symbol": "LTC", "name": "Litecoin", "coingecko_id": "litecoin", "enabled": True},
    {"symbol": "BCH", "name": "Bitcoin Cash", "coingecko_id": "bitcoin-cash", "enabled": True},
]

# Default trading pairs
DEFAULT_TRADING_PAIRS = [
    {"base_symbol": "BTC", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
    {"base_symbol": "ETH", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
    {"base_symbol": "SOL", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
    {"base_symbol": "BNB", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
    {"base_symbol": "XRP", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
    {"base_symbol": "ADA", "quote_symbol": "USDT", "exchange_id": "binance", "enabled": True},
]

# Default strategy templates
DEFAULT_STRATEGY_TEMPLATES = [
    {
        "id": "template_sma_crossover",
        "name": "SMA Crossover",
        "description": "Simple moving average crossover strategy",
        "template": {
            "indicators": {
                "fast_sma": {"period": 10},
                "slow_sma": {"period": 20},
            },
            "entry_rules": [
                {"condition": "crossover", "indicator": "fast_sma", "over": "slow_sma"}
            ],
            "exit_rules": [
                {"condition": "crossunder", "indicator": "fast_sma", "under": "slow_sma"}
            ],
        },
    },
    {
        "id": "template_rsi_reversal",
        "name": "RSI Reversal",
        "description": "RSI-based mean reversion strategy",
        "template": {
            "indicators": {
                "rsi": {"period": 14},
            },
            "entry_rules": [
                {"condition": "less_than", "indicator": "rsi", "value": 30}
            ],
            "exit_rules": [
                {"condition": "greater_than", "indicator": "rsi", "value": 70}
            ],
        },
    },
    {
        "id": "template_macd_momentum",
        "name": "MACD Momentum",
        "description": "MACD-based momentum following strategy",
        "template": {
            "indicators": {
                "macd": {"fast": 12, "slow": 26, "signal": 9},
            },
            "entry_rules": [
                {"condition": "crossover", "indicator": "macd", "over": "signal"}
            ],
            "exit_rules": [
                {"condition": "crossunder", "indicator": "macd", "under": "signal"}
            ],
        },
    },
]


def is_initialized() -> bool:
    """
    Check if the system has been initialized.

    Returns:
        True if reference data exists, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Check if exchanges table exists and has data
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='exchanges'"
            ))
            if not result.fetchone():
                return False

            # Check if we have exchanges
            result = conn.execute(text("SELECT COUNT(*) FROM exchanges"))
            exchange_count = result.fetchone()[0]

            return exchange_count > 0
    except Exception as e:
        logger.error(f"Error checking initialization status: {e}")
        return False


def initialize_exchanges() -> Dict[str, int]:
    """
    Initialize default exchanges in the database.

    Creates the exchanges table if it doesn't exist and inserts
    the default exchanges. Skips exchanges that already exist.

    Returns:
        Dictionary with counts: {"created": int, "skipped": int}
    """
    result = {"created": 0, "skipped": 0}

    try:
        # Create exchanges table if not exists
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS exchanges (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    api_base TEXT,
                    ws_base TEXT,
                    supports_spot BOOLEAN DEFAULT 0,
                    supports_futures BOOLEAN DEFAULT 0,
                    rate_limit INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        # Insert exchanges
        with get_db_context() as session:
            for exchange in DEFAULT_EXCHANGES:
                # Check if exists
                existing = session.execute(
                    text("SELECT id FROM exchanges WHERE id = :id"),
                    {"id": exchange["id"]}
                ).fetchone()

                if existing:
                    result["skipped"] += 1
                    continue

                # Insert new exchange
                session.execute(
                    text("""
                        INSERT INTO exchanges (
                            id, name, type, enabled, api_base, ws_base,
                            supports_spot, supports_futures, rate_limit
                        ) VALUES (
                            :id, :name, :type, :enabled, :api_base, :ws_base,
                            :supports_spot, :supports_futures, :rate_limit
                        )
                    """),
                    {
                        "id": exchange["id"],
                        "name": exchange["name"],
                        "type": exchange["type"],
                        "enabled": 1 if exchange["enabled"] else 0,
                        "api_base": exchange["api_base"],
                        "ws_base": exchange["ws_base"],
                        "supports_spot": 1 if exchange["supports_spot"] else 0,
                        "supports_futures": 1 if exchange["supports_futures"] else 0,
                        "rate_limit": exchange["rate_limit"],
                    }
                )
                result["created"] += 1

            session.commit()
            logger.info(f"Initialized exchanges: {result['created']} created, {result['skipped']} skipped")

    except Exception as e:
        logger.error(f"Error initializing exchanges: {e}")
        raise

    return result


def initialize_coins() -> Dict[str, int]:
    """
    Initialize default coins in the database.

    Creates the coins table if it doesn't exist and inserts
    the default cryptocurrencies. Skips coins that already exist.

    Returns:
        Dictionary with counts: {"created": int, "skipped": int}
    """
    result = {"created": 0, "skipped": 0}

    try:
        # Create coins table if not exists
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coins (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    coingecko_id TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        # Insert coins
        with get_db_context() as session:
            for coin in DEFAULT_COINS:
                # Check if exists
                existing = session.execute(
                    text("SELECT symbol FROM coins WHERE symbol = :symbol"),
                    {"symbol": coin["symbol"]}
                ).fetchone()

                if existing:
                    result["skipped"] += 1
                    continue

                # Insert new coin
                session.execute(
                    text("""
                        INSERT INTO coins (symbol, name, coingecko_id, enabled)
                        VALUES (:symbol, :name, :coingecko_id, :enabled)
                    """),
                    {
                        "symbol": coin["symbol"],
                        "name": coin["name"],
                        "coingecko_id": coin["coingecko_id"],
                        "enabled": 1 if coin["enabled"] else 0,
                    }
                )
                result["created"] += 1

            session.commit()
            logger.info(f"Initialized coins: {result['created']} created, {result['skipped']} skipped")

    except Exception as e:
        logger.error(f"Error initializing coins: {e}")
        raise

    return result


def initialize_trading_pairs() -> Dict[str, int]:
    """
    Initialize default trading pairs in the database.

    Creates the trading_pairs table if it doesn't exist and inserts
    the default trading pairs. Skips pairs that already exist.

    Returns:
        Dictionary with counts: {"created": int, "skipped": int}
    """
    result = {"created": 0, "skipped": 0}

    try:
        # Create trading_pairs table if not exists (without foreign key constraint for simplicity)
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trading_pairs (
                    id TEXT PRIMARY KEY,
                    base_symbol TEXT NOT NULL,
                    quote_symbol TEXT NOT NULL,
                    exchange_id TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(base_symbol, quote_symbol, exchange_id)
                )
            """))
            conn.commit()

        # Insert trading pairs
        with get_db_context() as session:
            for pair in DEFAULT_TRADING_PAIRS:
                # Create unique ID
                pair_id = f"{pair['exchange_id']}_{pair['base_symbol']}_{pair['quote_symbol']}"

                # Check if exists
                existing = session.execute(
                    text("SELECT id FROM trading_pairs WHERE id = :id"),
                    {"id": pair_id}
                ).fetchone()

                if existing:
                    result["skipped"] += 1
                    continue

                # Insert new trading pair
                session.execute(
                    text("""
                        INSERT INTO trading_pairs (id, base_symbol, quote_symbol, exchange_id, enabled)
                        VALUES (:id, :base_symbol, :quote_symbol, :exchange_id, :enabled)
                    """),
                    {
                        "id": pair_id,
                        "base_symbol": pair["base_symbol"],
                        "quote_symbol": pair["quote_symbol"],
                        "exchange_id": pair["exchange_id"],
                        "enabled": 1 if pair["enabled"] else 0,
                    }
                )
                result["created"] += 1

            session.commit()
            logger.info(f"Initialized trading pairs: {result['created']} created, {result['skipped']} skipped")

    except Exception as e:
        logger.error(f"Error initializing trading pairs: {result}")
        raise

    return result


def initialize_templates() -> Dict[str, int]:
    """
    Initialize default strategy templates in the database.

    Creates the strategy_templates table if it doesn't exist and inserts
    the default strategy templates. Skips templates that already exist.

    Returns:
        Dictionary with counts: {"created": int, "skipped": int}
    """
    result = {"created": 0, "skipped": 0}

    try:
        # Create strategy_templates table if not exists
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS strategy_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    template TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        # Insert templates
        import json
        with get_db_context() as session:
            for template in DEFAULT_STRATEGY_TEMPLATES:
                # Check if exists
                existing = session.execute(
                    text("SELECT id FROM strategy_templates WHERE id = :id"),
                    {"id": template["id"]}
                ).fetchone()

                if existing:
                    result["skipped"] += 1
                    continue

                # Insert new template
                session.execute(
                    text("""
                        INSERT INTO strategy_templates (id, name, description, template)
                        VALUES (:id, :name, :description, :template)
                    """),
                    {
                        "id": template["id"],
                        "name": template["name"],
                        "description": template["description"],
                        "template": json.dumps(template["template"]),
                    }
                )
                result["created"] += 1

            session.commit()
            logger.info(f"Initialized strategy templates: {result['created']} created, {result['skipped']} skipped")

    except Exception as e:
        logger.error(f"Error initializing strategy templates: {e}")
        raise

    return result


def initialize_system_metadata() -> Dict[str, str]:
    """
    Initialize system metadata table.

    Creates the system_metadata table for tracking initialization status,
    sync timestamps, and other system-level configuration.

    Returns:
        Dictionary with initialization status
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        # Set initialization timestamp
        with get_db_context() as session:
            session.execute(
                text("""
                    INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
                    VALUES (:key, :value, CURRENT_TIMESTAMP)
                """),
                {"key": "initialized_at", "value": datetime.utcnow().isoformat()}
            )
            session.commit()

        logger.info("Initialized system metadata")

    except Exception as e:
        logger.error(f"Error initializing system metadata: {e}")
        raise

    return {"status": "success", "initialized_at": datetime.utcnow().isoformat()}


def initialize_reference_data() -> Dict[str, any]:
    """
    Initialize all reference data on first run.

    This is the main entry point for data initialization. It runs all
    initialization functions in the correct order and returns a summary
    of what was done.

    Returns:
        Dictionary with initialization results
    """
    logger.info("Starting reference data initialization...")

    results = {
        "success": False,
        "timestamp": datetime.utcnow().isoformat(),
        "exchanges": {},
        "coins": {},
        "trading_pairs": {},
        "templates": {},
        "metadata": {},
    }

    try:
        # Initialize in order
        results["exchanges"] = initialize_exchanges()
        results["coins"] = initialize_coins()
        results["trading_pairs"] = initialize_trading_pairs()
        results["templates"] = initialize_templates()
        results["metadata"] = initialize_system_metadata()

        results["success"] = True
        logger.info("Reference data initialization completed successfully")

    except Exception as e:
        logger.error(f"Reference data initialization failed: {e}")
        results["error"] = str(e)

    return results


def get_initialization_status() -> Dict[str, any]:
    """
    Get the current initialization status of the system.

    Returns:
        Dictionary with status information about all data
    """
    status = {
        "initialized": False,
        "initialized_at": None,
        "data_counts": {},
    }

    try:
        with engine.connect() as conn:
            # Check if tables exist - use parameterized queries for table names
            # Note: SQLite doesn't support parameterized table names, so we validate input
            tables = {}
            valid_tables = ["exchanges", "coins", "trading_pairs", "strategy_templates"]

            for table in valid_tables:
                # Validate table name is alphanumeric and underscore only
                if not table.replace("_", "").isalnum():
                    raise ValueError(f"Invalid table name: {table}")

                # Use validated table name in query (safe because we validated above)
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:table_name"),
                    {"table_name": table}
                )
                tables[table] = result.fetchone()[0] > 0

            # Get data counts - validate table names before use
            for table in valid_tables:
                if tables.get(table, False):
                    # Use validated table name (safe because we validated above)
                    # Quote table name to prevent SQL injection
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    status["data_counts"][table] = result.fetchone()[0]
                else:
                    status["data_counts"][table] = 0

            # Check initialization metadata
            if tables.get("system_metadata", False):
                result = conn.execute(
                    text("SELECT value FROM system_metadata WHERE key = 'initialized_at'")
                )
                row = result.fetchone()
                if row:
                    status["initialized_at"] = row[0]
                    status["initialized"] = True

    except Exception as e:
        logger.error(f"Error getting initialization status: {e}")
        status["error"] = str(e)

    return status
