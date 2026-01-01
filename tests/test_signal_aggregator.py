"""
Tests for Signal Aggregation Service.

Tests the logic gates (AND, OR, WEIGHTED) for combining layer signals.
"""

import pytest

from models import SignalType, LogicGate
from services.signal_aggregator import (
    LayerSignal,
    AggregatedSignal,
    aggregate_signals_and,
    aggregate_signals_or,
    aggregate_signals_weighted,
    calculate_compound_confidence,
    aggregate_signals,
)


class TestLayerSignal:
    """Tests for LayerSignal class."""

    def test_create_layer_signal(self):
        """Test creating a layer signal."""
        signal = LayerSignal(
            layer_id="layer_123",
            signal_type=SignalType.LONG,
            confidence=0.8,
            weight=0.5,
        )
        assert signal.layer_id == "layer_123"
        assert signal.signal_type == SignalType.LONG
        assert signal.confidence == 0.8
        assert signal.weight == 0.5

    def test_layer_signal_default_weight(self):
        """Test layer signal with default weight."""
        signal = LayerSignal(
            layer_id="layer_123",
            signal_type=SignalType.LONG,
            confidence=0.8,
        )
        assert signal.weight == 1.0


class TestCalculateCompoundConfidence:
    """Tests for calculate_compound_confidence function."""

    def test_equal_weights(self):
        """Test compound confidence with equal weights."""
        signals = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.LONG, 0.6),
        ]
        confidence = calculate_compound_confidence(signals)
        assert confidence == 0.7  # (0.8 + 0.6) / 2

    def test_custom_weights(self):
        """Test compound confidence with custom weights."""
        signals = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.7),
            LayerSignal("l2", SignalType.LONG, 0.6, weight=0.3),
        ]
        weights = [0.7, 0.3]
        confidence = calculate_compound_confidence(signals, weights)
        # 0.8 * 0.7 + 0.6 * 0.3 = 0.56 + 0.18 = 0.74
        assert confidence == 0.74

    def test_normalize_weights(self):
        """Test that weights are normalized."""
        signals = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=2.0),
            LayerSignal("l2", SignalType.LONG, 0.6, weight=1.0),
        ]
        weights = [2.0, 1.0]
        confidence = calculate_compound_confidence(signals, weights)
        # Normalized: 0.8 * (2/3) + 0.6 * (1/3) = 0.533 + 0.2 = 0.733
        assert abs(confidence - 0.7333) < 0.001

    def test_empty_signals(self):
        """Test compound confidence with empty signals."""
        confidence = calculate_compound_confidence([])
        assert confidence == 0.0

    def test_zero_weights_normalized(self):
        """Test that zero weights are handled by normalizing to equal weights."""
        signals = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.0),
            LayerSignal("l2", SignalType.LONG, 0.6, weight=0.0),
        ]
        weights = [0.0, 0.0]
        confidence = calculate_compound_confidence(signals, weights)
        # Should use equal weights: (0.8 + 0.6) / 2 = 0.7
        assert confidence == 0.7

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched signal and weight counts raises error."""
        signals = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.LONG, 0.6),
        ]
        weights = [0.5]  # Only one weight for two signals
        with pytest.raises(ValueError, match="Number of signals must match"):
            calculate_compound_confidence(signals, weights)


class TestAggregateSignalsAnd:
    """Tests for AND gate aggregation."""

    def test_all_long_returns_long(self):
        """Test that all LONG signals return LONG."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.LONG, 0.6),
            LayerSignal("l3", SignalType.LONG, 0.9),
        ]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.7667  # Weighted average
        assert result.layer_count == 3
        assert result.agreement_count == 3

    def test_all_short_returns_short(self):
        """Test that all SHORT signals return SHORT."""
        layers = [
            LayerSignal("l1", SignalType.SHORT, 0.7),
            LayerSignal("l2", SignalType.SHORT, 0.5),
        ]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.SHORT
        assert result.confidence == 0.6

    def test_disagreement_returns_neutral(self):
        """Test that disagreeing signals return NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.SHORT, 0.6),
        ]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0
        assert result.agreement_count == 0

    def test_disagreement_three_signals(self):
        """Test disagreement with LONG, SHORT, NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.SHORT, 0.6),
            LayerSignal("l3", SignalType.NEUTRAL, 0.0),
        ]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0

    def test_all_neutral_returns_neutral(self):
        """Test that all NEUTRAL signals return NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.NEUTRAL, 0.0),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0),
        ]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0
        assert result.agreement_count == 0

    def test_neutral_ignored_in_agreement(self):
        """Test that NEUTRAL signals are ignored in AND logic."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0),
            LayerSignal("l3", SignalType.LONG, 0.6),
        ]
        result = aggregate_signals_and(layers)
        # NEUTRAL doesn't block AND - active signals agree
        assert result.signal_type == SignalType.LONG
        assert result.agreement_count == 2

    def test_empty_layers_returns_neutral(self):
        """Test that empty layers return NEUTRAL."""
        result = aggregate_signals_and([])
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0
        assert result.layer_count == 0


class TestAggregateSignalsOr:
    """Tests for OR gate aggregation."""

    def test_returns_highest_confidence(self):
        """Test that OR returns the highest confidence signal."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.6),
            LayerSignal("l2", SignalType.SHORT, 0.9),
            LayerSignal("l3", SignalType.LONG, 0.7),
        ]
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.SHORT
        assert result.confidence == 0.9

    def test_all_long_returns_long(self):
        """Test that all LONG signals return LONG."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.LONG, 0.6),
        ]
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8  # Highest

    def test_agreement_count(self):
        """Test agreement count is calculated correctly."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.6),
            LayerSignal("l2", SignalType.LONG, 0.9),
            LayerSignal("l3", SignalType.SHORT, 0.5),
        ]
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.LONG
        assert result.agreement_count == 2  # Two LONG signals

    def test_all_neutral_returns_neutral(self):
        """Test that all NEUTRAL signals return NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.NEUTRAL, 0.0),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0),
        ]
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0

    def test_neutral_ignored(self):
        """Test that NEUTRAL signals are ignored in OR logic."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0),
            LayerSignal("l3", SignalType.SHORT, 0.6),
        ]
        result = aggregate_signals_or(layers)
        # Should pick between LONG and SHORT
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

    def test_empty_layers_returns_neutral(self):
        """Test that empty layers return NEUTRAL."""
        result = aggregate_signals_or([])
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0


class TestAggregateSignalsWeighted:
    """Tests for WEIGHTED gate aggregation."""

    def test_weighted_voting_long_wins(self):
        """Test weighted voting where LONG wins."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.5),
            LayerSignal("l2", SignalType.SHORT, 0.6, weight=0.3),
            LayerSignal("l3", SignalType.LONG, 0.9, weight=0.2),
        ]
        result = aggregate_signals_weighted(layers)

        # LONG scores: 0.8 * 0.5 + 0.9 * 0.2 = 0.4 + 0.18 = 0.58
        # SHORT scores: 0.6 * 0.3 = 0.18
        assert result.signal_type == SignalType.LONG
        assert result.agreement_count == 2

    def test_weighted_voting_short_wins(self):
        """Test weighted voting where SHORT wins due to high weight."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.9, weight=0.2),
            LayerSignal("l2", SignalType.SHORT, 0.7, weight=0.8),
        ]
        result = aggregate_signals_weighted(layers)

        # LONG scores: 0.9 * 0.2 = 0.18
        # SHORT scores: 0.7 * 0.8 = 0.56
        assert result.signal_type == SignalType.SHORT
        assert abs(result.confidence - 0.56) < 0.001

    def test_weights_normalized(self):
        """Test that weights are normalized."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=2.0),
            LayerSignal("l2", SignalType.LONG, 0.6, weight=1.0),
        ]
        result = aggregate_signals_weighted(layers)

        # Normalized weights: 2/3 and 1/3
        # Confidence: 0.8 * (2/3) + 0.6 * (1/3) = 0.533 + 0.2 = 0.733
        assert abs(result.confidence - 0.7333) < 0.001

    def test_all_neutral_returns_neutral(self):
        """Test that all NEUTRAL signals return NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.NEUTRAL, 0.0, weight=0.5),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0, weight=0.5),
        ]
        result = aggregate_signals_weighted(layers)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0

    def test_zero_weights_use_equal_weights(self):
        """Test that zero weights fall back to equal weighting."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.0),
            LayerSignal("l2", SignalType.LONG, 0.6, weight=0.0),
        ]
        result = aggregate_signals_weighted(layers)
        # Equal weights: (0.8 + 0.6) / 2 = 0.7
        assert result.confidence == 0.7

    def test_empty_layers_returns_neutral(self):
        """Test that empty layers return NEUTRAL."""
        result = aggregate_signals_weighted([])
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0


class TestAggregateSignalsMain:
    """Tests for the main aggregate_signals function."""

    def test_routes_to_and(self):
        """Test that LogicGate.AND routes to AND aggregation."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.LONG, 0.6),
        ]
        result = aggregate_signals(layers, LogicGate.AND)
        assert result.signal_type == SignalType.LONG
        assert result.agreement_count == 2

    def test_routes_to_or(self):
        """Test that LogicGate.OR routes to OR aggregation."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.6),
            LayerSignal("l2", SignalType.SHORT, 0.9),
        ]
        result = aggregate_signals(layers, LogicGate.OR)
        assert result.signal_type == SignalType.SHORT
        assert result.confidence == 0.9

    def test_routes_to_weighted(self):
        """Test that LogicGate.WEIGHTED routes to WEIGHTED aggregation."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.7),
            LayerSignal("l2", SignalType.SHORT, 0.6, weight=0.3),
        ]
        result = aggregate_signals(layers, LogicGate.WEIGHTED)
        assert result.signal_type == SignalType.LONG

    def test_none_returns_first_active(self):
        """Test that LogicGate.NONE returns first non-NEUTRAL signal."""
        layers = [
            LayerSignal("l1", SignalType.NEUTRAL, 0.0),
            LayerSignal("l2", SignalType.LONG, 0.8),
            LayerSignal("l3", SignalType.SHORT, 0.6),
        ]
        result = aggregate_signals(layers, LogicGate.NONE)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

    def test_none_all_neutral_returns_neutral(self):
        """Test that LogicGate.NONE with all NEUTRAL returns NEUTRAL."""
        layers = [
            LayerSignal("l1", SignalType.NEUTRAL, 0.0),
            LayerSignal("l2", SignalType.NEUTRAL, 0.0),
        ]
        result = aggregate_signals(layers, LogicGate.NONE)
        assert result.signal_type == SignalType.NEUTRAL
        assert result.confidence == 0.0

    def test_empty_layers_returns_neutral(self):
        """Test that empty layers return NEUTRAL for all logic gates."""
        for logic_gate in [LogicGate.AND, LogicGate.OR, LogicGate.WEIGHTED, LogicGate.NONE]:
            result = aggregate_signals([], logic_gate)
            assert result.signal_type == SignalType.NEUTRAL
            assert result.confidence == 0.0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_signal(self):
        """Test aggregation with a single signal."""
        layers = [LayerSignal("l1", SignalType.LONG, 0.8)]

        # AND
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

        # OR
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

        # WEIGHTED
        result = aggregate_signals_weighted(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

    def test_close_voting(self):
        """Test weighted voting with close scores."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8, weight=0.5),
            LayerSignal("l2", SignalType.SHORT, 0.9, weight=0.44),  # Close but loses
        ]
        result = aggregate_signals_weighted(layers)
        # LONG: 0.8 * 0.5 = 0.4
        # SHORT: 0.9 * 0.44 = 0.396
        assert result.signal_type == SignalType.LONG

    def test_all_three_signal_types(self):
        """Test with all three signal types (LONG, SHORT, CLOSE)."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 0.8),
            LayerSignal("l2", SignalType.SHORT, 0.7),
            LayerSignal("l3", SignalType.CLOSE, 0.6),
        ]

        # AND: Disagreement -> NEUTRAL
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.NEUTRAL

        # OR: Highest confidence
        result = aggregate_signals_or(layers)
        assert result.signal_type == SignalType.LONG
        assert result.confidence == 0.8

        # WEIGHTED (equal)
        result = aggregate_signals_weighted(layers)
        assert result.signal_type == SignalType.LONG  # 0.8 > 0.7 > 0.6

    def test_confidence_boundaries(self):
        """Test with confidence at boundaries (0.0 and 1.0)."""
        layers = [
            LayerSignal("l1", SignalType.LONG, 1.0),
            LayerSignal("l2", SignalType.LONG, 0.0),
        ]
        result = aggregate_signals_and(layers)
        assert result.confidence == 0.5

    def test_many_layers(self):
        """Test aggregation with many layers."""
        layers = [LayerSignal(f"l{i}", SignalType.LONG, 0.8) for i in range(10)]
        result = aggregate_signals_and(layers)
        assert result.signal_type == SignalType.LONG
        assert result.layer_count == 10
        assert result.agreement_count == 10
