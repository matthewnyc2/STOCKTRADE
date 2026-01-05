"""
Traders API endpoints.

Provides endpoints for tracking and ranking paper trading performance.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status

from database.connection import get_db_context
from database.repositories import StrategyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traders", tags=["traders"])


@router.get("/top-performers")
async def get_top_performers(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of traders"),
    period_hours: int = Query(default=24, ge=1, le=168, description="Time period in hours"),
    metric: str = Query(default="total_return", description="Sort metric: total_return, sharpe_ratio, win_rate")
) -> List[dict]:
    """
    Get top performing traders based on paper trading results.

    Args:
        limit: Maximum number of traders to return
        period_hours: Time period for performance calculation
        metric: Performance metric to sort by

    Returns:
        List of top performing traders with their metrics
    """
    try:
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)

            # Get all active strategies
            strategies = strategy_repo.get_active()

            # Get paper trading results for each strategy
            performers = []
            for strategy in strategies:
                # Get backtest results for the strategy as proxy for paper trading
                from database.repositories import BacktestResultRepository
                backtest_repo = BacktestResultRepository(session)

                # Get recent backtests (simulating paper trading performance)
                since = datetime.utcnow() - timedelta(hours=period_hours)
                backtests = backtest_repo.get_by_strategy(
                    strategy.id,
                    limit=10
                )

                if backtests:
                    # Calculate average metrics
                    total_return = sum(b.total_return for b in backtests if b.total_return) / len(backtests)
                    sharpe_ratio = sum(b.sharpe_ratio for b in backtests if b.sharpe_ratio) / len([b for b in backtests if b.sharpe_ratio])
                    win_rate = sum(b.win_rate for b in backtests if b.win_rate) / len([b for b in backtests if b.win_rate])

                    performers.append({
                        "trader_id": strategy.id,
                        "name": strategy.name,
                        "total_return": float(total_return) if total_return else 0.0,
                        "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else 0.0,
                        "win_rate": float(win_rate) if win_rate else 0.0,
                        "total_trades": sum(b.total_trades for b in backtests if b.total_trades),
                        "strategy_type": strategy.type,
                    })

            # Sort by specified metric
            reverse_sort = metric != "max_drawdown"  # Descending for most metrics, ascending for drawdown
            performers.sort(key=lambda x: x.get(metric, 0), reverse=reverse_sort)

            return performers[:limit]

    except Exception as e:
        logger.error(f"Error getting top performers: {e}")
        # Return empty list on error rather than raising exception
        return []


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    period: str = Query(default="week", description="Time period: day, week, month, all")
) -> dict:
    """
    Get comprehensive trader leaderboard.

    Args:
        limit: Maximum number of traders to return
        period: Time period for ranking

    Returns:
        Leaderboard with rankings and statistics
    """
    try:
        # Calculate time period
        period_hours_map = {
            "day": 24,
            "week": 168,  # 7 days
            "month": 720,  # 30 days
            "all": None,
        }
        period_hours = period_hours_map.get(period)

        # Get top performers
        performers = await get_top_performers(
            limit=limit,
            period_hours=period_hours if period_hours else 168,
            metric="total_return"
        )

        # Calculate statistics
        if performers:
            avg_return = sum(p["total_return"] for p in performers) / len(performers)
            best_return = performers[0]["total_return"] if performers else 0
            worst_return = performers[-1]["total_return"] if performers else 0
        else:
            avg_return = best_return = worst_return = 0

        return {
            "period": period,
            "total_traders": len(performers),
            "leaderboard": [
                {
                    "rank": i + 1,
                    **performer
                }
                for i, performer in enumerate(performers)
            ],
            "statistics": {
                "average_return": avg_return,
                "best_return": best_return,
                "worst_return": worst_return,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return {
            "period": period,
            "total_traders": 0,
            "leaderboard": [],
            "statistics": {
                "average_return": 0,
                "best_return": 0,
                "worst_return": 0,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/{trader_id}/performance")
async def get_trader_performance(
    trader_id: str,
    period_hours: int = Query(default=168, ge=1, le=8760, description="Time period in hours")
) -> dict:
    """
    Get detailed performance metrics for a specific trader.

    Args:
        trader_id: Strategy ID
        period_hours: Time period for performance calculation

    Returns:
        Detailed performance metrics
    """
    try:
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            strategy = strategy_repo.get(trader_id)

            if not strategy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trader {trader_id} not found"
                )

            # Get backtest results
            from database.repositories import BacktestResultRepository
            backtest_repo = BacktestResultRepository(session)

            backtests = backtest_repo.get_by_strategy(trader_id, limit=50)

            if not backtests:
                return {
                    "trader_id": trader_id,
                    "name": strategy.name,
                    "period_hours": period_hours,
                    "metrics": None,
                    "message": "No performance data available"
                }

            # Aggregate metrics
            total_return = sum(b.total_return for b in backtests if b.total_return) / len(backtests)
            sharpe_ratio = sum(b.sharpe_ratio for b in backtests if b.sharpe_ratio) / len([b for b in backtests if b.sharpe_ratio])
            win_rate = sum(b.win_rate for b in backtests if b.win_rate) / len([b for b in backtests if b.win_rate])
            total_trades = sum(b.total_trades for b in backtests if b.total_trades)

            return {
                "trader_id": trader_id,
                "name": strategy.name,
                "strategy_type": strategy.type,
                "period_hours": period_hours,
                "metrics": {
                    "total_return": float(total_return) if total_return else 0.0,
                    "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else 0.0,
                    "win_rate": float(win_rate) if win_rate else 0.0,
                    "total_trades": total_trades,
                },
                "backtest_count": len(backtests),
                "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trader performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trader performance: {str(e)}"
        )
