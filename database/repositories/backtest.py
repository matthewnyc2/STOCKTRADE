"""
Backtest repository implementations.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import BacktestResultModel, EquityPointModel, TradeModel


class BacktestResultRepository(BaseRepository[BacktestResultModel]):
    """Repository for backtest result operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(BacktestResultModel, session)

    def get_by_strategy(self, strategy_id: str, limit: int = 100) -> List[BacktestResultModel]:
        """Get all backtests for a strategy."""
        stmt = (
            self.query()
            .where(BacktestResultModel.strategy_id == strategy_id)
            .order_by(BacktestResultModel.end_date.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_latest_for_strategy(
        self, strategy_id: str
    ) -> Optional[BacktestResultModel]:
        """Get the latest backtest for a strategy."""
        stmt = (
            self.query()
            .where(BacktestResultModel.strategy_id == strategy_id)
            .order_by(BacktestResultModel.end_date.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[BacktestResultModel]:
        """Get backtests within a date range."""
        stmt = (
            self.query()
            .where(
                BacktestResultModel.start_date >= start_date,
                BacktestResultModel.end_date <= end_date,
            )
            .order_by(BacktestResultModel.end_date.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_best_performing(
        self, strategy_id: Optional[str] = None, limit: int = 10
    ) -> List[BacktestResultModel]:
        """Get best performing backtests by total return."""
        stmt = self.query().order_by(BacktestResultModel.total_return.desc()).limit(limit)
        if strategy_id:
            stmt = stmt.where(BacktestResultModel.strategy_id == strategy_id)
        return list(self.session.execute(stmt).scalars().all())


class EquityPointRepository(BaseRepository[EquityPointModel]):
    """Repository for equity point operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(EquityPointModel, session)

    def get_by_backtest(self, backtest_id: str) -> List[EquityPointModel]:
        """Get all equity points for a backtest, ordered by timestamp."""
        stmt = (
            self.query()
            .where(EquityPointModel.backtest_id == backtest_id)
            .order_by(EquityPointModel.timestamp)
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_backtest(self, backtest_id: str) -> int:
        """Delete all equity points for a backtest. Returns count deleted."""
        stmt = self.query().where(EquityPointModel.backtest_id == backtest_id)
        count = self.session.execute(stmt).scalars().all()
        for point in count:
            self.session.delete(point)
        return len(count)


class TradeRepository(BaseRepository[TradeModel]):
    """Repository for trade operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(TradeModel, session)

    def get_by_backtest(self, backtest_id: str) -> List[TradeModel]:
        """Get all trades for a backtest."""
        stmt = (
            self.query()
            .where(TradeModel.backtest_id == backtest_id)
            .order_by(TradeModel.entry_date)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[TradeModel]:
        """Get recent trades for a symbol."""
        stmt = (
            self.query()
            .where(TradeModel.symbol == symbol.upper())
            .order_by(TradeModel.entry_date.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_winning_trades(
        self, backtest_id: Optional[str] = None, limit: int = 100
    ) -> List[TradeModel]:
        """Get winning trades (positive P&L)."""
        stmt = (
            self.query()
            .where(TradeModel.pnl > 0)
            .order_by(TradeModel.pnl.desc())
            .limit(limit)
        )
        if backtest_id:
            stmt = stmt.where(TradeModel.backtest_id == backtest_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_losing_trades(
        self, backtest_id: Optional[str] = None, limit: int = 100
    ) -> List[TradeModel]:
        """Get losing trades (negative P&L)."""
        stmt = (
            self.query()
            .where(TradeModel.pnl < 0)
            .order_by(TradeModel.pnl.asc())
            .limit(limit)
        )
        if backtest_id:
            stmt = stmt.where(TradeModel.backtest_id == backtest_id)
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_backtest(self, backtest_id: str) -> int:
        """Delete all trades for a backtest. Returns count deleted."""
        stmt = self.query().where(TradeModel.backtest_id == backtest_id)
        count = self.session.execute(stmt).scalars().all()
        for trade in count:
            self.session.delete(trade)
        return len(count)
