"""
Tests for Paper Trading Engine.

Tests cover:
- LONG and SHORT trade execution
- Slippage and commission calculation
- Unrealized P&L calculation
- Stop loss triggering
- Take profit triggering
- Balance validation
- Portfolio state
- Circuit breaker functionality
"""

import pytest
from decimal import Decimal
from datetime import datetime

from database.connection import init_db, close_db
from database.repositories import PortfolioRepository, PositionRepository
from services.paper_trading import (
    PaperTradingEngine,
    PaperTradingConfig,
    TradeResult,
    PositionUpdate,
)


@pytest.fixture(autouse=True)
def setup_database():
    """Set up test database before each test."""
    init_db(drop_all=True)
    yield
    close_db()


@pytest.fixture
def engine() -> PaperTradingEngine:
    """Create a paper trading engine for testing."""
    config = PaperTradingConfig(
        starting_balance=Decimal("10000"),
        commission_rate=Decimal("0.001"),  # 0.1%
        slippage_rate=Decimal("0.001"),  # 0.1%
        max_daily_loss_percent=Decimal("0.20"),
        max_open_positions=10,
    )
    return PaperTradingEngine(config)


def test_execute_long_trade(engine: PaperTradingEngine) -> None:
    """Test executing a LONG trade."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("49000"),
        take_profit=Decimal("51000"),
    )

    assert result.success is True
    assert result.position_id is not None
    assert result.executed_price is not None
    assert result.commission is not None
    assert result.slippage is not None

    # Verify slippage applied (LONG: pay more)
    assert result.executed_price > Decimal("50000")

    # Verify commission applied
    expected_commission = result.executed_price * Decimal("0.1") * Decimal("0.001")
    assert abs(result.commission - expected_commission) < Decimal("0.01")

    # Verify position created
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.side == "LONG"
    assert position.symbol == "BTC/USD"
    assert position.quantity == Decimal("0.1")


def test_execute_short_trade(engine: PaperTradingEngine) -> None:
    """Test executing a SHORT trade."""
    result = engine.execute_trade(
        symbol="ETH/USD",
        side="SHORT",
        quantity=Decimal("1.0"),
        entry_price=Decimal("3000"),
        stop_loss=Decimal("3100"),
        take_profit=Decimal("2900"),
    )

    assert result.success is True
    assert result.position_id is not None

    # Verify slippage applied (SHORT: receive less)
    assert result.executed_price < Decimal("3000")

    # Verify position created
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.side == "SHORT"
    assert position.symbol == "ETH/USD"


def test_cannot_exceed_balance(engine: PaperTradingEngine) -> None:
    """Test that trade fails if insufficient balance."""
    # Try to trade more than available balance
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("1.0"),  # ~$50,000 needed, only $10,000 available
        entry_price=Decimal("50000"),
    )

    assert result.success is False
    assert "Insufficient balance" in result.message


def test_invalid_side_rejected(engine: PaperTradingEngine) -> None:
    """Test that invalid side is rejected."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="INVALID",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    assert result.success is False
    assert "Invalid side" in result.message


def test_invalid_stop_loss_long(engine: PaperTradingEngine) -> None:
    """Test that LONG stop loss above entry is rejected."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("51000"),  # Above entry - invalid for LONG
    )

    assert result.success is False
    assert "stop loss must be below" in result.message.lower()


def test_invalid_stop_loss_short(engine: PaperTradingEngine) -> None:
    """Test that SHORT stop loss below entry is rejected."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("49000"),  # Below entry - invalid for SHORT
    )

    assert result.success is False
    assert "stop loss must be above" in result.message.lower()


def test_invalid_take_profit_long(engine: PaperTradingEngine) -> None:
    """Test that LONG take profit below entry is rejected."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        take_profit=Decimal("49000"),  # Below entry - invalid for LONG
    )

    assert result.success is False
    assert "take profit must be above" in result.message.lower()


def test_invalid_take_profit_short(engine: PaperTradingEngine) -> None:
    """Test that SHORT take profit above entry is rejected."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        take_profit=Decimal("51000"),  # Above entry - invalid for SHORT
    )

    assert result.success is False
    assert "take profit must be below" in result.message.lower()


def test_close_position_long_profit(engine: PaperTradingEngine) -> None:
    """Test closing a LONG position with profit."""
    # Open position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )
    assert open_result.success is True

    # Close at higher price (profit)
    close_result = engine.close_position(
        position_id=open_result.position_id,
        exit_price=Decimal("51000"),
    )

    assert close_result.success is True
    assert "P&L:" in close_result.message

    # Verify portfolio updated
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 0  # Position closed
    assert portfolio.total_pnl > 0  # Profit


def test_close_position_short_profit(engine: PaperTradingEngine) -> None:
    """Test closing a SHORT position with profit."""
    # Open position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )
    assert open_result.success is True

    # Close at lower price (profit for short)
    close_result = engine.close_position(
        position_id=open_result.position_id,
        exit_price=Decimal("49000"),
    )

    assert close_result.success is True

    # Verify portfolio updated
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 0
    assert portfolio.total_pnl > 0  # Profit


def test_close_position_long_loss(engine: PaperTradingEngine) -> None:
    """Test closing a LONG position with loss."""
    # Open position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )
    assert open_result.success is True

    initial_equity = engine.get_portfolio().total_equity

    # Close at lower price (loss)
    close_result = engine.close_position(
        position_id=open_result.position_id,
        exit_price=Decimal("49000"),
    )

    assert close_result.success is True

    # Verify portfolio shows loss
    portfolio = engine.get_portfolio()
    assert portfolio.total_pnl < 0  # Loss
    assert portfolio.total_equity < initial_equity


def test_update_unrealized_pnl_long(engine: PaperTradingEngine) -> None:
    """Test updating unrealized P&L for LONG position."""
    # Open position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )
    assert open_result.success is True

    # Update prices (price goes up - unrealized profit)
    updates = engine.update_positions({"BTC/USD": Decimal("51000")})

    assert len(updates) == 1
    update = updates[0]
    assert update.unrealized_pnl > 0  # Profit
    assert update.unrealized_pnl_percent > 0

    # Verify position updated
    portfolio = engine.get_portfolio()
    position = portfolio.positions[0]
    assert position.unrealized_pnl > 0
    assert position.current_price == Decimal("51000")


def test_update_unrealized_pnl_short(engine: PaperTradingEngine) -> None:
    """Test updating unrealized P&L for SHORT position."""
    # Open position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )
    assert open_result.success is True

    # Update prices (price goes down - unrealized profit for short)
    updates = engine.update_positions({"BTC/USD": Decimal("49000")})

    assert len(updates) == 1
    update = updates[0]
    assert update.unrealized_pnl > 0  # Profit for short


def test_stop_loss_triggered_long(engine: PaperTradingEngine) -> None:
    """Test stop loss triggering for LONG position."""
    # Open position with stop loss
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("49000"),
    )
    assert open_result.success is True

    # Price drops to stop loss
    closed = engine.check_stop_losses({"BTC/USD": Decimal("48900")})

    assert len(closed) == 1
    assert closed[0].closed is True
    assert closed[0].close_reason == "stop_loss"

    # Verify position closed
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 0


def test_stop_loss_triggered_short(engine: PaperTradingEngine) -> None:
    """Test stop loss triggering for SHORT position."""
    # Open position with stop loss
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        stop_loss=Decimal("51000"),
    )
    assert open_result.success is True

    # Price rises to stop loss
    closed = engine.check_stop_losses({"BTC/USD": Decimal("51100")})

    assert len(closed) == 1
    assert closed[0].closed is True
    assert closed[0].close_reason == "stop_loss"


def test_take_profit_triggered_long(engine: PaperTradingEngine) -> None:
    """Test take profit triggering for LONG position."""
    # Open position with take profit
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        take_profit=Decimal("51000"),
    )
    assert open_result.success is True

    # Price rises to take profit
    closed = engine.check_stop_losses({"BTC/USD": Decimal("51100")})

    assert len(closed) == 1
    assert closed[0].closed is True
    assert closed[0].close_reason == "take_profit"

    # Verify profit
    portfolio = engine.get_portfolio()
    assert portfolio.total_pnl > 0


def test_take_profit_triggered_short(engine: PaperTradingEngine) -> None:
    """Test take profit triggering for SHORT position."""
    # Open position with take profit
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="SHORT",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
        take_profit=Decimal("49000"),
    )
    assert open_result.success is True

    # Price drops to take profit
    closed = engine.check_stop_losses({"BTC/USD": Decimal("48900")})

    assert len(closed) == 1
    assert closed[0].closed is True
    assert closed[0].close_reason == "take_profit"


def test_portfolio_state(engine: PaperTradingEngine) -> None:
    """Test portfolio returns correct state."""
    # Open some positions
    engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    engine.execute_trade(
        symbol="ETH/USD",
        side="SHORT",
        quantity=Decimal("1.0"),
        entry_price=Decimal("3000"),
    )

    portfolio = engine.get_portfolio()

    assert portfolio.starting_balance == Decimal("10000")
    assert len(portfolio.positions) == 2
    assert portfolio.total_equity > 0
    assert portfolio.total_equity < Decimal("10000")  # Less due to costs

    # Verify metrics
    assert portfolio.metrics is not None
    assert portfolio.metrics.max_drawdown <= 0


def test_max_open_positions_limit(engine: PaperTradingEngine) -> None:
    """Test max open positions limit."""
    config = PaperTradingConfig(
        starting_balance=Decimal("100000"),
        max_open_positions=3,
    )
    limited_engine = PaperTradingEngine(config)

    # Open 3 positions
    for i in range(3):
        result = limited_engine.execute_trade(
            symbol=f"SYMBOL{i}/USD",
            side="LONG",
            quantity=Decimal("0.01"),
            entry_price=Decimal("1000"),
        )
        assert result.success is True

    # Try to open 4th position - should fail
    result = limited_engine.execute_trade(
        symbol="SYMBOL3/USD",
        side="LONG",
        quantity=Decimal("0.01"),
        entry_price=Decimal("1000"),
    )
    assert result.success is False
    assert "Maximum open positions" in result.message


def test_circuit_breaker_triggered(engine: PaperTradingEngine) -> None:
    """Test daily loss circuit breaker."""
    config = PaperTradingConfig(
        starting_balance=Decimal("10000"),
        max_daily_loss_percent=Decimal("0.05"),  # 5% limit = $500
    )
    circuit_engine = PaperTradingEngine(config)

    # Open and close position with loss that exceeds limit
    result1 = circuit_engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),  # ~$5,000 position
        entry_price=Decimal("50000"),
    )
    assert result1.success is True

    # Close with 15% loss = ~$750 loss (exceeds $500 limit)
    circuit_engine.close_position(
        position_id=result1.position_id,
        exit_price=Decimal("42500"),  # 15% drop
    )

    # Try to open new position - should be blocked by circuit breaker
    result2 = circuit_engine.execute_trade(
        symbol="ETH/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("3000"),
    )
    assert result2.success is False
    assert "Daily loss limit" in result2.message


def test_reset_portfolio(engine: PaperTradingEngine) -> None:
    """Test resetting portfolio."""
    # Open some positions
    engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 1
    assert portfolio.total_equity < Decimal("10000")

    # Reset
    engine.reset_portfolio()

    # Verify reset
    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 0
    assert portfolio.total_equity == Decimal("10000")
    assert portfolio.total_pnl == Decimal("0")


def test_slippage_calculation(engine: PaperTradingEngine) -> None:
    """Test slippage is applied correctly."""
    # LONG trade
    long_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    # LONG: executed price should be higher
    assert long_result.executed_price > Decimal("50000")
    expected_slippage = Decimal("50000") * Decimal("0.001")  # 0.1%
    assert abs(long_result.slippage - expected_slippage) < Decimal("0.01")

    # SHORT trade
    short_result = engine.execute_trade(
        symbol="ETH/USD",
        side="SHORT",
        quantity=Decimal("1.0"),
        entry_price=Decimal("3000"),
    )

    # SHORT: executed price should be lower
    assert short_result.executed_price < Decimal("3000")
    expected_slippage = Decimal("3000") * Decimal("0.001")
    assert abs(short_result.slippage - expected_slippage) < Decimal("0.01")


def test_commission_calculation(engine: PaperTradingEngine) -> None:
    """Test commission is calculated correctly."""
    result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    # Commission = executed_price * quantity * 0.001
    expected_commission = result.executed_price * Decimal("0.1") * Decimal("0.001")
    assert abs(result.commission - expected_commission) < Decimal("0.0001")


def test_multiple_positions_update(engine: PaperTradingEngine) -> None:
    """Test updating multiple positions at once."""
    # Open multiple positions
    engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    engine.execute_trade(
        symbol="ETH/USD",
        side="LONG",
        quantity=Decimal("1.0"),
        entry_price=Decimal("3000"),
    )

    engine.execute_trade(
        symbol="SOL/USD",
        side="SHORT",
        quantity=Decimal("10"),
        entry_price=Decimal("100"),
    )

    # Update all prices
    updates = engine.update_positions({
        "BTC/USD": Decimal("51000"),
        "ETH/USD": Decimal("3100"),
        "SOL/USD": Decimal("95"),
    })

    assert len(updates) == 3

    portfolio = engine.get_portfolio()
    assert len(portfolio.positions) == 3
    assert portfolio.open_pnl != 0


def test_close_nonexistent_position(engine: PaperTradingEngine) -> None:
    """Test closing a position that doesn't exist."""
    result = engine.close_position(
        position_id="nonexistent_id",
        exit_price=Decimal("50000"),
    )

    assert result.success is False
    assert "not found" in result.message.lower()


def test_close_already_closed_position(engine: PaperTradingEngine) -> None:
    """Test closing a position that's already closed."""
    # Open and close position
    open_result = engine.execute_trade(
        symbol="BTC/USD",
        side="LONG",
        quantity=Decimal("0.1"),
        entry_price=Decimal("50000"),
    )

    engine.close_position(
        position_id=open_result.position_id,
        exit_price=Decimal("51000"),
    )

    # Try to close again
    close_result = engine.close_position(
        position_id=open_result.position_id,
        exit_price=Decimal("52000"),
    )

    assert close_result.success is False
    assert "already closed" in close_result.message.lower()
