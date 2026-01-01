"""
WebSocket Manager for Crypto Quant Laboratory.

Manages WebSocket connections, channel broadcasting, and subscriptions.
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts.

    Supports multiple channels for different data streams:
    - /ws/signals - Live signal updates
    - /ws/portfolio - Portfolio updates
    - /ws/whales - Whale activity alerts
    - /ws/ai-reasoning - AI reasoning stream
    - /ws/price-ticker - Real-time price updates
    """

    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        # Channel -> Set of WebSocket connections
        self._channels: Dict[str, Set[WebSocket]] = defaultdict(set)
        # WebSocket -> Set of channels
        self._subscriptions: Dict[WebSocket, Set[str]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, channels: List[str]) -> None:
        """
        Connect a WebSocket and subscribe to channels.

        Args:
            websocket: The WebSocket connection
            channels: List of channel names to subscribe to
        """
        await websocket.accept()

        for channel in channels:
            self._channels[channel].add(websocket)
            self._subscriptions[websocket].add(channel)

        logger.info(
            f"WebSocket connected and subscribed to channels: {channels}. "
            f"Total connections: {len(self._subscriptions)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a WebSocket and clean up subscriptions.

        Args:
            websocket: The WebSocket connection to disconnect
        """
        channels = self._subscriptions.get(websocket, set())

        for channel in channels:
            self._channels[channel].discard(websocket)

        self._subscriptions.pop(websocket, None)

        logger.info(
            f"WebSocket disconnected from channels: {channels}. "
            f"Total connections: {len(self._subscriptions)}"
        )

    async def subscribe(self, websocket: WebSocket, channel: str) -> None:
        """
        Subscribe a WebSocket to a channel.

        Args:
            websocket: The WebSocket connection
            channel: Channel name to subscribe to
        """
        self._channels[channel].add(websocket)
        self._subscriptions[websocket].add(channel)

        # Send confirmation
        await websocket.send_json(
            {
                "type": "subscription_confirmed",
                "channel": channel,
                "message": f"Subscribed to {channel}",
            }
        )

        logger.info(f"WebSocket subscribed to channel: {channel}")

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        """
        Unsubscribe a WebSocket from a channel.

        Args:
            websocket: The WebSocket connection
            channel: Channel name to unsubscribe from
        """
        self._channels[channel].discard(websocket)
        self._subscriptions[websocket].discard(channel)

        # Send confirmation
        await websocket.send_json(
            {
                "type": "unsubscription_confirmed",
                "channel": channel,
                "message": f"Unsubscribed from {channel}",
            }
        )

        logger.info(f"WebSocket unsubscribed from channel: {channel}")

    async def broadcast(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all subscribers of a channel.

        Args:
            channel: Channel name to broadcast to
            message: Message payload to send
        """
        if channel not in self._channels:
            logger.debug(f"No subscribers for channel: {channel}")
            return

        # Prepare message with channel info
        payload = {
            "channel": channel,
            "data": message,
        }

        # Convert to JSON once for efficiency
        json_payload = json.dumps(payload)

        # Send to all subscribers
        disconnected = set()
        for websocket in self._channels[channel]:
            try:
                await websocket.send_text(json_payload)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

        logger.debug(
            f"Broadcasted message to {len(self._channels[channel])} "
            f"subscribers on channel: {channel}"
        )

    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message payload to send
            websocket: The WebSocket connection to send to
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    def get_subscriber_count(self, channel: str) -> int:
        """
        Get the number of subscribers for a channel.

        Args:
            channel: Channel name

        Returns:
            Number of subscribers
        """
        return len(self._channels.get(channel, set()))

    def get_all_channels(self) -> List[str]:
        """
        Get all active channels.

        Returns:
            List of channel names with subscribers
        """
        return [ch for ch, conns in self._channels.items() if conns]

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about current connections.

        Returns:
            Dictionary with connection statistics
        """
        return {
            "total_connections": len(self._subscriptions),
            "channels": {
                channel: len(conns)
                for channel, conns in self._channels.items()
                if conns
            },
        }


# Global WebSocket manager instance
_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocket manager singleton
    """
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager
