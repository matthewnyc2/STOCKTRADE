"""
Technical Indicators Calculator Service.

Provides calculations for common technical analysis indicators including:
- Moving Averages: SMA, EMA
- Momentum: RSI, MACD, Stochastic, Williams %R
- Volatility: Bollinger Bands, ATR
- Volume: Volume SMA, OBV
"""

import math
from typing import List, Optional, Tuple


def calculate_sma(prices: List[float], period: int = 20) -> List[Optional[float]]:
    """
    Calculate Simple Moving Average (SMA).

    Args:
        prices: List of price values
        period: Number of periods for the moving average

    Returns:
        List of SMA values (None where insufficient data)
    """
    if not prices or period <= 0:
        return []

    result: List[Optional[float]] = []

    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            # Use window from current index back (period) elements
            # For i=4, period=5: use indices 0,1,2,3,4
            avg = sum(prices[i - period + 1:i + 1]) / period
            result.append(avg)

    return result


def calculate_ema(prices: List[float], period: int = 20) -> List[Optional[float]]:
    """
    Calculate Exponential Moving Average (EMA).

    Uses SMA as the seed value, then applies EMA formula:
    EMA = (Close - EMA_previous) * multiplier + EMA_previous
    multiplier = 2 / (period + 1)

    Args:
        prices: List of price values
        period: Number of periods for the moving average

    Returns:
        List of EMA values (None where insufficient data)
    """
    if not prices or period <= 0:
        return []

    if len(prices) < period:
        return [None] * len(prices)

    result: List[Optional[float]] = []
    multiplier = 2.0 / (period + 1.0)

    # Calculate initial SMA
    initial_sma = sum(prices[:period]) / period

    # First period-1 values are None
    for _ in range(period - 1):
        result.append(None)

    # First EMA value is the SMA
    result.append(initial_sma)

    # Calculate remaining EMA values
    for i in range(period, len(prices)):
        ema = (prices[i] - result[-1]) * multiplier + result[-1]
        result.append(ema)

    return result


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI).

    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss

    Uses Wilder's smoothing method.

    Args:
        prices: List of price values (typically close prices)
        period: Number of periods (default 14)

    Returns:
        List of RSI values between 0-100 (None where insufficient data)
    """
    if not prices or period <= 0:
        return []

    if len(prices) < period + 1:
        return [None] * len(prices)

    result: List[Optional[float]] = []

    # Calculate price changes
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Separate gains and losses
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]

    # First period-1 values are None
    for _ in range(period):
        result.append(None)

    # Calculate initial average gain and loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Calculate first RSI
    if avg_loss == 0:
        rs = 100  # No losses, RSI = 100
    else:
        rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))
    result.append(rsi)

    # Calculate remaining RSI values using Wilder's smoothing
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        result.append(rsi)

    return result


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line

    Args:
        prices: List of price values
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    if not prices:
        return [], [], []

    # Calculate fast and slow EMAs
    fast_ema = calculate_ema(prices, period=fast)
    slow_ema = calculate_ema(prices, period=slow)

    macd_line: List[Optional[float]] = []

    for i in range(len(prices)):
        if fast_ema[i] is None or slow_ema[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(fast_ema[i] - slow_ema[i])

    # Calculate signal line (EMA of MACD)
    # Filter out None values for EMA calculation
    valid_macd = [m for m in macd_line if m is not None]

    if len(valid_macd) < signal:
        # Not enough data for signal line
        signal_line: List[Optional[float]] = [None] * len(prices)
        histogram: List[Optional[float]] = [None] * len(prices)
        return macd_line, signal_line, histogram

    signal_ema = calculate_ema(valid_macd, period=signal)

    # Pad signal line with None to match original length
    num_none = len(prices) - len(valid_macd)
    signal_line = [None] * num_none + signal_ema

    # Calculate histogram
    histogram: List[Optional[float]] = []
    for i in range(len(prices)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line[i])

    return macd_line, signal_line, histogram


def calculate_bollinger(
    prices: List[float],
    period: int = 20,
    std: float = 2.0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Calculate Bollinger Bands.

    Middle Band = SMA(period)
    Upper Band = Middle Band + (std * standard deviation)
    Lower Band = Middle Band - (std * standard deviation)

    Args:
        prices: List of price values
        period: Number of periods (default 20)
        std: Standard deviation multiplier (default 2)

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    if not prices or period <= 0:
        return [], [], []

    middle_band = calculate_sma(prices, period=period)

    upper_band: List[Optional[float]] = []
    lower_band: List[Optional[float]] = []

    for i in range(len(prices)):
        if i < period - 1:
            upper_band.append(None)
            lower_band.append(None)
        else:
            # Calculate standard deviation
            window = prices[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            stdev = math.sqrt(variance)

            upper_band.append(middle_band[i] + std * stdev)
            lower_band.append(middle_band[i] - std * stdev)

    return upper_band, middle_band, lower_band


def calculate_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    Calculate Average True Range (ATR).

    True Range is the greatest of:
    - High - Low
    - |High - Previous Close|
    - |Low - Previous Close|

    ATR is the moving average of True Range.

    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Number of periods (default 14)

    Returns:
        List of ATR values (None where insufficient data)
    """
    if not highs or len(highs) != len(lows) or len(highs) != len(closes):
        return []

    if len(highs) < period:
        return [None] * len(highs)

    # Calculate True Range for each period
    true_ranges: List[float] = []

    # First TR is just High - Low
    true_ranges.append(highs[0] - lows[0])

    # Subsequent TRs
    for i in range(1, len(highs)):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i - 1])
        tr3 = abs(lows[i] - closes[i - 1])
        true_ranges.append(max(tr1, tr2, tr3))

    # Calculate ATR using RSI-style smoothing (Wilder's method)
    # First (period-1) values are None
    result: List[Optional[float]] = [None] * (period - 1)

    # Initial ATR is average of first period TRs (at index period-1)
    initial_atr = sum(true_ranges[:period]) / period
    result.append(initial_atr)

    # Smooth remaining values (start from index 'period' in true_ranges)
    for i in range(period, len(true_ranges)):
        atr = (result[-1] * (period - 1) + true_ranges[i]) / period
        result.append(atr)

    return result


def calculate_stochastic(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Calculate Stochastic Oscillator.

    %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
    %D = SMA(%K, d_period)

    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        k_period: %K lookback period (default 14)
        d_period: %D smoothing period (default 3)

    Returns:
        Tuple of (%K, %D) values between 0-100
    """
    if not highs or len(highs) != len(lows) or len(highs) != len(closes):
        return [], []

    if len(highs) < k_period:
        return [None] * len(highs), [None] * len(highs)

    # Calculate %K
    k_values: List[Optional[float]] = []

    for i in range(len(highs)):
        if i < k_period - 1:
            k_values.append(None)
        else:
            window_highs = highs[i - k_period + 1:i + 1]
            window_lows = lows[i - k_period + 1:i + 1]
            highest_high = max(window_highs)
            lowest_low = min(window_lows)

            if highest_high - lowest_low == 0:
                k_values.append(50)  # No price change, return middle
            else:
                k = 100 * (closes[i] - lowest_low) / (highest_high - lowest_low)
                k_values.append(k)

    # Calculate %D (SMA of %K)
    valid_k = [k for k in k_values if k is not None]

    if len(valid_k) < d_period:
        d_values = [None] * len(highs)
    else:
        d_sma = calculate_sma(valid_k, period=d_period)

        # Pad with None to match original length
        num_none = len(k_values) - len(valid_k)
        d_values = [None] * (num_none + d_period - 1) + d_sma

    return k_values, d_values


def calculate_williams_r(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """
    Calculate Williams %R.

    Williams %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)

    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        period: Lookback period (default 14)

    Returns:
        List of Williams %R values between -100 and 0
    """
    if not highs or len(highs) != len(lows) or len(highs) != len(closes):
        return []

    if len(highs) < period:
        return [None] * len(highs)

    result: List[Optional[float]] = []

    for i in range(len(highs)):
        if i < period - 1:
            result.append(None)
        else:
            window_highs = highs[i - period + 1:i + 1]
            window_lows = lows[i - period + 1:i + 1]
            highest_high = max(window_highs)
            lowest_low = min(window_lows)

            if highest_high - lowest_low == 0:
                result.append(-50)  # No price change
            else:
                williams = -100 * (highest_high - closes[i]) / (highest_high - lowest_low)
                result.append(williams)

    return result


def calculate_volume_sma(volumes: List[float], period: int = 20) -> List[Optional[float]]:
    """
    Calculate Simple Moving Average of volume.

    Args:
        volumes: List of volume values
        period: Number of periods (default 20)

    Returns:
        List of volume SMA values (None where insufficient data)
    """
    # Volume SMA is the same calculation as price SMA
    return calculate_sma(volumes, period=period)


def calculate_obv(closes: List[float], volumes: List[float]) -> List[Optional[float]]:
    """
    Calculate On-Balance Volume (OBV).

    OBV starts with an initial value (first day's volume).
    If price closes up: add volume
    If price closes down: subtract volume
    If price is unchanged: OBV doesn't change

    Args:
        closes: List of close prices
        volumes: List of volume values

    Returns:
        List of OBV values
    """
    if not closes or not volumes or len(closes) != len(volumes):
        return []

    if len(closes) == 0:
        return []

    result: List[Optional[float]] = [volumes[0]]

    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            result.append(result[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            result.append(result[-1] - volumes[i])
        else:
            result.append(result[-1])

    return result


def calculate_all_indicators(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float]
) -> dict:
    """
    Calculate all available indicators for a price dataset.

    Args:
        opens: List of open prices
        highs: List of high prices
        lows: List of low prices
        closes: List of close prices
        volumes: List of volume values

    Returns:
        Dictionary containing all calculated indicators
    """
    indicators = {
        "sma_20": calculate_sma(closes, period=20),
        "sma_50": calculate_sma(closes, period=50),
        "sma_200": calculate_sma(closes, period=200),
        "ema_12": calculate_ema(closes, period=12),
        "ema_26": calculate_ema(closes, period=26),
        "ema_50": calculate_ema(closes, period=50),
        "rsi_14": calculate_rsi(closes, period=14),
        "macd_line": None,
        "macd_signal": None,
        "macd_histogram": None,
        "bollinger_upper": None,
        "bollinger_middle": None,
        "bollinger_lower": None,
        "atr_14": None,
        "stochastic_k": None,
        "stochastic_d": None,
        "williams_r": None,
        "volume_sma_20": calculate_volume_sma(volumes, period=20),
        "obv": None,
    }

    # Calculate multi-output indicators
    macd_line, macd_signal, macd_hist = calculate_macd(closes)
    indicators["macd_line"] = macd_line
    indicators["macd_signal"] = macd_signal
    indicators["macd_histogram"] = macd_hist

    bb_upper, bb_middle, bb_lower = calculate_bollinger(closes)
    indicators["bollinger_upper"] = bb_upper
    indicators["bollinger_middle"] = bb_middle
    indicators["bollinger_lower"] = bb_lower

    atr = calculate_atr(highs, lows, closes)
    indicators["atr_14"] = atr

    stoch_k, stoch_d = calculate_stochastic(highs, lows, closes)
    indicators["stochastic_k"] = stoch_k
    indicators["stochastic_d"] = stoch_d

    williams = calculate_williams_r(highs, lows, closes)
    indicators["williams_r"] = williams

    obv = calculate_obv(closes, volumes)
    indicators["obv"] = obv

    return indicators
