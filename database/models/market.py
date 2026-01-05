"""
Market Data SQLAlchemy ORM models.

Stores metadata about coins, exchanges, trading pairs, and cached price data.
Also stores real-time data from WebSocket feeds including order books, trades,
and funding rates.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Numeric, String, Boolean, Integer, DateTime, JSON, Index, ForeignKey, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import BaseModel
from decimal import Decimal


class CoinModel(BaseModel):
    """
    SQLAlchemy model for tradeable assets/coins.

    Stores metadata about cryptocurrencies and other tradeable assets.
    """

    __tablename__ = "coins"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Basic info
    symbol: Mapped[str] = mapped_column(String(20), index=True, unique=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20), default="crypto")  # crypto, stock, forex, etc.
    base_currency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quote_currency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # External IDs
    coingecko_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    coinmarketcap_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Market data
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    volume_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    circulating_supply: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_supply: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Metadata
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_coins_symbol_active', 'symbol', 'is_active'),
        Index('idx_coins_type', 'type'),
    )


class ExchangeModel(BaseModel):
    """
    SQLAlchemy model for cryptocurrency exchanges.

    Stores exchange metadata and API configuration.
    """

    __tablename__ = "exchanges"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(10), default="cex")  # cex or dex
    api_endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    websocket_endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # API credentials (encrypted in production)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Rate limits
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_per_second: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Supported features
    supports_websocket: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_rest: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_historical: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_exchanges_active', 'is_active'),
        Index('idx_exchanges_type', 'type'),
    )


class MarketPairModel(BaseModel):
    """
    SQLAlchemy model for trading pairs.

    Links base and quote coins on specific exchanges with trading constraints.
    """

    __tablename__ = "market_pairs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    exchange_id: Mapped[str] = mapped_column(String(50), ForeignKey("exchanges.id"), index=True)
    base_coin_id: Mapped[str] = mapped_column(String(20), ForeignKey("coins.symbol"), index=True)
    quote_coin_id: Mapped[str] = mapped_column(String(20), ForeignKey("coins.symbol"), index=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)  # e.g., BTC/USDT

    # Trading constraints
    min_tick_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    min_lot_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    max_lot_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)

    # Current market data
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    volume_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    price_change_24h_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_trading: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_market_pairs_exchange', 'exchange_id', 'is_active'),
        Index('idx_market_pairs_base_quote', 'base_coin_id', 'quote_coin_id'),
        Index('idx_market_pairs_symbol', 'symbol'),
    )


class StoredPriceDataModel(BaseModel):
    """
    SQLAlchemy model for cached price data.

    Stores recent price data with TTL for fast access without hitting external APIs.
    """

    __tablename__ = "cached_prices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Price data
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    bid_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    ask_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    volume_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Price changes
    price_change_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    price_change_percent_1h: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    price_change_percent_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    price_change_percent_7d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # Market data
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    market_cap_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Cache metadata
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_cached_prices_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_cached_prices_updated', 'updated_at'),
    )


class OrderBookModel(BaseModel):
    """
    SQLAlchemy model for real-time order book data.

    Stores order book depth snapshots from WebSocket feeds.
    Used for liquidity analysis and price impact calculations.
    """

    __tablename__ = "order_books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    exchange: Mapped[str] = mapped_column(String(50), index=True)

    # Order book data
    bids: Mapped[dict] = mapped_column(JSON)  # List of [price, quantity] pairs
    asks: Mapped[dict] = mapped_column(JSON)  # List of [price, quantity] pairs

    # Snapshot metadata
    sequence_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For ordering updates
    last_update_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_order_books_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_order_books_timestamp', 'timestamp'),
        Index('idx_order_books_symbol_timestamp', 'symbol', 'timestamp'),
    )


class TradeModel(BaseModel):
    """
    SQLAlchemy model for individual trade data.

    Stores executed trades from WebSocket feeds.
    Used for volume analysis, trade clustering, and whale tracking.
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    exchange: Mapped[str] = mapped_column(String(50), index=True)

    # Trade data
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    side: Mapped[str] = mapped_column(String(10))  # 'buy' or 'sell'

    # Trade identifiers
    trade_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Trade metadata
    is_buyer_maker: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_best_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Timestamps
    trade_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_trades_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_trades_symbol_time', 'symbol', 'trade_time'),
        Index('idx_trades_exchange_time', 'exchange', 'trade_time'),
        Index('idx_trades_trade_id', 'trade_id'),
    )


class FundingRateModel(BaseModel):
    """
    SQLAlchemy model for futures funding rates.

    Stores funding rates for perpetual futures contracts.
    Used for futures trading and market sentiment analysis.
    """

    __tablename__ = "funding_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    exchange: Mapped[str] = mapped_column(String(50), index=True)

    # Funding rate data
    funding_rate: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    mark_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    index_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    settle_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)

    # Funding interval
    funding_interval: Mapped[int] = mapped_column(Integer, default=8)  # Hours
    next_funding_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_funding_rates_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_funding_rates_timestamp', 'timestamp'),
        Index('idx_funding_rates_symbol_timestamp', 'symbol', 'timestamp'),
    )
