"""
Dashboard Tests - Priority #1
WHY: Main user interface must work for trading
"""
import pytest
from fastapi.testclient import TestClient


def test_dashboard_page_loads():
    """WHY: Main user interface must work"""
    from api.main import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_dashboard_components_render():
    """WHY: Trading widgets must display"""
    from api.main import app
    client = TestClient(app)
    response = client.get("/api/dashboard/components")
    assert response.status_code == 200
    data = response.json()
    assert "charts" in data
    assert "tables" in data
    assert "controls" in data


def test_real_time_data_updates():
    """WHY: Live trading data required"""
    from api.main import app
    client = TestClient(app)
    with client.websocket_connect("/ws/dashboard") as websocket:
        data = websocket.receive_json()
        assert "market_data" in data
        assert "timestamp" in data
