"""
Genetic Algorithm Optimization API router.

Endpoints for running GA optimization, tracking progress, and retrieving results.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from database.connection import get_db_session
from database.repositories import StrategyRepository
from models import Strategy, StrategyType
from services.genetic_optimizer import (
    GeneticOptimizer,
    GeneticConfig,
    ParameterRange,
    OptimizationResult,
    OptimizationStatus,
    GenerationResult,
    Individual,
    _running_optimizations,
    run_optimization_background,
    cancel_optimization,
)
from services.market_data import get_historical_prices
from core.websocket import get_websocket_manager


router = APIRouter(prefix="/genetic", tags=["genetic"])

# In-memory storage for optimization results
_optimization_results: dict[str, OptimizationResult] = {}


class ParameterRangeSchema(BaseModel):
    """Schema for parameter range definition."""

    name: str = Field(..., description="Parameter name")
    param_type: str = Field(..., description="Parameter type: float, int, or categorical")
    min_value: Optional[float] = Field(None, description="Minimum value (for numeric types)")
    max_value: Optional[float] = Field(None, description="Maximum value (for numeric types)")
    step: Optional[float] = Field(None, description="Step size for discrete values")
    categories: Optional[list[Any]] = Field(None, description="Allowed values for categorical type")


class GeneticOptimizationRequest(BaseModel):
    """Schema for starting a genetic optimization."""

    strategy_id: str = Field(..., description="Base strategy ID to optimize")
    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT)")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")

    # Genetic algorithm parameters
    population_size: int = Field(50, ge=10, le=200, description="Population size")
    generations: int = Field(30, ge=5, le=200, description="Number of generations")
    mutation_rate: float = Field(0.15, ge=0.0, le=1.0, description="Mutation rate")
    crossover_rate: float = Field(0.8, ge=0.0, le=1.0, description="Crossover rate")
    elitism_count: int = Field(3, ge=0, le=10, description="Number of elite individuals to preserve")
    tournament_size: int = Field(5, ge=2, le=20, description="Tournament size for selection")

    # Parameter ranges to optimize
    parameter_ranges: list[ParameterRangeSchema] = Field(
        ..., description="Ranges for parameters to optimize"
    )

    # Backtest configuration
    initial_capital: float = Field(10000, gt=0, description="Initial capital for backtesting")
    commission_rate: float = Field(0.001, ge=0.0, description="Commission rate per trade")
    slippage_rate: float = Field(0.001, ge=0.0, description="Slippage rate per trade")
    position_size_percent: float = Field(1.0, gt=0, le=1.0, description="Position size as fraction of capital")
    risk_free_rate: float = Field(0.02, description="Risk-free rate for Sharpe/Sortino")


class OptimizationStatusResponse(BaseModel):
    """Schema for optimization status response."""

    id: str
    status: str
    strategy_id: str
    symbol: str
    generations_completed: int
    total_generations: int
    best_fitness: float
    current_generation: Optional[GenerationResult] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class OptimizationResultResponse(BaseModel):
    """Schema for full optimization result."""

    id: str
    status: str
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime

    # Configuration
    config: dict[str, Any]

    # Results
    generations_completed: int
    generations: list[dict[str, Any]]
    best_individual: dict[str, Any]
    top_individuals: list[dict[str, Any]]

    # Metadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_fitness_evaluations: int
    total_backtests_run: int


def individual_to_dict(individual: Individual) -> dict[str, Any]:
    """Convert Individual to dict for JSON serialization."""
    return {
        "id": individual.id,
        "parameters": individual.parameters,
        "fitness": individual.fitness,
        "generation": individual.generation,
        "backtest_summary": {
            "total_return": float(individual.backtest_result.total_return) if individual.backtest_result else None,
            "sharpe_ratio": float(individual.backtest_result.sharpe_ratio) if individual.backtest_result and individual.backtest_result.sharpe_ratio else None,
            "sortino_ratio": float(individual.backtest_result.sortino_ratio) if individual.backtest_result and individual.backtest_result.sortino_ratio else None,
            "max_drawdown": float(individual.backtest_result.max_drawdown) if individual.backtest_result else None,
            "win_rate": float(individual.backtest_result.win_rate) if individual.backtest_result else None,
            "total_trades": individual.backtest_result.total_trades if individual.backtest_result else 0,
        } if individual.backtest_result else None,
    }


def generation_to_dict(generation: GenerationResult) -> dict[str, Any]:
    """Convert GenerationResult to dict for JSON serialization."""
    return {
        "generation": generation.generation,
        "best_fitness": generation.best_fitness,
        "worst_fitness": generation.worst_fitness,
        "avg_fitness": generation.avg_fitness,
        "best_individual": individual_to_dict(generation.best_individual),
    }


def config_to_dict(config: GeneticConfig) -> dict[str, Any]:
    """Convert GeneticConfig to dict for JSON serialization."""
    return {
        "population_size": config.population_size,
        "generations": config.generations,
        "mutation_rate": config.mutation_rate,
        "crossover_rate": config.crossover_rate,
        "elitism_count": config.elitism_count,
        "tournament_size": config.tournament_size,
        "initial_capital": float(config.initial_capital),
        "commission_rate": float(config.commission_rate),
        "slippage_rate": float(config.slippage_rate),
        "position_size_percent": float(config.position_size_percent),
        "risk_free_rate": config.risk_free_rate,
    }


def parameter_range_from_schema(schema: ParameterRangeSchema) -> ParameterRange:
    """Convert Pydantic schema to ParameterRange."""
    return ParameterRange(
        name=schema.name,
        param_type=schema.param_type,
        min_value=schema.min_value,
        max_value=schema.max_value,
        step=schema.step,
        categories=schema.categories,
    )


@router.post("/optimize", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def start_optimization(
    request: GeneticOptimizationRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """
    Start a genetic algorithm optimization.

    Runs async in background with progress tracking via WebSocket.

    Args:
        request: Optimization configuration
        background_tasks: FastAPI background tasks

    Returns:
        dict with optimization ID and status
    """
    # Generate optimization ID
    optimization_id = f"opt_{uuid4().hex[:8]}"

    # Fetch strategy
    with get_db_session() as session:
        strategy_repo = StrategyRepository(session)
        strategy_model = strategy_repo.get(request.strategy_id)

        if strategy_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {request.strategy_id} not found"
            )

        # Convert to Pydantic model
        strategy = Strategy(
            id=strategy_model.id,
            name=strategy_model.name,
            description=strategy_model.description,
            type=StrategyType(strategy_model.type),
            parameters=strategy_model.parameters or {},
            layers=strategy_model.layers or [],
            status=strategy_model.status,
            logic_gate=strategy_model.logic_gate or "none",
        )

    # Fetch historical price data
    price_data = await get_historical_prices(
        symbol=request.symbol,
        start=request.start_date,
        end=request.end_date,
        limit=10000,
    )

    if not price_data or len(price_data) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient price data for optimization. Need at least 50 candles."
        )

    # Convert price data to dict format
    price_dicts = [
        {
            "timestamp": p.timestamp,
            "open": float(p.open),
            "high": float(p.high),
            "low": float(p.low),
            "close": float(p.close),
            "volume": float(p.volume),
        }
        for p in price_data
    ]

    # Convert parameter ranges
    parameter_ranges = [
        parameter_range_from_schema(pr) for pr in request.parameter_ranges
    ]

    # Create genetic config
    config = GeneticConfig(
        population_size=request.population_size,
        generations=request.generations,
        mutation_rate=request.mutation_rate,
        crossover_rate=request.crossover_rate,
        elitism_count=request.elitism_count,
        tournament_size=request.tournament_size,
        initial_capital=Decimal(str(request.initial_capital)),
        commission_rate=Decimal(str(request.commission_rate)),
        slippage_rate=Decimal(str(request.slippage_rate)),
        position_size_percent=Decimal(str(request.position_size_percent)),
        risk_free_rate=request.risk_free_rate,
    )

    # Progress callback for WebSocket updates
    def progress_callback(generation_result: GenerationResult) -> None:
        """Broadcast progress via WebSocket."""
        try:
            ws_manager = get_websocket_manager()
            asyncio.create_task(
                ws_manager.broadcast(
                    "genetic-progress",
                    {
                        "optimization_id": optimization_id,
                        "generation": generation_result.generation,
                        "best_fitness": generation_result.best_fitness,
                        "avg_fitness": generation_result.avg_fitness,
                        "best_parameters": generation_result.best_individual.parameters,
                    }
                )
            )
        except Exception as e:
            # Don't fail optimization if WebSocket broadcast fails
            pass

    # Create optimizer
    optimizer = GeneticOptimizer(
        config=config,
        price_data=price_dicts,
        symbol=request.symbol,
        strategy_template=strategy,
        parameter_ranges=parameter_ranges,
        progress_callback=progress_callback,
    )

    # Store for access
    _running_optimizations[optimization_id] = optimizer

    # Create future for result
    result_future: asyncio.Future[OptimizationResult] = asyncio.Future()

    # Define completion callback
    def on_completion(result: OptimizationResult) -> None:
        """Store result when optimization completes."""
        _optimization_results[optimization_id] = result

        # Broadcast completion via WebSocket
        try:
            ws_manager = get_websocket_manager()
            asyncio.create_task(
                ws_manager.broadcast(
                    "genetic-complete",
                    {
                        "optimization_id": optimization_id,
                        "status": result.status.value,
                        "best_fitness": result.best_individual.fitness,
                        "best_parameters": result.best_individual.parameters,
                        "generations_completed": result.generations_completed,
                    }
                )
            )
        except Exception:
            pass

    # Chain futures
    result_future.add_done_callback(lambda f: on_completion(f.result()))

    # Run in background thread
    import concurrent.futures
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        lambda: run_optimization_background(optimization_id, optimizer, result_future)
    )

    return {
        "optimization_id": optimization_id,
        "status": "pending",
        "message": "Optimization started successfully",
        "websocket_channel": "genetic-progress",
    }


@router.get("/optimization/{optimization_id}", response_model=OptimizationStatusResponse)
async def get_optimization_status(optimization_id: str) -> OptimizationStatusResponse:
    """
    Get the status of a running or completed optimization.

    Args:
        optimization_id: The optimization ID

    Returns:
        OptimizationStatusResponse with current status
    """
    # Check if still running
    if optimization_id in _running_optimizations:
        optimizer = _running_optimizations[optimization_id]
        return OptimizationStatusResponse(
            id=optimization_id,
            status="running",
            strategy_id=optimizer.strategy_template.id,
            symbol=optimizer.symbol,
            generations_completed=optimizer._current_generation,
            total_generations=optimizer.config.generations,
            best_fitness=0.0,  # Not available while running
            created_at=datetime.utcnow(),
        )

    # Check for completed results
    result = _optimization_results.get(optimization_id)
    if result:
        current_gen = result.generations[-1] if result.generations else None
        return OptimizationStatusResponse(
            id=result.id,
            status=result.status.value,
            strategy_id=result.strategy_id,
            symbol=result.symbol,
            generations_completed=result.generations_completed,
            total_generations=result.config.generations,
            best_fitness=result.best_individual.fitness or 0.0,
            current_generation=generation_to_dict(current_gen) if current_gen else None,
            created_at=result.created_at,
            completed_at=result.completed_at,
            error_message=result.error_message,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Optimization {optimization_id} not found"
    )


@router.get("/optimization/{optimization_id}/result", response_model=OptimizationResultResponse)
async def get_optimization_result(optimization_id: str) -> OptimizationResultResponse:
    """
    Get the full result of a completed optimization.

    Args:
        optimization_id: The optimization ID

    Returns:
        OptimizationResultResponse with complete results
    """
    result = _optimization_results.get(optimization_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization {optimization_id} not found"
        )

    # Still running?
    if result.status == OptimizationStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Optimization is still running"
        )

    return OptimizationResultResponse(
        id=result.id,
        status=result.status.value,
        strategy_id=result.strategy_id,
        symbol=result.symbol,
        start_date=result.start_date,
        end_date=result.end_date,
        config=config_to_dict(result.config),
        generations_completed=result.generations_completed,
        generations=[generation_to_dict(g) for g in result.generations],
        best_individual=individual_to_dict(result.best_individual),
        top_individuals=[individual_to_dict(ind) for ind in result.top_individuals],
        created_at=result.created_at,
        completed_at=result.completed_at,
        error_message=result.error_message,
        total_fitness_evaluations=result.total_fitness_evaluations,
        total_backtests_run=result.total_backtests_run,
    )


@router.post("/optimization/{optimization_id}/cancel")
async def cancel_optimization_endpoint(optimization_id: str) -> dict[str, Any]:
    """
    Cancel a running optimization.

    Args:
        optimization_id: The optimization ID

    Returns:
        dict with cancellation status
    """
    success = cancel_optimization(optimization_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Running optimization {optimization_id} not found"
        )

    return {
        "optimization_id": optimization_id,
        "status": "cancelled",
        "message": "Optimization cancelled successfully"
    }


@router.get("/optimizations")
async def list_optimizations(
    limit: int = 50,
    status_filter: Optional[str] = None,
) -> list[OptimizationStatusResponse]:
    """
    List all optimizations.

    Args:
        limit: Maximum number of results
        status_filter: Optional filter by status

    Returns:
        List of optimization statuses
    """
    results = []

    # Add running optimizations
    for opt_id, optimizer in _running_optimizations.items():
        if status_filter is None or status_filter == "running":
            results.append(
                OptimizationStatusResponse(
                    id=opt_id,
                    status="running",
                    strategy_id=optimizer.strategy_template.id,
                    symbol=optimizer.symbol,
                    generations_completed=optimizer._current_generation,
                    total_generations=optimizer.config.generations,
                    best_fitness=0.0,
                    created_at=datetime.utcnow(),
                )
            )

    # Add completed optimizations
    for opt_id, result in _optimization_results.items():
        if status_filter is None or result.status.value == status_filter:
            current_gen = result.generations[-1] if result.generations else None
            results.append(
                OptimizationStatusResponse(
                    id=result.id,
                    status=result.status.value,
                    strategy_id=result.strategy_id,
                    symbol=result.symbol,
                    generations_completed=result.generations_completed,
                    total_generations=result.config.generations,
                    best_fitness=result.best_individual.fitness or 0.0,
                    current_generation=generation_to_dict(current_gen) if current_gen else None,
                    created_at=result.created_at,
                    completed_at=result.completed_at,
                    error_message=result.error_message,
                )
            )

    # Sort by creation time (newest first) and limit
    results.sort(key=lambda r: r.created_at, reverse=True)
    return results[:limit]


@router.delete("/optimization/{optimization_id}")
async def delete_optimization(optimization_id: str) -> dict[str, Any]:
    """
    Delete an optimization result.

    Args:
        optimization_id: The optimization ID

    Returns:
        dict with deletion status
    """
    # Cancel if running
    cancel_optimization(optimization_id)

    # Delete from storage
    deleted = _optimization_results.pop(optimization_id, None)

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization {optimization_id} not found"
        )

    return {
        "optimization_id": optimization_id,
        "status": "deleted",
        "message": "Optimization deleted successfully"
    }
