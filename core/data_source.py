"""
Abstract Base Class for Data Source Plugins.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class DataSource(ABC):
    """
    Abstract interface for a data source plugin.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique name of the data source.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price for a cryptocurrency symbol.

        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")

        Returns:
            Dictionary with price data or None if error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_historical_prices(
        self,
        symbol: str,
        timeframe: str = "1h",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV prices for a cryptocurrency.

        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
            timeframe: Time frame (e.g., "1h", "1d")
            start: Start datetime
            end: End datetime
            limit: Maximum number of candles to return

        Returns:
            List of OHLCV dictionaries.
        """
        raise NotImplementedError
