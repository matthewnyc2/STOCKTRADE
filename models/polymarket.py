"""
Polymarket Backtester — Pydantic models.

Covers wallet profiles, simulated trades, backtest results,
correlation arbitrage opportunities, and basket strategies.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────

class PolymarketWhaleTier(str, Enum):
    """Whale size classification by trade volume."""
    SMALL = "small"          # $5K+
    MEDIUM = "medium"        # $25K+
    LARGE = "large"          # $100K+
    MEGA = "mega"            # $500K+
    ULTRA = "ultra"          # $1M+
    GOD = "god"              # $5M+


class TradeOutcome(str, Enum):
    """Resolution state of a prediction market trade."""
    WIN = "win"
    LOSS = "loss"
    PENDING = "pending"
    REDEEMED = "redeemed"


class CopyDelay(str, Enum):
    """How quickly the copy-trader executes after the whale."""
    INSTANT = "instant"      # 0s — theoretical best case
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


class BacktestStatus(str, Enum):
    """Lifecycle of a backtest run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ArbType(str, Enum):
    """Types of arbitrage / hedge detected."""
    BINARY_COMPLEMENT = "binary_complement"     # YES+NO < $1
    MULTI_OUTCOME = "multi_outcome"             # All outcomes sum < $1
    CROSS_PLATFORM = "cross_platform"           # Polymarket vs Kalshi
    CORRELATION = "correlation"                 # Related markets mispriced
    TERM_STRUCTURE = "term_structure"            # Same event, different dates


# ── Wallet & Trade Models ────────────────────────────────────────────

class PolymarketWallet(BaseModel):
    """A wallet being tracked for the backtester."""
    address: str = Field(min_length=1, description="0x wallet address")
    label: Optional[str] = None
    tier: PolymarketWhaleTier = PolymarketWhaleTier.MEDIUM
    total_trades: int = Field(default=0, ge=0)
    total_volume_usd: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    win_rate: Optional[Decimal] = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    true_win_rate: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Win rate adjusted for zombie/unclosed orders",
    )
    profit_loss_ratio: Optional[Decimal] = None
    net_pnl_usd: Decimal = Field(default=Decimal("0"))
    first_trade_at: Optional[datetime] = None
    last_trade_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list, description="e.g. ['insider_suspect','fresh_whale']")


class PolymarketTrade(BaseModel):
    """A single trade on Polymarket."""
    id: str = Field(default_factory=lambda: f"pt_{uuid4().hex[:12]}")
    wallet_address: str
    market_slug: str = ""
    market_question: str = ""
    condition_id: str = ""
    token_id: str = ""
    side: str = Field(description="YES or NO")
    price: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    size: Decimal = Field(ge=Decimal("0"), description="Number of shares")
    cost_usd: Decimal = Field(ge=Decimal("0"))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    outcome: TradeOutcome = TradeOutcome.PENDING
    payout_usd: Optional[Decimal] = None
    pnl_usd: Optional[Decimal] = None


# ── Backtest Configuration & Results ─────────────────────────────────

class BacktestConfig(BaseModel):
    """Configuration for a Polymarket whale-copy backtest."""
    id: str = Field(default_factory=lambda: f"bt_{uuid4().hex[:12]}")
    name: str = Field(default="Polymarket Whale Backtest")
    wallet_addresses: list[str] = Field(min_length=1)
    starting_capital_usd: Decimal = Field(default=Decimal("10000"), gt=Decimal("0"))
    copy_delay: CopyDelay = CopyDelay.FIVE_MIN
    max_trade_size_usd: Decimal = Field(
        default=Decimal("500"),
        gt=Decimal("0"),
        description="Cap per copy-trade",
    )
    slippage_bps: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Assumed slippage in basis points",
    )
    min_whale_trade_usd: Decimal = Field(
        default=Decimal("5000"),
        ge=Decimal("0"),
        description="Only copy trades above this threshold",
    )
    basket_mode: bool = Field(
        default=False,
        description="If True, only trade when N+ wallets agree",
    )
    basket_min_agree: int = Field(
        default=2,
        ge=2,
        description="Minimum wallets that must agree (basket mode)",
    )
    include_closed_markets: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SimulatedTrade(BaseModel):
    """A trade produced by the backtest simulator."""
    id: str = Field(default_factory=lambda: f"st_{uuid4().hex[:12]}")
    source_wallet: str
    source_trade_id: str = ""
    market_question: str = ""
    condition_id: str = ""
    side: str
    entry_price: Decimal
    copy_price: Decimal = Field(description="Price at which the copy executes (after delay + slippage)")
    size_usd: Decimal
    shares: Decimal
    timestamp: datetime
    outcome: TradeOutcome = TradeOutcome.PENDING
    pnl_usd: Decimal = Field(default=Decimal("0"))
    pnl_pct: Decimal = Field(default=Decimal("0"))
    slippage_cost_usd: Decimal = Field(default=Decimal("0"))


class EquityCurvePoint(BaseModel):
    """Single point on the equity curve."""
    timestamp: datetime
    equity_usd: Decimal
    drawdown_pct: Decimal = Field(default=Decimal("0"))


class BacktestResult(BaseModel):
    """Full result of a whale-copy backtest."""
    config: BacktestConfig
    status: BacktestStatus = BacktestStatus.COMPLETED

    # Summary stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    pending_trades: int = 0
    win_rate: Decimal = Field(default=Decimal("0"))
    true_win_rate: Decimal = Field(
        default=Decimal("0"),
        description="Excludes pending/zombie trades from denominator",
    )
    net_pnl_usd: Decimal = Field(default=Decimal("0"))
    net_pnl_pct: Decimal = Field(default=Decimal("0"))
    total_volume_usd: Decimal = Field(default=Decimal("0"))
    profit_loss_ratio: Decimal = Field(default=Decimal("0"))
    max_drawdown_pct: Decimal = Field(default=Decimal("0"))
    sharpe_ratio: Optional[Decimal] = None
    avg_trade_pnl_usd: Decimal = Field(default=Decimal("0"))
    best_trade_pnl_usd: Decimal = Field(default=Decimal("0"))
    worst_trade_pnl_usd: Decimal = Field(default=Decimal("0"))
    total_slippage_cost_usd: Decimal = Field(default=Decimal("0"))

    # Per-wallet breakdown
    wallet_stats: dict[str, dict] = Field(default_factory=dict)

    # Time series
    equity_curve: list[EquityCurvePoint] = Field(default_factory=list)
    trades: list[SimulatedTrade] = Field(default_factory=list)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ── Arbitrage / Hedge Models ─────────────────────────────────────────

class ArbOpportunity(BaseModel):
    """A detected arbitrage or hedge opportunity."""
    id: str = Field(default_factory=lambda: f"arb_{uuid4().hex[:12]}")
    arb_type: ArbType
    markets: list[str] = Field(description="Condition IDs or slugs involved")
    description: str = ""
    total_cost: Decimal = Field(description="Cost to enter the hedge")
    guaranteed_payout: Decimal = Field(description="Minimum payout regardless of outcome")
    profit_usd: Decimal = Field(description="Guaranteed profit (payout - cost)")
    profit_pct: Decimal = Field(description="Return as a percentage")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    confidence: Decimal = Field(
        default=Decimal("1"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="1.0 for pure arb, lower for correlation-based",
    )


# ── API Request / Response Schemas ───────────────────────────────────

class BacktestRequest(BaseModel):
    """Request body for launching a backtest."""
    wallet_addresses: list[str] = Field(min_length=1)
    name: str = "Polymarket Whale Backtest"
    starting_capital_usd: Decimal = Field(default=Decimal("10000"), gt=Decimal("0"))
    copy_delay: CopyDelay = CopyDelay.FIVE_MIN
    max_trade_size_usd: Decimal = Field(default=Decimal("500"), gt=Decimal("0"))
    slippage_bps: int = Field(default=50, ge=0, le=500)
    min_whale_trade_usd: Decimal = Field(default=Decimal("5000"), ge=Decimal("0"))
    basket_mode: bool = False
    basket_min_agree: int = Field(default=2, ge=2)


class WalletAnalysisRequest(BaseModel):
    """Request body for analysing a single wallet."""
    address: str = Field(min_length=1)
    max_trades: int = Field(default=2000, ge=1, le=10000)


class ArbScanRequest(BaseModel):
    """Request body for scanning arbitrage opportunities."""
    min_profit_pct: Decimal = Field(default=Decimal("0.5"), ge=Decimal("0"))
    include_types: list[ArbType] = Field(
        default_factory=lambda: [ArbType.BINARY_COMPLEMENT, ArbType.MULTI_OUTCOME]
    )
    active_only: bool = True
    limit: int = Field(default=50, ge=1, le=500)
