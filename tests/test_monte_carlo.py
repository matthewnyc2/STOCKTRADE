"""
Monte Carlo Simulation Tests.

Tests for the Monte Carlo simulation service that randomizes trade ordering
to generate confidence intervals and probability distributions.
"""

from datetime import datetime
from decimal import Decimal

import pytest
import numpy as np

from models import BacktestResult, Trade, EquityPoint
from services.monte_carlo import (
    MonteCarloConfig,
    MonteCarloResult,
    run_monte_carlo,
    calculate_probability_of_threshold,
    calculate_risk_of_ruin,
    format_monte_carlo_for_api,
)


@pytest.fixture
def sample_backtest():
    """Create a sample backtest result for testing."""
    trades = [
        Trade(
            id="trade_1",
            symbol="BTC/USDT",
            entry_date=datetime(2024, 1, 1),
            exit_date=datetime(2024, 1, 2),
            entry_price=Decimal("50000"),
            exit_price=Decimal("51000"),
            quantity=Decimal("1.0"),
            side="LONG",
            pnl=Decimal("1000"),
            pnl_percent=Decimal("2.0"),
            exit_reason="SIGNAL",
        ),
        Trade(
            id="trade_2",
            symbol="BTC/USDT",
            entry_date=datetime(2024, 1, 3),
            exit_date=datetime(2024, 1, 4),
            entry_price=Decimal("51000"),
            exit_price=Decimal("50500"),
            quantity=Decimal("1.0"),
            side="LONG",
            pnl=Decimal("-500"),
            pnl_percent=Decimal("-1.0"),
            exit_reason="SIGNAL",
        ),
        Trade(
            id="trade_3",
            symbol="BTC/USDT",
            entry_date=datetime(2024, 1, 5),
            exit_date=datetime(2024, 1, 6),
            entry_price=Decimal("50500"),
            exit_price=Decimal("52000"),
            quantity=Decimal("1.0"),
            side="LONG",
            pnl=Decimal("1500"),
            pnl_percent=Decimal("3.0"),
            exit_reason="SIGNAL",
        ),
        Trade(
            id="trade_4",
            symbol="BTC/USDT",
            entry_date=datetime(2024, 1, 7),
            exit_date=datetime(2024, 1, 8),
            entry_price=Decimal("52000"),
            exit_price=Decimal("51500"),
            quantity=Decimal("1.0"),
            side="LONG",
            pnl=Decimal("-500"),
            pnl_percent=Decimal("-1.0"),
            exit_reason="SIGNAL",
        ),
    ]

    equity_curve = [
        EquityPoint(timestamp=datetime(2024, 1, 1), equity=Decimal("10000"), drawdown=Decimal("0")),
        EquityPoint(timestamp=datetime(2024, 1, 2), equity=Decimal("11000"), drawdown=Decimal("0")),
        EquityPoint(timestamp=datetime(2024, 1, 4), equity=Decimal("10500"), drawdown=Decimal("-0.0455")),
        EquityPoint(timestamp=datetime(2024, 1, 6), equity=Decimal("12000"), drawdown=Decimal("0")),
        EquityPoint(timestamp=datetime(2024, 1, 8), equity=Decimal("11500"), drawdown=Decimal("-0.0417")),
    ]

    return BacktestResult(
        id="bt_12345678",
        strategy_id="strategy_1",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 8),
        initial_capital=Decimal("10000"),
        final_capital=Decimal("11500"),
        total_return=Decimal("0.15"),
        sharpe_ratio=Decimal("1.5"),
        sortino_ratio=Decimal("2.0"),
        max_drawdown=Decimal("-0.0455"),
        win_rate=Decimal("0.5"),
        profit_factor=Decimal("3.0"),
        total_trades=4,
        equity_curve=equity_curve,
        trades=trades,
    )


class TestMonteCarloConfig:
    """Tests for MonteCarloConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MonteCarloConfig()
        assert config.simulations == 1000
        assert config.confidence_levels == [0.05, 0.5, 0.95]
        assert config.seed is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MonteCarloConfig(simulations=500, seed=42)
        assert config.simulations == 500
        assert config.seed == 42


class TestRunMonteCarlo:
    """Tests for run_monte_carlo function."""

    def test_run_monte_carlo_generates_correct_simulation_count(self, sample_backtest):
        """Test that Monte Carlo generates the correct number of simulations."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert result.simulations == 100
        assert len(result.confidence_5th) > 0
        assert len(result.confidence_50th) > 0
        assert len(result.confidence_95th) > 0

    def test_run_monte_carlo_randomizes_trade_order(self, sample_backtest):
        """Test that Monte Carlo randomizes trade order while preserving returns."""
        config = MonteCarloConfig(simulations=50, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        # Check that confidence bands are generated (different curves produce different results)
        # Using any() to handle numpy array comparisons
        assert not np.array_equal(result.confidence_5th, result.confidence_50th)
        assert not np.array_equal(result.confidence_50th, result.confidence_95th)
        # Upper band should be higher than lower band at the final point
        assert result.confidence_95th[-1] > result.confidence_5th[-1]

    def test_run_monte_carlo_calculates_confidence_intervals(self, sample_backtest):
        """Test that confidence intervals (5th, 50th, 95th percentile) are calculated."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        # Check final capital percentiles
        assert "5th" in result.final_capital_percentiles
        assert "50th" in result.final_capital_percentiles
        assert "95th" in result.final_capital_percentiles

        # Percentiles should be ordered
        assert result.final_capital_percentiles["5th"] <= result.final_capital_percentiles["50th"]
        assert result.final_capital_percentiles["50th"] <= result.final_capital_percentiles["95th"]

    def test_run_monte_carlo_calculates_return_statistics(self, sample_backtest):
        """Test that return statistics (mean, std dev, percentiles) are calculated."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert isinstance(result.return_mean, float)
        assert isinstance(result.return_std, float)
        assert "5th" in result.return_percentiles
        assert "50th" in result.return_percentiles
        assert "95th" in result.return_percentiles

    def test_run_monte_carlo_calculates_probability_statistics(self, sample_backtest):
        """Test that probability of profit/loss statistics are calculated."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert 0 <= result.profit_probability <= 1
        assert 0 <= result.loss_probability <= 1
        assert result.profit_probability + result.loss_probability <= 1.01  # Allow small rounding error

    def test_run_monte_carlo_calculates_drawdown_statistics(self, sample_backtest):
        """Test that drawdown statistics are calculated."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert isinstance(result.max_drawdown_mean, float)
        assert isinstance(result.max_drawdown_std, float)
        assert isinstance(result.max_drawdown_worst, float)
        assert result.max_drawdown_worst <= 0  # Drawdown should be negative or zero

    def test_run_monte_carlo_preserves_total_trades(self, sample_backtest):
        """Test that total trades count is preserved."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert result.total_trades == len(sample_backtest.trades)

    def test_run_monte_carlo_with_seed_is_reproducible(self, sample_backtest):
        """Test that using a seed produces reproducible results."""
        config1 = MonteCarloConfig(simulations=50, seed=42)
        result1 = run_monte_carlo(sample_backtest, config1)

        config2 = MonteCarloConfig(simulations=50, seed=42)
        result2 = run_monte_carlo(sample_backtest, config2)

        # Results should be identical with same seed
        assert result1.final_capital_mean == result2.final_capital_mean
        assert result1.return_mean == result2.return_mean
        assert result1.profit_probability == result2.profit_probability

    def test_run_monte_carlo_no_trades_raises_error(self):
        """Test that running Monte Carlo on a backtest with no trades raises ValueError."""
        backtest = BacktestResult(
            id="bt_empty",
            strategy_id="strategy_1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 8),
            initial_capital=Decimal("10000"),
            final_capital=Decimal("10000"),
            total_return=Decimal("0"),
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=Decimal("0"),
            win_rate=Decimal("0"),
            profit_factor=None,
            total_trades=0,
            equity_curve=[],
            trades=[],
        )

        config = MonteCarloConfig(simulations=10)
        with pytest.raises(ValueError, match="no trades"):
            run_monte_carlo(backtest, config)


class TestMonteCarloResult:
    """Tests for MonteCarloResult dataclass."""

    def test_monte_carlo_result_fields(self, sample_backtest):
        """Test that MonteCarloResult has all expected fields."""
        config = MonteCarloConfig(simulations=100, seed=42)
        result = run_monte_carlo(sample_backtest, config)

        assert hasattr(result, "backtest_id")
        assert hasattr(result, "simulations")
        assert hasattr(result, "initial_capital")
        assert hasattr(result, "confidence_5th")
        assert hasattr(result, "confidence_50th")
        assert hasattr(result, "confidence_95th")
        assert hasattr(result, "final_capital_mean")
        assert hasattr(result, "final_capital_std")
        assert hasattr(result, "final_capital_min")
        assert hasattr(result, "final_capital_max")
        assert hasattr(result, "final_capital_percentiles")
        assert hasattr(result, "return_mean")
        assert hasattr(result, "return_std")
        assert hasattr(result, "return_percentiles")
        assert hasattr(result, "profit_probability")
        assert hasattr(result, "loss_probability")
        assert hasattr(result, "max_drawdown_mean")
        assert hasattr(result, "max_drawdown_std")
        assert hasattr(result, "max_drawdown_worst")
        assert hasattr(result, "total_trades")


class TestCalculateProbabilityOfThreshold:
    """Tests for calculate_probability_of_threshold function."""

    def test_probability_of_threshold_with_realistic_result(self, sample_backtest):
        """Test probability calculation for realistic threshold."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        # Test probability of achieving 10% return
        prob = calculate_probability_of_threshold(monte_carlo_result, 0.10)
        assert 0 <= prob <= 1

    def test_probability_of_threshold_zero_threshold(self, sample_backtest):
        """Test probability of breaking even (0% return)."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        prob = calculate_probability_of_threshold(monte_carlo_result, 0.0)
        # Should be similar to profit_probability
        assert abs(prob - monte_carlo_result.profit_probability) < 0.1

    def test_probability_of_threshold_high_threshold(self, sample_backtest):
        """Test probability of achieving a very high return threshold."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        # Very high threshold should have low probability
        prob = calculate_probability_of_threshold(monte_carlo_result, 1.0)  # 100% return
        assert 0 <= prob <= 1


class TestCalculateRiskOfRuin:
    """Tests for calculate_risk_of_ruin function."""

    def test_risk_of_ruin_default_threshold(self, sample_backtest):
        """Test risk of ruin with default 50% threshold."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        risk = calculate_risk_of_ruin(monte_carlo_result)
        assert 0 <= risk <= 1

    def test_risk_of_ruin_custom_threshold(self, sample_backtest):
        """Test risk of ruin with custom threshold."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        # 20% loss threshold
        risk = calculate_risk_of_ruin(monte_carlo_result, ruin_threshold=0.20)
        assert 0 <= risk <= 1


class TestFormatMonteCarloForApi:
    """Tests for format_monte_carlo_for_api function."""

    def test_format_for_api_structure(self, sample_backtest):
        """Test that result is formatted correctly for API response."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        # Check all expected keys
        assert "backtest_id" in formatted
        assert "simulations" in formatted
        assert "initial_capital" in formatted
        assert "confidence_bands" in formatted
        assert "final_capital" in formatted
        assert "returns" in formatted
        assert "probabilities" in formatted
        assert "drawdown" in formatted
        assert "total_trades" in formatted

    def test_format_for_api_confidence_bands(self, sample_backtest):
        """Test that confidence bands are formatted correctly."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        assert "5th" in formatted["confidence_bands"]
        assert "50th" in formatted["confidence_bands"]
        assert "95th" in formatted["confidence_bands"]
        assert isinstance(formatted["confidence_bands"]["5th"], list)
        assert isinstance(formatted["confidence_bands"]["50th"], list)
        assert isinstance(formatted["confidence_bands"]["95th"], list)

    def test_format_for_api_final_capital(self, sample_backtest):
        """Test that final capital statistics are formatted correctly."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        assert "mean" in formatted["final_capital"]
        assert "std" in formatted["final_capital"]
        assert "min" in formatted["final_capital"]
        assert "max" in formatted["final_capital"]
        assert "percentiles" in formatted["final_capital"]

    def test_format_for_api_returns(self, sample_backtest):
        """Test that return statistics are formatted correctly."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        assert "mean" in formatted["returns"]
        assert "std" in formatted["returns"]
        assert "percentiles" in formatted["returns"]

    def test_format_for_api_probabilities(self, sample_backtest):
        """Test that probability statistics are formatted correctly."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        assert "profit" in formatted["probabilities"]
        assert "loss" in formatted["probabilities"]

    def test_format_for_api_drawdown(self, sample_backtest):
        """Test that drawdown statistics are formatted correctly."""
        config = MonteCarloConfig(simulations=100, seed=42)
        monte_carlo_result = run_monte_carlo(sample_backtest, config)

        formatted = format_monte_carlo_for_api(monte_carlo_result)

        assert "mean" in formatted["drawdown"]
        assert "std" in formatted["drawdown"]
        assert "worst" in formatted["drawdown"]


class TestMonteCarloAPI:
    """Tests for Monte Carlo API endpoint."""

    def test_monte_carlo_request_schema(self):
        """Test MonteCarloRequest schema."""
        from api.backtests import MonteCarloRequest

        # Valid request
        request = MonteCarloRequest(
            backtest_id="bt_123",
            simulations=500,
            seed=42,
        )
        assert request.backtest_id == "bt_123"
        assert request.simulations == 500
        assert request.seed == 42

        # Default values
        default_request = MonteCarloRequest(backtest_id="bt_123")
        assert default_request.simulations == 1000
        assert default_request.seed is None

    def test_monte_carlo_response_schema(self):
        """Test MonteCarloResponse schema."""
        from api.backtests import MonteCarloResponse

        response_data = {
            "backtest_id": "bt_123",
            "simulations": 100,
            "initial_capital": 10000.0,
            "confidence_bands": {
                "5th": [9000.0, 9500.0],
                "50th": [10000.0, 10500.0],
                "95th": [11000.0, 12000.0],
            },
            "final_capital": {
                "mean": 10500.0,
                "std": 500.0,
                "min": 9000.0,
                "max": 12000.0,
                "percentiles": {"5th": 9500.0, "50th": 10500.0, "95th": 11500.0},
            },
            "returns": {
                "mean": 0.05,
                "std": 0.05,
                "percentiles": {"5th": -0.1, "50th": 0.05, "95th": 0.2},
            },
            "probabilities": {
                "profit": 0.6,
                "loss": 0.4,
            },
            "drawdown": {
                "mean": -0.05,
                "std": 0.02,
                "worst": -0.15,
            },
            "total_trades": 10,
        }

        response = MonteCarloResponse(**response_data)
        assert response.backtest_id == "bt_123"
        assert response.simulations == 100
        assert response.total_trades == 10
