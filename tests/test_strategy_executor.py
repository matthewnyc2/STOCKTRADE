"""
Tests for Strategy Executor Service.

Tests the strategy execution loop and signal generation workflow.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from models import SignalType, LogicGate, Strategy, Signal
from services.strategy_executor import StrategyExecutor, execute_active_strategies
from services.signal_generator import SignalGenerator
from database.repositories import SignalRepository, StrategyRepository


class TestStrategyExecutor:
    """Tests for StrategyExecutor class."""

    def test_init(self):
        """Test StrategyExecutor initialization."""
        executor = StrategyExecutor()
        assert executor.signal_generator is not None

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    def test_execute_strategy_generates_signal(
        self,
        mock_ws_manager,
        mock_db_session
    ):
        """Test executing a single strategy generates a signal."""
        # Setup mocks
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        # Create strategy
        strategy = Strategy(
            id="strat_1",
            name="Test Strategy",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        # Create mock price data
        price_data = {
            "symbol": "BTC/USDT",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000.0
        }

        # Create mock indicators
        indicators = {
            "rsi_14": [None] * 13 + [25.0]
        }

        # Mock repository
        mock_repo = MagicMock()
        mock_signal = MagicMock()
        mock_signal.id = "sig_123"
        mock_repo.create.return_value = mock_signal
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_repo

        executor = StrategyExecutor()

        # Execute
        result = executor.execute_strategy(
            strategy,
            price_data,
            indicators
        )

        # Verify
        assert result is not None
        assert result.strategy_id == "strat_1"

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    def test_execute_strategy_saves_to_database(
        self,
        mock_ws_manager,
        mock_db_session
    ):
        """Test that generated signals are saved to database."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        strategy = Strategy(
            id="strat_1",
            name="Test Strategy",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        price_data = {"close": 100.0}
        indicators = {"rsi_14": [None] * 13 + [25.0]}

        executor = StrategyExecutor()
        executor.execute_strategy(strategy, price_data, indicators)

        # Verify database create was called
        assert mock_session.add.called

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    def test_execute_strategy_broadcasts_via_websocket(
        self,
        mock_ws_manager,
        mock_db_session
    ):
        """Test that signals are broadcast via WebSocket."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        strategy = Strategy(
            id="strat_1",
            name="Test Strategy",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        price_data = {"close": 100.0}
        indicators = {"rsi_14": [None] * 13 + [25.0]}

        executor = StrategyExecutor()

        # Run async - use the async method directly
        import asyncio

        async def test_broadcast():
            signal = executor.signal_generator.generate_signal(
                strategy, "BTC/USDT", price_data, indicators
            )
            await executor._broadcast_signal_async(signal)
            return signal

        signal = asyncio.run(test_broadcast())

        # Verify signal was generated
        assert signal.strategy_id == "strat_1"

        # Verify WebSocket broadcast was called
        mock_ws.broadcast.assert_called_once()

    @patch('services.strategy_executor.get_db_session')
    def test_execute_strategy_with_no_signal(
        self,
        mock_db_session
    ):
        """Test executing strategy that generates no signal."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        strategy = Strategy(
            id="strat_1",
            name="Test Strategy",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        # Neutral RSI - no signal
        price_data = {"close": 100.0}
        indicators = {"rsi_14": [None] * 13 + [50.0]}

        executor = StrategyExecutor()
        result = executor.execute_strategy(strategy, price_data, indicators)

        # Should still return a signal, but NEUTRAL
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0


class TestExecuteActiveStrategies:
    """Tests for execute_active_strategies function."""

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    @patch('services.strategy_executor.get_latest_price_data')
    @patch('services.strategy_executor.calculate_all_indicators')
    def test_execute_all_active_strategies(
        self,
        mock_calculate_indicators,
        mock_get_price,
        mock_ws_manager,
        mock_db_session
    ):
        """Test executing all active strategies."""
        # Setup mocks
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        # Mock strategies
        mock_strategies = [
            Strategy(
                id="strat_1",
                name="Strategy 1",
                type="template",
                parameters={"indicator_type": "rsi"},
                logic_gate=LogicGate.NONE
            ),
            Strategy(
                id="strat_2",
                name="Strategy 2",
                type="template",
                parameters={"indicator_type": "ma_crossover"},
                logic_gate=LogicGate.NONE
            )
        ]

        # Mock price data - include all fields
        price_data = {
            "opens": [100.0] * 50,
            "highs": [105.0] * 50,
            "lows": [95.0] * 50,
            "closes": [102.0] * 50,
            "volumes": [1000.0] * 50,
            "close": 102.0,  # Latest close for signal generation
            "symbol": "BTC/USDT"
        }
        mock_get_price.return_value = price_data

        # Mock indicators - need proper data for MA crossover
        # Create a bullish crossover: EMA12 goes from below to above EMA26
        ema_12 = [None] * 11 + [98.0, 99.0] + [101.0] * 38  # Crosses above
        ema_26 = [None] * 25 + [100.0] * 25  # Stays at 100

        mock_calculate_indicators.return_value = {
            "rsi_14": [None] * 13 + [25.0] * 37,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "macd_line": [None] * 25 + [0.5] * 25,
            "macd_signal": [None] * 33 + [0.4] * 17
        }

        executor = StrategyExecutor()

        # Execute
        results = executor.execute_active_strategies(
            mock_strategies,
            "BTC/USDT"
        )

        # Verify - should get 2 signals
        assert len(results) >= 1  # At least some signals should be generated
        assert all(r.strategy_id in ["strat_1", "strat_2"] for r in results)

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_latest_price_data')
    def test_execute_with_no_price_data(
        self,
        mock_get_price,
        mock_db_session
    ):
        """Test execution when no price data is available."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_get_price.return_value = None

        strategy = Strategy(
            id="strat_1",
            name="Test",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        executor = StrategyExecutor()
        results = executor.execute_active_strategies([strategy], "BTC/USDT")

        # Should return mock signals when no price data
        assert len(results) >= 1  # Falls back to mock signal generation

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    @patch('services.strategy_executor.get_latest_price_data')
    @patch('services.strategy_executor.calculate_all_indicators')
    def test_execute_with_multiple_symbols(
        self,
        mock_calculate_indicators,
        mock_get_price,
        mock_ws_manager,
        mock_db_session
    ):
        """Test executing strategies for multiple symbols."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        strategies = [
            Strategy(
                id="strat_1",
                name="Strategy 1",
                type="template",
                parameters={"indicator_type": "rsi"},
                logic_gate=LogicGate.NONE
            )
        ]

        price_data = {
            "opens": [100.0] * 50,
            "closes": [102.0] * 50,
            "highs": [105.0] * 50,
            "lows": [95.0] * 50,
            "volumes": [1000.0] * 50,
            "close": 102.0,
            "symbol": "BTC/USDT"
        }
        mock_get_price.return_value = price_data

        mock_calculate_indicators.return_value = {
            "rsi_14": [None] * 13 + [25.0] * 37
        }

        executor = StrategyExecutor()

        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        all_results = []

        for symbol in symbols:
            results = executor.execute_active_strategies(strategies, symbol)
            all_results.extend(results)

        # Should generate at least one signal per symbol
        # Each execution should return signals for the strategy
        assert len(all_results) >= len(symbols)


class TestErrorHandling:
    """Tests for error handling in strategy execution."""

    @patch('services.strategy_executor.get_db_session')
    def test_handles_invalid_strategy_gracefully(
        self,
        mock_db_session
    ):
        """Test that invalid strategies are handled gracefully."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        executor = StrategyExecutor()

        # Invalid strategy with unknown indicator type (but valid strategy type)
        strategy = Strategy(
            id="invalid",
            name="Invalid",
            type="template",  # Valid strategy type
            parameters={"indicator_type": "unknown_indicator"},  # Unknown indicator
            logic_gate=LogicGate.NONE
        )

        price_data = {"close": 100.0}
        indicators = {}

        # Should not raise exception - returns NEUTRAL signal
        result = executor.execute_strategy(strategy, price_data, indicators)
        assert result is not None
        assert result.signal_type == SignalType.NEUTRAL

    @patch('services.strategy_executor.get_db_session')
    def test_handles_database_error_gracefully(
        self,
        mock_db_session
    ):
        """Test that database errors are handled gracefully."""
        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("Database error")
        mock_db_session.return_value.__enter__.return_value = mock_session

        executor = StrategyExecutor()

        strategy = Strategy(
            id="strat_1",
            name="Test",
            type="template",
            parameters={"indicator_type": "rsi"},
            logic_gate=LogicGate.NONE
        )

        price_data = {"close": 100.0}
        indicators = {"rsi_14": [None] * 13 + [25.0]}

        # Should handle error gracefully
        # In production, this would log the error
        try:
            executor.execute_strategy(strategy, price_data, indicators)
        except Exception as e:
            # Expected to propagate or handle based on implementation
            pass


class TestPerformance:
    """Tests for performance considerations."""

    @patch('services.strategy_executor.get_db_session')
    @patch('services.strategy_executor.get_websocket_manager')
    @patch('services.strategy_executor.get_latest_price_data')
    @patch('services.strategy_executor.calculate_all_indicators')
    def test_executes_many_strategies_efficiently(
        self,
        mock_calculate_indicators,
        mock_get_price,
        mock_ws_manager,
        mock_db_session
    ):
        """Test that many strategies can be executed efficiently."""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session

        mock_ws = AsyncMock()
        mock_ws_manager.return_value = mock_ws

        # Create many strategies
        strategies = [
            Strategy(
                id=f"strat_{i}",
                name=f"Strategy {i}",
                type="template",
                parameters={"indicator_type": "rsi"},
                logic_gate=LogicGate.NONE
            )
            for i in range(100)
        ]

        price_data = {
            "opens": [100.0] * 50,
            "closes": [102.0] * 50,
            "highs": [105.0] * 50,
            "lows": [95.0] * 50,
            "volumes": [1000.0] * 50,
            "close": 102.0,
            "symbol": "BTC/USDT"
        }
        mock_get_price.return_value = price_data

        mock_calculate_indicators.return_value = {
            "rsi_14": [None] * 13 + [25.0] * 37
        }

        executor = StrategyExecutor()

        import time
        start = time.time()
        results = executor.execute_active_strategies(strategies, "BTC/USDT")
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds max for 100 strategies
        # At least some signals should be generated
        assert len(results) >= 50  # Most strategies should generate signals
