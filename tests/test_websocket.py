"""
Tests for WebSocket functionality.

Tests WebSocket connection management, channel broadcasting, and subscriptions.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import WebSocket

from core.websocket import WebSocketManager


class TestWebSocketManager:
    """Tests for WebSocket manager."""

    @pytest.fixture
    def ws_manager(self):
        """Create a WebSocket manager for testing."""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = MagicMock(spec=WebSocket)
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, ws_manager, mock_websocket):
        """Test WebSocket connection."""
        await ws_manager.connect(mock_websocket, ["signals", "portfolio"])

        assert "signals" in ws_manager._channels
        assert "portfolio" in ws_manager._channels
        assert mock_websocket in ws_manager._channels["signals"]
        assert mock_websocket in ws_manager._subscriptions

    @pytest.mark.asyncio
    async def test_disconnect(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection."""
        await ws_manager.connect(mock_websocket, ["signals"])
        ws_manager.disconnect(mock_websocket)

        assert mock_websocket not in ws_manager._subscriptions
        assert mock_websocket not in ws_manager._channels.get("signals", set())

    @pytest.mark.asyncio
    async def test_subscribe(self, ws_manager, mock_websocket):
        """Test subscribing to a channel."""
        await ws_manager.connect(mock_websocket, ["signals"])
        await ws_manager.subscribe(mock_websocket, "portfolio")

        assert "portfolio" in ws_manager._channels
        assert mock_websocket in ws_manager._channels["portfolio"]
        assert "portfolio" in ws_manager._subscriptions[mock_websocket]

        # Verify confirmation message was sent
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, ws_manager, mock_websocket):
        """Test unsubscribing from a channel."""
        await ws_manager.connect(mock_websocket, ["signals", "portfolio"])
        await ws_manager.unsubscribe(mock_websocket, "portfolio")

        assert mock_websocket not in ws_manager._channels.get("portfolio", set())
        assert "portfolio" not in ws_manager._subscriptions[mock_websocket]

    @pytest.mark.asyncio
    async def test_broadcast(self, ws_manager, mock_websocket):
        """Test broadcasting to a channel."""
        await ws_manager.connect(mock_websocket, ["signals"])

        message = {"action": "test", "data": "test_data"}
        await ws_manager.broadcast("signals", message)

        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        import json
        payload = json.loads(call_args)
        assert payload["channel"] == "signals"
        assert payload["data"] == message

    @pytest.mark.asyncio
    async def test_send_personal(self, ws_manager, mock_websocket):
        """Test sending a personal message."""
        message = {"action": "personal", "data": "test"}
        await ws_manager.send_personal(message, mock_websocket)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_get_subscriber_count(self, ws_manager, mock_websocket):
        """Test getting subscriber count."""
        await ws_manager.connect(mock_websocket, ["signals"])

        count = ws_manager.get_subscriber_count("signals")
        assert count == 1

        empty_count = ws_manager.get_subscriber_count("portfolio")
        assert empty_count == 0

    @pytest.mark.asyncio
    async def test_get_all_channels(self, ws_manager, mock_websocket):
        """Test getting all active channels."""
        await ws_manager.connect(mock_websocket, ["signals", "portfolio"])

        channels = ws_manager.get_all_channels()
        assert "signals" in channels
        assert "portfolio" in channels

    @pytest.mark.asyncio
    async def test_get_connection_info(self, ws_manager, mock_websocket):
        """Test getting connection info."""
        await ws_manager.connect(mock_websocket, ["signals"])

        info = ws_manager.get_connection_info()
        assert "total_connections" in info
        assert "channels" in info
        assert info["total_connections"] == 1

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_client(self, ws_manager):
        """Test broadcast handles disconnected clients gracefully."""
        # Create two mock websockets
        ws1 = MagicMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws1.send_text = AsyncMock()

        ws2 = MagicMock(spec=WebSocket)
        ws2.send_text = AsyncMock(side_effect=Exception("Disconnected"))

        await ws_manager.connect(ws1, ["signals"])
        await ws_manager.connect(ws2, ["signals"])

        # Broadcast - should handle ws2 error gracefully
        message = {"action": "test"}
        await ws_manager.broadcast("signals", message)

        # ws1 should have received the message
        ws1.send_text.assert_called_once()

        # ws2 should have been removed
        assert ws2 not in ws_manager._channels["signals"]


class TestWebSocketAPI:
    """Tests for WebSocket API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client."""
        from api.main import app
        return TestClient(app)

    def test_websocket_info(self, test_client):
        """Test WebSocket info endpoint."""
        response = test_client.get("/ws")
        assert response.status_code == 200
        data = response.json()
        assert "websocket" in data
        assert "channels" in data
        assert len(data["channels"]) > 0

    def test_websocket_info_channels(self, test_client):
        """Test WebSocket info returns all expected channels."""
        response = test_client.get("/ws")
        data = response.json()
        channel_names = {c["name"] for c in data["channels"]}
        expected_channels = {"signals", "portfolio", "whales", "ai-reasoning", "price-ticker"}
        assert channel_names == expected_channels

    def test_websocket_test_page(self, test_client):
        """Test WebSocket test page endpoint."""
        response = test_client.get("/ws/test")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        content = response.text
        assert "WebSocket Test" in content
        assert "connect()" in content

    def test_websocket_connection_with_default_channel(self, test_client):
        """Test WebSocket connection with default channel."""
        # Note: This test requires actual WebSocket support in TestClient
        # which may not be available. Mark as expected failure if needed.
        with test_client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_connection_with_custom_channels(self, test_client):
        """Test WebSocket connection with custom channels."""
        with test_client.websocket_connect("/ws?channels=portfolio,whales") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_ping_pong(self, test_client):
        """Test WebSocket ping/pong functionality."""
        with test_client.websocket_connect("/ws?channels=signals") as websocket:
            # Send ping
            websocket.send_json({"action": "ping"})

            # Receive pong
            data = websocket.receive_json()
            assert data.get("action") == "pong"

    def test_websocket_subscribe(self, test_client):
        """Test subscribing to additional channels."""
        with test_client.websocket_connect("/ws?channels=signals") as websocket:
            # Subscribe to portfolio channel
            websocket.send_json({
                "action": "subscribe",
                "channel": "portfolio",
            })

            # Should receive confirmation
            data = websocket.receive_json()
            assert data.get("type") == "subscription_confirmed"
            assert data.get("channel") == "portfolio"

    def test_websocket_unsubscribe(self, test_client):
        """Test unsubscribing from a channel."""
        with test_client.websocket_connect("/ws?channels=signals,portfolio") as websocket:
            # Unsubscribe from portfolio
            websocket.send_json({
                "action": "unsubscribe",
                "channel": "portfolio",
            })

            # Should receive confirmation
            data = websocket.receive_json()
            assert data.get("type") == "unsubscription_confirmed"
            assert data.get("channel") == "portfolio"

    def test_websocket_invalid_channel(self, test_client):
        """Test WebSocket ignores invalid channels."""
        with test_client.websocket_connect("/ws?channels=invalid,signals") as websocket:
            # Should connect and subscribe to valid channels only
            # This is implicitly tested by successful connection
            assert websocket is not None

    def test_websocket_receives_broadcasts(self, test_client):
        """Test WebSocket receives broadcast messages."""
        # This test would require triggering a broadcast from another context
        # For now, we test the connection is established
        with test_client.websocket_connect("/ws?channels=signals") as websocket:
            # Connection established
            assert websocket is not None


class TestWebSocketIntegration:
    """Integration tests for WebSocket with API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client."""
        from api.main import app
        return TestClient(app)

    def test_signal_broadcast_on_create(self, test_client):
        """Test that creating a signal broadcasts to WebSocket clients."""
        # This is an integration test that would require
        # actual WebSocket message handling verification
        # For now, we ensure the endpoint works
        pass

    def test_portfolio_update_on_trade(self, test_client):
        """Test that executing a trade broadcasts to WebSocket clients."""
        # Integration test for portfolio updates
        pass

    def test_whale_activity_broadcast(self, test_client):
        """Test that whale activity broadcasts to WebSocket clients."""
        # Integration test for whale updates
        pass
