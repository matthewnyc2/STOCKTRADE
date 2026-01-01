"""
Portfolio-related Pydantic models.

Defines portfolio state, positions, and performance metrics.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PortfolioMetrics(BaseModel):
    """
    Portfolio performance metrics.

    Contains risk-adjusted return metrics and trading statistics.
    """

    sharpe_ratio: Optional[Decimal] = Field(default=None)
    sortino_ratio: Optional[Decimal] = Field(default=None)
    max_drawdown: Decimal = Field(le=Decimal("0"), default=Decimal("0"))
    win_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    profit_factor: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class Position(BaseModel):
    """
    Represents an open position in the portfolio.

    Tracks entry details, current value, and unrealized P&L.
    """

    id: str = Field(default_factory=lambda: f"pos_{uuid4().hex[:12]}")
    symbol: str
    side: str = Field(pattern="^(LONG|SHORT)$")
    quantity: Decimal = Field(gt=Decimal("0"))
    entry_price: Decimal = Field(gt=Decimal("0"))
    current_price: Decimal = Field(gt=Decimal("0"))
    unrealized_pnl: Decimal = Field(description="Unrealized profit/loss")
    unrealized_pnl_percent: Decimal = Field(description="Unrealized P&L as percentage")
    stop_loss: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    take_profit: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    entry_timestamp: datetime
    metadata: dict = Field(default_factory=dict)


class Portfolio(BaseModel):
    """
    Represents the current portfolio state.

    Contains total equity, P&L, open positions, and performance metrics.
    """

    total_equity: Decimal = Field(ge=Decimal("0"))
    starting_balance: Decimal = Field(gt=Decimal("0"))
    total_pnl: Decimal = Field(description="Total realized profit/loss")
    total_pnl_percent: Decimal = Field(description="Total P&L as percentage")
    open_pnl: Decimal = Field(default=Decimal("0"), description="Total unrealized P&L")
    positions: list[Position] = Field(default_factory=list)
    metrics: PortfolioMetrics
    last_updated: datetime = Field(default_factory=datetime.utcnow)
