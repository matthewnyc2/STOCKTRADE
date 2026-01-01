"""
Strategy-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class StrategyModel(BaseModel):
    """
    SQLAlchemy model for trading strategies.

    Represents a strategy that can be composed of multiple layers,
    use genetic algorithms, leverage ML models, or be created from templates.
    """

    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50))  # StrategyType enum
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    layers: Mapped[list] = mapped_column(JSON, default=list)  # List of layer IDs
    status: Mapped[str] = mapped_column(String(50), default="draft")  # Status enum
    logic_gate: Mapped[str] = mapped_column(String(50), default="none")  # LogicGate enum

    # Template metadata fields (for template strategies)
    # Game Mode metadata - fun, gamified display info
    game_mode_display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    game_mode_stars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    game_mode_flavor_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    game_mode_emoji: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Pro Mode metadata - technical, professional display info
    pro_mode_technical_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    pro_mode_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pro_mode_complexity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Backtest metrics (pre-computed for templates)
    backtest_total_return: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backtest_sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backtest_max_drawdown: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backtest_win_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backtest_profit_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    backtest_total_trades: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_template: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyLayerModel(BaseModel):
    """
    SQLAlchemy model for strategy layers.

    Represents a single layer within a composed strategy.
    A layer can be a signal source, filter, or transformation.
    """

    __tablename__ = "strategy_layers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(50), index=True)
    layer_order: Mapped[int] = mapped_column(default=0)
    weight: Mapped[float] = mapped_column(default=1.0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
