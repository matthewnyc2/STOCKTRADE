"""
AI Reasoning-related SQLAlchemy ORM models.

For preserving AI thinking and chain-of-thought reasoning.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class AIReasoningSessionModel(BaseModel):
    """
    SQLAlchemy model for AI reasoning sessions.

    Stores AI thinking, chain-of-thought, and reasoning content
    for analysis and audit purposes.
    """

    __tablename__ = "ai_reasoning_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    reasoning_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
