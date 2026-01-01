"""
Whale API router.

Endpoints for whale tracking, activity monitoring, and constellation detection.
"""

from decimal import Decimal
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.connection import get_db_session
from database.repositories import (
    WhaleRepository,
    WhaleActivityRepository,
    WhaleConstellationRepository,
)
from models import Whale, WhaleActivity, WhaleConstellation, WhaleAction, WhaleTier, PatternType
from core.websocket import get_websocket_manager


router = APIRouter(prefix="/whales", tags=["whales"])


class WhaleCreate(BaseModel):
    """Schema for creating a new whale tracking entry."""

    address: str
    label: str | None = None
    tier: WhaleTier = WhaleTier.LARGE
    pattern_type: PatternType = PatternType.ACCUMULATOR


def model_to_whale(model) -> Whale:
    """Convert database model to Pydantic model."""
    return Whale(
        address=model.address,
        label=model.label,
        tier=model.tier,
        holdings_usd=model.holdings_usd,
        holdings_24h_change=model.holdings_24h_change,
        historical_accuracy=model.historical_accuracy,
        pattern_type=model.pattern_type,
        last_activity=model.last_activity or datetime.utcnow(),
        preferred_tokens=model.preferred_tokens or [],
        metadata=model.metadata or {},
    )


def model_to_activity(model) -> WhaleActivity:
    """Convert database model to Pydantic model."""
    return WhaleActivity(
        id=model.id,
        whale_address=model.whale_address,
        symbol=model.symbol,
        action=model.action,
        amount_usd=model.amount_usd,
        timestamp=model.timestamp,
        transaction_hash=model.transaction_hash,
        metadata=model.metadata or {},
    )


def model_to_constellation(model) -> WhaleConstellation:
    """Convert database model to Pydantic model."""
    return WhaleConstellation(
        id=model.id,
        type=model.type,
        symbol=model.symbol,
        whale_addresses=model.whale_addresses,
        confidence=model.confidence,
        detected_at=model.detected_at or datetime.utcnow(),
        description=model.description,
        metadata=model.metadata or {},
    )


@router.get("/", response_model=list[Whale])
async def list_whales(
    tier: WhaleTier | None = None,
    pattern_type: PatternType | None = None,
    limit: int = 100,
) -> list[Whale]:
    """
    List tracked whale wallets with optional filtering.

    Args:
        tier: Filter by whale tier.
        pattern_type: Filter by behavior pattern.
        limit: Maximum number of results.

    Returns:
        List[Whale]: List of tracked whale wallets.
    """
    with get_db_session() as session:
        repo = WhaleRepository(session)

        if tier:
            whales = repo.get_by_tier(tier.value, limit)
        elif pattern_type:
            whales = repo.get_by_pattern(pattern_type.value, limit)
        else:
            whales = repo.get_all(limit=limit)

        return [model_to_whale(w) for w in whales]


@router.get("/{address}", response_model=Whale)
async def get_whale(address: str) -> Whale:
    """
    Get a specific whale wallet by address.

    Args:
        address: The whale wallet address.

    Returns:
        Whale: The whale wallet details.

    Raises:
        HTTPException: If whale not found.
    """
    with get_db_session() as session:
        repo = WhaleRepository(session)
        whale = repo.get(address)

        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {address} not found"
            )

        return model_to_whale(whale)


@router.get("/{address}/activity", response_model=list[WhaleActivity])
async def get_whale_activity(
    address: str,
    symbol: str | None = None,
    limit: int = 50,
) -> list[WhaleActivity]:
    """
    Get activity for a specific whale wallet.

    Args:
        address: The whale wallet address.
        symbol: Filter by trading symbol.
        limit: Maximum number of results.

    Returns:
        List[WhaleActivity]: List of whale activities.

    Raises:
        HTTPException: If whale not found.
    """
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whale = whale_repo.get(address)

        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {address} not found"
            )

        activity_repo = WhaleActivityRepository(session)

        if symbol:
            activities = activity_repo.get_by_whale_and_symbol(address, symbol.upper(), limit)
        else:
            activities = activity_repo.get_by_whale(address, limit)

        return [model_to_activity(a) for a in activities]


@router.get("/constellations/", response_model=list[WhaleConstellation])
async def list_constellations(
    symbol: str | None = None,
    min_confidence: float = 0.5,
    limit: int = 50,
) -> list[WhaleConstellation]:
    """
    List detected whale constellations.

    Args:
        symbol: Filter by trading symbol.
        min_confidence: Minimum confidence threshold.
        limit: Maximum number of results.

    Returns:
        List[WhaleConstellation]: List of detected constellations.
    """
    with get_db_session() as session:
        repo = WhaleConstellationRepository(session)

        constellations = repo.get_active(min_confidence, limit)

        result = []
        for c in constellations:
            const = model_to_constellation(c)
            if symbol is None or const.symbol == symbol.upper():
                result.append(const)

        return result


@router.get("/constellations/{constellation_id}", response_model=WhaleConstellation)
async def get_constellation(constellation_id: str) -> WhaleConstellation:
    """
    Get a specific constellation by ID.

    Args:
        constellation_id: The constellation ID.

    Returns:
        WhaleConstellation: The constellation details.

    Raises:
        HTTPException: If constellation not found.
    """
    with get_db_session() as session:
        repo = WhaleConstellationRepository(session)
        constellation = repo.get(constellation_id)

        if constellation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Constellation {constellation_id} not found"
            )

        return model_to_constellation(constellation)


@router.post("/track", response_model=Whale, status_code=status.HTTP_201_CREATED)
async def track_whale_wallet(wallet_data: WhaleCreate) -> Whale:
    """
    Add a new whale wallet to track.

    Args:
        wallet_data: The wallet address and optional metadata.

    Returns:
        Whale: The created whale tracking entry.
    """
    with get_db_session() as session:
        repo = WhaleRepository(session)

        # Check if already tracking
        existing = repo.get(wallet_data.address)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Wallet {wallet_data.address} is already being tracked"
            )

        whale = repo.create(
            address=wallet_data.address,
            label=wallet_data.label,
            tier=wallet_data.tier.value,
            holdings_usd=Decimal("0"),
            holdings_24h_change=Decimal("0"),
            historical_accuracy=None,
            pattern_type=wallet_data.pattern_type.value,
            last_activity=datetime.utcnow(),
            preferred_tokens=[],
            metadata={},
        )

        result = model_to_whale(whale)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "whales",
            {
                "action": "whale_added",
                "whale": result.model_dump(mode="json"),
            }
        )

        return result


@router.post("/activity", response_model=WhaleActivity, status_code=status.HTTP_201_CREATED)
async def create_whale_activity(
    whale_address: str,
    symbol: str,
    action: WhaleAction,
    amount_usd: float,
    transaction_hash: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WhaleActivity:
    """
    Record whale activity (typically from external monitoring).

    Args:
        whale_address: The whale wallet address.
        symbol: The trading symbol.
        action: The action (BOUGHT, SOLD, TRANSFERRED).
        amount_usd: Amount in USD.
        transaction_hash: Optional transaction hash.
        metadata: Additional metadata.

    Returns:
        WhaleActivity: The created activity record.
    """
    from uuid import uuid4

    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whale = whale_repo.get(whale_address)

        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {whale_address} not found"
            )

        activity_repo = WhaleActivityRepository(session)

        activity = activity_repo.create(
            id=f"act_{uuid4().hex[:12]}",
            whale_address=whale_address,
            symbol=symbol.upper(),
            action=action.value,
            amount_usd=Decimal(str(amount_usd)),
            timestamp=datetime.utcnow(),
            transaction_hash=transaction_hash,
            metadata=metadata or {},
        )

        # Update whale's last activity
        whale_repo.update(
            whale_address,
            last_activity=datetime.utcnow(),
        )

        result = model_to_activity(activity)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "whales",
            {
                "action": "whale_activity",
                "activity": result.model_dump(mode="json"),
            }
        )

        return result


@router.delete("/{address}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_tracking_whale(address: str) -> None:
    """
    Stop tracking a whale wallet.

    Args:
        address: The whale wallet address.

    Raises:
        HTTPException: If whale not found.
    """
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        activity_repo = WhaleActivityRepository(session)

        whale = whale_repo.get(address)
        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {address} not found"
            )

        # Delete all activity records
        activity_repo.delete_by_whale(address)

        # Delete whale
        whale_repo.delete(address)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "whales",
            {
                "action": "whale_removed",
                "address": address,
            }
        )


@router.post("/{address}/classify", response_model=Whale)
async def classify_whale(address: str) -> Whale:
    """
    Recalculate and update the pattern classification for a whale.

    Args:
        address: The whale wallet address.

    Returns:
        Whale: Updated whale with new pattern classification.

    Raises:
        HTTPException: If whale not found.
    """
    from services.whale_tracker import classify_whale_pattern

    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whale = whale_repo.get(address)

        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {address} not found"
            )

        # Recalculate pattern
        new_pattern = classify_whale_pattern(address)

        # Update in database
        whale_repo.update(
            address,
            pattern_type=new_pattern.value,
        )

        # Get updated whale
        updated_whale = whale_repo.get(address)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "whales",
            {
                "action": "whale_updated",
                "whale": model_to_whale(updated_whale).model_dump(mode="json"),
            }
        )

        return model_to_whale(updated_whale)


@router.post("/{address}/calculate-accuracy", response_model=Whale)
async def calculate_whale_accuracy(address: str) -> Whale:
    """
    Calculate and update the historical accuracy for a whale.

    Args:
        address: The whale wallet address.

    Returns:
        Whale: Updated whale with new accuracy score.

    Raises:
        HTTPException: If whale not found.
    """
    from services.whale_tracker import calculate_accuracy

    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whale = whale_repo.get(address)

        if whale is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whale {address} not found"
            )

        # Calculate accuracy
        accuracy = calculate_accuracy(address)

        # Update in database
        whale_repo.update(
            address,
            historical_accuracy=accuracy,
        )

        # Get updated whale
        updated_whale = whale_repo.get(address)

        # Broadcast to WebSocket clients
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "whales",
            {
                "action": "whale_updated",
                "whale": model_to_whale(updated_whale).model_dump(mode="json"),
            }
        )

        return model_to_whale(updated_whale)


@router.post("/scan-movements", response_model=list[WhaleActivity])
async def scan_whale_movements(
    min_amount_usd: float = 50000,
    hours: int = 24,
) -> list[WhaleActivity]:
    """
    Scan for large whale transactions from monitored wallets.

    Args:
        min_amount_usd: Minimum transaction amount in USD.
        hours: Lookback period in hours.

    Returns:
        List[WhaleActivity]: List of detected whale movements.
    """
    from services.whale_tracker import detect_whale_movements

    activities = await detect_whale_movements(min_amount_usd, hours)

    return activities


@router.get("/smart-money/candidates", response_model=list[dict])
async def get_smart_money_candidates(
    limit: int = 10,
) -> list[dict]:
    """
    Get potential smart money wallet candidates.

    Args:
        limit: Maximum number of candidates to return.

    Returns:
        List of discovered smart money candidates.
    """
    from services.whale_tracker import scan_smart_money

    candidates = await scan_smart_money()

    return candidates[:limit]
