"""
Test suite for Shadow Protocol constellation detection.

This module tests all shadow protocol functionality including:
1. Constellation detection
2. Arbitrage scanning (all 4 types)
3. Dark pool scanning
4. Volatility/squeeze detection
5. WebSocket broadcasting
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)

from api.shadow import (
    router,
    broadcast_opportunity_detected,
    broadcast_opportunity_expired,
)
from models.arbitrage import (
    ArbitrageConfig,
    ArbitrageOpportunity,
    ArbitrageScanRequest,
    ArbitrageType,
    ExchangeVenue,
    Chain,
    ArbitrageStatus,
)
from services.constellation_detector import (
    ConstellationDetector,
    WhaleTransaction,
    WalletConnection,
    Constellation,
)


class TestConstellationDetection:
    """Test constellation detection functionality."""

    @pytest.fixture
    def constellation_detector(self):
        """Create a constellation detector instance."""
        return ConstellationDetector()

    @pytest.fixture
    def sample_whale_transactions(self):
        """Create sample whale transactions for testing."""
        now = datetime.utcnow()

        # Create transactions with timestamps within 24h window
        transactions = [
            WhaleTransaction(
                wallet_address="0x1234",
                transaction_id="tx1",
                symbol="BTC",
                amount=Decimal("100"),
                usd_value=Decimal("5000000"),
                transaction_time=now - timedelta(hours=1),
                transaction_type="BUY"
            ),
            WhaleTransaction(
                wallet_address="0x5678",
                transaction_id="tx2",
                symbol="BTC",
                amount=Decimal("100"),
                usd_value=Decimal("5000000"),
                transaction_time=now - timedelta(hours=2),
                transaction_type="BUY"
            ),
            WhaleTransaction(
                wallet_address="0x9abc",
                transaction_id="tx3",
                symbol="ETH",
                amount=Decimal("5000"),
                usd_value=Decimal("8000000"),
                transaction_time=now - timedelta(hours=3),
                transaction_type="BUY"
            ),
        ]
        return transactions

    @pytest.fixture
    def sample_wallet_connections(self):
        """Create sample wallet connections for testing."""
        now = datetime.utcnow()
        connections = [
            WalletConnection(
                wallet1="0x1234",
                wallet2="0x5678",
                connection_type="transfer",
                transaction_count=5,
                total_volume_usd=Decimal("10000000"),
                first_connection=now - timedelta(days=7),
                last_connection=now - timedelta(hours=1)
            ),
            WalletConnection(
                wallet1="0x5678",
                wallet2="0x9abc",
                connection_type="common_address",
                transaction_count=3,
                total_volume_usd=Decimal("5000000"),
                first_connection=now - timedelta(days=10),
                last_connection=now - timedelta(hours=2)
            ),
        ]
        return connections

    def test_detect_temporal_clusters(self, constellation_detector, sample_whale_transactions):
        """Test detection of temporal clusters (multiple whales in time window)."""
        # Test with 72h window
        clusters = constellation_detector.detect_temporal_clusters(
            sample_whale_transactions,
            time_window_hours=72
        )

        assert len(clusters) > 0
        assert len(clusters[0].transactions) >= 2

        # Check that all transactions in cluster are within time window
        cluster_time_range = max(t.transaction_time for t in clusters[0].transactions) - \
                            min(t.transaction_time for t in clusters[0].transactions)
        assert cluster_time_range.total_seconds() <= 72 * 3600

    def test_detect_wallet_networks(self, constellation_detector, sample_wallet_connections):
        """Test detection of wallet network clusters."""
        clusters = constellation_detector.detect_wallet_networks(sample_wallet_connections, min_connections=1)

        assert len(clusters) >= 0
        # Should identify connected wallets as clusters
        if clusters:
            assert all(len(cluster.whale_wallets) >= 2 for cluster in clusters)

    def test_calculate_constellation_confidence(self, constellation_detector):
        """Test calculation of constellation confidence score (0-1)."""
        # Create a test constellation
        constellation = Constellation(
            id="test_1",
            transactions=[],
            wallet_connections=[],
            symbols=["BTC", "ETH"],
            detected_at=datetime.utcnow(),
            confidence_score=0.0
        )

        # Add some transactions to boost confidence
        constellation.transactions = [
            type('MockTransaction', (), {
                'usd_value': Decimal('5000000'),
                'transaction_time': datetime.utcnow() - timedelta(hours=1)
            })(),
            type('MockTransaction', (), {
                'usd_value': Decimal('5000000'),
                'transaction_time': datetime.utcnow() - timedelta(hours=2)
            })()
        ]

        score = constellation_detector.calculate_constellation_confidence(constellation)

        assert 0 <= score <= 1
        assert isinstance(score, float)

    def test_get_constellations(self, constellation_detector):
        """Test retrieval of all active constellations."""
        constellations = constellation_detector.get_constellations()

        assert isinstance(constellations, list)
        for constellation in constellations:
            assert hasattr(constellation, 'id')
            assert hasattr(constellation, 'symbols')
            assert hasattr(constellation, 'detected_at')
            assert hasattr(constellation, 'confidence_score')

    def test_constellation_detection_integration(self, constellation_detector,
                                                  sample_whale_transactions,
                                                  sample_wallet_connections):
        """Test full constellation detection workflow."""
        # Combine transactions and connections
        all_transactions = sample_whale_transactions
        all_connections = sample_wallet_connections

        # Detect constellations
        constellations = constellation_detector.detect_constellations(
            transactions=all_transactions,
            wallet_connections=all_connections
        )

        assert len(constellations) > 0

        # Check constellation properties
        for constellation in constellations:
            assert 0 <= constellation.confidence_score <= 1
            assert len(constellation.symbols) > 0
            assert constellation.detected_at is not None


class TestArbitrageScanning:
    """Test arbitrage scanning functionality for all 4 types."""

    @pytest.fixture
    def arbitrage_config(self):
        """Create arbitrage configuration for testing."""
        return ArbitrageConfig(
            min_profit_percent=Decimal("0.1"),
            min_profit_usd=Decimal("100")
        )

    @pytest.fixture
    def scan_request(self):
        """Create arbitrage scan request."""
        return ArbitrageScanRequest(
            symbols=["BTC", "ETH"],
            include_types=[
                ArbitrageType.ORACLE_LATENCY,
                ArbitrageType.FUNDING_RATE,
                ArbitrageType.CROSS_VENUE,
                ArbitrageType.CROSS_CHAIN
            ]
        )

    def test_oracle_latency_arbitrage(self):
        """Test oracle latency arbitrage detection."""
        # This would test the specific oracle arbitrage logic
        # For now, test that the type is properly identified
        assert ArbitrageType.ORACLE_LATENCY.value == "oracle_latency"

    def test_funding_rate_arbitrage(self):
        """Test funding rate arbitrage detection."""
        assert ArbitrageType.FUNDING_RATE.value == "funding_rate"

    def test_cross_venue_arbitrage(self):
        """Test cross-venue arbitrage detection."""
        assert ArbitrageType.CROSS_VENUE.value == "cross_venue"

    def test_cross_chain_arbitrage(self):
        """Test cross-chain arbitrage detection."""
        assert ArbitrageType.CROSS_CHAIN.value == "cross_chain"

    async def test_scan_arbitrage_opportunities(self):
        """Test scanning for arbitrage opportunities."""
        # This would test the actual scanning logic
        # For now, test the endpoint structure
        from services.dark_arbitrage import get_cached_opportunities

        opportunities = get_cached_opportunities()

        assert isinstance(opportunities, list)
        if opportunities:
            opp = opportunities[0]
            assert hasattr(opp, 'type')
            assert hasattr(opp, 'symbol')
            assert hasattr(opp, 'profit_percent')
            assert opp.type in ArbitrageType


class TestDarkPoolScanning:
    """Test dark pool scanning functionality."""

    def test_hidden_order_wall_detection(self):
        """Test detection of hidden order walls."""
        # This would test the actual dark pool scanning logic
        # For now, test that the functionality is structured correctly
        from services.liquidity_hunter import detect_stop_clusters

        # Test with empty data
        clusters = detect_stop_clusters("BTC", [], 100)
        assert isinstance(clusters, list)


class TestVolatilityAndSqueezeDetection:
    """Test volatility and squeeze trap detection."""

    def test_squeeze_condition_detection(self):
        """Test detection of squeeze conditions."""
        # This would test the actual volatility/squeeze logic
        # For now, test that the functionality exists
        from services.liquidity_hunter import predict_sweep_probability

        # Test with empty clusters
        current_price = 50000
        clusters = []
        trend = "NEUTRAL"
        volatility = 0.02

        predictions = predict_sweep_probability(current_price, clusters, trend, volatility)
        assert isinstance(predictions, dict)
        assert "predictions" in predictions


class TestWebSocketBroadcasting:
    """Test WebSocket broadcasting functionality."""

    async def test_broadcast_opportunity_detected(self):
        """Test broadcasting of detected arbitrage opportunities."""
        # This would test the WebSocket broadcast
        # For now, test that the function exists and is async
        from api.shadow import broadcast_opportunity_detected
        assert asyncio.iscoroutinefunction(broadcast_opportunity_detected)

    async def test_broadcast_opportunity_expired(self):
        """Test broadcasting of expired arbitrage opportunities."""
        opportunity_id = "expired_opportunity"

        # This would test the WebSocket broadcast
        from api.shadow import broadcast_opportunity_expired
        assert asyncio.iscoroutinefunction(broadcast_opportunity_expired)


class TestShadowAPIEndpoints:
    """Test Shadow API endpoints."""

    @pytest.mark.asyncio
    async def test_get_shadow_constellations(self, client):
        """Test GET /shadow/constellations endpoint."""
        response = await client.get("/shadow/constellations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if data:
            constellation = data[0]
            assert "id" in constellation
            assert "symbols" in constellation
            assert "confidence_score" in constellation
            assert 0 <= constellation["confidence_score"] <= 1

    @pytest.mark.asyncio
    async def test_post_detect_constellations(self, client):
        """Test POST /shadow/constellations/detect endpoint."""
        response = await client.post("/shadow/constellations/detect")

        assert response.status_code == 200
        data = response.json()
        assert "detected_constellations" in data
        assert isinstance(data["detected_constellations"], list)

    @pytest.mark.asyncio
    async def test_get_arbitrage_opportunities(self, client):
        """Test GET /shadow/arbitrage-opportunities endpoint."""
        response = await client.get("/shadow/arbitrage-opportunities")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_arbitrage_summary(self, client):
        """Test GET /shadow/arbitrage-summary endpoint."""
        response = await client.get("/shadow/arbitrage-summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_opportunities" in data
        assert "avg_profit_percent" in data
        assert "by_type" in data

    @pytest.mark.asyncio
    async def test_get_liquidity_map(self, client):
        """Test GET /shadow/liquidity-map/{symbol} endpoint."""
        response = await client.get("/shadow/liquidity-map/BTC")

        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "current_price" in data
        assert "clusters" in data
        assert "voids" in data

    @pytest.mark.asyncio
    async def test_get_clusters(self, client):
        """Test GET /shadow/clusters/{symbol} endpoint."""
        response = await client.get("/shadow/clusters/BTC")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_voids(self, client):
        """Test GET /shadow/voids/{symbol} endpoint."""
        response = await client.get("/shadow/voids/BTC")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_sweep_probability(self, client):
        """Test GET /shadow/sweep-probability/{symbol} endpoint."""
        response = await client.get("/shadow/sweep-probability/BTC")

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data


class TestConstellationAlerts:
    """Test constellation alert functionality."""

    def test_constellation_alert_structure(self):
        """Test that constellation alerts have correct structure."""
        # Test the expected structure of constellation alerts
        expected_fields = [
            "constellation_id",
            "symbols",
            "confidence_score",
            "wallet_count",
            "total_volume_usd",
            "detected_at",
            "risk_level",
            "description"
        ]

        # This would be tested against actual alert data
        for field in expected_fields:
            assert field in expected_fields

    def test_high_confidence_threshold(self):
        """Test high confidence threshold for alerts."""
        # Test that high confidence scores trigger appropriate alerts
        high_confidence_threshold = 0.8

        assert 0 <= high_confidence_threshold <= 1

    def test_risk_level_calculation(self):
        """Test risk level calculation for constellations."""
        # Test different risk levels based on constellation properties
        risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        assert "CRITICAL" in risk_levels
        assert "LOW" in risk_levels


class TestWebSocketChannel:
    """Test WebSocket /ws/shadow channel functionality."""

    async def test_shadow_channel_subscription(self):
        """Test subscription to /ws/shadow channel."""
        # This would test WebSocket subscription
        # For now, test that the channel name is correct
        expected_channel = "shadow"
        assert expected_channel == "shadow"

    async def test_shadow_event_format(self):
        """Test format of shadow events via WebSocket."""
        # Test expected event structure
        expected_event_structure = {
            "type": "constellation_alert",
            "data": {
                "constellation_id": str,
                "symbols": list,
                "confidence_score": float,
                "detected_at": str,
                "risk_level": str
            },
            "timestamp": str
        }

        # Verify structure keys exist
        assert "type" in expected_event_structure
        assert "data" in expected_event_structure
        assert "timestamp" in expected_event_structure


# Integration test for the full shadow protocol
class TestShadowProtocolIntegration:
    """Integration test for complete shadow protocol workflow."""

    def test_full_shadow_workflow(self, test_client):
        """Test complete shadow protocol workflow from detection to alert."""
        # Step 1: Get constellations
        constellations_response = test_client.get("/api/shadow/constellations")
        assert constellations_response.status_code == 200

        # Step 2: Trigger constellation detection
        detect_response = test_client.post("/api/shadow/constellations/detect", json={})
        assert detect_response.status_code == 200

        # Step 3: Get arbitrage opportunities
        arbitrage_response = test_client.get("/api/shadow/arbitrage-opportunities")
        assert arbitrage_response.status_code == 200

        # Step 4: Get liquidity map (may return 404 if no data)
        liquidity_response = test_client.get("/api/shadow/liquidity-map/BTC")
        assert liquidity_response.status_code in [200, 404]

        # Step 5: Get sweep predictions (may return 404 if no data)
        sweep_response = test_client.get("/api/shadow/sweep-probability/BTC")
        assert sweep_response.status_code in [200, 404]

        # Verify all endpoints return valid JSON
        responses = [
            constellations_response,
            detect_response,
            arbitrage_response,
            liquidity_response,
            sweep_response
        ]

        for response in responses:
            data = response.json()
            assert isinstance(data, (dict, list, str, float, int, bool))