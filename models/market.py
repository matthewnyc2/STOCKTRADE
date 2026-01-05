"""
Market Data Pydantic models.

Defines models for coins, exchanges, trading pairs, and market metadata.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AssetType(str, Enum):
    """Types of trading assets."""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    COMMODITY = "commodity"
    INDEX = "index"


class ExchangeType(str, Enum):
    """Types of exchanges."""
    CEX = "cex"  # Centralized Exchange
    DEX = "dex"  # Decentralized Exchange


class Coin(BaseModel):
    """
    Represents a tradeable asset/cryptocurrency.

    Contains metadata about a coin including symbol, name, type,
    and which exchanges it trades on.
    """

    symbol: str = Field(min_length=1, max_length=20, description="Trading symbol (e.g., BTC, ETH)")
    name: str = Field(min_length=1, max_length=200, description="Full name of the coin")
    type: AssetType = Field(default=AssetType.CRYPTO, description="Asset type")
    base_currency: Optional[str] = Field(default=None, description="Base currency for forex pairs")
    quote_currency: Optional[str] = Field(default=None, description="Quote currency (e.g., USD, USDT)")
    exchange: Optional[str] = Field(default=None, description="Primary exchange")
    is_active: bool = Field(default=True, description="Whether the coin is actively traded")
    coingecko_id: Optional[str] = Field(default=None, description="CoinGecko API ID")
    coinmarketcap_id: Optional[str] = Field(default=None, description="CoinMarketCap ID")

    # Market data
    market_cap: Optional[Decimal] = Field(default=None, description="Current market cap")
    volume_24h: Optional[Decimal] = Field(default=None, description="24h trading volume")
    circulating_supply: Optional[Decimal] = Field(default=None, description="Circulating supply")
    total_supply: Optional[Decimal] = Field(default=None, description="Total supply")

    # Metadata
    logo_url: Optional[str] = Field(default=None, description="URL to coin logo")
    website: Optional[str] = Field(default=None, description="Official website")
    description: Optional[str] = Field(default=None, description="Coin description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase."""
        return v.upper()


class Exchange(BaseModel):
    """
    Represents a cryptocurrency exchange.

    Contains exchange metadata including API endpoints,
    websocket feeds, and supported features.
    """

    id: str = Field(min_length=1, max_length=50, description="Exchange identifier")
    name: str = Field(min_length=1, max_length=200, description="Exchange name")
    type: ExchangeType = Field(description="Exchange type (CEX or DEX)")
    api_endpoint: Optional[str] = Field(default=None, description="REST API base URL")
    websocket_endpoint: Optional[str] = Field(default=None, description="WebSocket endpoint URL")
    is_active: bool = Field(default=True, description="Whether exchange is active")

    # API credentials (optional, for when exchange supports multiple keys)
    api_key: Optional[str] = Field(default=None, description="API key")
    api_secret: Optional[str] = Field(default=None, description="API secret")

    # Rate limits
    rate_limit_per_minute: Optional[int] = Field(default=None, description="API rate limit")
    rate_limit_per_second: Optional[int] = Field(default=None, description="API rate limit")

    # Supported features
    supports_websocket: bool = Field(default=False, description="Supports WebSocket API")
    supports_rest: bool = Field(default=True, description="Supports REST API")
    supports_historical: bool = Field(default=False, description="Supports historical data")

    # Metadata
    logo_url: Optional[str] = Field(default=None, description="Exchange logo URL")
    website: Optional[str] = Field(default=None, description="Exchange website")
    description: Optional[str] = Field(default=None, description="Exchange description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MarketPair(BaseModel):
    """
    Represents a tradeable pair on an exchange.

    Links a base coin and quote coin on a specific exchange
    with trading constraints.
    """

    id: str = Field(min_length=1, max_length=50, description="Pair identifier")
    exchange_id: str = Field(min_length=1, description="Exchange identifier")
    base_coin_id: str = Field(min_length=1, description="Base coin symbol")
    quote_coin_id: str = Field(min_length=1, description="Quote coin symbol")
    symbol: str = Field(min_length=1, description="Trading pair symbol (e.g., BTC/USDT)")

    # Trading constraints
    min_tick_size: Optional[Decimal] = Field(default=None, description="Minimum price increment")
    min_lot_size: Optional[Decimal] = Field(default=None, description="Minimum order size")
    max_lot_size: Optional[Decimal] = Field(default=None, description="Maximum order size")

    # Current market data
    current_price: Optional[Decimal] = Field(default=None, description="Current price")
    volume_24h: Optional[Decimal] = Field(default=None, description="24h volume")
    price_change_24h_percent: Optional[Decimal] = Field(default=None, description="24h price change %")

    # Status
    is_active: bool = Field(default=True, description="Whether pair is tradeable")
    is_trading: bool = Field(default=True, description="Whether trading is currently enabled")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("symbol")
    @classmethod
    def symbol_format(cls, v: str) -> str:
        """Ensure symbol is in correct format (BASE/QUOTE)."""
        return v.upper()


class StoredPriceData(BaseModel):
    """
    Cached recent price data for quick access.

    Used for storing the latest prices in memory/database
    with TTL for fast access without hitting external APIs.
    """

    id: str = Field(min_length=1, description="Price cache entry ID")
    symbol: str = Field(min_length=1, description="Trading symbol")
    exchange: Optional[str] = Field(default=None, description="Exchange name")

    # Price data
    price: Decimal = Field(gt=0, description="Current price")
    bid_price: Optional[Decimal] = Field(default=None, description="Current bid price")
    ask_price: Optional[Decimal] = Field(default=None, description="Current ask price")
    volume_24h: Optional[Decimal] = Field(default=None, description="24h volume")

    # Price changes
    price_change_24h: Optional[Decimal] = Field(default=None, description="24h price change")
    price_change_percent_1h: Optional[Decimal] = Field(default=None, description="1h price change %")
    price_change_percent_24h: Optional[Decimal] = Field(default=None, description="24h price change %")
    price_change_percent_7d: Optional[Decimal] = Field(default=None, description="7d price change %")

    # Market data
    market_cap: Optional[Decimal] = Field(default=None, description="Market cap")
    market_cap_rank: Optional[int] = Field(default=None, description="Market cap rank")

    # Cache metadata
    ttl_seconds: int = Field(default=60, description="Time to live in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        """Ensure symbol is uppercase."""
        return v.upper()


class MarketOverview(BaseModel):
    """
    Overview of all markets.

    Summary statistics and top performing assets across all exchanges.
    """

    total_coins: int = Field(description="Total number of coins tracked")
    active_coins: int = Field(description="Number of actively traded coins")
    total_exchanges: int = Field(description="Total number of exchanges")
    active_exchanges: int = Field(description="Number of active exchanges")
    total_pairs: int = Field(description="Total trading pairs")
    active_pairs: int = Field(description="Number of active trading pairs")

    # Market stats
    total_market_cap: Optional[Decimal] = Field(default=None, description="Total market cap")
    total_24h_volume: Optional[Decimal] = Field(default=None, description="Total 24h volume")

    # Top coins
    top_gainers_24h: List[Dict[str, Any]] = Field(default_factory=list, description="Top gainers 24h")
    top_losers_24h: List[Dict[str, Any]] = Field(default_factory=list, description="Top losers 24h")
    top_by_volume: List[Dict[str, Any]] = Field(default_factory=list, description="Top by volume")
    top_by_market_cap: List[Dict[str, Any]] = Field(default_factory=list, description="Top by market cap")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CoinSearchResult(BaseModel):
    """Result from coin search."""

    symbol: str
    name: str
    type: AssetType
    exchanges: List[str]
    is_active: bool
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None


class MarketSyncRequest(BaseModel):
    """Request to sync market data from exchanges."""

    exchange: Optional[str] = Field(default=None, description="Specific exchange to sync (None = all)")
    force_refresh: bool = Field(default=False, description="Force refresh even if recently synced")
    include_historical: bool = Field(default=False, description="Include historical data")


class MarketSyncResponse(BaseModel):
    """Response from market sync operation."""

    success: bool
    message: str
    exchanges_synced: List[str]
    coins_added: int
    coins_updated: int
    pairs_added: int
    pairs_updated: int
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
