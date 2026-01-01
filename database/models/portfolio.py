"""
Portfolio-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Numeric, Float
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class PortfolioModel(BaseModel):
    """
    SQLAlchemy model for portfolio state.

    Represents the current portfolio state with total equity, P&L, and metrics.
    Uses a single row with id='current' for the active portfolio.
    """

    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="current")
    total_equity: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    starting_balance: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    total_pnl: Mapped[float] = mapped_column(Numeric(precision=20, scale=8), default=0)
    total_pnl_percent: Mapped[float] = mapped_column(Numeric(precision=10, scale=4), default=0)
    open_pnl: Mapped[float] = mapped_column(Numeric(precision=20, scale=8), default=0)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    max_drawdown: Mapped[float] = mapped_column(Numeric(precision=10, scale=4), default=0)
    win_rate: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    profit_factor: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class PositionModel(BaseModel):
    """
    SQLAlchemy model for open positions.

    Represents an open position in the portfolio.
    """

    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(String(50), default="current", index=True)
    symbol: Mapped[str] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(10))  # LONG or SHORT
    quantity: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    entry_price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    current_price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    unrealized_pnl_percent: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))
    stop_loss: Mapped[Optional[float]] = mapped_column(Numeric(precision=20, scale=8), nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Numeric(precision=20, scale=8), nullable=True)
    entry_timestamp: Mapped[datetime] = mapped_column()
    exit_timestamp: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Numeric(precision=20, scale=8), nullable=True)
    realized_pnl: Mapped[Optional[float]] = mapped_column(Numeric(precision=20, scale=8), nullable=True)
    open: Mapped[bool] = mapped_column(default=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
