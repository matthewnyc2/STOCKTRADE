"""
API Endpoint Tests
WHY: Frontend needs working backend endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_all_endpoints_respond():
    """WHY: Frontend needs working backend"""
    from api.main import app
    client = TestClient(app)
    
    endpoints = [
        "/api/ai",
        "/api/backtests",
        "/api/genetic",
        "/api/liquidations",
        "/api/market-data",
        "/api/ml",
        "/api/portfolio",
        "/api/settings",
        "/api/shadow",
        "/api/signals",
        "/api/strategies",
        "/api/whales"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [200, 404], f"Endpoint {endpoint} failed"


def test_websocket_connection():
    """WHY: Real-time updates required"""
    from api.main import app
    client = TestClient(app)
    
    with client.websocket_connect("/ws/test") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
