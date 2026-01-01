"""
Whale-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class WhaleModel(BaseModel):
    """
    SQLAlchemy model for whale wallet tracking.

    Represents a whale wallet address being tracked.
    """

    __tablename__ = "whales"

    address: Mapped[str] = mapped_column(String(100), primary_key=True)
    label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tier: Mapped[str] = mapped_column(String(50))  # WhaleTier enum
    holdings_usd: Mapped[float] = mapped_column(Numeric(precision=20, scale=2))
    holdings_24h_change: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))
    historical_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    pattern_type: Mapped[str] = mapped_column(String(50))  # PatternType enum
    last_activity: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    preferred_tokens: Mapped[list] = mapped_column(JSON, default=list)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class WhaleActivityModel(BaseModel):
    """
    SQLAlchemy model for whale activity events.

    Records buys, sells, and transfers from tracked whale wallets.
    """

    __tablename__ = "whale_activities"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    whale_address: Mapped[str] = mapped_column(String(100), index=True)
    symbol: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))  # WhaleAction enum
    amount_usd: Mapped[float] = mapped_column(Numeric(precision=20, scale=2))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class WhaleConstellationModel(BaseModel):
    """
    SQLAlchemy model for whale constellations.

    Represents detected patterns across multiple whale wallets.
    """

    __tablename__ = "whale_constellations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    type: Mapped[str] = mapped_column(String(50))  # WhaleConstellationType enum
    symbol: Mapped[str] = mapped_column(String(50))
    whale_addresses: Mapped[list] = mapped_column(JSON)  # List of addresses
    confidence: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
