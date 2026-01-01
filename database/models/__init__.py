"""
SQLAlchemy ORM models for Crypto Quant Laboratory.

All models inherit from BaseModel which provides common fields and functionality.
Models mirror the Pydantic models in the /models directory but include database-specific features.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Provides common fields and metadata.
    """

    __abstract__ = True

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Import all models for easy access
from database.models.strategy import StrategyModel, StrategyLayerModel
from database.models.signal import SignalModel, LayerSignalModel
from database.models.backtest import (
    BacktestResultModel,
    EquityPointModel,
    TradeModel,
)
from database.models.portfolio import PortfolioModel, PositionModel
from database.models.whale import (
    WhaleModel,
    WhaleActivityModel,
    WhaleConstellationModel,
)
from database.models.ml import MLModelModel
from database.models.settings import SettingsModel
from database.models.ai_reasoning import AIReasoningSessionModel
from database.models.price import PriceModel
from database.models.liquidation import LiquidationModel, CascadeModel

__all__ = [
    "BaseModel",
    "StrategyModel",
    "StrategyLayerModel",
    "SignalModel",
    "LayerSignalModel",
    "BacktestResultModel",
    "EquityPointModel",
    "TradeModel",
    "PortfolioModel",
    "PositionModel",
    "WhaleModel",
    "WhaleActivityModel",
    "WhaleConstellationModel",
    "MLModelModel",
    "SettingsModel",
    "AIReasoningSessionModel",
    "PriceModel",
    "LiquidationModel",
    "CascadeModel",
]
