"""
Backtest API router.

Endpoints for backtesting strategies and retrieving results.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.connection import get_db_session
from database.repositories import (
    BacktestResultRepository,
    EquityPointRepository,
    TradeRepository,
)
from models import BacktestResult, Trade


router = APIRouter(prefix="/backtests", tags=["backtests"])


class BacktestCreate(BaseModel):
    """Schema for creating a new backtest."""

    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbol: str | None = None
    parameters: dict[str, Any] = {}


def model_to_backtest(model) -> BacktestResult:
    """Convert database model to Pydantic model."""
    from models import EquityPoint

    # Get equity curve
    equity_repo = EquityPointRepository(model.session)
    equity_points = equity_repo.get_by_backtest(model.id)

    # Get trades
    trade_repo = TradeRepository(model.session)
    trades = trade_repo.get_by_backtest(model.id)

    return BacktestResult(
        id=model.id,
        strategy_id=model.strategy_id,
        start_date=model.start_date,
        end_date=model.end_date,
        initial_capital=model.initial_capital,
        final_capital=model.final_capital,
        total_return=model.total_return,
        sharpe_ratio=model.sharpe_ratio,
        sortino_ratio=model.sortino_ratio,
        max_drawdown=model.max_drawdown,
        win_rate=model.win_rate,
        profit_factor=model.profit_factor,
        total_trades=model.total_trades,
        equity_curve=[
            EquityPoint(
                timestamp=ep.timestamp,
                equity=ep.equity,
                drawdown=ep.drawdown,
            )
            for ep in equity_points
        ],
        trades=[
            Trade(
                id=t.id,
                symbol=t.symbol,
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                side=t.side,
                pnl=t.pnl,
                pnl_percent=t.pnl_percent,
                exit_reason=t.exit_reason,
            )
            for t in trades
        ],
    )


@router.get("/", response_model=list[BacktestResult])
async def list_backtests(
    strategy_id: str | None = None,
    limit: int = 50,
) -> list[BacktestResult]:
    """
    List backtests with optional filtering.

    Args:
        strategy_id: Filter by strategy ID.
        limit: Maximum number of results.

    Returns:
        List[BacktestResult]: List of backtest results.
    """
    with get_db_session() as session:
        repo = BacktestResultRepository(session)

        if strategy_id:
            backtests = repo.get_by_strategy(strategy_id, limit)
        else:
            backtests = repo.get_all(limit=limit, offset=0)

        results = []
        for bt in backtests:
            # Attach session to model for convenience
            bt.session = session
            results.append(model_to_backtest(bt))

        return results


@router.get("/{backtest_id}", response_model=BacktestResult)
async def get_backtest(backtest_id: str) -> BacktestResult:
    """
    Get a specific backtest result by ID.

    Args:
        backtest_id: The backtest ID.

    Returns:
        BacktestResult: The requested backtest result.

    Raises:
        HTTPException: If backtest not found.
    """
    with get_db_session() as session:
        repo = BacktestResultRepository(session)
        backtest = repo.get(backtest_id)

        if backtest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        backtest.session = session
        return model_to_backtest(backtest)


@router.post("/", response_model=BacktestResult, status_code=status.HTTP_201_CREATED)
async def create_backtest(backtest_data: BacktestCreate) -> BacktestResult:
    """
    Create and run a new backtest.

    Args:
        backtest_data: The backtest configuration.

    Returns:
        BacktestResult: The backtest results.
    """
    from decimal import Decimal
    from uuid import uuid4

    from services.backtest_engine import BacktestEngine, BacktestConfig
    from services.market_data import MarketDataService
    from database.repositories import StrategyRepository

    with get_db_session() as session:
        # Fetch strategy
        strategy_repo = StrategyRepository(session)
        strategy_model = strategy_repo.get(backtest_data.strategy_id)

        if strategy_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {backtest_data.strategy_id} not found"
            )

        # Convert to Pydantic model
        from models import Strategy, StrategyType
        strategy = Strategy(
            id=strategy_model.id,
            name=strategy_model.name,
            description=strategy_model.description,
            type=StrategyType(strategy_model.type),
            parameters=strategy_model.parameters or {},
            layers=strategy_model.layers or [],
            status=strategy_model.status,
        )

        # Determine symbol to use
        symbol = backtest_data.symbol or "BTC/USDT"

        # Fetch historical price data for the backtest period
        market_data_service = MarketDataService()
        price_data = await market_data_service.get_historical_prices(
            symbol=symbol,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            limit=10000,
        )

        if not price_data or len(price_data) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient price data for backtest. Need at least 50 candles."
            )

        # Convert price data to dict format for backtest engine
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

        # Configure backtest
        config = BacktestConfig(
            initial_capital=Decimal(str(backtest_data.initial_capital)),
            commission_rate=Decimal(str(backtest_data.parameters.get("commission_rate", 0.001))),
            slippage_rate=Decimal(str(backtest_data.parameters.get("slippage_rate", 0.001))),
            position_size_percent=Decimal(str(backtest_data.parameters.get("position_size_percent", 1.0))),
        )

        # Run backtest
        engine = BacktestEngine(config)
        result = engine.run_backtest(
            strategy=strategy,
            price_data=price_dicts,
            symbol=symbol,
        )

        # Store results in database
        repo = BacktestResultRepository(session)

        backtest_model = repo.create(
            id=result.id,
            strategy_id=result.strategy_id,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_return=result.total_return,
            sharpe_ratio=result.sharpe_ratio,
            sortino_ratio=result.sortino_ratio,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            profit_factor=result.profit_factor,
            total_trades=result.total_trades,
            parameters=backtest_data.parameters,
        )

        # Store equity points
        equity_repo = EquityPointRepository(session)
        for ep in result.equity_curve:
            equity_repo.create(
                id=f"ep_{uuid4().hex[:8]}",
                backtest_id=result.id,
                timestamp=ep.timestamp,
                equity=ep.equity,
                drawdown=ep.drawdown,
            )

        # Store trades
        trade_repo = TradeRepository(session)
        for trade in result.trades:
            trade_repo.create(
                id=trade.id,
                backtest_id=result.id,
                symbol=trade.symbol,
                entry_date=trade.entry_date,
                exit_date=trade.exit_date,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                quantity=trade.quantity,
                side=trade.side,
                pnl=trade.pnl,
                pnl_percent=trade.pnl_percent,
                exit_reason=trade.exit_reason,
            )

        backtest_model.session = session
        return model_to_backtest(backtest_model)



class MonteCarloRequest(BaseModel):
    """Schema for Monte Carlo simulation request."""

    backtest_id: str
    simulations: int = 1000
    seed: int | None = None


class MonteCarloResponse(BaseModel):
    """Schema for Monte Carlo simulation response."""

    backtest_id: str
    simulations: int
    initial_capital: float
    confidence_bands: dict[str, list[float]]
    final_capital: dict[str, Any]
    returns: dict[str, Any]
    probabilities: dict[str, float]
    drawdown: dict[str, float]
    total_trades: int


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def run_monte_carlo_simulation(request: MonteCarloRequest) -> MonteCarloResponse:
    """
    Run Monte Carlo simulation on an existing backtest.

    Randomizes the order of trades while preserving their returns to generate
    confidence intervals and probability distributions.

    Args:
        request: Monte Carlo simulation request with backtest_id and optional parameters

    Returns:
        MonteCarloResponse: Simulation results with confidence bands and statistics

    Raises:
        HTTPException: If backtest not found or has no trades
    """
    from services.monte_carlo import MonteCarloConfig, run_monte_carlo, format_monte_carlo_for_api

    with get_db_session() as session:
        # Fetch backtest
        repo = BacktestResultRepository(session)
        backtest = repo.get(request.backtest_id)

        if backtest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {request.backtest_id} not found"
            )

        # Attach session and convert to Pydantic model
        backtest.session = session
        backtest_result = model_to_backtest(backtest)

        # Validate backtest has trades
        if not backtest_result.trades:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Backtest {request.backtest_id} has no trades to simulate"
            )

        # Configure Monte Carlo simulation
        config = MonteCarloConfig(
            simulations=request.simulations,
            seed=request.seed,
        )

        # Run simulation
        result = run_monte_carlo(backtest_result, config)

        # Format for API response
        return MonteCarloResponse(**format_monte_carlo_for_api(result))


@router.get("/{backtest_id}/trades", response_model=list[Trade])
async def get_backtest_trades(backtest_id: str) -> list[Trade]:
    """
    Get all trades from a backtest.

    Args:
        backtest_id: The backtest ID.

    Returns:
        List[Trade]: List of trades from the backtest.

    Raises:
        HTTPException: If backtest not found.
    """
    with get_db_session() as session:
        bt_repo = BacktestResultRepository(session)
        backtest = bt_repo.get(backtest_id)

        if backtest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        trade_repo = TradeRepository(session)
        trades = trade_repo.get_by_backtest(backtest_id)

        return [
            Trade(
                id=t.id,
                symbol=t.symbol,
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                side=t.side,
                pnl=t.pnl,
                pnl_percent=t.pnl_percent,
                exit_reason=t.exit_reason,
            )
            for t in trades
        ]


@router.post("/compare")
async def compare_backtests(backtest_ids: list[str]) -> dict[str, Any]:
    """
    Compare multiple backtests.

    Args:
        backtest_ids: List of backtest IDs to compare.

    Returns:
        dict: Comparison metrics and analysis.
    """
    with get_db_session() as session:
        repo = BacktestResultRepository(session)

        backtests = []
        for bt_id in backtest_ids:
            bt = repo.get(bt_id)
            if bt:
                bt.session = session
                backtests.append(model_to_backtest(bt))

        if not backtests:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid backtests found"
            )

        # Build comparison
        comparison = {
            "backtests": [
                {
                    "id": bt.id,
                    "strategy_id": bt.strategy_id,
                    "total_return": float(bt.total_return),
                    "sharpe_ratio": float(bt.sharpe_ratio) if bt.sharpe_ratio else None,
                    "max_drawdown": float(bt.max_drawdown),
                    "win_rate": float(bt.win_rate),
                    "total_trades": bt.total_trades,
                }
                for bt in backtests
            ],
            "best_return": max(backtests, key=lambda bt: float(bt.total_return)).id if backtests else None,
            "best_sharpe": max(
                (bt for bt in backtests if bt.sharpe_ratio),
                key=lambda bt: float(bt.sharpe_ratio),
                default=None,
            ),
            "lowest_drawdown": min(backtests, key=lambda bt: float(bt.max_drawdown)).id if backtests else None,
        }

        return comparison


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(backtest_id: str) -> None:
    """
    Delete a backtest result.

    Args:
        backtest_id: The backtest ID.

    Raises:
        HTTPException: If backtest not found.
    """
    with get_db_session() as session:
        repo = BacktestResultRepository(session)

        backtest = repo.get(backtest_id)
        if backtest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest {backtest_id} not found"
            )

        # Delete related trades and equity points
        trade_repo = TradeRepository(session)
        equity_repo = EquityPointRepository(session)

        trade_repo.delete_by_backtest(backtest_id)
        equity_repo.delete_by_backtest(backtest_id)

        # Delete backtest
        repo.delete(backtest_id)


class WalkForwardRequest(BaseModel):
    """Schema for walk-forward optimization request."""

    strategy_id: str
    start_date: datetime
    end_date: datetime
    symbol: str | None = None
    in_sample_pct: float = 0.7
    window_size: int | None = None
    step_size: int | None = None
    commission_rate: float = 0.001
    slippage_rate: float = 0.001
    position_size_percent: float = 1.0


@router.post("/walk-forward")
async def run_walk_forward_optimization(request: WalkForwardRequest) -> dict[str, Any]:
    """
    Run walk-forward optimization on a strategy.

    Divides the data into rolling in-sample (training) and out-of-sample (testing)
    periods to validate strategy robustness over time and detect parameter degradation.

    Args:
        request: Walk-forward optimization configuration

    Returns:
        dict: Walk-forward results with period-by-period breakdown
    """
    from decimal import Decimal

    from services.walk_forward import (
        WalkForwardConfig,
        run_walk_forward,
        format_walk_forward_for_api,
        detect_parameter_degradation,
    )
    from database.repositories import StrategyRepository

    with get_db_session() as session:
        # Fetch strategy
        strategy_repo = StrategyRepository(session)
        strategy_model = strategy_repo.get(request.strategy_id)

        if strategy_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {request.strategy_id} not found"
            )

        # Convert to Pydantic model
        from models import Strategy, StrategyType
        strategy = Strategy(
            id=strategy_model.id,
            name=strategy_model.name,
            description=strategy_model.description,
            type=StrategyType(strategy_model.type),
            parameters=strategy_model.parameters or {},
            layers=strategy_model.layers or [],
            status=strategy_model.status,
        )

        # Determine symbol to use
        symbol = request.symbol or "BTC/USDT"

        # Fetch historical price data for the walk-forward period
        from services.market_data import get_historical_prices
        price_data = await get_historical_prices(
            symbol=symbol,
            start=request.start_date,
            end=request.end_date,
            limit=10000,
        )

        if not price_data or len(price_data) < 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient price data for walk-forward optimization. Need at least 200 candles."
            )

        # Convert price data to dict format for walk-forward engine
        price_dicts = [
            {
                "timestamp": p["timestamp"],
                "open": float(p["open"]),
                "high": float(p["high"]),
                "low": float(p["low"]),
                "close": float(p["close"]),
                "volume": float(p["volume"]),
            }
            for p in price_data
        ]

        # Configure walk-forward
        config = WalkForwardConfig(
            in_sample_pct=request.in_sample_pct,
            window_size=request.window_size,
            step_size=request.step_size,
            commission_rate=Decimal(str(request.commission_rate)),
            slippage_rate=Decimal(str(request.slippage_rate)),
            position_size_percent=Decimal(str(request.position_size_percent)),
        )

        # Run walk-forward optimization
        result = run_walk_forward(
            strategy=strategy,
            price_data=price_dicts,
            symbol=symbol,
            config=config,
        )

        # Detect parameter degradation
        degradation_analysis = detect_parameter_degradation(result)

        # Format for API response
        response = format_walk_forward_for_api(result)
        response["degradation_analysis"] = degradation_analysis

        return response
