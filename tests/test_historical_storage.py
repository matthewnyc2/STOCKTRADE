"""
Tests for HistoricalPriceRepository.
"""

import os
import pytest
import tempfile
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import BaseModel, HistoricalPriceModel
from database.repositories.historical_price import HistoricalPriceRepository
from models import HistoricalPrice

@pytest.fixture
def db_session():
    """Create a test database session."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}")
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    os.remove(path)

def test_create_historical_price(db_session):
    """Test creating a historical price record."""
    repo = HistoricalPriceRepository(db_session)
    price_data = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": datetime(2025, 1, 1, 12, 0, 0),
        "open": Decimal("50000.0"),
        "high": Decimal("51000.0"),
        "low": Decimal("49000.0"),
        "close": Decimal("50500.0"),
        "volume": Decimal("1000.0"),
    }
    repo.create(**price_data)
    created_price = db_session.query(HistoricalPriceModel).first()
    assert created_price.symbol == "BTC/USDT"
    assert created_price.timeframe == "1h"

def test_get_historical_price(db_session):
    """Test retrieving a historical price record."""
    repo = HistoricalPriceRepository(db_session)
    price = HistoricalPriceModel(
        symbol="BTC/USDT",
        timeframe="1h",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        open=Decimal("50000.0"),
        high=Decimal("51000.0"),
        low=Decimal("49000.0"),
        close=Decimal("50500.0"),
        volume=Decimal("1000.0"),
    )
    db_session.add(price)
    db_session.commit()
    pk = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": datetime(2025, 1, 1, 12, 0, 0),
    }
    retrieved_price = repo.get(pk)
    assert retrieved_price.symbol == "BTC/USDT"
    assert retrieved_price.timeframe == "1h"

def test_get_by_symbol_and_timeframe(db_session):
    """Test retrieving historical prices by symbol and timeframe."""
    repo = HistoricalPriceRepository(db_session)
    price1 = HistoricalPriceModel(
        symbol="BTC/USDT",
        timeframe="1h",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        open=Decimal("50000.0"),
        high=Decimal("51000.0"),
        low=Decimal("49000.0"),
        close=Decimal("50500.0"),
        volume=Decimal("1000.0"),
    )
    price2 = HistoricalPriceModel(
        symbol="BTC/USDT",
        timeframe="1h",
        timestamp=datetime(2025, 1, 1, 13, 0, 0),
        open=Decimal("50500.0"),
        high=Decimal("51500.0"),
        low=Decimal("49500.0"),
        close=Decimal("51000.0"),
        volume=Decimal("1200.0"),
    )
    db_session.add_all([price1, price2])
    db_session.commit()
    prices = repo.get_by_symbol_and_timeframe(symbol="BTC/USDT", timeframe="1h")
    assert len(prices) == 2
    assert prices[0].symbol == "BTC/USDT"
    assert prices[0].timeframe == "1h"
