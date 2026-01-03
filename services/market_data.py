"""
Market Data Service.

Handles price data fetching from external APIs and internal database storage.
Supports both real-time price fetching and historical OHLCV data retrieval.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging
import asyncio

from services.data_source_manager import data_source_manager

logger = logging.getLogger(__name__)


async def get_current_price(symbol: str, source: str = "coingecko") -> Optional[Dict[str, Any]]:
    """
    Get current price for a cryptocurrency symbol from a specified data source.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        source: The name of the data source to use (e.g., "coingecko")

    Returns:
        Dictionary with price data or None if error.
    """
    data_source = data_source_manager.get_data_source(source)
    if not data_source:
        logger.error(f"Data source '{source}' not found.")
        return None
    return await data_source.get_current_price(symbol)


async def get_historical_prices(
    symbol: str,
    timeframe: str = "1h",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100,
    source: str = "coingecko",
) -> List[Dict[str, Any]]:
    """
    Get historical OHLCV prices for a cryptocurrency from a specified data source.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        timeframe: Time frame - "1m", "5m", "15m", "30m", "1h", "4h", "1d"
        start: Start datetime
        end: End datetime
        limit: Maximum number of candles to return
        source: The name of the data source to use (e.g., "coingecko", "database")

    Returns:
        List of OHLCV dictionaries.
    """
    data_source = data_source_manager.get_data_source(source)
    if not data_source:
        logger.error(f"Data source '{source}' not found.")
        return []
    return await data_source.get_historical_prices(symbol, timeframe, start, end, limit)


def get_prices_from_db(
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get price data from the database. This is a synchronous wrapper for the database data source.
    """
    data_source = data_source_manager.get_data_source("database")
    if not data_source:
        logger.error("Database data source not found.")
        return []
        
    return asyncio.run(
        data_source.get_historical_prices(symbol, start=start, end=end, limit=limit)
    )


async def get_price_with_indicators(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
    Get price data with all technical indicators calculated.

    First tries to get from database, falls back to API if no data.

    Args:
        symbol: Cryptocurrency symbol
        timeframe: Time frame
        limit: Number of periods

    Returns:
        Dictionary with prices and indicators
    """
    from services.indicators import calculate_all_indicators

    # Try to get from database first
    prices = await get_historical_prices(symbol, timeframe, limit=limit, source="database")

    if not prices:
        # Fall back to API
        prices = await get_historical_prices(symbol, timeframe, limit=limit, source="coingecko")

    if not prices:
        return None

    # Extract OHLCV data
    opens = [p["open"] for p in prices]
    highs = [p["high"] for p in prices]
    lows = [p["low"] for p in prices]
    closes = [p["close"] for p in prices]
    volumes = [p["volume"] for p in prices]

    # Calculate all indicators
    indicators = calculate_all_indicators(opens, highs, lows, closes, volumes)

    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "prices": prices,
        "indicators": indicators,
    }

def calculate_ohlc_from_tick(ticks: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """
    Calculate OHLC from tick (trade) data.

    Args:
        ticks: List of trade data with "price" and "volume"

    Returns:
        Dictionary with open, high, low, close, volume or None if empty
    """
    if not ticks:
        return None

    prices = [tick["price"] for tick in ticks]
    volume = sum(tick.get("volume", 0) for tick in ticks)

    return {
        "open": prices[0],
        "high": max(prices),
        "low": min(prices),
        "close": prices[-1],
        "volume": volume,
    }


async def seed_price_data() -> Dict[str, int]:
    """
    Seed database with sample historical price data for BTC, ETH, SOL.
    """
    from database.connection import get_db_session
    from database.models.price import PriceModel
    from uuid import uuid4
    import random
    from datetime import timedelta

    random.seed(42)
    result = {"BTC": 0, "ETH": 0, "SOL": 0}
    base_prices = {"BTC": 45000, "ETH": 2500, "SOL": 100}
    num_periods = 720

    with get_db_session() as session:
        for symbol, base_price in base_prices.items():
            if session.query(PriceModel).filter(PriceModel.symbol == symbol).first():
                logger.info(f"Price data already exists for {symbol}, skipping seed")
                result[symbol] = session.query(PriceModel).filter(PriceModel.symbol == symbol).count()
                continue

            current_price = base_price
            now = datetime.utcnow()
            for i in range(num_periods):
                timestamp = now - timedelta(hours=num_periods - i)
                change_percent = random.gauss(0, 0.002)
                current_price *= (1 + change_percent)
                high = current_price * random.uniform(1.0, 1.005)
                low = current_price * random.uniform(0.995, 1.0)
                open_price = current_price * random.uniform(0.998, 1.002)
                volume = random.uniform(100, 1000) * base_price / 100

                price_record = PriceModel(
                    id=f"price_{uuid4().hex[:12]}",
                    symbol=symbol,
                    timestamp=timestamp,
                    open=Decimal(f"{open_price:.2f}"),
                    high=Decimal(f"{high:.2f}"),
                    low=Decimal(f"{low:.2f}"),
                    close=Decimal(f"{current_price:.2f}"),
                    volume=Decimal(f"{volume:.2f}"),
                )
                session.add(price_record)
                result[symbol] += 1
            logger.info(f"Seeded {result[symbol]} price records for {symbol}")
    return result
