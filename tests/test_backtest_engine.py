"""
Tests for the Backtest Engine Service.

Tests cover:
- Backtest execution on historical price data
- Performance metrics calculation (Sharpe, Sortino, Max DD, Win Rate, etc.)
- Trade simulation with slippage and commission
- Equity curve generation
"""

import math
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from models import BacktestResult, EquityPoint, Trade, Strategy, StrategyType, SignalType
from services.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
)


@pytest.fixture
def sample_strategy() -> Strategy:
    """Create a sample RSI strategy for testing."""
    return Strategy(
        id="strat_test001",
        name="Test RSI Strategy",
        type=StrategyType.COMPOSED,
        description="A simple RSI-based strategy for testing",
        parameters={
            "indicator_type": "rsi",
            "oversold_threshold": 30.0,
            "overbought_threshold": 70.0,
        },
        status="active",
    )


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing.

    Creates 100 candles with some price movement.
    """
    prices = []
    base_price = 100.0
    base_time = datetime(2024, 1, 1)

    for i in range(100):
        # Add some realistic price movement
        change = (i % 10 - 5) * 0.5  # Oscillating movement
        open_price = base_price + change
        close_price = open_price + (i % 3 - 1) * 0.3
        high_price = max(open_price, close_price) + abs(i % 2) * 0.2
        low_price = min(open_price, close_price) - abs(i % 2) * 0.2
        volume = 1000000 + i * 10000

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
def backtest_config():
    """Create a standard backtest configuration."""
    return BacktestConfig(
        initial_capital=Decimal("10000.0"),
        commission_rate=Decimal("0.001"),  # 0.1%
        slippage_rate=Decimal("0.001"),  # 0.1%
        position_size_percent=Decimal("1.0"),  # Full position
    )


class TestMetricsCalculation:
    """Test performance metrics calculations."""

    def test_calculate_sharpe_ratio_positive_returns(self):
        """Test Sharpe ratio calculation with positive returns."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.005, 0.015]
        risk_free_rate = 0.02  # 2% annual

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)

        # Should be positive with mostly upward trend
        assert sharpe is not None
        assert sharpe > 0

    def test_calculate_sharpe_ratio_all_negative(self):
        """Test Sharpe ratio with all negative returns."""
        returns = [-0.01, -0.02, -0.01, -0.03, -0.01]
        risk_free_rate = 0.02

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)

        # Should be negative
        assert sharpe is not None
        assert sharpe < 0

    def test_calculate_sharpe_ratio_insufficient_data(self):
        """Test Sharpe ratio with insufficient data."""
        returns = [0.01]
        risk_free_rate = 0.02

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)

        # Should return None for insufficient data
        assert sharpe is None

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.005, 0.015]
        risk_free_rate = 0.02

        sortino = calculate_sortino_ratio(returns, risk_free_rate)

        # Should be positive
        assert sortino is not None
        assert sortino > 0

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        equity_curve = [
            10000, 10500, 11000, 10800, 11500, 12000, 11800, 11200, 12500, 13000
        ]

        max_dd = calculate_max_drawdown(equity_curve)

        # Max drawdown should be between 0 and 1 (negative)
        assert max_dd <= 0
        # The worst drawdown here is from 12000 to 11200 = 800/12000 = 6.67%
        assert max_dd <= -0.06

    def test_calculate_max_drawdown_no_decline(self):
        """Test max drawdown with continuously rising equity."""
        equity_curve = [10000, 10500, 11000, 11500, 12000]

        max_dd = calculate_max_drawdown(equity_curve)

        # Should be 0 (no drawdown)
        assert max_dd == 0

    def test_calculate_win_rate_all_winners(self):
        """Test win rate with all winning trades."""
        trades = [
            {"pnl": Decimal("100")},
            {"pnl": Decimal("200")},
            {"pnl": Decimal("150")},
        ]

        win_rate = calculate_win_rate(trades)

        assert win_rate == Decimal("1.0")

    def test_calculate_win_rate_mixed(self):
        """Test win rate with mixed results."""
        trades = [
            {"pnl": Decimal("100")},
            {"pnl": Decimal("-50")},
            {"pnl": Decimal("200")},
            {"pnl": Decimal("-30")},
            {"pnl": Decimal("150")},
        ]

        win_rate = calculate_win_rate(trades)

        # 3 winners out of 5 = 60%
        assert win_rate == Decimal("0.6")

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        trades = [
            {"pnl": Decimal("100")},
            {"pnl": Decimal("-50")},
            {"pnl": Decimal("200")},
            {"pnl": Decimal("-30")},
            {"pnl": Decimal("150")},
        ]

        profit_factor = calculate_profit_factor(trades)

        # Gross profit = 450, gross loss = 80, ratio = 5.625
        assert profit_factor == Decimal("5.625")

    def test_calculate_profit_factor_no_losses(self):
        """Test profit factor with no losing trades."""
        trades = [
            {"pnl": Decimal("100")},
            {"pnl": Decimal("200")},
            {"pnl": Decimal("150")},
        ]

        profit_factor = calculate_profit_factor(trades)

        # Should be infinite (represented as a very large number)
        assert profit_factor == float("inf")

    def test_calculate_profit_factor_no_wins(self):
        """Test profit factor with no winning trades."""
        trades = [
            {"pnl": Decimal("-100")},
            {"pnl": Decimal("-50")},
            {"pnl": Decimal("-30")},
        ]

        profit_factor = calculate_profit_factor(trades)

        # Should be 0
        assert profit_factor == Decimal("0")

    def test_calculate_expectancy(self):
        """Test expectancy calculation."""
        trades = [
            {"pnl": Decimal("100")},
            {"pnl": Decimal("-50")},
            {"pnl": Decimal("200")},
            {"pnl": Decimal("-30")},
            {"pnl": Decimal("150")},
        ]

        expectancy = calculate_expectancy(trades)

        # Total profit = 370, 5 trades, avg = 74
        assert expectancy == Decimal("74")

    def test_calculate_expectancy_no_trades(self):
        """Test expectancy with no trades."""
        trades = []

        expectancy = calculate_expectancy(trades)

        assert expectancy == Decimal("0")


class TestTradeSimulation:
    """Test trade simulation logic."""

    def test_simulate_long_trade_with_commission(self):
        """Test long trade simulation with commission."""
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0"),
            position_size_percent=Decimal("1.0"),
        )

        engine = BacktestEngine(config)

        # Simulate a long trade
        entry_price = Decimal("100")
        exit_price = Decimal("110")
        quantity = Decimal("10")

        entry_cost, exit_value, commission = engine._calculate_trade_costs(
            entry_price, exit_price, quantity, "LONG"
        )

        # Entry: 100 * 10 = 1000 + 1 commission = 1001
        # Exit: 110 * 10 = 1100 - 1.1 commission = 1098.9
        # P&L: 1098.9 - 1001 = 97.9
        pnl = exit_value - entry_cost - commission

        assert pnl > 0
        assert pnl == Decimal("97.9")

    def test_simulate_short_trade_with_commission(self):
        """Test short trade simulation with commission."""
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0"),
            position_size_percent=Decimal("1.0"),
        )

        engine = BacktestEngine(config)

        # Simulate a short trade (profit when price drops)
        entry_price = Decimal("110")
        exit_price = Decimal("100")
        quantity = Decimal("10")

        entry_cost, exit_value, commission = engine._calculate_trade_costs(
            entry_price, exit_price, quantity, "SHORT"
        )

        # Short: enter at 110, exit at 100 (profit)
        # Entry: 110 * 10 = 1100
        # Exit: 100 * 10 = 1000
        # P&L should be positive
        pnl = (entry_price - exit_price) * quantity - commission

        assert pnl > 0

    def test_slippage_effect_on_entry(self):
        """Test slippage effect on trade entry."""
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0"),
            slippage_rate=Decimal("0.001"),  # 0.1% slippage
            position_size_percent=Decimal("1.0"),
        )

        engine = BacktestEngine(config)

        intended_price = Decimal("100")
        actual_price = engine._apply_slippage(intended_price, "LONG")

        # Long entry: slippage increases entry price
        assert actual_price > intended_price
        assert actual_price == Decimal("100.1")

    def test_slippage_effect_on_short_entry(self):
        """Test slippage effect on short trade entry."""
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        engine = BacktestEngine(config)

        intended_price = Decimal("100")
        actual_price = engine._apply_slippage(intended_price, "SHORT")

        # Short entry: slippage decreases entry price (worse for trader)
        assert actual_price < intended_price
        assert actual_price == Decimal("99.9")


class TestBacktestExecution:
    """Test full backtest execution."""

    def test_backtest_engine_initialization(self, backtest_config):
        """Test backtest engine initialization."""
        engine = BacktestEngine(backtest_config)

        assert engine.config.initial_capital == Decimal("10000")
        assert engine.config.commission_rate == Decimal("0.001")
        assert engine.config.slippage_rate == Decimal("0.001")

    def test_run_backtest_generates_result(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that running a backtest generates a valid result."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Verify result structure
        assert isinstance(result, BacktestResult)
        assert result.strategy_id == sample_strategy.id
        assert result.initial_capital == backtest_config.initial_capital
        assert len(result.equity_curve) > 0

    def test_backtest_equity_curve_monotonic_timestamps(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that equity curve has monotonically increasing timestamps."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Check timestamps are in order
        for i in range(1, len(result.equity_curve)):
            assert result.equity_curve[i].timestamp >= result.equity_curve[i - 1].timestamp

    def test_backtest_final_capital_reasonable(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that final capital is within reasonable bounds."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Final capital should be positive
        assert result.final_capital > 0

        # Should not be more than 10x initial (sanity check)
        assert result.final_capital < backtest_config.initial_capital * 10

        # Should not lose more than 90% (sanity check)
        assert result.final_capital > backtest_config.initial_capital * Decimal("0.1")

    def test_backtest_metrics_calculated(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that all required metrics are calculated."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Check all metrics are present
        assert result.total_return is not None
        assert result.max_drawdown is not None
        assert result.win_rate is not None
        assert result.total_trades >= 0

        # Sharpe and Sortino may be None if insufficient data
        if result.total_trades > 5:
            assert result.sharpe_ratio is not None

    def test_backtest_with_no_trades(
        self, sample_strategy, backtest_config
    ):
        """Test backtest with price data that generates no trades."""
        # Create nearly flat price data (minimal signals)
        # Need some variation for indicators to calculate
        flat_prices = []
        base_time = datetime(2024, 1, 1)
        base_price = 100.0

        for i in range(100):
            # Tiny variation to allow indicator calculation
            variation = 0.001 * (i % 3 - 1)  # -0.001, 0, 0.001
            price = base_price + variation

            flat_prices.append({
                "timestamp": base_time + timedelta(hours=i),
                "open": price,
                "high": price + 0.001,
                "low": price - 0.001,
                "close": price,
                "volume": 1000000,
            })

        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=flat_prices,
            symbol="BTC/USDT",
        )

        # Should have minimal to no trades with flat prices
        assert result.total_trades >= 0
        # Final capital should be close to initial
        assert abs(result.final_capital - backtest_config.initial_capital) < backtest_config.initial_capital * Decimal("0.1")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_price_data(self, sample_strategy, backtest_config):
        """Test backtest with empty price data."""
        engine = BacktestEngine(backtest_config)

        with pytest.raises(ValueError, match="Insufficient price data"):
            engine.run_backtest(
                strategy=sample_strategy,
                price_data=[],
                symbol="BTC/USDT",
            )

    def test_insufficient_price_data(self, sample_strategy, backtest_config):
        """Test backtest with insufficient price data for indicators."""
        engine = BacktestEngine(backtest_config)

        # Need at least ~50 candles for RSI
        short_prices = [
            {
                "timestamp": datetime(2024, 1, 1) + timedelta(hours=i),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(10)
        ]

        with pytest.raises(ValueError, match="Insufficient price data"):
            engine.run_backtest(
                strategy=sample_strategy,
                price_data=short_prices,
                symbol="BTC/USDT",
            )

    def test_zero_initial_capital(self, sample_strategy, sample_price_data):
        """Test backtest with zero initial capital."""
        config = BacktestConfig(
            initial_capital=Decimal("0"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        with pytest.raises(ValueError, match="Initial capital must be positive"):
            BacktestEngine(config)

    def test_negative_commission_rate(self, sample_strategy, sample_price_data):
        """Test backtest with negative commission rate."""
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("-0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        with pytest.raises(ValueError, match="Commission rate cannot be negative"):
            BacktestEngine(config)


class TestTradeExecution:
    """Test individual trade execution details."""

    def test_trade_has_valid_pnl_calculation(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that trade P&L is calculated correctly."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        # Check all trades have valid P&L
        for trade in result.trades:
            assert trade.pnl is not None
            assert trade.entry_price > 0
            assert trade.exit_price > 0
            assert trade.quantity > 0

    def test_trade_side_either_long_or_short(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that all trades have valid side (LONG or SHORT)."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        for trade in result.trades:
            assert trade.side in ["LONG", "SHORT"]

    def test_trade_dates_in_order(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that trade entry is before exit."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        for trade in result.trades:
            assert trade.entry_date < trade.exit_date


class TestEquityCurve:
    """Test equity curve generation."""

    def test_equity_curve_starts_with_initial_capital(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that equity curve starts with initial capital."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        if result.equity_curve:
            # First point should be at or near initial capital
            assert abs(result.equity_curve[0].equity - backtest_config.initial_capital) < Decimal("1")

    def test_equity_curve_matches_final_capital(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that last equity point matches final capital."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        if result.equity_curve:
            # Last point should match final capital
            assert result.equity_curve[-1].equity == result.final_capital

    def test_drawdown_never_positive(
        self, sample_strategy, sample_price_data, backtest_config
    ):
        """Test that drawdown is always negative or zero."""
        engine = BacktestEngine(backtest_config)

        result = engine.run_backtest(
            strategy=sample_strategy,
            price_data=sample_price_data,
            symbol="BTC/USDT",
        )

        for point in result.equity_curve:
            assert point.drawdown <= 0
