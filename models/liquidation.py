"""
Liquidation-related Pydantic models.

Defines liquidation events, cascade detection, and market pressure tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field


class LiquidationSide(str, Enum):
    """Enum for liquidation side (long/short)."""

    LONG = "long"
    SHORT = "short"


class CascadeSeverity(str, Enum):
    """Enum for cascade event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class Liquidation(BaseModel):
    """
    Represents a single liquidation event.

    Records large forced position closures from exchanges.
    """

    id: str = Field(default_factory=lambda: f"liq_{uuid4().hex[:12]}")
    exchange: str = Field(description="Exchange where liquidation occurred")
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    side: LiquidationSide = Field(description="Long or short position liquidated")
    amount_usd: Decimal = Field(gt=Decimal("0"), description="Liquidation amount in USD")
    price: Decimal = Field(gt=Decimal("0"), description="Price at liquidation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    blockchain_txid: Optional[str] = Field(default=None, description="Blockchain transaction ID if applicable")
    metadata: dict = Field(default_factory=dict)


class CascadeEvent(BaseModel):
    """
    Represents a detected cascade liquidation event.

    Cascade events occur when multiple liquidations happen in quick succession,
    potentially triggering further liquidations and market volatility.
    """

    id: str = Field(default_factory=lambda: f"casc_{uuid4().hex[:8]}")
    symbol: str = Field(description="Primary symbol affected")
    severity: CascadeSeverity = Field(description="Severity level of cascade")
    liquidation_count: int = Field(ge=1, description="Number of liquidations in cascade")
    total_amount_usd: Decimal = Field(ge=Decimal("0"), description="Total amount liquidated")
    start_time: datetime = Field(description="When cascade started")
    end_time: datetime = Field(description="When cascade ended")
    duration_seconds: int = Field(ge=0, description="Duration of cascade in seconds")
    affected_symbols: list[str] = Field(default_factory=list, description="Other symbols affected")
    long_percentage: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Percentage of long liquidations")
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Detection confidence")
    description: Optional[str] = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class LiquidationHeat(BaseModel):
    """
    Represents liquidation pressure/heat for a symbol.

    Heat indicates the likelihood of further liquidations based on
    recent liquidation activity and market conditions.
    """

    symbol: str = Field(description="Trading symbol")
    heat_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Heat score 0-1")
    long_heat: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Long liquidation pressure")
    short_heat: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Short liquidation pressure")
    total_liquidated_1h: Decimal = Field(ge=Decimal("0"), description="Total liquidated in last hour")
    total_liquidated_24h: Decimal = Field(ge=Decimal("0"), description="Total liquidated in last 24h")
    liquidation_count_1h: int = Field(ge=0, description="Number of liquidations in last hour")
    liquidation_count_24h: int = Field(ge=0, description="Number of liquidations in last 24h")
    trend: str = Field(description="Trend direction: increasing, decreasing, stable")
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class LiquidationStats(BaseModel):
    """
    Aggregated statistics for liquidations.
    """

    symbol: Optional[str] = Field(default=None, description="Symbol if filtered, otherwise all symbols")
    total_liquidated_usd: Decimal = Field(ge=Decimal("0"))
    long_liquidated_usd: Decimal = Field(ge=Decimal("0"))
    short_liquidated_usd: Decimal = Field(ge=Decimal("0"))
    liquidation_count: int = Field(ge=0)
    avg_liquidation_size: Decimal = Field(ge=Decimal("0"))
    largest_liquidation: Decimal = Field(ge=Decimal("0"))
    cascade_count: int = Field(ge=0)
    period_hours: int = Field(ge=0)
