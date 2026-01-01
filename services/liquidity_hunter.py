"""
Liquidity Hunter Service.

Detects stop-loss clusters, liquidity voids, and predicts stop hunts.
Market makers often target known liquidity zones to trigger cascades.

This service identifies:
1. Stop-loss clusters (round numbers, previous highs/lows, options max pain)
2. Liquidity voids (price gaps with minimal historical trading)
3. Sweep probability (likelihood of price sweeping a cluster)
4. Cascade risk (what other stops trigger if one is hit)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

from services.market_data import get_prices_from_db

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class LiquidityCluster:
    """Represents a cluster of stop-losses at a price level."""

    def __init__(
        self,
        price_level: float,
        density_score: float,
        cluster_type: str,
        estimated_volume: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.price_level = price_level
        self.density_score = density_score  # 0-1, higher = more stops
        self.cluster_type = cluster_type  # ROUND_NUMBER, PREVIOUS_HIGH/LOW, MAX_PAIN
        self.estimated_volume = estimated_volume
        self.metadata = metadata or {}


class LiquidityVoid:
    """Represents a price gap with minimal liquidity."""

    def __init__(
        self,
        start_price: float,
        end_price: float,
        void_size: float,
        risk_level: str,
    ):
        self.start_price = start_price
        self.end_price = end_price
        self.void_size = void_size  # Percentage gap
        self.risk_level = risk_level  # LOW, MEDIUM, HIGH


class SweepPrediction:
    """Prediction of a potential stop sweep."""

    def __init__(
        self,
        target_price: float,
        probability: float,
        expected_impulse: float,
        cascade_targets: List[float],
        time_horizon: str,
    ):
        self.target_price = target_price
        self.probability = probability  # 0-1
        self.expected_impulse = expected_impulse  # Expected price move after sweep
        self.cascade_targets = cascade_targets  # Next stops to trigger
        self.time_horizon = time_horizon  # IMMEDIATE, SHORT_TERM, MEDIUM_TERM


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def detect_stop_clusters(
    symbol: str,
    price_data: List[Dict[str, Any]],
    lookback_periods: int = 100,
) -> List[LiquidityCluster]:
    """
    Detect stop-loss clusters at key price levels.

    Analyzes price history to find where traders likely placed stops:
    - Round numbers (psychological levels)
    - Previous swing highs/lows
    - Recent support/resistance levels
    - Options max pain points (if available)

    Args:
        symbol: Trading symbol (e.g., "BTC", "ETH")
        price_data: List of OHLCV price data
        lookback_periods: Number of periods to analyze

    Returns:
        List of LiquidityCluster objects sorted by density score
    """
    if not price_data or len(price_data) < 20:
        logger.warning(f"Insufficient price data for {symbol}")
        return []

    clusters = []
    closes = [float(p["close"]) for p in price_data]
    highs = [float(p["high"]) for p in price_data]
    lows = [float(p["low"]) for p in price_data]
    volumes = [float(p.get("volume", 0)) for p in price_data]

    current_price = closes[-1]
    price_range = max(highs[-lookback_periods:]) - min(lows[-lookback_periods:])

    # 1. Detect round number clusters
    round_clusters = _detect_round_numbers(current_price, price_range)
    clusters.extend(round_clusters)

    # 2. Detect previous swing highs/lows
    swing_clusters = _detect_swing_points(highs, lows, closes, lookback_periods)
    clusters.extend(swing_clusters)

    # 3. Detect support/resistance zones
    sr_clusters = _detect_support_resistance(closes, highs, lows, volumes)
    clusters.extend(sr_clusters)

    # 4. Detect consolidation breakouts (stops above/below ranges)
    consolidation_clusters = _detect_consolidation_breakouts(closes, highs, lows)
    clusters.extend(consolidation_clusters)

    # Deduplicate and score clusters
    unique_clusters = _merge_nearby_clusters(clusters)

    # Calculate density scores based on multiple factors
    for cluster in unique_clusters:
        cluster.density_score = _calculate_cluster_density(
            cluster, closes, highs, lows, volumes
        )

    # Sort by density score (highest first)
    unique_clusters.sort(key=lambda c: c.density_score, reverse=True)

    return unique_clusters


def detect_liquidity_voids(
    symbol: str,
    price_data: List[Dict[str, Any]],
    min_gap_size: float = 0.02,  # 2%
) -> List[LiquidityVoid]:
    """
    Detect liquidity voids in price action.

    Liquidity voids are price gaps where trading was thin.
    Price often accelerates through voids and reverses at their edges.

    Args:
        symbol: Trading symbol
        price_data: List of OHLCV price data
        min_gap_size: Minimum gap size to consider (as percentage)

    Returns:
        List of LiquidityVoid objects
    """
    if not price_data or len(price_data) < 20:
        logger.warning(f"Insufficient price data for {symbol}")
        return []

    voids = []
    closes = [float(p["close"]) for p in price_data]
    highs = [float(p["high"]) for p in price_data]
    lows = [float(p["low"]) for p in price_data]
    volumes = [float(p.get("volume", 0)) for p in price_data]

    # Calculate average volume for comparison
    avg_volume = np.mean(volumes) if volumes else 0
    low_volume_threshold = avg_volume * 0.5

    # Look for gaps where volume was exceptionally low
    for i in range(1, len(price_data)):
        prev_high = highs[i - 1]
        prev_low = lows[i - 1]
        curr_high = highs[i]
        curr_low = lows[i]
        curr_volume = volumes[i]

        # Check for gap up
        if curr_low > prev_high:
            gap_size = (curr_low - prev_high) / prev_high
            if gap_size >= min_gap_size:
                risk = _assess_void_risk(gap_size, curr_volume, low_volume_threshold)
                voids.append(
                    LiquidityVoid(
                        start_price=prev_high,
                        end_price=curr_low,
                        void_size=gap_size * 100,  # As percentage
                        risk_level=risk,
                    )
                )

        # Check for gap down
        if curr_high < prev_low:
            gap_size = (prev_low - curr_high) / prev_low
            if gap_size >= min_gap_size:
                risk = _assess_void_risk(gap_size, curr_volume, low_volume_threshold)
                voids.append(
                    LiquidityVoid(
                        start_price=curr_high,
                        end_price=prev_low,
                        void_size=gap_size * 100,  # As percentage
                        risk_level=risk,
                    )
                )

    # Also look for low-volume consolidation zones that could become voids
    consolidation_voids = _detect_consolidation_voids(closes, highs, lows, volumes, min_gap_size)
    voids.extend(consolidation_voids)

    return voids


def predict_sweep_probability(
    current_price: float,
    clusters: List[LiquidityCluster],
    current_trend: str = "NEUTRAL",
    volatility: float = 0.02,
) -> Dict[str, Any]:
    """
    Predict probability of sweeping specific liquidity clusters.

    Uses multiple factors:
    - Distance to cluster (closer = higher probability)
    - Cluster density (more stops = more attractive target)
    - Current trend (uptrends target above, downtrends target below)
    - Volatility (higher volatility increases sweep likelihood)
    - Time of day/week effects

    Args:
        current_price: Current market price
        clusters: List of liquidity clusters
        current_trend: BULLISH, BEARISH, or NEUTRAL
        volatility: Current volatility (as decimal)

    Returns:
        Dictionary with sweep predictions for each cluster
    """
    predictions = []

    for cluster in clusters:
        # Calculate distance percentage
        distance = abs(cluster.price_level - current_price) / current_price

        # Base probability from distance (inverse relationship)
        # Closer clusters have higher probability
        distance_score = max(0, 1 - (distance / 0.05))  # 5% max distance

        # Density score influence (higher density = more attractive)
        density_score = cluster.density_score

        # Trend influence
        trend_multiplier = 1.0
        if current_trend == "BULLISH" and cluster.price_level > current_price:
            trend_multiplier = 1.3  # Uptrends more likely to sweep above
        elif current_trend == "BEARISH" and cluster.price_level < current_price:
            trend_multiplier = 1.3  # Downtrends more likely to sweep below
        elif current_trend == "BULLISH" and cluster.price_level < current_price:
            trend_multiplier = 0.7  # Less likely to sweep down in uptrend
        elif current_trend == "BEARISH" and cluster.price_level > current_price:
            trend_multiplier = 0.7  # Less likely to sweep up in downtrend

        # Volatility influence (higher vol = more sweeps)
        vol_multiplier = 1 + (volatility * 10)  # 2% vol = 1.2x multiplier

        # Type influence (round numbers are prime targets)
        type_multiplier = 1.0
        if cluster.cluster_type == "ROUND_NUMBER":
            type_multiplier = 1.2
        elif cluster.cluster_type == "PREVIOUS_HIGH_LOW":
            type_multiplier = 1.1

        # Calculate final probability
        probability = (
            distance_score * 0.4 +
            density_score * 0.3 +
            0.2  # Base probability
        ) * trend_multiplier * vol_multiplier * type_multiplier

        # Clamp to 0-1
        probability = max(0, min(1, probability))

        # Determine expected impulse (price move after sweep)
        expected_impulse = _estimate_sweep_impulse(cluster, clusters, volatility)

        # Find cascade targets
        cascade_targets = _find_cascade_targets(cluster, clusters, current_price)

        # Determine time horizon
        time_horizon = _determine_time_horizon(distance, volatility)

        predictions.append({
            "price_level": cluster.price_level,
            "cluster_type": cluster.cluster_type,
            "probability": round(probability, 3),
            "expected_impulse_pct": round(expected_impulse * 100, 2),
            "cascade_targets": cascade_targets,
            "time_horizon": time_horizon,
            "distance_from_current_pct": round(distance * 100, 2),
            "density_score": round(cluster.density_score, 3),
        })

    # Sort by probability
    predictions.sort(key=lambda p: p["probability"], reverse=True)

    return {
        "current_price": current_price,
        "trend": current_trend,
        "volatility_pct": round(volatility * 100, 2),
        "predictions": predictions[:10],  # Top 10
        "timestamp": datetime.utcnow().isoformat(),
    }


def calculate_cascade_risk(
    triggered_stop: LiquidityCluster,
    all_clusters: List[LiquidityCluster],
    current_price: float,
) -> Dict[str, Any]:
    """
    Calculate cascade risk if a specific stop cluster is triggered.

    When one cluster triggers, it can cause a cascade by:
    1. Triggering stops at adjacent levels
    2. Causing forced liquidations
    3. Creating momentum that pushes price to next cluster

    Args:
        triggered_stop: The cluster that was just triggered
        all_clusters: All detected clusters
        current_price: Current market price

    Returns:
        Dictionary with cascade risk assessment
    """
    cascade_levels = []
    total_cascade_volume = 0

    # Find clusters in the direction of the sweep
    is_upward_sweep = triggered_stop.price_level > current_price

    for cluster in all_clusters:
        if cluster.price_level == triggered_stop.price_level:
            continue

        # Check if this cluster would be cascaded into
        if is_upward_sweep and cluster.price_level > triggered_stop.price_level:
            distance = cluster.price_level - triggered_stop.price_level
            if distance <= current_price * 0.02:  # Within 2%
                cascade_levels.append({
                    "price_level": cluster.price_level,
                    "distance_pct": round((distance / current_price) * 100, 2),
                    "density_score": cluster.density_score,
                    "type": cluster.cluster_type,
                })
                if cluster.estimated_volume:
                    total_cascade_volume += cluster.estimated_volume

        elif not is_upward_sweep and cluster.price_level < triggered_stop.price_level:
            distance = triggered_stop.price_level - cluster.price_level
            if distance <= current_price * 0.02:  # Within 2%
                cascade_levels.append({
                    "price_level": cluster.price_level,
                    "distance_pct": round((distance / current_price) * 100, 2),
                    "density_score": cluster.density_score,
                    "type": cluster.cluster_type,
                })
                if cluster.estimated_volume:
                    total_cascade_volume += cluster.estimated_volume

    # Calculate overall cascade risk
    num_cascades = len(cascade_levels)
    avg_density = np.mean([c["density_score"] for c in cascade_levels]) if cascade_levels else 0

    # Risk assessment
    if num_cascades >= 3 and avg_density > 0.6:
        risk_level = "CRITICAL"
    elif num_cascades >= 2 and avg_density > 0.5:
        risk_level = "HIGH"
    elif num_cascades >= 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Estimate maximum excursion
    max_excursion = 0
    if cascade_levels:
        if is_upward_sweep:
            max_excursion = cascade_levels[-1]["price_level"] - current_price
        else:
            max_excursion = current_price - cascade_levels[-1]["price_level"]

    return {
        "triggered_level": triggered_stop.price_level,
        "cascade_levels": cascade_levels,
        "cascade_count": num_cascades,
        "total_estimated_volume": total_cascade_volume,
        "average_density_score": round(avg_density, 3),
        "risk_level": risk_level,
        "max_excursion_pct": round((max_excursion / current_price) * 100, 2),
        "sweep_direction": "UP" if is_upward_sweep else "DOWN",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _detect_round_numbers(current_price: float, price_range: float) -> List[LiquidityCluster]:
    """Detect round number psychological levels."""
    clusters = []

    # Determine appropriate round number increment based on price
    if current_price >= 10000:
        increments = [1000, 5000, 10000]
    elif current_price >= 1000:
        increments = [100, 500, 1000]
    elif current_price >= 100:
        increments = [10, 50, 100]
    else:
        increments = [1, 5, 10]

    for increment in increments:
        # Find round numbers near current price
        base = int(current_price / increment) * increment

        # Check levels above and below
        for offset in [-3, -2, -1, 0, 1, 2, 3]:
            level = base + (offset * increment)
            if level <= 0:
                continue

            distance_pct = abs(level - current_price) / current_price
            if distance_pct <= 0.10:  # Within 10%
                clusters.append(
                    LiquidityCluster(
                        price_level=float(level),
                        density_score=0.5,  # Will be recalculated
                        cluster_type="ROUND_NUMBER",
                        metadata={"increment": increment},
                    )
                )

    return clusters


def _detect_swing_points(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int,
) -> List[LiquidityCluster]:
    """Detect previous swing highs and lows."""
    clusters = []
    window = min(5, len(closes) // 4)

    # Find swing highs
    for i in range(window, len(highs) - window):
        is_swing_high = all(highs[i] >= highs[j] for j in range(i - window, i + window + 1))
        if is_swing_high:
            clusters.append(
                LiquidityCluster(
                    price_level=highs[i],
                    density_score=0.4,
                    cluster_type="PREVIOUS_HIGH",
                )
            )

    # Find swing lows
    for i in range(window, len(lows) - window):
        is_swing_low = all(lows[i] <= lows[j] for j in range(i - window, i + window + 1))
        if is_swing_low:
            clusters.append(
                LiquidityCluster(
                    price_level=lows[i],
                    density_score=0.4,
                    cluster_type="PREVIOUS_LOW",
                )
            )

    return clusters


def _detect_support_resistance(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
    window: int = 20,
) -> List[LiquidityCluster]:
    """Detect support and resistance levels based on price pivots."""
    clusters = []

    if len(closes) < window * 2:
        return clusters

    # Use pivots to find S/R levels
    pivots = []
    for i in range(window, len(closes) - window):
        pivot_high = max(highs[i - window:i + window])
        pivot_low = min(lows[i - window:i + window])
        pivots.append((pivot_high, pivot_low))

    # Cluster similar pivots
    high_levels = _cluster_similar_values([p[0] for p in pivots], tolerance=0.01)
    low_levels = _cluster_similar_values([p[1] for p in pivots], tolerance=0.01)

    for level in high_levels:
        clusters.append(
            LiquidityCluster(
                price_level=level,
                density_score=0.3,
                cluster_type="RESISTANCE",
            )
        )

    for level in low_levels:
        clusters.append(
            LiquidityCluster(
                price_level=level,
                density_score=0.3,
                cluster_type="SUPPORT",
            )
        )

    return clusters


def _detect_consolidation_breakouts(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    min_periods: int = 10,
) -> List[LiquidityCluster]:
    """Detect stops above/below consolidation ranges."""
    clusters = []

    # Look for recent consolidation periods
    i = 0
    while i < len(closes) - min_periods:
        # Check for tight range
        range_high = max(highs[i:i + min_periods])
        range_low = min(lows[i:i + min_periods])
        range_pct = (range_high - range_low) / range_low

        if range_pct < 0.02:  # Less than 2% range = consolidation
            # Add stops above and below range
            clusters.append(
                LiquidityCluster(
                    price_level=range_high * 1.005,  # Just above
                    density_score=0.35,
                    cluster_type="CONSOLIDATION_TOP",
                )
            )
            clusters.append(
                LiquidityCluster(
                    price_level=range_low * 0.995,  # Just below
                    density_score=0.35,
                    cluster_type="CONSOLIDATION_BOTTOM",
                )
            )
            i += min_periods  # Skip ahead
        else:
            i += 1

    return clusters


def _detect_consolidation_voids(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
    min_gap_size: float,
) -> List[LiquidityVoid]:
    """Detect potential voids from consolidation zones."""
    voids = []
    window = 10

    for i in range(window, len(closes) - window):
        # Check for consolidation (low volatility, low volume)
        period_highs = highs[i - window:i + window]
        period_lows = lows[i - window:i + window]
        period_volumes = volumes[i - window:i + window]

        volatility = (max(period_highs) - min(period_lows)) / np.mean(period_lows)
        avg_volume = np.mean(period_volumes)

        if volatility < 0.01 and avg_volume < np.mean(volumes) * 0.7:
            # This could be a void if price breaks out
            void_size_pct = volatility * 100
            if void_size_pct >= min_gap_size * 100:
                voids.append(
                    LiquidityVoid(
                        start_price=float(min(period_lows)),
                        end_price=float(max(period_highs)),
                        void_size=void_size_pct,
                        risk_level="MEDIUM" if void_size_pct > 3 else "LOW",
                    )
                )

    return voids


def _merge_nearby_clusters(
    clusters: List[LiquidityCluster],
    tolerance: float = 0.005,  # 0.5%
) -> List[LiquidityCluster]:
    """Merge clusters that are very close to each other."""
    if not clusters:
        return []

    # Sort by price level
    sorted_clusters = sorted(clusters, key=lambda c: c.price_level)
    merged = [sorted_clusters[0]]

    for cluster in sorted_clusters[1:]:
        last = merged[-1]
        distance = abs(cluster.price_level - last.price_level) / last.price_level

        if distance <= tolerance:
            # Merge: use higher density and combine metadata
            last.density_score = max(last.density_score, cluster.density_score)
            last.estimated_volume = (last.estimated_volume or 0) + (cluster.estimated_volume or 0)
            if cluster.cluster_type not in last.metadata.get("types", []):
                if "types" not in last.metadata:
                    last.metadata["types"] = [last.cluster_type]
                last.metadata["types"].append(cluster.cluster_type)
        else:
            merged.append(cluster)

    return merged


def _calculate_cluster_density(
    cluster: LiquidityCluster,
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
) -> float:
    """Calculate density score for a cluster based on multiple factors."""
    score = 0.0

    # 1. Price touch frequency (how often price was near this level)
    touches = sum(
        1 for h, l in zip(highs, lows)
        if l <= cluster.price_level <= h
    )
    touch_frequency = touches / len(closes) if closes else 0
    score += min(0.4, touch_frequency * 2)

    # 2. Volume near level (more volume = more interest)
    near_level_volumes = [
        v for h, l, v in zip(highs, lows, volumes)
        if abs(h - cluster.price_level) / cluster.price_level < 0.01 or
           abs(l - cluster.price_level) / cluster.price_level < 0.01
    ]
    avg_volume_near = np.mean(near_level_volumes) if near_level_volumes else 0
    avg_volume_all = np.mean(volumes) if volumes else 1
    volume_ratio = avg_volume_near / avg_volume_all if avg_volume_all > 0 else 0
    score += min(0.3, volume_ratio * 0.3)

    # 3. Type base score
    type_scores = {
        "ROUND_NUMBER": 0.2,
        "PREVIOUS_HIGH": 0.15,
        "PREVIOUS_LOW": 0.15,
        "RESISTANCE": 0.1,
        "SUPPORT": 0.1,
        "CONSOLIDATION_TOP": 0.12,
        "CONSOLIDATION_BOTTOM": 0.12,
    }
    score += type_scores.get(cluster.cluster_type, 0.1)

    # 4. Recency bonus (recent levels are more relevant)
    # (Already captured in touch frequency)

    return min(1.0, score)


def _assess_void_risk(gap_size: float, volume: float, low_volume_threshold: float) -> str:
    """Assess risk level of a liquidity void."""
    if gap_size > 0.05:  # More than 5% gap
        return "HIGH"
    elif gap_size > 0.02 or volume < low_volume_threshold:
        return "MEDIUM"
    else:
        return "LOW"


def _cluster_similar_values(values: List[float], tolerance: float) -> List[float]:
    """Cluster similar values and return representative values."""
    if not values:
        return []

    sorted_values = sorted(values)
    clusters = [[sorted_values[0]]]

    for v in sorted_values[1:]:
        last_cluster = clusters[-1]
        if abs(v - np.mean(last_cluster)) / np.mean(last_cluster) <= tolerance:
            last_cluster.append(v)
        else:
            clusters.append([v])

    return [float(np.mean(c)) for c in clusters]


def _estimate_sweep_impulse(
    cluster: LiquidityCluster,
    all_clusters: List[LiquidityCluster],
    volatility: float,
) -> float:
    """Estimate expected price impulse after sweeping a cluster."""
    # Base impulse from density (more stops = stronger impulse)
    base_impulse = cluster.density_score * 0.01  # Up to 1%

    # Add volatility component
    vol_impulse = volatility * 0.5

    # Check for next cluster (could amplify or dampen)
    next_clusters = sorted(
        [c for c in all_clusters if c.price_level != cluster.price_level],
        key=lambda c: abs(c.price_level - cluster.price_level)
    )

    if next_clusters:
        next_cluster = next_clusters[0]
        distance = abs(next_cluster.price_level - cluster.price_level) / cluster.price_level
        if distance < 0.01:  # Very close to another cluster
            base_impulse *= 1.5  # Amplified

    return base_impulse + vol_impulse


def _find_cascade_targets(
    cluster: LiquidityCluster,
    all_clusters: List[LiquidityCluster],
    current_price: float,
) -> List[float]:
    """Find potential cascade targets if this cluster is triggered."""
    is_above = cluster.price_level > current_price
    targets = []

    for other in all_clusters:
        if other.price_level == cluster.price_level:
            continue

        if is_above and other.price_level > cluster.price_level:
            distance = (other.price_level - cluster.price_level) / cluster.price_level
            if distance <= 0.02:  # Within 2%
                targets.append(other.price_level)
        elif not is_above and other.price_level < cluster.price_level:
            distance = (cluster.price_level - other.price_level) / cluster.price_level
            if distance <= 0.02:  # Within 2%
                targets.append(other.price_level)

    return sorted(targets)[:5]  # Max 5 targets


def _determine_time_horizon(distance_pct: float, volatility: float) -> str:
    """Determine likely time horizon for a sweep."""
    # Very close clusters = immediate
    if distance_pct < 0.01:
        return "IMMEDIATE"
    # High volatility = shorter term
    elif volatility > 0.03:
        return "SHORT_TERM"
    # Farther clusters = medium term
    elif distance_pct < 0.05:
        return "SHORT_TERM"
    else:
        return "MEDIUM_TERM"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_liquidity_map(
    symbol: str,
    lookback_periods: int = 100,
) -> Dict[str, Any]:
    """
    Get complete liquidity map for a symbol.

    Combines cluster detection, void detection, and sweep predictions
    into a comprehensive liquidity analysis.

    Args:
        symbol: Trading symbol
        lookback_periods: Number of periods to analyze

    Returns:
        Complete liquidity map with all analysis
    """
    # Get price data
    price_data = get_prices_from_db(symbol, limit=lookback_periods)

    if not price_data:
        return {
            "symbol": symbol,
            "error": "No price data available",
            "timestamp": datetime.utcnow().isoformat(),
        }

    closes = [float(p["close"]) for p in price_data]
    current_price = closes[-1]

    # Calculate volatility
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
    clusters = detect_stop_clusters(symbol, price_data, lookback_periods)

    # Detect voids
    voids = detect_liquidity_voids(symbol, price_data)

    # Predict sweeps
    sweep_predictions = predict_sweep_probability(
        current_price, clusters, trend, volatility
    )

    return {
        "symbol": symbol,
        "current_price": current_price,
        "trend": trend,
        "volatility_pct": round(volatility * 100, 2),
        "clusters": [
            {
                "price_level": c.price_level,
                "density_score": round(c.density_score, 3),
                "type": c.cluster_type,
                "distance_pct": round(abs(c.price_level - current_price) / current_price * 100, 2),
            }
            for c in clusters[:10]
        ],
        "voids": [
            {
                "start_price": v.start_price,
                "end_price": v.end_price,
                "size_pct": round(v.void_size, 2),
                "risk_level": v.risk_level,
            }
            for v in voids[:10]
        ],
        "sweep_predictions": sweep_predictions,
        "timestamp": datetime.utcnow().isoformat(),
    }
