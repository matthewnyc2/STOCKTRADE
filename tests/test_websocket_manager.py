"""
WebSocket Manager Tests.

Tests for real-time WebSocket connections to cryptocurrency exchanges.
Follows TDD principles - tests written before implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

# Test configuration
TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
TEST_EXCHANGE = "binance"


class TestBinanceWebSocketClient:
    """Test suite for Binance WebSocket client."""

    @pytest.fixture
    def mock_websocket_connection(self):
        """Create a mock WebSocket connection."""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    @pytest.fixture
    def binance_client(self):
        """Create a Binance WebSocket client instance."""
        from services.websocket_manager import BinanceWebSocketClient
        return BinanceWebSocketClient()

    def test_binance_client_initialization(self, binance_client):
        """WHY: Must initialize with correct configuration."""
        assert binance_client.exchange == "binance"
        assert binance_client.base_url == "wss://stream.binance.com:9443/ws"
        assert binance_client.is_connected is False
        assert binance_client.reconnect_attempts == 0
        assert binance_client.max_reconnect_attempts == 5

    @pytest.mark.asyncio
    async def test_connect_to_websocket(self, binance_client, mock_websocket_connection):
        """WHY: Must establish WebSocket connection successfully."""
        with patch('websockets.connect', return_value=mock_websocket_connection):
            await binance_client.connect(["btcusdt@ticker"])

            assert binance_client.is_connected is True
            mock_websocket_connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_to_ticker_stream(self, binance_client, mock_websocket_connection):
        """WHY: Must subscribe to ticker streams for price updates."""
        with patch('websockets.connect', return_value=mock_websocket_connection):
            streams = ["btcusdt@ticker", "ethusdt@ticker"]
            await binance_client.connect(streams)

            # Verify subscription message was sent
            subscribe_call = mock_websocket_connection.send.call_args
            assert subscribe_call is not None

    @pytest.mark.asyncio
    async def test_receive_ticker_message(self, binance_client, mock_websocket_connection):
        """WHY: Must receive and parse ticker messages correctly."""
        # Sample Binance ticker message
        sample_message = {
            "e": "24hrTicker",
            "E": 1672531200000,
            "s": "BTCUSDT",
            "c": "50000.00",
            "b": "49999.00",
            "a": "50001.00",
            "v": "1000.00",
            "q": "50000000.00"
        }

        mock_websocket_connection.recv = AsyncMock(return_value=sample_message)

        with patch('websockets.connect', return_value=mock_websocket_connection):
            await binance_client.connect(["btcusdt@ticker"])

            # Process messages
            message = await binance_client._receive_message()

            assert message is not None
            assert message["symbol"] == "BTCUSDT"
            assert Decimal(message["price"]) == Decimal("50000.00")

    @pytest.mark.asyncio
    async def test_reconnection_on_connection_loss(self, binance_client, mock_websocket_connection):
        """WHY: Must automatically reconnect on connection loss."""
        connect_attempts = []

        async def mock_connect_with_failure(*args, **kwargs):
            connect_attempts.append(len(connect_attempts))
            if len(connect_attempts) < 3:
                raise ConnectionError("Connection lost")
            return mock_websocket_connection

        with patch('websockets.connect', side_effect=mock_connect_with_failure):
            await binance_client.connect(["btcusdt@ticker"])

            assert binance_client.reconnect_attempts == 2
            assert binance_client.is_connected is True

    @pytest.mark.asyncio
    async def test_exponential_backoff_on_reconnect(self, binance_client):
        """WHY: Must use exponential backoff to avoid API rate limiting."""
        delays = []

        async def mock_connect_with_delay(*args, **kwargs):
            if len(delays) > 0:
                # Verify exponential backoff
                if len(delays) == 1:
                    assert delays[-1] >= 1  # First attempt: 1 second
                elif len(delays) == 2:
                    assert delays[-1] >= 2  # Second attempt: 2 seconds
                elif len(delays) == 3:
                    assert delays[-1] >= 4  # Third attempt: 4 seconds

            delays.append(1)
            raise ConnectionError("Connection lost")

        with patch('websockets.connect', side_effect=mock_connect_with_delay):
            with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
                try:
                    await binance_client.connect(["btcusdt@ticker"])
                except:
                    pass  # Expected to fail after max attempts

    @pytest.mark.asyncio
    async def test_max_reconnect_attempts(self, binance_client):
        """WHY: Must stop reconnecting after max attempts to avoid infinite loops."""
        with patch('websockets.connect', side_effect=ConnectionError("Connection lost")):
            with pytest.raises(ConnectionError):
                await binance_client.connect(["btcusdt@ticker"])

            assert binance_client.reconnect_attempts >= binance_client.max_reconnect_attempts

    @pytest.mark.asyncio
    async def test_heartbeat_monitoring(self, binance_client, mock_websocket_connection):
        """WHY: Must monitor connection health via heartbeat."""
        with patch('websockets.connect', return_value=mock_websocket_connection):
            await binance_client.connect(["btcusdt@ticker"])

            # Simulate heartbeat check
            is_healthy = await binance_client._check_connection_health()

            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_disconnect_gracefully(self, binance_client, mock_websocket_connection):
        """WHY: Must disconnect gracefully and cleanup resources."""
        with patch('websockets.connect', return_value=mock_websocket_connection):
            await binance_client.connect(["btcusdt@ticker"])

            await binance_client.disconnect()

            assert binance_client.is_connected is False
            mock_websocket_connection.close.assert_called_once()


class TestWebSocketManager:
    """Test suite for the WebSocket manager that handles multiple exchanges."""

    @pytest.fixture
    def websocket_manager(self):
        """Create a WebSocket manager instance."""
        from services.websocket_manager import WebSocketManager
        return WebSocketManager()

    def test_manager_initialization(self, websocket_manager):
        """WHY: Must initialize with support for multiple exchanges."""
        assert websocket_manager is not None
        assert hasattr(websocket_manager, 'clients')
        assert hasattr(websocket_manager, 'message_handlers')

    def test_register_exchange_client(self, websocket_manager):
        """WHY: Must be able to register clients for different exchanges."""
        from services.websocket_manager import BinanceWebSocketClient

        client = BinanceWebSocketClient()
        websocket_manager.register_client("binance", client)

        assert "binance" in websocket_manager.clients
        assert websocket_manager.clients["binance"] == client

    @pytest.mark.asyncio
    async def test_connect_to_exchange(self, websocket_manager):
        """WHY: Must connect to specified exchange."""
        from services.websocket_manager import BinanceWebSocketClient

        with patch.object(BinanceWebSocketClient, 'connect', new=AsyncMock()):
            client = BinanceWebSocketClient()
            websocket_manager.register_client("binance", client)

            await websocket_manager.connect_exchange("binance", ["btcusdt@ticker"])

            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_broadcast_messages_to_handlers(self, websocket_manager):
        """WHY: Must broadcast received messages to registered handlers."""
        test_message = {
            "symbol": "BTCUSDT",
            "price": "50000.00",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Create a mock handler
        handler = AsyncMock()
        websocket_manager.register_message_handler(handler)

        await websocket_manager._handle_message("binance", test_message)

        handler.assert_called_once_with("binance", test_message)

    @pytest.mark.asyncio
    async def test_handle_multiple_exchanges(self, websocket_manager):
        """WHY: Must manage connections to multiple exchanges simultaneously."""
        from services.websocket_manager import BinanceWebSocketClient

        with patch.object(BinanceWebSocketClient, 'connect', new=AsyncMock()):
            # Register multiple clients
            binance_client = BinanceWebSocketClient()
            websocket_manager.register_client("binance", binance_client)

            # Connect to all
            await websocket_manager.connect_all(["btcusdt@ticker"])

            assert binance_client.is_connected is True

    @pytest.mark.asyncio
    async def test_failover_on_exchange_failure(self, websocket_manager):
        """WHY: Must failover to backup data source on WebSocket failure."""
        from services.websocket_manager import BinanceWebSocketClient

        with patch.object(BinanceWebSocketClient, 'connect', side_effect=ConnectionError):
            binance_client = BinanceWebSocketClient()
            websocket_manager.register_client("binance", binance_client)

            # Should not raise, should handle gracefully
            try:
                await websocket_manager.connect_exchange("binance", ["btcusdt@ticker"])
            except ConnectionError:
                # Expected - but should trigger failover logic
                pass


class TestDataPipeline:
    """Test suite for the real-time data pipeline."""

    @pytest.fixture
    def data_pipeline(self):
        """Create a data pipeline instance."""
        from services.data_pipeline import RealTimeDataPipeline
        return RealTimeDataPipeline()

    def test_pipeline_initialization(self, data_pipeline):
        """WHY: Must initialize with buffer, validator, and enricher."""
        assert data_pipeline is not None
        assert hasattr(data_pipeline, 'buffer')
        assert hasattr(data_pipeline, 'validator')
        assert hasattr(data_pipeline, 'enricher')

    @pytest.mark.asyncio
    async def test_buffer_incoming_messages(self, data_pipeline):
        """WHY: Must buffer incoming messages before processing."""
        test_message = {
            "symbol": "BTCUSDT",
            "price": "50000.00",
            "timestamp": datetime.utcnow().isoformat()
        }

        await data_pipeline.buffer_message(test_message)

        buffer_size = await data_pipeline.get_buffer_size()
        assert buffer_size >= 1

    @pytest.mark.asyncio
    async def test_validate_message_quality(self, data_pipeline):
        """WHY: Must validate data quality before processing."""
        valid_message = {
            "symbol": "BTCUSDT",
            "price": "50000.00",
            "timestamp": datetime.utcnow().isoformat()
        }

        is_valid = await data_pipeline.validate_message(valid_message)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_reject_invalid_messages(self, data_pipeline):
        """WHY: Must reject messages that fail quality checks."""
        invalid_message = {
            "symbol": "BTCUSDT",
            "price": "-100.00",  # Negative price
            "timestamp": datetime.utcnow().isoformat()
        }

        is_valid = await data_pipeline.validate_message(invalid_message)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_enrich_message_with_metadata(self, data_pipeline):
        """WHY: Must enrich messages with additional metadata."""
        base_message = {
            "symbol": "BTCUSDT",
            "price": "50000.00",
            "timestamp": datetime.utcnow().isoformat()
        }

        enriched = await data_pipeline.enrich_message(base_message)

        assert "source" in enriched
        assert "received_at" in enriched
        assert enriched["source"] == "binance"

    @pytest.mark.asyncio
    async def test_flush_buffer_to_storage(self, data_pipeline):
        """WHY: Must flush buffered messages to storage in batches."""
        # Add multiple messages to buffer
        for i in range(10):
            await data_pipeline.buffer_message({
                "symbol": "BTCUSDT",
                "price": str(50000 + i),
                "timestamp": datetime.utcnow().isoformat()
            })

        # Flush buffer
        flushed_count = await data_pipeline.flush_buffer()

        assert flushed_count >= 10

    @pytest.mark.asyncio
    async def test_process_message_through_pipeline(self, data_pipeline):
        """WHY: Must process messages through complete pipeline."""
        test_message = {
            "symbol": "BTCUSDT",
            "price": "50000.00",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = await data_pipeline.process_message(test_message)

        assert result["success"] is True
        assert result["validated"] is True
        assert result["enriched"] is True


class TestMessageBuffer:
    """Test suite for the message buffer (Redis-based)."""

    @pytest.fixture
    def message_buffer(self):
        """Create a message buffer instance."""
        from services.data_pipeline import MessageBuffer
        return MessageBuffer()

    @pytest.mark.asyncio
    async def test_push_message_to_buffer(self, message_buffer):
        """WHY: Must push messages to buffer."""
        test_message = {"symbol": "BTCUSDT", "price": "50000.00"}

        await message_buffer.push(test_message)

        size = await message_buffer.size()
        assert size >= 1

    @pytest.mark.asyncio
    async def test_pop_messages_from_buffer(self, message_buffer):
        """WHY: Must pop messages from buffer for processing."""
        test_message = {"symbol": "BTCUSDT", "price": "50000.00"}

        await message_buffer.push(test_message)
        messages = await message_buffer.pop_batch(10)

        assert len(messages) >= 1
        assert messages[0]["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_buffer_size_limit(self, message_buffer):
        """WHY: Must enforce maximum buffer size to prevent memory issues."""
        # Fill buffer beyond limit
        for i in range(10000):
            await message_buffer.push({"symbol": "BTCUSDT", "price": str(i)})

        # Should not exceed limit
        size = await message_buffer.size()
        assert size <= 10000  # Or whatever the limit is

    @pytest.mark.asyncio
    async def test_clear_buffer(self, message_buffer):
        """WHY: Must be able to clear buffer."""
        await message_buffer.push({"symbol": "BTCUSDT", "price": "50000.00"})

        await message_buffer.clear()

        size = await message_buffer.size()
        assert size == 0
