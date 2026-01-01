"""
Market Data API endpoints.

Provides endpoints for fetching price data, calculating indicators,
and managing historical price data in the database.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from database.connection import get_db_context
from database.models.price import PriceModel
from sqlalchemy import desc, func

from models.market_data import (
    CurrentPrice,
    HistoricalPricesRequest,
    PriceData,
    PriceDataSummary,
    MarketDataResponse,
    IndicatorsRequest,
    SeedPriceDataResponse,
)

from services.market_data import (
    get_current_price as fetch_current_price,
    get_historical_prices as fetch_historical_prices,
    seed_price_data,
    get_prices_from_db,
    get_price_with_indicators,
)

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/price/{symbol}", response_model=CurrentPrice)
async def get_current_price_endpoint(symbol: str):
    """
    Get current price for a cryptocurrency.

    Returns current price, 24h change, market cap, and volume.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, SOL)

    Returns:
        Current price information
    """
    price_data = await fetch_current_price(symbol)

    if price_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch price for symbol: {symbol}"
        )

    return CurrentPrice(**price_data)


@router.get("/price/{symbol}/history", response_model=List[PriceData])
async def get_historical_prices_endpoint(
    symbol: str,
    timeframe: str = Query(default="1h", description="Time frame (1m, 5m, 15m, 30m, 1h, 4h, 1d)"),
    start: Optional[datetime] = Query(default=None, description="Start datetime"),
    end: Optional[datetime] = Query(default=None, description="End datetime"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max number of candles"),
):
    """
    Get historical OHLCV price data for a cryptocurrency.

    First tries to get from database, falls back to external API.

    Args:
        symbol: Cryptocurrency symbol
        timeframe: Time frame for candles
        start: Optional start datetime
        end: Optional end datetime
        limit: Maximum number of candles

    Returns:
        List of OHLCV candles
    """
    # Try database first
    prices = get_prices_from_db(symbol, start=start, end=end, limit=limit)

    if not prices:
        # Fall back to API
        prices = await fetch_historical_prices(symbol, timeframe, start=start, end=end, limit=limit)

    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data available for symbol: {symbol}"
        )

    return [PriceData(**p) for p in prices]


@router.get("/indicators/{symbol}")
async def get_indicators_endpoint(
    symbol: str,
    timeframe: str = Query(default="1h", description="Time frame"),
    limit: int = Query(default=100, ge=20, le=500, description="Number of periods"),
):
    """
    Get calculated technical indicators for a symbol.

    Returns price data with all technical indicators pre-calculated.

    Args:
        symbol: Cryptocurrency symbol
        timeframe: Time frame
        limit: Number of periods to analyze

    Returns:
        Price data with indicators
    """
    data = await get_price_with_indicators(symbol, timeframe, limit)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not calculate indicators for symbol: {symbol}"
        )

    return data


@router.get("/summary/{symbol}")
async def get_price_summary_endpoint(
    symbol: str,
    start: Optional[datetime] = Query(default=None, description="Start datetime"),
    end: Optional[datetime] = Query(default=None, description="End datetime"),
):
    """
    Get summary statistics for price data.

    Provides count, date range, price range, average price, and total volume.

    Args:
        symbol: Cryptocurrency symbol
        start: Optional start datetime filter
        end: Optional end datetime filter

    Returns:
        Price data summary
    """
    with get_db_context() as session:
        query = session.query(
            func.count(PriceModel.id).label("count"),
            func.min(PriceModel.timestamp).label("start_date"),
            func.max(PriceModel.timestamp).label("end_date"),
            func.min(PriceModel.low).label("min_price"),
            func.max(PriceModel.high).label("max_price"),
            func.avg(PriceModel.close).label("avg_price"),
            func.sum(PriceModel.volume).label("total_volume"),
        ).filter(PriceModel.symbol == symbol.upper())

        if start:
            query = query.filter(PriceModel.timestamp >= start)
        if end:
            query = query.filter(PriceModel.timestamp <= end)

        result = query.first()

        if not result or result.count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data found for symbol: {symbol}"
            )

        return PriceDataSummary(
            symbol=symbol.upper(),
            count=result.count,
            start_date=result.start_date,
            end_date=result.end_date,
            min_price=Decimal(str(result.min_price)),
            max_price=Decimal(str(result.max_price)),
            avg_price=Decimal(str(result.avg_price)),
            total_volume=Decimal(str(result.total_volume)),
        )


@router.post("/seed", response_model=SeedPriceDataResponse)
async def seed_price_data_endpoint():
    """
    Seed database with sample historical price data.

    Generates realistic-looking price data for BTC, ETH, and SOL
    for development and testing purposes.

    Returns:
        Summary of seeded data
    """
    try:
        counts = await seed_price_data()

        total_count = sum(counts.values())
        symbols = ", ".join(counts.keys())

        return SeedPriceDataResponse(
            success=True,
            message=f"Seeded {total_count} price records for {symbols}",
            counts=counts,
        )
    except Exception as e:
        return SeedPriceDataResponse(
            success=False,
            message=f"Error seeding price data: {str(e)}",
            counts={},
        )


@router.get("/available-symbols")
async def get_available_symbols():
    """
    Get list of symbols with price data available.

    Returns all symbols that have price data in the database.

    Returns:
        List of available symbols with record counts
    """
    with get_db_context() as session:
        results = session.query(
            PriceModel.symbol,
            func.count(PriceModel.id).label("count"),
            func.min(PriceModel.timestamp).label("first_date"),
            func.max(PriceModel.timestamp).label("last_date"),
        ).group_by(PriceModel.symbol).all()

        return [
            {
                "symbol": r.symbol,
                "count": r.count,
                "first_date": r.first_date.isoformat() if r.first_date else None,
                "last_date": r.last_date.isoformat() if r.last_date else None,
            }
            for r in results
        ]


@router.get("/latest/{symbol}")
async def get_latest_price(symbol: str):
    """
    Get the most recent price data for a symbol from the database.

    Args:
        symbol: Cryptocurrency symbol

    Returns:
        Latest OHLCV candle
    """
    with get_db_context() as session:
        price = session.query(PriceModel).filter(
            PriceModel.symbol == symbol.upper()
        ).order_by(desc(PriceModel.timestamp)).first()

        if not price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data found for symbol: {symbol}"
            )

        return {
            "symbol": price.symbol,
            "timestamp": price.timestamp,
            "open": float(price.open),
            "high": float(price.high),
            "low": float(price.low),
            "close": float(price.close),
            "volume": float(price.volume),
        }
