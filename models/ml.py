"""
ML-related Pydantic models.

Defines machine learning model metadata and configuration.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ModelType(str, Enum):
    """Enum for ML model types."""

    LSTM = "lstm"
    TRANSFORMER = "transformer"
    XGBOOST = "xgboost"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    """Enum for ML model status."""

    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    FAILED = "failed"


class MLModel(BaseModel):
    """
    Represents a machine learning model.

    Contains model metadata, training information, and performance metrics.
    """

    id: str = Field(default_factory=lambda: f"ml_{uuid4().hex[:8]}")
    name: str = Field(min_length=1, max_length=200)
    model_type: ModelType
    features: list[str] = Field(default_factory=list, description="Feature set used")
    training_start: Optional[datetime] = Field(default=None)
    training_end: Optional[datetime] = Field(default=None)
    accuracy: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ModelStatus = Field(default=ModelStatus.READY)
    parameters: dict = Field(default_factory=dict, description="Model hyperparameters")
    metrics: dict = Field(default_factory=dict, description="Additional model metrics")

    # Extended fields for ML Factory
    symbols: Optional[list[str]] = Field(default=None, description="Trading symbols trained on")
    timeframe: Optional[str] = Field(default=None, description="Data timeframe")
    sequence_length: Optional[int] = Field(default=None, description="Input sequence length")
    prediction_horizon: Optional[int] = Field(default=None, description="Prediction horizon")
    target_type: Optional[str] = Field(default=None, description="Target prediction type")
    model_path: Optional[str] = Field(default=None, description="Path to saved model")
    is_deployed: bool = Field(default=False, description="Whether model is deployed for signals")
    deployed_at: Optional[datetime] = Field(default=None, description="Deployment timestamp")

    @field_validator("training_end")
    @classmethod
    def training_end_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate training end is after training start."""
        if v is not None and info.data.get("training_start") is not None:
            if v < info.data["training_start"]:
                raise ValueError("training_end must be after training_start")
        return v


class TrainingRequest(BaseModel):
    """Request body for starting model training."""
    name: str = Field(min_length=1, max_length=200)
    model_type: ModelType = Field(default=ModelType.LSTM)
    symbols: list[str] = Field(min_length=1)
    start_date: datetime
    end_date: datetime
    timeframe: str = Field(default="1h")
    sequence_length: int = Field(default=60, ge=10, le=500)
    prediction_horizon: int = Field(default=1, ge=1, le=10)
    train_split: float = Field(default=0.8, ge=0.5, le=0.95)
    batch_size: int = Field(default=32, ge=1, le=256)
    epochs: int = Field(default=50, ge=1, le=500)
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1)
    early_stopping_patience: int = Field(default=10, ge=1, le=50)
    feature_selection: list[str] = Field(
        default_factory=lambda: ["price", "volume", "momentum", "volatility", "trend"]
    )
    target_type: str = Field(default="direction")
    threshold: float = Field(default=0.001, ge=0.0, le=0.1)


class PredictionRequest(BaseModel):
    """Request body for generating predictions."""
    model_id: str
    symbol: str
    lookback_periods: int = Field(default=100, ge=50, le=500)


class TrainingProgressResponse(BaseModel):
    """Response with training progress information."""
    task_id: str
    model_id: str
    status: str
    current_epoch: int
    total_epochs: int
    train_loss: float
    val_loss: float
    train_accuracy: float
    val_accuracy: float
    loss_history: list[float]
    val_loss_history: list[float]
    accuracy_history: list[float]
    val_accuracy_history: list[float]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    metrics: dict
