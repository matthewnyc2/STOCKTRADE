"""
Signal Aggregation Service.

Provides logic gates for combining multiple layer signals into a single output signal.
Supports AND, OR, and WEIGHTED aggregation modes.
"""

from typing import Optional
from models import SignalType, LogicGate


class AggregatedSignal:
    """
    Represents an aggregated signal from multiple layers.

    Attributes:
        signal_type: The final signal type after aggregation
        confidence: The compound confidence (0.0-1.0)
        layer_count: Number of layers that contributed
        agreement_count: Number of layers that agreed on the final signal
    """

    def __init__(
        self,
        signal_type: SignalType,
        confidence: float,
        layer_count: int,
        agreement_count: int,
    ):
        self.signal_type = signal_type
        self.confidence = confidence
        self.layer_count = layer_count
        self.agreement_count = agreement_count

    def __repr__(self) -> str:
        return (
            f"AggregatedSignal(signal_type={self.signal_type}, "
            f"confidence={self.confidence:.2f}, layers={self.layer_count}, "
            f"agreements={self.agreement_count})"
        )


class LayerSignal:
    """
    Represents a signal from a single layer.

    Attributes:
        layer_id: ID of the layer that generated this signal
        signal_type: The signal type (LONG, SHORT, CLOSE, NEUTRAL)
        confidence: Confidence level (0.0-1.0)
        weight: Weight of this layer for weighted aggregation (0.0-1.0)
        reasoning: Optional explanation for the signal
    """

    def __init__(
        self,
        layer_id: str,
        signal_type: SignalType,
        confidence: float,
        weight: float = 1.0,
        reasoning: Optional[str] = None,
    ):
        self.layer_id = layer_id
        self.signal_type = signal_type
        self.confidence = confidence
        self.weight = weight
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return (
            f"LayerSignal(layer_id={self.layer_id}, signal_type={self.signal_type}, "
            f"confidence={self.confidence:.2f}, weight={self.weight:.2f})"
        )


def aggregate_signals_and(layers: list[LayerSignal]) -> AggregatedSignal:
    """
    Aggregate layer signals using AND logic gate.

    All layers must agree on the same signal type. If they disagree,
    returns NEUTRAL with zero confidence.

    Args:
        layers: List of layer signals to aggregate

    Returns:
        AggregatedSignal: The aggregated result

    Examples:
        >>> layers = [
        ...     LayerSignal("l1", SignalType.LONG, 0.8),
        ...     LayerSignal("l2", SignalType.LONG, 0.6),
        ... ]
        >>> aggregate_signals_and(layers)
        AggregatedSignal(signal_type=long, confidence=0.70, layers=2, agreements=2)
    """
    if not layers:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, 0, 0)

    # Filter out NEUTRAL signals (they don't block AND, but don't count toward agreement)
    active_signals = [s for s in layers if s.signal_type != SignalType.NEUTRAL]

    if not active_signals:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, len(layers), 0)

    # Check if all active signals agree
    first_signal_type = active_signals[0].signal_type
    all_agree = all(s.signal_type == first_signal_type for s in active_signals)

    if not all_agree:
        # Signals disagree - return NEUTRAL
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, len(layers), 0)

    # All agree - calculate compound confidence
    compound_confidence = calculate_compound_confidence(active_signals, [s.weight for s in active_signals])
    agreement_count = len(active_signals)

    return AggregatedSignal(
        signal_type=first_signal_type,
        confidence=compound_confidence,
        layer_count=len(layers),
        agreement_count=agreement_count,
    )


def aggregate_signals_or(layers: list[LayerSignal]) -> AggregatedSignal:
    """
    Aggregate layer signals using OR logic gate.

    Returns the most confident signal among all layers.
    NEUTRAL signals are ignored unless all signals are NEUTRAL.

    Args:
        layers: List of layer signals to aggregate

    Returns:
        AggregatedSignal: The aggregated result

    Examples:
        >>> layers = [
        ...     LayerSignal("l1", SignalType.LONG, 0.6),
        ...     LayerSignal("l2", SignalType.SHORT, 0.9),
        ... ]
        >>> aggregate_signals_or(layers)
        AggregatedSignal(signal_type=short, confidence=0.90, layers=2, agreements=1)
    """
    if not layers:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, 0, 0)

    # Filter out NEUTRAL signals
    active_signals = [s for s in layers if s.signal_type != SignalType.NEUTRAL]

    if not active_signals:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, len(layers), 0)

    # Find the signal with highest confidence
    best_signal = max(active_signals, key=lambda s: s.confidence)

    # Count how many layers agree with this signal type
    agreement_count = sum(1 for s in active_signals if s.signal_type == best_signal.signal_type)

    return AggregatedSignal(
        signal_type=best_signal.signal_type,
        confidence=best_signal.confidence,
        layer_count=len(layers),
        agreement_count=agreement_count,
    )


def aggregate_signals_weighted(layers: list[LayerSignal]) -> AggregatedSignal:
    """
    Aggregate layer signals using weighted voting.

    Calculates a weighted score for each signal type and returns the winner.
    Scores are computed as: sum(confidence * weight) for each signal type.

    Args:
        layers: List of layer signals to aggregate

    Returns:
        AggregatedSignal: The aggregated result

    Examples:
        >>> layers = [
        ...     LayerSignal("l1", SignalType.LONG, 0.8, weight=0.5),
        ...     LayerSignal("l2", SignalType.SHORT, 0.6, weight=0.3),
        ...     LayerSignal("l3", SignalType.LONG, 0.9, weight=0.2),
        ... ]
        >>> aggregate_signals_weighted(layers)
        AggregatedSignal(signal_type=long, confidence=0.75, layers=3, agreements=2)
    """
    if not layers:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, 0, 0)

    # Filter out NEUTRAL signals
    active_signals = [s for s in layers if s.signal_type != SignalType.NEUTRAL]

    if not active_signals:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, len(layers), 0)

    # Normalize weights if they don't sum to 1.0
    weights = [s.weight for s in active_signals]
    total_weight = sum(weights)

    if total_weight == 0:
        # All weights are zero - use equal weighting
        weights = [1.0] * len(active_signals)
        total_weight = len(active_signals)

    normalized_weights = [w / total_weight for w in weights]

    # Calculate weighted scores for each signal type
    scores_by_type: dict[SignalType, float] = {}
    count_by_type: dict[SignalType, int] = {}

    for signal, norm_weight in zip(active_signals, normalized_weights):
        if signal.signal_type not in scores_by_type:
            scores_by_type[signal.signal_type] = 0.0
            count_by_type[signal.signal_type] = 0
        scores_by_type[signal.signal_type] += signal.confidence * norm_weight
        count_by_type[signal.signal_type] += 1

    # Find the signal type with highest score
    best_signal_type = max(scores_by_type, key=lambda k: scores_by_type[k])
    best_score = scores_by_type[best_signal_type]

    return AggregatedSignal(
        signal_type=best_signal_type,
        confidence=best_score,
        layer_count=len(layers),
        agreement_count=count_by_type[best_signal_type],
    )


def calculate_compound_confidence(
    signals: list[LayerSignal],
    weights: list[float] | None = None,
) -> float:
    """
    Calculate compound confidence from multiple layer signals.

    Args:
        signals: List of layer signals
        weights: Optional weights for each signal. If None, uses equal weights.

    Returns:
        float: Compound confidence (0.0-1.0)

    Examples:
        >>> signals = [
        ...     LayerSignal("l1", SignalType.LONG, 0.8),
        ...     LayerSignal("l2", SignalType.LONG, 0.6),
        ... ]
        >>> calculate_compound_confidence(signals)
        0.7
    """
    if not signals:
        return 0.0

    if weights is None:
        weights = [1.0] * len(signals)

    if len(signals) != len(weights):
        raise ValueError("Number of signals must match number of weights")

    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        weights = [1.0] * len(signals)
        total_weight = len(signals)

    normalized_weights = [w / total_weight for w in weights]

    # Calculate weighted average confidence
    compound_confidence = sum(
        s.confidence * w for s, w in zip(signals, normalized_weights)
    )

    return round(compound_confidence, 4)


def aggregate_signals(
    layers: list[LayerSignal],
    logic_gate: LogicGate,
) -> AggregatedSignal:
    """
    Aggregate layer signals based on the specified logic gate.

    This is the main entry point for signal aggregation.
    Routes to the appropriate aggregation function based on logic_gate.

    Args:
        layers: List of layer signals to aggregate
        logic_gate: The logic gate to use (AND, OR, WEIGHTED, NONE)

    Returns:
        AggregatedSignal: The aggregated result

    Examples:
        >>> layers = [
        ...     LayerSignal("l1", SignalType.LONG, 0.8, weight=0.5),
        ...     LayerSignal("l2", SignalType.LONG, 0.6, weight=0.5),
        ... ]
        >>> aggregate_signals(layers, LogicGate.AND)
        AggregatedSignal(signal_type=long, confidence=0.70, layers=2, agreements=2)
    """
    if not layers:
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, 0, 0)

    if logic_gate == LogicGate.AND:
        return aggregate_signals_and(layers)
    elif logic_gate == LogicGate.OR:
        return aggregate_signals_or(layers)
    elif logic_gate == LogicGate.WEIGHTED:
        return aggregate_signals_weighted(layers)
    else:  # LogicGate.NONE
        # For NONE, just return the first non-neutral signal or NEUTRAL
        for layer in layers:
            if layer.signal_type != SignalType.NEUTRAL:
                return AggregatedSignal(
                    signal_type=layer.signal_type,
                    confidence=layer.confidence,
                    layer_count=len(layers),
                    agreement_count=1,
                )
        return AggregatedSignal(SignalType.NEUTRAL, 0.0, len(layers), 0)
