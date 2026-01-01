"""
Tests for market data service and technical indicators.

Tests price data fetching, historical data retrieval, and indicator calculations.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from services.market_data import (
    get_current_price,
    get_historical_prices,
    seed_price_data,
    calculate_ohlc_from_tick,
)
from services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger,
    calculate_atr,
    calculate_stochastic,
    calculate_williams_r,
    calculate_volume_sma,
    calculate_obv,
)


class TestTechnicalIndicators:
    """Test technical indicator calculations."""

    def test_calculate_sma_basic(self):
        """Test basic SMA calculation."""
        prices = [10, 12, 15, 14, 16, 18, 20, 22, 25, 23]
        result = calculate_sma(prices, period=5)

        # Expected: (10+12+15+14+16)/5 = 13.4
        assert result is not None
        assert len(result) == len(prices)

        # First 4 values should be None (not enough data)
        assert result[0] is None
        assert result[1] is None
        assert result[2] is None
        assert result[3] is None

        # Fifth value
        assert abs(result[4] - 13.4) < 0.01

    def test_calculate_sma_period_1(self):
        """Test SMA with period 1 returns same values."""
        prices = [10, 15, 20, 25]
        result = calculate_sma(prices, period=1)

        assert result == prices

    def test_calculate_sma_empty_list(self):
        """Test SMA with empty list."""
        result = calculate_sma([], period=5)
        assert result == []

    def test_calculate_ema_basic(self):
        """Test basic EMA calculation."""
        prices = [22.27, 22.19, 22.08, 22.17, 22.18, 22.13, 22.23, 22.43, 22.24, 22.29]
        result = calculate_ema(prices, period=5)

        # EMA first period-1 values should be None, then SMA seed value
        assert result is not None
        assert len(result) == len(prices)

        # First 4 values should be None (warmup period)
        assert result[0] is None
        assert result[1] is None
        assert result[2] is None
        assert result[3] is None

        # 5th value should be SMA of first 5 prices
        expected_sma = sum(prices[:5]) / 5
        assert abs(result[4] - expected_sma) < 0.01

        # Values after the warmup should be non-None
        for i in range(4, len(prices)):
            assert result[i] is not None
            # EMA should be reasonably close to the price range
            assert abs(result[i] - prices[i]) < 5

    def test_calculate_ema_empty_list(self):
        """Test EMA with empty list."""
        result = calculate_ema([], period=5)
        assert result == []

    def test_calculate_rsi_basic(self):
        """Test basic RSI calculation."""
        # Create price series with clear uptrend and downtrend
        prices = [
            44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42,
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00
        ]
        result = calculate_rsi(prices, period=14)

        assert result is not None
        assert len(result) == len(prices)

        # First 13 values should be None (not enough data for 14-period RSI)
        for i in range(13):
            assert result[i] is None

        # Last value should be between 0 and 100
        assert result[14] is not None
        assert 0 <= result[14] <= 100

    def test_calculate_rsi_extreme_values(self):
        """Test RSI with extreme price movements."""
        # Strong uptrend - RSI should be high
        uptrend_prices = [100 + i for i in range(20)]
        result = calculate_rsi(uptrend_prices, period=14)

        # After warmup, RSI should be > 70 for strong uptrend
        assert result[-1] > 70

        # Strong downtrend - RSI should be low
        downtrend_prices = [100 - i for i in range(20)]
        result = calculate_rsi(downtrend_prices, period=14)

        # After warmup, RSI should be < 30 for strong downtrend
        assert result[-1] < 30

    def test_calculate_rsi_empty_list(self):
        """Test RSI with empty list."""
        result = calculate_rsi([], period=14)
        assert result == []

    def test_calculate_macd_basic(self):
        """Test basic MACD calculation."""
        prices = [100 + i * 0.5 for i in range(50)]
        macd_line, signal_line, histogram = calculate_macd(
            prices, fast=12, slow=26, signal=9
        )

        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None

        assert len(macd_line) == len(prices)
        assert len(signal_line) == len(prices)
        assert len(histogram) == len(prices)

        # MACD line uses slow=26 period, so first 25 values should be None
        # Signal line adds additional warmup
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                # Histogram should equal MACD - Signal
                expected_hist = macd_line[i] - signal_line[i]
                assert abs(histogram[i] - expected_hist) < 0.01

        # Check that we have some non-None values
        has_macd_data = any(v is not None for v in macd_line)
        has_signal_data = any(v is not None for v in signal_line)
        has_hist_data = any(v is not None for v in histogram)
        assert has_macd_data, "MACD line should have some data"
        assert has_signal_data, "Signal line should have some data"
        assert has_hist_data, "Histogram should have some data"

    def test_calculate_macd_empty_list(self):
        """Test MACD with empty list."""
        macd_line, signal_line, histogram = calculate_macd([], 12, 26, 9)
        assert macd_line == []
        assert signal_line == []
        assert histogram == []

    def test_calculate_bollinger_bands_basic(self):
        """Test basic Bollinger Bands calculation."""
        prices = [100 + i * 0.5 for i in range(30)]
        upper, middle, lower = calculate_bollinger(prices, period=20, std=2)

        assert upper is not None
        assert middle is not None
        assert lower is not None

        assert len(upper) == len(prices)
        assert len(middle) == len(prices)
        assert len(lower) == len(prices)

        # Check that upper > middle > lower when we have data
        for i in range(len(prices)):
            if upper[i] is not None:
                assert upper[i] > middle[i]
                assert middle[i] > lower[i]

                # Price should usually be within bands (for trending data might be outside)
                band_width = upper[i] - lower[i]
                assert band_width > 0

    def test_calculate_bollinger_bands_std_multiplier(self):
        """Test Bollinger Bands with different standard deviation multipliers."""
        prices = [100 + i for i in range(30)]

        upper_1, middle_1, lower_1 = calculate_bollinger(prices, period=20, std=1)
        upper_2, middle_2, lower_2 = calculate_bollinger(prices, period=20, std=2)

        # Bands with std=2 should be wider than std=1
        for i in range(len(prices)):
            if upper_1[i] is not None:
                width_1 = upper_1[i] - lower_1[i]
                width_2 = upper_2[i] - lower_2[i]
                assert width_2 > width_1

    def test_calculate_bollinger_empty_list(self):
        """Test Bollinger Bands with empty list."""
        upper, middle, lower = calculate_bollinger([], period=20)
        assert upper == []
        assert middle == []
        assert lower == []

    def test_calculate_atr_basic(self):
        """Test basic ATR calculation."""
        # Need at least period data points for ATR
        highs = [105 + i for i in range(20)]
        lows = [100 + i for i in range(20)]
        closes = [102 + i for i in range(20)]

        result = calculate_atr(highs, lows, closes, period=14)

        assert result is not None
        assert len(result) == len(highs)

        # First period-1 values should be None (not enough data)
        for i in range(13):  # period - 1 = 13
            assert result[i] is None

        # Index 13 should have the first ATR value
        assert result[13] is not None
        assert result[13] > 0

        # Once we have data, ATR should be positive
        has_data = False
        for val in result:
            if val is not None:
                assert val > 0
                has_data = True

        assert has_data, "ATR should have some non-None values"

    def test_calculate_atr_empty_lists(self):
        """Test ATR with empty lists."""
        result = calculate_atr([], [], [], period=14)
        assert result == []

    def test_calculate_stochastic_basic(self):
        """Test basic Stochastic oscillator calculation."""
        highs = [110, 112, 115, 118, 120, 122, 125, 128]
        lows = [100, 103, 105, 108, 110, 113, 115, 118]
        closes = [105, 108, 112, 115, 118, 120, 122, 125]

        k, d = calculate_stochastic(highs, lows, closes, k_period=14, d_period=3)

        assert k is not None
        assert d is not None
        assert len(k) == len(closes)
        assert len(d) == len(closes)

        # Values should be between 0 and 100 when we have data
        for i in range(len(k)):
            if k[i] is not None:
                assert 0 <= k[i] <= 100
            if d[i] is not None:
                assert 0 <= d[i] <= 100

    def test_calculate_stochastic_empty_lists(self):
        """Test Stochastic with empty lists."""
        k, d = calculate_stochastic([], [], [], 14, 3)
        assert k == []
        assert d == []

    def test_calculate_williams_r_basic(self):
        """Test basic Williams %R calculation."""
        highs = [110, 112, 115, 118, 120, 122, 125, 128, 130, 132, 135, 138, 140, 142]
        lows = [100, 103, 105, 108, 110, 113, 115, 118, 120, 122, 125, 128, 130, 132]
        closes = [105, 108, 112, 115, 118, 120, 122, 125, 128, 130, 132, 135, 138, 140]

        result = calculate_williams_r(highs, lows, closes, period=14)

        assert result is not None
        assert len(result) == len(closes)

        # When we have data, Williams %R should be between -100 and 0
        has_data = False
        for val in result:
            if val is not None:
                assert -100 <= val <= 0
                has_data = True

        assert has_data, "Williams %R should have some non-None values"

    def test_calculate_williams_r_empty_lists(self):
        """Test Williams %R with empty lists."""
        result = calculate_williams_r([], [], [], period=14)
        assert result == []

    def test_calculate_volume_sma_basic(self):
        """Test basic Volume SMA calculation."""
        volumes = [1000, 1200, 1500, 1800, 2000, 2200, 2500, 3000]
        result = calculate_volume_sma(volumes, period=5)

        assert result is not None
        assert len(result) == len(volumes)

        # First 4 values should be None
        for i in range(4):
            assert result[i] is None

        # Fifth value should be average of first 5
        expected = (1000 + 1200 + 1500 + 1800 + 2000) / 5
        assert abs(result[4] - expected) < 0.01

    def test_calculate_volume_sma_empty_list(self):
        """Test Volume SMA with empty list."""
        result = calculate_volume_sma([], period=5)
        assert result == []

    def test_calculate_obv_basic(self):
        """Test basic OBV calculation."""
        closes = [100, 102, 101, 103, 105, 104, 106]
        volumes = [1000, 1500, 800, 2000, 1200, 900, 1800]

        result = calculate_obv(closes, volumes)

        assert result is not None
        assert len(result) == len(closes)

        # First value is just the first volume
        assert result[0] == 1000

        # Second: price up, add volume
        assert result[1] == 1000 + 1500

        # Third: price down, subtract volume
        assert result[2] == 1000 + 1500 - 800

    def test_calculate_obv_empty_lists(self):
        """Test OBV with empty lists."""
        result = calculate_obv([], [])
        assert result == []

    def test_indicators_with_realistic_prices(self):
        """Test all indicators with a realistic price series."""
        # Generate realistic-looking price data
        import random
        random.seed(42)

        base_price = 50000
        prices = []
        highs = []
        lows = []

        for i in range(100):
            change = random.uniform(-0.02, 0.02)
            base_price = base_price * (1 + change)
            high = base_price * random.uniform(1.0, 1.01)
            low = base_price * random.uniform(0.99, 1.0)

            prices.append(base_price)
            highs.append(high)
            lows.append(low)

        closes = prices[:]
        volumes = [random.uniform(1000, 5000) for _ in range(100)]

        # Test all indicators
        sma = calculate_sma(prices, period=20)
        ema = calculate_ema(prices, period=20)
        rsi = calculate_rsi(prices, period=14)
        macd_line, signal_line, histogram = calculate_macd(prices)
        upper, middle, lower = calculate_bollinger(prices)
        atr = calculate_atr(highs, lows, closes, period=14)
        k, d = calculate_stochastic(highs, lows, closes)
        williams_r = calculate_williams_r(highs, lows, closes)
        vol_sma = calculate_volume_sma(volumes)
        obv = calculate_obv(closes, volumes)

        # All should return lists of correct length (ATR has an extra None at start)
        assert len(sma) == len(prices)
        assert len(ema) == len(prices)
        assert len(rsi) == len(prices)
        assert len(macd_line) == len(prices)
        assert len(upper) == len(prices)
        assert len(atr) == len(prices)  # ATR should return same length
        assert len(k) == len(prices)
        assert len(williams_r) == len(prices)
        assert len(vol_sma) == len(volumes)
        assert len(obv) == len(closes)

        # Check some values are non-None
        assert any(v is not None for v in sma)
        assert any(v is not None for v in ema)
        assert any(v is not None for v in rsi)
        assert any(v is not None for v in macd_line)
        assert any(v is not None for v in upper)
        assert any(v is not None for v in atr)
        assert any(v is not None for v in k)
        assert any(v is not None for v in williams_r)
        assert obv[0] is not None  # OBV starts immediately


class TestPriceData:
    """Test price data fetching and storage."""

    def test_ohlc_calculation_from_tick_data(self):
        """Test OHLC calculation from tick data."""
        # Simulate tick data for a single period
        ticks = [
            {"price": 100.0, "volume": 10},
            {"price": 102.0, "volume": 15},
            {"price": 101.0, "volume": 8},
            {"price": 103.0, "volume": 12},
            {"price": 99.0, "volume": 20},  # Low
            {"price": 104.0, "volume": 5},  # High
        ]

        result = calculate_ohlc_from_tick(ticks)

        assert result["open"] == 100.0
        assert result["high"] == 104.0
        assert result["low"] == 99.0
        assert result["close"] == 104.0  # Last tick
        assert result["volume"] == 70

    def test_ohlc_empty_ticks(self):
        """Test OHLC with empty tick data."""
        result = calculate_ohlc_from_tick([])
        assert result is None

    def test_ohlc_single_tick(self):
        """Test OHLC with single tick."""
        ticks = [{"price": 100.0, "volume": 10}]
        result = calculate_ohlc_from_tick(ticks)

        assert result["open"] == 100.0
        assert result["high"] == 100.0
        assert result["low"] == 100.0
        assert result["close"] == 100.0
        assert result["volume"] == 10


class TestIndicatorEdgeCases:
    """Test edge cases and error handling."""

    def test_sma_period_larger_than_data(self):
        """Test SMA when period is larger than data length."""
        prices = [1, 2, 3]
        result = calculate_sma(prices, period=10)

        # All values should be None
        assert all(v is None for v in result)

    def test_rsi_all_same_prices(self):
        """Test RSI when all prices are the same (no change)."""
        prices = [100] * 20
        result = calculate_rsi(prices, period=14)

        # Should handle gracefully - RSI undefined when no change
        # Typically returns 50 or None depending on implementation
        assert len(result) == len(prices)

    def test_ema_all_same_prices(self):
        """Test EMA when all prices are the same."""
        prices = [100] * 20
        result = calculate_ema(prices, period=10)

        # EMA should stay at 100
        for val in result:
            if val is not None:
                assert abs(val - 100) < 0.01

    def test_bollinger_constant_prices(self):
        """Test Bollinger Bands with constant prices."""
        prices = [100] * 30
        upper, middle, lower = calculate_bollinger(prices, period=20)

        # With constant prices, all bands should be at 100
        # (standard deviation is 0)
        for i in range(len(prices)):
            if upper[i] is not None:
                assert abs(upper[i] - 100) < 0.01
                assert abs(middle[i] - 100) < 0.01
                assert abs(lower[i] - 100) < 0.01
