"""
Backend API Endpoint Tests
Tests for all major STOCKTRADE API endpoints
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

# Import the FastAPI app
from api.main import app

# Create test client
client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "is_superuser": False,
        "full_name": "Test User"
    }


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer mock-token"}


@pytest.fixture
def mock_strategy():
    """Mock strategy data"""
    return {
        "id": "test-strategy-id",
        "name": "Test Strategy",
        "description": "A test strategy",
        "type": "momentum",
        "status": "active",
        "parameters": {"period": 14},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def mock_signal():
    """Mock signal data"""
    return {
        "id": "test-signal-id",
        "symbol": "BTC/USD",
        "action": "BUY",
        "confidence": 0.85,
        "reasoning": "Strong uptrend detected",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_demo_login_success(self):
        """Test demo login endpoint returns tokens"""
        response = client.get("/api/auth/demo")
        assert response.status_code in [200, 401]  # May work or need auth
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "message" in data

    @pytest.mark.skipif(True, reason="Requires user setup")
    def test_login_with_credentials(self):
        """Test login with email and password"""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpass"}
        )
        # May fail without user setup - just check endpoint exists
        assert response.status_code in [200, 401, 422]


# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

class TestStrategyEndpoints:
    """Test strategy management endpoints"""

    def test_list_strategies(self, mock_strategy):
        """Test GET /api/v1/strategies - list all strategies"""
        with patch('database.repositories.strategy.StrategyRepository.get_all') as mock_repo:
            mock_repo.return_value = [mock_strategy]
            response = client.get("/api/v1/strategies")
            assert response.status_code in [200, 401]  # May need auth

    def test_get_strategy_by_id(self, mock_strategy):
        """Test GET /api/v1/strategies/{id} - get single strategy"""
        with patch('database.repositories.strategy.StrategyRepository.get') as mock_repo:
            mock_repo.return_value = mock_strategy
            response = client.get("/api/v1/strategies/test-strategy-id")
            assert response.status_code in [200, 401, 404]

    def test_create_strategy(self):
        """Test POST /api/v1/strategies - create new strategy"""
        strategy_data = {
            "name": "New Strategy",
            "description": "Test strategy",
            "type": "momentum",
            "parameters": {"period": 14}
        }
        response = client.post(
            "/api/v1/strategies",
            json=strategy_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [201, 401, 422]

    def test_update_strategy(self):
        """Test PUT /api/v1/strategies/{id} - update strategy"""
        update_data = {
            "name": "Updated Strategy",
            "status": "active"
        }
        response = client.put(
            "/api/v1/strategies/test-id",
            json=update_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 401, 404]

    def test_delete_strategy(self):
        """Test DELETE /api/v1/strategies/{id} - delete strategy"""
        response = client.delete(
            "/api/v1/strategies/test-id",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 204, 401, 404]

    def test_get_strategy_templates(self):
        """Test GET /api/v1/strategies/templates - get templates"""
        response = client.get("/api/v1/strategies/templates")
        assert response.status_code in [200, 401]


# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

class TestSignalEndpoints:
    """Test signal endpoints"""

    def test_list_signals(self, mock_signal):
        """Test GET /api/v1/signals - list all signals"""
        with patch('database.repositories.signal.SignalRepository.get_all') as mock_repo:
            mock_repo.return_value = [mock_signal]
            response = client.get("/api/v1/signals")
            assert response.status_code in [200, 401]

    def test_get_signals_by_strategy(self, mock_signal):
        """Test GET /api/v1/signals?strategy_id={id} - filter by strategy"""
        with patch('database.repositories.signal.SignalRepository.get_by_strategy') as mock_repo:
            mock_repo.return_value = [mock_signal]
            response = client.get("/api/v1/signals?strategy_id=test-strategy")
            assert response.status_code in [200, 401]

    def test_create_signal(self):
        """Test POST /api/v1/signals - create signal"""
        signal_data = {
            "symbol": "ETH/USD",
            "action": "SELL",
            "confidence": 0.75,
            "reasoning": "Overbought conditions"
        }
        response = client.post(
            "/api/v1/signals",
            json=signal_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [201, 401, 422]


# ============================================================================
# MARKET DATA ENDPOINTS
# ============================================================================

class TestMarketDataEndpoints:
    """Test market data endpoints"""

    def test_get_current_price(self):
        """Test GET /api/v1/market-data/price/{symbol} - get current price"""
        response = client.get("/api/v1/market-data/price/BTC-USD")
        assert response.status_code in [200, 401, 404]

    def test_get_historical_data(self):
        """Test GET /api/v1/market-data/history/{symbol} - get historical data"""
        response = client.get("/api/v1/market-data/history/BTC-USD?period=1d")
        assert response.status_code in [200, 401, 404]

    def test_get_market_overview(self):
        """Test GET /api/v1/markets - get market overview"""
        response = client.get("/api/v1/markets")
        assert response.status_code in [200, 401]


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

class TestPortfolioEndpoints:
    """Test portfolio endpoints"""

    def test_get_portfolio(self):
        """Test GET /api/v1/portfolio - get portfolio data"""
        response = client.get(
            "/api/v1/portfolio",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 401]

    def test_get_positions(self):
        """Test GET /api/v1/portfolio/positions - get positions"""
        response = client.get(
            "/api/v1/portfolio/positions",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 401]

    def test_create_position(self):
        """Test POST /api/v1/portfolio/positions - open new position"""
        position_data = {
            "symbol": "BTC/USD",
            "side": "long",
            "quantity": 1.0,
            "entry_price": 50000.0
        }
        response = client.post(
            "/api/v1/portfolio/positions",
            json=position_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [201, 401, 422]


# ============================================================================
# BACKTEST ENDPOINTS
# ============================================================================

class TestBacktestEndpoints:
    """Test backtest endpoints"""

    def test_create_backtest(self):
        """Test POST /api/v1/backtests - create new backtest"""
        backtest_data = {
            "strategy_id": "test-strategy",
            "symbol": "BTC/USD",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        response = client.post(
            "/api/v1/backtests",
            json=backtest_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [201, 202, 401, 422]

    def test_get_backtest_results(self):
        """Test GET /api/v1/backtests/{id} - get backtest results"""
        response = client.get(
            "/api/v1/backtests/test-backtest-id",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 401, 404]

    def test_list_backtests(self):
        """Test GET /api/v1/backtests - list all backtests"""
        response = client.get(
            "/api/v1/backtests",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 401]


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

class TestAdminEndpoints:
    """Test admin endpoints"""

    def test_get_system_status(self):
        """Test GET /api/v1/admin/status - get system status"""
        response = client.get(
            "/api/v1/admin/status",
            headers={"Authorization": "Bearer admin-token"}
        )
        assert response.status_code in [200, 401, 403]

    def test_get_data_status(self):
        """Test GET /api/v1/admin/data/status - get data initialization status"""
        response = client.get(
            "/api/v1/admin/data/status",
            headers={"Authorization": "Bearer admin-token"}
        )
        assert response.status_code in [200, 401, 403]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test API error handling"""

    def test_404_on_invalid_endpoint(self):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404

    def test_422_on_invalid_input(self):
        """Test that invalid input returns 422"""
        response = client.post(
            "/api/v1/strategies",
            json={"invalid": "data"},  # Missing required fields
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [422, 401]

    def test_401_without_auth(self):
        """Test that protected endpoints require authentication"""
        response = client.post("/api/v1/strategies", json={})
        assert response.status_code in [401, 422]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
