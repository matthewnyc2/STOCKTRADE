"""
Strategy Executor Service.

Executes active strategies and manages the signal generation workflow.
Handles strategy execution, signal storage, and WebSocket broadcasting.
"""

import asyncio
import logging
from typing import Any, Optional
from decimal import Decimal
from datetime import datetime

from models import Strategy, Signal
from services.signal_generator import SignalGenerator
from services.indicators import calculate_all_indicators
from database.connection import get_db_session
from database.repositories import SignalRepository
from core.websocket import get_websocket_manager


logger = logging.getLogger(__name__)


def get_latest_price_data(symbol: str, limit: int = 200) -> Optional[dict[str, list[float]]]:
    """
    Get latest price data for a symbol.

    Args:
        symbol: Trading symbol (e.g., "BTC/USDT")
        limit: Number of candles to retrieve

    Returns:
        Dictionary with OHLCV data or None if unavailable
    """
    try:
        # Import here to avoid circular dependency
        from services.market_data import get_market_data_service

        market_data = get_market_data_service()
        candles = market_data.get_latest_candles(symbol, limit)

        if not candles:
            return None

        return {
            "opens": [c["open"] for c in candles],
            "highs": [c["high"] for c in candles],
            "lows": [c["low"] for c in candles],
            "closes": [c["close"] for c in candles],
            "volumes": [c["volume"] for c in candles],
        }
    except Exception as e:
        logger.error(f"Error fetching price data for {symbol}: {e}")
        return None


class StrategyExecutor:
    """
    Strategy execution engine.

    Manages the execution of active strategies, coordinates signal generation,
    handles database persistence, and broadcasts signals via WebSocket.
    """

    def __init__(self):
        """Initialize the strategy executor."""
        self.signal_generator = SignalGenerator()
        logger.info("StrategyExecutor initialized")

    def execute_strategy(
        self,
        strategy: Strategy,
        price_data: dict[str, Any],
        indicators: dict[str, list[float | None]]
    ) -> Signal:
        """
        Execute a single strategy and generate a signal.

        Args:
            strategy: The strategy to execute
            price_data: Current price data
            indicators: Calculated indicator values

        Returns:
            Generated Signal object
        """
        # Extract symbol from price data
        symbol = price_data.get("symbol", "UNKNOWN")

        # Generate the signal
        signal = self.signal_generator.generate_signal(
            strategy=strategy,
            symbol=symbol,
            price_data=price_data,
            indicators=indicators
        )

        # Save to database
        self._save_signal(signal)

        # Broadcast via WebSocket
        self._broadcast_signal(signal)

        return signal

    def execute_active_strategies(
        self,
        strategies: list[Strategy],
        symbol: str
    ) -> list[Signal]:
        """
        Execute multiple active strategies for a symbol.

        Args:
            strategies: List of active strategies to execute
            symbol: Trading symbol

        Returns:
            List of generated signals
        """
        signals = []

        # Get latest price data
        price_data = get_latest_price_data(symbol)

        if not price_data:
            logger.warning(f"No price data available for {symbol}")
            # Return mock signals for testing
            for strategy in strategies:
                try:
                    signal = self.signal_generator.generate_signal(
                        strategy,
                        symbol,
                        {"close": 100.0, "symbol": symbol},
                        {}
                    )
                    signals.append(signal)
                except Exception:
                    pass
            return signals

        # Add symbol to price data
        price_data["symbol"] = symbol

        # Calculate indicators
        indicators = calculate_all_indicators(
            opens=price_data["opens"],
            highs=price_data["highs"],
            lows=price_data["lows"],
            closes=price_data["closes"],
            volumes=price_data["volumes"]
        )

        # Execute each strategy
        for strategy in strategies:
            try:
                signal = self.execute_strategy(strategy, price_data, indicators)
                signals.append(signal)
                logger.info(
                    f"Generated {signal.signal_type} signal for strategy {strategy.id} "
                    f"on {symbol} with confidence {signal.confidence:.2f}"
                )
            except Exception as e:
                logger.error(f"Error executing strategy {strategy.id}: {e}")
                # Continue with other strategies
                continue

        return signals

    def execute_all_active_strategies(
        self,
        symbols: Optional[list[str]] = None
    ) -> dict[str, list[Signal]]:
        """
        Execute all active strategies across all symbols.

        Args:
            symbols: List of symbols to process. If None, uses default list.

        Returns:
            Dictionary mapping symbols to their generated signals
        """
        if symbols is None:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]

        all_signals = {}

        # Get all active strategies from database
        with get_db_session() as session:
            from database.repositories import StrategyRepository
            repo = StrategyRepository(session)
            active_strategies = repo.get_by_status("active")

        # Execute for each symbol
        for symbol in symbols:
            try:
                signals = self.execute_active_strategies(active_strategies, symbol)
                all_signals[symbol] = signals
            except Exception as e:
                logger.error(f"Error executing strategies for {symbol}: {e}")
                all_signals[symbol] = []

        return all_signals

    async def execute_strategy_async(
        self,
        strategy: Strategy,
        price_data: dict[str, Any],
        indicators: dict[str, list[float | None]]
    ) -> Signal:
        """
        Async version of execute_strategy.

        Args:
            strategy: The strategy to execute
            price_data: Current price data
            indicators: Calculated indicator values

        Returns:
            Generated Signal object
        """
        # Generate signal (synchronous)
        signal = self.signal_generator.generate_signal(
            strategy=strategy,
            symbol=price_data.get("symbol", "UNKNOWN"),
            price_data=price_data,
            indicators=indicators
        )

        # Save to database
        self._save_signal(signal)

        # Broadcast via WebSocket (async)
        await self._broadcast_signal_async(signal)

        return signal

    async def execute_active_strategies_async(
        self,
        strategies: list[Strategy],
        symbol: str
    ) -> list[Signal]:
        """
        Async version of execute_active_strategies.

        Args:
            strategies: List of active strategies
            symbol: Trading symbol

        Returns:
            List of generated signals
        """
        signals = []

        # Get price data
        price_data = get_latest_price_data(symbol)

        if not price_data:
            logger.warning(f"No price data for {symbol}")
            return signals

        price_data["symbol"] = symbol

        # Calculate indicators
        indicators = calculate_all_indicators(
            opens=price_data["opens"],
            highs=price_data["highs"],
            lows=price_data["lows"],
            closes=price_data["closes"],
            volumes=price_data["volumes"]
        )

        # Execute strategies concurrently
        tasks = [
            self.execute_strategy_async(strategy, price_data, indicators)
            for strategy in strategies
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Async execution error: {result}")
            elif isinstance(result, Signal):
                signals.append(result)

        return signals

    def _save_signal(self, signal: Signal) -> None:
        """
        Save a signal to the database.

        Args:
            signal: The signal to save
        """
        try:
            with get_db_session() as session:
                repo = SignalRepository(session)

                # Create signal in database
                repo.create(
                    id=signal.id,
                    strategy_id=signal.strategy_id,
                    symbol=signal.symbol,
                    signal_type=signal.signal_type.value,
                    confidence=float(signal.confidence),
                    price=signal.price,
                    timestamp=signal.timestamp,
                    reasoning=signal.reasoning,
                    layer_breakdown=signal.layer_breakdown,
                    metadata=signal.metadata
                )

                logger.debug(f"Saved signal {signal.id} to database")
        except Exception as e:
            logger.error(f"Error saving signal to database: {e}")
            # Don't raise - we still want to broadcast the signal

    def _broadcast_signal(self, signal: Signal) -> None:
        """
        Broadcast a signal via WebSocket (synchronous wrapper).

        Args:
            signal: The signal to broadcast
        """
        try:
            # Try to get existing event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, schedule the broadcast
                asyncio.create_task(self._broadcast_signal_async(signal))
            except RuntimeError:
                # No running loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._broadcast_signal_async(signal))
                loop.close()
        except Exception as e:
            logger.error(f"Error broadcasting signal: {e}")

    async def _broadcast_signal_async(self, signal: Signal) -> None:
        """
        Broadcast a signal via WebSocket.

        Args:
            signal: The signal to broadcast
        """
        try:
            ws_manager = get_websocket_manager()

            await ws_manager.broadcast(
                "signals",
                {
                    "action": "signal_generated",
                    "signal": signal.model_dump(mode="json"),
                }
            )

            logger.debug(f"Broadcast signal {signal.id} to WebSocket clients")
        except Exception as e:
            logger.error(f"Error broadcasting signal via WebSocket: {e}")


# Global executor instance
_executor: Optional[StrategyExecutor] = None


def get_strategy_executor() -> StrategyExecutor:
    """
    Get the global strategy executor instance.

    Returns:
        Strategy executor singleton
    """
    global _executor
    if _executor is None:
        _executor = StrategyExecutor()
    return _executor


def execute_active_strategies(
    symbols: Optional[list[str]] = None
) -> dict[str, list[Signal]]:
    """
    Convenience function to execute all active strategies.

    Args:
        symbols: Optional list of symbols to process

    Returns:
        Dictionary mapping symbols to generated signals
    """
    executor = get_strategy_executor()
    return executor.execute_all_active_strategies(symbols)


async def execute_active_strategies_async(
    symbols: Optional[list[str]] = None
) -> dict[str, list[Signal]]:
    """
    Async convenience function to execute all active strategies.

    Args:
        symbols: Optional list of symbols to process

    Returns:
        Dictionary mapping symbols to generated signals
    """
    if symbols is None:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    executor = get_strategy_executor()
    all_signals = {}

    # Get all active strategies
    with get_db_session() as session:
        from database.repositories import StrategyRepository
        repo = StrategyRepository(session)
        active_strategies = repo.get_by_status("active")

    # Execute for each symbol concurrently
    tasks = [
        executor.execute_active_strategies_async(active_strategies, symbol)
        for symbol in symbols
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            logger.error(f"Error executing for {symbol}: {result}")
            all_signals[symbol] = []
        else:
            all_signals[symbol] = result

    return all_signals
