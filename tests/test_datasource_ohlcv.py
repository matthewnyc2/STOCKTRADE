"""
Tests for Data Source OHLCV implementations.

Tests CoinGecko and Kraken OHLCV functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from services.multi_source_manager import (
    CoinGeckoDataSource,
    KrakenDataSource,
    BinanceDataSource,
    DataSourceConfig,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def coingecko_config():
    """CoinGecko data source configuration."""
    return DataSourceConfig(
        name="coingecko", priority=2, supports_rest=True, supports_historical=True, timeout=30.0
    )


@pytest.fixture
def kraken_config():
    """Kraken data source configuration."""
    return DataSourceConfig(
        name="kraken", priority=3, supports_rest=True, supports_historical=True, timeout=30.0
    )


@pytest.fixture
def binance_config():
    """Binance data source configuration."""
    return DataSourceConfig(
        name="binance",
        priority=1,
        supports_websocket=True,
        supports_rest=True,
        supports_historical=True,
        timeout=30.0,
    )


# ============================================================================
# TESTS: COINGECKO OHLCV
# ============================================================================


@pytest.mark.asyncio
async def test_coingecko_get_ohlcv_basic(coingecko_config):
    """Test basic CoinGecko OHLCV fetching."""
    source = CoinGeckoDataSource(coingecko_config)

    candles = await source.get_ohlcv("bitcoin", interval="1d", limit=30)

    # Should return data
    assert isinstance(candles, list)
    assert len(candles) > 0

    # Check first candle structure
    first_candle = candles[0]
    assert "timestamp" in first_candle
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "exchange" in first_candle
    assert first_candle["exchange"] == "coingecko"


@pytest.mark.asyncio
async def test_coingecko_get_ohlcv_with_time_range(coingecko_config):
    """Test CoinGecko OHLCV with start/end parameters."""
    source = CoinGeckoDataSource(coingecko_config)

    end = datetime.utcnow()
    start = end - timedelta(days=7)

    candles = await source.get_ohlcv("bitcoin", interval="1d", start=start, end=end)

    # Should return data within range
    assert isinstance(candles, list)

    # Verify all candles are within range
    for candle in candles:
        assert candle["timestamp"] >= start
        assert candle["timestamp"] <= end


@pytest.mark.asyncio
async def test_coingecko_get_ohlcv_interval_mapping(coingecko_config):
    """Test that CoinGecko maps intervals correctly."""
    source = CoinGeckoDataSource(coingecko_config)

    # Test different intervals
    for interval in ["1h", "4h", "1d"]:
        candles = await source.get_ohlcv("bitcoin", interval=interval, limit=10)
        assert isinstance(candles, list)
        # Should not crash on any supported interval


@pytest.mark.asyncio
async def test_coingecko_get_ohlcv_error_handling(coingecko_config):
    """Test CoinGecko error handling for invalid symbol."""
    source = CoinGeckoDataSource(coingecko_config)

    # Test with invalid symbol
    candles = await source.get_ohlcv("invalid_symbol_12345", interval="1h")

    # Should return empty list on error (graceful degradation)
    assert isinstance(candles, list)


# ============================================================================
# TESTS: KRAKEN OHLCV
# ============================================================================


@pytest.mark.asyncio
async def test_kraken_get_ohlcv_basic(kraken_config):
    """Test basic Kraken OHLCV fetching."""
    source = KrakenDataSource(kraken_config)

    candles = await source.get_ohlcv("XBTUSDT", interval="1h", limit=50)

    # Should return data
    assert isinstance(candles, list)
    assert len(candles) > 0

    # Check first candle structure
    first_candle = candles[0]
    assert "timestamp" in first_candle
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    assert "exchange" in first_candle
    assert first_candle["exchange"] == "kraken"


@pytest.mark.asyncio
async def test_kraken_get_ohlcv_with_since(kraken_config):
    """Test Kraken OHLCV with start parameter."""
    source = KrakenDataSource(kraken_config)

    start = datetime.utcnow() - timedelta(days=7)

    candles = await source.get_ohlcv("XBTUSDT", interval="1h", limit=50, start=start)

    # Should return data
    assert isinstance(candles, list)
    assert len(candles) > 0

    # Verify all candles are after start time
    for candle in candles:
        assert candle["timestamp"] >= start


@pytest.mark.asyncio
async def test_kraken_get_ohlcv_with_end(kraken_config):
    """Test Kraken OHLCV with end parameter."""
    source = KrakenDataSource(kraken_config)

    end = datetime.utcnow() - timedelta(days=1)

    candles = await source.get_ohlcv("XBTUSDT", interval="1h", limit=50, end=end)

    # Should return data
    assert isinstance(candles, list)

    # Verify all candles are before end time
    for candle in candles:
        assert candle["timestamp"] <= end


@pytest.mark.asyncio
async def test_kraken_get_ohlcv_interval_mapping(kraken_config):
    """Test that Kraken maps intervals correctly."""
    source = KrakenDataSource(kraken_config)

    # Test different intervals
    for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        candles = await source.get_ohlcv("XBTUSDT", interval=interval, limit=10)
        assert isinstance(candles, list)


@pytest.mark.asyncio
async def test_kraken_get_ohlcv_error_handling(kraken_config):
    """Test Kraken error handling for invalid symbol."""
    source = KrakenDataSource(kraken_config)

    # Test with invalid symbol
    candles = await source.get_ohlcv("INVALIDPAIR", interval="1h")

    # Should return empty list on error (graceful degradation)
    assert isinstance(candles, list)


# ============================================================================
# TESTS: BINANCE OHLCV TIME RANGE
# ============================================================================


@pytest.mark.asyncio
async def test_binance_get_ohlcv_with_start_end(binance_config):
    """Test Binance OHLCV with precise start/end time range."""
    source = BinanceDataSource(binance_config)

    end = datetime.utcnow() - timedelta(hours=1)
    start = end - timedelta(days=7)

    candles = await source.get_ohlcv("BTCUSDT", interval="1h", limit=100, start=start, end=end)

    # Should return data
    assert isinstance(candles, list)
    assert len(candles) > 0

    # Verify all candles are within time range
    for candle in candles:
        assert candle["timestamp"] >= start
        assert candle["timestamp"] <= end


@pytest.mark.asyncio
async def test_binance_get_ohlcv_backwards_in_time(binance_config):
    """Test Binance OHLCV returns data sorted by timestamp (newest first)."""
    source = BinanceDataSource(binance_config)

    candles = await source.get_ohlcv("BTCUSDT", interval="1h", limit=100)

    # Should be sorted reverse by timestamp (newest first)
    timestamps = [c["timestamp"] for c in candles]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_binance_get_ohlcv_respects_limit(binance_config):
    """Test Binance OHLCV respects limit parameter."""
    source = BinanceDataSource(binance_config)

    for limit in [10, 50, 100]:
        candles = await source.get_ohlcv("BTCUSDT", interval="1h", limit=limit)
        assert len(candles) <= limit


# ============================================================================
# TESTS: BACKFILL PRECISION
# ============================================================================


@pytest.mark.asyncio
async def test_all_sources_ohlcv_consistency(binance_config, coingecko_config, kraken_config):
    """Test that all data sources return consistent OHLCV format."""
    sources = [
        ("binance", BinanceDataSource(binance_config), "BTCUSDT"),
        ("coingecko", CoinGeckoDataSource(coingecko_config), "bitcoin"),
        ("kraken", KrakenDataSource(kraken_config), "XBTUSDT"),
    ]

    for name, source, symbol in sources:
        candles = await source.get_ohlcv(symbol, interval="1h", limit=10)

        # Verify all have same structure
        assert isinstance(candles, list)

        for candle in candles:
            assert "timestamp" in candle
            assert "open" in candle
            assert "high" in candle
            assert "low" in candle
            assert "close" in candle
            assert isinstance(candle["open"], Decimal)
            assert isinstance(candle["high"], Decimal)
            assert isinstance(candle["low"], Decimal)
            assert isinstance(candle["close"], Decimal)


# ============================================================================
# TESTS: RATE LIMITING
# ============================================================================


@pytest.mark.asyncio
async def test_coingecko_rate_limit_handling(coingecko_config):
    """Test that CoinGecko handles rate limits gracefully."""
    source = CoinGeckoDataSource(coingecko_config)

    # Make multiple rapid requests
    results = []
    for _ in range(5):
        candles = await source.get_ohlcv("bitcoin", interval="1h", limit=10)
        results.append(len(candles))

    # Should handle gracefully (return empty lists or data)
    # We're testing that it doesn't crash
    assert all(isinstance(r, int) for r in results)
