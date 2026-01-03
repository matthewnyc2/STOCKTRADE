"""
CoinGecko Data Source Plugin.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging

import httpx

from core.data_source import DataSource

logger = logging.getLogger(__name__)

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

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


class CoinGeckoDataSource(DataSource):
    """
    Data source for CoinGecko API.
    """

    @property
    def name(self) -> str:
        return "coingecko"

    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price for a cryptocurrency symbol from CoinGecko.
        """
        try:
            coin_id = SYMBOL_MAP.get(symbol.upper(), symbol.lower())
            headers = {}
            if COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

            async with httpx.AsyncClient(timeout=30.0) as client:
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
            logger.error(f"HTTP error fetching price for {symbol} from CoinGecko: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching price for {symbol} from CoinGecko: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {symbol} from CoinGecko: {e}")
            return None

    async def get_historical_prices(
        self,
        symbol: str,
        timeframe: str = "1h",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV prices for a cryptocurrency from CoinGecko.
        """
        try:
            coin_id = SYMBOL_MAP.get(symbol.upper(), symbol.lower())
            
            # The /ohlc endpoint's granularity is automatic based on the number of days.
            # We will approximate the number of days based on the timeframe and limit.
            days = 1
            if timeframe.endswith('d'):
                days = limit * int(timeframe[:-1])
            elif timeframe.endswith('h'):
                days = (limit * int(timeframe[:-1])) // 24
            elif timeframe.endswith('m'):
                days = (limit * int(timeframe[:-1])) // 1440
            days = max(1, days) # Ensure at least 1 day is requested.

            headers = {}
            if COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"vs_currency": "usd", "days": days}
                
                response = await client.get(
                    f"{COINGECKO_API_BASE}/coins/{coin_id}/ohlc",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                result = []
                # The data format is [timestamp, open, high, low, close]
                for row in data[-limit:]:
                    timestamp = datetime.fromtimestamp(row[0] / 1000)
                    
                    if start and timestamp < start:
                        continue
                    if end and timestamp > end:
                        continue

                    result.append({
                        "timestamp": timestamp,
                        "open": Decimal(str(row[1])),
                        "high": Decimal(str(row[2])),
                        "low": Decimal(str(row[3])),
                        "close": Decimal(str(row[4])),
                        "volume": Decimal("0"), # OHLC endpoint does not provide volume
                    })
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching historical prices for {symbol} from CoinGecko: {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching historical prices for {symbol} from CoinGecko: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching historical prices for {symbol} from CoinGecko: {e}")
            return []
