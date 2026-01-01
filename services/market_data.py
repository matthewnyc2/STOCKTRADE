"""
Market Data Service.

Handles price data fetching from external APIs and internal database storage.
Supports both real-time price fetching and historical OHLCV data retrieval.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging

import httpx

logger = logging.getLogger(__name__)


# CoinGecko API configuration
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

# Symbol mapping for common crypto pairs
SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "MATIC": "matic-network",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
}


async def get_current_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get current price for a cryptocurrency symbol.

    Uses CoinGecko free API for price data.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")

    Returns:
        Dictionary with price data or None if error
        {
            "symbol": str,
            "price": Decimal,
            "price_change_24h": Decimal,
            "price_change_percent_24h": Decimal,
            "market_cap": Optional[Decimal],
            "volume_24h": Optional[Decimal],
            "timestamp": datetime
        }
    """
    try:
        # Map symbol to CoinGecko ID
        coin_id = SYMBOL_MAP.get(symbol.upper(), symbol.lower())

        headers = {}
        if COINGECKO_API_KEY:
            headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try simple price endpoint first (free, no rate limit issues)
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            }

            response = await client.get(
                f"{COINGECKO_API_BASE}/coins/markets",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            if not data or len(data) == 0:
                logger.warning(f"No data found for symbol: {symbol}")
                return None

            coin_data = data[0]

            return {
                "symbol": symbol.upper(),
                "price": Decimal(str(coin_data.get("current_price", 0))),
                "price_change_24h": Decimal(str(coin_data.get("price_change_24h", 0))),
                "price_change_percent_24h": Decimal(str(coin_data.get("price_change_percentage_24h", 0))),
                "market_cap": Decimal(str(coin_data.get("market_cap", 0))) if coin_data.get("market_cap") else None,
                "volume_24h": Decimal(str(coin_data.get("total_volume", 0))) if coin_data.get("total_volume") else None,
                "timestamp": datetime.utcnow(),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching price for {symbol}: {e}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching price for {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching price for {symbol}: {e}")
        return None


async def get_historical_prices(
    symbol: str,
    timeframe: str = "1h",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get historical OHLCV prices for a cryptocurrency.

    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        timeframe: Time frame - "1m", "5m", "15m", "30m", "1h", "4h", "1d"
        start: Start datetime (default: limit periods ago)
        end: End datetime (default: now)
        limit: Maximum number of candles to return

    Returns:
        List of OHLCV dictionaries
        [
            {
                "timestamp": datetime,
                "open": Decimal,
                "high": Decimal,
                "low": Decimal,
                "close": Decimal,
                "volume": Decimal
            },
            ...
        ]
    """
    try:
        # Map symbol to CoinGecko ID
        coin_id = SYMBOL_MAP.get(symbol.upper(), symbol.lower())

        # Map timeframe to CoinGecko days
        timeframe_map = {
            "1m": 1,      # Use 1 day data
            "5m": 1,
            "15m": 1,
            "30m": 1,
            "1h": 1,
            "4h": max(1, limit * 4 // 24),  # Approximate days
            "1d": max(1, limit),
        }

        days = timeframe_map.get(timeframe, 1)

        headers = {}
        if COINGECKO_API_KEY:
            headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get market chart data
            params = {
                "vs_currency": "usd",
                "days": days,
            }

            # For hourly data, use specific endpoint
            if timeframe in ["1m", "5m", "15m", "30m", "1h"]:
                params["interval"] = "hourly"

            response = await client.get(
                f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            prices = data.get("prices", [])
            volumes_data = data.get("total_volumes", [])

            # Convert to OHLCV format
            # Note: CoinGecko only gives close prices, we'll estimate OHLC
            result = []

            for i, (timestamp_ms, price) in enumerate(prices[-limit:]):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)

                # For OHLC from close-only data, use close for all and estimate high/low
                # This is a limitation of free API
                close_price = Decimal(str(price))

                # Estimate high/low using nearby data points
                if i > 0:
                    prev_price = Decimal(str(prices[-limit:][i - 1][1]))
                    low_price = min(close_price, prev_price)
                    high_price = max(close_price, prev_price)
                else:
                    low_price = close_price
                    high_price = close_price

                open_price = close_price  # Best approximation

                volume = Decimal(str(volumes_data[-limit:][i][1])) if i < len(volumes_data) else Decimal("0")

                # Apply date filtering if specified
                if start and timestamp < start:
                    continue
                if end and timestamp > end:
                    continue

                result.append({
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                })

            return result

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching historical prices for {symbol}: {e}")
        return []
    except httpx.RequestError as e:
        logger.error(f"Request error fetching historical prices for {symbol}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching historical prices for {symbol}: {e}")
        return []


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

    Generates realistic-looking price data for development and testing.
    Stores data in the prices table.

    Returns:
        Dictionary with count of records inserted per symbol
    """
    from database.connection import get_db_session
    from database.models.price import PriceModel
    from uuid import uuid4
    import random

    random.seed(42)

    result = {"BTC": 0, "ETH": 0, "SOL": 0}

    # Base prices for generating sample data
    base_prices = {
        "BTC": 45000,
        "ETH": 2500,
        "SOL": 100,
    }

    # Generate 30 days of hourly data (720 candles per symbol)
    num_periods = 720

    with get_db_session() as session:
        for symbol, base_price in base_prices.items():
            # Check if data already exists
            existing = session.query(PriceModel).filter(
                PriceModel.symbol == symbol
            ).first()

            if existing:
                logger.info(f"Price data already exists for {symbol}, skipping seed")
                result[symbol] = session.query(PriceModel).filter(
                    PriceModel.symbol == symbol
                ).count()
                continue

            current_price = base_price
            now = datetime.utcnow()

            for i in range(num_periods):
                timestamp = now - timedelta(hours=num_periods - i)

                # Generate realistic price movement using random walk
                change_percent = random.gauss(0, 0.002)  # 0.2% standard deviation
                current_price = current_price * (1 + change_percent)

                # Generate OHLC from close price
                high = current_price * random.uniform(1.0, 1.005)
                low = current_price * random.uniform(0.995, 1.0)
                open_price = current_price * random.uniform(0.998, 1.002)

                # Volume (random but somewhat consistent)
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


def get_prices_from_db(
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get price data from the database.

    Args:
        symbol: Cryptocurrency symbol
        start: Start datetime filter
        end: End datetime filter
        limit: Maximum records to return

    Returns:
        List of OHLCV price data
    """
    from database.connection import get_db_session
    from database.models.price import PriceModel

    with get_db_session() as session:
        query = session.query(PriceModel).filter(
            PriceModel.symbol == symbol.upper()
        )

        if start:
            query = query.filter(PriceModel.timestamp >= start)
        if end:
            query = query.filter(PriceModel.timestamp <= end)

        query = query.order_by(PriceModel.timestamp.desc()).limit(limit)

        results = query.all()
        return [
            {
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": float(p.volume),
            }
            for p in reversed(results)
        ]


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
    prices = get_prices_from_db(symbol, limit=limit)

    if not prices:
        # Fall back to API
        prices = await get_historical_prices(symbol, timeframe, limit=limit)

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
