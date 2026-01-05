"""
Real-time Data Pipeline for Market Data.

Handles buffering, validation, enrichment, and storage of real-time
market data from WebSocket feeds. Uses Redis for buffering and
provides quality checks before data reaches the database.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""
    buffer_max_size: int = 10000
    buffer_flush_interval: float = 1.0  # seconds
    buffer_flush_threshold: int = 100  # Flush when buffer reaches this size
    validation_enabled: bool = True
    enrichment_enabled: bool = True
    storage_enabled: bool = True


@dataclass
class PipelineStats:
    """Statistics for the data pipeline."""
    messages_received: int = 0
    messages_buffered: int = 0
    messages_validated: int = 0
    messages_enriched: int = 0
    messages_stored: int = 0
    messages_rejected: int = 0
    validation_errors: Dict[str, int] = field(default_factory=dict)
    buffer_flushes: int = 0
    last_flush_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messages_received": self.messages_received,
            "messages_buffered": self.messages_buffered,
            "messages_validated": self.messages_validated,
            "messages_enriched": self.messages_enriched,
            "messages_stored": self.messages_stored,
            "messages_rejected": self.messages_rejected,
            "validation_errors": self.validation_errors,
            "buffer_flushes": self.buffer_flushes,
            "last_flush_time": self.last_flush_time.isoformat() if self.last_flush_time else None
        }


class MessageBuffer:
    """
    In-memory buffer for incoming messages.

    Acts as a staging area before messages are validated, enriched,
    and stored. Uses a deque-like structure for efficient operations.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize message buffer.

        Args:
            max_size: Maximum number of messages to buffer
        """
        self.max_size = max_size
        self._buffer: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

        logger.info(f"MessageBuffer initialized with max_size={max_size}")

    async def push(self, message: Dict[str, Any]) -> bool:
        """
        Push a message to the buffer.

        Args:
            message: Message to buffer

        Returns:
            True if message was buffered, False if buffer is full
        """
        async with self._lock:
            if len(self._buffer) >= self.max_size:
                logger.warning(f"Buffer full ({self.max_size} messages), dropping message")
                return False

            self._buffer.append(message)
            return True

    async def pop_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Pop a batch of messages from the buffer.

        Args:
            batch_size: Maximum number of messages to pop

        Returns:
            List of messages
        """
        async with self._lock:
            batch_size = min(batch_size, len(self._buffer))
            batch = self._buffer[:batch_size]
            self._buffer = self._buffer[batch_size:]
            return batch

    async def size(self) -> int:
        """
        Get current buffer size.

        Returns:
            Number of messages in buffer
        """
        async with self._lock:
            return len(self._buffer)

    async def clear(self):
        """Clear all messages from buffer."""
        async with self._lock:
            self._buffer = []
            logger.info("Buffer cleared")


class DataValidator:
    """
    Validates incoming market data for quality issues.

    Checks for:
    - Required fields presence
    - Data type correctness
    - Value validity (e.g., positive prices)
    - Timestamp freshness
    """

    def __init__(self):
        """Initialize data validator."""
        self.validation_errors = defaultdict(int)

        logger.info("DataValidator initialized")

    async def validate(self, message: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a message.

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ["symbol", "timestamp"]
        for field in required_fields:
            if field not in message:
                error = f"Missing required field: {field}"
                self.validation_errors[error] += 1
                return False, error

        # Validate symbol
        if not isinstance(message["symbol"], str) or len(message["symbol"]) == 0:
            error = "Invalid symbol"
            self.validation_errors[error] += 1
            return False, error

        # Validate timestamp
        try:
            if isinstance(message["timestamp"], str):
                timestamp = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
            elif isinstance(message["timestamp"], datetime):
                timestamp = message["timestamp"]
            else:
                error = "Invalid timestamp type"
                self.validation_errors[error] += 1
                return False, error

            # Check if timestamp is not too old (more than 1 hour)
            age = datetime.utcnow() - timestamp
            if age > timedelta(hours=1):
                error = f"Timestamp too old: {age}"
                self.validation_errors[error] += 1
                return False, error

        except Exception as e:
            error = f"Invalid timestamp: {e}"
            self.validation_errors[error] += 1
            return False, error

        # Validate price if present
        if "price" in message:
            try:
                price = Decimal(str(message["price"]))
                if price < 0:
                    error = "Negative price"
                    self.validation_errors[error] += 1
                    return False, error
                if price == 0:
                    error = "Zero price"
                    self.validation_errors[error] += 1
                    return False, error
            except Exception:
                error = "Invalid price format"
                self.validation_errors[error] += 1
                return False, error

        # Validate volume if present
        if "volume" in message or "volume_24h" in message:
            volume_key = "volume" if "volume" in message else "volume_24h"
            try:
                volume = Decimal(str(message[volume_key]))
                if volume < 0:
                    error = "Negative volume"
                    self.validation_errors[error] += 1
                    return False, error
            except Exception:
                error = "Invalid volume format"
                self.validation_errors[error] += 1
                return False, error

        return True, None

    def get_validation_errors(self) -> Dict[str, int]:
        """
        Get validation error counts.

        Returns:
            Dictionary of error types and counts
        """
        return dict(self.validation_errors)


class DataEnricher:
    """
    Enriches messages with additional metadata.

    Adds:
    - Source tracking
    - Received timestamp
    - Data quality hash
    - Normalized symbols
    """

    def __init__(self):
        """Initialize data enricher."""
        logger.info("DataEnricher initialized")

    async def enrich(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a message with metadata.

        Args:
            message: Message to enrich

        Returns:
            Enriched message
        """
        enriched = message.copy()

        # Add received timestamp
        enriched["received_at"] = datetime.utcnow().isoformat()

        # Add source if not present
        if "source" not in enriched:
            enriched["source"] = enriched.get("exchange", "unknown")

        # Add quality hash for deduplication
        message_str = json.dumps(message, sort_keys=True)
        enriched["quality_hash"] = hashlib.sha256(message_str.encode()).hexdigest()[:16]

        # Normalize symbol
        if "symbol" in enriched:
            enriched["symbol"] = enriched["symbol"].upper()
            enriched["normalized_symbol"] = enriched["symbol"].replace("-", "")

        return enriched


class DataStorage:
    """
    Stores validated and enriched messages.

    Handles:
    - Batch database writes
    - Redis caching
    - Error handling and retries
    """

    def __init__(self):
        """Initialize data storage."""
        self._write_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._storage_task: Optional[asyncio.Task] = None

        logger.info("DataStorage initialized")

    async def start(self):
        """Start the storage background task."""
        if self._storage_task is None:
            self._storage_task = asyncio.create_task(self._storage_loop())
            logger.info("DataStorage started")

    async def stop(self):
        """Stop the storage background task."""
        if self._storage_task:
            self._storage_task.cancel()
            try:
                await self._storage_task
            except asyncio.CancelledError:
                pass
            logger.info("DataStorage stopped")

    async def store(self, message: Dict[str, Any]):
        """
        Queue a message for storage.

        Args:
            message: Message to store
        """
        try:
            await self._write_queue.put(message)
        except asyncio.QueueFull:
            logger.error("Storage queue full, dropping message")

    async def _storage_loop(self):
        """Background task that writes messages to storage."""
        while True:
            try:
                # Get batch of messages
                batch = []
                for _ in range(100):  # Process in batches of 100
                    try:
                        message = await asyncio.wait_for(
                            self._write_queue.get(),
                            timeout=0.1
                        )
                        batch.append(message)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    await self._write_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in storage loop: {e}")

    async def _write_batch(self, batch: List[Dict[str, Any]]):
        """
        Write a batch of messages to storage.

        Args:
            batch: List of messages to write
        """
        try:
            # TODO: Implement actual database writes
            # For now, just log
            logger.debug(f"Writing {len(batch)} messages to storage")

            # Separate by message type
            ticker_messages = [m for m in batch if m.get("type") == "ticker"]
            trade_messages = [m for m in batch if m.get("type") == "trade"]
            orderbook_messages = [m for m in batch if m.get("type") == "orderbook"]

            # Write each type
            if ticker_messages:
                await self._write_tickers(ticker_messages)
            if trade_messages:
                await self._write_trades(trade_messages)
            if orderbook_messages:
                await self._write_orderbooks(orderbook_messages)

        except Exception as e:
            logger.error(f"Error writing batch to storage: {e}")

    async def _write_tickers(self, tickers: List[Dict[str, Any]]):
        """Write ticker messages to database."""
        # TODO: Implement database write
        logger.debug(f"Writing {len(tickers)} ticker messages")

    async def _write_trades(self, trades: List[Dict[str, Any]]):
        """Write trade messages to database."""
        # TODO: Implement database write
        logger.debug(f"Writing {len(trades)} trade messages")

    async def _write_orderbooks(self, orderbooks: List[Dict[str, Any]]):
        """Write orderbook messages to database."""
        # TODO: Implement database write
        logger.debug(f"Writing {len(orderbooks)} orderbook messages")


class RealTimeDataPipeline:
    """
    Real-time data pipeline for WebSocket market data.

    Orchestrates the flow of data from WebSocket feeds through
    buffering, validation, enrichment, and storage.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the data pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()

        # Initialize components
        self.buffer = MessageBuffer(max_size=self.config.buffer_max_size)
        self.validator = DataValidator()
        self.enricher = DataEnricher()
        self.storage = DataStorage()

        # Statistics
        self.stats = PipelineStats()

        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("RealTimeDataPipeline initialized")

    async def start(self):
        """Start the data pipeline."""
        if self._running:
            logger.warning("Pipeline already running")
            return

        self._running = True

        # Start storage
        await self.storage.start()

        # Start periodic buffer flush
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info("DataPipeline started")

    async def stop(self):
        """Stop the data pipeline."""
        if not self._running:
            return

        self._running = False

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Stop storage
        await self.storage.stop()

        # Flush remaining buffer
        await self.flush_buffer()

        logger.info("DataPipeline stopped")

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message through the complete pipeline.

        Args:
            message: Message to process

        Returns:
            Result dictionary with processing status
        """
        self.stats.messages_received += 1

        try:
            # 1. Buffer the message
            buffered = await self.buffer_message(message)
            if not buffered:
                self.stats.messages_rejected += 1
                return {
                    "success": False,
                    "reason": "buffer_full",
                    "validated": False,
                    "enriched": False
                }

            self.stats.messages_buffered += 1

            # 2. Validate the message
            if self.config.validation_enabled:
                is_valid, error = await self.validate_message(message)
                if not is_valid:
                    self.stats.messages_rejected += 1
                    return {
                        "success": False,
                        "reason": f"validation_failed: {error}",
                        "validated": False,
                        "enriched": False
                    }

            self.stats.messages_validated += 1

            # 3. Enrich the message
            enriched_message = message
            if self.config.enrichment_enabled:
                enriched_message = await self.enrich_message(message)
                self.stats.messages_enriched += 1

            # 4. Store the message
            if self.config.storage_enabled:
                await self.storage.store(enriched_message)
                self.stats.messages_stored += 1

            return {
                "success": True,
                "validated": True,
                "enriched": True,
                "stored": True
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.stats.messages_rejected += 1
            return {
                "success": False,
                "reason": str(e),
                "validated": False,
                "enriched": False
            }

    async def buffer_message(self, message: Dict[str, Any]) -> bool:
        """
        Buffer a message.

        Args:
            message: Message to buffer

        Returns:
            True if buffered successfully
        """
        return await self.buffer.push(message)

    async def validate_message(self, message: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a message.

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return await self.validator.validate(message)

    async def enrich_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a message.

        Args:
            message: Message to enrich

        Returns:
            Enriched message
        """
        return await self.enricher.enrich(message)

    async def _flush_loop(self):
        """Background task that periodically flushes the buffer."""
        while self._running:
            try:
                await asyncio.sleep(self.config.buffer_flush_interval)

                # Check if buffer needs flushing
                buffer_size = await self.buffer.size()
                if buffer_size >= self.config.buffer_flush_threshold:
                    await self.flush_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")

    async def flush_buffer(self) -> int:
        """
        Flush buffered messages to storage.

        Returns:
            Number of messages flushed
        """
        try:
            # Get batch from buffer
            batch = await self.buffer.pop_batch(1000)

            if not batch:
                return 0

            # Process each message through validation, enrichment, storage
            for message in batch:
                # Validate
                is_valid, error = await self.validator.validate(message)
                if not is_valid:
                    self.stats.messages_rejected += 1
                    continue

                # Enrich
                enriched = await self.enricher.enrich(message)

                # Store
                await self.storage.store(enriched)
                self.stats.messages_stored += 1

            self.stats.buffer_flushes += 1
            self.stats.last_flush_time = datetime.utcnow()

            logger.info(f"Flushed {len(batch)} messages from buffer")
            return len(batch)

        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")
            return 0

    async def get_buffer_size(self) -> int:
        """
        Get current buffer size.

        Returns:
            Number of messages in buffer
        """
        return await self.buffer.size()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with pipeline statistics
        """
        return {
            "config": {
                "buffer_max_size": self.config.buffer_max_size,
                "buffer_flush_interval": self.config.buffer_flush_interval,
                "buffer_flush_threshold": self.config.buffer_flush_threshold,
                "validation_enabled": self.config.validation_enabled,
                "enrichment_enabled": self.config.enrichment_enabled,
                "storage_enabled": self.config.storage_enabled
            },
            "stats": self.stats.to_dict(),
            "buffer_size": asyncio.create_task(self.buffer.size()).result() if self._running else 0,
            "validation_errors": self.validator.get_validation_errors()
        }


# Global pipeline instance
_pipeline: Optional[RealTimeDataPipeline] = None


def get_pipeline() -> RealTimeDataPipeline:
    """
    Get the global data pipeline instance.

    Returns:
        RealTimeDataPipeline singleton
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = RealTimeDataPipeline()
    return _pipeline
