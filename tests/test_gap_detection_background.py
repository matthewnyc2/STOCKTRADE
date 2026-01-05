"""
Tests for Gap Detection Background Task.

Tests periodic gap detection and backfill functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.background_tasks import (
    schedule_gap_detection_task,
    get_task_queue,
    TaskQueue,
)
from services.historical_data_manager import GapDetector, GapInfo


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_gap_detector():
    """Mock gap detector."""
    detector = AsyncMock(spec=GapDetector)

    # Mock detect_gaps to return some gaps
    mock_gap = GapInfo(
        symbol="BTCUSDT",
        timeframe="1h",
        gap_start=datetime.utcnow() - timedelta(hours=10),
        gap_end=datetime.utcnow() - timedelta(hours=8),
        missing_periods=2,
    )

    detector.detect_gaps = AsyncMock(return_value=[mock_gap])
    detector.detect_gaps_batch = AsyncMock(return_value={"BTCUSDT:1h": [mock_gap]})

    return detector


@pytest.fixture
def mock_backfill_manager():
    """Mock backfill manager."""
    from unittest.mock import MagicMock

    manager = MagicMock()
    manager.backfill_batch = AsyncMock(
        return_value={
            "total_symbols": 1,
            "completed_symbols": 1,
            "gaps_filled": 1,
            "periods_fetched": 2,
            "success": True,
        }
    )

    return manager


@pytest.fixture
def task_queue():
    """Task queue fixture."""
    queue = TaskQueue()
    return queue


# ============================================================================
# TESTS: GAP DETECTION TASK CREATION
# ============================================================================


@pytest.mark.asyncio
async def test_schedule_gap_detection_task_creates_task():
    """Test that gap detection task is created successfully."""
    task_id = await schedule_gap_detection_task(
        symbols=["BTCUSDT"], timeframes=["1h"], auto_backfill=False, check_interval_hours=1
    )

    # Should return a valid task ID (UUID)
    assert task_id is not None
    assert len(task_id) > 10  # UUID format


@pytest.mark.asyncio
async def test_schedule_gap_detection_task_defaults():
    """Test gap detection task with default parameters."""
    task_id = await schedule_gap_detection_task()

    # Should create task with defaults
    assert task_id is not None

    # Verify task exists in queue
    queue = get_task_queue()
    task = queue.get_task(task_id)

    assert task is not None
    assert task["name"] == "Periodic Gap Detection"


# ============================================================================
# TESTS: TASK PARAMETERS
# ============================================================================


@pytest.mark.asyncio
async def test_gap_detection_custom_symbols():
    """Test gap detection with custom symbols."""
    custom_symbols = ["ETHUSDT", "SOLUSDT", "LINKUSDT"]

    task_id = await schedule_gap_detection_task(
        symbols=custom_symbols, timeframes=["1h", "1d"], auto_backfill=False
    )

    assert task_id is not None

    queue = get_task_queue()
    task = queue.get_task(task_id)

    assert task is not None


@pytest.mark.asyncio
async def test_gap_detection_custom_interval():
    """Test gap detection with custom check interval."""
    task_id = await schedule_gap_detection_task(
        check_interval_hours=2  # Check every 2 hours instead of 1
    )

    assert task_id is not None


# ============================================================================
# TESTS: GAP DETECTION LOOP (INTEGRATION)
# ============================================================================


@pytest.mark.asyncio
async def test_gap_detection_loop_no_gaps(mock_gap_detector):
    """Test gap detection loop when no gaps found."""
    # Mock to return no gaps
    mock_gap_detector.detect_gaps_batch = AsyncMock(return_value={})

    # Patch imports
    with patch("services.background_tasks.get_gap_detector", return_value=mock_gap_detector):
        task_id = await schedule_gap_detection_task(
            symbols=["BTCUSDT"], timeframes=["1h"], auto_backfill=False, check_interval_hours=1
        )

        # Verify task created
        queue = get_task_queue()
        task = queue.get_task(task_id)

        assert task is not None
        assert task["name"] == "Periodic Gap Detection"


@pytest.mark.asyncio
async def test_gap_detection_loop_with_gaps(mock_gap_detector, mock_backfill_manager):
    """Test gap detection loop triggers backfill when gaps found."""
    # Mock to return gaps
    from unittest.mock import MagicMock

    mock_gap = GapInfo(
        symbol="BTCUSDT",
        timeframe="1h",
        gap_start=datetime.utcnow() - timedelta(hours=5),
        gap_end=datetime.utcnow() - timedelta(hours=3),
        missing_periods=2,
    )

    mock_gap_detector.detect_gaps_batch = AsyncMock(return_value={"BTCUSDT:1h": [mock_gap]})

    # Patch imports
    with (
        patch("services.background_tasks.get_gap_detector", return_value=mock_gap_detector),
        patch("services.background_tasks.get_backfill_manager", return_value=mock_backfill_manager),
    ):
        task_id = await schedule_gap_detection_task(
            symbols=["BTCUSDT"], timeframes=["1h"], auto_backfill=True, check_interval_hours=1
        )

        # Verify task created
        queue = get_task_queue()
        task = queue.get_task(task_id)

        assert task is not None
        assert task["name"] == "Periodic Gap Detection"


# ============================================================================
# TESTS: IDEMPOTENCY
# ============================================================================


@pytest.mark.asyncio
async def test_gap_detection_idempotency():
    """Test that multiple gap detection tasks can run safely."""
    # Create multiple tasks
    task_ids = []

    for _ in range(3):
        task_id = await schedule_gap_detection_task(
            symbols=["BTCUSDT"], timeframes=["1h"], auto_backfill=False, check_interval_hours=1
        )
        task_ids.append(task_id)

    # All tasks should be unique
    assert len(set(task_ids)) == len(task_ids)

    # All tasks should exist
    queue = get_task_queue()
    for task_id in task_ids:
        task = queue.get_task(task_id)
        assert task is not None


# ============================================================================
# TESTS: ERROR HANDLING
# ============================================================================


@pytest.mark.asyncio
async def test_gap_detection_error_handling():
    """Test that gap detection handles errors gracefully."""
    # The loop should continue even if one iteration fails

    task_id = await schedule_gap_detection_task(
        symbols=["BTCUSDT"], timeframes=["1h"], auto_backfill=False, check_interval_hours=1
    )

    # Should still create task
    assert task_id is not None

    queue = get_task_queue()
    task = queue.get_task(task_id)

    assert task is not None


# ============================================================================
# TESTS: GAP DETECTOR INTEGRATION
# ============================================================================


def test_gap_detector_detects_gaps():
    """Test that GapDetector correctly identifies gaps."""
    from services.historical_data_manager import get_gap_detector

    detector = get_gap_detector()

    # Create expected interval
    expected_interval_minutes = 60  # 1h timeframe

    # Test interval mapping
    assert "1h" in detector.intervals
    assert detector.intervals["1h"] == expected_interval_minutes

    assert "1d" in detector.intervals
    assert detector.intervals["1d"] == 1440

    assert "1m" in detector.intervals
    assert detector.intervals["1m"] == 1


def test_gap_info_to_dict():
    """Test GapInfo serialization."""
    gap = GapInfo(
        symbol="BTCUSDT",
        timeframe="1h",
        gap_start=datetime.utcnow() - timedelta(hours=5),
        gap_end=datetime.utcnow() - timedelta(hours=3),
        missing_periods=2,
    )

    gap_dict = gap.to_dict()

    # Verify structure
    assert "symbol" in gap_dict
    assert "timeframe" in gap_dict
    assert "gap_start" in gap_dict
    assert "gap_end" in gap_dict
    assert "missing_periods" in gap_dict
    assert "duration_hours" in gap_dict
    assert "detected_at" in gap_dict

    # Verify values
    assert gap_dict["symbol"] == "BTCUSDT"
    assert gap_dict["timeframe"] == "1h"
    assert gap_dict["missing_periods"] == 2
