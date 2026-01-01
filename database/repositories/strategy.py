"""
Strategy repository implementations.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import StrategyModel, StrategyLayerModel


class StrategyRepository(BaseRepository[StrategyModel]):
    """Repository for strategy operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StrategyModel, session)

    def get_by_name(self, name: str) -> Optional[StrategyModel]:
        """Get strategy by name."""
        return self.get_by(name=name)

    def get_by_type(self, strategy_type: str) -> List[StrategyModel]:
        """Get strategies by type."""
        return self.get_many(type=strategy_type)

    def get_by_status(self, status: str) -> List[StrategyModel]:
        """Get strategies by status."""
        return self.get_many(status=status)

    def get_active_strategies(self) -> List[StrategyModel]:
        """Get all active strategies."""
        return self.get_by_status("active")

    def get_user_strategies(self, user_id: Optional[str] = None) -> List[StrategyModel]:
        """
        Get strategies for a specific user.

        Note: Currently user_id is not implemented, so this returns all
        non-template strategies. When auth is added, this will filter by user_id.

        Args:
            user_id: Optional user ID to filter by (not yet implemented)

        Returns:
            List of non-template strategies belonging to the user
        """
        # For now, return all non-template strategies
        # When auth is added, filter by user_id
        stmt = (
            self.query()
            .where(StrategyModel.is_template == False)
            .order_by(StrategyModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def search(self, query: str, limit: int = 50) -> List[StrategyModel]:
        """Search strategies by name or description."""
        stmt = (
            self.query()
            .where(
                (StrategyModel.name.ilike(f"%{query}%"))
                | (StrategyModel.description.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


class StrategyLayerRepository(BaseRepository[StrategyLayerModel]):
    """Repository for strategy layer operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StrategyLayerModel, session)

    def get_by_strategy(self, strategy_id: str) -> List[StrategyLayerModel]:
        """Get all layers for a strategy, ordered by layer_order."""
        stmt = (
            self.query()
            .where(StrategyLayerModel.strategy_id == strategy_id)
            .order_by(StrategyLayerModel.layer_order)
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_strategy(self, strategy_id: str) -> int:
        """Delete all layers for a strategy. Returns count deleted."""
        stmt = (
            self.query()
            .where(StrategyLayerModel.strategy_id == strategy_id)
        )
        count = self.session.execute(stmt).scalars().all()
        for layer in count:
            self.session.delete(layer)
        return len(count)
