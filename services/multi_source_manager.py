"""
Multi-Source Data Manager with Failover.

Manages data acquisition from multiple sources with automatic failover.
Provides a unified interface for fetching market data with fallback
to alternative sources when primary sources fail.

Data Sources (in priority order):
1. Binance (primary) - WebSocket for real-time, REST for historical
2. CoinGecko (secondary) - REST API for reference prices
3. Kraken (tertiary) - REST API for backup
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """Status of a data source."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    name: str
    priority: int  # Lower number = higher priority
    enabled: bool = True
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Rate limiting
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_second: Optional[int] = None

    # Data types supported
    supports_websocket: bool = False
    supports_rest: bool = True
    supports_historical: bool = False


@dataclass
class SourceHealth:
    """Health status of a data source."""

    status: DataSourceStatus
    last_check: datetime
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    avg_response_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_requests - self.failed_requests) / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "avg_response_time": self.avg_response_time,
            "success_rate": self.success_rate,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
        }


class BinanceDataSource:
    """
    Binance data source (primary).

    Provides both WebSocket (real-time) and REST API (historical) access.
    """

    def __init__(self, config: DataSourceConfig):
        """
        Initialize Binance data source.

        Args:
            config: Data source configuration
        """
        self.config = config
        self.base_url = "https://api.binance.com"
        self._session: Optional[httpx.AsyncClient] = None

        logger.info("BinanceDataSource initialized")

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(timeout=self.config.timeout)
        return self._session

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticker data.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")

        Returns:
            Ticker data or None if error
        """
        try:
            session = await self._get_session()

            response = await session.get(
                f"{self.base_url}/api/v3/ticker/24hr", params={"symbol": symbol.upper()}
            )
            response.raise_for_status()

            data = response.json()

            return {
                "symbol": data.get("symbol"),
                "price": Decimal(str(data.get("lastPrice", 0))),
                "bid": Decimal(str(data.get("bidPrice", 0))),
                "ask": Decimal(str(data.get("askPrice", 0))),
                "volume_24h": Decimal(str(data.get("volume", 0))),
                "change_24h": Decimal(str(data.get("priceChange", 0))),
                "change_percent_24h": Decimal(str(data.get("priceChangePercent", 0))),
                "high_24h": Decimal(str(data.get("highPrice", 0))),
                "low_24h": Decimal(str(data.get("lowPrice", 0))),
                "timestamp": datetime.utcnow(),
                "exchange": "binance",
            }

        except Exception as e:
            logger.error(f"Binance API error for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV candlestick data.

        Args:
            symbol: Trading symbol
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of candles
            start: Optional start time for precise time range
            end: Optional end time for precise time range

        Returns:
            List of OHLCV candles
        """
        try:
            session = await self._get_session()

            params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

            # Add precise time range parameters for backfill
            if start:
                params["startTime"] = int(start.timestamp() * 1000)
            if end:
                params["endTime"] = int(end.timestamp() * 1000)

            response = await session.get(f"{self.base_url}/api/v3/klines", params=params)
            response.raise_for_status()

            data = response.json()

            candles = []
            for item in data:
                timestamp = datetime.fromtimestamp(item[0] / 1000)

                # Filter by time range if start/end specified
                if start and timestamp < start:
                    continue
                if end and timestamp > end:
                    continue

                candles.append(
                    {
                        "timestamp": timestamp,
                        "open": Decimal(str(item[1])),
                        "high": Decimal(str(item[2])),
                        "low": Decimal(str(item[3])),
                        "close": Decimal(str(item[4])),
                        "volume": Decimal(str(item[5])),
                        "close_time": datetime.fromtimestamp(item[6] / 1000),
                        "quote_volume": Decimal(str(item[7])),
                        "trades": int(item[8]),
                        "exchange": "binance",
                    }
                )

            # Sort and limit
            candles.sort(key=lambda x: x["timestamp"], reverse=True)

            if limit and len(candles) > limit:
                candles = candles[:limit]

            return candles

        except Exception as e:
            logger.error(f"Binance OHLCV error for {symbol}: {e}")
            return []

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()


class CoinGeckoDataSource:
    """
    CoinGecko data source (secondary).

    Provides reference prices and market data via REST API.
    """

    def __init__(self, config: DataSourceConfig, api_key: Optional[str] = None):
        """
        Initialize CoinGecko data source.

        Args:
            config: Data source configuration
            api_key: Optional API key for higher rate limits
        """
        self.config = config
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = api_key
        self._session: Optional[httpx.AsyncClient] = None

        logger.info("CoinGeckoDataSource initialized")

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self._session is None or self._session.is_closed:
            headers = {}
            if self.api_key:
                headers["x-cg-demo-api-key"] = self.api_key

            self._session = httpx.AsyncClient(timeout=self.config.timeout, headers=headers)
        return self._session

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticker data.

        Args:
            symbol: CoinGecko coin ID (e.g., "bitcoin")

        Returns:
            Ticker data or None if error
        """
        try:
            session = await self._get_session()

            response = await session.get(f"{self.base_url}/coins/{symbol.lower()}")
            response.raise_for_status()

            data = response.json()
            market_data = data.get("market_data", {})

            return {
                "symbol": data.get("symbol", "").upper(),
                "name": data.get("name"),
                "price": Decimal(str(market_data.get("current_price", {}).get("usd", 0))),
                "volume_24h": Decimal(str(market_data.get("total_volume", {}).get("usd", 0))),
                "market_cap": Decimal(str(market_data.get("market_cap", {}).get("usd", 0))),
                "change_24h": Decimal(str(market_data.get("price_change_24h", 0))),
                "change_percent_24h": Decimal(
                    str(market_data.get("price_change_percentage_24h", 0))
                ),
                "high_24h": Decimal(str(market_data.get("high_24h", {}).get("usd", 0))),
                "low_24h": Decimal(str(market_data.get("low_24h", {}).get("usd", 0))),
                "timestamp": datetime.utcnow(),
                "exchange": "coingecko",
            }

        except Exception as e:
            logger.error(f"CoinGecko API error for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV candlestick data.

        Args:
            symbol: CoinGecko coin ID (e.g., "bitcoin")
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of candles (max 365 for daily, 24 for hourly)
            start: Optional start time for time range
            end: Optional end time for time range

        Returns:
            List of OHLCV candles
        """
        try:
            session = await self._get_session()

            # Map interval to CoinGecko days parameter
            interval_map = {"1d": 1, "1h": 1, "4h": 1, "1m": 1, "5m": 1, "15m": 1, "30m": 1}

            # CoinGecko OHLC endpoint uses days parameter
            # For precise time ranges, we use market_chart with timestamp filtering
            if start or end:
                # Use market_chart for time range
                response = await session.get(
                    f"{self.base_url}/coins/{symbol.lower()}/market_chart",
                    params={
                        "vs_currency": "usd",
                        "days": "max",  # Get max data
                    },
                )
            else:
                # Use simple OHLC endpoint
                response = await session.get(
                    f"{self.base_url}/coins/{symbol.lower()}/ohlc",
                    params={"vs_currency": "usd", "days": str(interval_map.get(interval, 1))},
                )

            response.raise_for_status()
            data = response.json()

            if not data:
                return []

            # CoinGecko returns [timestamp, open, high, low, close]
            candles = []

            if start or end:
                # Parse market_chart data (prices array)
                prices = data.get("prices", [])
                for price_data in prices:
                    timestamp = datetime.fromtimestamp(price_data[0] / 1000)
                    price = Decimal(str(price_data[1]))

                    # Filter by time range
                    if start and timestamp < start:
                        continue
                    if end and timestamp > end:
                        continue

                    candles.append(
                        {
                            "timestamp": timestamp,
                            "open": price,
                            "high": price,  # CoinGecko OHLC doesn't provide H/L separately
                            "low": price,
                            "close": price,
                            "volume": Decimal("0"),  # Not available in this endpoint
                            "exchange": "coingecko",
                        }
                    )
            else:
                # Parse OHLC data
                for candle_data in data:
                    timestamp = datetime.fromtimestamp(candle_data[0] / 1000)

                    candles.append(
                        {
                            "timestamp": timestamp,
                            "open": Decimal(str(candle_data[1])),
                            "high": Decimal(str(candle_data[2])),
                            "low": Decimal(str(candle_data[3])),
                            "close": Decimal(str(candle_data[4])),
                            "volume": Decimal("0"),  # CoinGecko OHLC doesn't provide volume
                            "exchange": "coingecko",
                        }
                    )

            # Sort and limit
            candles.sort(key=lambda x: x["timestamp"], reverse=True)

            if limit:
                candles = candles[:limit]

            return candles

        except Exception as e:
            logger.error(f"CoinGecko OHLCV error for {symbol}: {e}")
            return []

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()


class KrakenDataSource:
    """
    Kraken data source (tertiary).

    Provides backup market data via REST API.
    """

    def __init__(self, config: DataSourceConfig):
        """
        Initialize Kraken data source.

        Args:
            config: Data source configuration
        """
        self.config = config
        self.base_url = "https://api.kraken.com"
        self._session: Optional[httpx.AsyncClient] = None

        logger.info("KrakenDataSource initialized")

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(timeout=self.config.timeout)
        return self._session

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticker data.

        Args:
            symbol: Trading pair (e.g., "XBTUSDT")

        Returns:
            Ticker data or None if error
        """
        try:
            session = await self._get_session()

            response = await session.get(
                f"{self.base_url}/0/public/Ticker", params={"pair": symbol}
            )
            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                logger.warning(f"Kraken API error: {data['error']}")
                return None

            # Get first result
            result = next(iter(data.get("result", {}).values()))

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
                "exchange": "kraken",
            }

        except Exception as e:
            logger.error(f"Kraken API error for {symbol}: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV candlestick data.

        Args:
            symbol: Trading pair (e.g., "XBTUSDT")
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of candles (max 720)
            start: Optional start time for time range
            end: Optional end time for time range

        Returns:
            List of OHLCV candles
        """
        try:
            session = await self._get_session()

            # Map interval to Kraken parameter
            interval_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
            kraken_interval = interval_map.get(interval, 60)

            params = {"pair": symbol, "interval": kraken_interval}

            if start:
                params["since"] = int(start.timestamp())

            response = await session.get(f"{self.base_url}/0/public/OHLC", params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                logger.warning(f"Kraken OHLCV error: {data['error']}")
                return []

            # Get first result
            result_data = next(iter(data.get("result", {}).values()), None)

            if not result_data:
                return []

            candles = []

            for candle_data in result_data:
                # Kraken returns: [time, open, high, low, close, vwap, volume, count]
                timestamp = datetime.fromtimestamp(candle_data[0])

                # Filter by time range
                if start and timestamp < start:
                    continue
                if end and timestamp > end:
                    continue

                candles.append(
                    {
                        "timestamp": timestamp,
                        "open": Decimal(str(candle_data[1])),
                        "high": Decimal(str(candle_data[2])),
                        "low": Decimal(str(candle_data[3])),
                        "close": Decimal(str(candle_data[4])),
                        "volume": Decimal(str(candle_data[6] or 0)),
                        "trades": int(candle_data[7] or 0),
                        "exchange": "kraken",
                    }
                )

            # Sort and limit
            candles.sort(key=lambda x: x["timestamp"], reverse=True)

            if limit:
                candles = candles[:limit]

            return candles

        except Exception as e:
            logger.error(f"Kraken OHLCV error for {symbol}: {e}")
            return []

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()


class MultiSourceManager:
    """
    Manages multiple data sources with automatic failover.

    Tries data sources in priority order and falls back to alternative
    sources when primary sources fail.
    """

    def __init__(self):
        """Initialize multi-source manager."""
        # Data source configurations
        self.sources: Dict[str, DataSourceConfig] = {
            "binance": DataSourceConfig(
                name="binance",
                priority=1,
                supports_websocket=True,
                supports_rest=True,
                supports_historical=True,
            ),
            "coingecko": DataSourceConfig(
                name="coingecko",
                priority=2,
                supports_websocket=False,
                supports_rest=True,
                supports_historical=True,
            ),
            "kraken": DataSourceConfig(
                name="kraken",
                priority=3,
                supports_websocket=False,
                supports_rest=True,
                supports_historical=True,
            ),
        }

        # Initialize data sources
        self._binance = BinanceDataSource(self.sources["binance"])
        self._coingecko = CoinGeckoDataSource(
            self.sources["coingecko"],
            api_key=None,  # Can be set via environment variable
        )
        self._kraken = KrakenDataSource(self.sources["kraken"])

        # Health tracking
        self.health: Dict[str, SourceHealth] = {
            "binance": SourceHealth(
                status=DataSourceStatus.AVAILABLE, last_check=datetime.utcnow()
            ),
            "coingecko": SourceHealth(
                status=DataSourceStatus.AVAILABLE, last_check=datetime.utcnow()
            ),
            "kraken": SourceHealth(status=DataSourceStatus.AVAILABLE, last_check=datetime.utcnow()),
        }

        logger.info("MultiSourceManager initialized with 3 data sources")

    def _get_source_instance(self, source_name: str):
        """Get data source instance by name."""
        if source_name == "binance":
            return self._binance
        elif source_name == "coingecko":
            return self._coingecko
        elif source_name == "kraken":
            return self._kraken
        else:
            raise ValueError(f"Unknown data source: {source_name}")

    def _get_sources_by_priority(self) -> List[str]:
        """Get enabled source names sorted by priority."""
        enabled_sources = [
            (name, config) for name, config in self.sources.items() if config.enabled
        ]
        enabled_sources.sort(key=lambda x: x[1].priority)
        return [name for name, _ in enabled_sources]

    async def get_ticker(
        self, symbol: str, preferred_sources: Optional[List[str]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get ticker data with automatic failover.

        Args:
            symbol: Trading symbol
            preferred_sources: Optional list of preferred sources (in order)

        Returns:
            Tuple of (ticker_data, source_name)
        """
        sources_to_try = preferred_sources or self._get_sources_by_priority()

        for source_name in sources_to_try:
            source_config = self.sources.get(source_name)
            if not source_config or not source_config.enabled:
                continue

            source_instance = self._get_source_instance(source_name)
            health = self.health[source_name]

            # Skip if source is unavailable
            if health.status == DataSourceStatus.UNAVAILABLE:
                logger.info(f"Skipping {source_name} (unavailable)")
                continue

            try:
                start_time = datetime.utcnow()

                # Try to fetch data
                ticker = await source_instance.get_ticker(symbol)

                response_time = (datetime.utcnow() - start_time).total_seconds()

                # Update health
                health.total_requests += 1
                health.last_check = datetime.utcnow()

                if ticker:
                    # Success
                    health.last_success = datetime.utcnow()
                    health.consecutive_successes += 1
                    health.consecutive_failures = 0
                    health.status = DataSourceStatus.AVAILABLE

                    # Update average response time
                    health.avg_response_time = (
                        health.avg_response_time * (health.total_requests - 1) + response_time
                    ) / health.total_requests

                    logger.info(f"Got ticker for {symbol} from {source_name}")
                    return ticker, source_name
                else:
                    # Failure
                    health.consecutive_failures += 1
                    health.failed_requests += 1
                    health.last_error = "No data returned"

                    # Mark as unavailable after 3 consecutive failures
                    if health.consecutive_failures >= 3:
                        health.status = DataSourceStatus.UNAVAILABLE
                        logger.warning(f"{source_name} marked as unavailable")

            except Exception as e:
                # Error
                health.consecutive_failures += 1
                health.failed_requests += 1
                health.last_error = str(e)

                logger.warning(f"{source_name} failed: {e}")

                # Mark as unavailable after 3 consecutive failures
                if health.consecutive_failures >= 3:
                    health.status = DataSourceStatus.UNAVAILABLE

        logger.error(f"All data sources failed for {symbol}")
        return None, None

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        preferred_sources: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get OHLCV data with automatic failover.

        Args:
            symbol: Trading symbol
            interval: Time interval
            limit: Number of candles
            preferred_sources: Optional list of preferred sources

        Returns:
            Tuple of (ohlcv_data, source_name)
        """
        sources_to_try = preferred_sources or self._get_sources_by_priority()

        for source_name in sources_to_try:
            source_config = self.sources.get(source_name)
            if not source_config or not source_config.enabled:
                continue

            # All sources now support OHLCV
            if not hasattr(source_instance, "get_ohlcv"):
                continue

            source_instance = self._get_source_instance(source_name)

            try:
                if hasattr(source_instance, "get_ohlcv"):
                    ohlcv = await source_instance.get_ohlcv(symbol, interval, limit)

                    if ohlcv:
                        logger.info(f"Got {len(ohlcv)} candles for {symbol} from {source_name}")
                        return ohlcv, source_name

            except Exception as e:
                logger.warning(f"{source_name} OHLCV failed: {e}")

        logger.error(f"All data sources failed for OHLCV {symbol}")
        return [], None

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all data sources.

        Returns:
            Dictionary of source health status
        """
        return {name: health.to_dict() for name, health in self.health.items()}

    async def health_check(self):
        """
        Perform health check on all data sources.

        Attempts to fetch data from each source to verify availability.
        """
        logger.info("Starting health check...")

        for source_name in self._get_sources_by_priority():
            source_instance = self._get_source_instance(source_name)
            health = self.health[source_name]

            try:
                # Try to fetch BTC price as health check
                test_symbol = "BTCUSDT" if source_name == "binance" else "bitcoin"
                ticker, _ = await self.get_ticker(test_symbol, [source_name])

                if ticker:
                    health.status = DataSourceStatus.AVAILABLE
                    health.last_success = datetime.utcnow()
                    health.consecutive_failures = 0
                    logger.info(f"{source_name} health check: PASSED")
                else:
                    health.consecutive_failures += 1
                    if health.consecutive_failures >= 3:
                        health.status = DataSourceStatus.UNAVAILABLE
                    logger.warning(f"{source_name} health check: FAILED")

            except Exception as e:
                health.consecutive_failures += 1
                health.last_error = str(e)
                if health.consecutive_failures >= 3:
                    health.status = DataSourceStatus.UNAVAILABLE
                logger.error(f"{source_name} health check: ERROR - {e}")

            health.last_check = datetime.utcnow()

    async def close(self):
        """Close all data source connections."""
        await self._binance.close()
        await self._coingecko.close()
        await self._kraken.close()
        logger.info("MultiSourceManager closed")


# Global manager instance
_manager: Optional[MultiSourceManager] = None


def get_multi_source_manager() -> MultiSourceManager:
    """
    Get the global multi-source manager instance.

    Returns:
        MultiSourceManager singleton
    """
    global _manager
    if _manager is None:
        _manager = MultiSourceManager()
    return _manager
