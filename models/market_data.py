"""
Market Data Pydantic models.

Defines models for price data, technical indicators, and related API responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class PriceData(BaseModel):
    """
    Represents a single OHLCV candle.

    Contains open, high, low, close prices and volume for a specific timestamp.
    """

    timestamp: datetime
    open: Decimal = Field(gt=Decimal("0"), description="Opening price")
    high: Decimal = Field(gt=Decimal("0"), description="Highest price")
    low: Decimal = Field(gt=Decimal("0"), description="Lowest price")
    close: Decimal = Field(gt=Decimal("0"), description="Closing price")
    volume: Decimal = Field(ge=Decimal("0"), description="Trading volume")

    @field_validator("high")
    @classmethod
    def high_gte_low(cls, v: Decimal, info) -> Decimal:
        """Ensure high is at least as high as low."""
        if "low" in info.data and v < info.data["low"]:
            raise ValueError("high must be >= low")
        return v

    @field_validator("low")
    @classmethod
    def low_lte_high(cls, v: Decimal, info) -> Decimal:
        """Ensure low is at most as high as high."""
        if "high" in info.data and v > info.data["high"]:
            raise ValueError("low must be <= high")
        return v


class CurrentPrice(BaseModel):
    """
    Current price information for a cryptocurrency.

    Includes price, 24h change, market cap, and volume.
    """

    symbol: str = Field(min_length=1, description="Trading symbol (e.g., BTC, ETH)")
    price: Decimal = Field(gt=Decimal("0"), description="Current price in USD")
    price_change_24h: Decimal = Field(description="24 hour price change")
    price_change_percent_24h: Decimal = Field(description="24 hour price change percentage")
    market_cap: Optional[Decimal] = Field(default=None, description="Market capitalization")
    volume_24h: Optional[Decimal] = Field(default=None, description="24 hour trading volume")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TechnicalIndicators(BaseModel):
    """
    Technical indicator values for a single time point.

    Contains all calculated indicators for signal generation.
    """

    # Moving averages
    sma_20: Optional[Decimal] = Field(default=None, description="20-period Simple Moving Average")
    sma_50: Optional[Decimal] = Field(default=None, description="50-period Simple Moving Average")
    sma_200: Optional[Decimal] = Field(default=None, description="200-period Simple Moving Average")
    ema_12: Optional[Decimal] = Field(default=None, description="12-period Exponential Moving Average")
    ema_26: Optional[Decimal] = Field(default=None, description="26-period Exponential Moving Average")
    ema_50: Optional[Decimal] = Field(default=None, description="50-period Exponential Moving Average")

    # Momentum indicators
    rsi_14: Optional[Decimal] = Field(default=None, description="14-period RSI")
    macd_line: Optional[Decimal] = Field(default=None, description="MACD line")
    macd_signal: Optional[Decimal] = Field(default=None, description="MACD signal line")
    macd_histogram: Optional[Decimal] = Field(default=None, description="MACD histogram")
    stochastic_k: Optional[Decimal] = Field(default=None, description="Stochastic %K")
    stochastic_d: Optional[Decimal] = Field(default=None, description="Stochastic %D")
    williams_r: Optional[Decimal] = Field(default=None, description="Williams %R")

    # Volatility indicators
    bollinger_upper: Optional[Decimal] = Field(default=None, description="Bollinger upper band")
    bollinger_middle: Optional[Decimal] = Field(default=None, description="Bollinger middle band")
    bollinger_lower: Optional[Decimal] = Field(default=None, description="Bollinger lower band")
    atr_14: Optional[Decimal] = Field(default=None, description="14-period Average True Range")

    # Volume indicators
    volume_sma_20: Optional[Decimal] = Field(default=None, description="20-period Volume SMA")
    obv: Optional[Decimal] = Field(default=None, description="On-Balance Volume")


class IndicatorSeries(BaseModel):
    """
    Time series of indicator values.

    Used for returning historical indicator calculations.
    """

    timestamps: List[datetime] = Field(default_factory=list, description="List of timestamps")
    values: List[Optional[float]] = Field(default_factory=list, description="Indicator values (None where unavailable)")
    name: str = Field(description="Indicator name")


class MarketDataResponse(BaseModel):
    """
    Complete market data response with prices and indicators.

    Used for charting and signal generation.
    """

    symbol: str = Field(description="Trading symbol")
    timeframe: str = Field(description="Time frame (1h, 4h, 1d, etc.)")
    prices: List[PriceData] = Field(default_factory=list, description="OHLCV price data")
    indicators: Dict[str, List[Optional[float]]] = Field(
        default_factory=dict,
        description="All calculated indicators as time series"
    )


class HistoricalPricesRequest(BaseModel):
    """
    Request parameters for historical price data.

    Allows filtering by date range, timeframe, and limit.
    """

    symbol: str = Field(min_length=1, description="Trading symbol")
    timeframe: str = Field(default="1h", description="Time frame")
    start: Optional[datetime] = Field(default=None, description="Start datetime")
    end: Optional[datetime] = Field(default=None, description="End datetime")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of candles")


class IndicatorsRequest(BaseModel):
    """
    Request parameters for calculating technical indicators.

    Specifies which indicators to calculate and parameters.
    """

    symbol: str = Field(min_length=1, description="Trading symbol")
    timeframe: str = Field(default="1h", description="Time frame")
    period: int = Field(default=100, ge=20, le=500, description="Number of periods to analyze")
    indicators: List[str] = Field(
        default_factory=list,
        description="List of indicators to calculate (empty = all)"
    )


class SeedPriceDataResponse(BaseModel):
    """
    Response from price data seeding operation.

    Reports how many records were inserted per symbol.
    """

    success: bool = Field(description="Whether seeding succeeded")
    message: str = Field(description="Human-readable status message")
    counts: Dict[str, int] = Field(default_factory=dict, description="Records inserted per symbol")


class PriceDataSummary(BaseModel):
    """
    Summary statistics for price data.

    Provides basic statistics for a price series.
    """

    symbol: str
    count: int = Field(description="Number of price records")
    start_date: Optional[datetime] = Field(default=None, description="Earliest timestamp")
    end_date: Optional[datetime] = Field(default=None, description="Latest timestamp")
    min_price: Decimal = Field(description="Lowest price in range")
    max_price: Decimal = Field(description="Highest price in range")
    avg_price: Decimal = Field(description="Average price in range")
    total_volume: Decimal = Field(description="Total volume in range")


class BatchMarketDataRequest(BaseModel):
    """
    Request parameters for batch market data retrieval.

    Allows fetching market data for multiple symbols in a single request.
    """

    symbols: List[str] = Field(min_length=1, max_length=50, description="List of trading symbols")
    include_indicators: bool = Field(default=False, description="Whether to include technical indicators")
    interval: str = Field(default="1h", description="Time frame (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of candles per symbol")


class SymbolMarketData(BaseModel):
    """
    Market data response for a single symbol in a batch request.

    Contains current price, historical prices, and optional indicators.
    """

    symbol: str = Field(description="Trading symbol")
    current_price: Optional[Decimal] = Field(default=None, description="Current price")
    prices: List[PriceData] = Field(default_factory=list, description="Historical OHLCV price data")
    indicators: Optional[Dict[str, List[Optional[float]]]] = Field(
        default=None,
        description="Technical indicators (if requested)"
    )
    error: Optional[str] = Field(default=None, description="Error message if data fetch failed")


class BatchMarketDataResponse(BaseModel):
    """
    Response from batch market data request.

    Contains market data for all requested symbols.
    """

    data: List[SymbolMarketData] = Field(description="Market data per symbol")
    interval: str = Field(description="Time frame used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    total_symbols: int = Field(description="Total number of symbols requested")
    successful: int = Field(description="Number of symbols with successful data fetch")
    failed: int = Field(description="Number of symbols with failed data fetch")
