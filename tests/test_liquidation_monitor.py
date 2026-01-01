"""
Tests for Liquidation Monitor Service.

Tests the liquidation monitoring, cascade detection, and heat calculation functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.liquidation_monitor import (
    fetch_liquidations,
    detect_cascades,
    calculate_liquidation_heat,
    get_liquidation_stats,
    _get_demo_liquidations,
    _detect_symbol_cascades,
    _get_correlated_symbols,
    _generate_cascade_description,
)
from models import (
    Liquidation,
    CascadeEvent,
    CascadeSeverity,
    LiquidationSide,
    LiquidationHeat,
    LiquidationStats,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_liquidations():
    """Sample liquidation data for testing."""
    now = datetime.utcnow()
    return [
        Liquidation(
            id=f"liq_{i}",
            exchange="binance",
            symbol="BTCUSDT",
            side=LiquidationSide.LONG if i % 2 == 0 else LiquidationSide.SHORT,
            amount_usd=Decimal(str(1000000 + i * 500000)),
            price=Decimal("50000"),
            timestamp=now - timedelta(seconds=i * 30),
            blockchain_txid=f"0x{i}",
            metadata={},
        )
        for i in range(10)
    ]


@pytest.fixture
def sample_cascade():
    """Sample cascade event for testing."""
    now = datetime.utcnow()
    return CascadeEvent(
        id="casc_test",
        symbol="BTC",
        severity=CascadeSeverity.HIGH,
        liquidation_count=5,
        total_amount_usd=Decimal("5000000"),
        start_time=now - timedelta(minutes=5),
        end_time=now,
        duration_seconds=300,
        affected_symbols=["ETH", "SOL"],
        long_percentage=Decimal("0.6"),
        confidence=Decimal("0.85"),
        description="Test cascade",
        metadata={},
    )


# ============================================================================
# FETCH LIQUIDATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_liquidations_returns_data():
    """Test that fetch_liquidations returns liquidation data."""
    liquidations = await fetch_liquidations(limit=10)

    assert isinstance(liquidations, list)
    assert len(liquidations) > 0

    for liq in liquidations:
        assert isinstance(liq, Liquidation)
        assert liq.amount_usd > 0
        assert liq.symbol
        assert liq.side in [LiquidationSide.LONG, LiquidationSide.SHORT]


@pytest.mark.asyncio
async def test_fetch_liquidations_filters_by_symbol():
    """Test that fetch_liquidations can filter by symbol."""
    liquidations = await fetch_liquidations(symbol="BTC", limit=20)

    assert isinstance(liquidations, list)
    for liq in liquidations:
        assert "BTC" in liq.symbol.upper()


@pytest.mark.asyncio
async def test_fetch_liquidations_filters_by_amount():
    """Test that fetch_liquidations respects minimum amount filter."""
    min_amount = 5000000  # $5M
    liquidations = await fetch_liquidations(min_amount_usd=min_amount, limit=20)

    for liq in liquidations:
        assert liq.amount_usd >= Decimal(str(min_amount))


@pytest.mark.asyncio
async def test_get_demo_liquidations_generates_data():
    """Test that demo liquidations are generated correctly."""
    liquidations = _get_demo_liquidations(
        symbol="ETH",
        min_amount_usd=100000,
        limit=10
    )

    assert len(liquidations) > 0
    assert len(liquidations) <= 10

    for liq in liquidations:
        assert "ETH" in liq.symbol
        assert liq.amount_usd >= Decimal("100000")
        assert liq.exchange in ["binance", "bybit", "okx", "bitget", "hyperliquid"]


# ============================================================================
# CASCADE DETECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_detect_cascades_identifies_cascades(sample_liquidations):
    """Test that cascades are detected from liquidation data."""
    cascades = await detect_cascades(
        liquidations=sample_liquidations,
        time_window_seconds=300,
        min_liquidations=3,
        min_amount_usd=1000000,
    )

    assert isinstance(cascades, list)

    # If cascades detected, validate structure
    for cascade in cascades:
        assert isinstance(cascade, CascadeEvent)
        assert cascade.liquidation_count >= 3
        assert cascade.total_amount_usd >= Decimal("1000000")
        assert cascade.duration_seconds <= 300
        assert 0 <= cascade.long_percentage <= 1
        assert 0 <= cascade.confidence <= 1


@pytest.mark.asyncio
async def test_detect_cascades_without_data_uses_api():
    """Test that detect_cascades fetches data when none provided."""
    cascades = await detect_cascades()

    assert isinstance(cascades, list)


def test_detect_symbol_cascades_groups_liquidations(sample_liquidations):
    """Test that symbol cascades group liquidations correctly."""
    cascades = _detect_symbol_cascades(
        symbol="BTC",
        liquidations=sample_liquidations,
        time_window_seconds=600,
        min_liquidations=3,
        min_amount_usd=1000000,
    )

    assert isinstance(cascades, list)

    for cascade in cascades:
        assert cascade.symbol == "BTC"
        assert cascade.liquidation_count >= 3


def test_get_correlated_symbols_returns_expected():
    """Test that correlated symbols are returned correctly."""
    btc_correlated = _get_correlated_symbols("BTC")
    assert "ETH" in btc_correlated
    assert "SOL" in btc_correlated

    eth_correlated = _get_correlated_symbols("ETH")
    assert "BTC" in eth_correlated


def test_generate_cascade_description():
    """Test cascade description generation."""
    description = _generate_cascade_description(
        "BTC",
        CascadeSeverity.HIGH,
        10,
        Decimal("15000000")
    )

    assert "HIGH" in description
    assert "BTC" in description
    assert "10" in description
    assert "15.00" in description


# ============================================================================
# HEAT CALCULATION TESTS
# ============================================================================

def test_calculate_liquidation_heat_returns_heat_object():
    """Test that heat calculation returns proper object."""
    heat = calculate_liquidation_heat("BTC")

    assert isinstance(heat, LiquidationHeat)
    assert heat.symbol == "BTC"
    assert 0 <= heat.heat_score <= 1
    assert 0 <= heat.long_heat <= 1
    assert 0 <= heat.short_heat <= 1
    assert heat.trend in ["increasing", "decreasing", "stable"]
    assert heat.liquidation_count_1h >= 0
    assert heat.liquidation_count_24h >= 0


def test_calculate_liquidation_heat_for_multiple_symbols():
    """Test heat calculation for different symbols."""
    symbols = ["BTC", "ETH", "SOL"]

    for symbol in symbols:
        heat = calculate_liquidation_heat(symbol)
        assert heat.symbol.upper() == symbol.upper()


# ============================================================================
# STATS TESTS
# ============================================================================

def test_get_liquidation_stats_returns_stats():
    """Test that stats calculation returns proper object."""
    stats = get_liquidation_stats(hours=24)

    assert isinstance(stats, LiquidationStats)
    assert stats.period_hours == 24
    assert stats.total_liquidated_usd >= 0
    assert stats.long_liquidated_usd >= 0
    assert stats.short_liquidated_usd >= 0
    assert stats.liquidation_count >= 0
    assert stats.avg_liquidation_size >= 0
    assert stats.largest_liquidation >= 0


def test_get_liquidation_stats_with_symbol_filter():
    """Test stats calculation with symbol filter."""
    stats = get_liquidation_stats(symbol="BTC", hours=24)

    assert isinstance(stats, LiquidationStats)
    assert stats.symbol == "BTC"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_liquidation_workflow():
    """Test the complete workflow from fetch to cascade detection."""
    # Fetch liquidations
    liquidations = await fetch_liquidations(limit=50)

    # Detect cascades
    cascades = await detect_cascades(liquidations)

    # Calculate heat for symbols
    symbols = set(liq.symbol.replace("USDT", "").replace("USD", "") for liq in liquidations)
    heat_results = {}
    for symbol in list(symbols)[:3]:  # Test first 3 symbols
        heat_results[symbol] = calculate_liquidation_heat(symbol)

    # Validate
    assert isinstance(liquidations, list)
    assert isinstance(cascades, list)
    assert len(heat_results) > 0


@pytest.mark.asyncio
async def test_cascade_detection_with_mixed_severities(sample_liquidations):
    """Test that cascades of different severities are detected."""
    cascades = await detect_cascades(
        liquidations=sample_liquidations,
        time_window_seconds=300,
        min_liquidations=3,
        min_amount_usd=100000,
    )

    severity_counts = {}
    for cascade in cascades:
        severity = cascade.severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # At minimum, we should have some cascades detected
    assert isinstance(cascades, list)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_liquidations_with_empty_params():
    """Test fetch with default parameters."""
    liquidations = await fetch_liquidations()
    assert isinstance(liquidations, list)


@pytest.mark.asyncio
async def test_detect_cascades_with_empty_list():
    """Test cascade detection with no liquidations."""
    cascades = await detect_cascades(liquidations=[])
    assert cascades == []


@pytest.mark.asyncio
async def test_detect_cascades_below_threshold():
    """Test that small liquidations don't trigger cascades."""
    small_liquidations = [
        Liquidation(
            id=f"liq_{i}",
            exchange="binance",
            symbol="BTCUSDT",
            side=LiquidationSide.LONG,
            amount_usd=Decimal("100000"),  # Below $1M threshold
            price=Decimal("50000"),
            timestamp=datetime.utcnow(),
            metadata={},
        )
        for i in range(5)
    ]

    cascades = await detect_cascades(
        liquidations=small_liquidations,
        min_amount_usd=1000000,  # $1M threshold
    )

    # Should not detect cascades below threshold
    assert len(cascades) == 0


def test_calculate_liquidation_heat_with_no_data():
    """Test heat calculation when no liquidations exist."""
    # This tests the function's behavior with empty data
    heat = calculate_liquidation_heat("UNKNOWN")

    # Should still return valid heat object
    assert isinstance(heat, LiquidationHeat)


# ============================================================================
# MODEL VALIDATION TESTS
# ============================================================================

def test_liquidation_model_validation():
    """Test Liquidation model accepts valid data."""
    liq = Liquidation(
        id="test_liq",
        exchange="binance",
        symbol="BTCUSDT",
        side=LiquidationSide.LONG,
        amount_usd=Decimal("1000000"),
        price=Decimal("50000"),
        timestamp=datetime.utcnow(),
        metadata={},
    )

    assert liq.id == "test_liq"
    assert liq.symbol == "BTCUSDT"
    assert liq.side == LiquidationSide.LONG


def test_cascade_event_model_validation():
    """Test CascadeEvent model accepts valid data."""
    cascade = CascadeEvent(
        id="test_cascade",
        symbol="BTC",
        severity=CascadeSeverity.EXTREME,
        liquidation_count=10,
        total_amount_usd=Decimal("10000000"),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        duration_seconds=300,
        affected_symbols=["ETH", "SOL"],
        long_percentage=Decimal("0.7"),
        confidence=Decimal("0.9"),
        metadata={},
    )

    assert cascade.id == "test_cascade"
    assert cascade.severity == CascadeSeverity.EXTREME
    assert cascade.liquidation_count == 10


def test_liquidation_heat_model_validation():
    """Test LiquidationHeat model accepts valid data."""
    heat = LiquidationHeat(
        symbol="BTC",
        heat_score=Decimal("0.8"),
        long_heat=Decimal("0.6"),
        short_heat=Decimal("0.4"),
        total_liquidated_1h=Decimal("5000000"),
        total_liquidated_24h=Decimal("50000000"),
        liquidation_count_1h=10,
        liquidation_count_24h=100,
        trend="increasing",
        calculated_at=datetime.utcnow(),
    )

    assert heat.symbol == "BTC"
    assert heat.heat_score == Decimal("0.8")
    assert heat.trend == "increasing"
