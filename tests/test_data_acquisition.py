"""
Data Acquisition Tests
WHY: Real-time and historical data required for trading
"""
import pytest
from fastapi.testclient import TestClient


def test_current_market_data_fetch():
    """WHY: Real-time prices needed for trading"""
    from api.main import app
    client = TestClient(app)
    response = client.get("/api/market-data/current/BTCUSDT")
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert "timestamp" in data


def test_historical_data_fetch():
    """WHY: Backtesting requires past data"""
    from api.main import app
    client = TestClient(app)
    response = client.get("/api/market-data/historical/BTCUSDT?days=30")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "price" in data[0]
    assert "timestamp" in data[0]


def test_trader_data_fetch():
    """WHY: User specifically requested trader data"""
    from api.main import app
    client = TestClient(app)
    response = client.get("/api/traders/top-performers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "trader_id" in data[0]
    assert "performance" in data[0]


def test_data_source_extensibility():
    """WHY: Must support multiple APIs (Binance, CoinGecko, etc)"""
    from services.data_sources import DataSourceManager
    manager = DataSourceManager()
    sources = manager.get_available_sources()
    assert "binance" in sources
    assert "coingecko" in sources
    assert len(sources) >= 2
