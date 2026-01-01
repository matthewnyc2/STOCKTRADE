"""
Backtest Engine Service.

Executes trading strategies on historical price data to simulate performance.
Calculates performance metrics, simulates trades with slippage/commission, and
generates equity curves.

Key Features:
- Walk-forward backtesting on historical OHLCV data
- Realistic trade simulation with slippage and commission
- Comprehensive performance metrics (Sharpe, Sortino, Max DD, Win Rate, etc.)
- Position sizing and risk management
- Equity curve and drawdown tracking
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from models import (
    BacktestResult,
    EquityPoint,
    Signal,
    SignalType,
    Strategy,
    Trade,
)
from services.indicators import calculate_all_indicators
from services.signal_generator import SignalGenerator


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""

    initial_capital: Decimal
    commission_rate: Decimal = Decimal("0.001")  # 0.1% per trade
    slippage_rate: Decimal = Decimal("0.001")  # 0.1% per trade
    position_size_percent: Decimal = Decimal("1.0")  # 100% of capital per trade
    risk_free_rate: float = 0.02  # 2% annual for Sharpe/Sortino
    min_data_points: int = 50  # Minimum candles needed for indicators


@dataclass
class Position:
    """Open position during backtesting."""

    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: Decimal
    quantity: Decimal
    entry_date: datetime
    entry_signal: Signal


def calculate_sharpe_ratio(
    returns: list[float], risk_free_rate: float, periods_per_year: int = 252
) -> Optional[float]:
    """
    Calculate Sharpe Ratio.

    Sharpe = (mean_return - risk_free) / std_dev_return

    Args:
        returns: List of periodic returns
        risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%)
        periods_per_year: Number of trading periods per year (252 for daily)

    Returns:
        Sharpe ratio or None if insufficient data
    """
    if len(returns) < 2:
        return None

    mean_return = sum(returns) / len(returns)

    if len(returns) < 2:
        return None

    # Calculate standard deviation
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return None

    # Annualize
    daily_rf = risk_free_rate / periods_per_year
    sharpe = (mean_return - daily_rf) / std_dev * math.sqrt(periods_per_year)

    return sharpe


def calculate_sortino_ratio(
    returns: list[float], risk_free_rate: float, periods_per_year: int = 252
) -> Optional[float]:
    """
    Calculate Sortino Ratio.

    Sortino = (mean_return - risk_free) / downside_deviation

    Only considers downside volatility (negative returns).

    Args:
        returns: List of periodic returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year

    Returns:
        Sortino ratio or None if insufficient data
    """
    if len(returns) < 2:
        return None

    mean_return = sum(returns) / len(returns)

    # Calculate downside deviation (only negative returns)
    negative_returns = [r for r in returns if r < 0]

    if len(negative_returns) == 0:
        # No downside risk, infinite Sortino
        return float("inf")

    downside_variance = sum(r ** 2 for r in negative_returns) / len(returns)
    downside_deviation = math.sqrt(downside_variance)

    if downside_deviation == 0:
        return None

    # Annualize
    daily_rf = risk_free_rate / periods_per_year
    sortino = (mean_return - daily_rf) / downside_deviation * math.sqrt(periods_per_year)

    return sortino


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    """
    Calculate Maximum Drawdown.

    Max DD is the largest peak-to-trough decline.

    Args:
        equity_curve: List of portfolio values over time

    Returns:
        Maximum drawdown as a negative decimal (e.g., -0.15 for -15%)
    """
    if not equity_curve:
        return 0.0

    max_dd = 0.0
    peak = equity_curve[0]

    for value in equity_curve:
        if value > peak:
            peak = value

        drawdown = (value - peak) / peak if peak > 0 else 0
        max_dd = min(max_dd, drawdown)

    return max_dd


def calculate_win_rate(trades: list[dict[str, Any]]) -> Decimal:
    """
    Calculate Win Rate.

    Win Rate = Winning Trades / Total Trades

    Args:
        trades: List of trades with 'pnl' field

    Returns:
        Win rate as decimal (0.0 to 1.0)
    """
    if not trades:
        return Decimal("0")

    winners = sum(1 for t in trades if t.get("pnl", Decimal("0")) > 0)
    return Decimal(str(winners / len(trades))).quantize(Decimal("0.0001"))


def calculate_profit_factor(trades: list[dict[str, Any]]) -> Decimal:
    """
    Calculate Profit Factor.

    Profit Factor = Gross Profit / Gross Loss

    Args:
        trades: List of trades with 'pnl' field

    Returns:
        Profit factor (inf if no losses, 0 if no wins)
    """
    if not trades:
        return Decimal("0")

    gross_profit = sum(t.get("pnl", Decimal("0")) for t in trades if t.get("pnl", Decimal("0")) > 0)
    gross_loss = abs(sum(t.get("pnl", Decimal("0")) for t in trades if t.get("pnl", Decimal("0")) < 0))

    if gross_loss == 0:
        return Decimal(str(float("inf")))
    if gross_profit == 0:
        return Decimal("0")

    return Decimal(str(gross_profit / gross_loss)).quantize(Decimal("0.001"))


def calculate_expectancy(trades: list[dict[str, Any]]) -> Decimal:
    """
    Calculate Expectancy (average profit per trade).

    Expectancy = Total P&L / Number of Trades

    Args:
        trades: List of trades with 'pnl' field

    Returns:
        Average profit per trade
    """
    if not trades:
        return Decimal("0")

    total_pnl = sum(t.get("pnl", Decimal("0")) for t in trades)
    return Decimal(str(total_pnl / len(trades))).quantize(Decimal("0.01"))


class BacktestEngine:
    """
    Core backtesting engine.

    Simulates strategy execution on historical price data with realistic
    trade costs and generates comprehensive performance metrics.
    """

    def __init__(self, config: BacktestConfig) -> None:
        """
        Initialize the backtest engine.

        Args:
            config: Backtest configuration
        """
        if config.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if config.commission_rate < 0:
            raise ValueError("Commission rate cannot be negative")
        if config.slippage_rate < 0:
            raise ValueError("Slippage rate cannot be negative")

        self.config = config
        self.signal_generator = SignalGenerator()

    def run_backtest(
        self,
        strategy: Strategy,
        price_data: list[dict[str, Any]],
        symbol: str,
    ) -> BacktestResult:
        """
        Run a backtest for a strategy on historical price data.

        Args:
            strategy: The strategy to backtest
            price_data: List of OHLCV candles
            symbol: Trading symbol

        Returns:
            BacktestResult with metrics, trades, and equity curve

        Raises:
            ValueError: If insufficient price data
        """
        if len(price_data) < self.config.min_data_points:
            raise ValueError(
                f"Insufficient price data: need at least {self.config.min_data_points} candles, "
                f"got {len(price_data)}"
            )

        # Initialize backtest state
        cash = self.config.initial_capital
        open_position: Optional[Position] = None
        trades: list[Trade] = []
        equity_curve: list[EquityPoint] = []
        all_returns: list[float] = []

        # Extract price series for indicator calculation
        opens = [float(p["open"]) for p in price_data]
        highs = [float(p["high"]) for p in price_data]
        lows = [float(p["low"]) for p in price_data]
        closes = [float(p["close"]) for p in price_data]
        volumes = [float(p["volume"]) for p in price_data]

        # Calculate all indicators once
        indicators = calculate_all_indicators(opens, highs, lows, closes, volumes)

        # Start backtest from first valid indicator point
        # Need at least 50 candles for RSI and other indicators
        start_idx = min(self.config.min_data_points, len(price_data) - 1)
        if start_idx < 1:
            start_idx = 1

        # Record initial equity
        equity_curve.append(
            EquityPoint(
                timestamp=price_data[start_idx]["timestamp"],
                equity=cash,
                drawdown=Decimal("0"),
            )
        )

        # Walk through each candle
        for i in range(start_idx, len(price_data)):
            candle = price_data[i]
            timestamp = candle["timestamp"]
            close_price = Decimal(str(candle["close"]))

            # Build current indicator state (up to current index)
            current_indicators = {}
            for key, values in indicators.items():
                if values and i < len(values):
                    current_indicators[key] = values[: i + 1]

            # Generate signal
            signal = self.signal_generator.generate_signal(
                strategy=strategy,
                symbol=symbol,
                price_data={"close": float(closes[i])},
                indicators=current_indicators,
            )

            # Check if we have an open position
            if open_position:
                # Get the signal type as value string for comparison
                signal_value = signal.signal_type.value.upper() if isinstance(signal.signal_type, SignalType) else str(signal.signal_type).upper()
                position_side = str(open_position.side).upper()

                # Check for exit signal
                if signal.signal_type in [SignalType.CLOSE, SignalType.NEUTRAL]:
                    # Close position
                    trade = self._close_position(open_position, close_price, timestamp, "SIGNAL")
                    trades.append(trade)
                    cash += trade.pnl + (trade.entry_price * trade.quantity)  # Return cost + P&L
                    open_position = None
                elif signal_value != position_side:
                    # Opposite signal - flip position
                    # Close current
                    trade = self._close_position(open_position, close_price, timestamp, "SIGNAL")
                    trades.append(trade)
                    cash += trade.pnl + (trade.entry_price * trade.quantity)  # Return cost + P&L

                    # Open new position if signal is clear
                    if signal.signal_type in [SignalType.LONG, SignalType.SHORT]:
                        open_position = self._open_position(
                            cash, signal.signal_type, close_price, timestamp, signal, symbol
                        )
                        cash -= open_position.entry_price * open_position.quantity
                    else:
                        open_position = None
            else:
                # No open position, check for entry signal
                if signal.signal_type in [SignalType.LONG, SignalType.SHORT]:
                    open_position = self._open_position(
                        cash, signal.signal_type, close_price, timestamp, signal, symbol
                    )
                    cash -= open_position.entry_price * open_position.quantity

            # Calculate current equity (cash + position value)
            current_equity = cash
            if open_position:
                # Mark-to-market open position
                if open_position.side == "LONG":
                    position_value = close_price * open_position.quantity
                else:  # SHORT
                    # For short, value is cash + (entry - current) * quantity
                    position_value = open_position.entry_price * open_position.quantity + (open_position.entry_price - close_price) * open_position.quantity
                current_equity += position_value

            # Calculate return for this period
            prev_equity = equity_curve[-1].equity
            if prev_equity > 0:
                period_return = float((current_equity - prev_equity) / prev_equity)
                all_returns.append(period_return)

            # Calculate drawdown (only negative values, 0 if at peak)
            peak_equity = max(ep.equity for ep in equity_curve)
            if peak_equity > 0:
                drawdown = min(Decimal("0"), Decimal(str((current_equity - peak_equity) / peak_equity)))
            else:
                drawdown = Decimal("0")

            # Record equity point
            equity_curve.append(
                EquityPoint(
                    timestamp=timestamp,
                    equity=current_equity.quantize(Decimal("0.01")),
                    drawdown=Decimal(str(drawdown)).quantize(Decimal("0.0001")),
                )
            )

        # Close any remaining position at end
        if open_position:
            final_price = Decimal(str(price_data[-1]["close"]))
            trade = self._close_position(open_position, final_price, price_data[-1]["timestamp"], "END_OF_PERIOD")
            trades.append(trade)
            cash += trade.pnl + (trade.entry_price * trade.quantity)

        # Final equity
        final_capital = cash.quantize(Decimal("0.01"))

        # Calculate metrics
        total_return = (final_capital - self.config.initial_capital) / self.config.initial_capital

        # Convert trades to dicts for metric calculations
        trade_dicts = [{"pnl": t.pnl} for t in trades]

        max_dd = calculate_max_drawdown([float(ep.equity) for ep in equity_curve])
        sharpe = calculate_sharpe_ratio(all_returns, self.config.risk_free_rate)
        sortino = calculate_sortino_ratio(all_returns, self.config.risk_free_rate)
        win_rate = calculate_win_rate(trade_dicts)
        profit_factor = calculate_profit_factor(trade_dicts)
        expectancy = calculate_expectancy(trade_dicts)

        return BacktestResult(
            id=f"bt_{uuid4().hex[:8]}",
            strategy_id=strategy.id,
            start_date=price_data[start_idx]["timestamp"],
            end_date=price_data[-1]["timestamp"],
            initial_capital=self.config.initial_capital,
            final_capital=final_capital,
            total_return=Decimal(str(total_return)).quantize(Decimal("0.0001")),
            sharpe_ratio=Decimal(str(sharpe)) if sharpe is not None else None,
            sortino_ratio=Decimal(str(sortino)) if sortino is not None and not math.isinf(sortino) else None,
            max_drawdown=Decimal(str(max_dd)).quantize(Decimal("0.0001")),
            win_rate=win_rate,
            profit_factor=profit_factor if not math.isinf(float(profit_factor)) else None,
            total_trades=len(trades),
            equity_curve=equity_curve,
            trades=trades,
        )

    def _open_position(
        self,
        capital: Decimal,
        side: str | SignalType,
        price: Decimal,
        timestamp: datetime,
        signal: Signal,
        symbol: str,
    ) -> Position:
        """Open a new position with proper sizing."""
        # Convert SignalType to string if needed
        if isinstance(side, SignalType):
            side_str = side.value.upper()
        else:
            side_str = str(side).upper()

        # Apply slippage
        entry_price = self._apply_slippage(price, side_str)

        # Calculate position size (fixed % of capital)
        position_value = capital * self.config.position_size_percent

        # Subtract commission from available capital
        commission = position_value * self.config.commission_rate
        available_for_position = position_value - commission

        quantity = (available_for_position / entry_price).quantize(Decimal("0.00000001"))

        return Position(
            symbol=symbol,
            side=side_str,
            entry_price=entry_price,
            quantity=quantity,
            entry_date=timestamp,
            entry_signal=signal,
        )

    def _close_position(
        self,
        position: Position,
        price: Decimal,
        timestamp: datetime,
        exit_reason: str,
    ) -> Trade:
        """Close an open position and calculate P&L."""
        # Ensure side is a string
        side_str = str(position.side).upper() if position.side else "LONG"

        # Apply slippage to exit price (opposite of entry side)
        exit_slippage_side = "SHORT" if side_str == "LONG" else "LONG"
        exit_price = self._apply_slippage(price, exit_slippage_side)

        # Calculate P&L
        if side_str == "LONG":
            gross_pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            gross_pnl = (position.entry_price - exit_price) * position.quantity

        # Subtract commission
        entry_value = position.entry_price * position.quantity
        exit_value = exit_price * position.quantity
        total_commission = (entry_value + exit_value) * self.config.commission_rate

        net_pnl = gross_pnl - total_commission

        # Calculate P&L percentage
        pnl_percent = (net_pnl / entry_value * 100) if entry_value > 0 else Decimal("0")

        return Trade(
            id=f"trade_{uuid4().hex[:12]}",
            symbol=position.symbol,
            entry_date=position.entry_date,
            exit_date=timestamp,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            side=side_str,
            pnl=net_pnl.quantize(Decimal("0.01")),
            pnl_percent=pnl_percent.quantize(Decimal("0.01")),
            exit_reason=exit_reason,
        )

    def _apply_slippage(self, price: Decimal, side: str) -> Decimal:
        """
        Apply slippage to price.

        For LONG: slippage increases entry price (worse for trader)
        For SHORT: slippage decreases entry price (worse for trader)

        Args:
            price: Original price
            side: Trade side ("LONG" or "SHORT")

        Returns:
            Price with slippage applied
        """
        if side == "LONG":
            # Buying: we pay more
            return price * (Decimal("1") + self.config.slippage_rate)
        else:
            # Selling: we receive less
            return price * (Decimal("1") - self.config.slippage_rate)

    def _calculate_trade_costs(
        self,
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: Decimal,
        side: str,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calculate trade costs including commission.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Position size
            side: Trade side

        Returns:
            Tuple of (entry_cost, exit_value, total_commission)
        """
        entry_value = entry_price * quantity
        exit_value = exit_price * quantity
        total_commission = (entry_value + exit_value) * self.config.commission_rate

        return entry_value, exit_value, total_commission
