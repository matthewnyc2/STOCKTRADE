"""
Historical Data Manager for Backfill and Gap Detection.

Manages historical data acquisition, including:
- Initial bulk import/backfill
- Gap detection and filling
- Data retention policies
- Time-series optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from sqlalchemy import func, and_, or_

from database.connection import get_db_session
from database.models.price import PriceModel

logger = logging.getLogger(__name__)


class DataRetentionPolicy(Enum):
    """Data retention policies."""

    KEEP_ALL = "keep_all"
    ONE_YEAR = "one_year"
    SIX_MONTHS = "six_months"
    THREE_MONTHS = "three_months"
    ONE_MONTH = "one_month"


@dataclass
class BackfillConfig:
    """Configuration for historical data backfill."""

    symbols: List[str]
    timeframe: str = "1h"
    lookback_days: int = 365
    batch_size: int = 1000
    max_concurrent_requests: int = 5
    delay_between_requests: float = 0.1  # seconds


@dataclass
class GapInfo:
    """Information about a data gap."""

    symbol: str
    timeframe: str
    gap_start: datetime
    gap_end: datetime
    missing_periods: int
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "gap_start": self.gap_start.isoformat(),
            "gap_end": self.gap_end.isoformat(),
            "missing_periods": self.missing_periods,
            "duration_hours": (self.gap_end - self.gap_start).total_seconds() / 3600,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class BackfillStats:
    """Statistics for backfill operations."""

    total_symbols: int = 0
    completed_symbols: int = 0
    total_periods_requested: int = 0
    total_periods_fetched: int = 0
    total_periods_stored: int = 0
    gaps_detected: int = 0
    gaps_filled: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate operation duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_periods_requested == 0:
            return 0.0
        return self.total_periods_fetched / self.total_periods_requested

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_symbols": self.total_symbols,
            "completed_symbols": self.completed_symbols,
            "total_periods_requested": self.total_periods_requested,
            "total_periods_fetched": self.total_periods_fetched,
            "total_periods_stored": self.total_periods_stored,
            "gaps_detected": self.gaps_detected,
            "gaps_filled": self.gaps_filled,
            "errors": self.errors,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
        }


class GapDetector:
    """
    Detects gaps in historical price data.

    Identifies missing time periods in OHLCV data for backfilling.
    """

    def __init__(self):
        """Initialize gap detector."""
        # Timeframe intervals in minutes
        self.intervals = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }

        logger.info("GapDetector initialized")

    def detect_gaps(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[GapInfo]:
        """
        Detect gaps in price data for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Time frame (1m, 5m, 1h, 1d, etc.)
            start: Start of range to check
            end: End of range to check

        Returns:
            List of detected gaps
        """
        session = get_db_session().__enter__()

        try:
            # Get interval in minutes
            interval_minutes = self.intervals.get(timeframe, 60)

            # Set default range if not provided
            if not end:
                end = datetime.utcnow()
            if not start:
                start = end - timedelta(days=30)

            # Query existing data
            query = (
                session.query(PriceModel.timestamp, PriceModel.symbol)
                .filter(
                    PriceModel.symbol == symbol.upper(),
                    PriceModel.timestamp >= start,
                    PriceModel.timestamp <= end,
                )
                .order_by(PriceModel.timestamp)
            )

            results = query.all()

            if not results:
                # No data at all - entire range is a gap
                return [
                    GapInfo(
                        symbol=symbol,
                        timeframe=timeframe,
                        gap_start=start,
                        gap_end=end,
                        missing_periods=int((end - start).total_seconds() / 60 / interval_minutes),
                    )
                ]

            # Detect gaps
            gaps = []
            expected_time = start

            for i, (timestamp, _) in enumerate(results):
                # Calculate difference between expected and actual
                diff = (timestamp - expected_time).total_seconds() / 60

                # If difference is more than 1.5x the interval, it's a gap
                if diff > interval_minutes * 1.5:
                    gap_end = timestamp
                    missing_periods = int(diff / interval_minutes)

                    gaps.append(
                        GapInfo(
                            symbol=symbol,
                            timeframe=timeframe,
                            gap_start=expected_time,
                            gap_end=gap_end,
                            missing_periods=missing_periods,
                        )
                    )

                # Set expected time for next period
                expected_time = timestamp + timedelta(minutes=interval_minutes)

            # Check for gap after last data point
            if expected_time < end:
                gaps.append(
                    GapInfo(
                        symbol=symbol,
                        timeframe=timeframe,
                        gap_start=expected_time,
                        gap_end=end,
                        missing_periods=int(
                            (end - expected_time).total_seconds() / 60 / interval_minutes
                        ),
                    )
                )

            logger.info(f"Detected {len(gaps)} gaps for {symbol} {timeframe}")
            return gaps

        finally:
            session.close()

    def detect_gaps_batch(
        self,
        symbols: List[str],
        timeframes: List[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, List[GapInfo]]:
        """
        Detect gaps for multiple symbols and timeframes.

        Args:
            symbols: List of trading symbols
            timeframes: List of time frames
            start: Start of range to check
            end: End of range to check

        Returns:
            Dictionary of symbol:timeframe -> gaps
        """
        all_gaps = {}

        for symbol in symbols:
            for timeframe in timeframes:
                key = f"{symbol}:{timeframe}"
                gaps = self.detect_gaps(symbol, timeframe, start, end)
                all_gaps[key] = gaps

        return all_gaps


class HistoricalDataBackfill:
    """
    Manages historical data backfill operations.

    Fetches missing historical data from exchanges and stores it in the database.
    """

    def __init__(self):
        """Initialize backfill manager."""
        self.gap_detector = GapDetector()

        # Import data sources
        from services.multi_source_manager import get_multi_source_manager

        self.source_manager = get_multi_source_manager()

        logger.info("HistoricalDataBackfill initialized")

    async def backfill_symbol(
        self,
        symbol: str,
        timeframe: str = "1h",
        lookback_days: int = 365,
        batch_size: int = 1000,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Backfill historical data for a single symbol.

        Args:
            symbol: Trading symbol
            timeframe: Time frame
            lookback_days: Number of days to look back
            batch_size: Batch size for fetching
            start: Optional start time for precise range
            end: Optional end time for precise range

        Returns:
            Dictionary with results
        """
        if not end:
            end = datetime.utcnow()
        if not start:
            start = end - timedelta(days=lookback_days)

        # Detect gaps
        gaps = self.gap_detector.detect_gaps(symbol, timeframe, start, end)

        if not gaps:
            logger.info(f"No gaps detected for {symbol} {timeframe}")
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "gaps_found": 0,
                "gaps_filled": 0,
                "periods_fetched": 0,
                "success": True,
            }

        total_periods = 0
        filled_gaps = 0

        # Fill each gap
        for gap in gaps:
            try:
                # Fetch data from source with precise time range
                candles, source = await self.source_manager.get_ohlcv(
                    symbol=symbol,
                    interval=timeframe,
                    limit=batch_size,
                    preferred_sources=["binance", "coingecko", "kraken"],
                )

                if candles:
                    # Filter candles to only include those in gap range
                    filtered_candles = [
                        c for c in candles if gap.gap_start <= c["timestamp"] <= gap.gap_end
                    ]

                    # Store in database
                    stored = await self._store_candles(filtered_candles, symbol)
                    total_periods += stored

                    if stored > 0:
                        filled_gaps += 1
                        logger.info(
                            f"Filled gap for {symbol}: {stored} candles from {source} ({gap.gap_start} to {gap.gap_end})"
                        )
                    else:
                        logger.warning(f"No new candles to store for {symbol} gap")
                else:
                    logger.warning(f"Failed to fetch data for {symbol} gap")

            except Exception as e:
                logger.error(f"Error filling gap for {symbol}: {e}")

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "gaps_found": len(gaps),
            "gaps_filled": filled_gaps,
            "periods_fetched": total_periods,
            "success": filled_gaps > 0,
        }

    async def backfill_batch(
        self, symbols: List[str], config: Optional[BackfillConfig] = None
    ) -> BackfillStats:
        """
        Backfill historical data for multiple symbols.

        Args:
            symbols: List of trading symbols
            config: Backfill configuration

        Returns:
            Backfill statistics
        """
        config = config or BackfillConfig(symbols=symbols)
        stats = BackfillStats(total_symbols=len(symbols), start_time=datetime.utcnow())

        logger.info(f"Starting backfill for {len(symbols)} symbols")

        # Process symbols in batches
        for i in range(0, len(symbols), config.max_concurrent_requests):
            batch = symbols[i : i + config.max_concurrent_requests]

            # Create tasks for concurrent processing
            tasks = [
                self.backfill_symbol(
                    symbol, config.timeframe, config.lookback_days, config.batch_size
                )
                for symbol in batch
            ]

            # Execute batch
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    stats.errors.append(str(result))
                else:
                    stats.completed_symbols += 1
                    stats.total_periods_requested += result.get("gaps_found", 0)
                    stats.total_periods_fetched += result.get("periods_fetched", 0)
                    stats.gaps_detected += result.get("gaps_found", 0)
                    stats.gaps_filled += result.get("gaps_filled", 0)

            # Delay between batches to respect rate limits
            if i + config.max_concurrent_requests < len(symbols):
                await asyncio.sleep(config.delay_between_requests)

        stats.end_time = datetime.utcnow()

        logger.info(
            f"Backfill complete: {stats.completed_symbols}/{stats.total_symbols} symbols, "
            f"{stats.total_periods_fetched} periods fetched, "
            f"{stats.gaps_filled}/{stats.gaps_detected} gaps filled"
        )

        return stats

    async def _store_candles(self, candles: List[Dict[str, Any]], symbol: str) -> int:
        """
        Store OHLCV candles in database.

        Args:
            candles: List of OHLCV candles
            symbol: Trading symbol

        Returns:
            Number of candles stored
        """
        session = get_db_session().__enter__()

        try:
            stored_count = 0

            for candle in candles:
                try:
                    # Check if already exists
                    existing = (
                        session.query(PriceModel)
                        .filter(
                            PriceModel.symbol == symbol.upper(),
                            PriceModel.timestamp == candle["timestamp"],
                        )
                        .first()
                    )

                    if not existing:
                        price = PriceModel(
                            symbol=symbol.upper(),
                            timestamp=candle["timestamp"],
                            open=candle["open"],
                            high=candle["high"],
                            low=candle["low"],
                            close=candle["close"],
                            volume=candle["volume"],
                        )
                        session.add(price)
                        stored_count += 1

                except Exception as e:
                    logger.error(f"Error storing candle: {e}")

            session.commit()
            return stored_count

        except Exception as e:
            session.rollback()
            logger.error(f"Error storing candles: {e}")
            return 0

        finally:
            session.close()


class DataRetentionManager:
    """
    Manages data retention policies and cleanup.

    Handles deletion of old data according to retention policies.
    """

    def __init__(self):
        """Initialize retention manager."""
        logger.info("DataRetentionManager initialized")

    def cleanup_old_data(
        self, policy: DataRetentionPolicy = DataRetentionPolicy.ONE_YEAR, dry_run: bool = True
    ) -> Dict[str, int]:
        """
        Clean up old data according to retention policy.

        Args:
            policy: Retention policy
            dry_run: If True, only report what would be deleted

        Returns:
            Dictionary with deletion counts by symbol
        """
        # Calculate cutoff date
        cutoff_date = datetime.utcnow()

        if policy == DataRetentionPolicy.ONE_YEAR:
            cutoff_date -= timedelta(days=365)
        elif policy == DataRetentionPolicy.SIX_MONTHS:
            cutoff_date -= timedelta(days=180)
        elif policy == DataRetentionPolicy.THREE_MONTHS:
            cutoff_date -= timedelta(days=90)
        elif policy == DataRetentionPolicy.ONE_MONTH:
            cutoff_date -= timedelta(days=30)

        session = get_db_session().__enter__()

        try:
            # Get count by symbol
            query = (
                session.query(PriceModel.symbol, func.count(PriceModel.id).label("count"))
                .filter(PriceModel.timestamp < cutoff_date)
                .group_by(PriceModel.symbol)
            )

            results = query.all()

            deletion_counts = {symbol: count for symbol, count in results}

            if not dry_run:
                # Perform deletion
                deleted = (
                    session.query(PriceModel).filter(PriceModel.timestamp < cutoff_date).delete()
                )

                session.commit()

                logger.info(f"Deleted {deleted} old price records (cutoff: {cutoff_date})")

            return deletion_counts

        finally:
            session.close()

    def get_data_age_stats(self) -> Dict[str, Any]:
        """
        Get statistics about data age.

        Returns:
            Dictionary with age statistics
        """
        session = get_db_session().__enter__()

        try:
            # Get oldest and newest data points
            oldest = (
                session.query(PriceModel.symbol, func.min(PriceModel.timestamp).label("oldest"))
                .group_by(PriceModel.symbol)
                .all()
            )

            newest = (
                session.query(PriceModel.symbol, func.max(PriceModel.timestamp).label("newest"))
                .group_by(PriceModel.symbol)
                .all()
            )

            # Build stats
            stats = {}
            for symbol, oldest_ts in oldest:
                newest_ts = next((ts for s, ts in newest if s == symbol), None)

                if newest_ts:
                    age_days = (datetime.utcnow() - oldest_ts).days
                    stats[symbol] = {
                        "oldest": oldest_ts.isoformat(),
                        "newest": newest_ts.isoformat(),
                        "age_days": age_days,
                        "total_days": (newest_ts - oldest_ts).days,
                    }

            return stats

        finally:
            session.close()


# Global instances
_gap_detector: Optional[GapDetector] = None
_backfill_manager: Optional[HistoricalDataBackfill] = None
_retention_manager: Optional[DataRetentionManager] = None


def get_gap_detector() -> GapDetector:
    """Get the global gap detector instance."""
    global _gap_detector
    if _gap_detector is None:
        _gap_detector = GapDetector()
    return _gap_detector


def get_backfill_manager() -> HistoricalDataBackfill:
    """Get the global backfill manager instance."""
    global _backfill_manager
    if _backfill_manager is None:
        _backfill_manager = HistoricalDataBackfill()
    return _backfill_manager


def get_retention_manager() -> DataRetentionManager:
    """Get the global retention manager instance."""
    global _retention_manager
    if _retention_manager is None:
        _retention_manager = DataRetentionManager()
    return _retention_manager
