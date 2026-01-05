"""
Shadow API router for Dark Arbitrage Scanner.

Provides endpoints for arbitrage opportunity detection, monitoring, and execution.
All endpoints are prefixed with /shadow to indicate they are part of the dark pool analytics.
"""

from asyncio import create_task
from decimal import Decimal
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, Field

from core.websocket import get_websocket_manager
from models.arbitrage import (
    ArbitrageConfig,
    ArbitrageExecution,
    ArbitrageOpportunity,
    ArbitrageScanRequest,
    ArbitrageStatus,
    ArbitrageSummary,
    ArbitrageType,
    Chain,
    ExchangeVenue,
)
from services.dark_arbitrage import (
    calculate_profit_potential,
    clear_expired_opportunities,
    get_arbitrage_summary,
    get_cached_opportunities,
    scan_all_arbitrage,
    start_continuous_scanning,
    _opportunities_cache,
)
from services.constellation_detector import (
    ConstellationDetector,
    WhaleTransaction,
    WalletConnection,
)


router = APIRouter(prefix="/shadow", tags=["shadow"])


# Scanning state
_scanning_active = False


class ArbitrageOpportunityResponse(BaseModel):
    """Response wrapper for arbitrage opportunity."""

    opportunity: ArbitrageOpportunity
    recommendations: list[str] = Field(default_factory=list)


class ProfitCalculationRequest(BaseModel):
    """Request for custom profit calculation."""

    opportunity_id: str
    position_size_usd: Optional[Decimal] = None
    custom_fees_usd: Optional[Decimal] = None
    custom_slippage_usd: Optional[Decimal] = None


# Constellation detector instance
constellation_detector = ConstellationDetector()


# ============================================================================
# CONSTELLATION DETECTION ENDPOINTS
# ============================================================================

class ConstellationRequest(BaseModel):
    """Request for constellation detection."""

    symbols: Optional[list[str]] = None
    time_window_hours: int = Query(72, ge=1, le=168, description="Time window in hours")
    min_whale_usd: Decimal = Query(Decimal("1000000"), ge=Decimal("100000"),
                                   description="Minimum USD value to consider whale activity")


@router.get("/constellations", response_model=list[dict[str, Any]])
async def list_constellations(
    min_confidence: float = Query(0.3, ge=0, le=1, description="Minimum confidence score"),
    symbols: Optional[str] = Query(None, description="Comma-separated symbols to filter by"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
) -> list[dict[str, Any]]:
    """
    List current constellations.

    Args:
        min_confidence: Minimum confidence score to include
        symbols: Filter by trading symbols (comma-separated)
        limit: Maximum number of results

    Returns:
        List of constellations matching filters
    """
    symbol_list = None
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

    constellations = constellation_detector.get_constellations(
        min_confidence=min_confidence,
        symbols=symbol_list
    )

    return constellations[:limit]


@router.post("/constellations/detect", response_model=dict[str, Any])
async def detect_constellations(
    request: ConstellationRequest,
) -> dict[str, Any]:
    """
    Run constellation detection analysis.

    Args:
        request: Detection configuration

    Returns:
        Detection results with new constellations found
    """
    # For demo purposes, create mock transactions and connections
    # In production, these would come from blockchain data sources
    from datetime import timedelta

    # Generate mock whale transactions
    mock_transactions = [
        WhaleTransaction(
            wallet_address="0x1234...abcd",
            transaction_id=f"tx_{i}",
            symbol=sym,
            amount=Decimal("100"),
            usd_value=request.min_whale_usd * Decimal("1.5"),
            transaction_time=datetime.utcnow() - timedelta(hours=i),
            transaction_type="BUY"
        )
        for i, sym in enumerate(request.symbols or ["BTC", "ETH"])
    ]

    # Generate mock wallet connections
    mock_connections = [
        WalletConnection(
            wallet1=f"0x{i:04x}...abcd",
            wallet2=f"0x{i+1:04x}...abcd",
            connection_type="transfer",
            transaction_count=5,
            total_volume_usd=request.min_whale_usd * Decimal("2"),
            first_connection=datetime.utcnow() - timedelta(days=7),
            last_connection=datetime.utcnow() - timedelta(hours=1)
        )
        for i in range(3)
    ]

    # Run detection
    detected = constellation_detector.detect_constellations(
        transactions=mock_transactions,
        wallet_connections=mock_connections
    )

    # Broadcast high-confidence constellations via WebSocket
    for constellation in detected:
        if constellation.confidence_score >= 0.7:
            await broadcast_constellation_alert(constellation)

    return {
        "detected_constellations": len(detected),
        "high_confidence_count": sum(1 for c in detected if c.confidence_score >= 0.7),
        "total_constellations": len(constellation_detector.constellations),
        "recent_constellations": [
            {
                "constellation_id": c.id,
                "symbols": c.symbols,
                "confidence_score": c.confidence_score,
                "risk_level": c.risk_level,
                "detected_at": c.detected_at.isoformat()
            }
            for c in detected
        ]
    }


async def broadcast_constellation_alert(constellation) -> None:
    """
    Broadcast constellation alert via WebSocket to /ws/shadow channel.

    Args:
        constellation: The constellation to broadcast
    """
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "shadow",
        {
            "type": "constellation_alert",
            "data": {
                "constellation_id": constellation.id,
                "symbols": constellation.symbols,
                "confidence_score": constellation.confidence_score,
                "risk_level": constellation.risk_level,
                "wallet_count": len(constellation.whale_wallets),
                "total_volume_usd": float(constellation.estimated_total_volume_usd),
                "description": constellation.description,
                "detected_at": constellation.detected_at.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("/constellations/{constellation_id}", response_model=dict[str, Any])
async def get_constellation_details(constellation_id: str) -> dict[str, Any]:
    """
    Get details of a specific constellation.

    Args:
        constellation_id: The constellation ID

    Returns:
        Detailed constellation information

    Raises:
        HTTPException: If constellation not found
    """
    for constellation in constellation_detector.constellations:
        if constellation.id == constellation_id:
            return {
                "constellation_id": constellation.id,
                "symbols": constellation.symbols,
                "confidence_score": constellation.confidence_score,
                "risk_level": constellation.risk_level,
                "wallet_count": len(constellation.whale_wallets),
                "total_volume_usd": float(constellation.estimated_total_volume_usd),
                "temporal_score": getattr(constellation, 'temporal_cluster_score', 0.0),
                "network_score": getattr(constellation, 'network_cluster_score', 0.0),
                "description": constellation.description,
                "detected_at": constellation.detected_at.isoformat(),
                "recent_transactions": [
                    {
                        "wallet": t.wallet_address,
                        "symbol": t.symbol,
                        "usd_value": float(t.usd_value),
                        "time": t.transaction_time.isoformat(),
                        "type": t.transaction_type
                    }
                    for t in sorted(constellation.transactions,
                                  key=lambda x: x.transaction_time, reverse=True)[:20]
                ]
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Constellation {constellation_id} not found"
    )


@router.delete("/constellations", status_code=status.HTTP_204_NO_CONTENT)
async def clear_constellations(
    older_than_hours: int = Query(168, ge=1, le=8760, description="Clear constellations older than X hours")
) -> None:
    """
    Clear old constellations from memory.

    Args:
        older_than_hours: Clear constellations detected more than X hours ago
    """
    constellation_detector.clear_old_constellations(hours_old=older_than_hours)


@router.get("/constellations/stats", response_model=dict[str, Any])
async def get_constellation_stats() -> dict[str, Any]:
    """
    Get constellation statistics.

    Returns:
        Statistics about current constellation state
    """
    constellations = constellation_detector.constellations

    if not constellations:
        return {
            "total_constellations": 0,
            "high_confidence_count": 0,
            "critical_risk_count": 0,
            "most_common_symbols": [],
            "avg_confidence_score": 0.0,
            "last_detection": None
        }

    confidence_scores = [c.confidence_score for c in constellations]
    risk_levels = [c.risk_level for c in constellations]
    all_symbols = [s for c in constellations for s in c.symbols]

    # Count symbol occurrences
    symbol_counts = {}
    for symbol in all_symbols:
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    # Get most common symbols
    most_common = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_constellations": len(constellations),
        "high_confidence_count": sum(1 for c in constellations if c.confidence_score >= 0.7),
        "critical_risk_count": sum(1 for c in constellations if c.risk_level == "CRITICAL"),
        "most_common_symbols": most_common,
        "avg_confidence_score": round(sum(confidence_scores) / len(confidence_scores), 4),
        "last_detection": max(c.detected_at for c in constellations).isoformat(),
        "risk_distribution": {
            level: sum(1 for r in risk_levels if r == level)
            for level in set(risk_levels)
        }
    }


@router.get("/arbitrage-opportunities", response_model=list[ArbitrageOpportunity])
async def list_arbitrage_opportunities(
    arb_type: Optional[ArbitrageType] = None,
    symbol: Optional[str] = None,
    min_profit_percent: Optional[Decimal] = None,
    active_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
) -> list[ArbitrageOpportunity]:
    """
    List current arbitrage opportunities.

    Args:
        arb_type: Filter by arbitrage type
        symbol: Filter by trading symbol
        min_profit_percent: Filter by minimum profit percentage
        active_only: Only show active (non-expired) opportunities
        limit: Maximum number of results

    Returns:
        List of arbitrage opportunities matching filters
    """
    opportunities = get_cached_opportunities()

    # Apply filters
    if active_only:
        now = datetime.utcnow()
        opportunities = [
            o for o in opportunities
            if o.expires_at is None or o.expires_at > now
        ]

    if arb_type:
        opportunities = [o for o in opportunities if o.type == arb_type]

    if symbol:
        opportunities = [o for o in opportunities if o.symbol.upper() == symbol.upper()]

    if min_profit_percent is not None:
        opportunities = [o for o in opportunities if o.profit_percent >= min_profit_percent]

    # Sort by profit (highest first)
    opportunities.sort(key=lambda x: x.profit_percent, reverse=True)

    return opportunities[:limit]


@router.get("/arbitrage-opportunities/{opportunity_id}", response_model=ArbitrageOpportunityResponse)
async def get_arbitrage_opportunity(opportunity_id: str) -> ArbitrageOpportunityResponse:
    """
    Get details of a specific arbitrage opportunity.

    Args:
        opportunity_id: The opportunity ID

    Returns:
        Detailed arbitrage opportunity with recommendations

    Raises:
        HTTPException: If opportunity not found
    """
    opportunities = get_cached_opportunities()

    for opp in opportunities:
        if opp.id == opportunity_id:
            # Generate recommendations
            recommendations = _generate_recommendations(opp)

            return ArbitrageOpportunityResponse(
                opportunity=opp,
                recommendations=recommendations
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Arbitrage opportunity {opportunity_id} not found"
    )


@router.post("/arbitrage-opportunities/scan", response_model=list[ArbitrageOpportunity])
async def scan_arbitrage_opportunities(
    request: ArbitrageScanRequest,
    background_tasks: BackgroundTasks,
) -> list[ArbitrageOpportunity]:
    """
    Trigger a new arbitrage scan.

    Args:
        request: Scan configuration
        background_tasks: FastAPI background tasks

    Returns:
        List of detected arbitrage opportunities
    """
    # Determine symbols to scan
    symbols = request.symbols or ["BTC", "ETH", "SOL", "LINK", "AVAX"]

    # Build config
    config = ArbitrageConfig()
    if request.min_profit_percent is not None:
        config.min_profit_percent = request.min_profit_percent
    if request.min_profit_usd is not None:
        config.min_profit_usd = request.min_profit_usd

    # Run scan
    opportunities = await scan_all_arbitrage(
        symbols=symbols,
        config=config,
    )

    # Filter by requested types
    if request.include_types:
        opportunities = [o for o in opportunities if o.type in request.include_types]

    return opportunities


@router.get("/arbitrage-summary", response_model=ArbitrageSummary)
async def get_arbitrage_summary_endpoint() -> ArbitrageSummary:
    """
    Get summary statistics of arbitrage opportunities.

    Returns:
        ArbitrageSummary with aggregated statistics
    """
    return get_arbitrage_summary()


@router.post("/arbitrage-opportunities/{opportunity_id}/calculate-profit", response_model=ArbitrageOpportunity)
async def calculate_custom_profit(
    opportunity_id: str,
    request: ProfitCalculationRequest,
) -> ArbitrageOpportunity:
    """
    Calculate profit with custom parameters.

    Args:
        opportunity_id: The opportunity ID
        request: Custom calculation parameters

    Returns:
        Updated arbitrage opportunity with custom profit calculation

    Raises:
        HTTPException: If opportunity not found
    """
    opportunities = get_cached_opportunities()

    for opp in opportunities:
        if opp.id == opportunity_id:
            # Recalculate with custom parameters
            updated = calculate_profit_potential(
                opp,
                fees=request.custom_fees_usd,
                slippage=request.custom_slippage_usd,
            )

            return updated

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Arbitrage opportunity {opportunity_id} not found"
    )


@router.post("/arbitrage-opportunities/clear-expired", status_code=status.HTTP_204_NO_CONTENT)
async def clear_expired_arbitrage_opportunities() -> None:
    """
    Clear expired arbitrage opportunities from cache.

    Removes opportunities that have passed their expiry time.
    """
    clear_expired_opportunities()

    # Broadcast to WebSocket
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "arbitrage",
        {
            "action": "expired_cleared",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.post("/arbitrage-scanner/start", status_code=status.HTTP_202_ACCEPTED)
async def start_arbitrage_scanner(
    background_tasks: BackgroundTasks,
    interval_seconds: int = Query(10, ge=5, le=300, description="Scan interval in seconds"),
    symbols: Optional[list[str]] = Query(None, description="Symbols to scan"),
) -> dict[str, Any]:
    """
    Start continuous arbitrage scanning in the background.

    Args:
        background_tasks: FastAPI background tasks
        interval_seconds: Scan interval (5-300 seconds)
        symbols: Symbols to scan (default: major tokens)

    Returns:
        Confirmation message with scanner status
    """
    global _scanning_active

    if _scanning_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Arbitrage scanner is already running"
        )

    _scanning_active = True

    # Start background scanning
    background_tasks.add_task(
        _run_continuous_scan,
        interval_seconds=interval_seconds,
        symbols=symbols,
    )

    # Broadcast to WebSocket
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "arbitrage",
        {
            "action": "scanner_started",
            "interval_seconds": interval_seconds,
            "symbols": symbols or ["BTC", "ETH", "SOL"],
        }
    )

    return {
        "status": "started",
        "message": "Arbitrage scanner started",
        "interval_seconds": interval_seconds,
        "symbols": symbols or ["BTC", "ETH", "SOL"],
    }


@router.post("/arbitrage-scanner/stop", status_code=status.HTTP_200_OK)
async def stop_arbitrage_scanner() -> dict[str, Any]:
    """
    Stop continuous arbitrage scanning.

    Returns:
        Confirmation message
    """
    global _scanning_active

    if not _scanning_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Arbitrage scanner is not running"
        )

    _scanning_active = False

    # Broadcast to WebSocket
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "arbitrage",
        {
            "action": "scanner_stopped",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    return {
        "status": "stopped",
        "message": "Arbitrage scanner stopped",
    }


@router.get("/arbitrage-scanner/status", status_code=status.HTTP_200_OK)
async def get_arbitrage_scanner_status() -> dict[str, Any]:
    """
    Get the current status of the arbitrage scanner.

    Returns:
        Scanner status information
    """
    opportunities = get_cached_opportunities()
    summary = get_arbitrage_summary()

    return {
        "scanning_active": _scanning_active,
        "cached_opportunities": len(opportunities),
        "last_scan_time": max([o.detected_at for o in opportunities]) if opportunities else None,
        "summary": summary.model_dump(),
    }


@router.get("/config", response_model=ArbitrageConfig)
async def get_arbitrage_config() -> ArbitrageConfig:
    """
    Get current arbitrage configuration.

    Returns:
        Current ArbitrageConfig
    """
    return ArbitrageConfig()


@router.put("/config", response_model=ArbitrageConfig)
async def update_arbitrage_config(
    config: ArbitrageConfig,
) -> ArbitrageConfig:
    """
    Update arbitrage configuration.

    Args:
        config: New configuration

    Returns:
        Updated configuration
    """
    # In production, this would persist to database
    # For now, just return the config
    return config


@router.get("/venues", response_model=list[dict[str, Any]])
async def get_supported_venues() -> list[dict[str, Any]]:
    """
    Get list of supported trading venues.

    Returns:
        List of supported exchanges and DEXs
    """
    return [
        {
            "venue": ExchangeVenue.BINANCE.value,
            "type": "cex",
            "fee_percent": "0.10",
            "enabled": True,
        },
        {
            "venue": ExchangeVenue.COINBASE.value,
            "type": "cex",
            "fee_percent": "0.50",
            "enabled": True,
        },
        {
            "venue": ExchangeVenue.BYBIT.value,
            "type": "cex",
            "fee_percent": "0.10",
            "enabled": True,
        },
        {
            "venue": ExchangeVenue.UNISWAP.value,
            "type": "dex",
            "fee_percent": "0.30",
            "enabled": True,
            "chain": Chain.ETHEREUM.value,
        },
        {
            "venue": ExchangeVenue.SUSHISWAP.value,
            "type": "dex",
            "fee_percent": "0.30",
            "enabled": True,
            "chain": Chain.ETHEREUM.value,
        },
    ]


@router.get("/chains", response_model=list[dict[str, Any]])
async def get_supported_chains() -> list[dict[str, Any]]:
    """
    Get list of supported blockchain networks.

    Returns:
        List of supported chains with estimated gas costs
    """
    from services.dark_arbitrage import CHAIN_GAS_COSTS

    return [
        {
            "chain": chain.value,
            "estimated_gas_usd": str(gas_cost),
        }
        for chain, gas_cost in CHAIN_GAS_COSTS.items()
    ]


async def _run_continuous_scan(
    interval_seconds: int,
    symbols: Optional[list[str]],
) -> None:
    """
    Background task for continuous scanning.

    Args:
        interval_seconds: Time between scans
        symbols: Symbols to scan
    """
    global _scanning_active

    while _scanning_active:
        try:
            await scan_all_arbitrage(symbols=symbols)
        except Exception as e:
            # Log error but continue scanning
            pass

        # Wait for next scan (check _scanning_active periodically)
        for _ in range(interval_seconds):
            if not _scanning_active:
                break
            import asyncio
            await asyncio.sleep(1)


def _generate_recommendations(opportunity: ArbitrageOpportunity) -> list[str]:
    """
    Generate actionable recommendations for an arbitrage opportunity.

    Args:
        opportunity: The arbitrage opportunity

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Basic recommendations
    if opportunity.profit_percent < Decimal("0.5"):
        recommendations.append("Profit margin is tight - consider waiting for higher spreads")

    if opportunity.estimated_slippage_usd > opportunity.net_profit_usd * Decimal("0.3"):
        recommendations.append("Slippage may consume significant profit - use limit orders")

    # Type-specific recommendations
    if opportunity.type == ArbitrageType.ORACLE_LATENCY:
        recommendations.append("Oracle arb requires fast execution - use flash loans if possible")
        recommendations.append(f"Oracle lag: {opportunity.metadata.get('oracle_lag_seconds', 0):.1f}s")

    elif opportunity.type == ArbitrageType.FUNDING_RATE:
        if opportunity.funding_rate and opportunity.funding_rate < Decimal("-0.01"):
            recommendations.append("Strong negative funding - consider larger position")
        recommendations.append("Monitor funding rate changes before next funding period")

    elif opportunity.type == ArbitrageType.CROSS_VENUE:
        recommendations.append(f"Transfer funds from {opportunity.buy_venue} to {opportunity.sell_venue}")
        recommendations.append("Check withdrawal limits and transfer times")

    elif opportunity.type == ArbitrageType.CROSS_CHAIN:
        recommendations.append(f"Bridge from {opportunity.buy_chain.value} to {opportunity.sell_chain.value}")
        recommendations.append("Account for bridge time (typically 10-30 minutes)")
        recommendations.append("Bridge costs may vary with network congestion")

    # Timing recommendations
    if opportunity.expires_at:
        time_remaining = (opportunity.expires_at - datetime.utcnow()).total_seconds()
        if time_remaining < 15:
            recommendations.append("URGENT: Opportunity expires very soon")
        elif time_remaining < 30:
            recommendations.append("Execute quickly - opportunity window is short")

    return recommendations


# WebSocket event handlers
async def broadcast_opportunity_detected(opportunity: ArbitrageOpportunity) -> None:
    """
    Broadcast a newly detected arbitrage opportunity via WebSocket.

    Args:
        opportunity: The detected opportunity
    """
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "arbitrage",
        {
            "action": "opportunity_detected",
            "opportunity": opportunity.model_dump(mode="json"),
        }
    )


async def broadcast_opportunity_expired(opportunity_id: str) -> None:
    """
    Broadcast an expired arbitrage opportunity via WebSocket.

    Args:
        opportunity_id: The ID of the expired opportunity
    """
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast(
        "arbitrage",
        {
            "action": "opportunity_expired",
            "opportunity_id": opportunity_id,
        }
    )


# ============================================================================
# LIQUIDITY HUNTING ENDPOINTS
# ============================================================================

from typing import List
from pydantic import Field

from services.liquidity_hunter import (
    get_liquidity_map as get_liquidity_map_service,
    detect_stop_clusters,
    detect_liquidity_voids,
    predict_sweep_probability,
    calculate_cascade_risk,
)
from services.market_data import get_prices_from_db, get_current_price


class LiquidityClusterResponse(BaseModel):
    """Response model for a liquidity cluster."""

    price_level: float = Field(description="Price level of the cluster")
    density_score: float = Field(ge=0, le=1, description="Density of stops at this level")
    type: str = Field(description="Type of cluster (ROUND_NUMBER, PREVIOUS_HIGH, etc.)")
    distance_pct: float = Field(description="Distance from current price as percentage")


class LiquidityVoidResponse(BaseModel):
    """Response model for a liquidity void."""

    start_price: float = Field(description="Start price of the void")
    end_price: float = Field(description="End price of the void")
    size_pct: float = Field(description="Size of the gap as percentage")
    risk_level: str = Field(description="Risk level (LOW, MEDIUM, HIGH)")


class SweepPredictionResponse(BaseModel):
    """Response model for a sweep prediction."""

    price_level: float = Field(description="Target price level")
    cluster_type: str = Field(description="Type of cluster")
    probability: float = Field(ge=0, le=1, description="Probability of sweep")
    expected_impulse_pct: float = Field(description="Expected price move after sweep")
    cascade_targets: List[float] = Field(default_factory=list, description="Next levels to trigger")
    time_horizon: str = Field(description="Expected timing (IMMEDIATE, SHORT_TERM, MEDIUM_TERM)")
    distance_from_current_pct: float = Field(description="Distance from current price")
    density_score: float = Field(description="Cluster density score")


class CascadeRiskResponse(BaseModel):
    """Response model for cascade risk assessment."""

    triggered_level: float = Field(description="Price level being triggered")
    cascade_levels: List[dict] = Field(default_factory=list, description="Levels that may cascade")
    cascade_count: int = Field(description="Number of cascade levels")
    total_estimated_volume: float = Field(description="Total volume at risk")
    average_density_score: float = Field(description="Average density of cascade levels")
    risk_level: str = Field(description="Overall risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    max_excursion_pct: float = Field(description="Maximum expected price move")
    sweep_direction: str = Field(description="Direction of sweep (UP or DOWN)")


class LiquidityMapResponse(BaseModel):
    """Complete liquidity map response."""

    symbol: str = Field(description="Trading symbol")
    current_price: float = Field(description="Current market price")
    trend: str = Field(description="Current trend (BULLISH, BEARISH, NEUTRAL)")
    volatility_pct: float = Field(description="Current volatility as percentage")
    clusters: List[LiquidityClusterResponse] = Field(default_factory=list, description="Detected stop clusters")
    voids: List[LiquidityVoidResponse] = Field(default_factory=list, description="Detected liquidity voids")
    sweep_predictions: dict = Field(description="Sweep probability predictions")
    timestamp: str = Field(description="Analysis timestamp")


@router.get("/liquidity-map/{symbol}", response_model=LiquidityMapResponse)
async def get_liquidity_map_endpoint(
    symbol: str,
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
) -> LiquidityMapResponse:
    """
    Get complete liquidity map for a symbol.

    Analyzes price history to detect:
    - Stop-loss clusters at key levels
    - Liquidity voids (price gaps)
    - Sweep probabilities
    - Current trend and volatility

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        lookback: Number of periods to analyze

    Returns:
        Complete liquidity map with all detected patterns

    Example:
        GET /shadow/liquidity-map/BTC?lookback=100
    """
    symbol = symbol.upper()

    # Get complete liquidity map
    liquidity_data = get_liquidity_map_service(symbol, lookback)

    if "error" in liquidity_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=liquidity_data["error"]
        )

    # Convert to response model
    return LiquidityMapResponse(**liquidity_data)


@router.get("/sweep-probability/{symbol}")
async def get_sweep_probability_endpoint(
    symbol: str,
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
) -> dict:
    """
    Get sweep probability analysis for a symbol.

    Returns probability of market makers sweeping each liquidity cluster.
    Higher probability clusters are more likely to be targeted.

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        lookback: Number of periods to analyze

    Returns:
        Sweep predictions sorted by probability

    Example:
        GET /shadow/sweep-probability/ETH
    """
    symbol = symbol.upper()

    # Get price data
    price_data = get_prices_from_db(symbol, limit=lookback)

    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}"
        )

    closes = [float(p["close"]) for p in price_data]
    current_price = closes[-1]

    # Calculate volatility
    import numpy as np
    returns = np.diff(closes) / closes[:-1] if len(closes) > 1 else [0]
    volatility = float(np.std(returns)) if returns else 0.02

    # Detect trend
    recent_closes = closes[-20:]
    trend = "NEUTRAL"
    if len(recent_closes) >= 10:
        if recent_closes[-1] > recent_closes[0] * 1.02:
            trend = "BULLISH"
        elif recent_closes[-1] < recent_closes[0] * 0.98:
            trend = "BEARISH"

    # Detect clusters
    clusters = detect_stop_clusters(symbol, price_data, lookback)

    # Predict sweeps
    predictions = predict_sweep_probability(current_price, clusters, trend, volatility)

    return predictions


@router.get("/clusters/{symbol}", response_model=List[LiquidityClusterResponse])
async def get_stop_clusters_endpoint(
    symbol: str,
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
    min_density: float = Query(default=0.3, ge=0, le=1, description="Minimum density score"),
) -> List[LiquidityClusterResponse]:
    """
    Get detected stop-loss clusters for a symbol.

    Returns clusters where traders likely placed stop-loss orders.
    Higher density scores indicate more stops at that level.

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        lookback: Number of periods to analyze
        min_density: Minimum density score to include

    Returns:
        List of liquidity clusters sorted by density

    Example:
        GET /shadow/clusters/SOL?min_density=0.5
    """
    symbol = symbol.upper()

    # Get price data
    price_data = get_prices_from_db(symbol, limit=lookback)

    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}"
        )

    closes = [float(p["close"]) for p in price_data]
    current_price = closes[-1]

    # Detect clusters
    clusters = detect_stop_clusters(symbol, price_data, lookback)

    # Filter by density and convert to response
    result = []
    for c in clusters:
        if c.density_score >= min_density:
            result.append(
                LiquidityClusterResponse(
                    price_level=c.price_level,
                    density_score=round(c.density_score, 3),
                    type=c.cluster_type,
                    distance_pct=round(abs(c.price_level - current_price) / current_price * 100, 2),
                )
            )

    return result


@router.get("/voids/{symbol}", response_model=List[LiquidityVoidResponse])
async def get_liquidity_voids_endpoint(
    symbol: str,
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
    min_gap_size: float = Query(default=0.02, ge=0.005, le=0.1, description="Minimum gap size (decimal)"),
) -> List[LiquidityVoidResponse]:
    """
    Get detected liquidity voids for a symbol.

    Liquidity voids are price gaps where trading was thin.
    Price often accelerates through voids and reverses at their edges.

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        lookback: Number of periods to analyze
        min_gap_size: Minimum gap size to detect (e.g., 0.02 = 2%)

    Returns:
        List of liquidity voids

    Example:
        GET /shadow/voids/BTC?min_gap_size=0.03
    """
    symbol = symbol.upper()

    # Get price data
    price_data = get_prices_from_db(symbol, limit=lookback)

    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}"
        )

    # Detect voids
    voids = detect_liquidity_voids(symbol, price_data, min_gap_size)

    # Convert to response
    return [
        LiquidityVoidResponse(
            start_price=v.start_price,
            end_price=v.end_price,
            size_pct=round(v.void_size, 2),
            risk_level=v.risk_level,
        )
        for v in voids
    ]


@router.post("/cascade-risk/{symbol}", response_model=CascadeRiskResponse)
async def analyze_cascade_risk_endpoint(
    symbol: str,
    triggered_price: float = Query(..., description="Price level being triggered"),
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
) -> CascadeRiskResponse:
    """
    Calculate cascade risk if a specific level is triggered.

    When one stop cluster triggers, it can cause a cascade by:
    - Triggering stops at adjacent levels
    - Causing forced liquidations
    - Creating momentum to next cluster

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        triggered_price: Price level being triggered
        lookback: Number of periods to analyze

    Returns:
        Cascade risk assessment with all potentially affected levels

    Example:
        POST /shadow/cascade-risk/BTC?triggered_price=50000
    """
    symbol = symbol.upper()

    # Get price data
    price_data = get_prices_from_db(symbol, limit=lookback)

    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}"
        )

    closes = [float(p["close"]) for p in price_data]
    current_price = closes[-1]

    # Detect all clusters
    clusters = detect_stop_clusters(symbol, price_data, lookback)

    # Find the triggered cluster
    triggered_cluster = None
    for cluster in clusters:
        if abs(cluster.price_level - triggered_price) / triggered_price < 0.001:
            triggered_cluster = cluster
            break

    if not triggered_cluster:
        # Create a synthetic cluster at the triggered price
        from services.liquidity_hunter import LiquidityCluster
        triggered_cluster = LiquidityCluster(
            price_level=triggered_price,
            density_score=0.5,
            cluster_type="MANUAL",
        )

    # Calculate cascade risk
    cascade_data = calculate_cascade_risk(triggered_cluster, clusters, current_price)

    return CascadeRiskResponse(**cascade_data)


@router.get("/round-numbers/{symbol}")
async def get_round_number_levels(
    symbol: str,
    count: int = Query(default=10, ge=1, le=20, description="Number of levels to return"),
) -> dict:
    """
    Get psychological round number levels for a symbol.

    Round numbers are key psychological levels where traders
    often place stop-losses and take-profits.

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        count: Number of levels to return above and below

    Returns:
        Dictionary with round number levels

    Example:
        GET /shadow/round-numbers/BTC?count=5
    """
    symbol = symbol.upper()

    # Try to get current price
    current_price_data = await get_current_price(symbol)
    if current_price_data:
        current_price = float(current_price_data["price"])
    else:
        # Fallback to database
        price_data = get_prices_from_db(symbol, limit=1)
        if not price_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data found for {symbol}"
            )
        current_price = float(price_data[0]["close"])

    # Determine appropriate increment
    if current_price >= 10000:
        increment = 1000
    elif current_price >= 1000:
        increment = 100
    elif current_price >= 100:
        increment = 10
    else:
        increment = 1

    # Calculate round numbers
    base = int(current_price / increment) * increment

    levels_above = []
    levels_below = []

    for i in range(1, count + 1):
        levels_above.append(base + (i * increment))
        levels_below.append(base - ((i - 1) * increment))

    return {
        "symbol": symbol,
        "current_price": current_price,
        "increment": increment,
        "levels_above": levels_above[::-1],  # Nearest first
        "levels_below": levels_below[::-1],  # Nearest first
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/liquidity/compare")
async def compare_liquidity_maps(
    symbols: str = Query(..., description="Comma-separated symbols to compare"),
    lookback: int = Query(default=100, ge=20, le=500, description="Number of periods to analyze"),
) -> dict:
    """
    Compare liquidity maps across multiple symbols.

    Returns a side-by-side comparison of liquidity patterns
    across different trading pairs.

    Args:
        symbols: Comma-separated symbols (e.g., "BTC,ETH,SOL")
        lookback: Number of periods to analyze

    Returns:
        Comparison of liquidity metrics across symbols

    Example:
        GET /shadow/liquidity/compare?symbols=BTC,ETH,SOL&lookback=100
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    results = {
        "symbols": symbol_list,
        "lookback_periods": lookback,
        "maps": {},
        "summary": {
            "highest_volatility": None,
            "most_clusters": None,
            "largest_void": None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    max_volatility = 0
    max_clusters = 0
    max_void_size = 0

    for symbol in symbol_list:
        try:
            liquidity_map = get_liquidity_map_service(symbol, lookback)
            results["maps"][symbol] = {
                "current_price": liquidity_map.get("current_price"),
                "trend": liquidity_map.get("trend"),
                "volatility_pct": liquidity_map.get("volatility_pct"),
                "cluster_count": len(liquidity_map.get("clusters", [])),
                "void_count": len(liquidity_map.get("voids", [])),
                "top_sweep_probability": (
                    liquidity_map.get("sweep_predictions", {})
                    .get("predictions", [{}])[0]
                    .get("probability", 0)
                    if liquidity_map.get("sweep_predictions")
                    else 0
                ),
            }

            # Track summary stats
            volatility = liquidity_map.get("volatility_pct", 0) / 100
            if volatility > max_volatility:
                max_volatility = volatility
                results["summary"]["highest_volatility"] = symbol

            cluster_count = len(liquidity_map.get("clusters", []))
            if cluster_count > max_clusters:
                max_clusters = cluster_count
                results["summary"]["most_clusters"] = symbol

            voids = liquidity_map.get("voids", [])
            if voids:
                largest_void = max((v.get("size_pct", 0) for v in voids), default=0)
                if largest_void > max_void_size:
                    max_void_size = largest_void
                    results["summary"]["largest_void"] = symbol

        except Exception as e:
            results["maps"][symbol] = {"error": str(e)}

    return results
