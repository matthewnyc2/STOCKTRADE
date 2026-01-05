"""
Backtest-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import JSON, String, Numeric, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class BacktestResultModel(BaseModel):
    """
    SQLAlchemy model for backtest results.

    Represents the results of a strategy backtest with performance metrics.
    """

    __tablename__ = "backtest_results"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(50), index=True)
    start_date: Mapped[datetime] = mapped_column()
    end_date: Mapped[datetime] = mapped_column()
    initial_capital: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    final_capital: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    total_return: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    max_drawdown: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))
    win_rate: Mapped[float] = mapped_column(Numeric(precision=5, scale=4))
    profit_factor: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer)
    parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class EquityPointModel(BaseModel):
    """
    SQLAlchemy model for equity curve points.

    Represents a single point on the equity curve during backtesting.
    """

    __tablename__ = "equity_points"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    backtest_id: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column()
    equity: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    drawdown: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))


class BacktestTradeModel(BaseModel):
    """
    SQLAlchemy model for individual backtest trades.

    Represents a single completed trade from backtesting.
    """

    __tablename__ = "backtest_trades"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(50))
    entry_date: Mapped[datetime] = mapped_column()
    exit_date: Mapped[datetime] = mapped_column()
    entry_price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    exit_price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    quantity: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    side: Mapped[str] = mapped_column(String(10))  # LONG or SHORT
    pnl: Mapped[float] = mapped_column(Numeric(precision=20, scale=8))
    pnl_percent: Mapped[float] = mapped_column(Numeric(precision=10, scale=4))
    exit_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    backtest_id: Mapped[str] = mapped_column(String(50), index=True)
