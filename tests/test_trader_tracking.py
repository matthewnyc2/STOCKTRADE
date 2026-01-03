"""
Tests for the Trader Tracking System.

Covers the API, service, and repository layers of the trader tracking feature.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

from api.main import app  # Assuming your FastAPI app is initialized here
from database.models import BaseModel as Base
from database.connection import get_db_session
from database.models.trader import Trader, TraderActivity
from models.trader import TraderProfile, TraderAction, TraderRiskLevel, TradingStyle
from services.trader_tracker import analyze_trader_profile, calculate_trader_performance

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db_session dependency to use the test database
def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db_session

@pytest.fixture(scope="function")
def db_session():
    """Fixture to set up and tear down the database for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    """Fixture to create a TestClient for the FastAPI app."""
    return TestClient(app)

# Sample data for testing
@pytest.fixture(scope="function")
def sample_trader(db_session):
    trader = Trader(
        id="trader1",
        username="test_trader",
        exchange="binance",
        rank=1,
        pnl_24h=1000.0,
        win_rate=0.75,
        last_activity=datetime.utcnow(),
        followers=100,
    )
    db_session.add(trader)
    db_session.commit()
    return trader

@pytest.fixture(scope="function")
def sample_activities(db_session, sample_trader):
    activities = [
        TraderActivity(
            id=f"act{i}",
            trader_id=sample_trader.id,
            symbol="BTC/USDT",
            action=TraderAction.BOUGHT.value,
            amount_usd=10000.0,
            timestamp=datetime.utcnow(),
            pnl=500.0,
            leverage=5.0,
        )
        for i in range(5)
    ]
    db_session.add_all(activities)
    db_session.commit()
    return activities

# API Tests
def test_list_traders(client, sample_trader):
    response = client.get("/api/traders/")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["username"] == "test_trader"

def test_get_trader(client, sample_trader):
    response = client.get(f"/api/traders/{sample_trader.id}")
    assert response.status_code == 200
    assert response.json()["username"] == "test_trader"

def test_get_trader_not_found(client):
    response = client.get("/api/traders/nonexistent")
    assert response.status_code == 404

def test_get_trader_activity(client, sample_trader, sample_activities):
    response = client.get(f"/api/traders/{sample_trader.id}/activity")
    assert response.status_code == 200
    assert len(response.json()) == 5

def test_get_trader_profile_not_found(client, sample_trader):
    response = client.get(f"/api/traders/{sample_trader.id}/profile")
    assert response.status_code == 404

def test_analyze_and_get_trader_profile(client, sample_trader, sample_activities):
    # First, analyze the trader to create the profile
    response = client.post(f"/api/traders/{sample_trader.id}/analyze")
    assert response.status_code == 200

    # Now, get the profile
    response = client.get(f"/api/traders/{sample_trader.id}/profile")
    assert response.status_code == 200
    assert response.json()["trader_id"] == sample_trader.id

def test_track_new_trader(client):
    response = client.post("/api/traders/track", json={"username": "new_trader", "exchange": "coinbase"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_trader"
    assert data["exchange"] == "coinbase"

# Service Tests
def test_analyze_trader_profile(db_session, sample_trader, sample_activities):
    profile = analyze_trader_profile(sample_trader.id)
    assert profile.trader_id == sample_trader.id
    assert profile.risk_level == TraderRiskLevel.MEDIUM
    assert "BTC/USDT" in profile.preferred_assets
    assert profile.trading_style in [TradingStyle.DAY_TRADER, TradingStyle.SCALPER]

def test_calculate_trader_performance(db_session, sample_trader, sample_activities):
    performance = calculate_trader_performance(sample_trader.id)
    assert performance["trader_id"] == sample_trader.id
    assert performance["total_trades"] == 5
    assert performance["win_rate"] == "100.00%"
    assert "2500.00" in performance["total_pnl_usd"]

# Repository Tests
def test_trader_repository_create_and_get(db_session):
    from database.repositories.trader_repository import TraderRepository
    repo = TraderRepository(db_session)
    trader_data = {
        "id": "repo_trader",
        "username": "repo_user",
        "exchange": "kraken",
    }
    repo.create(**trader_data)
    trader = repo.get("repo_trader")
    assert trader is not None
    assert trader.username == "repo_user"

def test_trader_repository_add_and_get_activity(db_session, sample_trader):
    from database.repositories.trader_repository import TraderRepository
    repo = TraderRepository(db_session)
    activity_data = {
        "id": "repo_act",
        "trader_id": sample_trader.id,
        "symbol": "ETH/USDT",
        "action": TraderAction.SOLD.value,
        "amount_usd": 5000.0,
    }
    repo.add_activity(**activity_data)
    activities = repo.get_activity(sample_trader.id)
    assert any(act.id == "repo_act" for act in activities)

def test_trader_repository_update_profile(db_session, sample_trader):
    from database.repositories.trader_repository import TraderRepository
    repo = TraderRepository(db_session)
    profile_data = {
        "risk_level": TraderRiskLevel.HIGH.value,
        "preferred_assets": ["SOL/USDT"],
        "trading_style": TradingStyle.SWING_TRADER.value,
    }
    repo.update_profile(sample_trader.id, profile_data)
    profile = repo.get_profile(sample_trader.id)
    assert profile is not None
    assert profile.risk_level == TraderRiskLevel.HIGH.value
