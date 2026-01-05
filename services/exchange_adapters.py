"""
Exchange Adapters for Multi-Exchange Market Data Support.

Provides a unified interface for fetching market data from multiple cryptocurrency exchanges.
Supports both REST API polling and WebSocket connections for real-time data.

Supported Exchanges:
- Kraken
- KuCoin
- Bybit
- Coinbase (Advanced Trade API)
- CoinGecko (aggregator)
"""

import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """Enumeration of supported exchange types."""
    KRAKEN = "kraken"
    KUCOIN = "kucoin"
    BYBIT = "bybit"
    COINBASE = "coinbase"
    COINGECKO = "coingecko"


class DataQuality(Enum):
    """Data quality indicators."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    STALE = "stale"


class ExchangeAdapter(ABC):
    """
    Abstract base class for exchange adapters.

    All exchange adapters must implement these methods to provide
    a unified interface for market data access.
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the exchange adapter.

        Args:
            api_key: Optional API key for authenticated requests
            api_secret: Optional API secret for signed requests
        """
        self.api_key = api_key or os.getenv(f"{self.get_name().upper()}_API_KEY")
        self.api_secret = api_secret or os.getenv(f"{self.get_name().upper()}_API_SECRET")
        self.timeout = 30.0
        self._session: Optional[httpx.AsyncClient] = None
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[datetime] = None

    @abstractmethod
    def get_name(self) -> str:
        """Return the exchange name."""
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for API requests."""
        pass

    @abstractmethod
    async def get_pairs(self) -> List[Dict[str, Any]]:
        """
        Get all available trading pairs from the exchange.

        Returns:
            List of trading pairs with metadata:
            [
                {
                    "symbol": "BTC-USDT",
                    "base": "BTC",
                    "quote": "USDT",
                    "active": True,
                    "trading": True
                },
                ...
            ]
        """
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticker data for a trading pair.

        Args:
            symbol: Trading pair symbol (exchange-specific format)

        Returns:
            Ticker data dictionary or None if error:
            {
                "symbol": "BTC-USDT",
                "price": Decimal("50000.00"),
                "bid": Decimal("49999.00"),
                "ask": Decimal("50001.00"),
                "volume_24h": Decimal("1000.00"),
                "change_24h": Decimal("2.5"),
                "timestamp": datetime
            }
        """
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV candlestick data.

        Args:
            symbol: Trading pair symbol
            timeframe: Time frame (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            limit: Maximum number of candles to return
            start: Optional start datetime
            end: Optional end datetime

        Returns:
            List of OHLCV candles:
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
        pass

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create an HTTP session."""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(timeout=self.timeout)
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()

    def get_rate_limit_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current rate limit status if available.

        Returns:
            Rate limit info or None:
            {
                "remaining": 100,
                "reset": datetime,
                "limit": 1000
            }
        """
        if self._rate_limit_remaining is not None:
            return {
                "remaining": self._rate_limit_remaining,
                "reset": self._rate_limit_reset,
                "limit": None  # Not always provided by APIs
            }
        return None

    def _convert_symbol_to_exchange_format(self, symbol: str) -> str:
        """
        Convert a standard symbol format to exchange-specific format.

        Default implementation returns as-is. Override if needed.

        Args:
            symbol: Standard symbol (e.g., "BTC-USDT" or "BTC/USDT")

        Returns:
            Exchange-specific symbol format
        """
        return symbol

    def _convert_symbol_from_exchange_format(self, symbol: str) -> str:
        """
        Convert exchange-specific symbol to standard format.

        Default implementation returns as-is. Override if needed.

        Args:
            symbol: Exchange-specific symbol format

        Returns:
            Standard symbol format
        """
        return symbol


class KrakenAdapter(ExchangeAdapter):
    """
    Adapter for the Kraken cryptocurrency exchange.

    API Documentation: https://docs.kraken.com/api/docs/
    Rate Limit: Public endpoints are not heavily restricted
    """

    def get_name(self) -> str:
        return "kraken"

    def get_base_url(self) -> str:
        return "https://api.kraken.com"

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get all tradable asset pairs from Kraken."""
        try:
            session = await self._get_session()
            response = await session.get(f"{self.get_base_url()}/0/public/AssetPairs")
            response.raise_for_status()
            data = response.json()

            if data.get("error") or not data.get("result"):
                logger.error(f"Kraken API error: {data.get('error')}")
                return []

            pairs = []
            for pair_id, pair_info in data["result"].items():
                # Skip dark pools and special pairs
                if pair_info.get("wsname") is None:
                    continue

                base = pair_info.get("base", "")
                quote = pair_info.get("quote", "")
                altname = pair_info.get("altname", "")

                pairs.append({
                    "symbol": altname,  # More readable than pair_id
                    "pair_id": pair_id,
                    "base": base,
                    "quote": quote,
                    "active": True,  # Kraken doesn't provide this in API
                    "trading": True,
                    "fees": pair_info.get("fees", [])
                })

            logger.info(f"Retrieved {len(pairs)} trading pairs from Kraken")
            return pairs

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Kraken pairs: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Kraken pairs: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from Kraken."""
        try:
            session = await self._get_session()

            # Kraken uses pair_id for API calls, try to get it
            params = {"pair": symbol}
            response = await session.get(
                f"{self.get_base_url()}/0/public/Ticker",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("error") or not data.get("result"):
                logger.warning(f"Kraken ticker error for {symbol}: {data.get('error')}")
                return None

            # Get first result
            result = next(iter(data["result"].values()))

            return {
                "symbol": symbol,
                "price": Decimal(str(result.get("c", [])[0] or 0)),
                "bid": Decimal(str(result.get("b", [])[0] or 0)),
                "ask": Decimal(str(result.get("a", [])[0] or 0)),
                "volume_24h": Decimal(str(result.get("v", [])[1] or 0)),
                "change_24h": Decimal(str(result.get("p", [])[0] or 0)),
                "high_24h": Decimal(str(result.get("h", [])[1] or 0)),
                "low_24h": Decimal(str(result.get("l", [])[1] or 0)),
                "timestamp": datetime.utcnow(),
                "trades_24h": int(result.get("t", [])[1] or 0)
            }

        except Exception as e:
            logger.error(f"Error fetching Kraken ticker for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get OHLCV data from Kraken."""
        try:
            session = await self._get_session()

            # Map timeframe to Kraken interval
            timeframe_map = {
                "1m": 1, "5m": 5, "15m": 15, "30m": 30,
                "1h": 60, "4h": 240, "1d": 1440, "1w": 10080
            }
            interval = timeframe_map.get(timeframe, 60)

            params = {
                "pair": symbol,
                "interval": interval
            }

            # Add since parameter if start time provided
            if start:
                params["since"] = int(start.timestamp())

            response = await session.get(
                f"{self.get_base_url()}/0/public/OHLC",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("error") or not data.get("result"):
                logger.error(f"Kraken OHLCV error for {symbol}: {data.get('error')}")
                return []

            ohlcv_data = data["result"]
            candles = []

            # Process OHLC data (last entry is for current timeframe)
            for timestamp, ohlc in ohlcv_data.items():
                if timestamp == "last":
                    continue

                ts = datetime.fromtimestamp(int(timestamp))
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue

                candles.append({
                    "timestamp": ts,
                    "open": Decimal(str(ohlc[0])),
                    "high": Decimal(str(ohlc[1])),
                    "low": Decimal(str(ohlc[2])),
                    "close": Decimal(str(ohlc[3])),
                    "volume": Decimal(str(ohlc[6])),
                    "trades": int(ohlc[7])
                })

            # Sort by timestamp and limit
            candles.sort(key=lambda x: x["timestamp"])
            return candles[-limit:] if limit else candles

        except Exception as e:
            logger.error(f"Error fetching Kraken OHLCV for {symbol}: {e}")
            return []


class KuCoinAdapter(ExchangeAdapter):
    """
    Adapter for the KuCoin cryptocurrency exchange.

    API Documentation: https://www.kucoin.com/docs-new/
    Rate Limit: 300 requests/min for public endpoints
    """

    def get_name(self) -> str:
        return "kucoin"

    def get_base_url(self) -> str:
        return "https://api.kucoin.com"

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get all trading symbols from KuCoin."""
        try:
            session = await self._get_session()
            response = await session.get(f"{self.get_base_url()}/api/v1/symbols")
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "200000" or not data.get("data"):
                logger.error(f"KuCoin API error: {data.get('msg')}")
                return []

            pairs = []
            for symbol_data in data["data"]:
                pairs.append({
                    "symbol": symbol_data.get("symbol"),
                    "base": symbol_data.get("baseCurrency"),
                    "quote": symbol_data.get("quoteCurrency"),
                    "active": symbol_data.get("enableTrading", False),
                    "trading": symbol_data.get("enableTrading", False),
                    "fee": symbol_data.get("fee"),
                    "price_precision": symbol_data.get("pricePrecision"),
                    "quantity_precision": symbol_data.get("quantityPrecision")
                })

            logger.info(f"Retrieved {len(pairs)} trading pairs from KuCoin")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching KuCoin pairs: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from KuCoin."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.get_base_url()}/api/v1/market/orderbook/level1",
                params={"symbol": symbol}
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "200000" or not data.get("data"):
                logger.warning(f"KuCoin ticker error for {symbol}: {data.get('msg')}")
                return None

            ticker_data = data["data"]
            price = Decimal(str(ticker_data.get("price", 0)))

            # Get 24h stats for more data
            stats_response = await session.get(
                f"{self.get_base_url()}/api/v1/market/stats",
                params={"symbol": symbol}
            )
            stats_data = stats_response.json().get("data", {})

            return {
                "symbol": symbol,
                "price": price,
                "bid": Decimal(str(ticker_data.get("bestBid", 0))),
                "ask": Decimal(str(ticker_data.get("bestAsk", 0))),
                "volume_24h": Decimal(str(stats_data.get("vol", 0))),
                "change_24h": Decimal(str(stats_data.get("changeRate", 0))),
                "high_24h": Decimal(str(stats_data.get("high", 0))),
                "low_24h": Decimal(str(stats_data.get("low", 0))),
                "timestamp": datetime.utcnow(),
                "turnover_24h": Decimal(str(stats_data.get("volValue", 0)))
            }

        except Exception as e:
            logger.error(f"Error fetching KuCoin ticker for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get OHLCV kline data from KuCoin."""
        try:
            session = await self._get_session()

            # Map timeframe to KuCoin type
            timeframe_map = {
                "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
                "1h": "1hour", "4h": "4hour", "1d": "1day", "1w": "1week"
            }
            kline_type = timeframe_map.get(timeframe, "1hour")

            params = {
                "symbol": symbol,
                "type": kline_type
            }

            if start:
                params["startAt"] = int(start.timestamp())
            if end:
                params["endAt"] = int(end.timestamp())

            response = await session.get(
                f"{self.get_base_url()}/api/v1/market/candles",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "200000" or not data.get("data"):
                logger.error(f"KuCoin klines error for {symbol}: {data.get('msg')}")
                return []

            candles = []
            # KuCoin returns: [startTime, open, close, high, low, volume, turnover]
            for candle in data["data"]:
                ts = datetime.fromtimestamp(int(candle[0]))
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue

                candles.append({
                    "timestamp": ts,
                    "open": Decimal(str(candle[1])),
                    "high": Decimal(str(candle[3])),
                    "low": Decimal(str(candle[4])),
                    "close": Decimal(str(candle[2])),
                    "volume": Decimal(str(candle[5])),
                    "turnover": Decimal(str(candle[6]))
                })

            # Sort and limit
            candles.sort(key=lambda x: x["timestamp"])
            return candles[-limit:] if limit else candles

        except Exception as e:
            logger.error(f"Error fetching KuCoin klines for {symbol}: {e}")
            return []


class BybitAdapter(ExchangeAdapter):
    """
    Adapter for the Bybit cryptocurrency exchange.

    API Documentation: https://bybit-exchange.github.io/docs/v5/
    Rate Limit: 120 requests/min for public endpoints
    """

    def get_name(self) -> str:
        return "bybit"

    def get_base_url(self) -> str:
        return "https://api.bybit.com"

    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get all trading symbols from Bybit (spot market)."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.get_base_url()}/v5/market/instruments-info",
                params={"category": "spot"}
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result", {}).get("list"):
                logger.error(f"Bybit API error: {data.get('retMsg')}")
                return []

            pairs = []
            for symbol_data in data["result"]["list"]:
                pairs.append({
                    "symbol": symbol_data.get("symbol"),
                    "base": symbol_data.get("baseCoin"),
                    "quote": symbol_data.get("quoteCoin"),
                    "active": symbol_data.get("status") == "Trading",
                    "trading": symbol_data.get("status") == "Trading",
                    "price_precision": symbol_data.get("priceScale"),
                    "quantity_precision": symbol_data.get("lotSizeFilter", {}).get("qtyScale")
                })

            logger.info(f"Retrieved {len(pairs)} trading pairs from Bybit")
            return pairs

        except Exception as e:
            logger.error(f"Error fetching Bybit pairs: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker information from Bybit."""
        try:
            session = await self._get_session()
            response = await session.get(
                f"{self.get_base_url()}/v5/market/tickers",
                params={
                    "category": "spot",
                    "symbol": symbol
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result", {}).get("list"):
                logger.warning(f"Bybit ticker error for {symbol}: {data.get('retMsg')}")
                return None

            ticker_data = data["result"]["list"][0]

            return {
                "symbol": symbol,
                "price": Decimal(str(ticker_data.get("lastPrice", 0))),
                "bid": Decimal(str(ticker_data.get("bid1Price", 0))),
                "ask": Decimal(str(ticker_data.get("ask1Price", 0))),
                "volume_24h": Decimal(str(ticker_data.get("volume24h", 0))),
                "change_24h": Decimal(str(ticker_data.get("price24hPcnt", 0))) * Decimal("100"),
                "high_24h": Decimal(str(ticker_data.get("highPrice24h", 0))),
                "low_24h": Decimal(str(ticker_data.get("lowPrice24h", 0))),
                "timestamp": datetime.utcnow(),
                "turnover_24h": Decimal(str(ticker_data.get("turnover24h", 0)))
            }

        except Exception as e:
            logger.error(f"Error fetching Bybit ticker for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get OHLCV kline data from Bybit."""
        try:
            session = await self._get_session()

            # Map timeframe to Bybit interval
            timeframe_map = {
                "1m": "1", "5m": "5", "15m": "15", "30m": "30",
                "1h": "60", "4h": "240", "1d": "D", "1w": "W"
            }
            interval = timeframe_map.get(timeframe, "60")

            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": interval,
                "limit": min(limit, 1000)  # Bybit max is 1000
            }

            if start:
                params["start"] = int(start.timestamp() * 1000)
            if end:
                params["end"] = int(end.timestamp() * 1000)

            response = await session.get(
                f"{self.get_base_url()}/v5/market/kline",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0 or not data.get("result", {}).get("list"):
                logger.error(f"Bybit klines error for {symbol}: {data.get('retMsg')}")
                return []

            candles = []
            # Bybit returns: [startTime, open, high, low, close, volume, turnover]
            for candle in data["result"]["list"]:
                ts = datetime.fromtimestamp(int(candle[0]) / 1000)
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue

                candles.append({
                    "timestamp": ts,
                    "open": Decimal(str(candle[1])),
                    "high": Decimal(str(candle[2])),
                    "low": Decimal(str(candle[3])),
                    "close": Decimal(str(candle[4])),
                    "volume": Decimal(str(candle[5])),
                    "turnover": Decimal(str(candle[6]))
                })

            # Bybit returns in reverse chronological order
            candles.sort(key=lambda x: x["timestamp"])
            return candles[-limit:] if limit else candles

        except Exception as e:
            logger.error(f"Error fetching Bybit klines for {symbol}: {e}")
            return []


class ExchangeManager:
    """
    Manager class for handling multiple exchange adapters.

    Provides unified access to multiple exchanges with failover,
    data aggregation, and quality monitoring.
    """

    def __init__(self):
        """Initialize the exchange manager with all available adapters."""
        self.adapters: Dict[str, ExchangeAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        """Initialize all available exchange adapters."""
        # Initialize adapters without API keys (public endpoints)
        self.adapters[ExchangeType.KRAKEN.value] = KrakenAdapter()
        self.adapters[ExchangeType.KUCOIN.value] = KuCoinAdapter()
        self.adapters[ExchangeType.BYBIT.value] = BybitAdapter()

        logger.info(f"Initialized {len(self.adapters)} exchange adapters")

    def get_adapter(self, exchange: str) -> Optional[ExchangeAdapter]:
        """
        Get an adapter by exchange name.

        Args:
            exchange: Exchange name (kraken, kucoin, bybit)

        Returns:
            ExchangeAdapter instance or None
        """
        return self.adapters.get(exchange.lower())

    def get_all_adapters(self) -> Dict[str, ExchangeAdapter]:
        """Get all initialized adapters."""
        return self.adapters.copy()

    async def get_ticker_from_any(
        self,
        symbol: str,
        preferred_exchanges: Optional[List[str]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get ticker from first available exchange.

        Args:
            symbol: Trading symbol (will be converted per exchange)
            preferred_exchanges: List of exchanges to try in order

        Returns:
            Tuple of (ticker_data, exchange_name)
        """
        exchanges = preferred_exchanges or list(self.adapters.keys())

        for exchange_name in exchanges:
            adapter = self.get_adapter(exchange_name)
            if not adapter:
                continue

            try:
                # Convert symbol for this exchange
                exchange_symbol = self._convert_symbol_for_exchange(symbol, exchange_name)
                ticker = await adapter.get_ticker(exchange_symbol)

                if ticker:
                    logger.info(f"Got ticker for {symbol} from {exchange_name}")
                    return ticker, exchange_name

            except Exception as e:
                logger.warning(f"Failed to get ticker from {exchange_name} for {symbol}: {e}")
                continue

        logger.error(f"Failed to get ticker for {symbol} from any exchange")
        return None, None

    async def get_aggregated_price(
        self,
        symbol: str,
        exchanges: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated price data from multiple exchanges.

        Args:
            symbol: Trading symbol
            exchanges: List of exchanges to query (default: all)

        Returns:
            Aggregated price data:
            {
                "symbol": "BTC-USDT",
                "prices": {
                    "kraken": {"price": 50000, "volume": 100},
                    "kucoin": {"price": 50001, "volume": 90},
                    ...
                },
                "avg_price": Decimal,
                "min_price": Decimal,
                "max_price": Decimal,
                "total_volume": Decimal,
                "price_spread_percent": Decimal,
                "timestamp": datetime
            }
        """
        target_exchanges = exchanges or list(self.adapters.keys())
        prices = {}
        total_volume = Decimal("0")
        sum_prices = Decimal("0")
        count = 0

        for exchange_name in target_exchanges:
            adapter = self.get_adapter(exchange_name)
            if not adapter:
                continue

            try:
                exchange_symbol = self._convert_symbol_for_exchange(symbol, exchange_name)
                ticker = await adapter.get_ticker(exchange_symbol)

                if ticker and ticker.get("price"):
                    prices[exchange_name] = {
                        "price": ticker["price"],
                        "volume": ticker.get("volume_24h", Decimal("0"))
                    }
                    total_volume += ticker.get("volume_24h", Decimal("0"))
                    sum_prices += ticker["price"]
                    count += 1

            except Exception as e:
                logger.warning(f"Failed to get price from {exchange_name} for {symbol}: {e}")

        if not prices:
            return {}

        avg_price = sum_prices / count if count > 0 else Decimal("0")
        price_values = [p["price"] for p in prices.values()]
        min_price = min(price_values)
        max_price = max(price_values)
        spread = ((max_price - min_price) / avg_price * 100) if avg_price > 0 else Decimal("0")

        return {
            "symbol": symbol,
            "prices": prices,
            "avg_price": avg_price,
            "min_price": min_price,
            "max_price": max_price,
            "total_volume": total_volume,
            "price_spread_percent": spread,
            "exchange_count": count,
            "timestamp": datetime.utcnow()
        }

    def _convert_symbol_for_exchange(self, symbol: str, exchange: str) -> str:
        """
        Convert a standard symbol format to exchange-specific format.

        Args:
            symbol: Standard symbol (e.g., "BTC-USDT")
            exchange: Target exchange name

        Returns:
            Exchange-specific symbol format
        """
        # Default format: BTC-USDT
        if "-" in symbol or "/" in symbol:
            base, quote = symbol.replace("/", "-").split("-")
        else:
            # Try to infer
            return symbol

        # Exchange-specific mappings
        if exchange == "kraken":
            # Kraken uses XBT for BTC in some pairs
            if base == "BTC":
                # Check if quote is USD, EUR, etc.
                if quote in ["USD", "EUR", "CAD"]:
                    base = "XBT"
            return f"{base}{quote}"

        elif exchange == "kucoin" or exchange == "bybit":
            # These exchanges use BASE-QUOTE format
            return f"{base}-{quote}"

        return symbol

    async def close_all(self):
        """Close all adapter sessions."""
        for adapter in self.adapters.values():
            await adapter.close()


# Global exchange manager instance
_exchange_manager: Optional[ExchangeManager] = None


def get_exchange_manager() -> ExchangeManager:
    """
    Get the global exchange manager instance.

    Returns:
        ExchangeManager singleton
    """
    global _exchange_manager
    if _exchange_manager is None:
        _exchange_manager = ExchangeManager()
    return _exchange_manager
