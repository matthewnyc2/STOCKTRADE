"""
Feature Engineering for Trading Models.

Generates 50+ technical indicators as features:
- Price features: OHLC ratios, returns, log returns
- Volume features: Volume changes, volume ratios
- Momentum: RSI, Stochastic, Williams %R, MACD
- Trend: SMAs, EMAs, ADX-like features
- Volatility: ATR, Bollinger Bands, standard deviation
- Time features: Hour of day, day of week
"""

import numpy as np
import numpy.typing as npt
from typing import Any, ClassVar

from services.indicators import (
    calculate_all_indicators,
    calculate_ema,
    calculate_rsi,
    calculate_sma,
)


class FeatureEngine:
    """
    Comprehensive feature engineering for trading models.

    Generates 50+ technical indicators as features:
    - Price features: OHLC ratios, returns, log returns
    - Volume features: Volume changes, volume ratios
    - Momentum: RSI, Stochastic, Williams %R, MACD
    - Trend: SMAs, EMAs, ADX-like features
    - Volatility: ATR, Bollinger Bands, standard deviation
    - Time features: Hour of day, day of week
    """

    # Feature groups
    PRICE_FEATURES: ClassVar[list[str]] = [
        "open",
        "high",
        "low",
        "close",
        "open_close_ratio",
        "high_low_ratio",
        "close_prev_ratio",
        "return",
        "log_return",
        "abs_return",
    ]

    VOLUME_FEATURES: ClassVar[list[str]] = [
        "volume",
        "volume_change",
        "volume_ratio",
        "volume_sma_20_ratio",
        "price_volume_trend",
    ]

    MOMENTUM_FEATURES: ClassVar[list[str]] = [
        "rsi_14",
        "rsi_30",
        "stochastic_k",
        "stochastic_d",
        "williams_r",
        "momentum",
        "roc",
        "macd_line",
        "macd_signal",
        "macd_histogram",
    ]

    TREND_FEATURES: ClassVar[list[str]] = [
        "sma_20",
        "sma_50",
        "sma_200",
        "ema_12",
        "ema_26",
        "ema_50",
        "sma_20_slope",
        "sma_50_slope",
        "price_above_sma20",
        "price_above_sma50",
        "sma_crossover_20_50",
    ]

    VOLATILITY_FEATURES: ClassVar[list[str]] = [
        "atr_14",
        "atr_ratio",
        "bollinger_upper",
        "bollinger_middle",
        "bollinger_lower",
        "bollinger_width",
        "bollinger_position",
        "std_20",
        "std_50",
    ]

    TIME_FEATURES: ClassVar[list[str]] = [
        "hour_sin",
        "hour_cos",
        "day_of_week",
        "day_of_month",
        "quarter",
    ]

    @classmethod
    def get_all_features(cls) -> list[str]:
        """Get list of all available features."""
        return (
            cls.PRICE_FEATURES
            + cls.VOLUME_FEATURES
            + cls.MOMENTUM_FEATURES
            + cls.TREND_FEATURES
            + cls.VOLATILITY_FEATURES
            + cls.TIME_FEATURES
        )

    @classmethod
    def get_feature_group(cls, group: str) -> list[str]:
        """Get features by group name."""
        groups = {
            "price": cls.PRICE_FEATURES,
            "volume": cls.VOLUME_FEATURES,
            "momentum": cls.MOMENTUM_FEATURES,
            "trend": cls.TREND_FEATURES,
            "volatility": cls.VOLATILITY_FEATURES,
            "time": cls.TIME_FEATURES,
        }
        return groups.get(group, [])

    @staticmethod
    def calculate_features(
        data: list[dict[str, Any]],
        feature_groups: list[str],
    ) -> npt.NDArray[np.float64]:
        """
        Calculate features from OHLCV data.

        Args:
            data: List of OHLCV dictionaries
            feature_groups: List of feature groups to include

        Returns:
            Feature matrix [n_samples, n_features]
        """
        if not data:
            return np.array([[]])

        n = len(data)

        # Extract basic data
        opens = np.array([float(d["open"]) for d in data])
        highs = np.array([float(d["high"]) for d in data])
        lows = np.array([float(d["low"]) for d in data])
        closes = np.array([float(d["close"]) for d in data])
        volumes = np.array([float(d["volume"]) for d in data])
        timestamps = [d.get("timestamp") for d in data]

        features_dict: dict[str, npt.NDArray[np.float64]] = {}

        # Price features
        if "price" in feature_groups:
            features_dict["open"] = opens
            features_dict["high"] = highs
            features_dict["low"] = lows
            features_dict["close"] = closes

            features_dict["open_close_ratio"] = opens / closes
            features_dict["high_low_ratio"] = np.where(
                lows > 0,
                highs / lows,
                1.0,
            )

            # Previous close
            prev_closes = np.roll(closes, 1)
            prev_closes[0] = closes[0]
            features_dict["close_prev_ratio"] = closes / prev_closes

            # Returns
            returns = np.where(prev_closes > 0, closes - prev_closes, 0)
            features_dict["return"] = returns

            log_returns = np.where(
                closes > 0,
                np.log(closes / prev_closes),
                0,
            )
            features_dict["log_return"] = log_returns
            features_dict["abs_return"] = np.abs(returns)

        # Volume features
        if "volume" in feature_groups:
            features_dict["volume"] = volumes

            vol_change = np.diff(volumes, prepend=volumes[0])
            features_dict["volume_change"] = vol_change

            features_dict["volume_ratio"] = np.where(
                volumes > 0,
                volumes / np.mean(volumes),
                1.0,
            )

            # Volume SMA
            vol_sma = np.convolve(volumes, np.ones(20) / 20, mode="same")
            features_dict["volume_sma_20_ratio"] = np.where(
                vol_sma > 0,
                volumes / vol_sma,
                1.0,
            )

            # Price volume trend
            features_dict["price_volume_trend"] = returns * volumes

        # Calculate technical indicators
        indicators = calculate_all_indicators(
            opens.tolist(),
            highs.tolist(),
            lows.tolist(),
            closes.tolist(),
            volumes.tolist(),
        )

        # Momentum features
        if "momentum" in feature_groups:
            if "rsi_14" in indicators:
                rsi_values = np.array([v if v is not None else 50 for v in indicators["rsi_14"]])
                features_dict["rsi_14"] = rsi_values / 100

            if "stochastic_k" in indicators:
                stoch_k = np.array([v if v is not None else 50 for v in indicators["stochastic_k"]])
                features_dict["stochastic_k"] = stoch_k / 100

            if "stochastic_d" in indicators:
                stoch_d = np.array([v if v is not None else 50 for v in indicators["stochastic_d"]])
                features_dict["stochastic_d"] = stoch_d / 100

            if "williams_r" in indicators:
                williams = np.array([v if v is not None else -50 for v in indicators["williams_r"]])
                features_dict["williams_r"] = williams / 100

            # Momentum
            momentum = np.where(
                closes.size > 10,
                closes - np.roll(closes, 10),
                0,
            )
            features_dict["momentum"] = momentum

            # Rate of change
            roc = np.where(
                np.roll(closes, 10) > 0,
                (closes - np.roll(closes, 10)) / np.roll(closes, 10) * 100,
                0,
            )
            features_dict["roc"] = roc

            if "macd_line" in indicators:
                macd_line = np.array([v if v is not None else 0 for v in indicators["macd_line"]])
                features_dict["macd_line"] = macd_line

            if "macd_signal" in indicators:
                macd_signal = np.array(
                    [v if v is not None else 0 for v in indicators["macd_signal"]]
                )
                features_dict["macd_signal"] = macd_signal

            if "macd_histogram" in indicators:
                macd_hist = np.array(
                    [v if v is not None else 0 for v in indicators["macd_histogram"]]
                )
                features_dict["macd_histogram"] = macd_hist

        # Trend features
        if "trend" in feature_groups:
            if "sma_20" in indicators:
                sma20 = np.array(
                    [v if v is not None else closes[i] for i, v in enumerate(indicators["sma_20"])]
                )
                features_dict["sma_20"] = sma20
                features_dict["price_above_sma20"] = (closes > sma20).astype(float)

            if "sma_50" in indicators:
                sma50 = np.array(
                    [v if v is not None else closes[i] for i, v in enumerate(indicators["sma_50"])]
                )
                features_dict["sma_50"] = sma50
                features_dict["price_above_sma50"] = (closes > sma50).astype(float)

            if "ema_12" in indicators:
                ema12 = np.array(
                    [v if v is not None else closes[i] for i, v in enumerate(indicators["ema_12"])]
                )
                features_dict["ema_12"] = ema12

            if "ema_26" in indicators:
                ema26 = np.array(
                    [v if v is not None else closes[i] for i, v in enumerate(indicators["ema_26"])]
                )
                features_dict["ema_26"] = ema26

            if "ema_50" in indicators:
                ema50 = np.array(
                    [v if v is not None else closes[i] for i, v in enumerate(indicators["ema_50"])]
                )
                features_dict["ema_50"] = ema50

            # SMA slopes
            if "sma_20" in indicators:
                sma20_slope = np.diff(sma20, prepend=sma20[0])
                features_dict["sma_20_slope"] = sma20_slope

            if "sma_50" in indicators:
                sma50_slope = np.diff(sma50, prepend=sma50[0])
                features_dict["sma_50_slope"] = sma50_slope

            # SMA crossover
            if "sma_20" in indicators and "sma_50" in indicators:
                features_dict["sma_crossover_20_50"] = (sma20 > sma50).astype(float)

        # Volatility features
        if "volatility" in feature_groups:
            if "atr_14" in indicators:
                atr = np.array([v if v is not None else 0 for v in indicators["atr_14"]])
                features_dict["atr_14"] = atr
                features_dict["atr_ratio"] = np.where(
                    closes > 0,
                    atr / closes,
                    0,
                )

            if "bollinger_upper" in indicators:
                bb_upper = np.array(
                    [
                        v if v is not None else closes[i]
                        for i, v in enumerate(indicators["bollinger_upper"])
                    ]
                )
                bb_middle = np.array(
                    [
                        v if v is not None else closes[i]
                        for i, v in enumerate(indicators["bollinger_middle"])
                    ]
                )
                bb_lower = np.array(
                    [
                        v if v is not None else closes[i]
                        for i, v in enumerate(indicators["bollinger_lower"])
                    ]
                )

                features_dict["bollinger_upper"] = bb_upper
                features_dict["bollinger_middle"] = bb_middle
                features_dict["bollinger_lower"] = bb_lower

                features_dict["bollinger_width"] = np.where(
                    bb_middle > 0,
                    (bb_upper - bb_lower) / bb_middle,
                    0,
                )

                features_dict["bollinger_position"] = np.where(
                    bb_upper - bb_lower > 0,
                    (closes - bb_lower) / (bb_upper - bb_lower),
                    0.5,
                )

            # Standard deviation
            std20 = np.array([np.std(closes[max(0, i - 20) : i + 1]) for i in range(n)])
            features_dict["std_20"] = std20

            std50 = np.array([np.std(closes[max(0, i - 50) : i + 1]) for i in range(n)])
            features_dict["std_50"] = std50

        # Time features
        if "time" in feature_groups:
            hours = np.array([ts.hour if ts else 0 for ts in timestamps])
            features_dict["hour_sin"] = np.sin(2 * np.pi * hours / 24)
            features_dict["hour_cos"] = np.cos(2 * np.pi * hours / 24)

            day_of_week = np.array([ts.weekday() if ts else 0 for ts in timestamps])
            features_dict["day_of_week"] = day_of_week / 7

            day_of_month = np.array([ts.day if ts else 1 for ts in timestamps])
            features_dict["day_of_month"] = day_of_month / 31

            quarter = np.array([(ts.month - 1) // 3 + 1 if ts else 1 for ts in timestamps])
            features_dict["quarter"] = quarter / 4

        # Stack features
        if features_dict:
            feature_matrix = np.column_stack(
                [features_dict[k] for k in sorted(features_dict.keys())]
            )
        else:
            feature_matrix = np.zeros((n, 1))

        return feature_matrix

    @staticmethod
    def create_sequences(
        features: npt.NDArray[np.float64],
        targets: npt.NDArray[np.float64],
        sequence_length: int,
        prediction_horizon: int = 1,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Create sequences for LSTM training.

        Args:
            features: Feature matrix [n_samples, n_features]
            targets: Target values [n_samples]
            sequence_length: Lookback period
            prediction_horizon: Predict N steps ahead

        Returns:
            X: Sequences [n_sequences, sequence_length, n_features]
            y: Targets [n_sequences]
        """
        X, y = [], []

        n_samples = len(features)

        for i in range(sequence_length, n_samples - prediction_horizon + 1):
            X.append(features[i - sequence_length : i])
            y.append(targets[i + prediction_horizon - 1])

        if X:
            return np.array(X), np.array(y)
        else:
            return np.array([[]]), np.array([[]])
