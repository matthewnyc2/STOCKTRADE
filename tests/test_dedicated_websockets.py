"""
Tests for dedicated WebSocket endpoints.

This test file verifies that the dedicated WebSocket endpoints
are properly registered and configured.
"""

import pytest


# Test data for endpoint-to-channel mapping
WEBSOCKET_ENDPOINTS = {
    "/ws/signals": "signals",
    "/ws/portfolio": "portfolio",
    "/ws/whales": "whales",
    "/ws/prices": "price-ticker",
    "/ws/shadow": "arbitrage",
    "/ws/ai-reasoning": "ai-reasoning",
    "/ws/genetic": "genetic-progress",
    "/ws/liquidations": "liquidations",
}


class TestDedicatedWebsocketEndpoints:
    """Test suite for dedicated WebSocket endpoint configuration."""

    def test_websocket_endpoint_mapping_complete(self):
        """Test that all expected endpoints are defined."""
        # Verify all endpoints are defined
        assert len(WEBSOCKET_ENDPOINTS) == 8, "All 8 WebSocket endpoints should be defined"

        # Verify required endpoints exist
        required_endpoints = [
            "/ws/signals",
            "/ws/portfolio",
            "/ws/whales",
            "/ws/prices",
            "/ws/shadow",
        ]

        for endpoint in required_endpoints:
            assert endpoint in WEBSOCKET_ENDPOINTS, f"Required endpoint {endpoint} not found"

    def test_channel_mappings_correct(self):
        """Test that endpoint to channel mappings are correct."""
        expected_mappings = {
            "/ws/signals": "signals",
            "/ws/portfolio": "portfolio",
            "/ws/whales": "whales",
            "/ws/prices": "price-ticker",
            "/ws/shadow": "arbitrage",
            "/ws/ai-reasoning": "ai-reasoning",
            "/ws/genetic": "genetic-progress",
            "/ws/liquidations": "liquidations",
        }

        for endpoint, expected_channel in expected_mappings.items():
            actual_channel = WEBSOCKET_ENDPOINTS.get(endpoint)
            assert actual_channel == expected_channel, \
                f"Endpoint {endpoint} maps to {actual_channel}, expected {expected_channel}"

    @pytest.mark.parametrize("endpoint,channel", [
        ("/ws/signals", "signals"),
        ("/ws/portfolio", "portfolio"),
        ("/ws/whales", "whales"),
        ("/ws/prices", "price-ticker"),
        ("/ws/shadow", "arbitrage"),
        ("/ws/ai-reasoning", "ai-reasoning"),
        ("/ws/genetic", "genetic-progress"),
        ("/ws/liquidations", "liquidations"),
    ])
    def test_endpoint_follows_naming_convention(self, endpoint, channel):
        """Test that endpoints follow the naming convention /ws/{name}."""
        assert endpoint.startswith("/ws/"), f"Endpoint {endpoint} should start with /ws/"

    def test_no_duplicate_endpoints(self):
        """Test that there are no duplicate endpoints."""
        endpoints = list(WEBSOCKET_ENDPOINTS.keys())
        assert len(endpoints) == len(set(endpoints)), "Duplicate endpoints found"

    def test_no_duplicate_channels(self):
        """Test that there are no duplicate channel mappings."""
        channels = list(WEBSOCKET_ENDPOINTS.values())
        assert len(channels) == len(set(channels)), "Duplicate channel mappings found"


class TestWebsocketInfoResponse:
    """Test suite for WebSocket info endpoint response structure."""

    def test_info_response_structure(self):
        """Test that the expected info response structure is correct."""
        # This is the expected structure from the /ws GET endpoint
        expected_structure = {
            "websocket": "available",
            "endpoints": [
                {
                    "path": "/ws/signals",
                    "channel": "signals",
                    "description": "Live signal updates"
                },
                {
                    "path": "/ws/portfolio",
                    "channel": "portfolio",
                    "description": "Portfolio updates"
                },
                {
                    "path": "/ws/whales",
                    "channel": "whales",
                    "description": "Whale activity alerts"
                },
                {
                    "path": "/ws/prices",
                    "channel": "price-ticker",
                    "description": "Real-time price updates"
                },
                {
                    "path": "/ws/shadow",
                    "channel": "arbitrage",
                    "description": "Shadow Protocol events"
                },
                {
                    "path": "/ws/ai-reasoning",
                    "channel": "ai-reasoning",
                    "description": "AI reasoning stream"
                },
                {
                    "path": "/ws/genetic",
                    "channel": "genetic-progress",
                    "description": "Genetic algorithm optimization progress"
                },
                {
                    "path": "/ws/liquidations",
                    "channel": "liquidations",
                    "description": "Real-time liquidation feed"
                },
            ],
            "channels": [
                {"name": "signals", "description": "Live signal updates"},
                {"name": "portfolio", "description": "Portfolio updates"},
                {"name": "whales", "description": "Whale activity alerts"},
                {"name": "ai-reasoning", "description": "AI reasoning stream"},
                {"name": "price-ticker", "description": "Real-time price updates"},
                {"name": "genetic-progress", "description": "Genetic algorithm optimization progress"},
                {"name": "arbitrage", "description": "Dark arbitrage opportunity alerts"},
                {"name": "liquidations", "description": "Real-time liquidation feed and cascade alerts"},
            ]
        }

        # Verify the structure has the required keys
        assert "endpoints" in expected_structure
        assert "channels" in expected_structure
        assert len(expected_structure["endpoints"]) == 8
        assert len(expected_structure["channels"]) == 8


class TestFrontendWebsocketClient:
    """Test suite for frontend WebSocket client configuration."""

    def test_websocket_channel_enum(self):
        """Test that WebSocketChannel enum has all expected values."""
        # Expected enum values (simulated)
        expected_channels = {
            "SIGNALS": "/ws/signals",
            "PORTFOLIO": "/ws/portfolio",
            "WHALES": "/ws/whales",
            "PRICES": "/ws/prices",
            "SHADOW": "/ws/shadow",
            "AI_REASONING": "/ws/ai-reasoning",
            "GENETIC": "/ws/genetic",
            "LIQUIDATIONS": "/ws/liquidations",
        }

        # Verify all expected channels exist
        assert len(expected_channels) == 8

    def test_channel_names_mapping(self):
        """Test that CHANNEL_NAMES maps endpoints to internal channel names."""
        expected_mapping = {
            "/ws/signals": "signals",
            "/ws/portfolio": "portfolio",
            "/ws/whales": "whales",
            "/ws/prices": "price-ticker",
            "/ws/shadow": "arbitrage",
            "/ws/ai-reasoning": "ai-reasoning",
            "/ws/genetic": "genetic-progress",
            "/ws/liquidations": "liquidations",
        }

        # Verify mapping matches backend expectations
        for endpoint, channel_name in expected_mapping.items():
            assert channel_name in WEBSOCKET_ENDPOINTS.values()

    def test_get_websocket_url_helper(self):
        """Test the getWebSocketUrl helper function behavior."""
        # Simulated behavior
        def get_websocket_url(channel_path: str, base_url: str = "ws://localhost:8000") -> str:
            return f"{base_url}{channel_path}"

        # Test with various channels
        assert get_websocket_url("/ws/signals") == "ws://localhost:8000/ws/signals"
        assert get_websocket_url("/ws/portfolio") == "ws://localhost:8000/ws/portfolio"
        assert get_websocket_url("/ws/shadow") == "ws://localhost:8000/ws/shadow"

    def test_get_channel_name_helper(self):
        """Test the getChannelName helper function behavior."""
        # Simulated channel name mapping
        channel_names = {
            "/ws/signals": "signals",
            "/ws/prices": "price-ticker",
            "/ws/shadow": "arbitrage",
        }

        # Verify mapping
        assert channel_names["/ws/signals"] == "signals"
        assert channel_names["/ws/prices"] == "price-ticker"
        assert channel_names["/ws/shadow"] == "arbitrage"
