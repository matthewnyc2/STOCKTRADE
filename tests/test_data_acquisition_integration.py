"""
Integration tests for the real-time data acquisition system.

Tests the complete flow from WebSocket feeds to storage.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch


@pytest.mark.asyncio
async def test_websocket_to_pipeline_flow():
    """WHY: Must verify data flows from WebSocket through pipeline to storage."""
    from services.websocket_manager import BinanceWebSocketClient
    from services.data_pipeline import RealTimeDataPipeline

    # Create pipeline
    pipeline = RealTimeDataPipeline()
    await pipeline.start()

    # Simulate WebSocket message
    test_message = {
        "type": "ticker",
        "symbol": "BTCUSDT",
        "price": "50000.00",
        "bid": "49999.00",
        "ask": "50001.00",
        "volume_24h": "1000.00",
        "timestamp": datetime.utcnow().isoformat(),
        "exchange": "binance"
    }

    # Process through pipeline
    result = await pipeline.process_message(test_message)

    # Verify processing
    assert result["success"] is True
    assert result["validated"] is True
    assert result["enriched"] is True

    await pipeline.stop()


@pytest.mark.asyncio
async def test_multi_source_failover():
    """WHY: Must verify failover works when primary source fails."""
    from services.multi_source_manager import MultiSourceManager

    manager = MultiSourceManager()

    # Mock primary source to fail
    with patch.object(manager._binance, 'get_ticker', return_value=None):
        # Mock secondary source to succeed
        with patch.object(
            manager._coingecko,
            'get_ticker',
            return_value={
                "symbol": "BTC",
                "price": Decimal("50000.00"),
                "timestamp": datetime.utcnow()
            }
        ):
            ticker, source = await manager.get_ticker("bitcoin")

            assert ticker is not None
            assert ticker["price"] == Decimal("50000.00")
            assert source == "coingecko"


@pytest.mark.asyncio
async def test_gap_detection():
    """WHY: Must verify gap detection identifies missing data."""
    from services.historical_data_manager import GapDetector

    detector = GapDetector()

    # Mock database query to return sparse data
    with patch('database.connection.get_db_session') as mock_session:
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            (datetime(2024, 1, 1, 10, 0), "BTCUSDT"),
            (datetime(2024, 1, 1, 12, 0), "BTCUSDT"),  # 2 hour gap
        ]
        mock_db.query.return_value = mock_query
        mock_session().__enter__.return_value = mock_db

        gaps = detector.detect_gaps(
            "BTCUSDT",
            "1h",
            start=datetime(2024, 1, 1, 9, 0),
            end=datetime(2024, 1, 1, 14, 0)
        )

        # Should detect gaps (initial gap before first data, gap between data points, and trailing gap)
        assert len(gaps) > 0
        assert any(gap.missing_periods > 0 for gap in gaps)  # At least one gap with missing periods


@pytest.mark.asyncio
async def test_data_quality_validation():
    """WHY: Must verify quality checks reject invalid data."""
    from services.data_pipeline import DataValidator

    validator = DataValidator()

    # Test valid data
    valid_message = {
        "symbol": "BTCUSDT",
        "price": "50000.00",
        "timestamp": datetime.utcnow().isoformat()
    }

    is_valid, error = await validator.validate(valid_message)
    assert is_valid is True
    assert error is None

    # Test invalid data (negative price)
    invalid_message = {
        "symbol": "BTCUSDT",
        "price": "-100.00",
        "timestamp": datetime.utcnow().isoformat()
    }

    is_valid, error = await validator.validate(invalid_message)
    assert is_valid is False
    assert error is not None


@pytest.mark.asyncio
async def test_complete_data_flow():
    """WHY: Must verify end-to-end data acquisition flow."""
    from services.websocket_manager import get_websocket_manager
    from services.data_pipeline import get_pipeline
    from services.multi_source_manager import get_multi_source_manager

    # Initialize components
    ws_manager = get_websocket_manager()
    pipeline = get_pipeline()
    source_manager = get_multi_source_manager()

    await pipeline.start()

    # Simulate ticker data from WebSocket
    test_ticker = {
        "type": "ticker",
        "symbol": "BTCUSDT",
        "price": "50000.00",
        "timestamp": datetime.utcnow().isoformat(),
        "exchange": "binance"
    }

    # Process through pipeline
    result = await pipeline.process_message(test_ticker)

    # Verify flow
    assert result["success"] is True

    # Get health status
    health = source_manager.get_health_status()
    assert "binance" in health
    assert "coingecko" in health

    await pipeline.stop()


def test_database_models_exist():
    """WHY: Must verify new database models are defined."""
    from database.models.market import (
        OrderBookModel,
        TradeModel,
        FundingRateModel
    )

    assert OrderBookModel is not None
    assert TradeModel is not None
    assert FundingRateModel is not None


def test_model_fields():
    """WHY: Must verify models have required fields."""
    from database.models.market import OrderBookModel, TradeModel, FundingRateModel

    # Check OrderBookModel
    assert hasattr(OrderBookModel, '__tablename__')
    assert OrderBookModel.__tablename__ == "order_books"

    # Check TradeModel
    assert hasattr(TradeModel, '__tablename__')
    assert TradeModel.__tablename__ == "trades"

    # Check FundingRateModel
    assert hasattr(FundingRateModel, '__tablename__')
    assert FundingRateModel.__tablename__ == "funding_rates"


@pytest.mark.asyncio
async def test_message_buffer_operations():
    """WHY: Must verify message buffer works correctly."""
    from services.data_pipeline import MessageBuffer

    buffer = MessageBuffer(max_size=100)

    # Push messages
    for i in range(10):
        await buffer.push({"test": i})

    # Check size
    size = await buffer.size()
    assert size == 10

    # Pop batch
    batch = await buffer.pop_batch(5)
    assert len(batch) == 5

    # Check new size
    size = await buffer.size()
    assert size == 5

    # Clear buffer
    await buffer.clear()
    size = await buffer.size()
    assert size == 0
