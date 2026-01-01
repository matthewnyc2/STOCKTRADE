"""
ML-related SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class MLModelModel(BaseModel):
    """
    SQLAlchemy model for machine learning models.

    Contains model metadata, training information, and performance metrics.
    """

    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    model_type: Mapped[str] = mapped_column(String(50))  # ModelType enum
    features: Mapped[list] = mapped_column(JSON, default=list)
    training_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    training_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50))  # ModelStatus enum
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    # Extended fields for ML Factory
    symbols: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    timeframe: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sequence_length: Mapped[Optional[int]] = mapped_column(nullable=True)
    prediction_horizon: Mapped[Optional[int]] = mapped_column(nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deployed: Mapped[bool] = mapped_column(default=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
