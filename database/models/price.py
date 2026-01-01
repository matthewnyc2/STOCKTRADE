"""
Price data SQLAlchemy ORM model.

Stores historical OHLCV (Open, High, Low, Close, Volume) price data
for cryptocurrencies used in backtesting and technical analysis.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Numeric, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel
from decimal import Decimal


class PriceModel(BaseModel):
    """
    SQLAlchemy model for historical price data.

    Stores OHLCV candles for cryptocurrency trading pairs.
    Used for technical analysis, backtesting, and signal generation.
    """

    __tablename__ = "prices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

    # OHLCV data
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 8))

    # Optional metadata
    timeframe: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # API source

    __table_args__ = (
        Index('idx_prices_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_prices_timestamp', 'timestamp'),
    )
