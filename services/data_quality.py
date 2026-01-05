"""
Data Quality Monitoring System for Market Data.

Monitors incoming market data for quality issues including:
- Stale data detection
- Price outlier detection
- Cross-exchange price discrepancies
- Missing data detection
- Data consistency checks
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class QualityIssue(Enum):
    """Types of data quality issues."""
    STALE_DATA = "stale_data"
    PRICE_OUTLIER = "price_outlier"
    PRICE_DISCREPANCY = "price_discrepancy"
    MISSING_DATA = "missing_data"
    ZERO_VOLUME = "zero_volume"
    NEGATIVE_PRICE = "negative_price"
    INVALID_OHLC = "invalid_ohlc"
    SPURIOUS_VOLUME = "spurious_volume"


class Severity(Enum):
    """Severity levels for quality issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityAlert:
    """Represents a data quality alert."""
    issue_type: QualityIssue
    severity: Severity
    symbol: str
    exchange: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "resolved": self.resolved
        }


@dataclass
class DataQualityScore:
    """Quality score for market data."""
    symbol: str
    exchange: str
    overall_score: float  # 0-100
    freshness: float
    accuracy: float
    completeness: float
    consistency: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "overall_score": self.overall_score,
            "freshness": self.freshness,
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "consistency": self.consistency,
            "timestamp": self.timestamp.isoformat()
        }


class DataQualityMonitor:
    """
    Monitor and validate market data quality.

    Tracks data from multiple sources and generates alerts for quality issues.
    """

    # Default thresholds
    DEFAULT_STALE_THRESHOLD = timedelta(minutes=5)
    DEFAULT_PRICE_DEVIATION_THRESHOLD = 0.05  # 5%
    DEFAULT_VOLUME_SPIKE_THRESHOLD = 10.0  # 10x normal
    DEFAULT_MIN_VOLUME = Decimal("0.001")

    def __init__(
        self,
        stale_threshold: Optional[timedelta] = None,
        price_deviation_threshold: float = 0.05,
        volume_spike_threshold: float = 10.0
    ):
        """
        Initialize the data quality monitor.

        Args:
            stale_threshold: Time threshold for considering data stale
            price_deviation_threshold: Percentage threshold for price deviation
            volume_spike_threshold: Multiplier for detecting volume spikes
        """
        self.stale_threshold = stale_threshold or self.DEFAULT_STALE_THRESHOLD
        self.price_deviation_threshold = price_deviation_threshold
        self.volume_spike_threshold = volume_spike_threshold

        # Track historical data for comparison
        self.price_history: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)
        self.volume_history: Dict[str, List[Tuple[datetime, Decimal]]] = defaultdict(list)

        # Track last update times
        self.last_updates: Dict[str, datetime] = {}

        # Active alerts
        self.active_alerts: List[QualityAlert] = []

        # Quality scores
        self.quality_scores: Dict[str, DataQualityScore] = {}

        logger.info(
            f"DataQualityMonitor initialized with thresholds: "
            f"stale={self.stale_threshold}, "
            f"price_dev={self.price_deviation_threshold}, "
            f"vol_spike={self.volume_spike_threshold}"
        )

    def check_ticker_quality(
        self,
        ticker: Dict[str, Any],
        exchange: str,
        reference_price: Optional[Decimal] = None
    ) -> List[QualityAlert]:
        """
        Check quality of a ticker data point.

        Args:
            ticker: Ticker data dictionary
            exchange: Exchange name
            reference_price: Optional reference price for comparison

        Returns:
            List of quality alerts (empty if no issues)
        """
        alerts = []
        symbol = ticker.get("symbol", "UNKNOWN")
        price = ticker.get("price")
        volume = ticker.get("volume_24h")
        timestamp = ticker.get("timestamp", datetime.utcnow())

        # 1. Check for stale data
        if isinstance(timestamp, datetime):
            age = datetime.utcnow() - timestamp
            if age > self.stale_threshold:
                alerts.append(QualityAlert(
                    issue_type=QualityIssue.STALE_DATA,
                    severity=Severity.HIGH if age > self.stale_threshold * 2 else Severity.MEDIUM,
                    symbol=symbol,
                    exchange=exchange,
                    message=f"Data is {age.total_seconds()/60:.1f} minutes old",
                    data={"age_seconds": age.total_seconds()}
                ))

        # 2. Check for negative prices
        if price is not None and price < 0:
            alerts.append(QualityAlert(
                issue_type=QualityIssue.NEGATIVE_PRICE,
                severity=Severity.CRITICAL,
                symbol=symbol,
                exchange=exchange,
                message=f"Negative price detected: {price}",
                data={"price": str(price)}
            ))

        # 3. Check for zero volume
        if volume is not None and volume == 0:
            alerts.append(QualityAlert(
                issue_type=QualityIssue.ZERO_VOLUME,
                severity=Severity.LOW,
                symbol=symbol,
                exchange=exchange,
                message="Zero trading volume in 24h period",
                data={"volume": str(volume)}
            ))

        # 4. Check for price outliers using historical data
        if price is not None and symbol in self.price_history:
            historical_prices = [p for _, p in self.price_history[symbol][-20:]]  # Last 20 points
            if historical_prices:
                mean_price = statistics.mean(historical_prices)
                std_price = statistics.stdev(historical_prices) if len(historical_prices) > 1 else 0

                # Z-score check
                if std_price > 0:
                    z_score = abs((float(price) - mean_price) / std_price)
                    if z_score > 3:  # 3 standard deviations
                        alerts.append(QualityAlert(
                            issue_type=QualityIssue.PRICE_OUTLIER,
                            severity=Severity.HIGH,
                            symbol=symbol,
                            exchange=exchange,
                            message=f"Price outlier detected (z-score: {z_score:.2f})",
                            data={
                                "price": str(price),
                                "mean": str(mean_price),
                                "std": str(std_price),
                                "z_score": z_score
                            }
                        ))

        # 5. Check against reference price (e.g., from other exchanges)
        if reference_price is not None and price is not None:
            deviation = abs((price - reference_price) / reference_price)
            if deviation > self.price_deviation_threshold:
                alerts.append(QualityAlert(
                    issue_type=QualityIssue.PRICE_DISCREPANCY,
                    severity=Severity.MEDIUM if deviation < self.price_deviation_threshold * 2 else Severity.HIGH,
                    symbol=symbol,
                    exchange=exchange,
                    message=f"Price deviation from reference: {deviation*100:.2f}%",
                    data={
                        "price": str(price),
                        "reference_price": str(reference_price),
                        "deviation_percent": deviation * 100
                    }
                ))

        # 6. Check for volume spikes
        if volume is not None and volume > 0 and symbol in self.volume_history:
            historical_volumes = [v for _, v in self.volume_history[symbol][-20:]]
            if historical_volumes:
                median_volume = statistics.median(historical_volumes)
                if median_volume > 0 and volume > median_volume * self.volume_spike_threshold:
                    alerts.append(QualityAlert(
                        issue_type=QualityIssue.SPURIOUS_VOLUME,
                        severity=Severity.MEDIUM,
                        symbol=symbol,
                        exchange=exchange,
                        message=f"Volume spike detected: {volume/median_volume:.1f}x median",
                        data={
                            "volume": str(volume),
                            "median_volume": str(median_volume),
                            "spike_multiplier": float(volume / median_volume)
                        }
                    ))

        # Update tracking data
        if price is not None:
            self.price_history[symbol].append((timestamp, price))
            # Keep only last 100 points
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]

        if volume is not None:
            self.volume_history[symbol].append((timestamp, volume))
            if len(self.volume_history[symbol]) > 100:
                self.volume_history[symbol] = self.volume_history[symbol][-100:]

        self.last_updates[f"{exchange}:{symbol}"] = timestamp

        # Store alerts
        self.active_alerts.extend(alerts)

        return alerts

    def check_ohlcv_quality(
        self,
        candles: List[Dict[str, Any]],
        exchange: str,
        symbol: str
    ) -> List[QualityAlert]:
        """
        Check quality of OHLCV candle data.

        Args:
            candles: List of OHLCV candles
            exchange: Exchange name
            symbol: Trading symbol

        Returns:
            List of quality alerts
        """
        alerts = []

        if not candles:
            alerts.append(QualityAlert(
                issue_type=QualityIssue.MISSING_DATA,
                severity=Severity.MEDIUM,
                symbol=symbol,
                exchange=exchange,
                message="No OHLCV data available"
            ))
            return alerts

        for i, candle in enumerate(candles):
            timestamp = candle.get("timestamp")
            open_price = candle.get("open")
            high = candle.get("high")
            low = candle.get("low")
            close = candle.get("close")
            volume = candle.get("volume")

            # Check for invalid OHLC relationships
            if all([open_price, high, low, close]):
                if high < max(open_price, close_price) or low > min(open_price, close_price):
                    alerts.append(QualityAlert(
                        issue_type=QualityIssue.INVALID_OHLC,
                        severity=Severity.HIGH,
                        symbol=symbol,
                        exchange=exchange,
                        message=f"Invalid OHLC relationship at index {i}",
                        data={
                            "index": i,
                            "timestamp": timestamp.isoformat() if timestamp else None,
                            "open": str(open_price),
                            "high": str(high),
                            "low": str(low),
                            "close": str(close_price)
                        }
                    ))

            # Check for zero volume in individual candles
            if volume == 0 and i < len(candles) - 1:  # Skip current candle
                alerts.append(QualityAlert(
                    issue_type=QualityIssue.MISSING_DATA,
                    severity=Severity.LOW,
                    symbol=symbol,
                    exchange=exchange,
                    message=f"Zero volume candle at index {i}",
                    data={"index": i, "timestamp": timestamp.isoformat() if timestamp else None}
                ))

        self.active_alerts.extend(alerts)
        return alerts

    def check_cross_exchange_prices(
        self,
        price_data: Dict[str, Dict[str, Any]]
    ) -> List[QualityAlert]:
        """
        Check for price discrepancies across exchanges.

        Args:
            price_data: Dictionary of exchange -> ticker data

        Returns:
            List of quality alerts
        """
        alerts = []

        if len(price_data) < 2:
            return alerts

        # Extract prices
        prices = {
            exchange: data.get("price", Decimal("0"))
            for exchange, data in price_data.items()
            if data.get("price", Decimal("0")) > 0
        }

        if not prices:
            return alerts

        # Calculate statistics
        mean_price = statistics.mean([float(p) for p in prices.values()])
        std_price = statistics.stdev([float(p) for p in prices.values()]) if len(prices) > 1 else 0

        # Check each exchange
        for exchange, price in prices.items():
            deviation = abs((price - Decimal(str(mean_price))) / Decimal(str(mean_price)))

            if deviation > self.price_deviation_threshold:
                alerts.append(QualityAlert(
                    issue_type=QualityIssue.PRICE_DISCREPANCY,
                    severity=Severity.MEDIUM,
                    symbol=price_data.get(exchange, {}).get("symbol", "UNKNOWN"),
                    exchange=exchange,
                    message=f"Price deviates {deviation*100:.2f}% from cross-exchange average",
                    data={
                        "price": str(price),
                        "mean_price": str(mean_price),
                        "deviation_percent": deviation * 100,
                        "all_prices": {ex: str(p) for ex, p in prices.items()}
                    }
                ))

        self.active_alerts.extend(alerts)
        return alerts

    def calculate_quality_score(
        self,
        symbol: str,
        exchange: str
    ) -> DataQualityScore:
        """
        Calculate overall quality score for a symbol/exchange.

        Args:
            symbol: Trading symbol
            exchange: Exchange name

        Returns:
            DataQualityScore with individual metrics
        """
        # Get recent alerts for this symbol/exchange
        recent_alerts = [
            a for a in self.active_alerts
            if a.symbol == symbol and a.exchange == exchange
            and not a.resolved
            and (datetime.utcnow() - a.timestamp) < timedelta(hours=1)
        ]

        # Calculate freshness score
        key = f"{exchange}:{symbol}"
        last_update = self.last_updates.get(key)
        if last_update:
            age = datetime.utcnow() - last_update
            freshness = max(0, 100 - (age.total_seconds() / self.stale_threshold.total_seconds() * 100))
        else:
            freshness = 0

        # Calculate accuracy score (based on alerts)
        critical_count = sum(1 for a in recent_alerts if a.severity == Severity.CRITICAL)
        high_count = sum(1 for a in recent_alerts if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in recent_alerts if a.severity == Severity.MEDIUM)

        accuracy = max(0, 100 - (critical_count * 50 + high_count * 20 + medium_count * 5))

        # Calculate completeness score (based on data history)
        price_points = len(self.price_history.get(symbol, []))
        completeness = min(100, price_points)

        # Calculate consistency score (price stability)
        if symbol in self.price_history and len(self.price_history[symbol]) > 5:
            prices = [float(p) for _, p in self.price_history[symbol][-20:]]
            if prices:
                cv = (statistics.stdev(prices) / statistics.mean(prices)) if statistics.mean(prices) > 0 else 0
                consistency = max(0, 100 - (cv * 100))
            else:
                consistency = 0
        else:
            consistency = 50  # Neutral score if insufficient data

        # Overall score (weighted average)
        overall = (freshness * 0.3 + accuracy * 0.4 + completeness * 0.15 + consistency * 0.15)

        score = DataQualityScore(
            symbol=symbol,
            exchange=exchange,
            overall_score=round(overall, 2),
            freshness=round(freshness, 2),
            accuracy=round(accuracy, 2),
            completeness=round(completeness, 2),
            consistency=round(consistency, 2)
        )

        self.quality_scores[key] = score
        return score

    def get_active_alerts(
        self,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        severity: Optional[Severity] = None,
        min_severity: Optional[Severity] = None
    ) -> List[QualityAlert]:
        """
        Get active alerts with optional filtering.

        Args:
            symbol: Filter by symbol
            exchange: Filter by exchange
            severity: Filter by exact severity
            min_severity: Filter by minimum severity

        Returns:
            List of active alerts
        """
        alerts = [
            a for a in self.active_alerts
            if not a.resolved
            and (datetime.utcnow() - a.timestamp) < timedelta(hours=24)  # Last 24h
        ]

        if symbol:
            alerts = [a for a in alerts if a.symbol == symbol]
        if exchange:
            alerts = [a for a in alerts if a.exchange == exchange]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if min_severity:
            severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
            min_idx = severity_order.index(min_severity)
            alerts = [a for a in alerts if severity_order.index(a.severity) >= min_idx]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def resolve_alerts(self, alert_ids: Optional[List[int]] = None):
        """
        Mark alerts as resolved.

        Args:
            alert_ids: List of alert indices to resolve (resolves all if None)
        """
        if alert_ids is None:
            # Resolve all alerts older than 1 hour
            cutoff = datetime.utcnow() - timedelta(hours=1)
            for alert in self.active_alerts:
                if alert.timestamp < cutoff:
                    alert.resolved = True
        else:
            for idx in alert_ids:
                if idx < len(self.active_alerts):
                    self.active_alerts[idx].resolved = True

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of monitoring status.

        Returns:
            Dictionary with monitoring statistics
        """
        recent_alerts = self.get_active_alerts()

        severity_counts = defaultdict(int)
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1

        return {
            "total_alerts": len(recent_alerts),
            "severity_breakdown": dict(severity_counts),
            "symbols_tracked": len(self.price_history),
            "exchanges_tracked": len(set(ex.split(":")[0] for ex in self.last_updates.keys())),
            "last_updated": datetime.utcnow().isoformat(),
            "avg_quality_score": statistics.mean([s.overall_score for s in self.quality_scores.values()]) if self.quality_scores else 0
        }

    def cleanup_old_data(self, max_age: timedelta = timedelta(days=7)):
        """
        Clean up old data to prevent memory bloat.

        Args:
            max_age: Maximum age of data to keep
        """
        cutoff = datetime.utcnow() - max_age

        # Clean price history
        for symbol in list(self.price_history.keys()):
            self.price_history[symbol] = [
                (ts, price) for ts, price in self.price_history[symbol]
                if ts > cutoff
            ]
            if not self.price_history[symbol]:
                del self.price_history[symbol]

        # Clean volume history
        for symbol in list(self.volume_history.keys()):
            self.volume_history[symbol] = [
                (ts, vol) for ts, vol in self.volume_history[symbol]
                if ts > cutoff
            ]
            if not self.volume_history[symbol]:
                del self.volume_history[symbol]

        # Clean old alerts
        self.active_alerts = [
            a for a in self.active_alerts
            if a.timestamp > cutoff or not a.resolved
        ]

        logger.info(f"Cleaned up data older than {max_age}")


# Global quality monitor instance
_quality_monitor: Optional[DataQualityMonitor] = None


def get_quality_monitor() -> DataQualityMonitor:
    """
    Get the global data quality monitor instance.

    Returns:
        DataQualityMonitor singleton
    """
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = DataQualityMonitor()
    return _quality_monitor
