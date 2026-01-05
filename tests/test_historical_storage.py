"""
Historical Data Storage Tests
WHY: Backtesting requires stored historical data
"""
import pytest
from datetime import datetime


def test_historical_data_model_exists():
    """WHY: Need database schema for historical prices"""
    from models.market_data import HistoricalPrice
    assert HistoricalPrice is not None


def test_save_historical_price():
    """WHY: Must persist historical data"""
    from models.market_data import HistoricalPrice
    from core.database import SessionLocal
    
    db = SessionLocal()
    price = HistoricalPrice(
        symbol="BTCUSDT",
        price=50000.0,
        timestamp=datetime.now()
    )
    db.add(price)
    db.commit()
    assert price.id is not None
    db.close()


def test_query_historical_prices():
    """WHY: Backtesting needs to retrieve historical data"""
    from database.repositories.market_data import get_historical_prices
    prices = get_historical_prices("BTCUSDT", days=30)
    assert isinstance(prices, list)
