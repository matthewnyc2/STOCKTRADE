"""
Arbitrage-related Pydantic models.

Defines arbitrage opportunities, profit calculations, and related API responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from enum import Enum

from pydantic import BaseModel, Field


class ArbitrageType(str, Enum):
    """Enum for arbitrage opportunity types."""

    ORACLE_LATENCY = "oracle_latency"
    FUNDING_RATE = "funding_rate"
    CROSS_VENUE = "cross_venue"
    CROSS_CHAIN = "cross_chain"


class ArbitrageStatus(str, Enum):
    """Enum for arbitrage opportunity status."""

    DETECTED = "detected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class ExchangeVenue(str, Enum):
    """Enum for trading venues."""

    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    OKX = "okx"
    BYBIT = "bybit"
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    PANCAKESWAP = "pancakeswap"


class Chain(str, Enum):
    """Enum for blockchain networks."""

    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    SOLANA = "solana"


class ArbitrageOpportunity(BaseModel):
    """
    Represents a detected arbitrage opportunity.

    Contains all details needed to evaluate and execute the arbitrage.
    """

    id: str = Field(default_factory=lambda: f"arb_{uuid4().hex[:12]}")
    type: ArbitrageType
    status: ArbitrageStatus = ArbitrageStatus.DETECTED
    symbol: str = Field(min_length=1, description="Trading symbol (e.g., BTC, ETH)")

    # Price information
    buy_price: Decimal = Field(gt=Decimal("0"), description="Price to buy at")
    sell_price: Decimal = Field(gt=Decimal("0"), description="Price to sell at")
    price_diff_percent: Decimal = Field(description="Price difference percentage")

    # Venue information
    buy_venue: str = Field(description="Venue to buy from (exchange or DEX)")
    sell_venue: str = Field(description="Venue to sell to (exchange or DEX)")

    # For cross-chain arbitrage
    buy_chain: Optional[Chain] = Field(default=None)
    sell_chain: Optional[Chain] = Field(default=None)

    # For funding rate arbitrage
    funding_rate: Optional[Decimal] = Field(default=None, description="Funding rate for perp")
    exchange: Optional[str] = Field(default=None, description="Exchange with perp")

    # Profitability
    gross_profit_usd: Decimal = Field(description="Gross profit before fees")
    estimated_fees_usd: Decimal = Field(description="Estimated transaction fees")
    estimated_slippage_usd: Decimal = Field(default=Decimal("0"), description="Estimated slippage cost")
    net_profit_usd: Decimal = Field(description="Net profit after fees and slippage")
    profit_percent: Decimal = Field(description="Profit as percentage of capital")

    # Timing
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="When opportunity expires")
    execution_time_seconds: Optional[float] = Field(default=None, description="Estimated execution time")

    # Metadata
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"), description="Confidence score")
    metadata: dict = Field(default_factory=dict)


class ArbitrageConfig(BaseModel):
    """
    Configuration for arbitrage scanning.

    Defines thresholds and limits for arbitrage detection.
    """

    min_profit_percent: Decimal = Field(default=Decimal("0.5"), description="Minimum profit percentage")
    min_profit_usd: Decimal = Field(default=Decimal("10"), description="Minimum profit in USD")
    max_slippage_percent: Decimal = Field(default=Decimal("0.1"), description="Maximum acceptable slippage")
    max_gas_price_gwei: Optional[int] = Field(default=None, description="Maximum gas price for on-chain trades")

    # Venues to monitor
    enabled_exchanges: list[ExchangeVenue] = Field(
        default_factory=lambda: [
            ExchangeVenue.BINANCE,
            ExchangeVenue.COINBASE,
            ExchangeVenue.BYBIT,
        ]
    )
    enabled_dexs: list[ExchangeVenue] = Field(
        default_factory=lambda: [
            ExchangeVenue.UNISWAP,
            ExchangeVenue.SUSHISWAP,
        ]
    )
    enabled_chains: list[Chain] = Field(
        default_factory=lambda: [
            Chain.ETHEREUM,
            Chain.ARBITRUM,
        ]
    )

    # Capital settings
    max_position_size_usd: Decimal = Field(default=Decimal("10000"), description="Maximum position size")
    min_position_size_usd: Decimal = Field(default=Decimal("100"), description="Minimum position size")

    # Funding rate settings
    min_funding_rate: Decimal = Field(default=Decimal("0.01"), description="Minimum funding rate for arb")

    # Oracle latency settings
    max_oracle_lag_seconds: int = Field(default=30, description="Maximum oracle lag for arb opportunity")


class ArbitrageExecution(BaseModel):
    """
    Represents an executed arbitrage trade.

    Contains execution details and final results.
    """

    id: str = Field(default_factory=lambda: f"arb_exec_{uuid4().hex[:12]}")
    opportunity_id: str = Field(description="ID of the opportunity that was executed")

    symbol: str
    type: ArbitrageType

    # Execution details
    buy_venue: str
    sell_venue: str
    buy_price: Decimal
    sell_price: Decimal
    position_size_usd: Decimal

    # Actual execution results
    actual_buy_price: Optional[Decimal] = Field(default=None)
    actual_sell_price: Optional[Decimal] = Field(default=None)
    actual_fees_usd: Optional[Decimal] = Field(default=None)
    actual_slippage_usd: Optional[Decimal] = Field(default=None)
    actual_profit_usd: Optional[Decimal] = Field(default=None)

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    execution_duration_seconds: Optional[float] = Field(default=None)

    # Status
    status: ArbitrageStatus = ArbitrageStatus.EXECUTING
    error_message: Optional[str] = Field(default=None)

    # Transaction hashes
    buy_tx_hash: Optional[str] = Field(default=None)
    sell_tx_hash: Optional[str] = Field(default=None)

    metadata: dict = Field(default_factory=dict)


class ArbitrageSummary(BaseModel):
    """
    Summary of arbitrage opportunities.

    Provides aggregated statistics for arbitrage scanning.
    """

    total_opportunities: int = Field(description="Total opportunities detected")
    active_opportunities: int = Field(description="Currently active opportunities")
    profitable_opportunities: int = Field(description="Opportunities meeting profit threshold")

    by_type: dict[str, int] = Field(default_factory=dict, description="Count by arbitrage type")
    by_symbol: dict[str, int] = Field(default_factory=dict, description="Count by symbol")

    avg_profit_percent: Decimal = Field(description="Average profit percentage")
    max_profit_percent: Decimal = Field(description="Maximum profit percentage")

    total_executed: int = Field(description="Total arbitrage executions")
    successful_executions: int = Field(description="Successful arbitrage executions")
    total_profit_usd: Decimal = Field(description="Total profit from executed arbitrages")


class ArbitrageScanRequest(BaseModel):
    """
    Request parameters for arbitrage scanning.

    Allows customization of scan parameters.
    """

    symbols: list[str] = Field(default_factory=list, description="Symbols to scan (empty = all)")
    min_profit_percent: Optional[Decimal] = Field(default=None, description="Override minimum profit %")
    min_profit_usd: Optional[Decimal] = Field(default=None, description="Override minimum profit USD")
    include_types: list[ArbitrageType] = Field(
        default_factory=lambda: [
            ArbitrageType.ORACLE_LATENCY,
            ArbitrageType.FUNDING_RATE,
            ArbitrageType.CROSS_VENUE,
        ],
        description="Arbitrage types to scan for"
    )


class VenuePrice(BaseModel):
    """
    Represents price data from a specific venue.

    Used for cross-venue arbitrage detection.
    """

    venue: ExchangeVenue
    symbol: str
    price: Decimal
    volume_24h: Optional[Decimal] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_dex: bool = Field(default=False)
    chain: Optional[Chain] = Field(default=None)


class FundingRateData(BaseModel):
    """
    Represents funding rate data for perpetual futures.

    Used for funding rate arbitrage.
    """

    symbol: str
    exchange: str
    funding_rate: Decimal = Field(description="Current funding rate (as decimal)")
    predicted_funding_rate: Optional[Decimal] = Field(default=None)
    mark_price: Decimal
    index_price: Decimal
    next_funding_time: Optional[datetime] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OraclePriceData(BaseModel):
    """
    Represents oracle price data for latency arbitrage.

    Used to detect lag between CEX and on-chain oracles.
    """

    symbol: str
    oracle_address: Optional[str] = Field(default=None)
    oracle_price: Decimal
    oracle_timestamp: datetime
    cex_price: Decimal
    cex_timestamp: datetime
    price_diff_percent: Decimal
    lag_seconds: float = Field(description="Lag in seconds between oracle and CEX")
