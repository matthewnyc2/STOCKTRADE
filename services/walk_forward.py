"""
Walk-Forward Optimization Service.

Divides data into rolling in-sample (training) and out-of-sample (testing) periods
to validate strategy robustness over time and detect parameter degradation.

Key Features:
- Rolling window walk-forward analysis
- Configurable in-sample percentage (default 70%)
- Parameter stability tracking across periods
- Aggregated performance metrics
- Period-by-period breakdown for analysis
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import numpy as np

from models.backtest import BacktestResult
from models.strategy import Strategy
from services.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_win_rate,
    calculate_profit_factor,
)


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward optimization."""

    in_sample_pct: float = 0.7  # Percentage of data for training (default 70%)
    window_size: Optional[int] = None  # Number of periods per window (None = auto)
    min_points_per_window: int = 100  # Minimum data points per window
    step_size: Optional[int] = None  # Step size for rolling (None = auto)
    commission_rate: Decimal = Decimal("0.001")
    slippage_rate: Decimal = Decimal("0.001")
    position_size_percent: Decimal = Decimal("1.0")
    risk_free_rate: float = 0.02


@dataclass
class WalkForwardPeriod:
    """Results from a single walk-forward period."""

    period_number: int
    in_sample_start: datetime
    in_sample_end: datetime
    out_of_sample_start: datetime
    out_of_sample_end: datetime

    # In-sample (training) results
    in_sample_return: float
    in_sample_sharpe: Optional[float]
    in_sample_max_drawdown: float
    in_sample_trades: int

    # Out-of-sample (testing) results
    out_of_sample_return: float
    out_of_sample_sharpe: Optional[float]
    out_of_sample_max_drawdown: float
    out_of_sample_trades: int

    # Optimized parameters (if optimization was performed)
    optimized_parameters: dict[str, Any] = field(default_factory=dict)

    # Performance degradation (in-sample vs out-of-sample)
    return_degradation: float = 0.0  # Positive means OOS performed worse


@dataclass
class WalkForwardResult:
    """Aggregated results from walk-forward optimization."""

    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    total_periods: int

    # Configuration
    in_sample_pct: float
    window_size: Optional[int]

    # Period-by-period results
    periods: list[WalkForwardPeriod]

    # Aggregated out-of-sample performance (what matters)
    avg_oos_return: float
    std_oos_return: float
    avg_oos_sharpe: float
    avg_oos_max_drawdown: float
    total_oos_trades: int

    # Win rate across periods (periods with positive return)
    period_win_rate: float

    # Parameter stability metrics
    parameter_stability_score: float  # 0-1, higher = more stable
    return_correlation_in_vs_oos: float  # Correlation between IS and OOS returns

    # Performance degradation tracking
    avg_return_degradation: float
    worst_period_return: float
    best_period_return: float

    # Consistency metrics
    positive_periods: int
    negative_periods: int

    def get_period_results(self) -> list[dict[str, Any]]:
        """Get period results as list of dicts for serialization."""
        return [
            {
                "period_number": p.period_number,
                "in_sample": {
                    "start": p.in_sample_start.isoformat(),
                    "end": p.in_sample_end.isoformat(),
                    "return": p.in_sample_return,
                    "sharpe": p.in_sample_sharpe,
                    "max_drawdown": p.in_sample_max_drawdown,
                    "trades": p.in_sample_trades,
                },
                "out_of_sample": {
                    "start": p.out_of_sample_start.isoformat(),
                    "end": p.out_of_sample_end.isoformat(),
                    "return": p.out_of_sample_return,
                    "sharpe": p.out_of_sample_sharpe,
                    "max_drawdown": p.out_of_sample_max_drawdown,
                    "trades": p.out_of_sample_trades,
                },
                "optimized_parameters": p.optimized_parameters,
                "return_degradation": p.return_degradation,
            }
            for p in self.periods
        ]


def _calculate_window_config(
    total_data_points: int,
    config: WalkForwardConfig,
) -> tuple[int, int]:
    """
    Calculate optimal window size and step size based on data and config.

    Args:
        total_data_points: Total number of data points available
        config: Walk-forward configuration

    Returns:
        Tuple of (window_size, step_size)
    """
    # Determine window size
    if config.window_size is not None:
        window_size = config.window_size
    else:
        # Auto-calculate: aim for at least 3-4 periods
        # Each period needs in-sample + out-of-sample
        # Window is the total size (IS + OOS)
        # We want at least config.min_points_per_window for OOS
        oos_size = max(config.min_points_per_window, int(total_data_points * (1 - config.in_sample_pct) / 4))
        in_sample_size = int(oos_size * config.in_sample_pct / (1 - config.in_sample_pct))
        window_size = in_sample_size + oos_size

    # Determine step size
    if config.step_size is not None:
        step_size = config.step_size
    else:
        # Default: step by the out-of-sample portion
        oos_size = int(window_size * (1 - config.in_sample_pct))
        step_size = max(oos_size, config.min_points_per_window // 2)

    return window_size, step_size


def _run_backtest_on_window(
    strategy: Strategy,
    price_data: list[dict[str, Any]],
    config: WalkForwardConfig,
    symbol: str,
) -> BacktestResult:
    """
    Run a backtest on a window of price data.

    Args:
        strategy: Strategy to test
        price_data: Window of OHLCV data
        config: Walk-forward configuration
        symbol: Trading symbol

    Returns:
        BacktestResult
    """
    backtest_config = BacktestConfig(
        initial_capital=Decimal("10000"),
        commission_rate=config.commission_rate,
        slippage_rate=config.slippage_rate,
        position_size_percent=config.position_size_percent,
        risk_free_rate=config.risk_free_rate,
        min_data_points=config.min_points_per_window,
    )

    engine = BacktestEngine(backtest_config)
    return engine.run_backtest(strategy=strategy, price_data=price_data, symbol=symbol)


def _optimize_parameters(
    strategy: Strategy,
    in_sample_data: list[dict[str, Any]],
    config: WalkForwardConfig,
    symbol: str,
) -> dict[str, Any]:
    """
    Optimize strategy parameters on in-sample data.

    This is a placeholder for actual optimization logic.
    In a full implementation, this would use grid search, genetic algorithms,
    or Bayesian optimization to find optimal parameters.

    For now, it returns the existing parameters.

    Args:
        strategy: Strategy with parameters to optimize
        in_sample_data: Training data
        config: Walk-forward configuration
        symbol: Trading symbol

    Returns:
        Dictionary of optimized parameters
    """
    # TODO: Implement actual parameter optimization
    # For now, return existing parameters
    # A full implementation could:
    # - Grid search over parameter ranges
    # - Use genetic algorithms
    # - Apply Bayesian optimization
    # - Use local search methods

    return strategy.parameters.copy()


def run_walk_forward(
    strategy: Strategy,
    price_data: list[dict[str, Any]],
    symbol: str,
    config: Optional[WalkForwardConfig] = None,
) -> WalkForwardResult:
    """
    Run walk-forward optimization on a strategy.

    Divides the data into rolling windows, optimizing parameters on in-sample
    data and testing on out-of-sample data for each period.

    Args:
        strategy: The strategy to test
        price_data: List of OHLCV candles (must be chronologically ordered)
        symbol: Trading symbol
        config: Walk-forward configuration (optional)

    Returns:
        WalkForwardResult with aggregated and period-by-period results

    Raises:
        ValueError: If insufficient data or invalid configuration
    """
    if config is None:
        config = WalkForwardConfig()

    # Validate inputs
    if len(price_data) < config.min_points_per_window * 2:
        raise ValueError(
            f"Insufficient data for walk-forward: need at least "
            f"{config.min_points_per_window * 2} candles, got {len(price_data)}"
        )

    if not (0 < config.in_sample_pct < 1):
        raise ValueError("in_sample_pct must be between 0 and 1")

    # Calculate window configuration
    total_points = len(price_data)
    window_size, step_size = _calculate_window_config(total_points, config)

    # Calculate in-sample size within each window
    in_sample_size = int(window_size * config.in_sample_pct)

    # Ensure minimum sizes
    if in_sample_size < config.min_points_per_window:
        raise ValueError(
            f"In-sample size ({in_sample_size}) is below minimum "
            f"({config.min_points_per_window})"
        )

    oos_size = window_size - in_sample_size
    if oos_size < config.min_points_per_window:
        raise ValueError(
            f"Out-of-sample size ({oos_size}) is below minimum "
            f"({config.min_points_per_window})"
        )

    # Run walk-forward periods
    periods: list[WalkForwardPeriod] = []
    period_num = 1

    # Start from beginning, roll forward
    start_idx = 0

    while start_idx + window_size <= total_points:
        # Define window boundaries
        in_sample_start_idx = start_idx
        in_sample_end_idx = start_idx + in_sample_size
        oos_start_idx = in_sample_end_idx
        oos_end_idx = start_idx + window_size

        # Extract data for this period
        in_sample_data = price_data[in_sample_start_idx:in_sample_end_idx]
        oos_data = price_data[oos_start_idx:oos_end_idx]

        # Skip if insufficient data
        if len(in_sample_data) < config.min_points_per_window:
            start_idx += step_size
            continue

        # Optimize parameters on in-sample data
        optimized_params = _optimize_parameters(strategy, in_sample_data, config, symbol)

        # Create strategy with optimized parameters
        optimized_strategy = Strategy(
            id=strategy.id,
            name=strategy.name,
            type=strategy.type,
            parameters=optimized_params,
            layers=strategy.layers,
            status=strategy.status,
        )

        # Run backtest on in-sample data
        try:
            in_sample_result = _run_backtest_on_window(
                optimized_strategy, in_sample_data, config, symbol
            )
        except ValueError as e:
            # Not enough data for indicators, skip this period
            start_idx += step_size
            continue

        # Run backtest on out-of-sample data
        try:
            oos_result = _run_backtest_on_window(
                optimized_strategy, oos_data, config, symbol
            )
        except ValueError as e:
            # Not enough data for indicators, skip this period
            start_idx += step_size
            continue

        # Calculate return degradation
        return_degradation = in_sample_result.total_return - oos_result.total_return

        # Create period result
        period = WalkForwardPeriod(
            period_number=period_num,
            in_sample_start=in_sample_data[0]["timestamp"],
            in_sample_end=in_sample_data[-1]["timestamp"],
            out_of_sample_start=oos_data[0]["timestamp"],
            out_of_sample_end=oos_data[-1]["timestamp"],
            in_sample_return=float(in_sample_result.total_return),
            in_sample_sharpe=float(in_sample_result.sharpe_ratio) if in_sample_result.sharpe_ratio else None,
            in_sample_max_drawdown=float(in_sample_result.max_drawdown),
            in_sample_trades=in_sample_result.total_trades,
            out_of_sample_return=float(oos_result.total_return),
            out_of_sample_sharpe=float(oos_result.sharpe_ratio) if oos_result.sharpe_ratio else None,
            out_of_sample_max_drawdown=float(oos_result.max_drawdown),
            out_of_sample_trades=oos_result.total_trades,
            optimized_parameters=optimized_params,
            return_degradation=float(return_degradation),
        )

        periods.append(period)
        period_num += 1

        # Roll forward
        start_idx += step_size

    # Validate we have periods
    if not periods:
        raise ValueError("No valid walk-forward periods could be created")

    # Calculate aggregated metrics
    oos_returns = [p.out_of_sample_return for p in periods]
    oos_sharps = [p.out_of_sample_sharpe for p in periods if p.out_of_sample_sharpe is not None]
    oos_drawdowns = [p.out_of_sample_max_drawdown for p in periods]

    avg_oos_return = float(np.mean(oos_returns))
    std_oos_return = float(np.std(oos_returns))
    avg_oos_sharpe = float(np.mean(oos_sharps)) if oos_sharps else 0.0
    avg_oos_max_drawdown = float(np.mean(oos_drawdowns))
    total_oos_trades = sum(p.out_of_sample_trades for p in periods)

    # Period win rate
    positive_periods = sum(1 for r in oos_returns if r > 0)
    negative_periods = sum(1 for r in oos_returns if r < 0)
    zero_periods = sum(1 for r in oos_returns if r == 0)
    period_win_rate = positive_periods / len(periods)

    # Calculate correlation between in-sample and out-of-sample returns
    in_sample_returns = [p.in_sample_return for p in periods]
    if len(in_sample_returns) > 1:
        return_correlation = float(np.corrcoef(in_sample_returns, oos_returns)[0, 1])
        if math.isnan(return_correlation):
            return_correlation = 0.0
    else:
        return_correlation = 0.0

    # Parameter stability (simplified version)
    # In a full implementation, this would track how much parameters change
    # For now, we use return correlation as a proxy
    parameter_stability_score = max(0.0, min(1.0, (return_correlation + 1) / 2))

    # Return degradation
    avg_return_degradation = float(np.mean([p.return_degradation for p in periods]))

    # Best and worst periods
    worst_period_return = float(np.min(oos_returns))
    best_period_return = float(np.max(oos_returns))

    return WalkForwardResult(
        strategy_id=strategy.id,
        symbol=symbol,
        start_date=price_data[0]["timestamp"],
        end_date=price_data[-1]["timestamp"],
        total_periods=len(periods),
        in_sample_pct=config.in_sample_pct,
        window_size=config.window_size,
        periods=periods,
        avg_oos_return=avg_oos_return,
        std_oos_return=std_oos_return,
        avg_oos_sharpe=avg_oos_sharpe,
        avg_oos_max_drawdown=avg_oos_max_drawdown,
        total_oos_trades=total_oos_trades,
        period_win_rate=period_win_rate,
        parameter_stability_score=parameter_stability_score,
        return_correlation_in_vs_oos=return_correlation,
        avg_return_degradation=avg_return_degradation,
        worst_period_return=worst_period_return,
        best_period_return=best_period_return,
        positive_periods=positive_periods,
        negative_periods=negative_periods,
    )


def format_walk_forward_for_api(result: WalkForwardResult) -> dict[str, Any]:
    """
    Format walk-forward result for API response.

    Args:
        result: Walk-forward optimization result

    Returns:
        Dictionary formatted for JSON serialization
    """
    return {
        "strategy_id": result.strategy_id,
        "symbol": result.symbol,
        "date_range": {
            "start": result.start_date.isoformat(),
            "end": result.end_date.isoformat(),
        },
        "configuration": {
            "in_sample_pct": result.in_sample_pct,
            "window_size": result.window_size,
            "total_periods": result.total_periods,
        },
        "aggregated_performance": {
            "avg_oos_return": result.avg_oos_return,
            "std_oos_return": result.std_oos_return,
            "avg_oos_sharpe": result.avg_oos_sharpe,
            "avg_oos_max_drawdown": result.avg_oos_max_drawdown,
            "total_oos_trades": result.total_oos_trades,
            "period_win_rate": result.period_win_rate,
        },
        "stability_metrics": {
            "parameter_stability_score": result.parameter_stability_score,
            "return_correlation_in_vs_oos": result.return_correlation_in_vs_oos,
            "avg_return_degradation": result.avg_return_degradation,
        },
        "period_analysis": {
            "best_period_return": result.best_period_return,
            "worst_period_return": result.worst_period_return,
            "positive_periods": result.positive_periods,
            "negative_periods": result.negative_periods,
        },
        "periods": result.get_period_results(),
    }


def detect_parameter_degradation(result: WalkForwardResult, threshold: float = 0.5) -> dict[str, Any]:
    """
    Detect if parameters are degrading over time.

    Analyzes the trend in out-of-sample returns to detect if performance
    is declining, which may indicate parameter degradation or regime change.

    Args:
        result: Walk-forward optimization result
        threshold: Performance drop threshold for warning (default 50% of best period)

    Returns:
        Dictionary with degradation analysis
    """
    if len(result.periods) < 3:
        return {
            "has_degradation": False,
            "reason": "Insufficient periods for degradation analysis",
        }

    oos_returns = [p.out_of_sample_return for p in result.periods]

    # Calculate trend using linear regression
    x = np.arange(len(oos_returns))
    z = np.polyfit(x, oos_returns, 1)
    slope = z[0]

    # Calculate percent decline from first half to second half
    mid_point = len(oos_returns) // 2
    first_half_avg = np.mean(oos_returns[:mid_point])
    second_half_avg = np.mean(oos_returns[mid_point:])

    percent_decline = 0.0
    if first_half_avg > 0:
        percent_decline = (first_half_avg - second_half_avg) / abs(first_half_avg)

    # Check for degradation
    has_degradation = False
    degradation_level = "none"

    if slope < 0 and percent_decline > threshold:
        has_degradation = True
        if percent_decline > 0.75:
            degradation_level = "severe"
        elif percent_decline > 0.5:
            degradation_level = "moderate"
        else:
            degradation_level = "mild"

    return {
        "has_degradation": has_degradation,
        "degradation_level": degradation_level,
        "trend_slope": float(slope),
        "percent_decline": float(percent_decline),
        "first_half_avg_return": float(first_half_avg),
        "second_half_avg_return": float(second_half_avg),
        "recommendation": _get_degradation_recommendation(degradation_level),
    }


def _get_degradation_recommendation(level: str) -> str:
    """Get recommendation based on degradation level."""
    recommendations = {
        "none": "Strategy performance is stable. Continue monitoring.",
        "mild": "Some performance decline detected. Consider re-optimizing parameters.",
        "moderate": "Significant performance decline detected. Recommend re-optimization or regime change analysis.",
        "severe": "Severe parameter degradation detected. Strategy may no longer be valid. Consider discontinuing or major re-optimization.",
    }
    return recommendations.get(level, "Unknown degradation level")
