"""
ML model repository implementations.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import MLModelModel


class MLModelRepository(BaseRepository[MLModelModel]):
    """Repository for ML model operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(MLModelModel, session)

    def get_by_name(self, name: str) -> Optional[MLModelModel]:
        """Get model by name."""
        return self.get_by(name=name)

    def get_by_type(self, model_type: str) -> List[MLModelModel]:
        """Get models by type."""
        stmt = (
            self.query()
            .where(MLModelModel.model_type == model_type)
            .order_by(MLModelModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_status(self, status: str) -> List[MLModelModel]:
        """Get models by status."""
        stmt = (
            self.query()
            .where(MLModelModel.status == status)
            .order_by(MLModelModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_deployed_models(self) -> List[MLModelModel]:
        """Get all deployed models."""
        return self.get_by_status("deployed")

    def get_ready_models(self) -> List[MLModelModel]:
        """Get all ready (not deployed) models."""
        return self.get_by_status("ready")

    def get_training_models(self) -> List[MLModelModel]:
        """Get all models currently training."""
        return self.get_by_status("training")

    def get_best_models(self, model_type: str | None = None, limit: int = 10) -> List[MLModelModel]:
        """Get best performing models by accuracy."""
        stmt = (
            self.query()
            .where(MLModelModel.accuracy.isnot(None))
            .order_by(MLModelModel.accuracy.desc())
            .limit(limit)
        )
        if model_type:
            stmt = stmt.where(MLModelModel.model_type == model_type)
        return list(self.session.execute(stmt).scalars().all())

    def search(self, query: str, limit: int = 50) -> List[MLModelModel]:
        """Search models by name."""
        stmt = (
            self.query()
            .where(MLModelModel.name.ilike(f"%{query}%"))
            .order_by(MLModelModel.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
