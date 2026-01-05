"""
Strategy Templates API endpoints.

Provides endpoints for browsing, retrieving, and creating strategies from templates.
Templates are pre-configured strategy definitions that users can customize.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from models import Strategy, StrategyType, Status
from database.connection import get_db_session
from database.repositories import StrategyRepository, StrategyLayerRepository
from services.template_loader import (
    load_templates,
    get_template,
    get_templates_by_category,
    get_templates_by_difficulty,
    get_template_categories,
    get_template_difficulties,
    search_templates,
    get_template_summary,
    get_cached_templates,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy-templates", tags=["templates"])


# ============================================================================
# Response Models
# ============================================================================

class LayerInfo(BaseModel):
    """Template layer information."""
    id: str
    layer_order: int
    weight: float
    config: dict[str, Any]


class GameModeMetadata(BaseModel):
    """Game Mode metadata."""
    display_name: Optional[str] = None
    stars: Optional[int] = None
    flavor_text: Optional[str] = None
    emoji: Optional[str] = None


class ProModeMetadata(BaseModel):
    """Pro Mode metadata."""
    technical_name: Optional[str] = None
    category: Optional[str] = None
    complexity: Optional[str] = None


class BacktestMetrics(BaseModel):
    """Backtest performance metrics."""
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_trades: Optional[int] = None


class TemplateResponse(BaseModel):
    """Strategy template response."""
    id: str
    name: str
    category: str
    description: str
    difficulty: str
    parameters: dict[str, Any]
    layers: list[LayerInfo]
    default_config: dict[str, Any]
    game_mode_metadata: Optional[GameModeMetadata] = None
    pro_mode_metadata: Optional[ProModeMetadata] = None
    backtest_metrics: Optional[BacktestMetrics] = None


class TemplateListResponse(BaseModel):
    """Response for template list endpoint."""
    templates: list[TemplateResponse]
    total: int
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class CategoriesResponse(BaseModel):
    """Response for categories endpoint."""
    categories: list[str]
    total: int


class DifficultiesResponse(BaseModel):
    """Response for difficulties endpoint."""
    difficulties: list[str]
    total: int


class SummaryResponse(BaseModel):
    """Response for summary endpoint."""
    total_templates: int
    categories: dict[str, int]
    difficulties: dict[str, int]


class CreateFromTemplateRequest(BaseModel):
    """Request to create a strategy from a template."""
    template_id: str = Field(..., description="ID of the template to use")
    name: str = Field(..., min_length=3, max_length=100, description="Custom name for the new strategy")
    symbol: str = Field(default="BTC/USDT", description="Trading symbol")
    custom_parameters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional custom parameters to override template defaults"
    )


class StrategyCreatedResponse(BaseModel):
    """Response after creating a strategy from a template."""
    strategy_id: str
    name: str
    type: str
    status: str
    template_id: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "",
    response_model=TemplateListResponse,
    summary="List all strategy templates",
    description="Get all available strategy templates with optional filtering"
)
def list_templates(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None
) -> TemplateListResponse:
    """
    List all available strategy templates.

    Query Parameters:
        category: Filter by template category (e.g., "trend_following", "mean_reversion")
        difficulty: Filter by difficulty level ("beginner", "intermediate", "advanced")
        search: Search in name and description

    Returns:
        List of matching templates
    """
    try:
        templates = get_cached_templates()

        # Apply filters
        filtered_templates = list(templates.values())

        if category:
            filtered_templates = get_templates_by_category(category, templates)

        if difficulty:
            filtered_templates = get_templates_by_difficulty(difficulty, templates)

        if search:
            filtered_templates = search_templates(search, templates)

        # Build response
        template_responses = [
            TemplateResponse(**template) for template in filtered_templates
        ]

        filters = {}
        if category:
            filters["category"] = category
        if difficulty:
            filters["difficulty"] = difficulty
        if search:
            filters["search"] = search

        return TemplateListResponse(
            templates=template_responses,
            total=len(template_responses),
            filters_applied=filters
        )

    except FileNotFoundError as e:
        logger.error(f"Template file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template configuration file not found"
        )
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading templates: {str(e)}"
        )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get a specific template",
    description="Get detailed information about a specific strategy template"
)
def get_template_endpoint(template_id: str) -> TemplateResponse:
    """
    Get a specific strategy template by ID.

    Path Parameters:
        template_id: ID of the template to retrieve

    Returns:
        Template details

    Raises:
        404: If template not found
    """
    try:
        templates = get_cached_templates()
        template = get_template(template_id, templates)

        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_id}' not found"
            )

        return TemplateResponse(**template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading template: {str(e)}"
        )


@router.get(
    "/categories/list",
    response_model=CategoriesResponse,
    summary="Get template categories",
    description="Get list of all available template categories"
)
def get_categories_endpoint() -> CategoriesResponse:
    """
    Get all available template categories.

    Returns:
        List of category names
    """
    try:
        categories = get_template_categories()
        return CategoriesResponse(
            categories=categories,
            total=len(categories)
        )
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading categories: {str(e)}"
        )


@router.get(
    "/difficulties/list",
    response_model=DifficultiesResponse,
    summary="Get template difficulties",
    description="Get list of all available difficulty levels"
)
def get_difficulties_endpoint() -> DifficultiesResponse:
    """
    Get all available difficulty levels.

    Returns:
        List of difficulty level names
    """
    try:
        difficulties = get_template_difficulties()
        return DifficultiesResponse(
            difficulties=difficulties,
            total=len(difficulties)
        )
    except Exception as e:
        logger.error(f"Error getting difficulties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading difficulties: {str(e)}"
        )


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Get template summary",
    description="Get summary statistics about available templates"
)
def get_summary_endpoint() -> SummaryResponse:
    """
    Get summary statistics about templates.

    Returns:
        Template count by category and difficulty
    """
    try:
        summary = get_template_summary()
        return SummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading summary: {str(e)}"
        )


@router.post(
    "/create",
    response_model=StrategyCreatedResponse,
    summary="Create strategy from template",
    description="Create a new strategy based on a template"
)
def create_from_template(request: CreateFromTemplateRequest) -> StrategyCreatedResponse:
    """
    Create a new strategy from a template.

    Request Body:
        template_id: ID of the template to use
        name: Custom name for the new strategy
        symbol: Trading symbol (default: BTC/USDT)
        custom_parameters: Optional parameters to override template defaults

    Returns:
        Created strategy details

    Raises:
        404: If template not found
        400: If validation fails
    """
    try:
        # Get template
        templates = get_cached_templates()
        template = get_template(request.template_id, templates)

        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{request.template_id}' not found"
            )

        # Merge template parameters with custom parameters
        parameters = template["parameters"].copy()
        if request.custom_parameters:
            parameters.update(request.custom_parameters)

        # Create strategy
        with get_db_session() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)

            # Create strategy record
            strategy = strategy_repo.create(
                name=request.name,
                description=template["description"],
                type=StrategyType.TEMPLATE,
                parameters=parameters,
                status=Status.DRAFT,
                is_template=False,  # This is a user strategy, not a template
                game_mode_metadata=None,
                pro_mode_metadata=None,
                backtest_metrics=None
            )

            # Create layers from template
            layer_ids = []
            for layer_template in template["layers"]:
                layer = layer_repo.create(
                    strategy_id=strategy.id,
                    layer_order=layer_template["layer_order"],
                    weight=layer_template["weight"],
                    config=layer_template["config"]
                )
                layer_ids.append(layer.id)

            # Update strategy with layer IDs
            strategy.layers = layer_ids
            session.commit()

            logger.info(
                f"Created strategy '{request.name}' from template '{request.template_id}' "
                f"with {len(layer_ids)} layers"
            )

            return StrategyCreatedResponse(
                strategy_id=strategy.id,
                name=strategy.name,
                type=strategy.type,
                status=strategy.status,
                template_id=request.template_id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating strategy: {str(e)}"
        )


@router.post(
    "/reload",
    summary="Reload templates from file",
    description="Clear cache and reload templates from file (admin function)"
)
def reload_templates() -> dict[str, str]:
    """
    Reload templates from file, clearing the cache.

    This is an admin function for testing and development.

    Returns:
        Success message
    """
    try:
        from services.template_loader import clear_template_cache
        clear_template_cache()

        # Force reload
        get_cached_templates()

        return {"status": "success", "message": "Templates reloaded successfully"}

    except Exception as e:
        logger.error(f"Error reloading templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reloading templates: {str(e)}"
        )
