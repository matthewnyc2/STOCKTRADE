"""Services package for Crypto Quant Laboratory - business logic."""

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

from services.walk_forward import (
    WalkForwardConfig,
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward,
    format_walk_forward_for_api,
    detect_parameter_degradation,
)

from services.paper_trading import (
    PaperTradingEngine,
    PaperTradingConfig,
    TradeResult,
    PositionUpdate,
)

from services.ai_reasoning import (
    AIReasoningEngine,
    get_ai_reasoning_engine,
)

__all__ = [
    "BacktestEngine",
    "BacktestConfig",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_expectancy",
    "WalkForwardConfig",
    "WalkForwardPeriod",
    "WalkForwardResult",
    "run_walk_forward",
    "format_walk_forward_for_api",
    "detect_parameter_degradation",
    "PaperTradingEngine",
    "PaperTradingConfig",
    "TradeResult",
    "PositionUpdate",
    "AIReasoningEngine",
    "get_ai_reasoning_engine",
]
