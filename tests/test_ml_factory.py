"""
Comprehensive tests for ML Factory.

Tests cover:
- Feature engineering
- Model creation and training
- Prediction generation
- API endpoints
- Database operations
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.connection import get_db_context, init_db
from database.models import MLModelModel, PriceModel
from models.ml import (
    MLModel,
    ModelStatus,
    ModelType,
    PredictionRequest,
    TrainingProgressResponse,
    TrainingRequest,
)
from services.ml import (
    FeatureEngine,
    LSTMModel,
    MLFactory,
    TrainingConfig,
    TrainingEngine,
    get_ml_factory,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session."""
    init_db(drop_all=True)
    with get_db_context() as session:
        yield session
        session.rollback()


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    np.random.seed(42)

    n = 200
    base_price = 50000

    data = []
    for i in range(n):
        price_change = np.random.randn() * 100
        open_price = base_price + price_change
        close_price = open_price + np.random.randn() * 50
        high_price = max(open_price, close_price) + abs(np.random.randn() * 20)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 20)
        volume = abs(np.random.randn() * 1000000) + 500000

        data.append(
            {
                "symbol": "BTC",
                "timestamp": datetime(2024, 1, 1) + timedelta(hours=i),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": float(volume),
            }
        )

        base_price = close_price

    return data


@pytest.fixture
def sample_price_data_db(db_session, sample_price_data):
    """Create sample price data in database."""
    import uuid

    for i, data in enumerate(sample_price_data):
        price = PriceModel(
            id=f"price_{uuid.uuid4().hex[:8]}",
            symbol=data["symbol"],
            timestamp=data["timestamp"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
        )
        db_session.add(price)
    db_session.commit()
    return sample_price_data


# ============================================================================
# FEATURE ENGINEERING TESTS
# ============================================================================


class TestFeatureEngine:
    """Tests for FeatureEngine class."""

    def test_get_all_features(self):
        """Test getting all available features."""
        features = FeatureEngine.get_all_features()

        assert isinstance(features, list)
        assert len(features) >= 50
        assert "close" in features
        assert "rsi_14" in features
        assert "sma_20" in features

    def test_get_feature_groups(self):
        """Test getting feature groups."""
        groups = FeatureEngine.get_feature_group("price")

        assert isinstance(groups, list)
        assert len(groups) > 0

    def test_calculate_features(self, sample_price_data):
        """Test feature calculation from price data."""
        engine = FeatureEngine()

        features = engine.calculate_features(
            sample_price_data,
            ["price", "volume", "momentum"],
        )

        assert features.shape[0] == len(sample_price_data)
        assert features.shape[1] > 0
        assert not np.any(np.isnan(features))
        assert not np.any(np.isinf(features))

    def test_create_sequences(self):
        """Test sequence creation for LSTM."""
        # Create dummy features and targets
        features = np.random.randn(100, 10)
        targets = np.random.randn(100)

        X, y = FeatureEngine.create_sequences(
            features,
            targets,
            sequence_length=20,
            prediction_horizon=1,
        )

        assert X.shape[0] == 100 - 20  # n - sequence_length
        assert X.shape[1] == 20  # sequence_length
        assert X.shape[2] == 10  # n_features
        assert y.shape[0] == X.shape[0]


# ============================================================================
# LSTM MODEL TESTS
# ============================================================================


class TestLSTMModel:
    """Tests for LSTM model implementation."""

    def test_model_creation(self):
        """Test creating LSTM model."""
        model = LSTMModel(
            input_size=10,
            hidden_sizes=[64, 32],
            output_size=1,
            dropout=0.2,
        )

        assert model.input_size == 10
        assert len(model.lstm_layers) == 2
        assert model.output_size == 1

    def test_forward_pass(self):
        """Test forward pass through model."""
        model = LSTMModel(
            input_size=5,
            hidden_sizes=[32, 16],
            output_size=1,
        )

        # Create dummy input [batch_size, seq_len, features]
        X = np.random.randn(4, 20, 5)

        output = model.forward(X)

        assert output.shape == (4, 1)
        assert not np.any(np.isnan(output))

    def test_prediction(self):
        """Test making predictions."""
        model = LSTMModel(
            input_size=3,
            hidden_sizes=[16],
            output_size=1,
        )

        X = np.random.randn(2, 10, 3)
        predictions = model.predict(X)

        assert predictions.shape == (2, 1)

    def test_parameter_count(self):
        """Test getting parameter count."""
        model = LSTMModel(
            input_size=5,
            hidden_sizes=[32, 16],
            output_size=1,
        )

        num_params = model.get_num_params()

        assert num_params > 0
        assert isinstance(num_params, int)


class TestTrainingEngine:
    """Tests for training engine."""

    def test_engine_creation(self):
        """Test creating training engine."""
        model = LSTMModel(
            input_size=5,
            hidden_sizes=[16],
            output_size=1,
        )

        engine = TrainingEngine(model, learning_rate=0.001)

        assert engine.model is model
        assert engine.learning_rate == 0.001

    def test_training_step(self):
        """Test single training step."""
        model = LSTMModel(
            input_size=3,
            hidden_sizes=[16],
            output_size=1,
        )

        engine = TrainingEngine(model, learning_rate=0.01)

        X_train = np.random.randn(50, 10, 3)
        y_train = np.random.randint(0, 2, 50)

        loss, accuracy = engine.train_epoch(X_train, y_train, batch_size=10)

        assert isinstance(loss, float)
        assert isinstance(accuracy, float)
        assert loss >= 0
        assert 0 <= accuracy <= 1


# ============================================================================
# ML FACTORY TESTS
# ============================================================================


class TestMLFactory:
    """Tests for MLFactory class."""

    @pytest.fixture
    def factory(self, tmp_path):
        """Create factory instance with temp directory."""
        return MLFactory(models_dir=str(tmp_path))

    def test_factory_creation(self, factory):
        """Test factory creation."""
        assert factory.models_dir.exists()
        assert isinstance(factory.training_tasks, dict)

    def test_get_available_features(self, factory):
        """Test getting available features."""
        features = factory.get_available_features()

        assert isinstance(features, list)
        assert len(features) >= 50

    def test_get_feature_groups(self, factory):
        """Test getting feature groups."""
        groups = factory.get_feature_groups()

        assert isinstance(groups, dict)
        assert "price" in groups

    @patch("services.ml_factory.ThreadPoolExecutor")
    def test_train_model_submission(self, mock_executor, factory):
        """Test that model training is submitted to executor."""
        mock_future = Mock()
        mock_executor.return_value.submit.return_value = mock_future

        config = TrainingConfig(
            symbols=["BTC"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 1),
            timeframe="1h",
        )

        task_id = factory.train_model(config)

        assert task_id in factory.training_tasks
        assert factory.training_tasks[task_id].status == "pending"


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================


class TestMLEndpoints:
    """Tests for ML API endpoints."""

    def test_list_models_empty(self, client):
        """Test listing models when none exist."""
        response = client.get("/api/ml/models")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_features(self, client):
        """Test getting available features endpoint."""
        response = client.get("/api/ml/features")

        assert response.status_code == 200
        data = response.json()
        assert "all_features" in data
        assert "feature_groups" in data
        assert len(data["all_features"]) >= 50

    def test_start_training_success(self, client, sample_price_data_db):
        """Test starting model training."""
        request = {
            "name": "Test Model",
            "model_type": "lstm",
            "symbols": ["BTC"],
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-02T00:00:00",
            "timeframe": "1h",
            "epochs": 2,
            "batch_size": 16,
        }

        with patch("services.ml_factory.ThreadPoolExecutor"):
            response = client.post("/api/ml/train", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "started"

    def test_start_training_invalid_request(self, client):
        """Test starting training with invalid request."""
        request = {
            "name": "",  # Empty name
            "symbols": [],  # Empty symbols
        }

        response = client.post("/api/ml/train", json=request)

        assert response.status_code == 422  # Validation error

    def test_get_training_progress_not_found(self, client):
        """Test getting progress for non-existent task."""
        response = client.get("/api/ml/training/nonexistent")

        assert response.status_code == 404

    def test_get_model_info_not_found(self, client):
        """Test getting info for non-existent model."""
        response = client.get("/api/ml/models/nonexistent/info")

        assert response.status_code == 404

    def test_deploy_model_not_found(self, client):
        """Test deploying non-existent model."""
        response = client.post("/api/ml/models/nonexistent/deploy")

        assert response.status_code == 404


# ============================================================================
# PYDANTIC MODEL TESTS
# ============================================================================


class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_training_request_valid(self):
        """Test valid training request."""
        request = TrainingRequest(
            name="Test Model",
            model_type=ModelType.LSTM,
            symbols=["BTC", "ETH"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 1),
            epochs=50,
        )

        assert request.name == "Test Model"
        assert request.model_type == ModelType.LSTM
        assert len(request.symbols) == 2

    def test_training_request_invalid_dates(self):
        """Test training request with invalid dates."""
        with pytest.raises(ValueError):
            TrainingRequest(
                name="Test",
                model_type=ModelType.LSTM,
                symbols=["BTC"],
                start_date=datetime(2024, 2, 1),
                end_date=datetime(2024, 1, 1),  # End before start
            )

    def test_prediction_request_valid(self):
        """Test valid prediction request."""
        request = PredictionRequest(
            model_id="ml_abc123",
            symbol="BTC",
            lookback_periods=100,
        )

        assert request.model_id == "ml_abc123"
        assert request.symbol == "BTC"

    def test_ml_model_validation(self):
        """Test ML model validation."""
        model = MLModel(
            id="ml_test",
            name="Test Model",
            model_type=ModelType.LSTM,
            features=["price", "volume"],
            accuracy=0.85,
        )

        assert model.accuracy == 0.85
        assert model.status == ModelStatus.READY

    def test_ml_model_invalid_accuracy(self):
        """Test ML model with invalid accuracy."""
        with pytest.raises(ValueError):
            MLModel(
                id="ml_test",
                name="Test",
                model_type=ModelType.LSTM,
                features=[],
                accuracy=1.5,  # Invalid (> 1)
            )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestMLFactoryIntegration:
    """Integration tests for ML Factory."""

    def test_full_training_workflow(self, client, sample_price_data_db, tmp_path):
        """Test complete training workflow."""
        # 1. Start training
        with patch("services.ml_factory.ThreadPoolExecutor"):
            train_response = client.post(
                "/api/ml/train",
                json={
                    "name": "Integration Test Model",
                    "model_type": "lstm",
                    "symbols": ["BTC"],
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-02T00:00:00",
                    "timeframe": "1h",
                    "epochs": 2,
                    "batch_size": 16,
                },
            )

        assert train_response.status_code == 200
        task_id = train_response.json()["task_id"]

        # 2. Check models list (would need to wait for training in real scenario)
        models_response = client.get("/api/ml/models")
        assert models_response.status_code == 200

    def test_feature_calculation_integration(self, sample_price_data):
        """Test feature calculation with real data."""
        engine = FeatureEngine()

        # Test all feature groups
        features = engine.calculate_features(
            sample_price_data,
            ["price", "volume", "momentum", "trend", "volatility", "time"],
        )

        assert features.shape[0] == len(sample_price_data)
        assert features.shape[1] >= 30  # At least 30 features


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestMLFactoryPerformance:
    """Performance tests for ML Factory."""

    def test_feature_calculation_performance(self, sample_price_data):
        """Test feature calculation performance."""
        import time

        engine = FeatureEngine()

        start = time.time()
        features = engine.calculate_features(
            sample_price_data,
            ["price", "volume", "momentum", "trend"],
        )
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should complete in < 1 second
        assert features.shape[0] == len(sample_price_data)

    def test_lstm_forward_pass_performance(self):
        """Test LSTM forward pass performance."""
        import time

        model = LSTMModel(
            input_size=20,
            hidden_sizes=[64, 32],
            output_size=1,
        )

        X = np.random.randn(32, 60, 20)  # batch_size=32, seq_len=60

        start = time.time()
        for _ in range(10):
            output = model.forward(X)
        elapsed = time.time() - start

        assert elapsed < 5.0  # 10 forward passes in < 5 seconds
