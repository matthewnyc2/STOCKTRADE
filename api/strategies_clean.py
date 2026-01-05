"""
Strategy API router - Refactored.

Endpoints for strategy management, creation, and execution.
All business logic moved to services/strategy_manager.py.
All Pydantic models moved to models/strategy.py.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from database.connection import get_db_context
from database.repositories import (
    StrategyRepository,
    StrategyLayerRepository,
    StrategyFavoriteRepository,
)
from models import (
    Strategy,
    StrategyLayer,
    StrategyType,
    Status,
    LogicGate,
    RiskLevel,
    CreateFromTemplateRequest,
    StrategyCreate,
    StrategyUpdate,
    LayerCreate,
    LogicGateUpdate,
    LayerWeightsUpdate,
    StrategyUpdateEnhanced,
    StrategyVersion,
    StrategyCloneRequest,
    StrategyExportRequest,
    StrategyImportRequest,
)
from services.strategy_manager import (
    model_to_strategy,
    model_to_layer,
    create_from_template,
    update_layer_weights,
    get_strategy_manager,
)


router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("/", response_model=list[Strategy])
async def list_strategies(
    strategy_type: StrategyType | None = None,
    status_filter: Status | None = None,
    is_template: bool | None = None,
    limit: int = 100,
) -> list[Strategy]:
    """List all strategies with optional filtering."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        if is_template is not None:
            strategies = repo.get_many(limit=limit)
            strategies = [s for s in strategies if getattr(s, "is_template", False) == is_template]
        elif strategy_type:
            strategies = repo.get_by_type(strategy_type.value)
        elif status_filter:
            strategies = repo.get_by_status(status_filter.value)
        else:
            strategies = repo.get_all(limit=limit)

        return [model_to_strategy(s) for s in strategies]


@router.get("/templates", response_model=list[Strategy])
async def list_templates() -> list[Strategy]:
    """List all template strategies with full metadata."""
    with get_db_context() as session:
        repo = StrategyRepository(session)
        all_strategies = repo.get_all(limit=1000)
        templates = [s for s in all_strategies if getattr(s, "is_template", False)]
        return [model_to_strategy(s) for s in templates]


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str) -> Strategy:
    """Get a specific strategy by ID with full metadata."""
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategy = repo.get(strategy_id)

        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        return model_to_strategy(strategy)


@router.post(
    "/from-template/{template_id}", response_model=Strategy, status_code=status.HTTP_201_CREATED
)
async def create_from_template_endpoint(
    template_id: str,
    request: CreateFromTemplateRequest,
) -> Strategy:
    """Create a new strategy from a template."""
    try:
        return create_from_template(
            template_id, request.name, custom_parameters=request.custom_parameters
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{strategy_id}/layers", response_model=list[StrategyLayer])
async def get_strategy_layers(strategy_id: str) -> list[StrategyLayer]:
    """Get all layers for a strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategy = repo.get(strategy_id)

        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        layer_repo = StrategyLayerRepository(session)
        layers = layer_repo.get_by_strategy(strategy_id)
        return [model_to_layer(l) for l in layers]


@router.post("/", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy_data: StrategyCreate) -> Strategy:
    """Create a new strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        existing = repo.get_by_name(strategy_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Strategy with name '{strategy_data.name}' already exists",
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
    """Update an existing strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

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
    """Delete a strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        if strategy.status == Status.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active strategy. Deactivate it first.",
            )

        layer_repo = StrategyLayerRepository(session)
        layer_repo.delete_by_strategy(strategy_id)
        session.flush()

        repo.delete(strategy_id)


@router.post("/{strategy_id}/activate", response_model=Strategy)
async def activate_strategy(strategy_id: str) -> Strategy:
    """Activate a strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, status=Status.ACTIVE.value)
        return model_to_strategy(updated)


@router.post("/{strategy_id}/deactivate", response_model=Strategy)
async def deactivate_strategy(strategy_id: str) -> Strategy:
    """Deactivate a strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, status=Status.INACTIVE.value)
        return model_to_strategy(updated)


@router.post(
    "/{strategy_id}/layers", response_model=StrategyLayer, status_code=status.HTTP_201_CREATED
)
async def add_layer_to_strategy(
    strategy_id: str,
    layer_data: LayerCreate,
) -> StrategyLayer:
    """Add a layer to a strategy."""
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)

        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        layer_repo = StrategyLayerRepository(session)
        layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:12]}",
            strategy_id=strategy_id,
            layer_order=layer_data.layer_order,
            weight=layer_data.weight,
            config=layer_data.config,
        )

        if layer.id not in strategy.layers:
            updated_layers = strategy.layers + [layer.id]
            strategy_repo.update(strategy_id, layers=updated_layers)

        return model_to_layer(layer)


@router.delete("/{strategy_id}/layers/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_layer_from_strategy(strategy_id: str, layer_id: str) -> None:
    """Remove a layer from a strategy."""
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        layer = layer_repo.get(layer_id)
        if layer is None or layer.strategy_id != strategy_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer {layer_id} not found in strategy {strategy_id}",
            )

        updated_layers = [l for l in strategy.layers if l != layer_id]
        strategy_repo.update(strategy_id, layers=updated_layers)
        session.flush()

        layer_repo.delete(layer_id)


@router.put("/{strategy_id}/logic-gate", response_model=Strategy)
async def set_strategy_logic_gate(
    strategy_id: str,
    request: LogicGateUpdate,
) -> Strategy:
    """Set the logic gate type for a strategy."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        updated = repo.update(strategy_id, logic_gate=request.logic_gate.value)
        return model_to_strategy(updated)


@router.put("/{strategy_id}/layer-weights", response_model=Strategy)
async def update_layer_weights_endpoint(
    strategy_id: str,
    request: LayerWeightsUpdate,
) -> Strategy:
    """Update the weights of layers in a strategy."""
    try:
        return update_layer_weights(strategy_id, request.weights)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/clone", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def clone_strategy_endpoint(
    strategy_id: str,
    request: StrategyCloneRequest,
) -> Strategy:
    """Clone an existing strategy."""
    manager = get_strategy_manager()
    try:
        return manager.clone_strategy(
            strategy_id=strategy_id,
            new_name=request.name,
            custom_parameters=request.custom_parameters,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/favorite", response_model=dict)
async def add_favorite(strategy_id: str, user_id: str = "default") -> dict:
    """Add a strategy to user's favorites."""
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        fav_repo = StrategyFavoriteRepository(session)

        strategy = strategy_repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        fav_repo.add_favorite(user_id, strategy_id)

        return {"message": "Strategy added to favorites", "strategy_id": strategy_id}


@router.delete("/{strategy_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(strategy_id: str, user_id: str = "default") -> None:
    """Remove a strategy from user's favorites."""
    with get_db_context() as session:
        fav_repo = StrategyFavoriteRepository(session)

        removed = fav_repo.remove_favorite(user_id, strategy_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Favorite not found for strategy {strategy_id}",
            )


@router.get("/favorites/list", response_model=list[Strategy])
async def list_favorites(user_id: str = "default", limit: int = 50) -> list[Strategy]:
    """List user's favorite strategies."""
    with get_db_context() as session:
        fav_repo = StrategyFavoriteRepository(session)
        strategy_repo = StrategyRepository(session)

        favorites = fav_repo.get_user_favorites(user_id, limit=limit)

        strategies = []
        for fav in favorites:
            strategy = strategy_repo.get(fav.strategy_id)
            if strategy:
                strategies.append(model_to_strategy(strategy))

        return strategies


@router.get("/{strategy_id}/versions", response_model=list[StrategyVersion])
async def get_version_history(strategy_id: str) -> list[dict]:
    """Get version history for a strategy."""
    manager = get_strategy_manager()

    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

    return manager.get_version_history(strategy_id)


@router.post("/{strategy_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(
    strategy_id: str,
    change_description: str | None = None,
    created_by: str = "system",
) -> dict:
    """Create a version snapshot of a strategy."""
    manager = get_strategy_manager()

    try:
        version_id = manager.create_version_snapshot(
            strategy_id=strategy_id,
            change_description=change_description,
            created_by=created_by,
        )
        return {"message": "Version created", "version_id": version_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{strategy_id}/export")
async def export_strategy(
    strategy_id: str,
    request: StrategyExportRequest = StrategyExportRequest(),
) -> dict:
    """Export a strategy to JSON or YAML."""
    manager = get_strategy_manager()

    try:
        exported = manager.export_strategy(
            strategy_id=strategy_id,
            format=request.format,
            include_metadata=True,
        )
        return {
            "strategy_id": strategy_id,
            "format": request.format,
            "data": exported,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/import", response_model=Strategy, status_code=status.HTTP_201_CREATED)
async def import_strategy(request: StrategyImportRequest) -> Strategy:
    """Import a strategy from JSON or YAML data."""
    manager = get_strategy_manager()

    try:
        return manager.import_strategy(
            data=request.data,
            name=request.name,
            format=request.format,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search", response_model=list[Strategy])
async def search_strategies(
    query: str,
    tags: str | None = None,
    risk_level: RiskLevel | None = None,
    strategy_type: StrategyType | None = None,
    limit: int = 50,
) -> list[Strategy]:
    """Search strategies with multiple filters."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        tag_list = tags.split(",") if tags else None

        strategies = repo.search(
            query=query,
            limit=limit,
            tags=tag_list,
            risk_level=risk_level.value if risk_level else None,
            strategy_type=strategy_type.value if strategy_type else None,
        )

        return [model_to_strategy(s) for s in strategies]


@router.get("/by-tag/{tag}", response_model=list[Strategy])
async def get_strategies_by_tag(tag: str, limit: int = 50) -> list[Strategy]:
    """Get strategies by tag."""
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategies = repo.get_by_tag(tag)

        return [model_to_strategy(s) for s in strategies[:limit]]


@router.get("/by-risk/{risk_level}", response_model=list[Strategy])
async def get_strategies_by_risk(risk_level: RiskLevel, limit: int = 50) -> list[Strategy]:
    """Get strategies by risk level."""
    with get_db_context() as session:
        repo = StrategyRepository(session)
        strategies = repo.get_by_risk_level(risk_level.value)

        return [model_to_strategy(s) for s in strategies[:limit]]


@router.get("/{strategy_id}/performance", response_model=dict)
async def get_strategy_performance(strategy_id: str) -> dict:
    """Get real-time performance metrics for a strategy."""
    manager = get_strategy_manager()
    return manager.calculate_performance(strategy_id)


@router.get("/recommendations", response_model=list[dict])
async def get_strategy_recommendations(
    risk_preference: RiskLevel | None = None,
    preferred_tags: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Get strategy recommendations based on preferences."""
    manager = get_strategy_manager()

    tag_list = preferred_tags.split(",") if preferred_tags else None

    return manager.get_strategy_recommendations(
        risk_preference=risk_preference,
        preferred_tags=tag_list,
        limit=limit,
    )


@router.patch("/{strategy_id}", response_model=Strategy)
async def update_strategy_enhanced(
    strategy_id: str,
    strategy_data: StrategyUpdateEnhanced,
) -> Strategy:
    """Update a strategy with enhanced fields."""
    with get_db_context() as session:
        repo = StrategyRepository(session)

        strategy = repo.get(strategy_id)
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy {strategy_id} not found"
            )

        update_data = {}
        if strategy_data.name is not None:
            update_data["name"] = strategy_data.name
        if strategy_data.description is not None:
            update_data["description"] = strategy_data.description
        if strategy_data.parameters is not None:
            update_data["parameters"] = strategy_data.parameters
        if strategy_data.status is not None:
            update_data["status"] = strategy_data.status.value
        if strategy_data.tags is not None:
            update_data["tags"] = strategy_data.tags
        if strategy_data.risk_level is not None:
            update_data["risk_level"] = strategy_data.risk_level.value
        if strategy_data.performance_summary is not None:
            update_data["performance_summary"] = strategy_data.performance_summary

        updated = repo.update(strategy_id, **update_data)
        return model_to_strategy(updated)
