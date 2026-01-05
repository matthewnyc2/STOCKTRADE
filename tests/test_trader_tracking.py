"""
Trader Tracking System Tests
WHY: User requested trader performance tracking
"""
import pytest


def test_trader_model_exists():
    """WHY: Need trader data structure"""
    from models.trader import Trader
    assert Trader is not None


def test_track_trader_performance():
    """WHY: Must track trader wins/losses"""
    from services.trader_tracker import TraderTracker
    tracker = TraderTracker()
    performance = tracker.get_trader_performance("trader_123")
    assert "win_rate" in performance
    assert "total_trades" in performance


def test_get_top_performers():
    """WHY: User wants to see best traders"""
    from services.trader_tracker import TraderTracker
    tracker = TraderTracker()
    top = tracker.get_top_performers(limit=10)
    assert isinstance(top, list)
    assert len(top) <= 10
