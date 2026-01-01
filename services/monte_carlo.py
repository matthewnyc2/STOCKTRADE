"""
Monte Carlo Simulation Service.

Runs backtest simulations with randomized trade ordering to generate
confidence intervals and probability distributions for strategy performance.

Key Features:
- Randomizes trade order while preserving returns
- Generates confidence bands (5th, 50th, 95th percentiles)
- Calculates probability of profit/loss thresholds
- Provides distribution statistics (mean, std dev, percentiles)
"""

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import numpy as np

from models import BacktestResult, EquityPoint


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation."""

    simulations: int = 1000
    confidence_levels: list[float] = None
    seed: int | None = None

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.05, 0.5, 0.95]


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""

    backtest_id: str
    simulations: int
    initial_capital: float

    # Confidence bands for equity curve
    # Each is a list of equity values at each time step
    confidence_5th: list[float]  # Lower band (worst case)
    confidence_50th: list[float]  # Median (expected case)
    confidence_95th: list[float]  # Upper band (best case)

    # Final capital distribution
    final_capital_mean: float
    final_capital_std: float
    final_capital_min: float
    final_capital_max: float
    final_capital_percentiles: dict[str, float]  # e.g., {"5th": 1000, "50th": 1500, "95th": 2000}

    # Return distribution
    return_mean: float
    return_std: float
    return_percentiles: dict[str, float]

    # Probability statistics
    profit_probability: float  # Probability of final capital > initial capital
    loss_probability: float  # Probability of final capital < initial capital

    # Drawdown statistics
    max_drawdown_mean: float
    max_drawdown_std: float
    max_drawdown_worst: float  # Worst drawdown across all simulations

    # Trade statistics
    total_trades: int


def run_monte_carlo(
    backtest_result: BacktestResult,
    config: MonteCarloConfig | None = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation on a backtest result.

    Randomizes the order of trades while preserving their returns,
    then recalculates equity curves for each simulation to generate
    confidence intervals.

    Args:
        backtest_result: The original backtest result to simulate
        config: Monte Carlo configuration (optional)

    Returns:
        MonteCarloResult with confidence bands and statistics

    Raises:
        ValueError: If backtest has no trades
    """
    if config is None:
        config = MonteCarloConfig()

    # Validate we have trades to simulate
    if not backtest_result.trades:
        raise ValueError("Cannot run Monte Carlo simulation on backtest with no trades")

    # Extract trade returns (as percentages)
    trade_returns = [float(t.pnl_percent) for t in backtest_result.trades]
    num_trades = len(trade_returns)

    # Set random seed for reproducibility
    if config.seed is not None:
        np.random.seed(config.seed)

    # Store all simulation equity curves
    all_equity_curves: list[list[float]] = []
    all_final_capitals: list[float] = []
    all_returns: list[float] = []
    all_max_drawdowns: list[float] = []

    initial_capital = float(backtest_result.initial_capital)

    # Run simulations
    for _ in range(config.simulations):
        # Randomize trade order using numpy
        shuffled_returns = np.random.permutation(trade_returns)

        # Calculate equity curve for this simulation
        equity_curve = [initial_capital]
        capital = initial_capital
        peak = initial_capital
        max_drawdown = 0.0

        for ret_pct in shuffled_returns:
            # Apply return to capital
            # ret_pct is percentage, so we multiply by (1 + ret_pct/100)
            capital = capital * (1 + ret_pct / 100.0)
            equity_curve.append(capital)

            # Track drawdown
            if capital > peak:
                peak = capital
            drawdown = (capital - peak) / peak if peak > 0 else 0
            max_drawdown = min(max_drawdown, drawdown)

        all_equity_curves.append(equity_curve)
        all_final_capitals.append(capital)
        all_returns.append((capital - initial_capital) / initial_capital)
        all_max_drawdowns.append(max_drawdown)

    # Convert to numpy arrays for easier percentile calculation
    all_equity_curves_array = np.array(all_equity_curves)

    # Calculate confidence bands at each time step
    # We need to handle curves of different lengths if needed,
    # but since we preserve trade count, all curves have same length
    confidence_5th = []
    confidence_50th = []
    confidence_95th = []

    for i in range(all_equity_curves_array.shape[1]):
        values_at_step = all_equity_curves_array[:, i]
        confidence_5th.append(np.percentile(values_at_step, 5))
        confidence_50th.append(np.percentile(values_at_step, 50))
        confidence_95th.append(np.percentile(values_at_step, 95))

    # Calculate final capital statistics
    final_capitals_array = np.array(all_final_capitals)
    final_capital_mean = float(np.mean(final_capitals_array))
    final_capital_std = float(np.std(final_capitals_array))
    final_capital_min = float(np.min(final_capitals_array))
    final_capital_max = float(np.max(final_capitals_array))

    final_capital_percentiles = {
        "5th": float(np.percentile(final_capitals_array, 5)),
        "10th": float(np.percentile(final_capitals_array, 10)),
        "25th": float(np.percentile(final_capitals_array, 25)),
        "50th": float(np.percentile(final_capitals_array, 50)),
        "75th": float(np.percentile(final_capitals_array, 75)),
        "90th": float(np.percentile(final_capitals_array, 90)),
        "95th": float(np.percentile(final_capitals_array, 95)),
    }

    # Calculate return statistics
    returns_array = np.array(all_returns)
    return_mean = float(np.mean(returns_array))
    return_std = float(np.std(returns_array))

    return_percentiles = {
        "5th": float(np.percentile(returns_array, 5)),
        "10th": float(np.percentile(returns_array, 10)),
        "25th": float(np.percentile(returns_array, 25)),
        "50th": float(np.percentile(returns_array, 50)),
        "75th": float(np.percentile(returns_array, 75)),
        "90th": float(np.percentile(returns_array, 90)),
        "95th": float(np.percentile(returns_array, 95)),
    }

    # Calculate probability statistics
    profitable_count = np.sum(final_capitals_array > initial_capital)
    loss_count = np.sum(final_capitals_array < initial_capital)
    profit_probability = profitable_count / config.simulations
    loss_probability = loss_count / config.simulations

    # Calculate drawdown statistics
    drawdowns_array = np.array(all_max_drawdowns)
    max_drawdown_mean = float(np.mean(drawdowns_array))
    max_drawdown_std = float(np.std(drawdowns_array))
    max_drawdown_worst = float(np.min(drawdowns_array))  # Most negative

    return MonteCarloResult(
        backtest_id=backtest_result.id,
        simulations=config.simulations,
        initial_capital=initial_capital,
        confidence_5th=confidence_5th,
        confidence_50th=confidence_50th,
        confidence_95th=confidence_95th,
        final_capital_mean=final_capital_mean,
        final_capital_std=final_capital_std,
        final_capital_min=final_capital_min,
        final_capital_max=final_capital_max,
        final_capital_percentiles=final_capital_percentiles,
        return_mean=return_mean,
        return_std=return_std,
        return_percentiles=return_percentiles,
        profit_probability=profit_probability,
        loss_probability=loss_probability,
        max_drawdown_mean=max_drawdown_mean,
        max_drawdown_std=max_drawdown_std,
        max_drawdown_worst=max_drawdown_worst,
        total_trades=num_trades,
    )


def calculate_probability_of_threshold(
    monte_carlo_result: MonteCarloResult,
    threshold_return: float,
) -> float:
    """
    Calculate probability of achieving a minimum return threshold.

    Uses the distribution from Monte Carlo results to estimate
    the probability of achieving at least the specified return.

    Args:
        monte_carlo_result: Results from Monte Carlo simulation
        threshold_return: Return threshold as decimal (e.g., 0.10 for 10%)

    Returns:
        Probability (0.0 to 1.0) of achieving at least this return
    """
    # Use z-score approximation based on normal distribution
    if monte_carlo_result.return_std == 0:
        return 1.0 if threshold_return <= monte_carlo_result.return_mean else 0.0

    from scipy import stats

    z_score = (threshold_return - monte_carlo_result.return_mean) / monte_carlo_result.return_std
    probability = 1 - stats.norm.cdf(z_score)

    return max(0.0, min(1.0, probability))


def calculate_risk_of_ruin(
    monte_carlo_result: MonteCarloResult,
    ruin_threshold: float = 0.5,  # 50% loss
) -> float:
    """
    Calculate risk of ruin (losing a significant portion of capital).

    Args:
        monte_carlo_result: Results from Monte Carlo simulation
        ruin_threshold: Loss threshold as decimal (e.g., 0.5 for 50% loss)

    Returns:
        Probability (0.0 to 1.0) of losing at least this threshold
    """
    # Count simulations that fell below the ruin threshold
    ruin_capital = monte_carlo_result.initial_capital * (1 - ruin_threshold)

    # Use the 5th percentile as approximation for risk
    # If 5th percentile is below ruin threshold, estimate probability
    if monte_carlo_result.final_capital_percentiles["5th"] < ruin_capital:
        # Linear interpolation between 5th percentile and min
        pct_5 = monte_carlo_result.final_capital_percentiles["5th"]
        min_capital = monte_carlo_result.final_capital_min

        if min_capital < ruin_capital:
            # Estimate what % of simulations are below threshold
            range_below_5th = pct_5 - min_capital
            if range_below_5th > 0:
                portion_below_threshold = (pct_5 - ruin_capital) / range_below_5th
                return 0.05 + (0.05 * portion_below_threshold)

    return 0.0


def format_monte_carlo_for_api(result: MonteCarloResult) -> dict[str, Any]:
    """
    Format Monte Carlo result for API response.

    Args:
        result: Monte Carlo simulation result

    Returns:
        Dictionary formatted for JSON serialization
    """
    return {
        "backtest_id": result.backtest_id,
        "simulations": result.simulations,
        "initial_capital": result.initial_capital,
        "confidence_bands": {
            "5th": result.confidence_5th,
            "50th": result.confidence_50th,
            "95th": result.confidence_95th,
        },
        "final_capital": {
            "mean": result.final_capital_mean,
            "std": result.final_capital_std,
            "min": result.final_capital_min,
            "max": result.final_capital_max,
            "percentiles": result.final_capital_percentiles,
        },
        "returns": {
            "mean": result.return_mean,
            "std": result.return_std,
            "percentiles": result.return_percentiles,
        },
        "probabilities": {
            "profit": result.profit_probability,
            "loss": result.loss_probability,
        },
        "drawdown": {
            "mean": result.max_drawdown_mean,
            "std": result.max_drawdown_std,
            "worst": result.max_drawdown_worst,
        },
        "total_trades": result.total_trades,
    }
