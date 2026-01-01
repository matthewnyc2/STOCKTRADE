"""
Paper Trading Engine Service.

Simulates real trading with realistic execution, slippage, and commission.
Provides a complete paper trading system for the Crypto Quant Laboratory.

Key Features:
- Starting balance: $10,000
- Realistic slippage: 0.1%
- Commission: 0.1% per trade
- Position tracking (entry, current P&L, stop loss, take profit)
- Auto-close on stop loss or take profit hits
- Daily loss circuit breaker
- Support for LONG and SHORT positions
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, List
from uuid import uuid4

from database.connection import get_db_context
from database.repositories import PortfolioRepository, PositionRepository
from database.models import PortfolioModel, PositionModel
from models import Portfolio, Position, PortfolioMetrics


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading engine."""

    starting_balance: Decimal = Decimal("10000")
    commission_rate: Decimal = Decimal("0.001")  # 0.1% per trade
    slippage_rate: Decimal = Decimal("0.001")  # 0.1% per trade
    max_daily_loss_percent: Decimal = Decimal("0.20")  # 20% daily loss limit
    max_open_positions: int = 10


@dataclass
class TradeResult:
    """Result of a trade execution."""

    success: bool
    position_id: Optional[str] = None
    message: str = ""
    executed_price: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    slippage: Optional[Decimal] = None


@dataclass
class PositionUpdate:
    """Result of position update."""

    position_id: str
    closed: bool = False
    close_reason: Optional[str] = None
    unrealized_pnl: Decimal = Decimal("0")
    unrealized_pnl_percent: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")


class PaperTradingEngine:
    """
    Core paper trading engine.

    Simulates real trading with realistic execution, slippage, and commission.
    Manages portfolio state, positions, and risk management.
    """

    def __init__(self, config: Optional[PaperTradingConfig] = None) -> None:
        """
        Initialize the paper trading engine.

        Args:
            config: Paper trading configuration (uses defaults if not provided)
        """
        self.config = config or PaperTradingConfig()
        self._daily_loss_limit = self.config.starting_balance * self.config.max_daily_loss_percent
        self._daily_realized_loss = Decimal("0")
        self._last_reset_date = date.today()

        # Ensure portfolio is initialized with configured starting balance
        self._ensure_portfolio_initialized()

    def _ensure_portfolio_initialized(self) -> None:
        """Ensure portfolio is initialized with configured starting balance."""
        with get_db_context() as session:
            port_repo = PortfolioRepository(session)
            portfolio = port_repo.get("current")

            if portfolio is None:
                # Create portfolio with configured starting balance
                port_repo.create(
                    id="current",
                    total_equity=float(self.config.starting_balance),
                    starting_balance=float(self.config.starting_balance),
                    total_pnl=0.0,
                    total_pnl_percent=0.0,
                    open_pnl=0.0,
                    sharpe_ratio=None,
                    sortino_ratio=None,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    profit_factor=None,
                )
            elif portfolio.starting_balance != float(self.config.starting_balance):
                # Update if starting balance doesn't match config
                port_repo.update(
                    "current",
                    starting_balance=float(self.config.starting_balance),
                )

    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> TradeResult:
        """
        Execute a simulated trade.

        Applies slippage and commission, validates balance and risk limits,
        and creates a new position.

        Args:
            symbol: Trading symbol (e.g., "BTC/USD")
            side: Trade side ("LONG" or "SHORT")
            quantity: Position size
            entry_price: Entry price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            reason: Trade reason (optional)

        Returns:
            TradeResult with execution details

        Raises:
            ValueError: If trade parameters are invalid
        """
        # Validate inputs
        side = side.upper()
        if side not in ("LONG", "SHORT"):
            return TradeResult(
                success=False,
                message=f"Invalid side: {side}. Must be LONG or SHORT"
            )

        if quantity <= 0:
            return TradeResult(
                success=False,
                message=f"Quantity must be positive: {quantity}"
            )

        if entry_price <= 0:
            return TradeResult(
                success=False,
                message=f"Entry price must be positive: {entry_price}"
            )

        # Check daily loss circuit breaker
        if self._is_circuit_breaker_triggered():
            return TradeResult(
                success=False,
                message="Daily loss limit reached. Trading suspended for the day."
            )

        # Reset daily loss if new day
        self._reset_daily_loss_if_new_day()

        with get_db_context() as session:
            port_repo = PortfolioRepository(session)
            pos_repo = PositionRepository(session)

            # Get or create portfolio
            portfolio = port_repo.get_current()

            # Calculate position value with slippage and commission
            executed_price = self._apply_slippage(entry_price, side)
            slippage = abs(executed_price - entry_price)
            position_value = executed_price * quantity
            commission = position_value * self.config.commission_rate
            total_cost = position_value + commission

            # Check available balance
            available_balance = portfolio.total_equity
            if total_cost > available_balance:
                return TradeResult(
                    success=False,
                    message=f"Insufficient balance. Need ${total_cost:.2f}, available ${available_balance:.2f}"
                )

            # Check max open positions
            open_positions = pos_repo.get_open_positions()
            if len(open_positions) >= self.config.max_open_positions:
                return TradeResult(
                    success=False,
                    message=f"Maximum open positions reached ({self.config.max_open_positions})"
                )

            # Validate stop loss and take profit
            if stop_loss is not None:
                if side == "LONG" and stop_loss >= executed_price:
                    return TradeResult(
                        success=False,
                        message=f"LONG stop loss must be below entry price: {stop_loss} >= {executed_price}"
                    )
                if side == "SHORT" and stop_loss <= executed_price:
                    return TradeResult(
                        success=False,
                        message=f"SHORT stop loss must be above entry price: {stop_loss} <= {executed_price}"
                    )

            if take_profit is not None:
                if side == "LONG" and take_profit <= executed_price:
                    return TradeResult(
                        success=False,
                        message=f"LONG take profit must be above entry price: {take_profit} <= {executed_price}"
                    )
                if side == "SHORT" and take_profit >= executed_price:
                    return TradeResult(
                        success=False,
                        message=f"SHORT take profit must be below entry price: {take_profit} >= {executed_price}"
                    )

            # Create position
            position_id = f"pos_{uuid4().hex[:12]}"
            pos_repo.create(
                id=position_id,
                symbol=symbol.upper(),
                side=side,
                quantity=float(quantity),
                entry_price=float(executed_price),
                current_price=float(executed_price),
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                stop_loss=float(stop_loss) if stop_loss else None,
                take_profit=float(take_profit) if take_profit else None,
                entry_timestamp=datetime.utcnow(),
                exit_timestamp=None,
                exit_price=None,
                realized_pnl=None,
                open=True,
                exit_reason=None,
                meta={"reason": reason, "commission": float(commission), "slippage": float(slippage)} if reason or commission or slippage else {},
            )

            # Update portfolio equity
            new_equity = portfolio.total_equity - total_cost
            port_repo.update(
                portfolio.id,
                total_equity=float(new_equity),
                last_updated=datetime.utcnow(),
            )

            return TradeResult(
                success=True,
                position_id=position_id,
                message=f"{side} position opened in {symbol}",
                executed_price=executed_price,
                commission=commission,
                slippage=slippage,
            )

    def close_position(
        self,
        position_id: str,
        exit_price: Decimal,
        reason: Optional[str] = None,
    ) -> TradeResult:
        """
        Close an open position.

        Calculates realized P&L, applies commission, and updates portfolio.

        Args:
            position_id: Position ID to close
            exit_price: Exit price
            reason: Reason for closing (optional)

        Returns:
            TradeResult with execution details

        Raises:
            ValueError: If position not found or already closed
        """
        if exit_price <= 0:
            return TradeResult(
                success=False,
                message=f"Exit price must be positive: {exit_price}"
            )

        with get_db_context() as session:
            pos_repo = PositionRepository(session)
            port_repo = PortfolioRepository(session)

            # Get position
            position = pos_repo.get(position_id)
            if position is None:
                return TradeResult(
                    success=False,
                    message=f"Position not found: {position_id}"
                )

            if not position.open:
                return TradeResult(
                    success=False,
                    message=f"Position already closed: {position_id}"
                )

            # Apply slippage to exit price (opposite of entry side)
            exit_side = "SHORT" if position.side == "LONG" else "LONG"
            executed_price = self._apply_slippage(exit_price, exit_side)
            slippage = abs(executed_price - exit_price)

            # Calculate P&L
            entry_price = Decimal(str(position.entry_price))
            quantity = Decimal(str(position.quantity))

            if position.side == "LONG":
                gross_pnl = (executed_price - entry_price) * quantity
            else:  # SHORT
                gross_pnl = (entry_price - executed_price) * quantity

            # Calculate commission
            entry_value = entry_price * quantity
            exit_value = executed_price * quantity
            total_commission = (entry_value + exit_value) * self.config.commission_rate

            # Net P&L
            net_pnl = gross_pnl - total_commission

            # Calculate P&L percentage
            pnl_percent = (net_pnl / entry_value * 100) if entry_value > 0 else Decimal("0")

            # Update position
            pos_repo.update(
                position_id,
                current_price=float(executed_price),
                exit_price=float(executed_price),
                exit_timestamp=datetime.utcnow(),
                realized_pnl=float(net_pnl),
                open=False,
                exit_reason=reason or "manual_close",
            )

            # Update portfolio
            portfolio = port_repo.get_current()
            new_total_pnl = portfolio.total_pnl + net_pnl
            new_pnl_percent = (new_total_pnl / portfolio.starting_balance * 100) if portfolio.starting_balance > 0 else Decimal("0")
            new_equity = portfolio.total_equity + net_pnl

            port_repo.update(
                portfolio.id,
                total_equity=float(new_equity),
                total_pnl=float(new_total_pnl),
                total_pnl_percent=float(new_pnl_percent),
                last_updated=datetime.utcnow(),
            )

            # Track daily loss
            if net_pnl < 0:
                self._daily_realized_loss += abs(net_pnl)

            return TradeResult(
                success=True,
                position_id=position_id,
                message=f"Position closed. P&L: ${net_pnl:.2f} ({pnl_percent:.2f}%)",
                executed_price=executed_price,
                commission=total_commission,
                slippage=slippage,
            )

    def update_positions(self, current_prices: dict[str, Decimal]) -> List[PositionUpdate]:
        """
        Update unrealized P&L for all open positions.

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            List of PositionUpdate results
        """
        updates = []

        with get_db_context() as session:
            pos_repo = PositionRepository(session)
            port_repo = PortfolioRepository(session)

            open_positions = pos_repo.get_open_positions()

            total_open_pnl = Decimal("0")

            for position in open_positions:
                symbol = position.symbol
                if symbol not in current_prices:
                    continue

                current_price = current_prices[symbol]
                entry_price = Decimal(str(position.entry_price))
                quantity = Decimal(str(position.quantity))

                # Calculate unrealized P&L
                if position.side == "LONG":
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:  # SHORT
                    unrealized_pnl = (entry_price - current_price) * quantity

                # Calculate P&L percentage
                entry_value = entry_price * quantity
                unrealized_pnl_percent = (unrealized_pnl / entry_value * 100) if entry_value > 0 else Decimal("0")

                # Update position in database
                pos_repo.update(
                    position.id,
                    current_price=float(current_price),
                    unrealized_pnl=float(unrealized_pnl),
                    unrealized_pnl_percent=float(unrealized_pnl_percent),
                )

                total_open_pnl += unrealized_pnl

                updates.append(
                    PositionUpdate(
                        position_id=position.id,
                        closed=False,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_percent=unrealized_pnl_percent,
                        current_price=current_price,
                    )
                )

            # Update portfolio open P&L
            portfolio = port_repo.get_current()
            port_repo.update(
                portfolio.id,
                open_pnl=float(total_open_pnl),
                last_updated=datetime.utcnow(),
            )

        return updates

    def check_stop_losses(self, current_prices: dict[str, Decimal]) -> List[PositionUpdate]:
        """
        Check and trigger stop losses and take profits.

        Automatically closes positions that hit their stop loss or take profit levels.

        Args:
            current_prices: Dictionary of symbol -> current price

        Returns:
            List of PositionUpdate results including closed positions
        """
        updates = []

        with get_db_context() as session:
            pos_repo = PositionRepository(session)
            open_positions = pos_repo.get_open_positions()

            for position in open_positions:
                symbol = position.symbol
                if symbol not in current_prices:
                    continue

                current_price = current_prices[symbol]

                # Check stop loss
                stop_loss = Decimal(str(position.stop_loss)) if position.stop_loss else None
                take_profit = Decimal(str(position.take_profit)) if position.take_profit else None

                close_reason = None
                should_close = False

                if position.side == "LONG":
                    # LONG: Stop loss is below, take profit is above
                    if stop_loss and current_price <= stop_loss:
                        close_reason = "stop_loss"
                        should_close = True
                    elif take_profit and current_price >= take_profit:
                        close_reason = "take_profit"
                        should_close = True
                else:  # SHORT
                    # SHORT: Stop loss is above, take profit is below
                    if stop_loss and current_price >= stop_loss:
                        close_reason = "stop_loss"
                        should_close = True
                    elif take_profit and current_price <= take_profit:
                        close_reason = "take_profit"
                        should_close = True

                if should_close:
                    # Close the position
                    result = self.close_position(
                        position.id,
                        current_price,
                        reason=close_reason,
                    )

                    if result.success:
                        updates.append(
                            PositionUpdate(
                                position_id=position.id,
                                closed=True,
                                close_reason=close_reason,
                                current_price=result.executed_price or current_price,
                            )
                        )

        return updates

    def get_portfolio(self) -> Portfolio:
        """
        Return full portfolio state.

        Returns:
            Portfolio with all positions and metrics
        """
        with get_db_context() as session:
            port_repo = PortfolioRepository(session)
            pos_repo = PositionRepository(session)

            # Get or create portfolio
            portfolio = port_repo.get_current()

            # Get all open positions
            open_positions = pos_repo.get_open_positions()

            # Convert to Pydantic models
            positions = [
                Position(
                    id=p.id,
                    symbol=p.symbol,
                    side=p.side,
                    quantity=Decimal(str(p.quantity)),
                    entry_price=Decimal(str(p.entry_price)),
                    current_price=Decimal(str(p.current_price)),
                    unrealized_pnl=Decimal(str(p.unrealized_pnl)),
                    unrealized_pnl_percent=Decimal(str(p.unrealized_pnl_percent)),
                    stop_loss=Decimal(str(p.stop_loss)) if p.stop_loss else None,
                    take_profit=Decimal(str(p.take_profit)) if p.take_profit else None,
                    entry_timestamp=p.entry_timestamp,
                    metadata=p.meta or {},
                )
                for p in open_positions
            ]

            return Portfolio(
                total_equity=Decimal(str(portfolio.total_equity)),
                starting_balance=Decimal(str(portfolio.starting_balance)),
                total_pnl=Decimal(str(portfolio.total_pnl)),
                total_pnl_percent=Decimal(str(portfolio.total_pnl_percent)),
                open_pnl=Decimal(str(portfolio.open_pnl or 0)),
                positions=positions,
                metrics=PortfolioMetrics(
                    sharpe_ratio=Decimal(str(portfolio.sharpe_ratio)) if portfolio.sharpe_ratio else None,
                    sortino_ratio=Decimal(str(portfolio.sortino_ratio)) if portfolio.sortino_ratio else None,
                    max_drawdown=Decimal(str(portfolio.max_drawdown)),
                    win_rate=Decimal(str(portfolio.win_rate)),
                    profit_factor=Decimal(str(portfolio.profit_factor)) if portfolio.profit_factor else None,
                ),
                last_updated=portfolio.last_updated or datetime.utcnow(),
            )

    def reset_portfolio(self) -> None:
        """Reset portfolio to initial state."""
        self._daily_realized_loss = Decimal("0")
        self._last_reset_date = date.today()

        with get_db_context() as session:
            pos_repo = PositionRepository(session)
            port_repo = PortfolioRepository(session)

            # Close all open positions
            open_positions = pos_repo.get_open_positions()
            for position in open_positions:
                pos_repo.update(
                    position.id,
                    open=False,
                    exit_timestamp=datetime.utcnow(),
                    exit_price=position.current_price,
                    exit_reason="portfolio_reset",
                )

            # Reset portfolio
            portfolio = port_repo.get_current()
            port_repo.update(
                portfolio.id,
                total_equity=float(self.config.starting_balance),
                total_pnl=0.0,
                total_pnl_percent=0.0,
                open_pnl=0.0,
                last_updated=datetime.utcnow(),
            )

    def _apply_slippage(self, price: Decimal, side: str) -> Decimal:
        """
        Apply slippage to price.

        For LONG: slippage increases entry price (worse for trader)
        For SHORT: slippage decreases entry price (worse for trader)

        Args:
            price: Original price
            side: Trade side ("LONG" or "SHORT")

        Returns:
            Price with slippage applied
        """
        if side == "LONG":
            # Buying: we pay more
            return price * (Decimal("1") + self.config.slippage_rate)
        else:
            # Selling: we receive less
            return price * (Decimal("1") - self.config.slippage_rate)

    def _is_circuit_breaker_triggered(self) -> bool:
        """
        Check if daily loss circuit breaker is triggered.

        Returns:
            True if daily loss limit has been reached
        """
        return self._daily_realized_loss >= self._daily_loss_limit

    def _reset_daily_loss_if_new_day(self) -> None:
        """Reset daily loss tracking if a new day has started."""
        today = date.today()
        if today != self._last_reset_date:
            self._daily_realized_loss = Decimal("0")
            self._last_reset_date = today
