"""
Backtest-related Pydantic models.

Defines backtest results, equity curves, and individual trades.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EquityPoint(BaseModel):
    """
    Represents a single point on the equity curve.

    Records portfolio value and drawdown at a specific timestamp.
    """

    timestamp: datetime
    equity: Decimal = Field(ge=Decimal("0"), description="Portfolio equity value")
    drawdown: Decimal = Field(le=Decimal("0"), description="Drawdown from peak (negative or zero)")


class Trade(BaseModel):
    """
    Represents a single completed trade from backtesting.

    Records entry, exit, P&L, and exit reason for analysis.
    """

    id: str = Field(default_factory=lambda: f"trade_{uuid4().hex[:12]}")
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: Decimal = Field(gt=Decimal("0"))
    exit_price: Decimal = Field(gt=Decimal("0"))
    quantity: Decimal = Field(gt=Decimal("0"))
    side: str = Field(pattern="^(LONG|SHORT)$", description="Trade direction: LONG or SHORT")
    pnl: Decimal = Field(description="Profit/loss in base currency")
    pnl_percent: Decimal = Field(description="Profit/loss as percentage")
    exit_reason: Optional[str] = Field(
        default=None,
        description="Reason for exit (STOP_LOSS, TAKE_PROFIT, SIGNAL, etc.)",
    )


class BacktestResult(BaseModel):
    """
    Represents the results of a strategy backtest.

    Contains performance metrics, equity curve, and individual trades.
    """

    id: str = Field(default_factory=lambda: f"bt_{uuid4().hex[:8]}")
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Field(gt=Decimal("0"))
    final_capital: Decimal = Field(ge=Decimal("0"))
    total_return: Decimal = Field(description="Total return as decimal (e.g., 0.25 for 25%)")
    sharpe_ratio: Optional[Decimal] = Field(default=None)
    sortino_ratio: Optional[Decimal] = Field(default=None)
    max_drawdown: Decimal = Field(le=Decimal("0"), description="Maximum drawdown (negative)")
    win_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    profit_factor: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    total_trades: int = Field(ge=0)
    equity_curve: list[EquityPoint] = Field(default_factory=list)
    trades: list[Trade] = Field(default_factory=list)
