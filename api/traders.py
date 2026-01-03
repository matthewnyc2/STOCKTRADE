"""
API endpoints for the Trader Tracking System.

Provides endpoints for tracking traders, retrieving their activity,
and analyzing their performance and trading profiles.
"""
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.connection import get_db_session
from database.repositories import TraderRepository
from models.trader import Trader, TraderActivity, TraderProfile, TradingStyle, TraderRiskLevel
from services.trader_tracker import (
    analyze_trader_profile,
    calculate_trader_performance,
)

router = APIRouter(prefix="/traders", tags=["traders"])

class TraderCreate(BaseModel):
    """Schema for tracking a new trader."""
    username: str
    exchange: str

def model_to_trader(model: Any) -> Trader:
    """Converts a database model to a Trader Pydantic model."""
    return Trader(
        id=model.id,
        username=model.username,
        exchange=model.exchange,
        rank=model.rank,
        pnl_24h=model.pnl_24h,
        win_rate=model.win_rate,
        last_activity=model.last_activity or datetime.utcnow(),
        followers=model.followers,
    )

def model_to_activity(model: Any) -> TraderActivity:
    """Converts a database model to a TraderActivity Pydantic model."""
    return TraderActivity(
        id=model.id,
        trader_id=model.trader_id,
        symbol=model.symbol,
        action=model.action,
        amount_usd=model.amount_usd,
        timestamp=model.timestamp,
        pnl=model.pnl,
        leverage=model.leverage,
    )

def model_to_profile(model: Any) -> TraderProfile:
    """Converts a database model to a TraderProfile Pydantic model."""
    return TraderProfile(
        trader_id=model.trader_id,
        risk_level=TraderRiskLevel(model.risk_level),
        preferred_assets=model.preferred_assets or [],
        trading_style=TradingStyle(model.trading_style),
        avg_holding_period_seconds=model.avg_holding_period_seconds,
        preferred_exchange=model.preferred_exchange,
    )

@router.get("/", response_model=list[Trader])
async def list_traders(exchange: str | None = None, limit: int = 100) -> list[Trader]:
    """
    List tracked traders, with optional filtering by exchange.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        if exchange:
            traders = repo.get_by_exchange(exchange, limit)
        else:
            traders = repo.get_all(limit=limit)
        return [model_to_trader(t) for t in traders]

@router.get("/{trader_id}", response_model=Trader)
async def get_trader(trader_id: str) -> Trader:
    """
    Get a specific trader by their ID.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        trader = repo.get(trader_id)
        if not trader:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader not found")
        return model_to_trader(trader)

@router.get("/{trader_id}/activity", response_model=list[TraderActivity])
async def get_trader_activity(trader_id: str, limit: int = 50) -> list[TraderActivity]:
    """
    Get the recent trading activity for a specific trader.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        activities = repo.get_activity(trader_id, limit=limit)
        return [model_to_activity(a) for a in activities]

@router.get("/{trader_id}/profile", response_model=TraderProfile)
async def get_trader_profile(trader_id: str) -> TraderProfile:
    """
    Get the trading profile for a specific trader.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        profile = repo.get_profile(trader_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
        return model_to_profile(profile)

@router.post("/track", response_model=Trader, status_code=status.HTTP_201_CREATED)
async def track_trader(trader_data: TraderCreate) -> Trader:
    """
    Start tracking a new trader.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        # This is a simplified version; in a real app, you'd fetch initial data
        trader_id = f"trader_{uuid4().hex[:12]}"
        trader = repo.create(
            id=trader_id,
            username=trader_data.username,
            exchange=trader_data.exchange,
        )
        return model_to_trader(trader)

@router.post("/{trader_id}/analyze", response_model=TraderProfile)
async def analyze_trader(trader_id: str) -> TraderProfile:
    """
    Analyze a trader's performance and update their profile.
    """
    profile = analyze_trader_profile(trader_id)
    return model_to_profile(profile)

@router.post("/{trader_id}/performance")
async def get_trader_performance(trader_id: str) -> dict[str, Any]:
    """
    Calculate and return the performance metrics for a trader.
    """
    performance = calculate_trader_performance(trader_id)
    return performance
