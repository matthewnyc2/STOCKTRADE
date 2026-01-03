import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_websocket_test_endpoint():
    with client.websocket_connect("/ws/test") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
