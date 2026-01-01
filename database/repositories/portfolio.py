"""
Portfolio repository implementations.
"""

from typing import List

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import PortfolioModel, PositionModel


class PortfolioRepository(BaseRepository[PortfolioModel]):
    """Repository for portfolio operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(PortfolioModel, session)

    def get_current(self) -> PortfolioModel:
        """Get the current portfolio (creates if doesn't exist)."""
        portfolio = self.get("current")
        if portfolio is None:
            # Create default portfolio
            portfolio = self.create(
                id="current",
                total_equity=100000.00,
                starting_balance=100000.00,
                win_rate=0.0,
            )
        return portfolio

    def update_metrics(
        self,
        total_equity: float,
        total_pnl: float,
        open_pnl: float,
        sharpe_ratio: float | None = None,
        sortino_ratio: float | None = None,
        max_drawdown: float = 0.0,
        win_rate: float = 0.0,
        profit_factor: float | None = None,
    ) -> PortfolioModel:
        """Update portfolio metrics."""
        portfolio = self.get_current()

        total_pnl_percent = (total_pnl / portfolio.starting_balance) * 100 if portfolio.starting_balance > 0 else 0

        return self.update(
            "current",
            total_equity=total_equity,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            open_pnl=open_pnl,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
        )


class PositionRepository(BaseRepository[PositionModel]):
    """Repository for position operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(PositionModel, session)

    def get_open_positions(self) -> List[PositionModel]:
        """Get all open positions for the current portfolio."""
        stmt = (
            self.query()
            .where(PositionModel.open == True)
            .order_by(PositionModel.entry_timestamp.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_symbol(self, symbol: str) -> List[PositionModel]:
        """Get all positions for a specific symbol."""
        stmt = (
            self.query()
            .where(PositionModel.symbol == symbol.upper())
            .order_by(PositionModel.entry_timestamp.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_open_position_for_symbol(self, symbol: str) -> PositionModel | None:
        """Get open position for a specific symbol."""
        return self.get_by(open=True, symbol=symbol.upper())

    def get_long_positions(self) -> List[PositionModel]:
        """Get all long positions."""
        stmt = (
            self.query()
            .where(
                PositionModel.portfolio_id == "current",
                PositionModel.side == "LONG",
            )
            .order_by(PositionModel.entry_timestamp.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_short_positions(self) -> List[PositionModel]:
        """Get all short positions."""
        stmt = (
            self.query()
            .where(
                PositionModel.portfolio_id == "current",
                PositionModel.side == "SHORT",
            )
            .order_by(PositionModel.entry_timestamp.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def close_position(self, position_id: str) -> bool:
        """Close a position by deleting it. Returns True if closed."""
        return self.delete(position_id)
