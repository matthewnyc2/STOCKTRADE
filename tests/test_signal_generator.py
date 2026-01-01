"""
Tests for Signal Generation Service.

Tests the signal generation engine for different strategy types:
- Simple strategies (RSI, MA crossover, MACD)
- Layered strategies (using signal_aggregator)
- Strategy execution loop
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from models import SignalType, LogicGate, Strategy
from services.signal_generator import (
    SignalGenerator,
    check_rsi_signals,
    check_ma_crossover_signals,
    check_macd_signals,
    calculate_rsi_confidence,
    detect_crossover,
)
from services.signal_aggregator import LayerSignal, aggregate_signals


class TestCalculateRsiConfidence:
    """Tests for RSI confidence calculation."""

    def test_extreme_oversold_high_confidence(self):
        """Test extreme oversold (RSI < 20) returns high confidence."""
        confidence = calculate_rsi_confidence(15.0, SignalType.LONG)
        assert confidence == 0.9

    def test_moderate_oversold_medium_confidence(self):
        """Test moderate oversold (RSI 20-30) returns medium confidence."""
        confidence = calculate_rsi_confidence(25.0, SignalType.LONG)
        assert confidence == 0.7

    def test_weak_oversold_low_confidence(self):
        """Test weak oversold (RSI 30-40) returns low confidence."""
        confidence = calculate_rsi_confidence(35.0, SignalType.LONG)
        assert confidence == 0.5

    def test_extreme_overbought_high_confidence(self):
        """Test extreme overbought (RSI > 80) returns high confidence."""
        confidence = calculate_rsi_confidence(85.0, SignalType.SHORT)
        assert confidence == 0.9

    def test_moderate_overbought_medium_confidence(self):
        """Test moderate overbought (RSI 70-80) returns medium confidence."""
        confidence = calculate_rsi_confidence(75.0, SignalType.SHORT)
        assert confidence == 0.7

    def test_weak_overbought_low_confidence(self):
        """Test weak overbought (RSI 60-70) returns low confidence."""
        confidence = calculate_rsi_confidence(65.0, SignalType.SHORT)
        assert confidence == 0.5

    def test_neutral_zone_no_signal(self):
        """Test neutral zone (RSI 40-60) returns no confidence."""
        confidence = calculate_rsi_confidence(50.0, SignalType.LONG)
        assert confidence == 0.0

    def test_invalid_rsi_signal_mismatch(self):
        """Test that mismatched RSI and signal type returns zero confidence."""
        # RSI is oversold but signal is SHORT - should return 0
        confidence = calculate_rsi_confidence(20.0, SignalType.SHORT)
        assert confidence == 0.0


class TestDetectCrossover:
    """Tests for crossover detection."""

    def test_bullish_crossover_detected(self):
        """Test bullish crossover (fast crosses above slow)."""
        # Previous: fast below slow
        # Current: fast above slow
        result = detect_crossover(
            fast_prev=10.0, fast_curr=12.0,
            slow_prev=11.0, slow_curr=11.5
        )
        assert result == SignalType.LONG

    def test_bearish_crossover_detected(self):
        """Test bearish crossover (fast crosses below slow)."""
        # Previous: fast above slow
        # Current: fast below slow
        result = detect_crossover(
            fast_prev=12.0, fast_curr=11.0,
            slow_prev=11.0, slow_curr=11.5
        )
        assert result == SignalType.SHORT

    def test_no_crossover_both_above(self):
        """Test no crossover when both remain above."""
        result = detect_crossover(
            fast_prev=12.0, fast_curr=13.0,
            slow_prev=10.0, slow_curr=11.0
        )
        assert result is None

    def test_no_crossover_both_below(self):
        """Test no crossover when both remain below."""
        result = detect_crossover(
            fast_prev=8.0, fast_curr=9.0,
            slow_prev=10.0, slow_curr=11.0
        )
        assert result is None

    def test_no_crossover_parallel(self):
        """Test no crossover when lines are parallel."""
        result = detect_crossover(
            fast_prev=10.0, fast_curr=11.0,
            slow_prev=9.0, slow_curr=10.0
        )
        assert result is None


class TestCheckRsiSignals:
    """Tests for RSI signal generation."""

    def test_oversold_generates_long_signal(self):
        """Test oversold RSI generates LONG signal."""
        indicators = {"rsi_14": [None] * 13 + [25.0]}
        signal = check_rsi_signals(
            indicators,
            oversold_threshold=30,
            overbought_threshold=70
        )
        assert signal.signal_type == SignalType.LONG
        assert signal.confidence == 0.7
        assert "RSI" in signal.reasoning

    def test_overbought_generates_short_signal(self):
        """Test overbought RSI generates SHORT signal."""
        indicators = {"rsi_14": [None] * 13 + [75.0]}
        signal = check_rsi_signals(
            indicators,
            oversold_threshold=30,
            overbought_threshold=70
        )
        assert signal.signal_type == SignalType.SHORT
        assert signal.confidence == 0.7

    def test_neutral_rsi_no_signal(self):
        """Test neutral RSI generates NEUTRAL signal."""
        indicators = {"rsi_14": [None] * 13 + [50.0]}
        signal = check_rsi_signals(
            indicators,
            oversold_threshold=30,
            overbought_threshold=70
        )
        assert signal.signal_type == SignalType.NEUTRAL
        assert signal.confidence == 0.0

    def test_custom_thresholds(self):
        """Test custom RSI thresholds."""
        indicators = {"rsi_14": [None] * 13 + [20.0]}
        signal = check_rsi_signals(
            indicators,
            oversold_threshold=25,
            overbought_threshold=75
        )
        assert signal.signal_type == SignalType.LONG
        # RSI is 20, which is below 25 threshold
        # confidence is based on RSI value: 20 < 20 is false, 20 < 30 is true
        # So it's in moderate oversold range
        assert signal.confidence >= 0.7

    def test_missing_rsi_data_returns_neutral(self):
        """Test missing RSI data returns NEUTRAL."""
        indicators = {"rsi_14": [None] * 14}
        signal = check_rsi_signals(indicators)
        assert signal.signal_type == SignalType.NEUTRAL
        assert signal.confidence == 0.0


class TestCheckMACrossoverSignals:
    """Tests for MA crossover signal generation."""

    def test_bullish_ma_crossover(self):
        """Test bullish MA crossover generates LONG signal."""
        indicators = {
            "ema_12": [10.0, 12.0],
            "ema_26": [11.0, 11.5]
        }
        signal = check_ma_crossover_signals(
            indicators,
            fast_period=12,
            slow_period=26
        )
        assert signal.signal_type == SignalType.LONG
        assert "crossover" in signal.reasoning.lower()

    def test_bearish_ma_crossover(self):
        """Test bearish MA crossover generates SHORT signal."""
        indicators = {
            "ema_12": [12.0, 11.0],
            "ema_26": [11.0, 11.5]
        }
        signal = check_ma_crossover_signals(
            indicators,
            fast_period=12,
            slow_period=26
        )
        assert signal.signal_type == SignalType.SHORT

    def test_no_crossover_no_signal(self):
        """Test no crossover returns NEUTRAL."""
        indicators = {
            "ema_12": [10.0, 11.0],
            "ema_26": [9.0, 10.0]
        }
        signal = check_ma_crossover_signals(
            indicators,
            fast_period=12,
            slow_period=26
        )
        assert signal.signal_type == SignalType.NEUTRAL

    def test_insufficient_data_returns_neutral(self):
        """Test insufficient data returns NEUTRAL."""
        indicators = {
            "ema_12": [None] * 10,
            "ema_26": [None] * 10
        }
        signal = check_ma_crossover_signals(
            indicators,
            fast_period=12,
            slow_period=26
        )
        assert signal.signal_type == SignalType.NEUTRAL


class TestCheckMACDSignals:
    """Tests for MACD signal generation."""

    def test_macd_bullish_crossover(self):
        """Test MACD bullish crossover generates LONG signal."""
        indicators = {
            "macd_line": [0.5, 0.8],
            "macd_signal": [0.6, 0.7]
        }
        signal = check_macd_signals(indicators)
        assert signal.signal_type == SignalType.LONG
        assert "MACD" in signal.reasoning

    def test_macd_bearish_crossover(self):
        """Test MACD bearish crossover generates SHORT signal."""
        indicators = {
            "macd_line": [0.8, 0.5],
            "macd_signal": [0.7, 0.6]
        }
        signal = check_macd_signals(indicators)
        assert signal.signal_type == SignalType.SHORT

    def test_macd_histogram_growing(self):
        """Test growing histogram with positive values generates signal."""
        indicators = {
            "macd_histogram": [-0.1, 0.2, 0.3],  # Negative to positive transition, then growing
            "macd_line": [0.7, 0.8, 0.9],
            "macd_signal": [0.75, 0.77, 0.78]
        }
        signal = check_macd_signals(indicators)
        # Should detect bullish momentum from histogram turning positive
        assert signal.signal_type == SignalType.LONG

    def test_no_macd_crossover(self):
        """Test no MACD crossover returns NEUTRAL."""
        indicators = {
            "macd_line": [0.5, 0.6],
            "macd_signal": [0.4, 0.5]
        }
        signal = check_macd_signals(indicators)
        assert signal.signal_type == SignalType.NEUTRAL


class TestSignalGenerator:
    """Tests for the main SignalGenerator class."""

    def test_generate_signal_rsi_strategy(self):
        """Test generating signal for RSI strategy."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_1",
            name="RSI Strategy",
            type="template",
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 30,
                "overbought_threshold": 70
            },
            logic_gate=LogicGate.NONE
        )

        indicators = {"rsi_14": [None] * 13 + [25.0]}
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.LONG
        assert signal.strategy_id == "strat_1"
        assert signal.symbol == "BTC/USDT"
        assert signal.price == Decimal("100.0")

    def test_generate_signal_ma_crossover_strategy(self):
        """Test generating signal for MA crossover strategy."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_2",
            name="MA Crossover",
            type="template",
            parameters={
                "indicator_type": "ma_crossover",
                "fast_period": 12,
                "slow_period": 26
            },
            logic_gate=LogicGate.NONE
        )

        indicators = {
            "ema_12": [10.0, 12.0],
            "ema_26": [11.0, 11.5]
        }
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "ETH/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.LONG
        assert signal.symbol == "ETH/USDT"

    def test_generate_signal_layered_strategy_and_gate(self):
        """Test generating signal for layered strategy with AND gate."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_3",
            name="Layered AND",
            type="composed",
            layers=["layer_1", "layer_2"],
            logic_gate=LogicGate.AND,
            parameters={
                "layers": [
                    {
                        "id": "layer_1",
                        "indicator_type": "rsi",
                        "weight": 0.5
                    },
                    {
                        "id": "layer_2",
                        "indicator_type": "ma_crossover",
                        "weight": 0.5
                    }
                ]
            }
        )

        indicators = {
            "rsi_14": [None] * 13 + [25.0],  # LONG
            "ema_12": [10.0, 12.0],  # LONG crossover
            "ema_26": [11.0, 11.5]
        }
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        # Both layers agree on LONG
        assert signal.signal_type == SignalType.LONG
        assert len(signal.layer_breakdown) == 2

    def test_generate_signal_layered_strategy_disagreement(self):
        """Test layered strategy with disagreeing layers."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_4",
            name="Layered Disagree",
            type="composed",
            layers=["layer_1", "layer_2"],
            logic_gate=LogicGate.AND,
            parameters={
                "layers": [
                    {
                        "id": "layer_1",
                        "indicator_type": "rsi",
                        "weight": 0.5
                    },
                    {
                        "id": "layer_2",
                        "indicator_type": "ma_crossover",
                        "weight": 0.5
                    }
                ]
            }
        )

        indicators = {
            "rsi_14": [None] * 13 + [25.0],  # LONG
            "ema_12": [12.0, 11.0],  # SHORT crossover
            "ema_26": [11.0, 11.5]
        }
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        # Layers disagree - AND gate returns NEUTRAL
        assert signal.signal_type == SignalType.NEUTRAL

    def test_generate_signal_unknown_indicator_type(self):
        """Test unknown indicator type returns NEUTRAL."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_5",
            name="Unknown Indicator",
            type="template",
            parameters={"indicator_type": "unknown_indicator"},
            logic_gate=LogicGate.NONE
        )

        indicators = {}
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.NEUTRAL
        assert signal.confidence == 0.0


class TestIntegrationScenarios:
    """Integration tests for realistic signal generation scenarios."""

    def test_strong_buy_signal_confluence(self):
        """Test strong buy signal from multiple indicators."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_buy",
            name="Strong Buy",
            type="composed",
            layers=["rsi", "macd", "ma"],
            logic_gate=LogicGate.AND,
            parameters={
                "layers": [
                    {"id": "rsi", "indicator_type": "rsi", "weight": 0.33},
                    {"id": "macd", "indicator_type": "macd", "weight": 0.33},
                    {"id": "ma", "indicator_type": "ma_crossover", "weight": 0.34}
                ]
            }
        )

        # All indicators show LONG
        indicators = {
            "rsi_14": [None] * 13 + [20.0],  # Extreme oversold
            "ema_12": [10.0, 12.0],  # Bullish crossover
            "ema_26": [11.0, 11.5],
            "macd_line": [0.5, 0.8],  # Bullish crossover
            "macd_signal": [0.6, 0.7]
        }
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.LONG
        assert signal.confidence > 0.7  # High confidence from confluence
        assert len(signal.layer_breakdown) == 3

    def test_weak_signal_single_indicator(self):
        """Test weak signal from single indicator."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_weak",
            name="Weak Signal",
            type="template",
            parameters={
                "indicator_type": "rsi",
                "oversold_threshold": 40  # Higher threshold to capture weak signal
            },
            logic_gate=LogicGate.NONE
        )

        # Weak oversold signal (just below 40)
        indicators = {"rsi_14": [None] * 13 + [35.0]}
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.LONG
        assert signal.confidence == 0.5  # Low confidence (30-40 range)

    def test_no_clear_signal(self):
        """Test scenario with no clear signal."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_neutral",
            name="Neutral",
            type="template",
            parameters={
                "indicator_type": "rsi"
            },
            logic_gate=LogicGate.NONE
        )

        # RSI in neutral zone
        indicators = {"rsi_14": [None] * 13 + [50.0]}
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        assert signal.signal_type == SignalType.NEUTRAL
        assert signal.confidence == 0.0

    def test_weighted_voting_scenario(self):
        """Test weighted voting with different layer weights."""
        generator = SignalGenerator()

        strategy = Strategy(
            id="strat_weighted",
            name="Weighted Vote",
            type="composed",
            layers=["heavy", "light1", "light2"],
            logic_gate=LogicGate.WEIGHTED,
            parameters={
                "layers": [
                    {"id": "heavy", "indicator_type": "rsi", "weight": 0.7},
                    {"id": "light1", "indicator_type": "ma_crossover", "weight": 0.15},
                    {"id": "light2", "indicator_type": "macd", "weight": 0.15}
                ]
            }
        )

        # Heavy layer says LONG, light layers say SHORT
        indicators = {
            "rsi_14": [None] * 13 + [20.0],  # LONG (heavy weight)
            "ema_12": [12.0, 11.0],  # SHORT crossover (light)
            "ema_26": [11.0, 11.5],
            "macd_line": [0.8, 0.5],  # SHORT crossover (light)
            "macd_signal": [0.7, 0.6]
        }
        price_data = {"close": 100.0}

        signal = generator.generate_signal(strategy, "BTC/USDT", price_data, indicators)

        # Heavy weight should win
        assert signal.signal_type == SignalType.LONG
