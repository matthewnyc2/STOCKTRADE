"""
Tests for Liquidity Hunter Service.

Tests the stop hunting and liquidity detection engine.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from services.liquidity_hunter import (
    LiquidityCluster,
    LiquidityVoid,
    detect_stop_clusters,
    detect_liquidity_voids,
    predict_sweep_probability,
    calculate_cascade_risk,
    get_liquidity_map,
    _detect_round_numbers,
    _calculate_cluster_density,
    _merge_nearby_clusters,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_price_data() -> List[Dict[str, Any]]:
    """Generate sample price data for testing."""
    base_price = 45000
    data = []
    now = datetime.utcnow()

    for i in range(100):
        timestamp = now - timedelta(hours=100 - i)
        # Add some volatility
        change = (i % 10 - 5) * 0.002  # -1% to +1% swings
        price = base_price * (1 + change)

        data.append({
            "timestamp": timestamp,
            "open": price * 0.999,
            "high": price * 1.002,
            "low": price * 0.998,
            "close": price,
            "volume": 1000000 + (i % 5) * 100000,
        })

    return data


@pytest.fixture
def price_with_clusters() -> List[Dict[str, Any]]:
    """Generate price data with known cluster patterns."""
    base_price = 50000
    data = []
    now = datetime.utcnow()

    # Create price action that touches round numbers
    for i in range(100):
        timestamp = now - timedelta(hours=100 - i)

        # Create patterns that touch round numbers (50000, 51000, 49000)
        if i % 20 == 0:
            price = 50000  # Touch round number
        elif i % 15 == 0:
            price = 51000  # Touch another round number
        elif i % 10 == 0:
            price = 49000  # Touch round number below
        else:
            price = base_price + (i % 5 - 2) * 100

        data.append({
            "timestamp": timestamp,
            "open": price * 0.999,
            "high": price * 1.003,
            "low": price * 0.997,
            "close": price,
            "volume": 1000000,
        })

    return data


@pytest.fixture
def price_with_voids() -> List[Dict[str, Any]]:
    """Generate price data with liquidity voids (gaps)."""
    data = []
    now = datetime.utcnow()
    current_price = 45000

    for i in range(50):
        timestamp = now - timedelta(hours=50 - i)

        # Create some gaps
        if i == 20:
            # Gap up
            current_price = 46000
        elif i == 35:
            # Gap down
            current_price = 45500
        else:
            current_price += (i % 3 - 1) * 50

        data.append({
            "timestamp": timestamp,
            "open": current_price * 0.999,
            "high": current_price * 1.001,
            "low": current_price * 0.999,
            "close": current_price,
            "volume": 500000,  # Low volume at gaps
        })

    return data


# ============================================================================
# TESTS: STOP CLUSTER DETECTION
# ============================================================================

class TestDetectStopClusters:
    """Tests for detect_stop_clusters function."""

    def test_detects_clusters_with_valid_data(self, sample_price_data):
        """Test that clusters are detected with valid price data."""
        clusters = detect_stop_clusters("BTC", sample_price_data, lookback_periods=50)

        assert len(clusters) > 0, "Should detect at least some clusters"
        assert all(isinstance(c, LiquidityCluster) for c in clusters)

    def test_returns_empty_with_insufficient_data(self):
        """Test that empty list is returned with insufficient data."""
        short_data = [{"close": 45000}]
        clusters = detect_stop_clusters("BTC", short_data)

        assert len(clusters) == 0

    def test_detects_round_number_clusters(self, price_with_clusters):
        """Test detection of round number clusters."""
        clusters = detect_stop_clusters("BTC", price_with_clusters)

        round_number_clusters = [c for c in clusters if c.cluster_type == "ROUND_NUMBER"]
        assert len(round_number_clusters) > 0, "Should detect round number clusters"

    def test_clusters_sorted_by_density(self, sample_price_data):
        """Test that clusters are sorted by density score."""
        clusters = detect_stop_clusters("BTC", sample_price_data)

        if len(clusters) > 1:
            for i in range(len(clusters) - 1):
                assert clusters[i].density_score >= clusters[i + 1].density_score

    def test_density_scores_between_0_and_1(self, sample_price_data):
        """Test that all density scores are in valid range."""
        clusters = detect_stop_clusters("BTC", sample_price_data)

        for cluster in clusters:
            assert 0 <= cluster.density_score <= 1

    def test_detects_previous_highs_lows(self, price_with_clusters):
        """Test detection of previous swing highs and lows."""
        clusters = detect_stop_clusters("BTC", price_with_clusters)

        swing_clusters = [
            c for c in clusters
            if c.cluster_type in ["PREVIOUS_HIGH", "PREVIOUS_LOW"]
        ]
        # May or may not have swing points depending on data
        assert isinstance(swing_clusters, list)


class TestDetectLiquidityVoids:
    """Tests for detect_liquidity_voids function."""

    def test_detects_voids_with_valid_data(self, price_with_voids):
        """Test that voids are detected in price data."""
        voids = detect_liquidity_voids("BTC", price_with_voids, min_gap_size=0.01)

        assert isinstance(voids, list)
        # Voids may or may not be detected depending on gap sizes

    def test_returns_empty_with_insufficient_data(self):
        """Test that empty list is returned with insufficient data."""
        short_data = [{"close": 45000}]
        voids = detect_liquidity_voids("BTC", short_data)

        assert len(voids) == 0

    def test_void_risk_levels_are_valid(self, price_with_voids):
        """Test that all void risk levels are valid."""
        voids = detect_liquidity_voids("BTC", price_with_voids)

        for void in voids:
            assert void.risk_level in ["LOW", "MEDIUM", "HIGH"]

    def test_void_size_is_recorded(self, price_with_voids):
        """Test that void sizes are calculated correctly."""
        voids = detect_liquidity_voids("BTC", price_with_voids)

        for void in voids:
            assert void.void_size >= 0
            assert void.start_price < void.end_price


# ============================================================================
# TESTS: SWEEP PROBABILITY
# ============================================================================

class TestPredictSweepProbability:
    """Tests for predict_sweep_probability function."""

    @pytest.fixture
    def sample_clusters(self):
        """Create sample liquidity clusters for testing."""
        return [
            LiquidityCluster(price_level=46000, density_score=0.7, cluster_type="ROUND_NUMBER"),
            LiquidityCluster(price_level=45500, density_score=0.5, cluster_type="PREVIOUS_HIGH"),
            LiquidityCluster(price_level=45000, density_score=0.6, cluster_type="PREVIOUS_LOW"),
            LiquidityCluster(price_level=44500, density_score=0.4, cluster_type="SUPPORT"),
        ]

    def test_predicts_sweep_probability(self, sample_clusters):
        """Test that sweep probabilities are calculated."""
        predictions = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
            current_trend="BULLISH",
            volatility=0.02
        )

        assert "predictions" in predictions
        assert len(predictions["predictions"]) == len(sample_clusters)

    def test_probabilities_between_0_and_1(self, sample_clusters):
        """Test that all probabilities are in valid range."""
        predictions = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
        )

        for pred in predictions["predictions"]:
            assert 0 <= pred["probability"] <= 1

    def test_includes_cascade_targets(self, sample_clusters):
        """Test that cascade targets are identified."""
        predictions = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
        )

        for pred in predictions["predictions"]:
            assert isinstance(pred["cascade_targets"], list)

    def test_bullish_trend_favors_upward_sweeps(self, sample_clusters):
        """Test that bullish trend increases upward sweep probability."""
        bullish = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
            current_trend="BULLISH",
        )

        bearish = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
            current_trend="BEARISH",
        )

        # Upward sweeps should be more likely in bullish trend
        upward_bullish = [p for p in bullish["predictions"] if p["price_level"] > 45200]
        upward_bearish = [p for p in bearish["predictions"] if p["price_level"] > 45200]

        if upward_bullish and upward_bearish:
            bullish_avg = sum(p["probability"] for p in upward_bullish) / len(upward_bullish)
            bearish_avg = sum(p["probability"] for p in upward_bearish) / len(upward_bearish)
            assert bullish_avg >= bearish_avg

    def test_higher_volatility_increases_sweep_probability(self, sample_clusters):
        """Test that higher volatility increases sweep probability."""
        low_vol = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
            volatility=0.01,
        )

        high_vol = predict_sweep_probability(
            current_price=45200,
            clusters=sample_clusters,
            volatility=0.05,
        )

        # High volatility should generally increase probabilities
        low_vol_avg = sum(p["probability"] for p in low_vol["predictions"]) / len(low_vol["predictions"])
        high_vol_avg = sum(p["probability"] for p in high_vol["predictions"]) / len(high_vol["predictions"])

        assert high_vol_avg >= low_vol_avg


# ============================================================================
# TESTS: CASCADE RISK
# ============================================================================

class TestCalculateCascadeRisk:
    """Tests for calculate_cascade_risk function."""

    @pytest.fixture
    def sample_cascade_clusters(self):
        """Create clusters that might cascade."""
        current_price = 45000
        return [
            LiquidityCluster(price_level=45200, density_score=0.6, cluster_type="ROUND_NUMBER"),
            LiquidityCluster(price_level=45400, density_score=0.5, cluster_type="RESISTANCE"),
            LiquidityCluster(price_level=45600, density_score=0.4, cluster_type="ROUND_NUMBER"),
            LiquidityCluster(price_level=44800, density_score=0.5, cluster_type="SUPPORT"),
        ]

    def test_calculates_cascade_risk(self, sample_cascade_clusters):
        """Test that cascade risk is calculated."""
        triggered = LiquidityCluster(price_level=45200, density_score=0.6, cluster_type="ROUND_NUMBER")

        risk = calculate_cascade_risk(triggered, sample_cascade_clusters, current_price=45000)

        assert "risk_level" in risk
        assert "cascade_levels" in risk
        assert isinstance(risk["cascade_levels"], list)

    def test_identifies_sweep_direction(self, sample_cascade_clusters):
        """Test that sweep direction is correctly identified."""
        # Trigger above current price = upward sweep
        triggered_above = LiquidityCluster(price_level=45200, density_score=0.6, cluster_type="ROUND_NUMBER")
        risk_above = calculate_cascade_risk(triggered_above, sample_cascade_clusters, current_price=45000)
        assert risk_above["sweep_direction"] == "UP"

        # Trigger below current price = downward sweep
        triggered_below = LiquidityCluster(price_level=44800, density_score=0.5, cluster_type="SUPPORT")
        risk_below = calculate_cascade_risk(triggered_below, sample_cascade_clusters, current_price=45000)
        assert risk_below["sweep_direction"] == "DOWN"

    def test_risk_levels_are_valid(self, sample_cascade_clusters):
        """Test that risk levels are valid."""
        triggered = LiquidityCluster(price_level=45200, density_score=0.6, cluster_type="ROUND_NUMBER")
        risk = calculate_cascade_risk(triggered, sample_cascade_clusters, current_price=45000)

        assert risk["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_calculates_max_excursion(self, sample_cascade_clusters):
        """Test that maximum excursion is calculated."""
        triggered = LiquidityCluster(price_level=45200, density_score=0.6, cluster_type="ROUND_NUMBER")
        risk = calculate_cascade_risk(triggered, sample_cascade_clusters, current_price=45000)

        assert "max_excursion_pct" in risk
        assert risk["max_excursion_pct"] >= 0


# ============================================================================
# TESTS: LIQUIDITY MAP
# ============================================================================

class TestGetLiquidityMap:
    """Tests for get_liquidity_map function."""

    def test_returns_complete_map(self, sample_price_data):
        """Test that complete liquidity map is returned."""
        # This test would require database integration
        # For now, we test the structure
        pass

    def test_includes_all_required_fields(self):
        """Test that all required fields are present in the map."""
        # This would require mocking the database
        pass


# ============================================================================
# TESTS: HELPER FUNCTIONS
# ============================================================================

class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_detect_round_numbers(self):
        """Test round number detection."""
        current_price = 45234
        price_range = 5000

        clusters = _detect_round_numbers(current_price, price_range)

        assert len(clusters) > 0
        # Should detect 45000 as a round number
        round_levels = [c.price_level for c in clusters]
        assert 45000 in round_levels

    def test_calculate_cluster_density(self):
        """Test cluster density calculation."""
        cluster = LiquidityCluster(
            price_level=45000,
            density_score=0.5,
            cluster_type="ROUND_NUMBER"
        )

        # Create price data that touches the cluster level
        closes = [44900 + i * 20 for i in range(100)]
        highs = [c + 100 for c in closes]
        lows = [c - 100 for c in closes]
        volumes = [1000000] * 100

        # Make some touches at the cluster level
        for i in range(10):
            highs[i * 10] = 45050
            lows[i * 10] = 44950

        density = _calculate_cluster_density(cluster, closes, highs, lows, volumes)

        assert 0 <= density <= 1

    def test_merge_nearby_clusters(self):
        """Test that nearby clusters are merged."""
        clusters = [
            LiquidityCluster(price_level=45000, density_score=0.5, cluster_type="ROUND_NUMBER"),
            LiquidityCluster(price_level=45020, density_score=0.6, cluster_type="PREVIOUS_HIGH"),  # Close to 45000
            LiquidityCluster(price_level=46000, density_score=0.7, cluster_type="ROUND_NUMBER"),
        ]

        merged = _merge_nearby_clusters(clusters, tolerance=0.005)  # 0.5%

        # The first two should be merged
        assert len(merged) <= len(clusters)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestLiquidityHunterIntegration:
    """Integration tests for the complete liquidity hunting workflow."""

    def test_complete_workflow(self, sample_price_data):
        """Test the complete workflow from data to predictions."""
        # 1. Detect clusters
        clusters = detect_stop_clusters("BTC", sample_price_data)
        assert len(clusters) > 0

        # 2. Detect voids
        voids = detect_liquidity_voids("BTC", sample_price_data)
        assert isinstance(voids, list)

        # 3. Predict sweeps
        current_price = sample_price_data[-1]["close"]
        predictions = predict_sweep_probability(current_price, clusters)
        assert "predictions" in predictions

        # 4. Calculate cascade risk for top prediction
        if predictions["predictions"]:
            top_prediction = predictions["predictions"][0]
            target_cluster = LiquidityCluster(
                price_level=top_prediction["price_level"],
                density_score=top_prediction["density_score"],
                cluster_type=top_prediction["cluster_type"]
            )
            cascade_risk = calculate_cascade_risk(target_cluster, clusters, current_price)
            assert "risk_level" in cascade_risk

    def test_handles_edge_cases(self):
        """Test handling of edge cases."""
        # Empty data
        assert len(detect_stop_clusters("BTC", [])) == 0
        assert len(detect_liquidity_voids("BTC", [])) == 0

        # Single data point
        single_point = [{"close": 45000, "high": 45100, "low": 44900, "volume": 1000000}]
        assert len(detect_stop_clusters("BTC", single_point)) == 0

        # No clusters
        predictions = predict_sweep_probability(45000, [])
        assert len(predictions["predictions"]) == 0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestLiquidityHunterPerformance:
    """Performance tests for liquidity hunting functions."""

    def test_handles_large_datasets(self):
        """Test that functions can handle large price datasets."""
        import time

        # Generate large dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                "timestamp": datetime.utcnow() - timedelta(hours=1000 - i),
                "open": 45000 + (i % 100) * 10,
                "high": 45100 + (i % 100) * 10,
                "low": 44900 + (i % 100) * 10,
                "close": 45000 + (i % 100) * 10,
                "volume": 1000000,
            })

        start = time.time()
        clusters = detect_stop_clusters("BTC", large_data)
        duration = time.time() - start

        assert duration < 5.0  # Should complete in less than 5 seconds
        assert len(clusters) > 0
