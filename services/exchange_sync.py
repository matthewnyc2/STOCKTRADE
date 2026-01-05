"""
Exchange Synchronization Service.

Handles synchronization of data from external exchanges including:
- Trading pairs from Binance
- Coin listings from CoinGecko
- Extensible sync framework for additional exchanges
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx
from sqlalchemy import text

from core.database import engine
from database.connection import get_db_context

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Sync status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ExchangeSync:
    """
    Main exchange synchronization service.

    Provides methods to sync data from various exchanges and
    track sync status and history.
    """

    def __init__(self):
        """Initialize the exchange sync service."""
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY", "")
        self.coingecko_api_base = "https://api.coingecko.com/api/v3"
        self.binance_api_base = "https://api.binance.com"

    def _get_sync_lock(self, exchange_id: str) -> bool:
        """
        Attempt to acquire a sync lock for an exchange.

        Args:
            exchange_id: Exchange identifier

        Returns:
            True if lock acquired, False if sync already in progress
        """
        try:
            with engine.connect() as conn:
                # Create sync_locks table if not exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sync_locks (
                        exchange_id TEXT PRIMARY KEY,
                        locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        locked_by TEXT DEFAULT 'system'
                    )
                """))
                conn.commit()

                # Try to acquire lock
                now = datetime.utcnow()
                conn.execute(
                    text("""
                        INSERT INTO sync_locks (exchange_id, locked_at)
                        VALUES (:exchange_id, :locked_at)
                    """),
                    {"exchange_id": exchange_id, "locked_at": now}
                )
                conn.commit()
                return True

        except Exception:
            # Lock already exists
            return False

    def _release_sync_lock(self, exchange_id: str):
        """
        Release the sync lock for an exchange.

        Args:
            exchange_id: Exchange identifier
        """
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM sync_locks WHERE exchange_id = :exchange_id"),
                    {"exchange_id": exchange_id}
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error releasing sync lock for {exchange_id}: {e}")

    def _update_sync_status(
        self,
        exchange_id: str,
        status: SyncStatus,
        records_synced: int = 0,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ):
        """
        Update sync status for an exchange.

        Args:
            exchange_id: Exchange identifier
            status: Sync status
            records_synced: Number of records synchronized
            error_message: Error message if failed
            duration_seconds: Duration of sync operation
        """
        try:
            with engine.connect() as conn:
                # Create sync_status table if not exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sync_status (
                        exchange_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        last_sync_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        records_synced INTEGER DEFAULT 0,
                        error_message TEXT,
                        duration_seconds REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()

                # Update status
                conn.execute(
                    text("""
                        INSERT OR REPLACE INTO sync_status
                        (exchange_id, status, last_sync_at, records_synced, error_message, duration_seconds, updated_at)
                        VALUES (:exchange_id, :status, CURRENT_TIMESTAMP, :records_synced, :error_message, :duration_seconds, CURRENT_TIMESTAMP)
                    """),
                    {
                        "exchange_id": exchange_id,
                        "status": status.value,
                        "records_synced": records_synced,
                        "error_message": error_message,
                        "duration_seconds": duration_seconds,
                    }
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error updating sync status for {exchange_id}: {e}")

    async def sync_binance_pairs(self) -> Dict[str, Any]:
        """
        Sync trading pairs from Binance exchange.

        Fetches all trading pairs from Binance API and updates
        the trading_pairs table with new pairs.

        Returns:
            Dictionary with sync results
        """
        exchange_id = "binance"
        start_time = datetime.utcnow()

        logger.info(f"Starting Binance pairs sync...")

        # Check lock
        if not self._get_sync_lock(exchange_id):
            return {
                "exchange": exchange_id,
                "status": SyncStatus.PENDING.value,
                "message": "Sync already in progress"
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch exchange info from Binance
                response = await client.get(f"{self.binance_api_base}/api/v3/exchangeInfo")
                response.raise_for_status()

                data = response.json()
                symbols = data.get("symbols", [])

                # Filter for USDT pairs
                usdt_pairs = [
                    s for s in symbols
                    if s.get("status") == "TRADING"
                    and s.get("quoteAsset") == "USDT"
                    and s.get("symbol").endswith("USDT")
                ]

                synced_count = 0

                with get_db_context() as session:
                    for symbol_info in usdt_pairs:
                        base_symbol = symbol_info["baseAsset"]
                        quote_symbol = symbol_info["quoteAsset"]
                        pair_id = f"{exchange_id}_{base_symbol}_{quote_symbol}"

                        # Check if exists
                        existing = session.execute(
                            text("SELECT id FROM trading_pairs WHERE id = :id"),
                            {"id": pair_id}
                        ).fetchone()

                        if not existing:
                            # Insert new trading pair
                            session.execute(
                                text("""
                                    INSERT INTO trading_pairs (id, base_symbol, quote_symbol, exchange_id, enabled)
                                    VALUES (:id, :base_symbol, :quote_symbol, :exchange_id, :enabled)
                                """),
                                {
                                    "id": pair_id,
                                    "base_symbol": base_symbol,
                                    "quote_symbol": quote_symbol,
                                    "exchange_id": exchange_id,
                                    "enabled": 1,
                                }
                            )
                            synced_count += 1

                    session.commit()

                duration = (datetime.utcnow() - start_time).total_seconds()

                self._update_sync_status(
                    exchange_id,
                    SyncStatus.SUCCESS,
                    records_synced=synced_count,
                    duration_seconds=duration
                )

                logger.info(f"Binance sync completed: {synced_count} pairs synced")

                return {
                    "exchange": exchange_id,
                    "status": SyncStatus.SUCCESS.value,
                    "records_synced": synced_count,
                    "duration_seconds": duration,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error syncing Binance: {e}"
            logger.error(error_msg)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_sync_status(exchange_id, SyncStatus.FAILED, error_message=error_msg, duration_seconds=duration)

            return {
                "exchange": exchange_id,
                "status": SyncStatus.FAILED.value,
                "error": error_msg,
                "duration_seconds": duration,
            }

        except Exception as e:
            error_msg = f"Error syncing Binance: {e}"
            logger.error(error_msg)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_sync_status(exchange_id, SyncStatus.FAILED, error_message=error_msg, duration_seconds=duration)

            return {
                "exchange": exchange_id,
                "status": SyncStatus.FAILED.value,
                "error": error_msg,
                "duration_seconds": duration,
            }

        finally:
            self._release_sync_lock(exchange_id)

    async def sync_coingecko_listings(self, limit: int = 250) -> Dict[str, Any]:
        """
        Sync coin listings from CoinGecko.

        Fetches coin listings from CoinGecko API and updates
        the coins table with new cryptocurrencies.

        Args:
            limit: Maximum number of coins to fetch (default: 250, max: 1000 for free tier)

        Returns:
            Dictionary with sync results
        """
        exchange_id = "coingecko"
        start_time = datetime.utcnow()

        logger.info(f"Starting CoinGecko listings sync...")

        # Check lock
        if not self._get_sync_lock(exchange_id):
            return {
                "exchange": exchange_id,
                "status": SyncStatus.PENDING.value,
                "message": "Sync already in progress"
            }

        try:
            headers = {}
            if self.coingecko_api_key:
                headers["x-cg-demo-api-key"] = self.coingecko_api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch coin list from CoinGecko
                params = {"per_page": limit, "page": 1, "sparkline": False}

                response = await client.get(
                    f"{self.coingecko_api_base}/coins/markets",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()

                coins_data = response.json()

                synced_count = 0

                with get_db_context() as session:
                    for coin in coins_data:
                        symbol = coin.get("symbol", "").upper()
                        name = coin.get("name", "")
                        coin_id = coin.get("id", "")

                        if not symbol or not coin_id:
                            continue

                        # Check if exists
                        existing = session.execute(
                            text("SELECT symbol FROM coins WHERE symbol = :symbol"),
                            {"symbol": symbol}
                        ).fetchone()

                        if not existing:
                            # Insert new coin
                            session.execute(
                                text("""
                                    INSERT INTO coins (symbol, name, coingecko_id, enabled)
                                    VALUES (:symbol, :name, :coingecko_id, :enabled)
                                """),
                                {
                                    "symbol": symbol,
                                    "name": name,
                                    "coingecko_id": coin_id,
                                    "enabled": 1,
                                }
                            )
                            synced_count += 1

                    session.commit()

                duration = (datetime.utcnow() - start_time).total_seconds()

                self._update_sync_status(
                    exchange_id,
                    SyncStatus.SUCCESS,
                    records_synced=synced_count,
                    duration_seconds=duration
                )

                logger.info(f"CoinGecko sync completed: {synced_count} coins synced")

                return {
                    "exchange": exchange_id,
                    "status": SyncStatus.SUCCESS.value,
                    "records_synced": synced_count,
                    "duration_seconds": duration,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error syncing CoinGecko: {e}"
            logger.error(error_msg)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_sync_status(exchange_id, SyncStatus.FAILED, error_message=error_msg, duration_seconds=duration)

            return {
                "exchange": exchange_id,
                "status": SyncStatus.FAILED.value,
                "error": error_msg,
                "duration_seconds": duration,
            }

        except Exception as e:
            error_msg = f"Error syncing CoinGecko: {e}"
            logger.error(error_msg)

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_sync_status(exchange_id, SyncStatus.FAILED, error_message=error_msg, duration_seconds=duration)

            return {
                "exchange": exchange_id,
                "status": SyncStatus.FAILED.value,
                "error": error_msg,
                "duration_seconds": duration,
            }

        finally:
            self._release_sync_lock(exchange_id)

    async def sync_exchange(self, exchange_id: str) -> Dict[str, Any]:
        """
        Sync data from a specific exchange.

        Routes the sync request to the appropriate exchange sync method.

        Args:
            exchange_id: Exchange identifier (binance, coingecko, etc.)

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Syncing exchange: {exchange_id}")

        if exchange_id == "binance":
            return await self.sync_binance_pairs()
        elif exchange_id == "coingecko":
            return await self.sync_coingecko_listings()
        else:
            return {
                "exchange": exchange_id,
                "status": SyncStatus.FAILED.value,
                "error": f"Unknown exchange: {exchange_id}"
            }

    async def sync_all_exchanges(self, exchanges: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync all configured exchanges.

        Args:
            exchanges: Optional list of specific exchanges to sync.
                      If None, syncs all enabled exchanges.

        Returns:
            Dictionary with aggregate sync results
        """
        start_time = datetime.utcnow()

        # Get enabled exchanges if not specified
        if exchanges is None:
            with get_db_context() as session:
                result = session.execute(
                    text("SELECT id FROM exchanges WHERE enabled = 1")
                )
                exchanges = [row[0] for row in result.fetchall()]

        logger.info(f"Starting sync for exchanges: {exchanges}")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "exchanges": exchanges,
            "results": [],
            "summary": {
                "total": len(exchanges),
                "successful": 0,
                "failed": 0,
                "pending": 0,
            }
        }

        # Sync each exchange
        for exchange_id in exchanges:
            result = await self.sync_exchange(exchange_id)
            results["results"].append(result)

            if result["status"] == SyncStatus.SUCCESS.value:
                results["summary"]["successful"] += 1
            elif result["status"] == SyncStatus.FAILED.value:
                results["summary"]["failed"] += 1
            elif result["status"] == SyncStatus.PENDING.value:
                results["summary"]["pending"] += 1

        duration = (datetime.utcnow() - start_time).total_seconds()
        results["duration_seconds"] = duration

        logger.info(f"Sync all completed: {results['summary']}")

        return results

    def get_sync_status(self, exchange_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sync status for exchanges.

        Args:
            exchange_id: Optional specific exchange to query.
                        If None, returns status for all exchanges.

        Returns:
            Dictionary with sync status information
        """
        try:
            with engine.connect() as conn:
                # Ensure sync_status table exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sync_status (
                        exchange_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        last_sync_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        records_synced INTEGER DEFAULT 0,
                        error_message TEXT,
                        duration_seconds REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()

                if exchange_id:
                    # Get status for specific exchange
                    result = conn.execute(
                        text("SELECT * FROM sync_status WHERE exchange_id = :exchange_id"),
                        {"exchange_id": exchange_id}
                    ).fetchone()

                    if result:
                        return {
                            "exchange_id": result[0],
                            "status": result[1],
                            "last_sync_at": result[2].isoformat() if result[2] else None,
                            "records_synced": result[3],
                            "error_message": result[4],
                            "duration_seconds": result[5],
                            "updated_at": result[6].isoformat() if result[6] else None,
                        }
                    else:
                        return {"exchange_id": exchange_id, "status": "not_synced"}

                else:
                    # Get status for all exchanges
                    results = conn.execute(text("SELECT * FROM sync_status")).fetchall()

                    return [
                        {
                            "exchange_id": row[0],
                            "status": row[1],
                            "last_sync_at": row[2].isoformat() if row[2] else None,
                            "records_synced": row[3],
                            "error_message": row[4],
                            "duration_seconds": row[5],
                            "updated_at": row[6].isoformat() if row[6] else None,
                        }
                        for row in results
                    ]

        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"error": str(e)}

    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """
        Get data quality metrics for synchronized data.

        Returns:
            Dictionary with data quality metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "exchanges": {},
            "coins": {},
            "trading_pairs": {},
        }

        try:
            with engine.connect() as conn:
                # Exchange metrics
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled
                    FROM exchanges
                """)).fetchone()

                if result:
                    metrics["exchanges"] = {
                        "total": result[0] or 0,
                        "enabled": result[1] or 0,
                    }

                # Coin metrics
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled,
                        COUNT(DISTINCT coingecko_id) as with_coingecko_id
                    FROM coins
                """)).fetchone()

                if result:
                    metrics["coins"] = {
                        "total": result[0] or 0,
                        "enabled": result[1] or 0,
                        "with_coingecko_id": result[2] or 0,
                    }

                # Trading pair metrics
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled,
                        COUNT(DISTINCT exchange_id) as exchanges
                    FROM trading_pairs
                """)).fetchone()

                if result:
                    metrics["trading_pairs"] = {
                        "total": result[0] or 0,
                        "enabled": result[1] or 0,
                        "exchanges": result[2] or 0,
                    }

                # Per-exchange pair counts
                result = conn.execute(text("""
                    SELECT
                        exchange_id,
                        COUNT(*) as count,
                        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled
                    FROM trading_pairs
                    GROUP BY exchange_id
                """)).fetchall()

                metrics["trading_pairs"]["by_exchange"] = {
                    row[0]: {"total": row[1], "enabled": row[2]}
                    for row in result
                }

        except Exception as e:
            logger.error(f"Error getting data quality metrics: {e}")
            metrics["error"] = str(e)

        return metrics
