"""
Market data repository implementations.

Provides CRUD operations for coins, exchanges, and market pairs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc

from database.base import BaseRepository
from database.models.market import (
    CoinModel,
    ExchangeModel,
    MarketPairModel,
    StoredPriceDataModel,
)


class CoinRepository(BaseRepository[CoinModel]):
    """Repository for coin operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(CoinModel, session)

    def get_by_symbol(self, symbol: str) -> Optional[CoinModel]:
        """Get coin by symbol."""
        return self.get_by(symbol=symbol.upper())

    def get_active_coins(self, limit: Optional[int] = None) -> List[CoinModel]:
        """Get all active coins."""
        stmt = (
            select(CoinModel)
            .where(CoinModel.is_active == True)
            .order_by(CoinModel.market_cap.desc().nullslast())
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_coins_by_type(self, coin_type: str, limit: Optional[int] = None) -> List[CoinModel]:
        """Get coins by type (crypto, stock, forex, etc.)."""
        stmt = (
            select(CoinModel)
            .where(CoinModel.type == coin_type)
            .where(CoinModel.is_active == True)
            .order_by(CoinModel.market_cap.desc().nullslast())
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_coins_by_exchange(self, exchange: str, limit: Optional[int] = None) -> List[CoinModel]:
        """Get coins for a specific exchange."""
        stmt = (
            select(CoinModel)
            .where(CoinModel.exchange == exchange)
            .where(CoinModel.is_active == True)
            .order_by(CoinModel.market_cap.desc().nullslast())
        )
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def search_coins(self, query: str, limit: int = 50) -> List[CoinModel]:
        """Search coins by symbol or name."""
        stmt = (
            select(CoinModel)
            .where(
                or_(
                    CoinModel.symbol.ilike(f"%{query}%"),
                    CoinModel.name.ilike(f"%{query}%"),
                )
            )
            .where(CoinModel.is_active == True)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def upsert_coin(self, coin_data: Dict[str, Any]) -> CoinModel:
        """Insert or update a coin."""
        symbol = coin_data.get("symbol", "").upper()

        existing = self.get_by_symbol(symbol)
        if existing:
            # Update existing
            for key, value in coin_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.flush()
            return existing
        else:
            # Create new
            coin_data["symbol"] = symbol
            coin_data["id"] = f"coin_{symbol}"
            return self.create(**coin_data)

    def bulk_upsert_coins(self, coins_data: List[Dict[str, Any]]) -> int:
        """Bulk insert or update coins."""
        count = 0
        for coin_data in coins_data:
            self.upsert_coin(coin_data)
            count += 1
        self.session.flush()
        return count

    def get_top_by_market_cap(self, limit: int = 100) -> List[CoinModel]:
        """Get top coins by market cap."""
        stmt = (
            select(CoinModel)
            .where(CoinModel.is_active == True)
            .where(CoinModel.market_cap.isnot(None))
            .order_by(desc(CoinModel.market_cap))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_top_by_volume(self, limit: int = 100) -> List[CoinModel]:
        """Get top coins by 24h volume."""
        stmt = (
            select(CoinModel)
            .where(CoinModel.is_active == True)
            .where(CoinModel.volume_24h.isnot(None))
            .order_by(desc(CoinModel.volume_24h))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_top_gainers_24h(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top gainers in last 24h."""
        # This requires joining with price data
        stmt = (
            select(
                CoinModel.symbol,
                CoinModel.name,
                StoredPriceDataModel.price_change_percent_24h,
            )
            .join(
                StoredPriceDataModel,
                CoinModel.symbol == StoredPriceDataModel.symbol,
            )
            .where(CoinModel.is_active == True)
            .where(StoredPriceDataModel.price_change_percent_24h.isnot(None))
            .order_by(desc(StoredPriceDataModel.price_change_percent_24h))
            .limit(limit)
        )
        results = self.session.execute(stmt).all()
        return [
            {
                "symbol": r.symbol,
                "name": r.name,
                "change_24h_percent": float(r.price_change_percent_24h) if r.price_change_percent_24h else 0,
            }
            for r in results
        ]

    def get_top_losers_24h(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top losers in last 24h."""
        stmt = (
            select(
                CoinModel.symbol,
                CoinModel.name,
                StoredPriceDataModel.price_change_percent_24h,
            )
            .join(
                StoredPriceDataModel,
                CoinModel.symbol == StoredPriceDataModel.symbol,
            )
            .where(CoinModel.is_active == True)
            .where(StoredPriceDataModel.price_change_percent_24h.isnot(None))
            .order_by(StoredPriceDataModel.price_change_percent_24h.asc())
            .limit(limit)
        )
        results = self.session.execute(stmt).all()
        return [
            {
                "symbol": r.symbol,
                "name": r.name,
                "change_24h_percent": float(r.price_change_percent_24h) if r.price_change_percent_24h else 0,
            }
            for r in results
        ]


class ExchangeRepository(BaseRepository[ExchangeModel]):
    """Repository for exchange operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(ExchangeModel, session)

    def get_by_name(self, name: str) -> Optional[ExchangeModel]:
        """Get exchange by name."""
        return self.get_by(name=name)

    def get_active_exchanges(self) -> List[ExchangeModel]:
        """Get all active exchanges."""
        return self.get_many(is_active=True)

    def get_by_type(self, exchange_type: str) -> List[ExchangeModel]:
        """Get exchanges by type (CEX or DEX)."""
        return self.get_many(type=exchange_type, is_active=True)

    def upsert_exchange(self, exchange_data: Dict[str, Any]) -> ExchangeModel:
        """Insert or update an exchange."""
        exchange_id = exchange_data.get("id")

        existing = self.get(exchange_id)
        if existing:
            # Update existing
            for key, value in exchange_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.flush()
            return existing
        else:
            # Create new
            return self.create(**exchange_data)

    def get_exchanges_with_websocket(self) -> List[ExchangeModel]:
        """Get exchanges that support WebSocket."""
        stmt = (
            select(ExchangeModel)
            .where(ExchangeModel.is_active == True)
            .where(ExchangeModel.supports_websocket == True)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_exchanges_with_historical(self) -> List[ExchangeModel]:
        """Get exchanges that support historical data."""
        stmt = (
            select(ExchangeModel)
            .where(ExchangeModel.is_active == True)
            .where(ExchangeModel.supports_historical == True)
        )
        return list(self.session.execute(stmt).scalars().all())


class MarketPairRepository(BaseRepository[MarketPairModel]):
    """Repository for market pair operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(MarketPairModel, session)

    def get_by_symbol(self, symbol: str) -> Optional[MarketPairModel]:
        """Get pair by symbol (e.g., BTC/USDT)."""
        return self.get_by(symbol=symbol.upper())

    def get_by_exchange(self, exchange_id: str) -> List[MarketPairModel]:
        """Get all pairs for an exchange."""
        stmt = (
            select(MarketPairModel)
            .where(MarketPairModel.exchange_id == exchange_id)
            .where(MarketPairModel.is_active == True)
            .order_by(MarketPairModel.volume_24h.desc().nullslast())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_available_pairs(self, base_coin: Optional[str] = None, quote_coin: Optional[str] = None) -> List[MarketPairModel]:
        """Get all tradeable pairs, optionally filtered by base/quote coin."""
        stmt = select(MarketPairModel).where(MarketPairModel.is_active == True)

        if base_coin:
            stmt = stmt.where(MarketPairModel.base_coin_id == base_coin.upper())
        if quote_coin:
            stmt = stmt.where(MarketPairModel.quote_coin_id == quote_coin.upper())

        stmt = stmt.order_by(MarketPairModel.volume_24h.desc().nullslast())
        return list(self.session.execute(stmt).scalars().all())

    def get_pairs_for_coin(self, coin_symbol: str) -> List[MarketPairModel]:
        """Get all pairs where a coin is either base or quote."""
        stmt = (
            select(MarketPairModel)
            .where(
                or_(
                    MarketPairModel.base_coin_id == coin_symbol.upper(),
                    MarketPairModel.quote_coin_id == coin_symbol.upper(),
                )
            )
            .where(MarketPairModel.is_active == True)
            .order_by(MarketPairModel.volume_24h.desc().nullslast())
        )
        return list(self.session.execute(stmt).scalars().all())

    def upsert_pair(self, pair_data: Dict[str, Any]) -> MarketPairModel:
        """Insert or update a trading pair."""
        symbol = pair_data.get("symbol", "").upper()
        exchange_id = pair_data.get("exchange_id")

        # Check if exists
        existing = (
            self.session.query(MarketPairModel)
            .filter(
                and_(
                    MarketPairModel.symbol == symbol,
                    MarketPairModel.exchange_id == exchange_id,
                )
            )
            .first()
        )

        if existing:
            # Update existing
            for key, value in pair_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.flush()
            return existing
        else:
            # Create new
            pair_data["symbol"] = symbol
            if "id" not in pair_data:
                pair_data["id"] = f"pair_{exchange_id}_{symbol.replace('/', '_')}"
            return self.create(**pair_data)

    def bulk_upsert_pairs(self, pairs_data: List[Dict[str, Any]]) -> int:
        """Bulk insert or update pairs."""
        count = 0
        for pair_data in pairs_data:
            self.upsert_pair(pair_data)
            count += 1
        self.session.flush()
        return count

    def get_top_pairs_by_volume(self, exchange_id: Optional[str] = None, limit: int = 100) -> List[MarketPairModel]:
        """Get top pairs by 24h volume."""
        stmt = (
            select(MarketPairModel)
            .where(MarketPairModel.is_active == True)
            .where(MarketPairModel.volume_24h.isnot(None))
        )

        if exchange_id:
            stmt = stmt.where(MarketPairModel.exchange_id == exchange_id)

        stmt = stmt.order_by(desc(MarketPairModel.volume_24h)).limit(limit)
        return list(self.session.execute(stmt).scalars().all())


class StoredPriceDataRepository(BaseRepository[StoredPriceDataModel]):
    """Repository for cached price data operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StoredPriceDataModel, session)

    def get_latest_price(self, symbol: str, exchange: Optional[str] = None) -> Optional[StoredPriceDataModel]:
        """Get latest cached price for a symbol."""
        stmt = select(StoredPriceDataModel).where(StoredPriceDataModel.symbol == symbol.upper())

        if exchange:
            stmt = stmt.where(StoredPriceDataModel.exchange == exchange)

        stmt = stmt.order_by(desc(StoredPriceDataModel.updated_at)).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_stale_prices(self, stale_seconds: int = 60) -> List[StoredPriceDataModel]:
        """Get all price entries that are stale (older than stale_seconds)."""
        cutoff = datetime.utcnow() - timedelta(seconds=stale_seconds)
        stmt = (
            select(StoredPriceDataModel)
            .where(StoredPriceDataModel.updated_at < cutoff)
        )
        return list(self.session.execute(stmt).scalars().all())

    def upsert_price(self, price_data: Dict[str, Any]) -> StoredPriceDataModel:
        """Insert or update cached price data."""
        symbol = price_data.get("symbol", "").upper()
        exchange = price_data.get("exchange")

        # Find existing
        stmt = select(StoredPriceDataModel).where(
            and_(
                StoredPriceDataModel.symbol == symbol,
                StoredPriceDataModel.exchange == exchange,
            )
        )
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            # Update existing
            for key, value in price_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.flush()
            return existing
        else:
            # Create new
            price_data["symbol"] = symbol
            if "id" not in price_data:
                exchange_suffix = exchange or "default"
                price_data["id"] = f"price_{symbol}_{exchange_suffix}"
            return self.create(**price_data)

    def bulk_upsert_prices(self, prices_data: List[Dict[str, Any]]) -> int:
        """Bulk insert or update price cache entries."""
        count = 0
        for price_data in prices_data:
            self.upsert_price(price_data)
            count += 1
        self.session.flush()
        return count

    def delete_stale_prices(self, stale_seconds: int = 3600) -> int:
        """Delete price entries older than stale_seconds."""
        cutoff = datetime.utcnow() - timedelta(seconds=stale_seconds)
        stmt = select(StoredPriceDataModel).where(
            StoredPriceDataModel.updated_at < cutoff
        )
        stale_entries = self.session.execute(stmt).scalars().all()
        count = len(stale_entries)
        for entry in stale_entries:
            self.session.delete(entry)
        self.session.flush()
        return count
