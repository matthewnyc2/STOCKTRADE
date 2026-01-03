"""
Pydantic models for the Trader Tracking System.

Defines the data structures for traders, their activities, and profiles,
ensuring type safety and validation for all trader-related data.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

class TraderRiskLevel(str, Enum):
    """Enum for trader risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TradingStyle(str, Enum):
    """Enum for trader trading styles."""
    DAY_TRADER = "DAY_TRADER"
    SWING_TRADER = "SWING_TRADER"
    SCALPER = "SCALPER"
    POSITION_TRADER = "POSITION_TRADER"

class TraderAction(str, Enum):
    """Enum for trader actions."""
    BOUGHT = "BOUGHT"
    SOLD = "SOLD"
    OPENED_POSITION = "OPENED_POSITION"
    CLOSED_POSITION = "CLOSED_POSITION"

class Trader(BaseModel):
    """Represents a tracked trader."""
    id: str = Field(..., description="Unique trader identifier")
    username: str = Field(..., description="Trader's username on the exchange")
    exchange: str = Field(..., description="Exchange where the trader is active")
    rank: int | None = Field(None, description="Trader's rank on the exchange leaderboard")
    pnl_24h: Decimal | None = Field(None, description="Trader's 24-hour profit and loss in USD")
    win_rate: float | None = Field(None, description="Trader's overall win rate")
    last_activity: datetime = Field(..., description="Timestamp of the trader's last activity")
    followers: int | None = Field(None, description="Number of followers on the exchange")

class TraderActivity(BaseModel):
    """Represents a single trading activity of a trader."""
    id: str = Field(..., description="Unique activity identifier")
    trader_id: str = Field(..., description="ID of the trader who performed the activity")
    symbol: str = Field(..., description="The trading symbol (e.g., BTC/USD)")
    action: TraderAction = Field(..., description="The trading action performed")
    amount_usd: Decimal = Field(..., description="The value of the transaction in USD")
    timestamp: datetime = Field(..., description="Timestamp when the activity occurred")
    pnl: Decimal | None = Field(None, description="Profit or loss from this activity, if applicable")
    leverage: float | None = Field(None, description="Leverage used in the trade")

class TraderProfile(BaseModel):
    """Represents the trading profile and style of a trader."""
    trader_id: str = Field(..., description="ID of the trader")
    risk_level: TraderRiskLevel = Field(..., description="Calculated risk level of the trader")
    preferred_assets: list[str] = Field(..., description="List of assets the trader frequently trades")
    trading_style: TradingStyle = Field(..., description="Dominant trading style of the trader")
    avg_holding_period_seconds: int | None = Field(None, description="Average time the trader holds a position")
    preferred_exchange: str | None = Field(None, description="The trader's primary exchange")
