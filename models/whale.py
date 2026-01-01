"""
Whale-related Pydantic models.

Defines whale wallet tracking, activity, and constellation detection.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field


class WhaleTier(str, Enum):
    """Enum for whale classification tiers."""

    MEGA = "mega"
    LARGE = "large"
    SMART_MONEY = "smart_money"


class PatternType(str, Enum):
    """Enum for whale behavior patterns."""

    ACCUMULATOR = "accumulator"
    SNIPER = "sniper"
    DISTRIBUTOR = "distributor"
    MANIPULATOR = "manipulator"


class WhaleAction(str, Enum):
    """Enum for whale activity actions."""

    BOUGHT = "bought"
    SOLD = "sold"
    TRANSFERRED = "transferred"


class WhaleConstellationType(str, Enum):
    """Enum for whale constellation types."""

    TEMPORAL = "temporal"
    WALLET_NETWORK = "wallet_network"
    CROSS_CHAIN = "cross_chain"
    SMART_MONEY = "smart_money"


class Whale(BaseModel):
    """
    Represents a whale wallet address being tracked.

    Contains classification, holdings, and behavior pattern data.
    """

    address: str = Field(min_length=1, description="Wallet address")
    label: Optional[str] = Field(default=None, description="Human-readable label")
    tier: WhaleTier
    holdings_usd: Decimal = Field(ge=Decimal("0"), description="Total holdings in USD")
    holdings_24h_change: Decimal = Field(description="24h holdings change percentage")
    historical_accuracy: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), le=Decimal("1")
    )
    pattern_type: PatternType
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    preferred_tokens: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class WhaleActivity(BaseModel):
    """
    Represents a single whale activity event.

    Records buys, sells, and transfers from tracked whale wallets.
    """

    id: str = Field(default_factory=lambda: f"act_{uuid4().hex[:12]}")
    whale_address: str
    symbol: str
    action: WhaleAction
    amount_usd: Decimal = Field(gt=Decimal("0"))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction_hash: Optional[str] = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class WhaleConstellation(BaseModel):
    """
    Represents a detected pattern across multiple whale wallets.

    Constellations indicate coordinated activity or smart money movements.
    """

    id: str = Field(default_factory=lambda: f"const_{uuid4().hex[:8]}")
    type: WhaleConstellationType
    symbol: str
    whale_addresses: list[str] = Field(min_length=2, description="Whale addresses in constellation")
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(default=None)
    metadata: dict = Field(default_factory=dict)
