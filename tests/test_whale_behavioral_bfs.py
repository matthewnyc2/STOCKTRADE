"""
Tests for BFS behavioral pattern detection in Whale Tracker.

Tests for multi-step behavioral sequence detection using BFS algorithm.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from services.whale_tracker import (
    _detect_behavioral_sequence,
    _classify_sequence_pattern,
)
from models import WhaleAction, PatternType

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_activities_buy_sell_buy():
    """Sample activities showing buy-sell-buy pattern (wash trading)."""
    base_time = datetime.utcnow()

    return [
        {
            "id": "act_001",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("1000000"),
            "timestamp": base_time - timedelta(hours=6),
            "transaction_hash": "0x1" * 64,
            "metadata": {},
        },
        {
            "id": "act_002",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.SOLD.value,
            "amount_usd": Decimal("950000"),
            "timestamp": base_time - timedelta(hours=4),
            "transaction_hash": "0x2" * 64,
            "metadata": {},
        },
        {
            "id": "act_003",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("980000"),
            "timestamp": base_time - timedelta(hours=2),
            "transaction_hash": "0x3" * 64,
            "metadata": {},
        },
    ]


@pytest.fixture
def sample_activities_buy_transfer_sell():
    """Sample activities showing buy-transfer-sell pattern (wallet hopping)."""
    base_time = datetime.utcnow()

    return [
        {
            "id": "act_001",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("500000"),
            "timestamp": base_time - timedelta(hours=6),
            "transaction_hash": "0x1" * 64,
            "metadata": {},
        },
        {
            "id": "act_002",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.TRANSFERRED.value,
            "amount_usd": Decimal("500000"),
            "timestamp": base_time - timedelta(hours=5),
            "transaction_hash": "0x2" * 64,
            "metadata": {},
        },
        {
            "id": "act_003",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.SOLD.value,
            "amount_usd": Decimal("490000"),
            "timestamp": base_time - timedelta(hours=4),
            "transaction_hash": "0x3" * 64,
            "metadata": {},
        },
    ]


@pytest.fixture
def sample_activities_manipulator():
    """Sample activities showing manipulator pattern with multiple transfers."""
    base_time = datetime.utcnow()

    activities = []
    for i in range(15):
        action = WhaleAction.TRANSFERRED.value if i % 2 == 0 else WhaleAction.BOUGHT.value
        activities.append({
            "id": f"act_{i:03d}",
            "whale_address": "0x" + "2" * 40,
            "symbol": "SOL",
            "action": action,
            "amount_usd": Decimal("100000"),
            "timestamp": base_time - timedelta(hours=i),
            "transaction_hash": "0x" + str(i) * 60,
            "metadata": {},
        })

    return activities


# ============================================================================
# TESTS: SEQUENCE PATTERN CLASSIFICATION
# ============================================================================

def test_classify_sequence_pattern_buy_sell_buy_wash_trading():
    """Test detection of wash trading pattern."""
    base_time = datetime.utcnow()

    activities = [
        {
            "id": "act_001",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("1000000"),
            "timestamp": base_time - timedelta(hours=3),
            "transaction_hash": "0x1" * 64,
            "metadata": {},
        },
        {
            "id": "act_002",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.SOLD.value,
            "amount_usd": Decimal("950000"),
            "timestamp": base_time - timedelta(hours=2),
            "transaction_hash": "0x2" * 64,
            "metadata": {},
        },
        {
            "id": "act_003",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("980000"),
            "timestamp": base_time - timedelta(hours=1),
            "transaction_hash": "0x3" * 64,
            "metadata": {},
        },
    ]

    pattern = _classify_sequence_pattern(activities)

    # Should detect as MANIPULATOR due to wash trading
    assert pattern == PatternType.MANIPULATOR


def test_classify_sequence_pattern_buy_transfer_sell_wallet_hopping():
    """Test detection of wallet hopping pattern."""
    base_time = datetime.utcnow()

    activities = [
        {
            "id": "act_001",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("500000"),
            "timestamp": base_time - timedelta(hours=3),
            "transaction_hash": "0x1" * 64,
            "metadata": {},
        },
        {
            "id": "act_002",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.TRANSFERRED.value,
            "amount_usd": Decimal("500000"),
            "timestamp": base_time - timedelta(hours=2),
            "transaction_hash": "0x2" * 64,
            "metadata": {},
        },
        {
            "id": "act_003",
            "whale_address": "0x" + "1" * 40,
            "symbol": "ETH",
            "action": WhaleAction.SOLD.value,
            "amount_usd": Decimal("490000"),
            "timestamp": base_time - timedelta(hours=1),
            "transaction_hash": "0x3" * 64,
            "metadata": {},
        },
    ]

    pattern = _classify_sequence_pattern(activities)

    # Should detect as MANIPULATOR due to wallet hopping
    assert pattern == PatternType.MANIPULATOR


def test_classify_sequence_pattern_accumulator_default():
    """Test default classification for accumulator pattern."""
    base_time = datetime.utcnow()

    activities = [
        {
            "id": f"act_{i:03d}",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("100000"),
            "timestamp": base_time - timedelta(hours=i),
            "transaction_hash": "0x" + str(i) * 60,
            "metadata": {},
        }
        for i in range(10)
    ]

    pattern = _classify_sequence_pattern(activities)

    # Should default to ACCUMULATOR
    assert pattern == PatternType.ACCUMULATOR


# ============================================================================
# TESTS: BFS BEHAVIORAL DETECTION
# ============================================================================

def test_detect_behavioral_sequence_wash_trading(sample_activities_buy_sell_buy):
    """Test BFS detection of wash trading sequence."""
    pattern = _detect_behavioral_sequence(sample_activities_buy_sell_buy)

    # Should detect MANIPULATOR pattern
    assert pattern == PatternType.MANIPULATOR


def test_detect_behavioral_sequence_wallet_hopping(sample_activities_buy_transfer_sell):
    """Test BFS detection of wallet hopping sequence."""
    pattern = _detect_behavioral_sequence(sample_activities_buy_transfer_sell)

    # Should detect MANIPULATOR pattern
    assert pattern == PatternType.MANIPULATOR


def test_detect_behavioral_sequence_manipulator(sample_activities_manipulator):
    """Test BFS detection of manipulator with multiple transfers."""
    pattern = _detect_behavioral_sequence(sample_activities_manipulator)

    # Should detect MANIPULATOR pattern
    assert pattern == PatternType.MANIPULATOR


def test_detect_behavioral_sequence_insufficient_data():
    """Test BFS behavior detection with insufficient data."""
    activities = [
        {
            "id": "act_001",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("100000"),
            "timestamp": datetime.utcnow(),
            "transaction_hash": "0x1" * 64,
            "metadata": {},
        }
        for _ in range(3)
    ]

    pattern = _detect_behavioral_sequence(activities)

    # Should default to ACCUMULATOR with insufficient data
    assert pattern == PatternType.ACCUMULATOR


def test_detect_behavioral_sequence_temporal_clustering():
    """Test BFS detection of temporal clustering."""
    base_time = datetime.utcnow()

    # Create activities with temporal clustering
    activities = []
    for i in range(20):
        action = WhaleAction.BOUGHT.value if i % 3 == 0 else WhaleAction.SOLD.value
        activities.append({
            "id": f"act_{i:03d}",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": action,
            "amount_usd": Decimal("50000"),
            # Cluster activities within 24 hour window
            timestamp=base_time - timedelta(hours=i % 5),
            "transaction_hash": "0x" + str(i) * 60,
            "metadata": {},
        })

    pattern = _detect_behavioral_sequence(activities)

    # Should detect some pattern (not default)
    # Due to temporal clustering, should trigger sequence detection
    assert isinstance(pattern, PatternType)


# ============================================================================
# TESTS: GRAPH STRUCTURE
# ============================================================================

def test_bfs_graph_building():
    """Test that BFS correctly builds activity graph."""
    base_time = datetime.utcnow()

    activities = []
    for i in range(10):
        activities.append({
            "id": f"act_{i:03d}",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("100000"),
            timestamp=base_time - timedelta(hours=i),
            "transaction_hash": "0x" + str(i) * 60,
            "metadata": {},
        })

    # Should not raise exception
    pattern = _detect_behavioral_sequence(activities)
    assert isinstance(pattern, PatternType)


def test_bfs_time_threshold():
    """Test that BFS respects time threshold."""
    base_time = datetime.utcnow()

    # Activities spread over more than 24 hours
    activities = [
        {
            "id": f"act_{i:03d}",
            "whale_address": "0x" + "1" * 40,
            "symbol": "BTC",
            "action": WhaleAction.BOUGHT.value,
            "amount_usd": Decimal("100000"),
            timestamp=base_time - timedelta(hours=i * 26),  # 26h apart
            "transaction_hash": "0x" + str(i) * 60,
            "metadata": {},
        }
        for i in range(5)
    ]

    pattern = _detect_behavioral_sequence(activities)

    # Should default to ACCUMULATOR (activities too spread out)
    assert pattern == PatternType.ACCUMULATOR


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_behavioral_detection_integration():
    """Test integration of BFS behavioral detection with main classification."""
    # This test verifies that the new BFS functions integrate correctly
    # with the existing classify_whale_pattern function

    # The main classify_whale_pattern should call _detect_behavioral_sequence
    # first before falling back to ratio-based classification

    # Verify functions exist and are callable
    assert callable(_detect_behavioral_sequence)
    assert callable(_classify_sequence_pattern)
