"""
Crypto Quant Laboratory - Shared Type Definitions & Contract.

All Pydantic models for the backend API.
"""

# Strategy models
from models.strategy import (
    Strategy,
    StrategyLayer,
    StrategyType,
    Status,
    LogicGate,
    GameModeMetadata,
    ProModeMetadata,
    BacktestMetrics,
    CreateFromTemplateRequest,
)

# Signal models
from models.signal import LayerSignal, Signal, SignalType

# Backtest models
from models.backtest import BacktestResult, EquityPoint, Trade

# Portfolio models
from models.portfolio import Portfolio, PortfolioMetrics, Position

# Whale models
from models.whale import (
    Whale,
    WhaleActivity,
    WhaleAction,
    WhaleConstellation,
    WhaleConstellationType,
    PatternType,
    WhaleTier,
)

# ML models
from models.ml import (
    MLModel,
    ModelStatus,
    ModelType,
    TrainingRequest,
    PredictionRequest,
    TrainingProgressResponse,
)

# Settings models
from models.settings import Settings, UIMode

# Market data models
from models.market_data import (
    PriceData,
    CurrentPrice,
    TechnicalIndicators,
    IndicatorSeries,
    MarketDataResponse,
    HistoricalPricesRequest,
    IndicatorsRequest,
    SeedPriceDataResponse,
    PriceDataSummary,
)

# Liquidation models
from models.liquidation import (
    Liquidation,
    CascadeEvent,
    CascadeSeverity,
    LiquidationSide,
    LiquidationHeat,
    LiquidationStats,
)

# Arbitrage models
from models.arbitrage import (
    ArbitrageOpportunity,
    ArbitrageType,
    ArbitrageStatus,
    ArbitrageConfig,
    ArbitrageExecution,
    ArbitrageSummary,
    ArbitrageScanRequest,
    ExchangeVenue,
    Chain,
    VenuePrice,
    FundingRateData,
    OraclePriceData,
)

__all__ = [
    # Strategy
    "Strategy",
    "StrategyLayer",
    "StrategyType",
    "Status",
    "LogicGate",
    "GameModeMetadata",
    "ProModeMetadata",
    "BacktestMetrics",
    "CreateFromTemplateRequest",
    # Signal
    "Signal",
    "LayerSignal",
    "SignalType",
    # Backtest
    "BacktestResult",
    "EquityPoint",
    "Trade",
    # Portfolio
    "Portfolio",
    "Position",
    "PortfolioMetrics",
    # Whale
    "Whale",
    "WhaleActivity",
    "WhaleAction",
    "WhaleConstellation",
    "WhaleConstellationType",
    "PatternType",
    "WhaleTier",
    # ML
    "MLModel",
    "ModelType",
    "ModelStatus",
    "TrainingRequest",
    "PredictionRequest",
    "TrainingProgressResponse",
    # Settings
    "Settings",
    "UIMode",
    # Market Data
    "PriceData",
    "CurrentPrice",
    "TechnicalIndicators",
    "IndicatorSeries",
    "MarketDataResponse",
    "HistoricalPricesRequest",
    "IndicatorsRequest",
    "SeedPriceDataResponse",
    "PriceDataSummary",
    # Liquidation
    "Liquidation",
    "CascadeEvent",
    "CascadeSeverity",
    "LiquidationSide",
    "LiquidationHeat",
    "LiquidationStats",
    # Arbitrage
    "ArbitrageOpportunity",
    "ArbitrageType",
    "ArbitrageStatus",
    "ArbitrageConfig",
    "ArbitrageExecution",
    "ArbitrageSummary",
    "ArbitrageScanRequest",
    "ExchangeVenue",
    "Chain",
    "VenuePrice",
    "FundingRateData",
    "OraclePriceData",
]
