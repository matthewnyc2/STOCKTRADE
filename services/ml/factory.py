"""
ML Factory - Orchestration and Data Structures.

Main service orchestrator for model training and prediction.
"""

import json
import pickle
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import numpy.typing as npt

from database.connection import get_db_context
from models.ml import MLModel, ModelStatus, ModelType

from .models import LSTMModel
from .engine import TrainingEngine
from .features import FeatureEngine


class TrainingTaskStatus(str, Enum):
    """Status of a training task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PredictionType(str, Enum):
    """Types of predictions supported."""

    DIRECTION = "direction"  # Binary: up/down
    MAGNITUDE = "magnitude"  # Regression: price change %


@dataclass
class TrainingConfig:
    """Configuration for model training."""

    # Data parameters
    symbols: list[str]
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"

    # Model parameters
    model_type: ModelType = ModelType.LSTM
    sequence_length: int = 60  # Lookback period
    prediction_horizon: int = 1  # Predict N periods ahead

    # Training parameters
    train_split: float = 0.8  # 80% train, 20% validation
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.001
    early_stopping_patience: int = 10
    early_stopping_min_delta: float = 0.0001

    # Feature selection
    features: list[str] = field(default_factory=list)
    feature_selection: list[str] = field(
        default_factory=lambda: ["price", "volume", "momentum", "volatility", "trend"]
    )

    # Target
    target_type: PredictionType = PredictionType.DIRECTION
    threshold: float = 0.001  # Price change threshold for classification

    # Ensemble parameters
    n_estimators: int = 5
    ensemble_method: str = "voting"  # voting, stacking, averaging

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbols": self.symbols,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "timeframe": self.timeframe,
            "model_type": self.model_type.value,
            "sequence_length": self.sequence_length,
            "prediction_horizon": self.prediction_horizon,
            "train_split": self.train_split,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "early_stopping_patience": self.early_stopping_patience,
            "early_stopping_min_delta": self.early_stopping_min_delta,
            "features": self.features,
            "feature_selection": self.feature_selection,
            "target_type": self.target_type.value,
            "threshold": self.threshold,
            "n_estimators": self.n_estimators,
            "ensemble_method": self.ensemble_method,
        }


@dataclass
class TrainingProgress:
    """Progress tracking for training tasks."""

    task_id: str
    model_id: str
    status: TrainingTaskStatus
    current_epoch: int = 0
    total_epochs: int = 0
    train_loss: float = 0.0
    val_loss: float = 0.0
    train_accuracy: float = 0.0
    val_accuracy: float = 0.0
    loss_history: list[float] = field(default_factory=list)
    val_loss_history: list[float] = field(default_factory=list)
    accuracy_history: list[float] = field(default_factory=list)
    val_accuracy_history: list[float] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "model_id": self.model_id,
            "status": self.status.value,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "train_loss": self.train_loss,
            "val_loss": self.val_loss,
            "train_accuracy": self.train_accuracy,
            "val_accuracy": self.val_accuracy,
            "loss_history": self.loss_history,
            "val_loss_history": self.val_loss_history,
            "accuracy_history": self.accuracy_history,
            "val_accuracy_history": self.val_accuracy_history,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "metrics": self.metrics,
        }


@dataclass
class PredictionResult:
    """Result of model prediction."""

    model_id: str
    symbol: str
    timestamp: datetime
    prediction: float
    confidence: float
    prediction_type: PredictionType
    features_used: list[str]
    model_version: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "prediction": self.prediction,
            "confidence": self.confidence,
            "prediction_type": self.prediction_type.value,
            "features_used": self.features_used,
            "model_version": self.model_version,
        }


class MLFactory:
    """
    Machine Learning Factory for trading strategy development.

    Features:
    - Feature engineering with 50+ indicators
    - LSTM model training
    - Ensemble model support
    - Model versioning and storage
    - Background training with progress tracking
    - Prediction generation for live trading
    """

    def __init__(self, models_dir: str = "./data/models"):
        """
        Initialize ML Factory.

        Args:
            models_dir: Directory for storing trained models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Training tasks storage (in production, use Redis/DB)
        self.training_tasks: dict[str, TrainingProgress] = {}

        # Thread pool for background training
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Feature engine
        self.feature_engine = FeatureEngine()

        # Cached models
        self.loaded_models: dict[str, LSTMModel] = {}

    def get_available_features(self) -> list[str]:
        """Get list of all available features."""
        return FeatureEngine.get_all_features()

    def get_feature_groups(self) -> dict[str, list[str]]:
        """Get feature groups."""
        return {
            "price": FeatureEngine.PRICE_FEATURES,
            "volume": FeatureEngine.VOLUME_FEATURES,
            "momentum": FeatureEngine.MOMENTUM_FEATURES,
            "trend": FeatureEngine.TREND_FEATURES,
            "volatility": FeatureEngine.VOLATILITY_FEATURES,
            "time": FeatureEngine.TIME_FEATURES,
        }

    def train_model(
        self,
        config: TrainingConfig,
    ) -> str:
        """
        Train a model with the given configuration.

        Args:
            config: Training configuration

        Returns:
            task_id: Training task ID for progress tracking
        """
        # Generate task ID
        task_id = f"task_{uuid4().hex[:12]}"

        # Create model ID
        model_id = f"ml_{uuid4().hex[:8]}"

        # Create progress tracker
        progress = TrainingProgress(
            task_id=task_id,
            model_id=model_id,
            status=TrainingTaskStatus.PENDING,
            total_epochs=config.epochs,
        )
        self.training_tasks[task_id] = progress

        # Submit background training task
        self.executor.submit(self._train_model_task, config, task_id, progress)

        return task_id

    def _train_model_task(
        self,
        config: TrainingConfig,
        task_id: str,
        progress: TrainingProgress,
    ) -> None:
        """
        Execute model training in background.

        Args:
            config: Training configuration
            task_id: Task ID
            progress: Progress tracker
        """
        try:
            # Update status
            progress.status = TrainingTaskStatus.RUNNING
            progress.started_at = datetime.utcnow()

            # Load data
            data = self._load_training_data(
                config.symbols,
                config.start_date,
                config.end_date,
                config.timeframe,
            )

            if not data:
                raise ValueError("No training data available")

            # Feature engineering
            feature_matrix = self.feature_engine.calculate_features(
                data,
                config.feature_selection,
            )

            # Create targets (price direction)
            closes = np.array([float(d["close"]) for d in data])
            returns = np.diff(closes, prepend=closes[0])
            targets = (returns > config.threshold).astype(float)

            # Create sequences
            X, y = self.feature_engine.create_sequences(
                feature_matrix,
                targets,
                config.sequence_length,
                config.prediction_horizon,
            )

            if len(X) == 0:
                raise ValueError("Insufficient data for sequence creation")

            # Split data
            split_idx = int(len(X) * config.train_split)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Create model
            n_features = X.shape[2]
            model = LSTMModel(
                input_size=n_features,
                hidden_sizes=[128, 64, 32],
                output_size=1,
                dropout=0.2,
            )

            # Create training engine
            engine = TrainingEngine(model, learning_rate=config.learning_rate)

            # Progress callback
            def progress_callback(epoch, total_epochs, train_loss, val_loss, train_acc, val_acc):
                progress.current_epoch = epoch + 1
                progress.train_loss = train_loss
                progress.val_loss = val_loss
                progress.train_accuracy = train_acc
                progress.val_accuracy = val_acc
                progress.loss_history.append(train_loss)
                progress.val_loss_history.append(val_loss)
                progress.accuracy_history.append(train_acc)
                progress.val_accuracy_history.append(val_acc)

            # Train model
            metrics = engine.train(
                X_train,
                y_train,
                X_val,
                y_val,
                epochs=config.epochs,
                batch_size=config.batch_size,
                early_stopping_patience=config.early_stopping_patience,
                progress_callback=progress_callback,
            )

            # Save model
            model_path = self._save_model(
                model_id,
                model,
                config,
                metrics,
                X.shape[2],
            )

            # Update progress
            progress.status = TrainingTaskStatus.COMPLETED
            progress.completed_at = datetime.utcnow()
            progress.metrics = {
                "model_path": model_path,
                "num_params": model.get_num_params(),
                "training_samples": len(X_train),
                "validation_samples": len(X_val),
                "num_features": X.shape[2],
                **metrics,
            }

            # Save to database
            self._save_model_to_db(model_id, config, metrics, progress)

        except Exception as e:
            progress.status = TrainingTaskStatus.FAILED
            progress.completed_at = datetime.utcnow()
            progress.error_message = str(e)

    def _load_training_data(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> list[dict[str, Any]]:
        """
        Load training data from database.

        Args:
            symbols: List of trading symbols
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe

        Returns:
            List of OHLCV data
        """
        # Query database for price data
        with get_db_context() as session:
            from database.models import PriceData as PriceDataModel

            data = []
            for symbol in symbols:
                prices = (
                    session.query(PriceDataModel)
                    .filter(
                        PriceDataModel.symbol == symbol,
                        PriceDataModel.timestamp >= start_date,
                        PriceDataModel.timestamp <= end_date,
                    )
                    .order_by(PriceDataModel.timestamp)
                    .all()
                )

                for price in prices:
                    data.append(
                        {
                            "symbol": symbol,
                            "timestamp": price.timestamp,
                            "open": float(price.open),
                            "high": float(price.high),
                            "low": float(price.low),
                            "close": float(price.close),
                            "volume": float(price.volume),
                        }
                    )

            return data

    def _save_model(
        self,
        model_id: str,
        model: LSTMModel,
        config: TrainingConfig,
        metrics: dict[str, Any],
        n_features: int,
    ) -> str:
        """
        Save model to disk.

        Args:
            model_id: Model ID
            model: Trained model
            config: Training configuration
            metrics: Training metrics
            n_features: Number of features

        Returns:
            Model file path
        """
        model_dir = self.models_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save model parameters
        model_path = model_dir / "model.pkl"

        model_data = {
            "model_id": model_id,
            "input_size": n_features,
            "hidden_sizes": model.hidden_sizes,
            "output_size": model.output_size,
            "dropout": model.dropout,
            "lstm_layers": [lstm.get_params() for lstm in model.lstm_layers],
            "W_out": model.W_out,
            "b_out": model.b_out,
            "config": config.to_dict(),
            "metrics": metrics,
            "created_at": datetime.utcnow().isoformat(),
        }

        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        # Save metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(
                {
                    "model_id": model_id,
                    "model_type": config.model_type.value,
                    "created_at": model_data["created_at"],
                    "config": config.to_dict(),
                    "metrics": {
                        k: v if isinstance(v, (int, float, str, list, dict)) else str(v)
                        for k, v in metrics.items()
                    },
                },
                f,
                indent=2,
            )

        return str(model_path)

    def _save_model_to_db(
        self,
        model_id: str,
        config: TrainingConfig,
        metrics: dict[str, Any],
        progress: TrainingProgress,
    ) -> None:
        """
        Save model metadata to database.

        Args:
            model_id: Model ID
            config: Training configuration
            metrics: Training metrics
            progress: Training progress
        """
        with get_db_context() as session:
            from database.models import MLModel as MLModelDB

            # Calculate accuracy from metrics
            accuracy = metrics.get("final_val_accuracy", 0.0)

            ml_model = MLModelDB(
                id=model_id,
                name=f"{config.model_type.value.upper()} Model - {', '.join(config.symbols)}",
                model_type=config.model_type.value,
                features=config.feature_selection,
                training_start=config.start_date,
                training_end=config.end_date,
                accuracy=float(accuracy),
                status="ready",
                parameters={
                    "sequence_length": config.sequence_length,
                    "prediction_horizon": config.prediction_horizon,
                    "hidden_sizes": [128, 64, 32],
                    "dropout": 0.2,
                },
                metrics={
                    "train_loss": float(metrics.get("final_train_loss", 0)),
                    "val_loss": float(metrics.get("final_val_loss", 0)),
                    "train_accuracy": float(metrics.get("final_train_accuracy", 0)),
                    "val_accuracy": float(metrics.get("final_val_accuracy", 0)),
                    "epochs_trained": int(metrics.get("epochs_trained", 0)),
                },
            )

            session.add(ml_model)

    def get_training_progress(self, task_id: str) -> Optional[dict[str, Any]]:
        """
        Get training progress for a task.

        Args:
            task_id: Task ID

        Returns:
            Progress information or None
        """
        progress = self.training_tasks.get(task_id)
        if progress:
            return progress.to_dict()
        return None

    def load_model(self, model_id: str) -> Optional[LSTMModel]:
        """
        Load a trained model from disk.

        Args:
            model_id: Model ID

        Returns:
            Loaded model or None
        """
        # Check cache
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        # Load from disk
        model_path = self.models_dir / model_id / "model.pkl"

        if not model_path.exists():
            return None

        with open(model_path, "rb") as f:
            model_data = pickle.load(f)

        # Reconstruct model
        model = LSTMModel(
            input_size=model_data["input_size"],
            hidden_sizes=model_data["hidden_sizes"],
            output_size=model_data["output_size"],
            dropout=model_data.get("dropout", 0.0),
        )

        # Load parameters
        for lstm, params in zip(model.lstm_layers, model_data["lstm_layers"]):
            lstm.set_params(params)

        model.W_out = model_data["W_out"]
        model.b_out = model_data["b_out"]

        # Cache model
        self.loaded_models[model_id] = model

        return model

    def generate_predictions(
        self,
        model_id: str,
        current_data: list[dict[str, Any]],
    ) -> list[PredictionResult]:
        """
        Generate predictions using a trained model.

        Args:
            model_id: Model ID
            current_data: Recent OHLCV data

        Returns:
            List of prediction results
        """
        model = self.load_model(model_id)

        if model is None:
            raise ValueError(f"Model {model_id} not found")

        # Load model metadata
        metadata_path = self.models_dir / model_id / "metadata.json"
        if not metadata_path.exists():
            raise ValueError(f"Model metadata not found for {model_id}")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        config = TrainingConfig(**metadata["config"])

        # Calculate features
        feature_matrix = self.feature_engine.calculate_features(
            current_data,
            config.feature_selection,
        )

        # Create sequences
        # Use of the last sequence_length data points
        if len(feature_matrix) < config.sequence_length:
            raise ValueError(
                f"Insufficient data: need {config.sequence_length} points, got {len(feature_matrix)}"
            )

        last_sequence = feature_matrix[-config.sequence_length :]
        X = last_sequence.reshape(1, config.sequence_length, -1)

        # Make prediction
        prediction = model.predict(X)[0, 0]

        # Calculate confidence (simple version)
        confidence = min(abs(prediction - 0.5) * 2, 1.0)

        result = PredictionResult(
            model_id=model_id,
            symbol=current_data[-1].get("symbol", "UNKNOWN"),
            timestamp=datetime.utcnow(),
            prediction=float(prediction),
            confidence=float(confidence),
            prediction_type=config.target_type,
            features_used=config.feature_selection,
            model_version=metadata.get("created_at", "unknown"),
        )

        return [result]

    def get_model_info(self, model_id: str) -> Optional[dict[str, Any]]:
        """
        Get model information.

        Args:
            model_id: Model ID

        Returns:
            Model information or None
        """
        metadata_path = self.models_dir / model_id / "metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, "r") as f:
            return json.load(f)

    def list_models(self) -> list[dict[str, Any]]:
        """
        List all trained models.

        Returns:
            List of model information
        """
        models = []

        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                metadata_path = model_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        models.append(metadata)

        return models


# Global instance
_ml_factory_instance: Optional[MLFactory] = None


def get_ml_factory() -> MLFactory:
    """Get global ML Factory instance."""
    global _ml_factory_instance
    if _ml_factory_instance is None:
        _ml_factory_instance = MLFactory()
    return _ml_factory_instance
