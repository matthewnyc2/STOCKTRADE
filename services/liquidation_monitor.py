"""
Liquidation Monitor Service.

Track large liquidations and cascade events across crypto markets.
Fetches data from Coinglass/Hyblock APIs and detects cascade patterns.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from collections import defaultdict

import httpx

from database.connection import get_db_session
from database.repositories import LiquidationRepository, CascadeRepository
from models import (
    Liquidation,
    CascadeEvent,
    CascadeSeverity,
    LiquidationSide,
    LiquidationHeat,
    LiquidationStats,
)

logger = logging.getLogger(__name__)


# API Configuration
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY", "")
HYBLOCK_API_KEY = os.getenv("HYBLOCK_API_KEY", "")

COINGLASS_API_BASE = "https://open-api.coinglass.com/public"
HYBLOCK_API_BASE = "https://api.hyperliquid.xyz/info"


# ============================================================================
# LIQUIDATION FETCHING
# ============================================================================

async def fetch_liquidations(
    symbol: Optional[str] = None,
    min_amount_usd: float = 100000,
    limit: int = 100,
) -> List[Liquidation]:
    """
    Fetch recent liquidations from external APIs.

    Queries Coinglass and Hyblock for recent liquidation data.
    Falls back to demo data if no API keys are configured.

    Args:
        symbol: Optional symbol filter (e.g., "BTC")
        min_amount_usd: Minimum liquidation size in USD
        limit: Maximum number of results

    Returns:
        List[Liquidation]: List of liquidation events
    """
    liquidations = []

    # Try Coinglass API
    if COINGLASS_API_KEY:
        try:
            coinglass_data = await _fetch_coinglass_liquidations(symbol, limit)
            liquidations.extend(coinglass_data)
        except Exception as e:
            logger.error(f"Error fetching from Coinglass: {e}")

    # Try Hyblock API
    if HYBLOCK_API_KEY:
        try:
            hyblock_data = await _fetch_hyblock_liquidations(symbol, limit)
            liquidations.extend(hyblock_data)
        except Exception as e:
            logger.error(f"Error fetching from Hyblock: {e}")

    # If no data from APIs, use demo data
    if not liquidations:
        logger.warning("No API keys configured, using demo liquidation data")
        liquidations = _get_demo_liquidations(symbol, min_amount_usd, limit)

    # Filter by minimum amount
    liquidations = [
        liq for liq in liquidations
        if liq.amount_usd >= Decimal(str(min_amount_usd))
    ]

    # Store in database
    with get_db_session() as session:
        liq_repo = LiquidationRepository(session)

        for liq in liquidations:
            # Check if already exists
            existing = session.query(liq_repo.model).filter_by(id=liq.id).first()
            if not existing:
                liq_repo.create(
                    id=liq.id,
                    exchange=liq.exchange,
                    symbol=liq.symbol,
                    side=liq.side.value,
                    amount_usd=liq.amount_usd,
                    price=liq.price,
                    timestamp=liq.timestamp,
                    blockchain_txid=liq.blockchain_txid,
                    metadata=liq.metadata,
                )

    logger.info(f"Fetched {len(liquidations)} liquidations")

    return liquidations


async def _fetch_coinglass_liquidations(
    symbol: Optional[str],
    limit: int,
) -> List[Liquidation]:
    """Fetch liquidations from Coinglass API."""
    from uuid import uuid4

    liquidations = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Coinglass liquidation endpoint
            headers = {"Authorization": f"Bearer {COINGLASS_API_KEY}"}
            params = {"limit": limit}

            if symbol:
                params["symbol"] = symbol.upper()

            response = await client.get(
                f"{COINGLASS_API_BASE}/v2/liquidation_chart",
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("data", [])

            for item in results:
                liquidations.append(Liquidation(
                    id=f"liq_coinglass_{uuid4().hex[:12]}",
                    exchange=item.get("exchange", "unknown"),
                    symbol=item.get("symbol", "UNKNOWN"),
                    side=LiquidationSide.LONG if item.get("side") == "long" else LiquidationSide.SHORT,
                    amount_usd=Decimal(str(item.get("amount", 0))),
                    price=Decimal(str(item.get("price", 0))),
                    timestamp=datetime.fromtimestamp(item.get("time", 0)),
                    metadata={"source": "coinglass"},
                ))

    except Exception as e:
        logger.error(f"Coinglass API error: {e}")

    return liquidations


async def _fetch_hyblock_liquidations(
    symbol: Optional[str],
    limit: int,
) -> List[Liquidation]:
    """Fetch liquidations from Hyblock API."""
    from uuid import uuid4

    liquidations = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Hyblock/Hyperliquid endpoint
            params = {"limit": limit}

            if symbol:
                params["coin"] = symbol.upper()

            response = await client.post(
                f"{HYBLOCK_API_BASE}/liquidations",
                json=params,
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("liquidations", [])

            for item in results:
                liquidations.append(Liquidation(
                    id=f"liq_hyblock_{uuid4().hex[:12]}",
                    exchange="hyperliquid",
                    symbol=item.get("coin", "UNKNOWN"),
                    side=LiquidationSide.LONG if item.get("side") == "long" else LiquidationSide.SHORT,
                    amount_usd=Decimal(str(item.get("usd", 0))),
                    price=Decimal(str(item.get("price", 0))),
                    timestamp=datetime.fromtimestamp(item.get("time", 0)),
                    metadata={"source": "hyblock"},
                ))

    except Exception as e:
        logger.error(f"Hyblock API error: {e}")

    return liquidations


def _get_demo_liquidations(
    symbol: Optional[str],
    min_amount_usd: float,
    limit: int,
) -> List[Liquidation]:
    """Generate demo liquidation data for testing."""
    import random

    exchanges = ["binance", "bybit", "okx", "bitget", "hyperliquid"]
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT"]

    if symbol:
        symbols = [f"{symbol.upper()}USDT"]

    liquidations = []
    num_liquidations = random.randint(5, min(limit, 20))

    for _ in range(num_liquidations):
        minutes_ago = random.uniform(0, 60)
        amount = random.uniform(min_amount_usd, min_amount_usd * 10)

        liquidations.append(Liquidation(
            exchange=random.choice(exchanges),
            symbol=random.choice(symbols),
            side=random.choice([LiquidationSide.LONG, LiquidationSide.SHORT]),
            amount_usd=Decimal(str(amount)),
            price=Decimal(str(random.uniform(30000, 70000))),
            timestamp=datetime.utcnow() - timedelta(minutes=minutes_ago),
            metadata={"source": "demo"},
        ))

    return sorted(liquidations, key=lambda x: x.timestamp, reverse=True)


# ============================================================================
# CASCADE DETECTION
# ============================================================================

async def detect_cascades(
    liquidations: Optional[List[Liquidation]] = None,
    time_window_seconds: int = 300,
    min_liquidations: int = 3,
    min_amount_usd: float = 1000000,
) -> List[CascadeEvent]:
    """
    Detect cascade liquidation events.

    A cascade occurs when multiple liquidations happen within a short time window,
    potentially triggering further liquidations and market volatility.

    Args:
        liquidations: List of liquidations to analyze (fetches recent if None)
        time_window_seconds: Time window for cascade detection (default: 5 min)
        min_liquidations: Minimum number of liquidations for cascade
        min_amount_usd: Minimum total amount for cascade

    Returns:
        List[CascadeEvent]: List of detected cascade events
    """
    if liquidations is None:
        # Fetch recent liquidations
        liquidations = await fetch_liquidations(limit=200)

    if len(liquidations) < min_liquidations:
        logger.debug(f"Not enough liquidations for cascade detection: {len(liquidations)}")
        return []

    # Sort by timestamp
    liquidations = sorted(liquidations, key=lambda x: x.timestamp)

    cascades = []

    # Group liquidations by symbol and time window
    symbol_groups = defaultdict(list)
    for liq in liquidations:
        # Extract base symbol (remove USDT/USD suffix)
        base_symbol = liq.symbol.replace("USDT", "").replace("USD", "").replace("PERP", "")
        symbol_groups[base_symbol].append(liq)

    # Detect cascades for each symbol
    for symbol, symbol_liqs in symbol_groups.items():
        symbol_cascades = _detect_symbol_cascades(
            symbol,
            symbol_liqs,
            time_window_seconds,
            min_liquidations,
            min_amount_usd,
        )
        cascades.extend(symbol_cascades)

    # Store cascades in database
    with get_db_session() as session:
        cascade_repo = CascadeRepository(session)

        for cascade in cascades:
            # Check if already exists
            existing = session.query(cascade_repo.model).filter_by(id=cascade.id).first()
            if not existing:
                cascade_repo.create(
                    id=cascade.id,
                    symbol=cascade.symbol,
                    severity=cascade.severity.value,
                    liquidation_count=cascade.liquidation_count,
                    total_amount_usd=cascade.total_amount_usd,
                    start_time=cascade.start_time,
                    end_time=cascade.end_time,
                    duration_seconds=cascade.duration_seconds,
                    affected_symbols=cascade.affected_symbols,
                    long_percentage=cascade.long_percentage,
                    confidence=cascade.confidence,
                    description=cascade.description,
                    metadata=cascade.metadata,
                )

    logger.info(f"Detected {len(cascades)} cascade events")

    return cascades


def _detect_symbol_cascades(
    symbol: str,
    liquidations: List[Liquidation],
    time_window_seconds: int,
    min_liquidations: int,
    min_amount_usd: float,
) -> List[CascadeEvent]:
    """Detect cascades for a specific symbol."""
    from uuid import uuid4

    cascades = []

    if len(liquidations) < min_liquidations:
        return cascades

    # Sliding window detection
    window_start_idx = 0

    for i in range(len(liquidations)):
        window_end_time = liquidations[i].timestamp
        window_start_time = window_end_time - timedelta(seconds=time_window_seconds)

        # Find all liquidations in window
        window_liqs = []
        for j in range(window_start_idx, len(liquidations)):
            if liquidations[j].timestamp >= window_start_time:
                if liquidations[j].timestamp <= window_end_time:
                    window_liqs.append(liquidations[j])
                else:
                    break

        if len(window_liqs) >= min_liquidations:
            # Calculate cascade metrics
            total_amount = sum(liq.amount_usd for liq in window_liqs)

            if total_amount >= Decimal(str(min_amount_usd)):
                long_count = sum(1 for liq in window_liqs if liq.side == LiquidationSide.LONG)
                long_pct = Decimal(str(long_count / len(window_liqs)))

                # Determine severity
                if total_amount >= Decimal("10000000"):  # $10M+
                    severity = CascadeSeverity.EXTREME
                elif total_amount >= Decimal("5000000"):  # $5M+
                    severity = CascadeSeverity.HIGH
                elif total_amount >= Decimal("2000000"):  # $2M+
                    severity = CascadeSeverity.MEDIUM
                else:
                    severity = CascadeSeverity.LOW

                # Calculate confidence based on density
                confidence = Decimal(str(min(1.0, len(window_liqs) / time_window_seconds * 100)))

                # Duration of cascade
                duration = int((window_liqs[-1].timestamp - window_liqs[0].timestamp).total_seconds())

                # Affected symbols (include correlated symbols)
                affected_symbols = _get_correlated_symbols(symbol)

                cascades.append(CascadeEvent(
                    id=f"casc_{uuid4().hex[:8]}",
                    symbol=symbol,
                    severity=severity,
                    liquidation_count=len(window_liqs),
                    total_amount_usd=total_amount,
                    start_time=window_liqs[0].timestamp,
                    end_time=window_liqs[-1].timestamp,
                    duration_seconds=duration,
                    affected_symbols=affected_symbols,
                    long_percentage=long_pct,
                    confidence=confidence,
                    description=_generate_cascade_description(symbol, severity, len(window_liqs), total_amount),
                    metadata={"window_seconds": time_window_seconds},
                ))

                # Move window start past this cascade
                window_start_idx = i + 1

    return cascades


def _get_correlated_symbols(symbol: str) -> List[str]:
    """Get list of correlated symbols for cascade detection."""
    correlations = {
        "BTC": ["ETH", "SOL", "LINK"],
        "ETH": ["BTC", "MATIC", "AVAX"],
        "SOL": ["BTC", "ETH", "AVAX"],
        "LINK": ["BTC", "ETH"],
        "AVAX": ["BTC", "ETH", "SOL"],
    }
    return correlations.get(symbol.upper(), [])


def _generate_cascade_description(
    symbol: str,
    severity: CascadeSeverity,
    count: int,
    total_amount: Decimal,
) -> str:
    """Generate human-readable cascade description."""
    amount_millions = float(total_amount) / 1_000_000

    return (
        f"{severity.value.upper()} cascade detected on {symbol}. "
        f"{count} liquidations totaling ${amount_millions:.2f}M. "
    )


# ============================================================================
# LIQUIDATION HEAT
# ============================================================================

def calculate_liquidation_heat(symbol: str) -> LiquidationHeat:
    """
    Calculate liquidation pressure/heat for a symbol.

    Heat score indicates the likelihood of further liquidations based on
    recent liquidation activity and patterns.

    Args:
        symbol: Trading symbol (e.g., "BTC")

    Returns:
        LiquidationHeat: Heat metrics for the symbol
    """
    with get_db_session() as session:
        liq_repo = LiquidationRepository(session)

        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Get liquidations from database
        liqs_1h = liq_repo.get_by_symbol_and_time_range(
            symbol.upper(),
            one_hour_ago,
            now,
        )
        liqs_24h = liq_repo.get_by_symbol_and_time_range(
            symbol.upper(),
            twenty_four_hours_ago,
            now,
        )

        # Calculate metrics
        total_1h = sum(liq.amount_usd for liq in liqs_1h) if liqs_1h else Decimal("0")
        total_24h = sum(liq.amount_usd for liq in liqs_24h) if liqs_24h else Decimal("0")

        long_1h = sum(liq.amount_usd for liq in liqs_1h if liq.side == LiquidationSide.LONG.value) if liqs_1h else Decimal("0")
        short_1h = sum(liq.amount_usd for liq in liqs_1h if liq.side == LiquidationSide.SHORT.value) if liqs_1h else Decimal("0")

        long_24h = sum(liq.amount_usd for liq in liqs_24h if liq.side == LiquidationSide.LONG.value) if liqs_24h else Decimal("0")
        short_24h = sum(liq.amount_usd for liq in liqs_24h if liq.side == LiquidationSide.SHORT.value) if liqs_24h else Decimal("0")

        # Calculate heat scores (0-1)
        # Heat increases with: 1) More liquidations, 2) Larger amounts, 3) Recent clustering
        base_heat = min(Decimal("1"), total_1h / Decimal("10000000"))  # $10M = max heat

        long_heat = min(Decimal("1"), long_1h / Decimal("5000000"))  # $5M long = max
        short_heat = min(Decimal("1"), short_1h / Decimal("5000000"))  # $5M short = max

        # Determine trend
        if total_1h > total_24h / Decimal("24"):
            trend = "increasing"
        elif total_1h < total_24h / Decimal("48"):
            trend = "decreasing"
        else:
            trend = "stable"

        return LiquidationHeat(
            symbol=symbol.upper(),
            heat_score=base_heat,
            long_heat=long_heat,
            short_heat=short_heat,
            total_liquidated_1h=total_1h,
            total_liquidated_24h=total_24h,
            liquidation_count_1h=len(liqs_1h),
            liquidation_count_24h=len(liqs_24h),
            trend=trend,
            calculated_at=now,
        )


def get_liquidation_stats(
    symbol: Optional[str] = None,
    hours: int = 24,
) -> LiquidationStats:
    """
    Get aggregated liquidation statistics.

    Args:
        symbol: Optional symbol filter
        hours: Time period in hours

    Returns:
        LiquidationStats: Aggregated statistics
    """
    with get_db_session() as session:
        liq_repo = LiquidationRepository(session)

        since = datetime.utcnow() - timedelta(hours=hours)

        if symbol:
            liqs = liq_repo.get_by_symbol_and_time_range(
                symbol.upper(),
                since,
                datetime.utcnow(),
            )
        else:
            liqs = liq_repo.get_since(since)

        if not liqs:
            return LiquidationStats(
                symbol=symbol,
                total_liquidated_usd=Decimal("0"),
                long_liquidated_usd=Decimal("0"),
                short_liquidated_usd=Decimal("0"),
                liquidation_count=0,
                avg_liquidation_size=Decimal("0"),
                largest_liquidation=Decimal("0"),
                cascade_count=0,
                period_hours=hours,
            )

        total = sum(liq.amount_usd for liq in liqs)
        long_total = sum(liq.amount_usd for liq in liqs if liq.side == LiquidationSide.LONG.value)
        short_total = sum(liq.amount_usd for liq in liqs if liq.side == LiquidationSide.SHORT.value)
        largest = max(liq.amount_usd for liq in liqs)
        avg = total / len(liqs)

        # Count cascades in period
        cascade_repo = CascadeRepository(session)
        cascades = cascade_repo.get_since(since)
        cascade_count = len(cascades)

        return LiquidationStats(
            symbol=symbol,
            total_liquidated_usd=total,
            long_liquidated_usd=long_total,
            short_liquidated_usd=short_total,
            liquidation_count=len(liqs),
            avg_liquidation_size=avg,
            largest_liquidation=largest,
            cascade_count=cascade_count,
            period_hours=hours,
        )


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def start_liquidation_monitoring(interval_seconds: int = 60):
    """
    Start continuous liquidation monitoring.

    Periodically fetches liquidations and detects cascades.
    Broadcasts events to WebSocket clients.

    Args:
        interval_seconds: Polling interval
    """
    from core.websocket import get_websocket_manager

    ws_manager = get_websocket_manager()

    logger.info(f"Starting liquidation monitoring with {interval_seconds}s interval")

    while True:
        try:
            # Fetch liquidations
            liquidations = await fetch_liquidations()

            if liquidations:
                # Broadcast to WebSocket
                await ws_manager.broadcast(
                    "liquidations",
                    {
                        "action": "new_liquidations",
                        "liquidations": [liq.model_dump(mode="json") for liq in liquidations],
                    }
                )

            # Detect cascades
            cascades = await detect_cascades(liquidations)

            if cascades:
                # Broadcast cascades
                await ws_manager.broadcast(
                    "liquidations",
                    {
                        "action": "cascade_detected",
                        "cascades": [cascade.model_dump(mode="json") for cascade in cascades],
                    }
                )

            # Update heat for major symbols
            for symbol in ["BTC", "ETH", "SOL"]:
                heat = calculate_liquidation_heat(symbol)
                await ws_manager.broadcast(
                    "liquidations",
                    {
                        "action": "heat_update",
                        "symbol": symbol,
                        "heat": heat.model_dump(mode="json"),
                    }
                )

        except Exception as e:
            logger.error(f"Error in liquidation monitoring: {e}")

        await asyncio.sleep(interval_seconds)
