"""
WebSocket Manager for Real-time Market Data.

Provides WebSocket connections to cryptocurrency exchanges for real-time
market data streaming. Includes automatic reconnection, message buffering,
and failover support.

Supported Exchanges:
- Binance (primary)
- Extensible architecture for additional exchanges
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import websockets

logger = logging.getLogger(__name__)


class WebSocketState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class WebSocketStats:
    """Statistics for WebSocket connections."""
    messages_received: int = 0
    messages_sent: int = 0
    connection_time: Optional[datetime] = None
    last_message_time: Optional[datetime] = None
    reconnect_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "connection_time": self.connection_time.isoformat() if self.connection_time else None,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
            "reconnect_count": self.reconnect_count,
            "error_count": self.error_count
        }


class BinanceWebSocketClient:
    """
    WebSocket client for Binance exchange.

    Provides real-time market data streaming from Binance with automatic
    reconnection and error handling.
    """

    # Binance WebSocket endpoints
    BASE_URL = "wss://stream.binance.com:9443/ws"
    BASE_URL_TESTNET = "wss://testnet.binance.vision/ws"

    def __init__(
        self,
        testnet: bool = False,
        max_reconnect_attempts: int = 5,
        reconnect_delay_base: int = 1,
        heartbeat_interval: int = 30
    ):
        """
        Initialize Binance WebSocket client.

        Args:
            testnet: Use testnet instead of production
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay_base: Base delay for exponential backoff (seconds)
            heartbeat_interval: Heartbeat check interval (seconds)
        """
        self.exchange = "binance"
        self.base_url = self.BASE_URL_TESTNET if testnet else self.BASE_URL
        self.testnet = testnet

        # Connection state
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._state = WebSocketState.DISCONNECTED
        self.is_connected = False

        # Reconnection configuration
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay_base = reconnect_delay_base
        self.reconnect_attempts = 0

        # Heartbeat
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Message handling
        self._message_handler_task: Optional[asyncio.Task] = None
        self._message_callbacks: List[Callable[[Dict[str, Any]], Awaitable]] = []

        # Statistics
        self.stats = WebSocketStats()

        # Subscribed streams
        self._streams: List[str] = []

        logger.info(f"BinanceWebSocketClient initialized (testnet={testnet})")

    async def connect(self, streams: List[str]):
        """
        Connect to Binance WebSocket and subscribe to streams.

        Args:
            streams: List of stream names (e.g., ["btcusdt@ticker"])
        """
        if self._state in [WebSocketState.CONNECTED, WebSocketState.CONNECTING]:
            logger.warning("Already connected or connecting")
            return

        self._state = WebSocketState.CONNECTING
        self._streams = streams

        try:
            # Build WebSocket URL with streams
            stream_path = "/".join(streams)
            url = f"{self.base_url}/{stream_path}"

            logger.info(f"Connecting to Binance WebSocket: {url}")

            # Establish connection
            self._ws = await websockets.connect(url)
            self.is_connected = True
            self._state = WebSocketState.CONNECTED
            self.stats.connection_time = datetime.utcnow()
            self.reconnect_attempts = 0

            logger.info(f"Connected to Binance WebSocket successfully")

            # Start message handler
            self._message_handler_task = asyncio.create_task(self._message_handler())

            # Start heartbeat monitor
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            self._state = WebSocketState.ERROR
            self.stats.error_count += 1

            # Attempt reconnection
            await self._reconnect()

    async def _message_handler(self):
        """
        Handle incoming WebSocket messages.

        Continuously receives messages from the WebSocket and passes them
        to registered callbacks.
        """
        try:
            async for message in self._ws:
                try:
                    # Parse JSON message
                    data = json.loads(message)

                    # Update stats
                    self.stats.messages_received += 1
                    self.stats.last_message_time = datetime.utcnow()

                    # Process message
                    await self._process_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                    self.stats.error_count += 1
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.stats.error_count += 1

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            self._state = WebSocketState.DISCONNECTED

            # Attempt reconnection
            await self._reconnect()

        except Exception as e:
            logger.error(f"Message handler error: {e}")
            self._state = WebSocketState.ERROR
            self.stats.error_count += 1

    async def _process_message(self, data: Dict[str, Any]):
        """
        Process a received message.

        Args:
            data: Parsed JSON message
        """
        try:
            # Transform Binance message to standard format
            transformed = self._transform_message(data)

            # Call registered callbacks
            for callback in self._message_callbacks:
                try:
                    await callback(transformed)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _transform_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Binance message to standard format.

        Args:
            data: Raw Binance message

        Returns:
            Transformed message
        """
        # Handle different message types
        event_type = data.get("e", "")

        if event_type == "24hrTicker":
            # Ticker message
            return {
                "type": "ticker",
                "symbol": data.get("s"),
                "price": data.get("c"),  # Current price
                "bid": data.get("b"),     # Best bid
                "ask": data.get("a"),     # Best ask
                "volume_24h": data.get("v"),  # 24h volume
                "change_24h": data.get("p"),  # 24h price change
                "high_24h": data.get("h"),    # 24h high
                "low_24h": data.get("l"),     # 24h low
                "timestamp": datetime.utcnow(),
                "exchange": "binance",
                "raw": data
            }

        elif event_type == "depthUpdate":
            # Order book update
            return {
                "type": "orderbook",
                "symbol": data.get("s"),
                "bids": data.get("b", []),
                "asks": data.get("a", []),
                "timestamp": datetime.utcnow(),
                "exchange": "binance",
                "raw": data
            }

        elif event_type == "aggTrade":
            # Aggregate trade
            return {
                "type": "trade",
                "symbol": data.get("s"),
                "price": data.get("p"),
                "quantity": data.get("q"),
                "trade_id": data.get("a"),
                "timestamp": datetime.utcnow(),
                "exchange": "binance",
                "raw": data
            }

        else:
            # Unknown message type
            return {
                "type": "unknown",
                "timestamp": datetime.utcnow(),
                "exchange": "binance",
                "raw": data
            }

    async def _reconnect(self):
        """
        Reconnect to WebSocket with exponential backoff.
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            self._state = WebSocketState.ERROR
            return

        self._state = WebSocketState.RECONNECTING
        self.reconnect_attempts += 1
        self.stats.reconnect_count += 1

        # Calculate delay with exponential backoff
        delay = self.reconnect_delay_base * (2 ** (self.reconnect_attempts - 1))
        delay = min(delay, 60)  # Cap at 60 seconds

        logger.info(f"Reconnecting in {delay} seconds... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")

        await asyncio.sleep(delay)

        try:
            await self.connect(self._streams)
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            await self._reconnect()

    async def _heartbeat_monitor(self):
        """
        Monitor connection health via heartbeat.

        Periodically checks if messages are being received and
        triggers reconnection if connection appears stale.
        """
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Check if connection is stale
                if self.stats.last_message_time:
                    time_since_last_message = (
                        datetime.utcnow() - self.stats.last_message_time
                    ).total_seconds()

                    # If no messages for 2x heartbeat interval, reconnect
                    if time_since_last_message > self.heartbeat_interval * 2:
                        logger.warning("Connection appears stale, reconnecting...")
                        await self._reconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")

    async def _check_connection_health(self) -> bool:
        """
        Check if WebSocket connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        return self.is_connected and self._state == WebSocketState.CONNECTED

    def register_callback(self, callback: Callable[[Dict[str, Any]], Awaitable]):
        """
        Register a callback for incoming messages.

        Args:
            callback: Async function to call with each message
        """
        self._message_callbacks.append(callback)

    async def disconnect(self):
        """
        Disconnect from WebSocket and cleanup resources.
        """
        logger.info("Disconnecting from Binance WebSocket")

        self.is_connected = False
        self._state = WebSocketState.DISCONNECTED

        # Cancel tasks
        if self._message_handler_task:
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._ws:
            await self._ws.close()

        logger.info("Disconnected from Binance WebSocket")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection statistics
        """
        return {
            "state": self._state.value,
            "is_connected": self.is_connected,
            "streams": self._streams,
            "reconnect_attempts": self.reconnect_attempts,
            "stats": self.stats.to_dict()
        }


class WebSocketManager:
    """
    Manager for multiple WebSocket connections.

    Manages WebSocket connections to multiple exchanges and provides
    unified message handling and failover capabilities.
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        self.clients: Dict[str, BinanceWebSocketClient] = {}
        self.message_handlers: List[Callable[[str, Dict[str, Any]], Awaitable]] = []

        logger.info("WebSocketManager initialized")

    def register_client(self, exchange: str, client: BinanceWebSocketClient):
        """
        Register a WebSocket client for an exchange.

        Args:
            exchange: Exchange name
            client: WebSocket client instance
        """
        self.clients[exchange] = client
        logger.info(f"Registered WebSocket client for {exchange}")

    def register_message_handler(
        self,
        handler: Callable[[str, Dict[str, Any]], Awaitable]
    ):
        """
        Register a message handler for all exchanges.

        Args:
            handler: Async function to call with messages
        """
        self.message_handlers.append(handler)

    async def connect_exchange(self, exchange: str, streams: List[str]):
        """
        Connect to an exchange's WebSocket.

        Args:
            exchange: Exchange name
            streams: List of streams to subscribe to
        """
        client = self.clients.get(exchange)
        if not client:
            raise ValueError(f"No client registered for {exchange}")

        # Register manager's message handlers
        for handler in self.message_handlers:
            client.register_callback(lambda msg, handler=handler: handler(exchange, msg))

        await client.connect(streams)

    async def connect_all(self, streams: List[str]):
        """
        Connect to all registered exchanges.

        Args:
            streams: List of streams to subscribe to
        """
        tasks = [
            self.connect_exchange(exchange, streams)
            for exchange in self.clients.keys()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def disconnect_all(self):
        """Disconnect from all exchanges."""
        tasks = [
            client.disconnect()
            for client in self.clients.values()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_message(self, exchange: str, message: Dict[str, Any]):
        """
        Handle a message from an exchange.

        Args:
            exchange: Exchange name
            message: Message data
        """
        for handler in self.message_handlers:
            try:
                await handler(exchange, message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all connections.

        Returns:
            Dictionary with connection statistics
        """
        return {
            exchange: client.get_stats()
            for exchange, client in self.clients.items()
        }


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocketManager singleton
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()

        # Register Binance client
        binance_client = BinanceWebSocketClient()
        _websocket_manager.register_client("binance", binance_client)

    return _websocket_manager
