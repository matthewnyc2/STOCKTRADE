"""
Portfolio API router.

Endpoints for portfolio management and position tracking.
"""

from decimal import Decimal
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.connection import get_db_session
from database.repositories import PortfolioRepository, PositionRepository
from models import Portfolio, Position, PortfolioMetrics
from core.websocket import get_websocket_manager
from services.paper_trading import PaperTradingEngine, PaperTradingConfig


router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Global paper trading engine instance
_paper_trading_engine: PaperTradingEngine | None = None


def get_paper_trading_engine() -> PaperTradingEngine:
    """Get or create the global paper trading engine instance."""
    global _paper_trading_engine
    if _paper_trading_engine is None:
        _paper_trading_engine = PaperTradingEngine(
            config=PaperTradingConfig(
                starting_balance=Decimal("10000"),
                commission_rate=Decimal("0.001"),
                slippage_rate=Decimal("0.001"),
                max_daily_loss_percent=Decimal("0.20"),
                max_open_positions=10,
            )
        )
    return _paper_trading_engine


class TradeRequest(BaseModel):
    """Schema for executing a paper trade."""

    symbol: str
    side: str  # LONG or SHORT
    quantity: float
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    reason: str | None = None


def model_to_position(model) -> Position:
    """Convert database model to Pydantic model."""
    return Position(
        id=model.id,
        symbol=model.symbol,
        side=model.side,
        quantity=model.quantity,
        entry_price=model.entry_price,
        current_price=model.current_price,
        unrealized_pnl=model.unrealized_pnl,
        unrealized_pnl_percent=model.unrealized_pnl_percent,
        stop_loss=model.stop_loss,
        take_profit=model.take_profit,
        entry_timestamp=model.entry_timestamp,
        metadata=model.meta or {},
    )


def model_to_portfolio(model, positions: list[Position] | None = None) -> Portfolio:
    """Convert database model to Pydantic model."""
    return Portfolio(
        total_equity=model.total_equity,
        starting_balance=model.starting_balance,
        total_pnl=model.total_pnl,
        total_pnl_percent=model.total_pnl_percent,
        open_pnl=model.open_pnl or Decimal("0"),
        positions=positions or [],
        metrics=PortfolioMetrics(
            sharpe_ratio=model.sharpe_ratio,
            sortino_ratio=model.sortino_ratio,
            max_drawdown=model.max_drawdown,
            win_rate=model.win_rate,
            profit_factor=model.profit_factor,
        ),
        last_updated=model.last_updated or datetime.utcnow(),
    )


@router.get("/", response_model=Portfolio)
async def get_portfolio() -> Portfolio:
    """
    Get the current portfolio state.

    Returns:
        Portfolio: Current portfolio with positions and metrics.
    """
    engine = get_paper_trading_engine()
    return engine.get_portfolio()


@router.get("/positions", response_model=list[Position])
async def get_positions(
    open_only: bool = True,
    symbol: str | None = None,
    limit: int = 100,
) -> list[Position]:
    """
    Get positions with optional filtering.

    Args:
        open_only: Only return open positions.
        symbol: Filter by symbol.
        limit: Maximum number of results.

    Returns:
        List[Position]: List of positions.
    """
    with get_db_session() as session:
        repo = PositionRepository(session)

        if symbol:
            positions = repo.get_by_symbol(symbol.upper())
        elif open_only:
            positions = repo.get_many(open=True, limit=limit)
        else:
            positions = repo.get_all(limit=limit)

        return [model_to_position(p) for p in positions]


@router.get("/positions/{position_id}", response_model=Position)
async def get_position(position_id: str) -> Position:
    """
    Get a specific position by ID.

    Args:
        position_id: The position ID.

    Returns:
        Position: The requested position.

    Raises:
        HTTPException: If position not found.
    """
    with get_db_session() as session:
        repo = PositionRepository(session)
        position = repo.get(position_id)

        if position is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {position_id} not found"
            )

        return model_to_position(position)


@router.post("/trade", response_model=Position, status_code=status.HTTP_201_CREATED)
async def execute_trade(trade: TradeRequest) -> Position:
    """
    Execute a paper trade.

    Args:
        trade: The trade details.

    Returns:
        Position: The created position.

    Raises:
        HTTPException: If trade execution fails.
    """
    engine = get_paper_trading_engine()

    # Get price from trade or use default
    entry_price = Decimal(str(trade.price)) if trade.price else Decimal("50000")

    # Execute the trade
    result = engine.execute_trade(
        symbol=trade.symbol,
        side=trade.side,
        quantity=Decimal(str(trade.quantity)),
        entry_price=entry_price,
        stop_loss=Decimal(str(trade.stop_loss)) if trade.stop_loss else None,
        take_profit=Decimal(str(trade.take_profit)) if trade.take_profit else None,
        reason=trade.reason,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    # Get the created position
    with get_db_session() as session:
        repo = PositionRepository(session)
        position = repo.get(result.position_id)
        if position is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Position was created but not found"
            )

        position_model = model_to_position(position)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "portfolio",
            {
                "action": "position_opened",
                "position": position_model.model_dump(mode="json"),
                "executed_price": float(result.executed_price) if result.executed_price else None,
                "commission": float(result.commission) if result.commission else None,
                "slippage": float(result.slippage) if result.slippage else None,
            }
        )

        return position_model


@router.post("/positions/{position_id}/close", response_model=Position)
async def close_position(
    position_id: str,
    exit_price: float | None = None,
    reason: str | None = None,
) -> Position:
    """
    Close an open position.

    Args:
        position_id: The position ID.
        exit_price: The exit price (optional, uses current if not provided).
        reason: Reason for closing.

    Returns:
        Position: The closed position details.

    Raises:
        HTTPException: If position not found or already closed.
    """
    engine = get_paper_trading_engine()

    # First get the position to find current price if not provided
    with get_db_session() as session:
        repo = PositionRepository(session)
        position = repo.get(position_id)

        if position is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {position_id} not found"
            )

        if not position.open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position {position_id} is already closed"
            )

        # Use current price if exit price not provided
        if exit_price is None:
            exit_price = float(position.current_price)

    # Close the position
    result = engine.close_position(
        position_id=position_id,
        exit_price=Decimal(str(exit_price)),
        reason=reason,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    # Get the updated position
    with get_db_session() as session:
        repo = PositionRepository(session)
        updated = repo.get(position_id)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Position was closed but not found"
            )

        result_model = model_to_position(updated)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "portfolio",
            {
                "action": "position_closed",
                "position": result_model.model_dump(mode="json"),
                "executed_price": float(result.executed_price) if result.executed_price else None,
                "commission": float(result.commission) if result.commission else None,
            }
        )

        return result_model


@router.get("/history")
async def get_portfolio_history(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Get portfolio equity history.

    Args:
        start_date: Start date for history (ISO format).
        end_date: End date for history (ISO format).

    Returns:
        dict: Portfolio history data with equity curve.
    """
    # For now, return empty history
    # In a real system, this would query equity snapshots
    return {
        "equity_curve": [],
        "metrics": {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
        },
    }


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_portfolio() -> None:
    """
    Reset the portfolio to initial state.

    Closes all positions and resets equity.
    """
    engine = get_paper_trading_engine()
    engine.reset_portfolio()

    # Broadcast reset
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "portfolio",
        {"action": "portfolio_reset"}
    )


@router.post("/update-prices")
async def update_prices(prices: dict[str, float]) -> dict:
    """
    Update position prices and check stop losses/take profits.

    Args:
        prices: Dictionary of symbol -> current price

    Returns:
        dict with updated positions and any closed positions
    """
    engine = get_paper_trading_engine()

    # Convert to Decimal
    decimal_prices = {k: Decimal(str(v)) for k, v in prices.items()}

    # Update positions
    updates = engine.update_positions(decimal_prices)

    # Check stop losses and take profits
    closed_positions = engine.check_stop_losses(decimal_prices)

    # Get updated portfolio
    portfolio = engine.get_portfolio()

    # Broadcast updates
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "portfolio",
        {
            "action": "prices_updated",
            "portfolio": portfolio.model_dump(mode="json"),
            "closed_positions": [
                {
                    "position_id": c.position_id,
                    "reason": c.close_reason,
                    "current_price": float(c.current_price),
                }
                for c in closed_positions
            ],
        }
    )

    return {
        "portfolio": portfolio.model_dump(mode="json"),
        "updated_positions": len(updates),
        "closed_positions": [
            {
                "position_id": c.position_id,
                "reason": c.close_reason,
            }
            for c in closed_positions
        ],
    }
