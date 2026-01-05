"""
Market Data Manager Service.

High-level service for managing market metadata including coins,
exchanges, and trading pairs. Handles syncing from external APIs
and provides market overview data.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

import httpx

from database.connection import get_db_session
from database.repositories.market import (
    CoinRepository,
    ExchangeRepository,
    MarketPairRepository,
    StoredPriceDataRepository,
)
from models.market import (
    Coin,
    Exchange,
    MarketPair,
    StoredPriceData,
    MarketOverview,
    MarketSyncRequest,
    MarketSyncResponse,
    AssetType,
    ExchangeType,
)

logger = logging.getLogger(__name__)


# CoinGecko API configuration
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")


class MarketDataManager:
    """
    High-level service for managing market data.

    Handles syncing coin/exchange metadata from external APIs,
    caching prices, and providing market overview statistics.
    """

    def __init__(self):
        """Initialize the market data manager."""
        self.coin_repo: Optional[CoinRepository] = None
        self.exchange_repo: Optional[ExchangeRepository] = None
        self.pair_repo: Optional[MarketPairRepository] = None
        self.price_cache_repo: Optional[StoredPriceDataRepository] = None

    def _init_repositories(self):
        """Initialize repository instances."""
        if not self.coin_repo:
            session = get_db_session().__enter__()
            self.coin_repo = CoinRepository(session)
            self.exchange_repo = ExchangeRepository(session)
            self.pair_repo = MarketPairRepository(session)
            self.price_cache_repo = StoredPriceDataRepository(session)
            self._session = session

    def _close_repositories(self):
        """Close repository sessions."""
        if hasattr(self, '_session') and self._session:
            self._session.close()
            self.coin_repo = None
            self.exchange_repo = None
            self.pair_repo = None
            self.price_cache_repo = None

    def sync_coins_from_exchange(
        self,
        exchange: Optional[str] = None,
        force_refresh: bool = False,
    ) -> MarketSyncResponse:
        """
        Sync coin metadata from exchange APIs.

        Args:
            exchange: Specific exchange to sync (None = all active exchanges)
            force_refresh: Force refresh even if recently synced

        Returns:
            MarketSyncResponse with sync results
        """
        self._init_repositories()

        try:
            exchanges_synced = []
            coins_added = 0
            coins_updated = 0
            errors = []

            # Get exchanges to sync
            if exchange:
                exchanges_to_sync = [self.exchange_repo.get(exchange)]
                exchanges_to_sync = [e for e in exchanges_to_sync if e]
            else:
                exchanges_to_sync = self.exchange_repo.get_active_exchanges()

            for exchange_model in exchanges_to_sync:
                try:
                    # Sync coins for this exchange
                    if exchange_model.name.lower() == "coingecko":
                        result = self._sync_from_coingecko()
                        exchanges_synced.append(exchange_model.name)
                        coins_added += result.get("coins_added", 0)
                        coins_updated += result.get("coins_updated", 0)
                    else:
                        logger.warning(f"Exchange sync not implemented for: {exchange_model.name}")

                except Exception as e:
                    error_msg = f"Error syncing {exchange_model.name}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return MarketSyncResponse(
                success=len(errors) == 0,
                message=f"Synced {len(exchanges_synced)} exchanges",
                exchanges_synced=exchanges_synced,
                coins_added=coins_added,
                coins_updated=coins_updated,
                pairs_added=0,
                pairs_updated=0,
                errors=errors,
            )

        finally:
            self._close_repositories()

    def _sync_from_coingecko(self) -> Dict[str, int]:
        """
        Sync coin data from CoinGecko API.

        Returns:
            Dictionary with counts of added/updated coins
        """
        coins_added = 0
        coins_updated = 0

        try:
            headers = {}
            if COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

            with httpx.Client(timeout=30.0) as client:
                # Get top coins by market cap
                params = {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": 1,
                    "sparkline": "false",
                }

                response = client.get(
                    f"{COINGECKO_API_BASE}/coins/markets",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()

                coins_data = response.json()

                for coin_data in coins_data:
                    coin_dict = {
                        "symbol": coin_data.get("symbol", "").upper(),
                        "name": coin_data.get("name", ""),
                        "type": "crypto",
                        "coingecko_id": coin_data.get("id", ""),
                        "market_cap": Decimal(str(coin_data.get("market_cap", 0))) if coin_data.get("market_cap") else None,
                        "volume_24h": Decimal(str(coin_data.get("total_volume", 0))) if coin_data.get("total_volume") else None,
                        "circulating_supply": Decimal(str(coin_data.get("circulating_supply", 0))) if coin_data.get("circulating_supply") else None,
                        "total_supply": Decimal(str(coin_data.get("total_supply", 0))) if coin_data.get("total_supply") else None,
                        "logo_url": coin_data.get("image"),
                        "is_active": True,
                    }

                    existing = self.coin_repo.get_by_symbol(coin_dict["symbol"])
                    if existing:
                        self.coin_repo.upsert_coin(coin_dict)
                        coins_updated += 1
                    else:
                        self.coin_repo.upsert_coin(coin_dict)
                        coins_added += 1

        except Exception as e:
            logger.error(f"Error syncing from CoinGecko: {e}")
            raise

        return {"coins_added": coins_added, "coins_updated": coins_updated}

    def update_price_cache(self, symbols: Optional[List[str]] = None) -> int:
        """
        Update cached prices for specified symbols or all active coins.

        Args:
            symbols: List of symbols to update (None = all active coins)

        Returns:
            Number of prices updated
        """
        self._init_repositories()

        try:
            updated_count = 0

            if not symbols:
                # Get all active coins
                coins = self.coin_repo.get_active_coins(limit=100)
                symbols = [coin.symbol for coin in coins]

            for symbol in symbols:
                try:
                    # Fetch current price from external API
                    import asyncio
                    from services.market_data import get_current_price

                    # Run async function in sync context
                    loop = asyncio.get_event_loop()
                    price_data = loop.run_until_complete(get_current_price(symbol))

                    if price_data:
                        cache_data = {
                            "symbol": symbol,
                            "price": price_data.get("price"),
                            "price_change_24h": price_data.get("price_change_24h"),
                            "price_change_percent_24h": price_data.get("price_change_percent_24h"),
                            "market_cap": price_data.get("market_cap"),
                            "volume_24h": price_data.get("volume_24h"),
                            "exchange": "coingecko",
                        }

                        self.price_cache_repo.upsert_price(cache_data)
                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error updating price cache for {symbol}: {e}")

            return updated_count

        finally:
            self._close_repositories()

    def get_market_overview(self) -> MarketOverview:
        """
        Get overview of all markets.

        Returns summary statistics and top performing assets.

        Returns:
            MarketOverview with market statistics
        """
        self._init_repositories()

        try:
            # Get counts
            all_coins = self.coin_repo.get_all()
            active_coins = self.coin_repo.get_active_coins()
            all_exchanges = self.exchange_repo.get_all()
            active_exchanges = self.exchange_repo.get_active_exchanges()
            all_pairs = self.pair_repo.get_all()
            active_pairs = self.pair_repo.get_many(is_active=True)

            # Calculate totals
            total_market_cap = sum(
                coin.market_cap or Decimal("0")
                for coin in active_coins
            )
            total_volume = sum(
                coin.volume_24h or Decimal("0")
                for coin in active_coins
            )

            # Get top lists
            top_by_market_cap = self.coin_repo.get_top_by_market_cap(limit=10)
            top_by_volume = self.coin_repo.get_top_by_volume(limit=10)
            top_gainers = self.coin_repo.get_top_gainers_24h(limit=10)
            top_losers = self.coin_repo.get_top_losers_24h(limit=10)

            return MarketOverview(
                total_coins=len(all_coins),
                active_coins=len(active_coins),
                total_exchanges=len(all_exchanges),
                active_exchanges=len(active_exchanges),
                total_pairs=len(all_pairs),
                active_pairs=len(active_pairs),
                total_market_cap=total_market_cap,
                total_24h_volume=total_volume,
                top_gainers_24h=top_gainers,
                top_losers_24h=top_losers,
                top_by_volume=[
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "volume_24h": float(c.volume_24h) if c.volume_24h else 0,
                    }
                    for c in top_by_volume
                ],
                top_by_market_cap=[
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "market_cap": float(c.market_cap) if c.market_cap else 0,
                    }
                    for c in top_by_market_cap
                ],
            )

        finally:
            self._close_repositories()

    def search_coins(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search coins by symbol or name.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching coins with basic info
        """
        self._init_repositories()

        try:
            coins = self.coin_repo.search_coins(query, limit=limit)

            return [
                {
                    "symbol": coin.symbol,
                    "name": coin.name,
                    "type": coin.type,
                    "exchanges": [coin.exchange] if coin.exchange else [],
                    "is_active": coin.is_active,
                    "market_cap": float(coin.market_cap) if coin.market_cap else None,
                    "volume_24h": float(coin.volume_24h) if coin.volume_24h else None,
                }
                for coin in coins
            ]

        finally:
            self._close_repositories()

    def get_popular_coins(
        self,
        by: str = "market_cap",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get popular coins by various metrics.

        Args:
            by: Sort metric - "market_cap", "volume", "gainers", "losers"
            limit: Maximum results to return

        Returns:
            List of popular coins
        """
        self._init_repositories()

        try:
            if by == "market_cap":
                coins = self.coin_repo.get_top_by_market_cap(limit=limit)
            elif by == "volume":
                coins = self.coin_repo.get_top_by_volume(limit=limit)
            elif by == "gainers":
                return self.coin_repo.get_top_gainers_24h(limit=limit)
            elif by == "losers":
                return self.coin_repo.get_top_losers_24h(limit=limit)
            else:
                coins = self.coin_repo.get_active_coins(limit=limit)

            return [
                {
                    "symbol": coin.symbol,
                    "name": coin.name,
                    "type": coin.type,
                    "market_cap": float(coin.market_cap) if coin.market_cap else None,
                    "volume_24h": float(coin.volume_24h) if coin.volume_24h else None,
                }
                for coin in coins
            ]

        finally:
            self._close_repositories()

    def get_available_pairs(
        self,
        base_coin: Optional[str] = None,
        quote_coin: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get available trading pairs.

        Args:
            base_coin: Filter by base coin
            quote_coin: Filter by quote coin
            exchange: Filter by exchange
            limit: Maximum results

        Returns:
            List of trading pairs
        """
        self._init_repositories()

        try:
            if exchange:
                pairs = self.pair_repo.get_by_exchange(exchange_id=exchange)
                pairs = [p for p in pairs if p.is_active][:limit]
            else:
                pairs = self.pair_repo.get_available_pairs(
                    base_coin=base_coin,
                    quote_coin=quote_coin,
                )[:limit]

            return [
                {
                    "id": pair.id,
                    "symbol": pair.symbol,
                    "exchange": pair.exchange_id,
                    "base_coin": pair.base_coin_id,
                    "quote_coin": pair.quote_coin_id,
                    "current_price": float(pair.current_price) if pair.current_price else None,
                    "volume_24h": float(pair.volume_24h) if pair.volume_24h else None,
                    "is_active": pair.is_active,
                    "is_trading": pair.is_trading,
                }
                for pair in pairs
            ]

        finally:
            self._close_repositories()

    def get_exchanges(
        self,
        exchange_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get list of exchanges.

        Args:
            exchange_type: Filter by type (CEX/DEX)
            active_only: Only return active exchanges

        Returns:
            List of exchanges
        """
        self._init_repositories()

        try:
            if exchange_type:
                exchanges = self.exchange_repo.get_by_type(exchange_type)
            elif active_only:
                exchanges = self.exchange_repo.get_active_exchanges()
            else:
                exchanges = self.exchange_repo.get_all()

            return [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "type": ex.type,
                    "is_active": ex.is_active,
                    "supports_websocket": ex.supports_websocket,
                    "supports_historical": ex.supports_historical,
                    "website": ex.website,
                }
                for ex in exchanges
            ]

        finally:
            self._close_repositories()


# Singleton instance
_market_data_manager: Optional[MarketDataManager] = None


def get_market_data_manager() -> MarketDataManager:
    """Get or create the MarketDataManager singleton."""
    global _market_data_manager
    if _market_data_manager is None:
        _market_data_manager = MarketDataManager()
    return _market_data_manager
