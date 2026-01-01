"""
Constellation Detection Service for Shadow Protocol.

Detects coordinated whale movements and wallet network clusters
to identify potential market manipulation patterns.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from decimal import Decimal
import statistics

from models.arbitrage import ArbitrageType


@dataclass
class WhaleTransaction:
    """Represents a whale transaction for constellation analysis."""

    wallet_address: str
    transaction_id: str
    symbol: str
    amount: Decimal
    usd_value: Decimal
    transaction_time: datetime
    transaction_type: str  # BUY, SELL, TRANSFER
    fee: Optional[Decimal] = None
    gas_used: Optional[int] = None
    block_number: Optional[int] = None


@dataclass
class WalletConnection:
    """Represents a connection between wallets."""

    wallet1: str
    wallet2: str
    connection_type: str  # transfer, common_address, co_wallet, interaction
    transaction_count: int
    total_volume_usd: Decimal
    first_connection: datetime
    last_connection: datetime


@dataclass
class Constellation:
    """Represents a detected constellation of coordinated activity."""

    id: str
    transactions: List[WhaleTransaction]
    wallet_connections: List[WalletConnection]
    symbols: List[str]
    detected_at: datetime
    confidence_score: float
    temporal_cluster_score: float = 0.0
    network_cluster_score: float = 0.0
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    description: str = ""
    whale_wallets: Set[str] = field(default_factory=set)
    estimated_total_volume_usd: Decimal = Decimal("0")


class ConstellationDetector:
    """Detects coordinated whale activity across multiple dimensions."""

    def __init__(self):
        self.constellations: List[Constellation] = []
        self.whale_threshold_usd = Decimal("1000000")  # $1M minimum
        self.time_window_hours = 72  # Default 72h window
        self.connection_threshold = 3  # Minimum connections to form cluster

    def detect_temporal_clusters(self,
                                transactions: List[WhaleTransaction],
                                time_window_hours: int = 72,
                                symbol: Optional[str] = None) -> List[Constellation]:
        """
        Detect temporal clusters - multiple whales acting within time window.

        Args:
            transactions: List of whale transactions
            time_window_hours: Time window to look for clustering
            symbol: Optional symbol to filter by

        Returns:
            List of temporal cluster constellations
        """
        if not transactions:
            return []

        # Filter by symbol if specified
        if symbol:
            transactions = [t for t in transactions if t.symbol.upper() == symbol.upper()]

        # Sort by time
        transactions.sort(key=lambda x: x.transaction_time)

        constellations = []

        # Use sliding window to find clusters
        window_size = time_window_hours * 3600  # Convert to seconds

        for i, transaction in enumerate(transactions):
            window_start = transaction.transaction_time
            window_end = window_start + timedelta(seconds=window_size)

            # Find transactions within window
            cluster_txs = [
                t for t in transactions[i:]
                if t.transaction_time <= window_end
            ]

            # Only consider clusters with multiple unique whales
            unique_whales = set(t.wallet_address for t in cluster_txs)
            if len(unique_whales) >= 2:
                # Create constellation
                constellation_id = f"temporal_{int(datetime.utcnow().timestamp())}_{i}"

                # Calculate cluster score based on:
                # 1. Number of whales
                # 2. Total volume
                # 3. Time concentration

                whale_count = len(unique_whales)
                total_volume = sum(t.usd_value for t in cluster_txs)

                # Time concentration - how concentrated are the transactions?
                times = [t.transaction_time for t in cluster_txs]
                time_span = (max(times) - min(times)).total_seconds()
                concentration = 1.0 - (time_span / window_size) if window_size > 0 else 1.0

                # Combine factors for temporal score
                temporal_score = min(1.0, (whale_count * 0.3) +
                                   (float(total_volume) / 10000000 * 0.3) +
                                   (concentration * 0.4))

                constellation = Constellation(
                    id=constellation_id,
                    transactions=cluster_txs,
                    wallet_connections=[],
                    symbols=list(set(t.symbol for t in cluster_txs)),
                    detected_at=datetime.utcnow(),
                    confidence_score=0.0,  # Will be calculated later
                    temporal_cluster_score=temporal_score,
                    risk_level=self._calculate_temporal_risk(whale_count, total_volume, temporal_score),
                    description=f"Temporal cluster: {whale_count} whales, ${total_volume:,.0f} volume",
                    whale_wallets=unique_whales,
                    estimated_total_volume_usd=total_volume
                )

                constellations.append(constellation)

        return constellations

    def detect_wallet_networks(self,
                              connections: List[WalletConnection],
                              min_connections: int = 2) -> List[Constellation]:
        """
        Detect wallet network clusters - connected wallets forming networks.

        Args:
            connections: List of wallet connections
            min_connections: Minimum connections to form a cluster

        Returns:
            List of network cluster constellations
        """
        if not connections:
            return []

        # Build graph of wallet connections
        graph = {}
        for conn in connections:
            if conn.wallet1 not in graph:
                graph[conn.wallet1] = []
            if conn.wallet2 not in graph:
                graph[conn.wallet2] = []
            graph[conn.wallet1].append(conn.wallet2)
            graph[conn.wallet2].append(conn.wallet1)

        # Find connected components (clusters)
        visited = set()
        constellations = []

        for wallet in graph:
            if wallet not in visited:
                # BFS to find connected component
                cluster_wallets = self._bfs_find_cluster(graph, wallet, visited)

                if len(cluster_wallets) >= min_connections:
                    # Find connections within this cluster
                    cluster_connections = [
                        conn for conn in connections
                        if conn.wallet1 in cluster_wallets and conn.wallet2 in cluster_wallets
                    ]

                    # Calculate network score based on:
                    # 1. Size of cluster
                    # 2. Connection density
                    # 3. Total volume

                    cluster_size = len(cluster_wallets)
                    total_volume = sum(conn.total_volume_usd for conn in cluster_connections)

                    # Connection density - how well connected is the cluster?
                    max_possible = cluster_size * (cluster_size - 1) / 2
                    density = len(cluster_connections) / max_possible if max_possible > 0 else 0

                    network_score = min(1.0, (cluster_size * 0.2) +
                                      (density * 0.4) +
                                      (float(total_volume) / 50000000 * 0.4))

                    constellation_id = f"network_{int(datetime.utcnow().timestamp())}"

                    constellation = Constellation(
                        id=constellation_id,
                        transactions=[],  # Would need transaction data
                        wallet_connections=cluster_connections,
                        symbols=[],  # Would need symbol data
                        detected_at=datetime.utcnow(),
                        confidence_score=0.0,  # Will be calculated later
                        network_cluster_score=network_score,
                        risk_level=self._calculate_network_risk(cluster_size, density, total_volume),
                        description=f"Network cluster: {cluster_size} wallets, {len(cluster_connections)} connections",
                        whale_wallets=set(cluster_wallets),
                        estimated_total_volume_usd=total_volume
                    )

                    constellations.append(constellation)

        return constellations

    def calculate_constellation_confidence(self, constellation: Constellation) -> float:
        """
        Calculate overall confidence score for a constellation (0-1).

        Args:
            constellation: The constellation to score

        Returns:
            Confidence score between 0 and 1
        """
        if not constellation.transactions and not constellation.wallet_connections:
            return 0.0

        # Weight factors
        weights = {
            'temporal': 0.4,
            'network': 0.4,
            'volume': 0.2
        }

        # Base scores
        temporal_score = getattr(constellation, 'temporal_cluster_score', 0.0)
        network_score = getattr(constellation, 'network_cluster_score', 0.0)

        # Volume score based on total USD value
        volume_usd = constellation.estimated_total_volume_usd
        volume_score = min(1.0, float(volume_usd) / 100000000)  # Normalize to $100M

        # Calculate weighted score
        confidence = (
            temporal_score * weights['temporal'] +
            network_score * weights['network'] +
            volume_score * weights['volume']
        )

        return round(confidence, 4)

    def detect_constellations(self,
                            transactions: List[WhaleTransaction],
                            wallet_connections: List[WalletConnection]) -> List[Constellation]:
        """
        Main constellation detection method combining all analysis.

        Args:
            transactions: List of whale transactions
            wallet_connections: List of wallet connections

        Returns:
            Complete list of detected constellations
        """
        # Detect temporal clusters
        temporal_constellations = self.detect_temporal_clusters(transactions)

        # Detect network clusters
        network_constellations = self.detect_wallet_networks(wallet_connections)

        # Combine and enhance with transaction data
        all_constellations = temporal_constellations + network_constellations

        # Enhance network constellations with transaction data
        for constellation in network_constellations:
            # Find transactions involving cluster wallets
            cluster_txs = [
                t for t in transactions
                if t.wallet_address in constellation.whale_wallets
            ]

            if cluster_txs:
                constellation.transactions.extend(cluster_txs)
                # Update symbols
                symbols = list(set(t.symbol for t in cluster_txs))
                if symbols:
                    constellation.symbols.extend(symbols)
                    constellation.symbols = list(set(constellation.symbols))

                # Update total volume
                volume = sum(t.usd_value for t in cluster_txs)
                constellation.estimated_total_volume_usd += volume

        # Calculate final confidence scores
        for constellation in all_constellations:
            constellation.confidence_score = self.calculate_constellation_confidence(constellation)

        # Store and return
        self.constellations.extend(all_constellations)
        return all_constellations

    def get_constellations(self,
                         min_confidence: float = 0.3,
                         symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all active constellations with filtering.

        Args:
            min_confidence: Minimum confidence score to include
            symbols: Optional list of symbols to filter by

        Returns:
            List of constellation dictionaries
        """
        filtered = [
            c for c in self.constellations
            if c.confidence_score >= min_confidence
        ]

        if symbols:
            symbol_set = set(s.upper() for s in symbols)
            filtered = [
                c for c in filtered
                if any(s.upper() in symbol_set for s in c.symbols)
            ]

        # Convert to dictionary format
        result = []
        for constellation in filtered:
            result.append({
                "constellation_id": constellation.id,
                "symbols": constellation.symbols,
                "confidence_score": constellation.confidence_score,
                "risk_level": constellation.risk_level,
                "wallet_count": len(constellation.whale_wallets),
                "total_volume_usd": float(constellation.estimated_total_volume_usd),
                "temporal_score": getattr(constellation, 'temporal_cluster_score', 0.0),
                "network_score": getattr(constellation, 'network_cluster_score', 0.0),
                "description": constellation.description,
                "detected_at": constellation.detected_at.isoformat(),
                "recent_transactions": [
                    {
                        "wallet": t.wallet_address,
                        "symbol": t.symbol,
                        "usd_value": float(t.usd_value),
                        "time": t.transaction_time.isoformat(),
                        "type": t.transaction_type
                    }
                    for t in sorted(constellation.transactions,
                                  key=lambda x: x.transaction_time, reverse=True)[:10]
                ]
            })

        return sorted(result, key=lambda x: x['confidence_score'], reverse=True)

    def _bfs_find_cluster(self, graph: Dict[str, List[str]],
                         start_wallet: str, visited: Set[str]) -> Set[str]:
        """BFS to find connected component in wallet graph."""
        cluster = set()
        queue = [start_wallet]

        while queue:
            wallet = queue.pop(0)
            if wallet not in visited:
                visited.add(wallet)
                cluster.add(wallet)

                # Add connected wallets to queue
                for connected in graph.get(wallet, []):
                    if connected not in visited:
                        queue.append(connected)

        return cluster

    def _calculate_temporal_risk(self, whale_count: int,
                               total_volume: Decimal,
                               concentration: float) -> str:
        """Calculate risk level for temporal clusters."""
        if whale_count >= 5 and total_volume >= Decimal("50000000") and concentration >= 0.8:
            return "CRITICAL"
        elif whale_count >= 3 and total_volume >= Decimal("20000000") and concentration >= 0.6:
            return "HIGH"
        elif whale_count >= 2 and total_volume >= Decimal("10000000"):
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_network_risk(self, cluster_size: int,
                              density: float, total_volume: Decimal) -> str:
        """Calculate risk level for network clusters."""
        if cluster_size >= 10 and density >= 0.7 and total_volume >= Decimal("100000000"):
            return "CRITICAL"
        elif cluster_size >= 5 and density >= 0.5 and total_volume >= Decimal("50000000"):
            return "HIGH"
        elif cluster_size >= 3 and density >= 0.3:
            return "MEDIUM"
        else:
            return "LOW"

    def clear_old_constellations(self, hours_old: int = 168) -> None:
        """Clear constellations older than specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        self.constellations = [
            c for c in self.constellations
            if c.detected_at > cutoff_time
        ]