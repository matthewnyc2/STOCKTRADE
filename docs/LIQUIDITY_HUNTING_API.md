# Liquidity Hunting & Stop Detection API

## Overview

The Liquidity Hunting API detects stop-loss clusters, liquidity voids, and predicts when market makers may sweep liquidity. This is part of the Shadow API for analyzing market manipulation patterns.

## Base Path

All endpoints are prefixed with `/api/shadow`

## Endpoints

### 1. Get Complete Liquidity Map

**Endpoint:** `GET /api/shadow/liquidity-map/{symbol}`

**Description:** Returns complete liquidity analysis including clusters, voids, and sweep probabilities.

**Query Parameters:**
- `lookback` (optional, default=100): Number of periods to analyze (20-500)

### 2. Get Sweep Probability

**Endpoint:** `GET /api/shadow/sweep-probability/{symbol}`

**Description:** Returns probability of market makers sweeping each liquidity cluster.

### 3. Get Stop Clusters

**Endpoint:** `GET /api/shadow/clusters/{symbol}`

**Description:** Returns detected stop-loss clusters sorted by density.

### 4. Get Liquidity Voids

**Endpoint:** `GET /api/shadow/voids/{symbol}`

**Description:** Returns detected liquidity voids (price gaps).

### 5. Calculate Cascade Risk

**Endpoint:** `POST /api/shadow/cascade-risk/{symbol}`

**Description:** Calculate cascade risk if a specific level is triggered.

### 6. Get Round Number Levels

**Endpoint:** `GET /api/shadow/round-numbers/{symbol}`

**Description:** Returns psychological round number levels where traders often place stops.

### 7. Compare Liquidity Maps

**Endpoint:** `GET /api/shadow/liquidity/compare`

**Description:** Compare liquidity patterns across multiple symbols.

## Cluster Types

- **ROUND_NUMBER**: Psychological levels (e.g., $50,000, $100,000)
- **PREVIOUS_HIGH**: Previous swing high points
- **PREVIOUS_LOW**: Previous swing low points
- **RESISTANCE**: Resistance levels from price pivots
- **SUPPORT**: Support levels from price pivots
- **CONSOLIDATION_TOP**: Stops above consolidation ranges
- **CONSOLIDATION_BOTTOM**: Stops below consolidation ranges

## Risk Levels

- **LOW**: Minimal cascade risk
- **MEDIUM**: Moderate cascade risk
- **HIGH**: High cascade risk
- **CRITICAL**: Severe cascade risk expected

## Service Functions

The underlying service (`services/liquidity_hunter.py`) provides:

- `detect_stop_clusters(symbol, price_data)`: Find stop-loss concentrations
- `detect_liquidity_voids(symbol, price_data)`: Find price gaps with no liquidity
- `predict_sweep_probability(current_price, clusters)`: Likelihood of sweep
- `calculate_cascade_risk(triggered_stop, clusters, current_price)`: Cascade risk if triggered
- `get_liquidity_map(symbol, lookback)`: Complete analysis in one call
