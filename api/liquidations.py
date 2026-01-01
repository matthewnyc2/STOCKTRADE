"""
Liquidation API router.

Endpoints for liquidation monitoring, cascade detection, and heat tracking.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from database.connection import get_db_session
from database.repositories import (
    LiquidationRepository,
    CascadeRepository,
)
from models import (
    Liquidation,
    CascadeEvent,
    LiquidationSide,
    CascadeSeverity,
    LiquidationHeat,
    LiquidationStats,
)
from core.websocket import get_websocket_manager
from services.liquidation_monitor import (
    fetch_liquidations,
    detect_cascades,
    calculate_liquidation_heat,
    get_liquidation_stats,
    start_liquidation_monitoring,
)


router = APIRouter(prefix="/liquidations", tags=["liquidations"])


class LiquidationFetchRequest(BaseModel):
    """Schema for requesting liquidation fetch."""
    symbol: str | None = None
    min_amount_usd: float = 100000
    limit: int = 100


class CascadeDetectionRequest(BaseModel):
    """Schema for cascade detection request."""
    time_window_seconds: int = 300
    min_liquidations: int = 3
    min_amount_usd: float = 1000000


def model_to_liquidation(model) -> Liquidation:
    """Convert database model to Pydantic model."""
    return Liquidation(
        id=model.id,
        exchange=model.exchange,
        symbol=model.symbol,
        side=LiquidationSide(model.side),
        amount_usd=model.amount_usd,
        price=model.price,
        timestamp=model.timestamp,
        blockchain_txid=model.blockchain_txid,
        metadata=model.meta_data or {},
    )


def model_to_cascade(model) -> CascadeEvent:
    """Convert database model to Pydantic model."""
    return CascadeEvent(
        id=model.id,
        symbol=model.symbol,
        severity=CascadeSeverity(model.severity),
        liquidation_count=model.liquidation_count,
        total_amount_usd=model.total_amount_usd,
        start_time=model.start_time,
        end_time=model.end_time,
        duration_seconds=model.duration_seconds,
        affected_symbols=model.affected_symbols or [],
        long_percentage=model.long_percentage,
        confidence=model.confidence,
        description=model.description,
        metadata=model.meta_data or {},
    )


# ============================================================================
# LIQUIDATION ENDPOINTS
# ============================================================================

@router.get("/", response_model=list[Liquidation])
async def list_liquidations(
    symbol: str | None = None,
    exchange: str | None = None,
    side: LiquidationSide | None = None,
    min_amount_usd: float = 100000,
    limit: int = 100,
) -> list[Liquidation]:
    """
    List recent liquidations with optional filtering.

    Args:
        symbol: Filter by trading symbol.
        exchange: Filter by exchange.
        side: Filter by liquidation side (long/short).
        min_amount_usd: Minimum liquidation amount.
        limit: Maximum number of results.

    Returns:
        List[Liquidation]: List of liquidation events.
    """
    with get_db_session() as session:
        repo = LiquidationRepository(session)

        if symbol:
            liquidations = repo.get_by_symbol(symbol.upper(), limit)
        elif exchange:
            liquidations = repo.get_by_exchange(exchange.lower(), limit)
        elif side:
            liquidations = repo.get_by_side(side.value, limit)
        else:
            liquidations = repo.get_recent_hours(24, limit)

        # Filter by minimum amount
        result = [liq for liq in liquidations if liq.amount_usd >= min_amount_usd]

        return [model_to_liquidation(liq) for liq in result]


@router.get("/stats", response_model=LiquidationStats)
async def get_stats(
    symbol: str | None = None,
    hours: int = 24,
) -> LiquidationStats:
    """
    Get aggregated liquidation statistics.

    Args:
        symbol: Optional symbol filter.
        hours: Time period in hours.

    Returns:
        LiquidationStats: Aggregated statistics.
    """
    return get_liquidation_stats(symbol, hours)


@router.get("/heat/{symbol}", response_model=LiquidationHeat)
async def get_heat(symbol: str) -> LiquidationHeat:
    """
    Get liquidation heat/pressure for a symbol.

    Args:
        symbol: Trading symbol (e.g., "BTC").

    Returns:
        LiquidationHeat: Heat metrics for the symbol.
    """
    heat = calculate_liquidation_heat(symbol)
    return heat


@router.post("/fetch", response_model=list[Liquidation])
async def fetch_liquidations_endpoint(
    request: LiquidationFetchRequest,
    background_tasks: BackgroundTasks,
) -> list[Liquidation]:
    """
    Fetch liquidations from external APIs.

    Queries Coinglass/Hyblock for recent liquidation data.
    Results are stored in the database and broadcast via WebSocket.

    Args:
        request: Fetch parameters.

    Returns:
        List[Liquidation]: Fetched liquidation events.
    """
    liquidations = await fetch_liquidations(
        symbol=request.symbol,
        min_amount_usd=request.min_amount_usd,
        limit=request.limit,
    )

    # Broadcast to WebSocket clients
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "liquidations",
        {
            "action": "new_liquidations",
            "liquidations": [liq.model_dump(mode="json") for liq in liquidations],
        }
    )

    return liquidations


@router.get("/large", response_model=list[Liquidation])
async def get_large_liquidations(
    min_amount_usd: float = 1000000,
    limit: int = 50,
) -> list[Liquidation]:
    """
    Get large liquidations above a threshold.

    Args:
        min_amount_usd: Minimum amount in USD (default: $1M).
        limit: Maximum number of results.

    Returns:
        List[Liquidation]: Large liquidation events.
    """
    with get_db_session() as session:
        repo = LiquidationRepository(session)
        liquidations = repo.get_large_liquidations(min_amount_usd, limit)
        return [model_to_liquidation(liq) for liq in liquidations]


# ============================================================================
# CASCADE ENDPOINTS
# ============================================================================

@router.get("/cascades/", response_model=list[CascadeEvent])
async def list_cascades(
    symbol: str | None = None,
    severity: CascadeSeverity | None = None,
    hours: int = 24,
    limit: int = 100,
) -> list[CascadeEvent]:
    """
    List detected cascade events.

    Args:
        symbol: Filter by symbol.
        severity: Filter by severity level.
        hours: Time period in hours.
        limit: Maximum number of results.

    Returns:
        List[CascadeEvent]: List of cascade events.
    """
    with get_db_session() as session:
        repo = CascadeRepository(session)

        if symbol:
            cascades = repo.get_by_symbol(symbol.upper(), limit)
        elif severity:
            cascades = repo.get_by_severity(severity.value, limit)
        else:
            cascades = repo.get_recent_hours(hours, limit)

        return [model_to_cascade(casc) for casc in cascades]


@router.get("/cascades/active", response_model=list[CascadeEvent])
async def get_active_cascades(
    min_hours_ago: int = 1,
    limit: int = 50,
) -> list[CascadeEvent]:
    """
    Get recently active cascade events.

    Args:
        min_hours_ago: Lookback period in hours.
        limit: Maximum number of results.

    Returns:
        List[CascadeEvent]: Active cascade events.
    """
    with get_db_session() as session:
        repo = CascadeRepository(session)
        cascades = repo.get_active(min_hours_ago, limit)
        return [model_to_cascade(casc) for casc in cascades]


@router.get("/cascades/high-severity", response_model=list[CascadeEvent])
async def get_high_severity_cascades(
    limit: int = 50,
) -> list[CascadeEvent]:
    """
    Get high and extreme severity cascades.

    Args:
        limit: Maximum number of results.

    Returns:
        List[CascadeEvent]: High severity cascade events.
    """
    with get_db_session() as session:
        repo = CascadeRepository(session)
        cascades = repo.get_high_severity(limit)
        return [model_to_cascade(casc) for casc in cascades]


@router.post("/cascades/detect", response_model=list[CascadeEvent])
async def detect_cascade_events(
    request: CascadeDetectionRequest,
) -> list[CascadeEvent]:
    """
    Detect cascade liquidation events.

    Analyzes recent liquidations to identify cascade patterns.

    Args:
        request: Detection parameters.

    Returns:
        List[CascadeEvent]: Detected cascade events.
    """
    cascades = await detect_cascades(
        time_window_seconds=request.time_window_seconds,
        min_liquidations=request.min_liquidations,
        min_amount_usd=request.min_amount_usd,
    )

    # Broadcast to WebSocket clients
    if cascades:
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "liquidations",
            {
                "action": "cascade_detected",
                "cascades": [cascade.model_dump(mode="json") for cascade in cascades],
            }
        )

    return cascades


@router.get("/cascades/{cascade_id}", response_model=CascadeEvent)
async def get_cascade(cascade_id: str) -> CascadeEvent:
    """
    Get a specific cascade by ID.

    Args:
        cascade_id: The cascade ID.

    Returns:
        CascadeEvent: The cascade details.

    Raises:
        HTTPException: If cascade not found.
    """
    with get_db_session() as session:
        repo = CascadeRepository(session)
        cascade = repo.get(cascade_id)

        if cascade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cascade {cascade_id} not found"
            )

        return model_to_cascade(cascade)


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.post("/monitoring/start")
async def start_monitoring(
    interval_seconds: int = 60,
) -> dict:
    """
    Start continuous liquidation monitoring.

    Periodically fetches liquidations and detects cascades.
    Events are broadcast via WebSocket.

    Note: This runs in the background and should be called once at startup.

    Args:
        interval_seconds: Polling interval in seconds.

    Returns:
        dict: Confirmation message.
    """
    # In production, this would be managed by a task queue
    # For now, return info about the monitoring service
    return {
        "status": "info",
        "message": "Liquidation monitoring should be started via background task",
        "interval_seconds": interval_seconds,
        "websocket_channel": "liquidations",
        "note": "Call start_liquidation_monitoring() in background task",
    }


@router.get("/monitoring/status")
async def get_monitoring_status() -> dict:
    """
    Get the current status of liquidation monitoring.

    Returns:
        dict: Monitoring status information.
    """
    # Get recent activity
    with get_db_session() as session:
        liq_repo = LiquidationRepository(session)
        cascade_repo = CascadeRepository(session)

        recent_liqs = liq_repo.get_recent_hours(1, limit=1)
        recent_cascades = cascade_repo.get_recent_hours(1, limit=1)

        last_liquidation = recent_liqs[0].timestamp if recent_liqs else None
        last_cascade = recent_cascades[0].start_time if recent_cascades else None

    return {
        "status": "monitoring",
        "websocket_channel": "liquidations",
        "last_liquidation": last_liquidation.isoformat() if last_liquidation else None,
        "last_cascade": last_cascade.isoformat() if last_cascade else None,
        "apis_configured": {
            "coinglass": bool(os.getenv("COINGLASS_API_KEY")),
            "hyblock": bool(os.getenv("HYBLOCK_API_KEY")),
        },
    }


# Import os for status check
import os
