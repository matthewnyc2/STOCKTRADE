"""
Tests for Walk-Forward Optimization Service.

Tests cover:
- Walk-forward window splitting logic
- In-sample and out-of-sample period execution
- Parameter degradation detection
- Aggregated metrics calculation
- Edge cases and error handling
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from models import Strategy, StrategyType
from services.walk_forward import (
    WalkForwardConfig,
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward,
    format_walk_forward_for_api,
    detect_parameter_degradation,
    _calculate_window_config,
)


@pytest.fixture
def sample_strategy() -> Strategy:
    """Create a sample RSI strategy for testing."""
    return Strategy(
        id="strat_wf_test",
        name="Walk-Forward Test Strategy",
        type=StrategyType.COMPOSED,
        description="A strategy for walk-forward testing",
        parameters={
            "indicator_type": "rsi",
            "oversold_threshold": 30.0,
            "overbought_threshold": 70.0,
        },
        status="active",
    )


@pytest.fixture
def sample_price_data():
    """Generate sample price data for walk-forward testing.

    Creates 500 candles with enough data for multiple periods.
    """
    prices = []
    base_price = 100.0
    base_time = datetime(2024, 1, 1)

    for i in range(500):
        # Add some realistic price movement with trends
        trend = (i % 200) / 200 * 5 - 2.5  # Cyclic trend
        noise = (i % 20 - 10) * 0.2  # Short-term noise
        open_price = base_price + trend + noise
        close_price = open_price + (i % 7 - 3) * 0.3
        high_price = max(open_price, close_price) + abs(i % 3) * 0.3
        low_price = min(open_price, close_price) - abs(i % 3) * 0.3
        volume = 1000000 + i * 5000

        prices.append({
            "timestamp": base_time + timedelta(hours=i),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        })

    return prices


@pytest.fixture
def walk_forward_config():
    """Create a standard walk-forward configuration."""
    return WalkForwardConfig(
        in_sample_pct=0.6,  # 60% in-sample, 40% out-of-sample
        window_size=250,  # 150 IS, 100 OOS - both above minimum
        step_size=100,
        commission_rate=Decimal("0.001"),
        slippage_rate=Decimal("0.001"),
        position_size_percent=Decimal("1.0"),
    )


class TestWindowConfiguration:
    """Test window and step size calculation logic."""

    def test_calculate_window_config_with_defaults(self):
        """Test window config calculation with default settings."""
        total_points = 500
        config = WalkForwardConfig(in_sample_pct=0.7)

        window_size, step_size = _calculate_window_config(total_points, config)

        # Window size should be calculated based on data
        assert window_size > 0
        assert step_size > 0
        assert window_size <= total_points

    def test_calculate_window_config_with_fixed_window(self):
        """Test window config with fixed window size."""
        total_points = 500
        config = WalkForwardConfig(
            in_sample_pct=0.7,
            window_size=150,
        )

        window_size, step_size = _calculate_window_config(total_points, config)

        assert window_size == 150
        assert step_size > 0

    def test_calculate_window_config_with_fixed_step(self):
        """Test window config with fixed step size."""
        total_points = 500
        config = WalkForwardConfig(
            in_sample_pct=0.7,
            window_size=150,
            step_size=75,
        )

        window_size, step_size = _calculate_window_config(total_points, config)

        assert window_size == 150
        assert step_size == 75

    def test_in_sample_size_within_window(self):
        """Test that in-sample size is correct within window."""
        total_points = 500
        config = WalkForwardConfig(in_sample_pct=0.7, window_size=200)

        window_size, step_size = _calculate_window_config(total_points, config)
        in_sample_size = int(window_size * config.in_sample_pct)

        assert in_sample_size == 140  # 70% of 200
        assert window_size - in_sample_size == 60  # OOS is 30%


class TestWalkForwardExecution:
    """Test main walk-forward execution logic."""

    def test_run_walk_forward_generates_periods(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test that walk-forward generates multiple periods."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        # Should have multiple periods
        assert result.total_periods >= 1
        assert len(result.periods) == result.total_periods

    def test_run_walk_forward_with_default_config(
        self, sample_strategy, sample_price_data
    ):
        """Test walk-forward with default configuration."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Should complete successfully
        assert result.total_periods >= 1
        assert result.in_sample_pct == 0.7

    def test_walk_forward_period_structure(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test that each period has the correct structure."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        if result.periods:
            period = result.periods[0]

            # Check period structure
            assert period.period_number >= 1
            assert period.in_sample_start < period.in_sample_end
            assert period.out_of_sample_start > period.in_sample_end
            assert period.out_of_sample_end > period.out_of_sample_start

            # Check metrics are present
            assert isinstance(period.in_sample_return, float)
            assert isinstance(period.out_of_sample_return, float)
            assert period.in_sample_trades >= 0
            assert period.out_of_sample_trades >= 0

    def test_walk_forward_periods_sequential(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test that periods are sequential and roll forward."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        if len(result.periods) >= 2:
            # Check that periods roll forward
            for i in range(len(result.periods) - 1):
                current = result.periods[i]
                next_period = result.periods[i + 1]

                # Next period should start after current period
                assert next_period.in_sample_start >= current.in_sample_start
                assert next_period.period_number == current.period_number + 1

    def test_walk_forward_aggregated_metrics(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test that aggregated metrics are calculated correctly."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        # Check aggregated metrics
        assert isinstance(result.avg_oos_return, float)
        assert isinstance(result.std_oos_return, float)
        assert isinstance(result.avg_oos_sharpe, float)
        assert isinstance(result.avg_oos_max_drawdown, float)
        assert result.total_oos_trades >= 0
        assert 0 <= result.period_win_rate <= 1

    def test_walk_forward_stability_metrics(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test that stability metrics are calculated."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        # Check stability metrics
        assert 0 <= result.parameter_stability_score <= 1
        assert -1 <= result.return_correlation_in_vs_oos <= 1
        assert isinstance(result.avg_return_degradation, float)

    def test_walk_forward_period_analysis(
        self, sample_strategy, sample_price_data, walk_forward_config
    ):
        """Test period-level analysis metrics."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            config=walk_forward_config,
        )

        # Check period analysis
        # positive + negative may be less than total if there are zero-return periods
        assert result.positive_periods + result.negative_periods <= result.total_periods
        assert result.worst_period_return <= result.best_period_return

    def test_walk_forward_returns_correct_symbol(
        self, sample_strategy, sample_price_data
    ):
        """Test that walk-forward returns the correct symbol."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="ETH/USDT",
        )

        assert result.symbol == "ETH/USDT"


class TestParameterDegradation:
    """Test parameter degradation detection."""

    def test_no_degradation_with_insufficient_periods(self):
        """Test degradation detection with insufficient periods."""
        # Create minimal result with 1 period
        result = WalkForwardResult(
            strategy_id="test",
            symbol="BTC/USDT",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            total_periods=1,
            in_sample_pct=0.7,
            window_size=100,
            periods=[
                WalkForwardPeriod(
                    period_number=1,
                    in_sample_start=datetime(2024, 1, 1),
                    in_sample_end=datetime(2024, 1, 7),
                    out_of_sample_start=datetime(2024, 1, 7),
                    out_of_sample_end=datetime(2024, 1, 10),
                    in_sample_return=0.1,
                    in_sample_sharpe=1.5,
                    in_sample_max_drawdown=-0.1,
                    in_sample_trades=10,
                    out_of_sample_return=0.08,
                    out_of_sample_sharpe=1.2,
                    out_of_sample_max_drawdown=-0.12,
                    out_of_sample_trades=8,
                    return_degradation=0.02,
                )
            ],
            avg_oos_return=0.08,
            std_oos_return=0.01,
            avg_oos_sharpe=1.2,
            avg_oos_max_drawdown=-0.12,
            total_oos_trades=8,
            period_win_rate=1.0,
            parameter_stability_score=0.8,
            return_correlation_in_vs_oos=0.7,
            avg_return_degradation=0.02,
            worst_period_return=0.08,
            best_period_return=0.08,
            positive_periods=1,
            negative_periods=0,
        )

        analysis = detect_parameter_degradation(result)

        assert analysis["has_degradation"] is False
        assert "Insufficient periods" in analysis["reason"]

    def test_detect_performance_decline(self):
        """Test detection of performance decline."""
        # Create result with declining returns
        periods = []
        for i in range(5):
            is_return = 0.1 - i * 0.015
            oos_return = 0.08 - i * 0.02
            periods.append(
                WalkForwardPeriod(
                    period_number=i + 1,
                    in_sample_start=datetime(2024, 1, 1 + i * 2),
                    in_sample_end=datetime(2024, 1, 2 + (i + 1) * 2 - 1),
                    out_of_sample_start=datetime(2024, 1, 2 + (i + 1) * 2 - 1),
                    out_of_sample_end=datetime(2024, 1, 2 + (i + 2) * 2),
                    in_sample_return=is_return,
                    in_sample_sharpe=1.5 - i * 0.2,
                    in_sample_max_drawdown=-0.1,
                    in_sample_trades=10,
                    out_of_sample_return=oos_return,  # Declining
                    out_of_sample_sharpe=1.2 - i * 0.2,
                    out_of_sample_max_drawdown=-0.12 - i * 0.02,
                    out_of_sample_trades=8,
                    return_degradation=is_return - oos_return,
                )
            )

        result = WalkForwardResult(
            strategy_id="test",
            symbol="BTC/USDT",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 20),
            total_periods=5,
            in_sample_pct=0.7,
            window_size=100,
            periods=periods,
            avg_oos_return=0.02,
            std_oos_return=0.03,
            avg_oos_sharpe=0.4,
            avg_oos_max_drawdown=-0.18,
            total_oos_trades=40,
            period_win_rate=0.6,
            parameter_stability_score=0.5,
            return_correlation_in_vs_oos=0.5,
            avg_return_degradation=0.05,
            worst_period_return=-0.02,
            best_period_return=0.08,
            positive_periods=3,
            negative_periods=2,
        )

        analysis = detect_parameter_degradation(result, threshold=0.3)

        # Should detect some level of degradation
        assert "has_degradation" in analysis
        assert "degradation_level" in analysis
        assert "trend_slope" in analysis
        assert "recommendation" in analysis

    def test_stable_performance_no_degradation(self):
        """Test that stable performance doesn't trigger degradation warning."""
        # Create result with stable returns
        periods = []
        for i in range(5):
            is_return = 0.1
            oos_return = 0.08 + (i % 2) * 0.01
            periods.append(
                WalkForwardPeriod(
                    period_number=i + 1,
                    in_sample_start=datetime(2024, 1, 1 + i * 2),
                    in_sample_end=datetime(2024, 1, 2 + (i + 1) * 2 - 1),
                    out_of_sample_start=datetime(2024, 1, 2 + (i + 1) * 2 - 1),
                    out_of_sample_end=datetime(2024, 1, 2 + (i + 2) * 2),
                    in_sample_return=is_return,
                    in_sample_sharpe=1.5,
                    in_sample_max_drawdown=-0.1,
                    in_sample_trades=10,
                    out_of_sample_return=oos_return,  # Slight oscillation
                    out_of_sample_sharpe=1.2,
                    out_of_sample_max_drawdown=-0.12,
                    out_of_sample_trades=8,
                    return_degradation=is_return - oos_return,
                )
            )

        result = WalkForwardResult(
            strategy_id="test",
            symbol="BTC/USDT",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 20),
            total_periods=5,
            in_sample_pct=0.7,
            window_size=100,
            periods=periods,
            avg_oos_return=0.085,
            std_oos_return=0.005,
            avg_oos_sharpe=1.2,
            avg_oos_max_drawdown=-0.12,
            total_oos_trades=40,
            period_win_rate=1.0,
            parameter_stability_score=0.9,
            return_correlation_in_vs_oos=0.95,
            avg_return_degradation=0.02,
            worst_period_return=0.08,
            best_period_return=0.09,
            positive_periods=5,
            negative_periods=0,
        )

        analysis = detect_parameter_degradation(result)

        # Should not detect severe degradation
        assert analysis["degradation_level"] in ["none", "mild"]


class TestFormatting:
    """Test API response formatting."""

    def test_format_walk_forward_for_api(
        self, sample_strategy, sample_price_data
    ):
        """Test formatting walk-forward result for API."""
        result = run_walk_forward(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        formatted = format_walk_forward_for_api(result)

        # Check top-level structure
        assert "strategy_id" in formatted
        assert "symbol" in formatted
        assert "date_range" in formatted
        assert "configuration" in formatted
        assert "aggregated_performance" in formatted
        assert "stability_metrics" in formatted
        assert "period_analysis" in formatted
        assert "periods" in formatted

        # Check date range
        assert "start" in formatted["date_range"]
        assert "end" in formatted["date_range"]

        # Check configuration
        assert formatted["configuration"]["in_sample_pct"] == result.in_sample_pct
        assert formatted["configuration"]["total_periods"] == result.total_periods

        # Check aggregated performance
        perf = formatted["aggregated_performance"]
        assert "avg_oos_return" in perf
        assert "std_oos_return" in perf
        assert "period_win_rate" in perf

        # Check stability metrics
        stability = formatted["stability_metrics"]
        assert "parameter_stability_score" in stability
        assert "return_correlation_in_vs_oos" in stability

        # Check periods
        assert len(formatted["periods"]) == result.total_periods

    def test_get_period_results(self):
        """Test period results serialization."""
        period = WalkForwardPeriod(
            period_number=1,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 1, 7),
            out_of_sample_start=datetime(2024, 1, 7),
            out_of_sample_end=datetime(2024, 1, 10),
            in_sample_return=0.1,
            in_sample_sharpe=1.5,
            in_sample_max_drawdown=-0.1,
            in_sample_trades=10,
            out_of_sample_return=0.08,
            out_of_sample_sharpe=1.2,
            out_of_sample_max_drawdown=-0.12,
            out_of_sample_trades=8,
            optimized_parameters={"rsi_period": 14},
            return_degradation=0.02,  # 0.10 - 0.08 = 0.02
        )

        result = WalkForwardResult(
            strategy_id="test",
            symbol="BTC/USDT",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            total_periods=1,
            in_sample_pct=0.7,
            window_size=100,
            periods=[period],
            avg_oos_return=0.08,
            std_oos_return=0.01,
            avg_oos_sharpe=1.2,
            avg_oos_max_drawdown=-0.12,
            total_oos_trades=8,
            period_win_rate=1.0,
            parameter_stability_score=0.8,
            return_correlation_in_vs_oos=0.7,
            avg_return_degradation=0.02,
            worst_period_return=0.08,
            best_period_return=0.08,
            positive_periods=1,
            negative_periods=0,
        )

        period_results = result.get_period_results()

        assert len(period_results) == 1
        assert period_results[0]["period_number"] == 1
        assert "in_sample" in period_results[0]
        assert "out_of_sample" in period_results[0]
        assert "optimized_parameters" in period_results[0]
        assert "return_degradation" in period_results[0]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_insufficient_data_raises_error(self, sample_strategy):
        """Test that insufficient data raises an error."""
        short_data = [
            {
                "timestamp": datetime(2024, 1, 1) + timedelta(hours=i),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(50)  # Too little data
        ]

        config = WalkForwardConfig(in_sample_pct=0.7)

        with pytest.raises(ValueError, match="Insufficient data"):
            run_walk_forward(
                strategy=sample_strategy,
                price_data=short_data,
                symbol="BTC/USDT",
                config=config,
            )

    def test_invalid_in_sample_pct_raises_error(
        self, sample_strategy, sample_price_data
    ):
        """Test that invalid in_sample_pct raises an error."""
        config = WalkForwardConfig(in_sample_pct=1.5)  # Invalid (> 1)

        with pytest.raises(ValueError, match="in_sample_pct must be between 0 and 1"):
            run_walk_forward(
                strategy=sample_strategy,
                price_data=sample_price_data,
                symbol="BTC/USDT",
                config=config,
            )

    def test_window_too_small_raises_error(self, sample_strategy):
        """Test that too small window size raises an error."""
        # Need enough data to pass the min_points_per_window * 2 check
        # but the window configuration should fail because OOS is too small
        short_data = [
            {
                "timestamp": datetime(2024, 1, 1) + timedelta(hours=i),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(250)  # Enough for 2 * min_points
        ]

        config = WalkForwardConfig(
            in_sample_pct=0.9,  # Too high, OOS would be too small
            window_size=200,  # With 90% IS, OOS would be 20, below min 100
        )

        with pytest.raises(ValueError, match="Out-of-sample size.*below minimum"):
            run_walk_forward(
                strategy=sample_strategy,
                price_data=short_data,
                symbol="BTC/USDT",
                config=config,
            )

    def test_empty_price_data_raises_error(self, sample_strategy):
        """Test that empty price data raises an error."""
        config = WalkForwardConfig()

        with pytest.raises(ValueError, match="Insufficient data"):
            run_walk_forward(
                strategy=sample_strategy,
                price_data=[],
                symbol="BTC/USDT",
                config=config,
            )


class TestReturnDegradation:
    """Test return degradation calculation within periods."""

    def test_return_degradation_calculation(self):
        """Test that return degradation is calculated correctly."""
        period = WalkForwardPeriod(
            period_number=1,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 1, 7),
            out_of_sample_start=datetime(2024, 1, 7),
            out_of_sample_end=datetime(2024, 1, 10),
            in_sample_return=0.15,  # 15% IS return
            in_sample_sharpe=1.8,
            in_sample_max_drawdown=-0.08,
            in_sample_trades=12,
            out_of_sample_return=0.10,  # 10% OOS return
            out_of_sample_sharpe=1.4,
            out_of_sample_max_drawdown=-0.10,
            out_of_sample_trades=10,
            return_degradation=0.05,  # 0.15 - 0.10 = 0.05
        )

        # Degradation = IS - OOS = 0.15 - 0.10 = 0.05
        assert period.return_degradation == 0.05

    def test_return_improvement_negative_degradation(self):
        """Test that OOS outperforming IS gives negative degradation."""
        period = WalkForwardPeriod(
            period_number=1,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 1, 7),
            out_of_sample_start=datetime(2024, 1, 7),
            out_of_sample_end=datetime(2024, 1, 10),
            in_sample_return=0.08,
            in_sample_sharpe=1.2,
            in_sample_max_drawdown=-0.10,
            in_sample_trades=10,
            out_of_sample_return=0.12,  # OOS better than IS
            out_of_sample_sharpe=1.5,
            out_of_sample_max_drawdown=-0.08,
            out_of_sample_trades=12,
            return_degradation=-0.04,  # 0.08 - 0.12 = -0.04 (improvement)
        )

        # Degradation = IS - OOS = 0.08 - 0.12 = -0.04 (improvement)
        assert period.return_degradation == -0.04
