"""
Database Data Source Plugin.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from decimal import Decimal

from core.data_source import DataSource

logger = logging.getLogger(__name__)


class DatabaseDataSource(DataSource):
    """
    Data source for local database.
    """

    @property
    def name(self) -> str:
        return "database"

    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Not supported for historical database source.
        """
        logger.warning("get_current_price is not supported by the database data source.")
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
        Get historical OHLCV prices for a cryptocurrency from the database.
        """
        from database.connection import get_db_session
        from database.models.price import PriceModel

        try:
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
                        "open": p.open,
                        "high": p.high,
                        "low": p.low,
                        "close": p.close,
                        "volume": p.volume,
                    }
                    for p in reversed(results)
                ]
        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol} from database: {e}")
            return []
