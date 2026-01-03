"""
SQLAlchemy models for the Trader Tracking System.

Defines the database schema for traders, their activities, and profiles.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Float,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from database.models import BaseModel as Base

class Trader(Base):
    """Database model for a tracked trader."""
    __tablename__ = 'traders'

    id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)
    rank = Column(Integer)
    pnl_24h = Column(Float)
    win_rate = Column(Float)
    last_activity = Column(DateTime, default=datetime.utcnow)
    followers = Column(Integer)

    activities = relationship("TraderActivity", back_populates="trader")
    profile = relationship("TraderProfile", uselist=False, back_populates="trader")

class TraderActivity(Base):
    """Database model for a trader's activity."""
    __tablename__ = 'trader_activities'

    id = Column(String, primary_key=True, index=True)
    trader_id = Column(String, ForeignKey('traders.id'), nullable=False)
    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)
    amount_usd = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pnl = Column(Float)
    leverage = Column(Float)

    trader = relationship("Trader", back_populates="activities")

class TraderProfile(Base):
    """Database model for a trader's profile."""
    __tablename__ = 'trader_profiles'

    trader_id = Column(String, ForeignKey('traders.id'), primary_key=True)
    risk_level = Column(String)
    preferred_assets = Column(JSON)
    trading_style = Column(String)
    avg_holding_period_seconds = Column(Integer)
    preferred_exchange = Column(String)

    trader = relationship("Trader", back_populates="profile")
