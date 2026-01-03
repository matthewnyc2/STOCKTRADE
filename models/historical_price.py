"""
Historical Price Pydantic Model.

Defines the data structure for a single historical price record (OHLCV).
This model is used for storing and retrieving historical market data from the database.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class HistoricalPrice(BaseModel):
    """
    Represents a single historical OHLCV candle.

    This model is used for database storage and retrieval of historical price data.
    """

    symbol: str = Field(min_length=1, description="Trading symbol (e.g., BTC/USDT)")
    timeframe: str = Field(min_length=1, description="Timeframe of the candle (e.g., 1h, 4h, 1d)")
    timestamp: datetime
    open: Decimal = Field(gt=Decimal("0"), description="Opening price")
    high: Decimal = Field(gt=Decimal("0"), description="Highest price")
    low: Decimal = Field(gt=Decimal("0"), description="Lowest price")
    close: Decimal = Field(gt=Decimal("0"), description="Closing price")
    volume: Decimal = Field(ge=Decimal("0"), description="Trading volume")

    class Config:
        """Pydantic model configuration."""
        orm_mode = True  # Allows mapping to SQLAlchemy models
        from_attributes = True

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
