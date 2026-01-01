"""
Whale Tracker Service.

Track large wallet movements to detect smart money activity.
Provides functions for tracking whales, detecting movements, classifying patterns,
and calculating historical accuracy.

Uses public APIs (Etherscan, Whale Alert) for demo data.
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
from database.repositories import (
    WhaleRepository,
    WhaleActivityRepository,
)
from models import Whale, WhaleActivity, WhaleAction, PatternType, WhaleTier

logger = logging.getLogger(__name__)


# API Configuration
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
WHALE_ALERT_API_KEY = os.getenv("WHALE_ALERT_API_KEY", "")

ETHERSCAN_API_BASE = "https://api.etherscan.io/api"
WHALE_ALERT_API_BASE = "https://api.whale-alert.io/v1"


# ============================================================================
# WHALE TRACKING FUNCTIONS
# ============================================================================

def track_whale(
    address: str,
    label: Optional[str] = None,
    tier: WhaleTier = WhaleTier.LARGE,
    pattern_type: PatternType = PatternType.ACCUMULATOR,
) -> Whale:
    """
    Add a wallet to whale tracking.

    Args:
        address: Wallet address to track
        label: Optional human-readable label
        tier: Whale classification tier
        pattern_type: Initial pattern type classification

    Returns:
        Whale: Created whale tracking entry

    Raises:
        ValueError: If address is already being tracked
    """
    with get_db_session() as session:
        repo = WhaleRepository(session)

        # Check if already tracking
        existing = repo.get(address)
        if existing:
            raise ValueError(f"Wallet {address} is already being tracked")

        # Initial holdings detection
        holdings_usd = _detect_whale_holdings(address)

        whale = repo.create(
            address=address,
            label=label or _generate_whale_label(address),
            tier=tier.value,
            holdings_usd=Decimal(str(holdings_usd)),
            holdings_24h_change=Decimal("0"),
            historical_accuracy=None,
            pattern_type=pattern_type.value,
            last_activity=datetime.utcnow(),
            preferred_tokens=[],
            metadata={},
        )

        logger.info(f"Started tracking whale: {address} ({label})")

        return Whale(
            address=whale.address,
            label=whale.label,
            tier=WhaleTier(whale.tier),
            holdings_usd=whale.holdings_usd,
            holdings_24h_change=whale.holdings_24h_change,
            historical_accuracy=whale.historical_accuracy,
            pattern_type=PatternType(whale.pattern_type),
            last_activity=whale.last_activity,
            preferred_tokens=whale.preferred_tokens or [],
            metadata=whale.metadata or {},
        )


async def detect_whale_movements(
    min_amount_usd: float = 50000,
    hours: int = 24,
) -> List[WhaleActivity]:
    """
    Scan for large whale transactions from monitored wallets.

    Fetches recent large transactions from tracked whales and external APIs.

    Args:
        min_amount_usd: Minimum transaction amount in USD
        hours: Lookback period in hours

    Returns:
        List[WhaleActivity]: List of detected whale movements
    """
    activities = []

    # Get tracked whales
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        tracked_whales = whale_repo.get_all()

    # Fetch transactions for each tracked whale
    async with httpx.AsyncClient(timeout=30.0) as client:
        for whale in tracked_whales:
            try:
                whale_activities = await _fetch_whale_transactions(
                    client,
                    whale.address,
                    min_amount_usd,
                    hours,
                )
                activities.extend(whale_activities)
            except Exception as e:
                logger.error(f"Error fetching transactions for {whale.address}: {e}")

    # Store detected activities
    with get_db_session() as session:
        activity_repo = WhaleActivityRepository(session)

        for activity_data in activities:
            # Check if activity already exists
            existing = session.query(activity_repo.model).filter_by(
                transaction_hash=activity_data.get("transaction_hash")
            ).first()

            if not existing:
                activity_repo.create(
                    id=activity_data["id"],
                    whale_address=activity_data["whale_address"],
                    symbol=activity_data["symbol"],
                    action=activity_data["action"],
                    amount_usd=Decimal(str(activity_data["amount_usd"])),
                    timestamp=activity_data["timestamp"],
                    transaction_hash=activity_data.get("transaction_hash"),
                    metadata=activity_data.get("metadata", {}),
                )

    logger.info(f"Detected {len(activities)} whale movements")

    return [
        WhaleActivity(
            id=a["id"],
            whale_address=a["whale_address"],
            symbol=a["symbol"],
            action=WhaleAction(a["action"]),
            amount_usd=Decimal(str(a["amount_usd"])),
            timestamp=a["timestamp"],
            transaction_hash=a.get("transaction_hash"),
            metadata=a.get("metadata", {}),
        )
        for a in activities
    ]


def classify_whale_pattern(whale_address: str) -> PatternType:
    """
    Classify a whale's behavior pattern based on historical activity.

    Analyzes buy/sell patterns, timing, and token preferences to classify as:
    - ACCUMULATOR: Consistently buys over time, rarely sells
    - DISTRIBUTOR: Sells holdings gradually over time
    - SNIPER: Makes large, timely trades before price movements
    - MANIPULATOR: Attempts to influence price through large trades

    Args:
        whale_address: The whale wallet address

    Returns:
        PatternType: Classified behavior pattern
    """
    with get_db_session() as session:
        activity_repo = WhaleActivityRepository(session)
        activities = activity_repo.get_by_whale(whale_address, limit=100)

    if len(activities) < 5:
        # Not enough data, default to accumulator
        return PatternType.ACCUMULATOR

    # Calculate metrics
    buy_count = sum(1 for a in activities if a.action == WhaleAction.BOUGHT.value)
    sell_count = sum(1 for a in activities if a.sell_count if hasattr(a, 'sell_count') else 0)
    transfer_count = sum(1 for a in activities if a.action == WhaleAction.TRANSFERRED.value)

    total_count = len(activities)
    buy_ratio = buy_count / total_count if total_count > 0 else 0
    sell_ratio = sell_count / total_count if total_count > 0 else 0

    # Calculate average transaction size
    avg_amount = sum(a.amount_usd for a in activities) / total_count

    # Calculate timing consistency (standard deviation of time between trades)
    if len(activities) > 1:
        timestamps = [a.timestamp for a in activities]
        timestamps_sorted = sorted(timestamps, reverse=True)
        intervals = [
            (timestamps_sorted[i] - timestamps_sorted[i + 1]).total_seconds()
            for i in range(len(timestamps_sorted) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        timing_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals) if intervals else 0
    else:
        timing_variance = 0

    # Classification logic
    if avg_amount > 1000000 and timing_variance < 86400:  # Large, consistent trades
        return PatternType.SNIPER
    elif sell_ratio > 0.6 and buy_ratio < 0.3:
        return PatternType.DISTRIBUTOR
    elif buy_ratio > 0.7 and sell_ratio < 0.2:
        return PatternType.ACCUMULATOR
    elif transfer_count > buy_count + sell_count:
        return PatternType.MANIPULATOR
    else:
        return PatternType.ACCUMULATOR


def calculate_accuracy(whale_address: str) -> Optional[Decimal]:
    """
    Calculate historical win rate for a whale's trades.

    Compares whale's buy/sell timing to subsequent price movements.
    A "win" is defined as buying before a price increase or selling before a decrease.

    Args:
        whale_address: The whale wallet address

    Returns:
        Decimal: Win rate (0-1), or None if insufficient data
    """
    from services.market_data import get_prices_from_db

    with get_db_session() as session:
        activity_repo = WhaleActivityRepository(session)
        activities = activity_repo.get_by_whale(whale_address, limit=50)

    if len(activities) < 3:
        return None

    wins = 0
    total = 0

    for activity in activities:
        if activity.action not in [WhaleAction.BOUGHT.value, WhaleAction.SOLD.value]:
            continue

        # Get price data around the activity time
        symbol = activity.symbol
        activity_time = activity.timestamp

        try:
            # Get price 1 hour before and 24 hours after
            prices = get_prices_from_db(
                symbol,
                start=activity_time - timedelta(hours=1),
                end=activity_time + timedelta(hours=24),
                limit=50,
            )

            if not prices or len(prices) < 2:
                continue

            # Find closest prices
            before_price = None
            after_price = None

            for p in prices:
                if p["timestamp"] <= activity_time:
                    before_price = p["close"]
                if p["timestamp"] >= activity_time + timedelta(hours=24):
                    after_price = p["close"]
                    break

            if before_price and after_price:
                price_change = (after_price - before_price) / before_price

                # Win if bought before price increase or sold before decrease
                if activity.action == WhaleAction.BOUGHT.value and price_change > 0:
                    wins += 1
                    total += 1
                elif activity.action == WhaleAction.SOLD.value and price_change < 0:
                    wins += 1
                    total += 1
                else:
                    total += 1

        except Exception as e:
            logger.warning(f"Error calculating accuracy for {activity.id}: {e}")
            continue

    if total == 0:
        return None

    accuracy = Decimal(str(wins / total))

    # Update whale's accuracy
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whale = whale_repo.get(whale_address)
        if whale:
            whale_repo.update(whale_address, historical_accuracy=accuracy)

    return accuracy


async def scan_smart_money() -> List[Dict[str, Any]]:
    """
    Scan for potential smart money wallets using Whale Alert API.

    Identifies wallets making large, timely moves that may indicate insider knowledge
    or sophisticated trading strategies.

    Returns:
        List of discovered smart money candidates
    """
    if not WHALE_ALERT_API_KEY:
        logger.warning("WHALE_ALERT_API_KEY not set, using demo data")
        return _get_demo_smart_money()

    candidates = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get recent large transactions
            params = {
                "api_key": WHALE_ALERT_API_KEY,
                "min_value": 500000,
                "limit": 100,
            }

            response = await client.get(
                f"{WHALE_ALERT_API_BASE}/transactions",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            transactions = data.get("transactions", [])

            # Group by wallet
            wallet_stats = defaultdict(lambda: {
                "transactions": [],
                "total_volume": 0,
                "symbols": set(),
            })

            for tx in transactions:
                if tx.get("to_owner") == "unknown":
                    continue

                wallet = tx["to_owner"]
                wallet_stats[wallet]["transactions"].append(tx)
                wallet_stats[wallet]["total_volume"] += tx.get("amount_usd", 0)
                wallet_stats[wallet]["symbols"].add(tx.get("symbol", "UNKNOWN"))

            # Identify promising candidates
            for wallet, stats in wallet_stats.items():
                if (
                    stats["total_volume"] > 1000000  # $1M+ volume
                    and len(stats["transactions"]) >= 3  # Multiple transactions
                    and len(stats["symbols"]) <= 5  # Focused on few tokens
                ):
                    candidates.append({
                        "address": wallet,
                        "estimated_volume": stats["total_volume"],
                        "transaction_count": len(stats["transactions"]),
                        "preferred_tokens": list(stats["symbols"])[:5],
                        "confidence": min(0.9, 0.5 + len(stats["transactions"]) * 0.1),
                    })

    except Exception as e:
        logger.error(f"Error scanning smart money: {e}")
        return _get_demo_smart_money()

    return candidates


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_whale_label(address: str) -> str:
    """Generate a label for a whale based on address."""
    return f"Whale-{address[:6]}...{address[-4:]}"


def _detect_whale_holdings(address: str) -> float:
    """
    Detect whale holdings from Etherscan.

    For demo purposes, returns simulated data.
    """
    if not ETHERSCAN_API_KEY:
        # Return demo data
        import random
        random.seed(hash(address))
        return random.uniform(100000, 10000000)  # $100K - $10M

    # TODO: Implement actual Etherscan API call
    return 0.0


async def _fetch_whale_transactions(
    client: httpx.AsyncClient,
    address: str,
    min_amount_usd: float,
    hours: int,
) -> List[Dict[str, Any]]:
    """Fetch recent transactions for a whale wallet."""
    from uuid import uuid4

    # For demo purposes, return simulated data
    # In production, this would call Etherscan or similar APIs

    activities = []

    # Simulate some recent activity
    if not ETHERSCAN_API_KEY:
        import random
        random.seed(address)

        num_activities = random.randint(0, 3)
        symbols = ["BTC", "ETH", "SOL", "LINK", "UNI"]

        for _ in range(num_activities):
            hours_ago = random.uniform(0, hours)
            timestamp = datetime.utcnow() - timedelta(hours=hours_ago)

            activity = {
                "id": f"act_{uuid4().hex[:12]}",
                "whale_address": address,
                "symbol": random.choice(symbols),
                "action": random.choice([WhaleAction.BOUGHT.value, WhaleAction.SOLD.value]),
                "amount_usd": random.uniform(min_amount_usd, min_amount_usd * 10),
                "timestamp": timestamp,
                "transaction_hash": f"0x{uuid4().hex}",
                "metadata": {"source": "demo"},
            }
            activities.append(activity)

    return activities


def _get_demo_smart_money() -> List[Dict[str, Any]]:
    """Get demo smart money data for testing."""
    return [
        {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "estimated_volume": 5000000,
            "transaction_count": 15,
            "preferred_tokens": ["BTC", "ETH"],
            "confidence": 0.85,
        },
        {
            "address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "estimated_volume": 2500000,
            "transaction_count": 8,
            "preferred_tokens": ["SOL", "LINK"],
            "confidence": 0.72,
        },
    ]


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def update_all_whale_classifications() -> Dict[str, PatternType]:
    """
    Recalculate pattern classifications for all tracked whales.

    Returns:
        Dictionary mapping whale addresses to their new patterns
    """
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whales = whale_repo.get_all()

    results = {}

    for whale in whales:
        try:
            new_pattern = classify_whale_pattern(whale.address)
            results[whale.address] = new_pattern

            # Update in database
            with get_db_session() as session:
                whale_repo = WhaleRepository(session)
                whale_repo.update(
                    whale.address,
                    pattern_type=new_pattern.value,
                )

        except Exception as e:
            logger.error(f"Error classifying whale {whale.address}: {e}")

    return results


async def update_all_whale_accuracy() -> Dict[str, Optional[Decimal]]:
    """
    Recalculate accuracy for all tracked whales.

    Returns:
        Dictionary mapping whale addresses to their accuracy scores
    """
    with get_db_session() as session:
        whale_repo = WhaleRepository(session)
        whales = whale_repo.get_all()

    results = {}

    for whale in whales:
        try:
            accuracy = calculate_accuracy(whale.address)
            results[whale.address] = accuracy
        except Exception as e:
            logger.error(f"Error calculating accuracy for {whale.address}: {e}")
            results[whale.address] = None

    return results
