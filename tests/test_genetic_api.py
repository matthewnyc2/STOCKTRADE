"""
Tests for the Genetic Algorithm Optimization API.

Tests cover:
- POST /genetic/optimize - Start optimization
- GET /genetic/optimization/{id} - Get status
- GET /genetic/optimization/{id}/result - Get results
- POST /genetic/optimization/{id}/cancel - Cancel optimization
- GET /genetic/optimizations - List optimizations
- DELETE /genetic/optimization/{id} - Delete optimization
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.genetic import (
    _optimization_results,
    _running_optimizations,
    ParameterRangeSchema,
    GeneticOptimizationRequest,
)
from api.main import app
from models import Strategy, StrategyType
from services.genetic_optimizer import OptimizationStatus


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def cleanup_optimizations():
    """Clean up optimization state before and after tests."""
    _optimization_results.clear()
    _running_optimizations.clear()
    yield
    _optimization_results.clear()
    _running_optimizations.clear()


class TestGeneticAPIModels:
    """Test API request/response models."""

    def test_parameter_range_schema_float(self):
        """Test ParameterRangeSchema for float type."""
        schema = ParameterRangeSchema(
            name="threshold",
            param_type="float",
            min_value=10.0,
            max_value=50.0,
            step=1.0,
        )

        assert schema.name == "threshold"
        assert schema.param_type == "float"
        assert schema.min_value == 10.0
        assert schema.max_value == 50.0

    def test_parameter_range_schema_categorical(self):
        """Test ParameterRangeSchema for categorical type."""
        schema = ParameterRangeSchema(
            name="indicator",
            param_type="categorical",
            categories=["rsi", "macd", "bb"],
        )

        assert schema.name == "indicator"
        assert schema.param_type == "categorical"
        assert schema.categories == ["rsi", "macd", "bb"]

    def test_genetic_optimization_request(self):
        """Test GeneticOptimizationRequest schema."""
        request = GeneticOptimizationRequest(
            strategy_id="strat_001",
            symbol="BTC/USDT",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 1),
            population_size=20,
            generations=10,
            parameter_ranges=[
                ParameterRangeSchema(
                    name="threshold",
                    param_type="float",
                    min_value=10.0,
                    max_value=50.0,
                )
            ],
        )

        assert request.strategy_id == "strat_001"
        assert request.symbol == "BTC/USDT"
        assert request.population_size == 20
        assert len(request.parameter_ranges) == 1


class TestGeneticAPIEndpoints:
    """Test genetic optimization API endpoints."""

    def test_list_optimizations_empty(self, test_client, cleanup_optimizations):
        """Test listing optimizations when none exist."""
        response = test_client.get("/api/genetic/optimizations")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_nonexistent_optimization(self, test_client, cleanup_optimizations):
        """Test getting status of non-existent optimization."""
        response = test_client.get("/api/genetic/optimization/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_nonexistent_optimization(self, test_client, cleanup_optimizations):
        """Test cancelling non-existent optimization."""
        response = test_client.post("/api/genetic/optimization/nonexistent/cancel")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_optimization(self, test_client, cleanup_optimizations):
        """Test deleting non-existent optimization."""
        response = test_client.delete("/api/genetic/optimization/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_start_optimization_invalid_strategy(
        self, test_client, cleanup_optimizations
    ):
        """Test starting optimization with non-existent strategy."""
        request_data = {
            "strategy_id": "nonexistent_strategy",
            "symbol": "BTC/USDT",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-06-01T00:00:00",
            "population_size": 10,
            "generations": 2,
            "parameter_ranges": [
                {
                    "name": "threshold",
                    "param_type": "float",
                    "min_value": 10.0,
                    "max_value": 50.0,
                }
            ],
        }

        response = test_client.post("/api/genetic/optimize", json=request_data)

        # Could be 404 (strategy not found), 422 (validation), or 500 (no database)
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_optimization_schema_validation(
        self, test_client, cleanup_optimizations
    ):
        """Test request schema validation."""
        # Missing required fields
        request_data = {
            "strategy_id": "test_strategy",
            # Missing symbol, dates, parameter_ranges
        }

        response = test_client.post("/api/genetic/optimize", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGeneticConversionFunctions:
    """Test utility conversion functions."""

    def test_individual_to_dict(self):
        """Test converting Individual to dict."""
        from api.genetic import individual_to_dict
        from services.genetic_optimizer import Individual

        individual = Individual(
            id="ind_test",
            parameters={"threshold": 30.0},
            fitness=1.5,
            generation=1,
        )

        result = individual_to_dict(individual)

        assert result["id"] == "ind_test"
        assert result["parameters"] == {"threshold": 30.0}
        assert result["fitness"] == 1.5
        assert result["generation"] == 1

    def test_generation_to_dict(self):
        """Test converting GenerationResult to dict."""
        from api.genetic import generation_to_dict
        from services.genetic_optimizer import GenerationResult, Individual

        generation = GenerationResult(
            generation=1,
            best_fitness=2.5,
            worst_fitness=0.5,
            avg_fitness=1.5,
            best_individual=Individual(
                id="ind_best", parameters={}, fitness=2.5
            ),
            population=[],
        )

        result = generation_to_dict(generation)

        assert result["generation"] == 1
        assert result["best_fitness"] == 2.5
        assert result["worst_fitness"] == 0.5
        assert result["avg_fitness"] == 1.5
        assert result["best_individual"]["id"] == "ind_best"

    def test_config_to_dict(self):
        """Test converting GeneticConfig to dict."""
        from api.genetic import config_to_dict
        from services.genetic_optimizer import GeneticConfig

        config = GeneticConfig(
            population_size=50,
            generations=30,
            mutation_rate=0.15,
            crossover_rate=0.8,
            elitism_count=3,
            tournament_size=5,
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
            risk_free_rate=0.02,
        )

        result = config_to_dict(config)

        assert result["population_size"] == 50
        assert result["generations"] == 30
        assert result["mutation_rate"] == 0.15
        assert result["crossover_rate"] == 0.8
        assert result["elitism_count"] == 3
        assert result["tournament_size"] == 5
        assert result["initial_capital"] == 10000.0
