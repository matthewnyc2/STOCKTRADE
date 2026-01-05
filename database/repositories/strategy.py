"""
Strategy repository implementations.
"""

from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database.base import BaseRepository
from database.models import (
    StrategyModel,
    StrategyLayerModel,
    StrategyFavoriteModel,
    StrategyShareModel,
    StrategyVersionModel,
)


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

    def get_templates(self) -> List[StrategyModel]:
        """Get all template strategies."""
        stmt = (
            self.query()
            .where(StrategyModel.is_template == True)
            .order_by(StrategyModel.name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_tag(self, tag: str) -> List[StrategyModel]:
        """
        Get strategies by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of strategies with the specified tag
        """
        stmt = (
            self.query()
            .where(func.json_extract(StrategyModel.tags, '$').contains(tag))
            .order_by(StrategyModel.created_at.desc())
        )
        # Alternative approach using text comparison
        strategies = self.get_all()
        return [s for s in strategies if tag in getattr(s, 'tags', [])]

    def get_by_tags(self, tags: List[str]) -> List[StrategyModel]:
        """
        Get strategies by multiple tags (OR logic).

        Args:
            tags: List of tags to filter by

        Returns:
            List of strategies with any of the specified tags
        """
        strategies = self.get_all()
        return [
            s for s in strategies
            if any(tag in getattr(s, 'tags', []) for tag in tags)
        ]

    def get_by_risk_level(self, risk_level: str) -> List[StrategyModel]:
        """
        Get strategies by risk level.

        Args:
            risk_level: Risk level (low/medium/high)

        Returns:
            List of strategies with the specified risk level
        """
        return self.get_many(risk_level=risk_level)

    def get_clones(self, parent_id: str) -> List[StrategyModel]:
        """
        Get all clones of a strategy.

        Args:
            parent_id: Parent strategy ID

        Returns:
            List of cloned strategies
        """
        return self.get_many(parent_id=parent_id)

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

    def search(self, query: str, limit: int = 50, tags: Optional[List[str]] = None,
               risk_level: Optional[str] = None, strategy_type: Optional[str] = None) -> List[StrategyModel]:
        """
        Advanced search strategies with multiple filters.

        Args:
            query: Search query for name/description
            limit: Maximum results
            tags: Optional tag filters
            risk_level: Optional risk level filter
            strategy_type: Optional strategy type filter

        Returns:
            List of matching strategies
        """
        stmt = self.query()

        # Text search
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    StrategyModel.name.ilike(search_pattern),
                    StrategyModel.description.ilike(search_pattern)
                )
            )

        # Tag filter
        if tags:
            # Get all and filter by tags since JSON querying varies by DB
            all_results = list(self.session.execute(stmt).scalars().all())
            tag_filtered = [
                s for s in all_results
                if any(tag in getattr(s, 'tags', []) for tag in tags)
            ]
            # Continue with filtered results
            if risk_level:
                tag_filtered = [s for s in tag_filtered if getattr(s, 'risk_level', None) == risk_level]
            if strategy_type:
                tag_filtered = [s for s in tag_filtered if s.type == strategy_type]
            return tag_filtered[:limit]

        # Risk level filter
        if risk_level:
            stmt = stmt.where(StrategyModel.risk_level == risk_level)

        # Strategy type filter
        if strategy_type:
            stmt = stmt.where(StrategyModel.type == strategy_type)

        stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())


class StrategyFavoriteRepository(BaseRepository[StrategyFavoriteModel]):
    """Repository for strategy favorite operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StrategyFavoriteModel, session)

    def get_user_favorites(self, user_id: str = "default") -> List[StrategyFavoriteModel]:
        """
        Get all favorites for a user.

        Args:
            user_id: User ID (default for non-auth)

        Returns:
            List of user's favorite strategies
        """
        return self.get_many(user_id=user_id)

    def get_favorite(self, user_id: str, strategy_id: str) -> Optional[StrategyFavoriteModel]:
        """
        Get a specific favorite entry.

        Args:
            user_id: User ID
            strategy_id: Strategy ID

        Returns:
            Favorite entry or None
        """
        return self.get_by(user_id=user_id, strategy_id=strategy_id)

    def add_favorite(self, user_id: str, strategy_id: str, notes: Optional[str] = None) -> StrategyFavoriteModel:
        """
        Add a strategy to user's favorites.

        Args:
            user_id: User ID
            strategy_id: Strategy ID
            notes: Optional user notes

        Returns:
            Created favorite entry
        """
        # Check if already exists
        existing = self.get_favorite(user_id, strategy_id)
        if existing:
            return existing

        return self.create(
            id=f"fav_{uuid4().hex[:12]}",
            user_id=user_id,
            strategy_id=strategy_id,
            notes=notes
        )

    def remove_favorite(self, user_id: str, strategy_id: str) -> bool:
        """
        Remove a strategy from user's favorites.

        Args:
            user_id: User ID
            strategy_id: Strategy ID

        Returns:
            True if removed, False if not found
        """
        favorite = self.get_favorite(user_id, strategy_id)
        if favorite:
            self.session.delete(favorite)
            self.session.flush()
            return True
        return False


class StrategyShareRepository(BaseRepository[StrategyShareModel]):
    """Repository for strategy share operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StrategyShareModel, session)

    def get_pending_shares(self, user_id: str = "default") -> List[StrategyShareModel]:
        """
        Get pending shares for a user.

        Args:
            user_id: User ID to receive shares

        Returns:
            List of pending shares
        """
        stmt = (
            self.query()
            .where(and_(
                StrategyShareModel.to_user_id == user_id,
                StrategyShareModel.accepted == False
            ))
            .order_by(StrategyShareModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_user_shares(self, user_id: str = "default") -> List[StrategyShareModel]:
        """
        Get all shares involving a user (sent or received).

        Args:
            user_id: User ID

        Returns:
            List of shares
        """
        stmt = (
            self.query()
            .where(or_(
                StrategyShareModel.from_user_id == user_id,
                StrategyShareModel.to_user_id == user_id
            ))
            .order_by(StrategyShareModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def create_share(self, from_user_id: str, to_user_id: str, strategy_id: str,
                     permissions: str = "view", message: Optional[str] = None) -> StrategyShareModel:
        """
        Create a new strategy share.

        Args:
            from_user_id: Sender user ID
            to_user_id: Receiver user ID
            strategy_id: Strategy to share
            permissions: Permission level (view/edit/clone)
            message: Optional message

        Returns:
            Created share entry
        """
        return self.create(
            id=f"share_{uuid4().hex[:12]}",
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            strategy_id=strategy_id,
            permissions=permissions,
            message=message,
            accepted=False
        )

    def accept_share(self, share_id: str) -> Optional[StrategyShareModel]:
        """
        Accept a strategy share.

        Args:
            share_id: Share ID

        Returns:
            Updated share or None
        """
        share = self.get(share_id)
        if share:
            share.accepted = True
            share.accepted_at = datetime.utcnow()
            self.session.flush()
            self.session.refresh(share)
            return share
        return None


class StrategyVersionRepository(BaseRepository[StrategyVersionModel]):
    """Repository for strategy version operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(StrategyVersionModel, session)

    def get_version_history(self, strategy_id: str) -> List[StrategyVersionModel]:
        """
        Get version history for a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            List of versions ordered by version number
        """
        stmt = (
            self.query()
            .where(StrategyVersionModel.strategy_id == strategy_id)
            .order_by(StrategyVersionModel.version_number.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_latest_version(self, strategy_id: str) -> Optional[StrategyVersionModel]:
        """
        Get the latest version of a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            Latest version or None
        """
        stmt = (
            self.query()
            .where(StrategyVersionModel.strategy_id == strategy_id)
            .order_by(StrategyVersionModel.version_number.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_version(self, strategy: StrategyModel, change_description: Optional[str] = None,
                       created_by: str = "system") -> StrategyVersionModel:
        """
        Create a new version snapshot of a strategy.

        Args:
            strategy: Strategy model to version
            change_description: Description of changes
            created_by: User creating the version

        Returns:
            Created version entry
        """
        # Get next version number
        latest = self.get_latest_version(strategy.id)
        next_version = (latest.version_number + 1) if latest else 1

        return self.create(
            id=f"ver_{uuid4().hex[:12]}",
            strategy_id=strategy.id,
            version_number=next_version,
            name=strategy.name,
            description=strategy.description,
            type=strategy.type,
            parameters=strategy.parameters.copy(),
            layers=strategy.layers.copy(),
            tags=getattr(strategy, 'tags', []).copy(),
            risk_level=getattr(strategy, 'risk_level', None),
            change_description=change_description,
            created_by=created_by
        )

    def restore_version(self, strategy_id: str, version_number: int,
                        strategy_repo: StrategyRepository) -> Optional[StrategyModel]:
        """
        Restore a strategy to a previous version.

        Args:
            strategy_id: Strategy ID
            version_number: Version to restore
            strategy_repo: Strategy repository instance

        Returns:
            Updated strategy or None
        """
        # Get the version
        stmt = (
            self.query()
            .where(and_(
                StrategyVersionModel.strategy_id == strategy_id,
                StrategyVersionModel.version_number == version_number
            ))
        )
        version = self.session.execute(stmt).scalar_one_or_none()

        if not version:
            return None

        # Restore strategy
        return strategy_repo.update(
            strategy_id,
            name=version.name,
            description=version.description,
            parameters=version.parameters.copy(),
            layers=version.layers.copy(),
            tags=version.tags.copy(),
            risk_level=version.risk_level
        )


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
