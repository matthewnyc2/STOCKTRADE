"""
Strategy API router.

Endpoints for strategy management, creation, and execution.
"""

from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from database.connection import get_db_context
from database.repositories import StrategyRepository, StrategyLayerRepository
from models import (
    Strategy,
    StrategyLayer,
    StrategyType,
    Status,
    LogicGate,
    GameModeMetadata,
    ProModeMetadata,
    BacktestMetrics,
    CreateFromTemplateRequest,
)


router = APIRouter(prefix="/strategies", tags=["strategies"])


class StrategyCreate(BaseModel):
    """Schema for creating a new strategy."""

    name: str = Field(..., min_length=3, max_length=100, description="Strategy name (3-100 characters)")
    description: str | None = Field(default=None, max_length=2000, description="Strategy description")
    type: StrategyType
    parameters: dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
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
    parameters: dict[str, Any] | None = Field(default=None, description="Strategy parameters")
    status: Status | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_whitespace(cls, v: str | None) -> str | None:
        """Validate strategy name is not just whitespace."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Strategy name cannot be empty or whitespace")
        return v.strip() if v else v


class LayerCreate(BaseModel):
    """Schema for creating a strategy layer."""

    layer_order: int
    weight: float
    config: dict[str, Any] = {}


def model_to_strategy(model) -> Strategy:
    """Convert database model to Pydantic model with template metadata."""
    strategy = Strategy(
        id=model.id,
        name=model.name,
        description=model.description,
        type=model.type,
        parameters=model.parameters,
        layers=model.layers,
        status=model.status,
        logic_gate=LogicGate(getattr(model, 'logic_gate', 'none')),
        is_template=getattr(model, 'is_template', False),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

    # Add Game Mode metadata if available
    if hasattr(model, 'game_mode_display_name') and model.game_mode_display_name:
        strategy.game_mode_metadata = GameModeMetadata(
            display_name=model.game_mode_display_name,
            stars=getattr(model, 'game_mode_stars', None),
            flavor_text=getattr(model, 'game_mode_flavor_text', None),
            emoji=getattr(model, 'game_mode_emoji', None),
        )

    # Add Pro Mode metadata if available
    if hasattr(model, 'pro_mode_technical_name') and model.pro_mode_technical_name:
        strategy.pro_mode_metadata = ProModeMetadata(
            technical_name=model.pro_mode_technical_name,
            category=getattr(model, 'pro_mode_category', None),
            complexity=getattr(model, 'pro_mode_complexity', None),
        )

    # Add backtest metrics if available
    if hasattr(model, 'backtest_total_return') and model.backtest_total_return is not None:
        strategy.backtest_metrics = BacktestMetrics(
            total_return=model.backtest_total_return,
            sharpe_ratio=getattr(model, 'backtest_sharpe_ratio', None),
            max_drawdown=getattr(model, 'backtest_max_drawdown', None),
            win_rate=getattr(model, 'backtest_win_rate', None),
            profit_factor=getattr(model, 'backtest_profit_factor', None),
            total_trades=getattr(model, 'backtest_total_trades', None),
        )

    return strategy


def model_to_layer(model) -> StrategyLayer:
    """Convert database model to Pydantic model."""
    return StrategyLayer(
        id=model.id,
        strategy_id=model.strategy_id,
        layer_order=model.layer_order,
        weight=model.weight,
        config=model.config,
    )


@router.get("/", response_model=list[Strategy])
async def list_strategies(
    strategy_type: StrategyType | None = None,
    status_filter: Status | None = None,
    is_template: bool | None = None,
    limit: int = 100,
) -> list[Strategy]:
    """
    List all strategies with optional filtering.

    Args:
        strategy_type: Filter by strategy type.
        status_filter: Filter by status.
        is_template: Filter by template flag.
        limit: Maximum number of results.

    Returns:
        List[Strategy]: List of strategies.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        if is_template is not None:
            # Filter by is_template flag
            strategies = repo.get_many(limit=limit)
            strategies = [s for s in strategies if getattr(s, 'is_template', False) == is_template]
        elif strategy_type:
            strategies = repo.get_by_type(strategy_type.value)
        elif status_filter:
            strategies = repo.get_by_status(status_filter.value)
        else:
            strategies = repo.get_all(limit=limit)

        return [model_to_strategy(s) for s in strategies]


@router.get("/templates", response_model=list[Strategy])
async def list_templates() -> list[Strategy]:
    """
    List all template strategies with full metadata.

    Returns:
        List[Strategy]: List of template strategies with Game Mode and Pro Mode metadata.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)
        # Get all strategies and filter by is_template=True
        all_strategies = repo.get_all(limit=1000)
        templates = [s for s in all_strategies if getattr(s, 'is_template', False)]
        return [model_to_strategy(s) for s in templates]


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str) -> Strategy:
    """
    Get a specific strategy by ID with full metadata.

    Args:
        strategy_id: The strategy ID.

    Returns:
        Strategy: The requested strategy with metadata.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategy = repo.get(strategy_id)

        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        return model_to_strategy(strategy)


@router.post("/from-template/{template_id}", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_from_template(
    template_id: str,
    request: CreateFromTemplateRequest,
) -> Strategy:
    """
    Create a new strategy from a template.

    Creates a copy of the template strategy with a custom name.
    Optionally allows overriding template parameters.

    Args:
        template_id: The template strategy ID.
        request: Request with custom name and optional parameters.

    Returns:
        Strategy: The created strategy.

    Raises:
        HTTPException: If template not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Get the template
        template = repo.get(template_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )

        # Verify it's a template
        if not getattr(template, 'is_template', False) and template.type != 'template':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy {template_id} is not a template"
            )

        # Merge parameters
        final_parameters = template.parameters.copy()
        if request.custom_parameters:
            final_parameters.update(request.custom_parameters)

        # Create new strategy
        new_strategy = repo.create(
            id=f"strat_{uuid4().hex[:12]}",
            name=request.name,
            description=template.description,
            type="composed",  # Created strategies are composed type
            parameters=final_parameters,
            layers=[],  # Will copy layers below
            status=Status.DRAFT.value,
            is_template=False,  # Not a template
        )

        # Copy layers from template
        template_layers = layer_repo.get_by_strategy(template_id)
        new_layer_ids = []
        for layer in template_layers:
            new_layer = layer_repo.create(
                id=f"layer_{uuid4().hex[:12]}",
                strategy_id=new_strategy.id,
                layer_order=layer.layer_order,
                weight=layer.weight,
                config=layer.config.copy(),
            )
            new_layer_ids.append(new_layer.id)

        # Update strategy with new layers
        repo.update(new_strategy.id, layers=new_layer_ids)

        return model_to_strategy(new_strategy)


@router.get("/{strategy_id}/layers", response_model=list[StrategyLayer])
async def get_strategy_layers(strategy_id: str) -> list[StrategyLayer]:
    """
    Get all layers for a strategy.

    Args:
        strategy_id: The strategy ID.

    Returns:
        List[StrategyLayer]: List of strategy layers.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategy = repo.get(strategy_id)

        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        layer_repo = StrategyLayerRepository(session)
        layers = layer_repo.get_by_strategy(strategy_id)
        return [model_to_layer(l) for l in layers]


@router.post("/", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy_data: StrategyCreate) -> Strategy:
    """
    Create a new strategy.

    Args:
        strategy_data: The strategy creation data.

    Returns:
        Strategy: The created strategy.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        # Check if strategy with same name exists
        existing = repo.get_by_name(strategy_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Strategy with name '{strategy_data.name}' already exists"
            )

        strategy = repo.create(
            id=f"strat_{uuid4().hex[:12]}",
            name=strategy_data.name,
            description=strategy_data.description,
            type=strategy_data.type.value,
            parameters=strategy_data.parameters,
            layers=strategy_data.layers,
            status=Status.DRAFT.value,
        )

        return model_to_strategy(strategy)


@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: str,
    strategy_data: StrategyUpdate,
) -> Strategy:
    """
    Update an existing strategy.

    Args:
        strategy_id: The strategy ID.
        strategy_data: The strategy update data.

    Returns:
        Strategy: The updated strategy.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        # Check if strategy exists
        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        # Build update dict
        update_data = {}
        if strategy_data.name is not None:
            update_data["name"] = strategy_data.name
        if strategy_data.description is not None:
            update_data["description"] = strategy_data.description
        if strategy_data.parameters is not None:
            update_data["parameters"] = strategy_data.parameters
        if strategy_data.status is not None:
            update_data["status"] = strategy_data.status.value

        updated = repo.update(strategy_id, **update_data)
        return model_to_strategy(updated)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(strategy_id: str) -> None:
    """
    Delete a strategy.

    Args:
        strategy_id: The strategy ID.

    Raises:
        HTTPException: If strategy not found or cannot be deleted.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        # Check if strategy exists
        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        # Prevent deletion of active strategies
        if strategy.status == Status.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active strategy. Deactivate it first."
            )

        # Delete layers first
        layer_repo = StrategyLayerRepository(session)
        layer_repo.delete_by_strategy(strategy_id)
        session.flush()  # Ensure layers are deleted before committing

        # Delete strategy
        repo.delete(strategy_id)


@router.post("/{strategy_id}/activate", response_model=Strategy)
async def activate_strategy(strategy_id: str) -> Strategy:
    """
    Activate a strategy.

    Args:
        strategy_id: The strategy ID.

    Returns:
        Strategy: The activated strategy.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, status=Status.ACTIVE.value)
        return model_to_strategy(updated)


@router.post("/{strategy_id}/deactivate", response_model=Strategy)
async def deactivate_strategy(strategy_id: str) -> Strategy:
    """
    Deactivate a strategy.

    Args:
        strategy_id: The strategy ID.

    Returns:
        Strategy: The deactivated strategy.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, status=Status.INACTIVE.value)
        return model_to_strategy(updated)


@router.post("/{strategy_id}/layers", response_model=StrategyLayer, status_code=status.HTTP_201_CREATED)
async def add_layer_to_strategy(
    strategy_id: str,
    layer_data: LayerCreate,
) -> StrategyLayer:
    """
    Add a layer to a strategy.

    Args:
        strategy_id: The strategy ID.
        layer_data: The layer configuration data.

    Returns:
        StrategyLayer: The created strategy layer.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)

        # Check if strategy exists
        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        layer_repo = StrategyLayerRepository(session)
        layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:12]}",
            strategy_id=strategy_id,
            layer_order=layer_data.layer_order,
            weight=layer_data.weight,
            config=layer_data.config,
        )

        # Add layer ID to strategy's layers list
        if layer.id not in strategy.layers:
            updated_layers = strategy.layers + [layer.id]
            strategy_repo.update(strategy_id, layers=updated_layers)

        return model_to_layer(layer)


@router.delete("/{strategy_id}/layers/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_layer_from_strategy(strategy_id: str, layer_id: str) -> None:
    """
    Remove a layer from a strategy.

    Args:
        strategy_id: The strategy ID.
        layer_id: The layer ID.

    Raises:
        HTTPException: If strategy or layer not found.
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Check if strategy exists
        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        # Check if layer exists
        layer = layer_repo.get(layer_id)
        if layer is None or layer.strategy_id != strategy_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer {layer_id} not found in strategy {strategy_id}"
            )

        # Remove layer ID from strategy's layers list
        updated_layers = [l for l in strategy.layers if l != layer_id]
        strategy_repo.update(strategy_id, layers=updated_layers)
        session.flush()  # Ensure strategy is updated before deleting layer

        # Delete the layer
        layer_repo.delete(layer_id)


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


@router.put("/{strategy_id}/logic-gate", response_model=Strategy)
async def set_strategy_logic_gate(
    strategy_id: str,
    request: LogicGateUpdate,
) -> Strategy:
    """
    Set the logic gate type for a strategy.

    The logic gate determines how multiple layer signals are combined.

    Args:
        strategy_id: The strategy ID.
        request: Request containing the logic gate type.

    Returns:
        Strategy: The updated strategy.

    Raises:
        HTTPException: If strategy not found.
    """
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, logic_gate=request.logic_gate.value)
        return model_to_strategy(updated)


@router.put("/{strategy_id}/layer-weights", response_model=Strategy)
async def update_layer_weights(
    strategy_id: str,
    request: LayerWeightsUpdate,
) -> Strategy:
    """
    Update the weights of layers in a strategy.

    Args:
        strategy_id: The strategy ID.
        request: Request containing layer_id to weight mappings.

    Returns:
        Strategy: The updated strategy.

    Raises:
        HTTPException: If strategy or any layer not found.
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        # Update each layer's weight
        for layer_id, weight in request.weights.items():
            layer = layer_repo.get(layer_id)
            if layer is None or layer.strategy_id != strategy_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Layer {layer_id} not found in strategy {strategy_id}"
                )

            # Update the layer weight - we need to modify the config or update the layer model
            # The StrategyLayerModel has a weight field, so we update it
            from database.models.strategy import StrategyLayerModel
            session.query(StrategyLayerModel).filter(
                StrategyLayerModel.id == layer_id
            ).update({"weight": weight})

        # Refresh and return the strategy
        session.refresh(strategy)
        return model_to_strategy(strategy)
