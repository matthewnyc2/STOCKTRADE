"""
Signal Generation Service.

Executes strategy logic on price data and indicators to generate trading signals.
Supports simple template-based strategies and layered strategies with aggregation.
"""

from decimal import Decimal
from typing import Any, Optional
from datetime import datetime

from models import SignalType, LogicGate, Strategy, Signal
from services.signal_aggregator import LayerSignal, aggregate_signals


def calculate_rsi_confidence(rsi: float, signal_type: SignalType) -> float:
    """
    Calculate confidence based on RSI value and signal type.

    Confidence levels:
    - Extreme (RSI < 20 or > 80): High confidence (0.9)
    - Moderate (RSI 20-30 or 70-80): Medium confidence (0.7)
    - Weak (RSI 30-40 or 60-70): Low confidence (0.5)
    - Neutral (RSI 40-60): No confidence (0.0)

    Args:
        rsi: Current RSI value
        signal_type: Type of signal being generated

    Returns:
        float: Confidence level (0.0-1.0)
    """
    if signal_type == SignalType.LONG:
        if rsi < 20:
            return 0.9  # Extreme oversold
        elif rsi < 30:
            return 0.7  # Moderate oversold
        elif rsi < 40:
            return 0.5  # Weak oversold
        else:
            return 0.0  # Neutral zone
    elif signal_type == SignalType.SHORT:
        if rsi > 80:
            return 0.9  # Extreme overbought
        elif rsi > 70:
            return 0.7  # Moderate overbought
        elif rsi > 60:
            return 0.5  # Weak overbought
        else:
            return 0.0  # Neutral zone
    else:
        return 0.0


def detect_crossover(
    fast_prev: float,
    fast_curr: float,
    slow_prev: float,
    slow_curr: float
) -> Optional[SignalType]:
    """
    Detect if a crossover occurred between fast and slow lines.

    Bullish crossover: Fast line crosses above slow line
    Bearish crossover: Fast line crosses below slow line

    Args:
        fast_prev: Previous fast line value
        fast_curr: Current fast line value
        slow_prev: Previous slow line value
        slow_curr: Current slow line value

    Returns:
        SignalType.LONG if bullish crossover, SignalType.SHORT if bearish, None if no crossover
    """
    # Check if fast was below slow and is now above (bullish)
    if fast_prev <= slow_prev and fast_curr > slow_curr:
        return SignalType.LONG

    # Check if fast was above slow and is now below (bearish)
    if fast_prev >= slow_prev and fast_curr < slow_curr:
        return SignalType.SHORT

    # No crossover
    return None


def check_rsi_signals(
    indicators: dict[str, list[float | None]],
    oversold_threshold: float = 30.0,
    overbought_threshold: float = 70.0
) -> LayerSignal:
    """
    Check for RSI-based signals.

    Args:
        indicators: Dictionary of indicator values
        oversold_threshold: RSI level for oversold condition
        overbought_threshold: RSI level for overbought condition

    Returns:
        LayerSignal with signal type and confidence
    """
    rsi_key = "rsi_14"
    rsi_values = indicators.get(rsi_key, [])

    # Get latest RSI value
    if not rsi_values or len(rsi_values) < 2:
        return LayerSignal(
            layer_id="rsi",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning="Insufficient RSI data"
        )

    latest_rsi = rsi_values[-1]
    if latest_rsi is None:
        return LayerSignal(
            layer_id="rsi",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning="No RSI value available"
        )

    # Check for oversold (LONG signal)
    if latest_rsi <= oversold_threshold:
        confidence = calculate_rsi_confidence(latest_rsi, SignalType.LONG)
        return LayerSignal(
            layer_id="rsi",
            signal_type=SignalType.LONG,
            confidence=confidence,
            reasoning=f"RSI ({latest_rsi:.1f}) is oversold (< {oversold_threshold})"
        )

    # Check for overbought (SHORT signal)
    if latest_rsi >= overbought_threshold:
        confidence = calculate_rsi_confidence(latest_rsi, SignalType.SHORT)
        return LayerSignal(
            layer_id="rsi",
            signal_type=SignalType.SHORT,
            confidence=confidence,
            reasoning=f"RSI ({latest_rsi:.1f}) is overbought (> {overbought_threshold})"
        )

    # Neutral zone
    return LayerSignal(
        layer_id="rsi",
        signal_type=SignalType.NEUTRAL,
        confidence=0.0,
        reasoning=f"RSI ({latest_rsi:.1f}) is in neutral zone"
    )


def check_ma_crossover_signals(
    indicators: dict[str, list[float | None]],
    fast_period: int = 12,
    slow_period: int = 26
) -> LayerSignal:
    """
    Check for Moving Average crossover signals.

    Args:
        indicators: Dictionary of indicator values
        fast_period: Fast MA period (e.g., 12 for EMA)
        slow_period: Slow MA period (e.g., 26 for EMA)

    Returns:
        LayerSignal with signal type and confidence
    """
    fast_key = f"ema_{fast_period}"
    slow_key = f"ema_{slow_period}"

    fast_values = indicators.get(fast_key, [])
    slow_values = indicators.get(slow_key, [])

    # Need at least 2 values to detect crossover
    if len(fast_values) < 2 or len(slow_values) < 2:
        return LayerSignal(
            layer_id="ma_crossover",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning=f"Insufficient MA data for {fast_period}/{slow_period} crossover"
        )

    # Get previous and current values
    fast_prev = fast_values[-2]
    fast_curr = fast_values[-1]
    slow_prev = slow_values[-2]
    slow_curr = slow_values[-1]

    if any(v is None for v in [fast_prev, fast_curr, slow_prev, slow_curr]):
        return LayerSignal(
            layer_id="ma_crossover",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning="Missing MA values"
        )

    # Detect crossover
    crossover = detect_crossover(fast_prev, fast_curr, slow_prev, slow_curr)

    if crossover == SignalType.LONG:
        return LayerSignal(
            layer_id="ma_crossover",
            signal_type=SignalType.LONG,
            confidence=0.7,  # Fixed confidence for MA crossover
            reasoning=f"Bullish MA crossover: EMA({fast_period}) crossed above EMA({slow_period})"
        )
    elif crossover == SignalType.SHORT:
        return LayerSignal(
            layer_id="ma_crossover",
            signal_type=SignalType.SHORT,
            confidence=0.7,
            reasoning=f"Bearish MA crossover: EMA({fast_period}) crossed below EMA({slow_period})"
        )

    return LayerSignal(
        layer_id="ma_crossover",
        signal_type=SignalType.NEUTRAL,
        confidence=0.0,
        reasoning=f"No MA crossover detected for {fast_period}/{slow_period}"
    )


def check_macd_signals(
    indicators: dict[str, list[float | None]]
) -> LayerSignal:
    """
    Check for MACD-based signals.

    Looks for:
    1. MACD line crossing above/below signal line
    2. Histogram direction changes

    Args:
        indicators: Dictionary of indicator values

    Returns:
        LayerSignal with signal type and confidence
    """
    macd_line = indicators.get("macd_line", [])
    macd_signal = indicators.get("macd_signal", [])
    histogram = indicators.get("macd_histogram", [])

    # Need at least 2 values to detect crossover
    if len(macd_line) < 2 or len(macd_signal) < 2:
        return LayerSignal(
            layer_id="macd",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning="Insufficient MACD data"
        )

    # Get values
    macd_prev = macd_line[-2]
    macd_curr = macd_line[-1]
    signal_prev = macd_signal[-2]
    signal_curr = macd_signal[-1]

    if any(v is None for v in [macd_prev, macd_curr, signal_prev, signal_curr]):
        return LayerSignal(
            layer_id="macd",
            signal_type=SignalType.NEUTRAL,
            confidence=0.0,
            reasoning="Missing MACD values"
        )

    # Detect MACD crossover
    crossover = detect_crossover(macd_prev, macd_curr, signal_prev, signal_curr)

    if crossover == SignalType.LONG:
        confidence = 0.75
        reasoning = "Bullish MACD crossover"

        # Check histogram for additional confirmation
        if len(histogram) >= 2 and histogram[-2] is not None and histogram[-1] is not None:
            if histogram[-1] > histogram[-2] > 0:
                confidence = 0.85
                reasoning += " with growing bullish histogram"

        return LayerSignal(
            layer_id="macd",
            signal_type=SignalType.LONG,
            confidence=confidence,
            reasoning=reasoning
        )
    elif crossover == SignalType.SHORT:
        confidence = 0.75
        reasoning = "Bearish MACD crossover"

        # Check histogram for additional confirmation
        if len(histogram) >= 2 and histogram[-2] is not None and histogram[-1] is not None:
            if histogram[-1] < histogram[-2] < 0:
                confidence = 0.85
                reasoning += " with growing bearish histogram"

        return LayerSignal(
            layer_id="macd",
            signal_type=SignalType.SHORT,
            confidence=confidence,
            reasoning=reasoning
        )

    # Check histogram momentum even without crossover
    if len(histogram) >= 3:
        if histogram[-3] is not None and histogram[-2] is not None and histogram[-1] is not None:
            # Histogram turning positive
            if histogram[-3] <= 0 and histogram[-2] > 0 and histogram[-1] > histogram[-2]:
                return LayerSignal(
                    layer_id="macd",
                    signal_type=SignalType.LONG,
                    confidence=0.6,
                    reasoning="MACD histogram turning positive with momentum"
                )
            # Histogram turning negative
            if histogram[-3] >= 0 and histogram[-2] < 0 and histogram[-1] < histogram[-2]:
                return LayerSignal(
                    layer_id="macd",
                    signal_type=SignalType.SHORT,
                    confidence=0.6,
                    reasoning="MACD histogram turning negative with momentum"
                )

    return LayerSignal(
        layer_id="macd",
        signal_type=SignalType.NEUTRAL,
        confidence=0.0,
        reasoning="No clear MACD signal"
    )


class SignalGenerator:
    """
    Main signal generation engine.

    Generates trading signals by executing strategy logic on price data and indicators.
    Supports both simple template-based strategies and complex layered strategies.
    """

    def __init__(self):
        """Initialize the signal generator."""
        pass

    def generate_signal(
        self,
        strategy: Strategy,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, list[float | None]]
    ) -> Signal:
        """
        Generate a trading signal for a strategy.

        Args:
            strategy: The strategy to execute
            symbol: Trading symbol (e.g., "BTC/USDT")
            price_data: Current price data (must include 'close')
            indicators: Calculated indicator values

        Returns:
            Signal object with type, confidence, and reasoning
        """
        # Handle layered strategies
        if strategy.type == "composed" and strategy.parameters.get("layers"):
            return self._generate_layered_signal(strategy, symbol, price_data, indicators)

        # Handle simple template strategies
        return self._generate_simple_signal(strategy, symbol, price_data, indicators)

    def _generate_simple_signal(
        self,
        strategy: Strategy,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, list[float | None]]
    ) -> Signal:
        """
        Generate signal for a simple (template) strategy.

        Args:
            strategy: The strategy configuration
            symbol: Trading symbol
            price_data: Current price data
            indicators: Calculated indicators

        Returns:
            Signal object
        """
        indicator_type = strategy.parameters.get("indicator_type", "unknown")

        # Generate layer signal based on indicator type
        if indicator_type == "rsi":
            layer_signal = check_rsi_signals(
                indicators,
                oversold_threshold=strategy.parameters.get("oversold_threshold", 30.0),
                overbought_threshold=strategy.parameters.get("overbought_threshold", 70.0)
            )
        elif indicator_type == "ma_crossover":
            layer_signal = check_ma_crossover_signals(
                indicators,
                fast_period=strategy.parameters.get("fast_period", 12),
                slow_period=strategy.parameters.get("slow_period", 26)
            )
        elif indicator_type == "macd":
            layer_signal = check_macd_signals(indicators)
        else:
            # Unknown indicator type
            layer_signal = LayerSignal(
                layer_id="unknown",
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                reasoning=f"Unknown indicator type: {indicator_type}"
            )

        # Convert layer signal to full signal
        close_price = Decimal(str(price_data.get("close", 0)))

        return Signal(
            strategy_id=strategy.id,
            symbol=symbol,
            signal_type=layer_signal.signal_type,
            confidence=layer_signal.confidence,
            price=close_price,
            timestamp=datetime.utcnow(),
            reasoning=layer_signal.reasoning,
            layer_breakdown=[{
                "layer_id": layer_signal.layer_id,
                "signal_type": layer_signal.signal_type.value,
                "confidence": layer_signal.confidence,
                "reasoning": layer_signal.reasoning
            }],
            metadata=strategy.parameters
        )

    def _generate_layered_signal(
        self,
        strategy: Strategy,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, list[float | None]]
    ) -> Signal:
        """
        Generate signal for a layered strategy using aggregation.

        Args:
            strategy: The strategy with multiple layers
            symbol: Trading symbol
            price_data: Current price data
            indicators: Calculated indicators

        Returns:
            Signal object with aggregated results
        """
        layers_config = strategy.parameters.get("layers", [])
        layer_signals = []

        for layer_config in layers_config:
            layer_id = layer_config.get("id", "unknown")
            layer_weight = layer_config.get("weight", 1.0)
            indicator_type = layer_config.get("indicator_type", "unknown")

            # Generate signal for this layer
            if indicator_type == "rsi":
                layer_signal = check_rsi_signals(indicators)
            elif indicator_type == "ma_crossover":
                layer_signal = check_ma_crossover_signals(indicators)
            elif indicator_type == "macd":
                layer_signal = check_macd_signals(indicators)
            else:
                layer_signal = LayerSignal(
                    layer_id=layer_id,
                    signal_type=SignalType.NEUTRAL,
                    confidence=0.0,
                    reasoning=f"Unknown layer indicator: {indicator_type}"
                )

            # Update layer ID and weight
            layer_signal.layer_id = layer_id
            layer_signal.weight = layer_weight
            layer_signals.append(layer_signal)

        # Aggregate layer signals using the strategy's logic gate
        aggregated = aggregate_signals(layer_signals, strategy.logic_gate)

        # Build layer breakdown for the signal
        layer_breakdown = [
            {
                "layer_id": ls.layer_id,
                "signal_type": ls.signal_type.value,
                "confidence": ls.confidence,
                "weight": ls.weight,
                "reasoning": ls.reasoning
            }
            for ls in layer_signals
        ]

        close_price = Decimal(str(price_data.get("close", 0)))

        reasoning = self._build_aggregated_reasoning(
            aggregated,
            strategy.logic_gate,
            layer_breakdown
        )

        return Signal(
            strategy_id=strategy.id,
            symbol=symbol,
            signal_type=aggregated.signal_type,
            confidence=aggregated.confidence,
            price=close_price,
            timestamp=datetime.utcnow(),
            reasoning=reasoning,
            layer_breakdown=layer_breakdown,
            metadata={
                "aggregation": strategy.logic_gate.value,
                "layer_count": aggregated.layer_count,
                "agreement_count": aggregated.agreement_count
            }
        )

    def _build_aggregated_reasoning(
        self,
        aggregated,
        logic_gate: LogicGate,
        layer_breakdown: list[dict]
    ) -> str:
        """
        Build a reasoning string for aggregated signals.

        Args:
            aggregated: AggregatedSignal result
            logic_gate: The logic gate used
            layer_breakdown: List of layer signal details

        Returns:
            str: Human-readable reasoning
        """
        if aggregated.signal_type == SignalType.NEUTRAL:
            if logic_gate == LogicGate.AND:
                return f"NEUTRAL: Layers disagree ({aggregated.agreement_count}/{aggregated.layer_count} agreement)"
            elif logic_gate == LogicGate.OR:
                return f"NEUTRAL: No active signals from {aggregated.layer_count} layers"
            else:
                return f"NEUTRAL: No clear signal from {aggregated.layer_count} layers"

        signal_name = aggregated.signal_type.value.upper()
        gate_name = logic_gate.value.upper()

        return (
            f"{signal_name} signal ({gate_name} aggregation): "
            f"{aggregated.agreement_count}/{aggregated.layer_count} layers agree, "
            f"confidence {aggregated.confidence:.2f}"
        )
