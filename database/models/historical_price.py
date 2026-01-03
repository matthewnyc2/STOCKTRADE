"""
Historical price data SQLAlchemy ORM model.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Numeric, PrimaryKeyConstraint, Index
from database.models import BaseModel

class HistoricalPriceModel(BaseModel):
    """
    SQLAlchemy model for historical price data.
    """

    __tablename__ = "historical_prices"

    symbol: str = Column(String(20), nullable=False)
    timeframe: str = Column(String(10), nullable=False)
    timestamp: datetime = Column(DateTime, nullable=False)
    open: Decimal = Column(Numeric(20, 8), nullable=False)
    high: Decimal = Column(Numeric(20, 8), nullable=False)
    low: Decimal = Column(Numeric(20, 8), nullable=False)
    close: Decimal = Column(Numeric(20, 8), nullable=False)
    volume: Decimal = Column(Numeric(20, 8), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'timeframe', 'timestamp'),
    )
