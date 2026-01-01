"""
Strategy-related Pydantic models.

Defines the core strategy and strategy layer models with their associated enums.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class StrategyType(str, Enum):
    """Enum for strategy types."""

    COMPOSED = "composed"
    GENETIC = "genetic"
    ML = "ml"
    TEMPLATE = "template"


class Status(str, Enum):
    """Enum for strategy status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class LogicGate(str, Enum):
    """Enum for strategy logic gates used to combine layer signals."""

    AND = "and"
    OR = "or"
    WEIGHTED = "weighted"
    NONE = "none"


class GameModeMetadata(BaseModel):
    """Game Mode metadata for template strategies - fun, gamified display info."""

    display_name: Optional[str] = Field(default=None, description="Fun display name for Game Mode")
    stars: Optional[int] = Field(default=None, ge=1, le=5, description="Star rating (1-5)")
    flavor_text: Optional[str] = Field(default=None, description="Fun flavor text describing the strategy")
    emoji: Optional[str] = Field(default=None, description="Emoji icon for the strategy")


class ProModeMetadata(BaseModel):
    """Pro Mode metadata for template strategies - technical, professional display info."""

    technical_name: Optional[str] = Field(default=None, description="Technical name for Pro Mode")
    category: Optional[str] = Field(
        default=None,
        description="Strategy category (e.g., 'Mean Reversion', 'Trend Following', 'Momentum')"
    )
    complexity: Optional[str] = Field(
        default=None,
        description="Complexity level (e.g., 'Basic', 'Intermediate', 'Advanced')"
    )


class BacktestMetrics(BaseModel):
    """Backtest performance metrics for template strategies."""

    total_return: Optional[float] = Field(default=None, description="Total return as decimal (e.g., 0.124 for 12.4%)")
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(default=None, description="Maximum drawdown as negative decimal")
    win_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Win rate as decimal (e.g., 0.58 for 58%)")
    profit_factor: Optional[float] = Field(default=None, description="Profit factor")
    total_trades: Optional[int] = Field(default=None, ge=0, description="Total number of trades")


class StrategyLayer(BaseModel):
    """
    Represents a single layer within a composed strategy.

    A layer can be a signal source, filter, or transformation
    with configurable weight in the final decision.
    """

    id: str = Field(default_factory=lambda: f"layer_{uuid4().hex[:8]}")
    strategy_id: str
    layer_order: int = Field(ge=0, description="Order of execution for this layer")
    weight: float = Field(ge=0.0, le=1.0, description="Weight of this layer in final signal")
    config: dict = Field(default_factory=dict, description="Layer-specific configuration")


class Strategy(BaseModel):
    """
    Represents a trading strategy.

    A strategy can be composed of multiple layers, use genetic algorithms,
    leverage ML models, or be created from templates.
    """

    id: str = Field(default_factory=lambda: f"strat_{uuid4().hex[:8]}")
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    type: StrategyType
    parameters: dict = Field(default_factory=dict, description="Strategy parameters")
    layers: list[str] = Field(
        default_factory=list, description="List of layer IDs in this strategy"
    )
    status: Status = Field(default=Status.DRAFT)
    logic_gate: LogicGate = Field(default=LogicGate.NONE, description="Logic gate for combining layer signals")

    # Template metadata fields
    game_mode_metadata: Optional[GameModeMetadata] = Field(default=None, description="Game Mode metadata for templates")
    pro_mode_metadata: Optional[ProModeMetadata] = Field(default=None, description="Pro Mode metadata for templates")
    backtest_metrics: Optional[BacktestMetrics] = Field(default=None, description="Backtest performance metrics for templates")
    is_template: bool = Field(default=False, description="Whether this is a template strategy")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Validate strategy name is not empty."""
        if not v or not v.strip():
            raise ValueError("Strategy name cannot be empty")
        return v.strip()

    @field_validator("layers")
    @classmethod
    def layers_must_be_unique(cls, v: list[str]) -> list[str]:
        """Validate layer IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Layer IDs must be unique")
        return v


class StrategyCreate(BaseModel):
    """Schema for creating a new strategy."""

    name: str = Field(..., min_length=3, max_length=100, description="Strategy name (3-100 characters)")
    description: str | None = Field(default=None, max_length=2000, description="Strategy description")
    type: StrategyType
    parameters: dict = Field(default_factory=dict, description="Strategy parameters")
    layers: list[str] = Field(default_factory=list, description="List of layer IDs")

    @field_validator("name")
    @classmethod
    def name_must_not_be_whitespace(cls, v: str) -> str:
        """Validate strategy name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Strategy name cannot be empty or whitespace")
        return v.strip()


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy."""

    name: str | None = Field(default=None, min_length=3, max_length=100, description="Strategy name (3-100 characters)")
    description: str | None = Field(default=None, max_length=2000, description="Strategy description")
    parameters: dict | None = Field(default=None, description="Strategy parameters")
    status: Status | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_whitespace(cls, v: str | None) -> str | None:
        """Validate strategy name is not just whitespace."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Strategy name cannot be empty or whitespace")
        return v.strip() if v else v


class CreateFromTemplateRequest(BaseModel):
    """Schema for creating a strategy from a template."""

    name: str = Field(..., description="Custom name for the new strategy")
    custom_parameters: Optional[dict] = Field(
        default=None,
        description="Optional custom parameters to override template defaults"
    )
