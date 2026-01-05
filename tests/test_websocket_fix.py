"""
WebSocket Fix Tests
WHY: WebSocket /ws/test endpoint must handle ping/pong correctly
"""
import pytest
from fastapi.testclient import TestClient


def test_websocket_ping_pong():
    """WHY: Real-time updates require working WebSocket"""
    from api.main import app
    client = TestClient(app)
    
    with client.websocket_connect("/ws/test") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
