"""
Repository implementations for database operations.

Each domain has its own repository inheriting from BaseRepository.
"""

from database.repositories.strategy import StrategyRepository, StrategyLayerRepository
from database.repositories.signal import SignalRepository, LayerSignalRepository
from database.repositories.backtest import (
    BacktestResultRepository,
    EquityPointRepository,
    TradeRepository,
)
from database.repositories.portfolio import PortfolioRepository, PositionRepository
from database.repositories.whale import (
    WhaleRepository,
    WhaleActivityRepository,
    WhaleConstellationRepository,
)
from database.repositories.ml import MLModelRepository
from database.repositories.settings import SettingsRepository
from database.repositories.ai_reasoning import AIReasoningSessionRepository
from database.repositories.liquidation import (
    LiquidationRepository,
    CascadeRepository,
)
from database.repositories.trader_repository import TraderRepository

__all__ = [
    "TraderRepository",
    "StrategyRepository",
    "StrategyLayerRepository",
    "SignalRepository",
    "LayerSignalRepository",
    "BacktestResultRepository",
    "EquityPointRepository",
    "TradeRepository",
    "PortfolioRepository",
    "PositionRepository",
    "WhaleRepository",
    "WhaleActivityRepository",
    "WhaleConstellationRepository",
    "MLModelRepository",
    "SettingsRepository",
    "AIReasoningSessionRepository",
    "LiquidationRepository",
    "CascadeRepository",
]
