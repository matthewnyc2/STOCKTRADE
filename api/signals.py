"""
Signal API router.

Endpoints for signal generation and retrieval.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db_session
from database.repositories import SignalRepository
from models import Signal, SignalType
from core.websocket import get_websocket_manager


router = APIRouter(prefix="/signals", tags=["signals"])


class SignalCreate(BaseModel):
    """Schema for creating a new signal."""

    strategy_id: str
    symbol: str
    signal_type: SignalType
    confidence: float
    price: float
    reasoning: str | None = None
    layer_breakdown: list[dict[str, Any]] = []


def model_to_signal(model) -> Signal:
    """Convert database model to Pydantic model."""
    return Signal(
        id=model.id,
        strategy_id=model.strategy_id,
        symbol=model.symbol,
        signal_type=model.signal_type,
        confidence=model.confidence,
        price=model.price,
        timestamp=model.timestamp,
        reasoning=model.reasoning,
        layer_breakdown=model.layer_breakdown,
        metadata=model.metadata,
    )


@router.get("/", response_model=list[Signal])
async def list_signals(
    strategy_id: str | None = None,
    symbol: str | None = None,
    signal_type: SignalType | None = None,
    hours: int | None = None,
    limit: int = 100,
) -> list[Signal]:
    """
    List signals with optional filtering.

    Args:
        strategy_id: Filter by strategy ID.
        symbol: Filter by trading symbol.
        signal_type: Filter by signal type.
        hours: Filter by last N hours.
        limit: Maximum number of results.

    Returns:
        List[Signal]: List of signals.
    """
    with get_db_session() as session:
        repo = SignalRepository(session)

        if strategy_id and symbol:
            signals = repo.get_by_strategy_and_symbol(strategy_id, symbol, limit)
        elif strategy_id:
            signals = repo.get_by_strategy(strategy_id, limit)
        elif symbol:
            signals = repo.get_by_symbol(symbol, limit)
        elif signal_type:
            signals = repo.get_by_type(signal_type.value, limit)
        elif hours:
            signals = repo.get_recent(hours, limit)
        else:
            signals = repo.get_all(limit=limit)

        return [model_to_signal(s) for s in signals]


@router.get("/live")
async def stream_live_signals():
    """
    SSE stream of live signals.

    Returns a Server-Sent Events stream for real-time signal updates.

    Returns:
        StreamingResponse: SSE stream of signals.
    """
    async def event_stream():
        """Generator for SSE events."""
        # Import here to avoid circular dependency
        import asyncio
        import json

        ws_manager = get_websocket_manager()

        while True:
            # Check for new signals via subscriber count
            # In a real implementation, you'd use a queue or pub/sub
            await asyncio.sleep(1)

            # Send a keepalive comment
            yield ": keepalive\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{signal_id}", response_model=Signal)
async def get_signal(signal_id: str) -> Signal:
    """
    Get a specific signal by ID.

    Args:
        signal_id: The signal ID.

    Returns:
        Signal: The requested signal.

    Raises:
        HTTPException: If signal not found.
    """
    with get_db_session() as session:
        repo = SignalRepository(session)
        signal = repo.get(signal_id)

        if signal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Signal {signal_id} not found"
            )

        return model_to_signal(signal)


@router.get("/strategy/{strategy_id}/latest", response_model=list[Signal])
async def get_latest_signals_for_strategy(
    strategy_id: str,
    limit: int = 10,
) -> list[Signal]:
    """
    Get the latest signals for a specific strategy.

    Args:
        strategy_id: The strategy ID.
        limit: Maximum number of results.

    Returns:
        List[Signal]: List of latest signals.
    """
    with get_db_session() as session:
        repo = SignalRepository(session)
        signals = repo.get_by_strategy(strategy_id, limit)
        return [model_to_signal(s) for s in signals]


@router.get("/symbol/{symbol}/latest", response_model=Signal | None)
async def get_latest_signal_for_symbol(symbol: str) -> Signal | None:
    """
    Get the latest signal for a specific symbol.

    Args:
        symbol: The trading symbol.

    Returns:
        Signal: The latest signal or None.
    """
    with get_db_session() as session:
        repo = SignalRepository(session)
        signal = repo.get_latest_for_symbol(symbol)

        if signal:
            return model_to_signal(signal)

        return None


@router.post("/", response_model=Signal, status_code=status.HTTP_201_CREATED)
async def create_signal(signal_data: SignalCreate) -> Signal:
    """
    Create a new signal.

    Args:
        signal_data: The signal creation data.

    Returns:
        Signal: The created signal.
    """
    from decimal import Decimal
    from uuid import uuid4

    with get_db_session() as session:
        repo = SignalRepository(session)

        signal = repo.create(
            id=f"sig_{uuid4().hex[:12]}",
            strategy_id=signal_data.strategy_id,
            symbol=signal_data.symbol.upper(),
            signal_type=signal_data.signal_type.value,
            confidence=signal_data.confidence,
            price=Decimal(str(signal_data.price)),
            timestamp=datetime.utcnow(),
            reasoning=signal_data.reasoning,
            layer_breakdown=signal_data.layer_breakdown,
            metadata={},
        )

        result = model_to_signal(signal)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "signals",
            {
                "action": "signal_created",
                "signal": result.model_dump(mode="json"),
            }
        )

        return result


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signal(signal_id: str) -> None:
    """
    Delete a signal.

    Args:
        signal_id: The signal ID.

    Raises:
        HTTPException: If signal not found.
    """
    with get_db_session() as session:
        repo = SignalRepository(session)

        signal = repo.get(signal_id)
        if signal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Signal {signal_id} not found"
            )

        repo.delete(signal_id)

        # Broadcast deletion
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "signals",
            {
                "action": "signal_deleted",
                "signal_id": signal_id,
            }
        )


class SignalGenerateRequest(BaseModel):
    """Schema for manual signal generation request."""

    strategy_id: str
    symbol: str


class SignalGenerateResponse(BaseModel):
    """Schema for signal generation response."""

    success: bool
    signals: list[Signal] = []
    message: str | None = None


@router.post("/generate", response_model=SignalGenerateResponse)
async def generate_signals(request: SignalGenerateRequest) -> SignalGenerateResponse:
    """
    Manually trigger signal generation for a strategy and symbol.

    This endpoint allows manually generating signals by:
    1. Fetching the latest price data
    2. Calculating indicators
    3. Executing the strategy
    4. Storing and broadcasting generated signals

    Args:
        request: Signal generation request with strategy_id and symbol

    Returns:
        SignalGenerateResponse: Generated signals

    Raises:
        HTTPException: If strategy not found or signal generation fails
    """
    from services.strategy_executor import get_strategy_executor
    from database.repositories import StrategyRepository

    # Get the strategy
    with get_db_session() as session:
        strategy_repo = StrategyRepository(session)
        strategy_model = strategy_repo.get(request.strategy_id)

        if strategy_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {request.strategy_id} not found"
            )

        # Convert to Pydantic model
        from models import Strategy, StrategyType, Status, LogicGate
        strategy = Strategy(
            id=strategy_model.id,
            name=strategy_model.name,
            description=strategy_model.description,
            type=StrategyType(strategy_model.type),
            parameters=strategy_model.parameters,
            layers=strategy_model.layers,
            status=Status(strategy_model.status),
            logic_gate=LogicGate(strategy_model.logic_gate),
            created_at=strategy_model.created_at,
            updated_at=strategy_model.updated_at,
        )

    # Get price data and calculate indicators
    from services.strategy_executor import get_latest_price_data
    from services.indicators import calculate_all_indicators

    price_data = get_latest_price_data(request.symbol)

    if not price_data:
        return SignalGenerateResponse(
            success=False,
            signals=[],
            message=f"No price data available for {request.symbol}"
        )

    price_data["symbol"] = request.symbol

    indicators = calculate_all_indicators(
        opens=price_data["opens"],
        highs=price_data["highs"],
        lows=price_data["lows"],
        closes=price_data["closes"],
        volumes=price_data["volumes"]
    )

    # Generate signal
    executor = get_strategy_executor()
    signal = executor.execute_strategy(strategy, price_data, indicators)

    return SignalGenerateResponse(
        success=True,
        signals=[signal],
        message=f"Generated {signal.signal_type} signal with confidence {signal.confidence:.2f}"
    )


@router.post("/generate/active", response_model=SignalGenerateResponse)
async def generate_signals_for_active_strategies(
    symbol: str | None = None,
    symbols: list[str] | None = None
) -> SignalGenerateResponse:
    """
    Generate signals for all active strategies.

    Args:
        symbol: Optional single symbol to generate signals for
        symbols: Optional list of symbols to generate signals for

    Returns:
        SignalGenerateResponse: All generated signals
    """
    from services.strategy_executor import get_strategy_executor

    # Determine symbols to process
    if symbol:
        symbols_to_process = [symbol]
    elif symbols:
        symbols_to_process = symbols
    else:
        symbols_to_process = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    # Execute all active strategies
    executor = get_strategy_executor()
    all_signals_dict = executor.execute_all_active_strategies(symbols_to_process)

    # Flatten the signals
    all_signals = []
    for signals in all_signals_dict.values():
        all_signals.extend(signals)

    return SignalGenerateResponse(
        success=True,
        signals=all_signals,
        message=f"Generated {len(all_signals)} signals across {len(symbols_to_process)} symbols"
    )
