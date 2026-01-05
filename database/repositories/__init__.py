"""
Repository implementations for database operations.

Each domain has its own repository inheriting from BaseRepository.
"""

from database.repositories.strategy import (
    StrategyRepository,
    StrategyLayerRepository,
    StrategyFavoriteRepository,
    StrategyShareRepository,
    StrategyVersionRepository,
)
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
from database.repositories.market import (
    CoinRepository,
    ExchangeRepository,
    MarketPairRepository,
    StoredPriceDataRepository,
)
from database.repositories.user import UserRepository

__all__ = [
    "StrategyRepository",
    "StrategyLayerRepository",
    "StrategyFavoriteRepository",
    "StrategyShareRepository",
    "StrategyVersionRepository",
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
    "CoinRepository",
    "ExchangeRepository",
    "MarketPairRepository",
    "StoredPriceDataRepository",
    "UserRepository",
]
