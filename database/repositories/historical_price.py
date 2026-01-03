"""
Historical Price Repository.

This repository handles all database operations for the HistoricalPrice model.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.base import BaseRepository
from database.models import HistoricalPriceModel
from models import HistoricalPrice

class HistoricalPriceRepository(BaseRepository[HistoricalPriceModel]):
    """
    Repository for historical price data.
    """

    def __init__(self, session: Session):
        super().__init__(HistoricalPriceModel, session)

    def get_by_symbol_and_timeframe(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[HistoricalPrice]:
        """
        Get historical prices for a given symbol and timeframe.
        """
        statement = (
            select(self.model)
            .where(self.model.symbol == symbol, self.model.timeframe == timeframe)
            .order_by(self.model.timestamp.desc())
            .limit(limit)
        )
        results = self.session.execute(statement).scalars().all()
        return [HistoricalPrice.from_orm(result) for result in results]
