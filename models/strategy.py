"""
Strategy-related Pydantic models.

Defines the core strategy and strategy layer models with their associated enums.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict, ConfigDict


class StrategyType(str, Enum):
    """Enum for strategy types."""

    COMPOSED = "composed"
    GENETIC = "genetic"
    ML = "ml"
    TEMPLATE = "template"


class RiskLevel(str, Enum):
    """Enum for risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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
    flavor_text: Optional[str] = Field(
        default=None, description="Fun flavor text describing the strategy"
    )
    emoji: Optional[str] = Field(default=None, description="Emoji icon for the strategy")


class ProModeMetadata(BaseModel):
    """Pro Mode metadata for template strategies - technical, professional display info."""

    technical_name: Optional[str] = Field(default=None, description="Technical name for Pro Mode")
    category: Optional[str] = Field(
        default=None,
        description="Strategy category (e.g., 'Mean Reversion', 'Trend Following', 'Momentum')",
    )
    complexity: Optional[str] = Field(
        default=None, description="Complexity level (e.g., 'Basic', 'Intermediate', 'Advanced')"
    )

    model_config = ConfigDict(from_attributes=True)
    complexity: Optional[str] = Field(
        default=None, description="Complexity level (e.g., 'Basic', 'Intermediate', 'Advanced')"
    )


class BacktestMetrics(BaseModel):
    """Backtest performance metrics for template strategies."""

    total_return: Optional[float] = Field(
        default=None, description="Total return as decimal (e.g., 0.124 for 12.4%)"
    )
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(
        default=None, description="Maximum drawdown as negative decimal"
    )
    win_rate: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Win rate as decimal (e.g., 0.58 for 58%)"
    )
    profit_factor: Optional[float] = Field(default=None, description="Profit factor")
    total_trades: Optional[int] = Field(default=None, ge=0, description="Total number of trades")

    model_config = ConfigDict(from_attributes=True)


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
    logic_gate: LogicGate = Field(
        default=LogicGate.NONE, description="Logic gate for combining layer signals"
    )

    # Enhanced fields for strategy management
    template_id: Optional[str] = Field(
        default=None, description="ID of template this strategy was created from"
    )
    parent_id: Optional[str] = Field(default=None, description="ID of parent strategy if cloned")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    risk_level: Optional[RiskLevel] = Field(
        default=None, description="Risk level (LOW/MEDIUM/HIGH)"
    )
    performance_summary: Optional[dict] = Field(
        default=None, description="Latest backtest performance summary"
    )

    # Template metadata fields
    game_mode_metadata: Optional[GameModeMetadata] = Field(
        default=None, description="Game Mode metadata for templates"
    )
    pro_mode_metadata: Optional[ProModeMetadata] = Field(
        default=None, description="Pro Mode metadata for templates"
    )
    backtest_metrics: Optional[BacktestMetrics] = Field(
        default=None, description="Backtest performance metrics for templates"
    )
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

    name: str = Field(
        ..., min_length=3, max_length=100, description="Strategy name (3-100 characters)"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Strategy description"
    )
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

    name: str | None = Field(
        default=None, min_length=3, max_length=100, description="Strategy name (3-100 characters)"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Strategy description"
    )
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
        default=None, description="Optional custom parameters to override template defaults"
    )


class StrategyFavorite(BaseModel):
    """Represents a user's favorited strategy."""

    id: str
    user_id: str = Field(default="default")
    strategy_id: str
    notes: Optional[str] = None
    created_at: datetime


class StrategyShare(BaseModel):
    """Represents a shared strategy between users."""

    id: str
    from_user_id: str = Field(default="default")
    to_user_id: str = Field(default="default")
    strategy_id: str
    permissions: str = Field(default="view")  # view, edit, clone
    message: Optional[str] = None
    accepted: bool = Field(default=False)
    created_at: datetime
    accepted_at: Optional[datetime] = None


class StrategyVersion(BaseModel):
    """Represents a version of a strategy."""

    id: str
    strategy_id: str
    version_number: int
    name: str
    description: Optional[str] = None
    type: str
    parameters: dict
    layers: list[str]
    tags: list[str]
    risk_level: Optional[str] = None
    change_description: Optional[str] = None
    created_by: str = Field(default="system")
    created_at: datetime


class StrategyCloneRequest(BaseModel):
    """Schema for cloning a strategy."""

    name: str = Field(..., min_length=3, max_length=100, description="Name for the cloned strategy")
    custom_parameters: Optional[dict] = Field(
        default=None, description="Optional custom parameters"
    )


class StrategyExportRequest(BaseModel):
    """Schema for exporting a strategy."""

    format: str = Field(default="json", description="Export format (json or yaml)")


class StrategyImportRequest(BaseModel):
    """Schema for importing a strategy."""

    name: str = Field(
        ..., min_length=3, max_length=100, description="Name for the imported strategy"
    )
    data: dict = Field(..., description="Strategy data to import")
    format: str = Field(default="json", description="Import format (json or yaml)")


class StrategySearchRequest(BaseModel):
    """Schema for searching strategies."""

    query: str = Field(..., min_length=2, description="Search query")
    tags: Optional[list[str]] = Field(default=None, description="Filter by tags")
    risk_level: Optional[RiskLevel] = Field(default=None, description="Filter by risk level")
    strategy_type: Optional[StrategyType] = Field(
        default=None, description="Filter by strategy type"
    )
    limit: int = Field(default=50, ge=1, le=100, description="Maximum results")


class LayerCreate(BaseModel):
    """Schema for creating a strategy layer."""

    layer_order: int
    weight: float
    config: dict = Field(default_factory=dict)


class LogicGateUpdate(BaseModel):
    """Schema for updating a strategy's logic gate."""

    logic_gate: LogicGate


class LayerWeightsUpdate(BaseModel):
    """Schema for updating layer weights."""

    weights: dict[str, float] = Field(..., description="Mapping of layer_id to weight (0.0-1.0)")

    @field_validator("weights")
    @classmethod
    def weights_must_be_valid(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate weights are in valid range."""
        for layer_id, weight in v.items():
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"Weight for layer {layer_id} must be between 0.0 and 1.0")
        return v


class StrategyUpdateEnhanced(BaseModel):
    """Enhanced schema for updating a strategy with new fields."""

    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    parameters: dict | None = Field(default=None)
    status: Status | None = None
    tags: list[str] | None = Field(default=None)
    risk_level: RiskLevel | None = None
    performance_summary: dict | None = Field(default=None)
