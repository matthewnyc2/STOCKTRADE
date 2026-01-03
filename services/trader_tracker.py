"""
Trader Tracker Service.

Provides the business logic for tracking traders, analyzing their behavior,
and calculating performance metrics.
"""
import logging
from datetime import datetime
from collections import defaultdict

from database.connection import get_db_session
from database.repositories import TraderRepository
from models.trader import TraderProfile, TraderRiskLevel, TradingStyle, TraderAction

logger = logging.getLogger(__name__)

def analyze_trader_profile(trader_id: str) -> TraderProfile:
    """
    Analyzes a trader's activity to create a trading profile.

    This function assesses a trader's risk level, preferred assets, and trading style
    based on their recent trading activity.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        activities = repo.get_activity(trader_id, limit=100)

        if not activities:
            raise ValueError("No activity found for this trader, cannot generate profile.")

        # Analyze preferred assets
        asset_counts = defaultdict(int)
        for activity in activities:
            asset_counts[activity.symbol] += 1
        preferred_assets = sorted(asset_counts, key=asset_counts.get, reverse=True)[:5]

        # Analyze risk level
        leverages = [a.leverage for a in activities if a.leverage is not None and a.leverage > 1]
        avg_leverage = sum(leverages) / len(leverages) if leverages else 1.0
        risk_level = TraderRiskLevel.LOW
        if avg_leverage > 10:
            risk_level = TraderRiskLevel.HIGH
        elif avg_leverage > 3:
            risk_level = TraderRiskLevel.MEDIUM

        # Analyze trading style
        holding_periods = []
        positions = {}
        for activity in sorted(activities, key=lambda a: a.timestamp):
            if activity.action in [TraderAction.BOUGHT, TraderAction.OPENED_POSITION]:
                positions[activity.symbol] = activity.timestamp
            elif activity.action in [TraderAction.SOLD, TraderAction.CLOSED_POSITION]:
                if activity.symbol in positions:
                    holding_periods.append((activity.timestamp - positions.pop(activity.symbol)).total_seconds())
        
        avg_holding_period = sum(holding_periods) / len(holding_periods) if holding_periods else 0

        trading_style = TradingStyle.POSITION_TRADER
        if avg_holding_period < 3600:  # Less than an hour
            trading_style = TradingStyle.SCALPER
        elif avg_holding_period < 86400:  # Less than a day
            trading_style = TradingStyle.DAY_TRADER
        elif avg_holding_period < 604800:  # Less than a week
            trading_style = TradingStyle.SWING_TRADER

        trader = repo.get(trader_id)
        profile = {
            "trader_id": trader_id,
            "risk_level": risk_level.value,
            "preferred_assets": preferred_assets,
            "trading_style": trading_style.value,
            "avg_holding_period_seconds": int(avg_holding_period),
            "preferred_exchange": trader.exchange if trader else "Unknown",
        }

        # Persist the profile to the database
        repo.update_profile(trader_id, profile)

        return TraderProfile(**profile)

def calculate_trader_performance(trader_id: str) -> dict:
    """
    Calculates key performance indicators (KPIs) for a trader.

    This includes win rate, average profit/loss, and total volume traded.
    """
    with get_db_session() as session:
        repo = TraderRepository(session)
        activities = repo.get_activity(trader_id, limit=200)

        if not activities:
            return {"error": "No trading activity to analyze."}

        wins = 0
        losses = 0
        total_pnl = 0
        total_volume = 0

        for activity in activities:
            total_volume += activity.amount_usd
            if activity.pnl is not None:
                total_pnl += activity.pnl
                if activity.pnl > 0:
                    wins += 1
                elif activity.pnl < 0:
                    losses += 1
        
        total_trades = wins + losses
        win_rate = (wins / total_trades) if total_trades > 0 else 0
        avg_pnl_per_trade = (total_pnl / total_trades) if total_trades > 0 else 0

        return {
            "trader_id": trader_id,
            "total_trades": total_trades,
            "win_rate": f"{win_rate:.2%}",
            "total_pnl_usd": f"{total_pnl:.2f}",
            "avg_pnl_per_trade_usd": f"{avg_pnl_per_trade:.2f}",
            "total_volume_usd": f"{total_volume:.2f}",
        }
