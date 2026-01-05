"""
ML Package - Machine Learning Model Training & Prediction System.

Provides comprehensive ML capabilities for trading strategies:
- Feature engineering with 50+ technical indicators
- LSTM model training
- Ensemble model support
- Model versioning and storage
- Background training with progress tracking
- Prediction generation for live trading
"""

# Models
from .models import LSTMLayer, LSTMModel

# Training Engine
from .engine import TrainingEngine

# Feature Engineering
from .features import FeatureEngine

# Factory and Data Structures
from .factory import (
    MLFactory,
    TrainingConfig,
    TrainingProgress,
    TrainingTaskStatus,
    PredictionResult,
    PredictionType,
    get_ml_factory,
)

__all__ = [
    # Models
    "LSTMLayer",
    "LSTMModel",
    # Training
    "TrainingEngine",
    # Features
    "FeatureEngine",
    # Factory
    "MLFactory",
    "TrainingConfig",
    "TrainingProgress",
    "TrainingTaskStatus",
    "PredictionResult",
    "PredictionType",
    "get_ml_factory",
]
