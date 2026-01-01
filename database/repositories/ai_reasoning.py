"""
AI Reasoning repository implementations.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import AIReasoningSessionModel


class AIReasoningSessionRepository(BaseRepository[AIReasoningSessionModel]):
    """Repository for AI reasoning session operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(AIReasoningSessionModel, session)

    def get_by_session_id(self, session_id: str) -> AIReasoningSessionModel | None:
        """Get reasoning session by session ID."""
        return self.get_by(session_id=session_id)

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[AIReasoningSessionModel]:
        """Get recent reasoning sessions."""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            self.query()
            .where(AIReasoningSessionModel.created_at >= since)
            .order_by(AIReasoningSessionModel.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def search_reasoning(self, query: str, limit: int = 50) -> List[AIReasoningSessionModel]:
        """Search reasoning content."""
        stmt = (
            self.query()
            .where(AIReasoningSessionModel.reasoning_content.ilike(f"%{query}%"))
            .order_by(AIReasoningSessionModel.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
