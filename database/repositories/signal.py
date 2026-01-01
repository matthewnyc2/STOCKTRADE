"""
Signal repository implementations.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import SignalModel, LayerSignalModel


class SignalRepository(BaseRepository[SignalModel]):
    """Repository for signal operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(SignalModel, session)

    def get_by_strategy(self, strategy_id: str, limit: int = 100) -> List[SignalModel]:
        """Get recent signals for a strategy."""
        stmt = (
            self.query()
            .where(SignalModel.strategy_id == strategy_id)
            .order_by(SignalModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[SignalModel]:
        """Get recent signals for a symbol."""
        stmt = (
            self.query()
            .where(SignalModel.symbol == symbol.upper())
            .order_by(SignalModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_latest_for_symbol(self, symbol: str) -> SignalModel | None:
        """Get the latest signal for a symbol."""
        stmt = (
            self.query()
            .where(SignalModel.symbol == symbol.upper())
            .order_by(SignalModel.timestamp.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_type(
        self, signal_type: str, limit: int = 100
    ) -> List[SignalModel]:
        """Get recent signals by type."""
        stmt = (
            self.query()
            .where(SignalModel.signal_type == signal_type)
            .order_by(SignalModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[SignalModel]:
        """Get signals from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            self.query()
            .where(SignalModel.timestamp >= since)
            .order_by(SignalModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_strategy_and_symbol(
        self, strategy_id: str, symbol: str, limit: int = 100
    ) -> List[SignalModel]:
        """Get signals for a strategy and symbol."""
        stmt = (
            self.query()
            .where(
                SignalModel.strategy_id == strategy_id,
                SignalModel.symbol == symbol.upper(),
            )
            .order_by(SignalModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


class LayerSignalRepository(BaseRepository[LayerSignalModel]):
    """Repository for layer signal operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(LayerSignalModel, session)

    def get_by_layer(self, layer_id: str, limit: int = 100) -> List[LayerSignalModel]:
        """Get recent signals for a layer."""
        stmt = (
            self.query()
            .where(LayerSignalModel.layer_id == layer_id)
            .order_by(LayerSignalModel.id.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
