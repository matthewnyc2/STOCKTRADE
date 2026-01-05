# Architect 7 Context: Feature Implementation

**Generated**: 2026-01-03
**Architect ID**: 7
**Feature**: Complete Whale Tracking (BFS behavioral patterns) and Historical Data Manager (active gap detection)
**Priority**: HIGH
**Complexity**: HIGH

---

## Current State

### Whale Tracking - BFS Behavioral Patterns

**Current Implementation**: `services/whale_tracker.py`

**Current BFS Usage**:
- BFS used for wallet network connectivity only
- Simple pattern detection: buy/sell ratios
- No multi-step behavioral sequence detection

**Current Pattern Classification**:
```python
class WhalePattern(str, Enum):
    ACCUMULATOR = "accumulator"      # Buys consistently
    DISTRIBUTOR = "distributor"      # Sells consistently
    SNIPER = "sniper"                # Large single trades
    MANIPULATOR = "manipulator"      # Suspect behavior
```

**Issues**:
- No complex pattern detection (Accumulate → Wash → Manipulate)
- No multi-hop wallet analysis
- Limited behavioral understanding

### Historical Data Manager - Active Gap Detection

**Current Implementation**: `services/historical_data_manager.py`

**Current Gap Detection**:
- Batch-only (manual trigger)
- No active/real-time monitoring
- Binance only for OHLCV data
- Imprecise backfill (fetches latest N candles, not specific time ranges)

**Current Exchange Support**:
- Binance: Full OHLCV support
- CoinGecko: No OHLCV support
- Kraken: No OHLCV support
- KuCoin/Bybit: No OHLCV support

**Issues**:
- No active monitoring for gaps
- Missing OHLCV support for failover exchanges
- Backfill imprecise (may miss gaps or duplicate data)

---

## Desired State

### Whale Tracking - BFS Behavioral Patterns

**Enhanced BFS Usage**:
- Detect complex multi-step behavioral patterns
- Pattern: Accumulate → Wash → Manipulate sequence
- Multi-hop wallet analysis (wallets interacting with manipulators)

**New Pattern Classification**:
```python
class WhalePattern(str, Enum):
    ACCUMULATOR = "accumulator"
    DISTRIBUTOR = "distributor"
    SNIPER = "sniper"
    MANIPULATOR = "manipulator"
    WASH_TRADER = "wash_trader"        # NEW: Buys and sells to self
    PUMP_AND_DUMP = "pump_and_dump"    # NEW: Accumulate, pump, dump
    FRONT_RUNNER = "front_runner"      # NEW: Trades before large movements
```

**BFS Algorithm**:
1. Start from target whale wallet
2. Traverse transaction graph (BFS)
3. Detect behavioral patterns across wallet network
4. Identify multi-step manipulation sequences

### Historical Data Manager - Active Gap Detection

**Active Gap Detection**:
- Background task runs continuously (e.g., every hour)
- Detects gaps in real-time
- Triggers backfill automatically

**OHLCV Support for All Exchanges**:
- Binance: Existing implementation
- CoinGecko: NEW - Implement `get_ohlcv()`
- Kraken: NEW - Implement `get_ohlcv()`
- KuCoin: NEW - Implement `get_ohlcv()` (optional)
- Bybit: NEW - Implement `get_ohlcv()` (optional)

**Precise Backfill**:
- Use specific `startTime` and `endTime` parameters
- Fetch only missing data
- Avoid duplicate data
- Precise gap filling

---

## Specific Tasks

### Whale Tracking - BFS Behavioral Patterns

#### Task 1: Analyze Current Whale Tracking Implementation
- Read `services/whale_tracker.py`
- Identify current pattern detection logic
- Identify current BFS implementation
- Map existing behavior to desired behavior

#### Task 2: Enhance classify_whale_pattern with BFS
- Update `classify_whale_pattern()` function
- Add BFS-based behavioral detection
- Detect multi-step sequences (Accumulate → Wash → Manipulate)
- Implement algorithm:
  1. BFS traverse wallet network
  2. Track transaction sequence
  3. Classify based on sequence patterns
  4. Return pattern + confidence score

#### Task 3: Add Multi-step Sequence Detection
- Add detection for 3+ step manipulation patterns
- Patterns:
  - Accumulate → Wash → Manipulate
  - Pump → Dump → Wash
  - Front run → Execute → Profit
- Implement sequence matching algorithm
- Return matched sequences with timestamps

#### Task 4: Update Constellation Detection
- Read `services/constellation_detector.py`
- Incorporate behavioral clustering
- Use BFS results to cluster manipulator networks
- Identify whale constellations
- Update constellation scoring

#### Task 5: Add New Whale Patterns
- Add `WASH_TRADER` to WhalePattern enum
- Add `PUMP_AND_DUMP` to WhalePattern enum
- Add `FRONT_RUNNER` to WhalePattern enum
- Update database migrations if needed
- Update Pydantic models

#### Task 6: Write Whale Tracking Tests
- Create `tests/test_whale_tracking_bfs.py`
- Test BFS pattern detection
- Test multi-step sequence detection
- Test new whale patterns
- Test constellation detection integration
- Verify all tests pass

### Historical Data Manager - Active Gap Detection

#### Task 7: Add get_ohlcv to CoinGeckoDataSource
- Read `services/multi_source_manager.py`
- Locate CoinGeckoDataSource class
- Implement `get_ohlcv(symbol, interval, startTime, endTime)` method
- Use CoinGecko API for historical candle data
- Return OHLCV data in standard format
- Error handling for API limits

#### Task 8: Add get_ohlcv to KrakenDataSource
- Locate KrakenDataSource class
- Implement `get_ohlcv(symbol, interval, startTime, endTime)` method
- Use Kraken API for historical candle data
- Return OHLCV data in standard format
- Error handling for API limits

#### Task 9: Update BinanceDataSource.get_ohlcv
- Locate BinanceDataSource class
- Verify `get_ohlcv()` exists
- Add `startTime` and `endTime` parameters (if not present)
- Ensure precise time range fetching
- Test with specific time ranges

#### Task 10: Create Background Task for Active Gap Detection
- Read `services/background_tasks.py`
- Create `GapDetector` class or function
- Implement `run_daily()` method:
  1. Check all symbols for gaps
  2. Identify missing time ranges
  3. Trigger backfill for gaps
- Add to background task scheduler (e.g., run every hour)

#### Task 11: Implement Precise Backfill
- Read `services/historical_data_manager.py`
- Locate backfill logic
- Update to use specific `startTime` and `endTime`
- Fetch only missing data (no duplicates)
- Use exchange failover (Binance → CoinGecko → Kraken)
- Verify data integrity

#### Task 12: Write Historical Data Manager Tests
- Create `tests/test_historical_data_active.py`
- Test CoinGecko OHLCV fetching
- Test Kraken OHLCV fetching
- Test precise backfill with time ranges
- Test active gap detection background task
- Test exchange failover
- Verify all tests pass

#### Task 13: Integration Tests
- Run full whale tracking workflow with BFS
- Run full historical data workflow with active gap detection
- Verify end-to-end functionality
- Check for any regressions

---

## Critical Considerations

### BFS Algorithm Complexity
- BFS can be expensive on large wallet networks
- Limit BFS depth (e.g., max 5 hops)
- Cache BFS results
- Optimize traversal (visited set, early termination)

### Pattern Detection Accuracy
- Behavioral patterns can be false positives
- Add confidence scores to pattern detection
- Require multiple data points for classification
- Test with real whale data

### Exchange API Rate Limits
- CoinGecko, Kraken have rate limits
- Implement rate limiting / backoff
- Use pagination for large time ranges
- Cache data to reduce API calls

### Background Task Reliability
- Background tasks must be idempotent
- Handle failures gracefully (retry logic)
- Log all gap detections and backfills
- Monitor task execution

### Data Integrity
- Precise backfill must avoid duplicates
- Verify data timestamps don't overlap
- Validate OHLCV data format
- Test with edge cases (empty ranges, single candle)

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| BFS performance issues on large networks | HIGH | Limit depth, cache results, optimize traversal |
| False positive pattern detection | MEDIUM | Add confidence scores, require multiple data points |
| Exchange API rate limits | MEDIUM | Implement rate limiting, pagination, caching |
| Background task failures | MEDIUM | Add retry logic, logging, monitoring |
| Data duplication in backfill | HIGH | Verify no timestamp overlap, validate data |

---

## Success Criteria

### Whale Tracking - BFS Behavioral Patterns
- [ ] BFS implemented for pattern detection
- [ ] Multi-step sequence detection works
- [ ] New whale patterns added (WASH_TRADER, PUMP_AND_DUMP, FRONT_RUNNER)
- [ ] Constellation detection updated
- [ ] Whale tracking tests pass
- [ ] Pattern detection accuracy verified

### Historical Data Manager - Active Gap Detection
- [ ] CoinGeckoDataSource.get_ohlcv() implemented
- [ ] KrakenDataSource.get_ohlcv() implemented
- [ ] BinanceDataSource.get_ohlcv() updated with precise parameters
- [ ] Background task for active gap detection created
- [ ] Precise backfill implemented
- [ ] Historical data manager tests pass
- [ ] Exchange failover works correctly

### Integration
- [ ] Full whale tracking workflow works
- [ ] Full historical data workflow works
- [ ] No regressions in existing features
- [ ] Performance acceptable (BFS, background tasks)
- [ ] API rate limits respected

---

## Notes

- **DO NOT** implement unlimited BFS depth (performance risk)
- **DO NOT** skip API rate limiting (exchange bans)
- **DO NOT** duplicate data in backfill (integrity risk)
- **DO** add confidence scores to pattern detection
- **DO** test with real whale data
- **DO** log all background task activity

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 5)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 7)
- Codebase knowledge: `AGENTS.md` (Whale Tracking, Historical Data Manager sections)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the feature (BFS pattern, OHLCV fetching, gap detection)
2. CODE_WRITER: Implement the feature (BFS algorithm, exchange API, background task)
3. Regression Check: Run tests after each implementation

**Order of Execution**: Tasks 1-6 (whale tracking) sequential, Tasks 7-12 (historical data) sequential, Task 13 (integration) final
