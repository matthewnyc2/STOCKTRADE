"""
Strategy-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Text, Float, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel
from models.strategy import RiskLevel, StrategyType, Status, LogicGate


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

    # Enhanced fields for strategy management
    template_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("strategies.id"), nullable=True, index=True
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("strategies.id"), nullable=True, index=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list)  # JSON array of tags for categorization
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # RiskLevel enum
    performance_summary: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # JSON with latest backtest metrics

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

    is_template: Mapped[bool] = mapped_column(default=False, index=True)

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


class StrategyFavoriteModel(BaseModel):
    """
    SQLAlchemy model for user-favorited strategies.

    Represents a user's favorite strategies for quick access.
    """

    __tablename__ = "strategy_favorites"

    __table_args__ = (UniqueConstraint("user_id", "strategy_id", name="uq_user_strategy_favorite"),)

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(50), index=True, default="default"
    )  # For future auth
    strategy_id: Mapped[str] = mapped_column(String(50), ForeignKey("strategies.id"), index=True)
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # User's notes about the strategy
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class StrategyShareModel(BaseModel):
    """
    SQLAlchemy model for shared strategies.

    Represents sharing of strategies between users.
    """

    __tablename__ = "strategy_shares"

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", "strategy_id", name="uq_strategy_share"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    from_user_id: Mapped[str] = mapped_column(
        String(50), index=True, default="default"
    )  # For future auth
    to_user_id: Mapped[str] = mapped_column(
        String(50), index=True, default="default"
    )  # For future auth
    strategy_id: Mapped[str] = mapped_column(String(50), ForeignKey("strategies.id"), index=True)
    permissions: Mapped[str] = mapped_column(String(50), default="view")  # view, edit, clone
    message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Optional message from sender
    accepted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class StrategyVersionModel(BaseModel):
    """
    SQLAlchemy model for strategy version history.

    Tracks all changes made to strategies for rollback and audit purposes.
    """

    __tablename__ = "strategy_versions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(50), ForeignKey("strategies.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    layers: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    change_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Description of changes made
    created_by: Mapped[str] = mapped_column(
        String(50), default="system"
    )  # User who created this version
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
