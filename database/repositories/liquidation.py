"""
Liquidation repository implementations.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import LiquidationModel, CascadeModel


class LiquidationRepository(BaseRepository[LiquidationModel]):
    """Repository for liquidation operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(LiquidationModel, session)

    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[LiquidationModel]:
        """Get recent liquidations for a symbol."""
        stmt = (
            self.query()
            .where(LiquidationModel.symbol == symbol.upper())
            .order_by(LiquidationModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_symbol_and_time_range(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[LiquidationModel]:
        """Get liquidations for a symbol within a time range."""
        stmt = (
            self.query()
            .where(
                LiquidationModel.symbol == symbol.upper(),
                LiquidationModel.timestamp >= start_time,
                LiquidationModel.timestamp <= end_time,
            )
            .order_by(LiquidationModel.timestamp.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_exchange(self, exchange: str, limit: int = 100) -> List[LiquidationModel]:
        """Get recent liquidations from an exchange."""
        stmt = (
            self.query()
            .where(LiquidationModel.exchange == exchange.lower())
            .order_by(LiquidationModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_side(self, side: str, limit: int = 100) -> List[LiquidationModel]:
        """Get recent liquidations by side (long/short)."""
        stmt = (
            self.query()
            .where(LiquidationModel.side == side.lower())
            .order_by(LiquidationModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_since(self, since: datetime, limit: int = 1000) -> List[LiquidationModel]:
        """Get liquidations since a timestamp."""
        stmt = (
            self.query()
            .where(LiquidationModel.timestamp >= since)
            .order_by(LiquidationModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_large_liquidations(
        self,
        min_amount_usd: float = 1000000,
        limit: int = 100,
    ) -> List[LiquidationModel]:
        """Get large liquidations above a threshold."""
        stmt = (
            self.query()
            .where(LiquidationModel.amount_usd >= min_amount_usd)
            .order_by(LiquidationModel.amount_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_recent_hours(self, hours: int = 24, limit: int = 1000) -> List[LiquidationModel]:
        """Get liquidations from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.get_since(since, limit)

    def get_stats_by_symbol(
        self,
        symbol: str,
        hours: int = 24,
    ) -> dict:
        """Get aggregated stats for a symbol."""
        since = datetime.utcnow() - timedelta(hours=hours)

        stmt = (
            self.query()
            .where(
                LiquidationModel.symbol == symbol.upper(),
                LiquidationModel.timestamp >= since,
            )
        )

        liquidations = list(self.session.execute(stmt).scalars().all())

        if not liquidations:
            return {
                "total_amount": 0,
                "long_amount": 0,
                "short_amount": 0,
                "count": 0,
                "avg_amount": 0,
                "largest": 0,
            }

        total = sum(liq.amount_usd for liq in liquidations)
        long_total = sum(liq.amount_usd for liq in liquidations if liq.side == "long")
        short_total = sum(liq.amount_usd for liq in liquidations if liq.side == "short")
        largest = max(liq.amount_usd for liq in liquidations)

        return {
            "total_amount": total,
            "long_amount": long_total,
            "short_amount": short_total,
            "count": len(liquidations),
            "avg_amount": total / len(liquidations),
            "largest": largest,
        }


class CascadeRepository(BaseRepository[CascadeModel]):
    """Repository for cascade event operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(CascadeModel, session)

    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[CascadeModel]:
        """Get recent cascades for a symbol."""
        stmt = (
            self.query()
            .where(CascadeModel.symbol == symbol.upper())
            .order_by(CascadeModel.start_time.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_severity(self, severity: str, limit: int = 100) -> List[CascadeModel]:
        """Get cascades by severity level."""
        stmt = (
            self.query()
            .where(CascadeModel.severity == severity.lower())
            .order_by(CascadeModel.start_time.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_since(self, since: datetime, limit: int = 100) -> List[CascadeModel]:
        """Get cascades since a timestamp."""
        stmt = (
            self.query()
            .where(CascadeModel.start_time >= since)
            .order_by(CascadeModel.start_time.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_recent_hours(self, hours: int = 24, limit: int = 100) -> List[CascadeModel]:
        """Get cascades from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.get_since(since, limit)

    def get_active(self, min_hours_ago: int = 1, limit: int = 50) -> List[CascadeModel]:
        """Get recently active cascades."""
        since = datetime.utcnow() - timedelta(hours=min_hours_ago)
        stmt = (
            self.query()
            .where(CascadeModel.start_time >= since)
            .order_by(CascadeModel.confidence.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_high_severity(self, limit: int = 50) -> List[CascadeModel]:
        """Get high and extreme severity cascades."""
        stmt = (
            self.query()
            .where(CascadeModel.severity.in_(["high", "extreme"]))
            .order_by(CascadeModel.start_time.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
