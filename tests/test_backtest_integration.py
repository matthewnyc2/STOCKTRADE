"""
Integration tests for the Backtest Engine API.

Tests the full flow from API request to backtest execution and result storage.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from models import BacktestResult, Strategy, StrategyType
from services.backtest_engine import BacktestEngine, BacktestConfig


@pytest.fixture
def trending_price_data():
    """Generate price data with a clear uptrend then downtrend."""
    prices = []
    base_time = datetime(2024, 1, 1)
    base_price = 100.0

    # First 50 candles: uptrend
    for i in range(50):
        change = i * 0.5  # Gradual increase
        open_price = base_price + change
        close_price = open_price + 0.3
        high_price = close_price + 0.2
        low_price = open_price - 0.1
        volume = 1000000 + i * 10000

        prices.append({
            "timestamp": base_time + timedelta(hours=i),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        })

    # Next 50 candles: downtrend
    for i in range(50, 100):
        change = (100 - i) * 0.5  # Gradual decrease
        open_price = base_price + change + 25
        close_price = open_price - 0.3
        high_price = open_price + 0.1
        low_price = close_price - 0.2
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


class TestBacktestIntegration:
    """Integration tests for complete backtest flow."""

    def test_full_backtest_workflow(self, trending_price_data):
        """Test complete backtest workflow from start to finish."""
        # Create a simple RSI strategy
        strategy = Strategy(
            id="strat_integration_test",
            name="Integration Test RSI Strategy",
            type=StrategyType.COMPOSED,
            description="RSI strategy for integration testing",
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
            },
            status="active",
        )

        # Configure backtest
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        # Run backtest
        engine = BacktestEngine(config)
        result = engine.run_backtest(
            strategy=strategy,
            price_data=trending_price_data,
            symbol="BTC/USDT",
        )

        # Verify result structure
        assert isinstance(result, BacktestResult)
        assert result.strategy_id == strategy.id
        assert len(result.equity_curve) > 0

        # Verify date range
        assert result.start_date == trending_price_data[50]["timestamp"]
        assert result.end_date == trending_price_data[-1]["timestamp"]

        # Verify capital tracking
        assert result.initial_capital == Decimal("10000")
        assert result.final_capital > 0

        # Verify metrics are calculated
        assert result.total_return is not None
        assert result.max_drawdown is not None
        assert result.win_rate is not None
        assert result.total_trades >= 0

    def test_backtest_result_serialization(self, trending_price_data):
        """Test that backtest results can be serialized to JSON."""
        strategy = Strategy(
            id="strat_serialize_test",
            name="Serialization Test Strategy",
            type=StrategyType.COMPOSED,
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
            },
        )

        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        engine = BacktestEngine(config)
        result = engine.run_backtest(
            strategy=strategy,
            price_data=trending_price_data,
            symbol="ETH/USDT",
        )

        # Convert to dict (simulating JSON serialization)
        result_dict = result.model_dump()

        # Verify all fields are present
        assert "id" in result_dict
        assert "strategy_id" in result_dict
        assert "total_return" in result_dict
        assert "sharpe_ratio" in result_dict
        assert "max_drawdown" in result_dict
        assert "win_rate" in result_dict
        assert "total_trades" in result_dict
        assert "equity_curve" in result_dict
        assert "trades" in result_dict

        # Verify equity curve serialization
        assert len(result_dict["equity_curve"]) > 0
        equity_point = result_dict["equity_curve"][0]
        assert "timestamp" in equity_point
        assert "equity" in equity_point
        assert "drawdown" in equity_point

    def test_multiple_strategies_comparison(self, trending_price_data):
        """Test comparing backtest results from multiple strategies."""
        # RSI Strategy
        rsi_strategy = Strategy(
            id="strat_rsi_compare",
            name="RSI Comparison Strategy",
            type=StrategyType.COMPOSED,
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
            },
        )

        # MACD Strategy (simulated with different parameters)
        macd_strategy = Strategy(
            id="strat_macd_compare",
            name="MACD Comparison Strategy",
            type=StrategyType.COMPOSED,
            parameters={
                "indicator_type": "macd",
            },
        )

        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
        )

        engine = BacktestEngine(config)

        # Run both backtests
        rsi_result = engine.run_backtest(
            strategy=rsi_strategy,
            price_data=trending_price_data,
            symbol="BTC/USDT",
        )

        macd_result = engine.run_backtest(
            strategy=macd_strategy,
            price_data=trending_price_data,
            symbol="BTC/USDT",
        )

        # Both should have results
        assert rsi_result.total_trades >= 0
        assert macd_result.total_trades >= 0

        # Results may differ
        # (different strategies produce different trades)

    def test_backtest_with_different_capital_levels(self, trending_price_data):
        """Test backtest behavior with different initial capital levels."""
        strategy = Strategy(
            id="strat_capital_test",
            name="Capital Level Test Strategy",
            type=StrategyType.COMPOSED,
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
            },
        )

        # Test with different capital levels
        capital_levels = [
            Decimal("1000"),
            Decimal("10000"),
            Decimal("100000"),
        ]

        results = []
        for capital in capital_levels:
            config = BacktestConfig(
                initial_capital=capital,
                commission_rate=Decimal("0.001"),
                slippage_rate=Decimal("0.001"),
            )

            engine = BacktestEngine(config)
            result = engine.run_backtest(
                strategy=strategy,
                price_data=trending_price_data,
                symbol="BTC/USDT",
            )

            results.append(result)

            # Verify initial capital is preserved in result
            assert result.initial_capital == capital

        # All should have the same return percentage (same trades, different scale)
        # Allow for small rounding differences
        returns = [float(r.total_return) for r in results]
        max_return_diff = max(returns) - min(returns)
        assert max_return_diff < 0.01  # Less than 1% difference


class TestExampleBacktestOutput:
    """Tests that generate example backtest output for documentation."""

    def test_example_backtest_output(self, trending_price_data):
        """Generate and display example backtest output."""
        strategy = Strategy(
            id="strat_example",
            name="Example RSI Strategy",
            type=StrategyType.COMPOSED,
            description="A simple RSI-based strategy that goes long when RSI < 30 and short when RSI > 70",
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
            },
        )

        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),  # 0.1% per trade
            slippage_rate=Decimal("0.001"),  # 0.1% per trade
        )

        engine = BacktestEngine(config)
        result = engine.run_backtest(
            strategy=strategy,
            price_data=trending_price_data,
            symbol="BTC/USDT",
        )

        # Print example output (useful for documentation)
        print("\n" + "=" * 60)
        print("EXAMPLE BACKTEST RESULT")
        print("=" * 60)
        print(f"Strategy: {result.strategy_id}")
        print(f"Symbol: BTC/USDT")
        print(f"Period: {result.start_date} to {result.end_date}")
        print(f"Initial Capital: ${result.initial_capital:,.2f}")
        print(f"Final Capital: ${result.final_capital:,.2f}")
        print(f"Total Return: {float(result.total_return) * 100:.2f}%")
        print(f"Sharpe Ratio: {float(result.sharpe_ratio) if result.sharpe_ratio else 'N/A':.2f}")
        print(f"Sortino Ratio: {float(result.sortino_ratio) if result.sortino_ratio else 'N/A':.2f}")
        print(f"Max Drawdown: {float(result.max_drawdown) * 100:.2f}%")
        print(f"Win Rate: {float(result.win_rate) * 100:.2f}%")
        print(f"Profit Factor: {float(result.profit_factor) if result.profit_factor else 'N/A':.2f}")
        print(f"Total Trades: {result.total_trades}")
        print("=" * 60)

        if result.trades:
            print(f"\nFirst Trade Example:")
            trade = result.trades[0]
            print(f"  Side: {trade.side}")
            print(f"  Entry: ${trade.entry_price:.2f}")
            print(f"  Exit: ${trade.exit_price:.2f}")
            print(f"  P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")

        # Verify output is valid
        assert isinstance(result, BacktestResult)
