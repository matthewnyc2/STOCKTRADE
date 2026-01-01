"""
Liquidation-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class LiquidationModel(BaseModel):
    """
    SQLAlchemy model for liquidation events.

    Records large forced position closures from exchanges.
    """

    __tablename__ = "liquidations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    exchange: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    side: Mapped[str] = mapped_column(String(20))  # LiquidationSide enum
    amount_usd: Mapped[float] = mapped_column(Numeric(precision=20, scale=2), index=True)
    price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    blockchain_txid: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)


class CascadeModel(BaseModel):
    """
    SQLAlchemy model for cascade liquidation events.

    Represents detected patterns of multiple liquidations in quick succession.
    """

    __tablename__ = "cascades"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))  # CascadeSeverity enum
    liquidation_count: Mapped[int]
    total_amount_usd: Mapped[float] = mapped_column(Numeric(precision=20, scale=2))
    start_time: Mapped[datetime] = mapped_column(index=True)
    end_time: Mapped[datetime]
    duration_seconds: Mapped[int]
    affected_symbols: Mapped[list] = mapped_column(JSON)
    long_percentage: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    confidence: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)
