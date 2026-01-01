"""
Whale repository implementations.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import WhaleModel, WhaleActivityModel, WhaleConstellationModel


class WhaleRepository(BaseRepository[WhaleModel]):
    """Repository for whale wallet operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(WhaleModel, session)

    def get_by_tier(self, tier: str, limit: int = 100) -> List[WhaleModel]:
        """Get whales by tier."""
        stmt = (
            self.query()
            .where(WhaleModel.tier == tier)
            .order_by(WhaleModel.holdings_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_pattern(self, pattern_type: str, limit: int = 100) -> List[WhaleModel]:
        """Get whales by behavior pattern."""
        stmt = (
            self.query()
            .where(WhaleModel.pattern_type == pattern_type)
            .order_by(WhaleModel.holdings_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_active_whales(self, hours: int = 24) -> List[WhaleModel]:
        """Get whales with recent activity."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            self.query()
            .where(WhaleModel.last_activity >= since)
            .order_by(WhaleModel.holdings_usd.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_top_holders(self, limit: int = 50) -> List[WhaleModel]:
        """Get top whales by holdings."""
        stmt = (
            self.query()
            .order_by(WhaleModel.holdings_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def search_by_label(self, query: str, limit: int = 50) -> List[WhaleModel]:
        """Search whales by label."""
        stmt = (
            self.query()
            .where(WhaleModel.label.ilike(f"%{query}%"))
            .order_by(WhaleModel.holdings_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


class WhaleActivityRepository(BaseRepository[WhaleActivityModel]):
    """Repository for whale activity operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(WhaleActivityModel, session)

    def get_by_whale(self, whale_address: str, limit: int = 100) -> List[WhaleActivityModel]:
        """Get recent activity for a whale."""
        stmt = (
            self.query()
            .where(WhaleActivityModel.whale_address == whale_address)
            .order_by(WhaleActivityModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_whale_and_symbol(self, whale_address: str, symbol: str, limit: int = 100) -> List[WhaleActivityModel]:
        """Get recent activity for a whale and symbol."""
        stmt = (
            self.query()
            .where(
                WhaleActivityModel.whale_address == whale_address,
                WhaleActivityModel.symbol == symbol.upper(),
            )
            .order_by(WhaleActivityModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[WhaleActivityModel]:
        """Get recent activity for a symbol."""
        stmt = (
            self.query()
            .where(WhaleActivityModel.symbol == symbol.upper())
            .order_by(WhaleActivityModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_action(self, action: str, limit: int = 100) -> List[WhaleActivityModel]:
        """Get recent activity by action type."""
        stmt = (
            self.query()
            .where(WhaleActivityModel.action == action)
            .order_by(WhaleActivityModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[WhaleActivityModel]:
        """Get activity from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            self.query()
            .where(WhaleActivityModel.timestamp >= since)
            .order_by(WhaleActivityModel.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_large_transactions(self, min_amount_usd: float = 100000, limit: int = 100) -> List[WhaleActivityModel]:
        """Get large whale transactions above a threshold."""
        stmt = (
            self.query()
            .where(WhaleActivityModel.amount_usd >= min_amount_usd)
            .order_by(WhaleActivityModel.amount_usd.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_whale(self, whale_address: str) -> int:
        """Delete all activity for a whale. Returns count deleted."""
        stmt = self.query().where(WhaleActivityModel.whale_address == whale_address)
        count = self.session.execute(stmt).scalars().all()
        for activity in count:
            self.session.delete(activity)
        return len(count)


class WhaleConstellationRepository(BaseRepository[WhaleConstellationModel]):
    """Repository for whale constellation operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(WhaleConstellationModel, session)

    def get_by_symbol(self, symbol: str) -> List[WhaleConstellationModel]:
        """Get constellations for a symbol."""
        stmt = (
            self.query()
            .where(WhaleConstellationModel.symbol == symbol.upper())
            .order_by(WhaleConstellationModel.detected_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_type(self, constellation_type: str) -> List[WhaleConstellationModel]:
        """Get constellations by type."""
        stmt = (
            self.query()
            .where(WhaleConstellationModel.type == constellation_type)
            .order_by(WhaleConstellationModel.detected_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_recent(self, hours: int = 24) -> List[WhaleConstellationModel]:
        """Get constellations from the last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            self.query()
            .where(WhaleConstellationModel.detected_at >= since)
            .order_by(WhaleConstellationModel.detected_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_high_confidence(self, min_confidence: float = 0.7) -> List[WhaleConstellationModel]:
        """Get high confidence constellations."""
        stmt = (
            self.query()
            .where(WhaleConstellationModel.confidence >= min_confidence)
            .order_by(WhaleConstellationModel.confidence.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_active(self, min_confidence: float = 0.5, limit: int = 50) -> List[WhaleConstellationModel]:
        """Get active constellations above confidence threshold."""
        stmt = (
            self.query()
            .where(WhaleConstellationModel.confidence >= min_confidence)
            .order_by(WhaleConstellationModel.detected_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
