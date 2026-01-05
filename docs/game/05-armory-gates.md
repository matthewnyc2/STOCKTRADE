# 05 - ARMORY GATES: UNLOCK CONDITIONS

## Overview

Gates are challenges that must be completed to unlock features or advance tiers. This document specifies every gate in the system, its conditions, and how to evaluate completion.

---

## GATE DESIGN PHILOSOPHY

### The Golden Rule
> Every gate should teach something valuable, not just block progress.

### Gate Types

1. **Knowledge Gates**: Prove you understand a concept
2. **Volume Gates**: Prove you're engaged (do X things)
3. **Skill Gates**: Prove you can perform (achieve Y result)
4. **Consistency Gates**: Prove you're not lucky (do Z repeatedly)
5. **Risk Gates**: Prove you're disciplined (stay within limits)

---

## TIER ADVANCEMENT GATES

### GATE: Tier 1 → Tier 2

**ID**: `gate_tier_1_to_2`

**Requirements**:
```yaml
all_of:
  - type: tutorial_complete
    module: "introduction"
  - type: count
    action: "backtest_run"
    minimum: 3
  - type: quiz_pass
    quiz: "candle_basics"
    minimum_score: 70
```

**Evaluation Logic**:
```python
def check_tier_1_to_2(user):
    return (
        user.tutorials_completed.includes("introduction") and
        user.backtest_count >= 3 and
        user.quiz_scores.get("candle_basics", 0) >= 70
    )
```

**Teaching Purpose**: 
- Introduction ensures they know the app
- 3 backtests ensures they've tried the core feature
- Quiz ensures they understand candles

---

### GATE: Tier 2 → Tier 3

**ID**: `gate_tier_2_to_3`

**Requirements**:
```yaml
all_of:
  - type: count
    action: "backtest_run"
    minimum: 10
  - type: count_with_condition
    action: "backtest_run"
    condition: "profit > 0"
    minimum: 3
  - type: tutorial_complete
    module: "candles_101"
  - type: quiz_pass
    quiz: "candlestick_patterns"
    minimum_score: 70
```

**Evaluation Logic**:
```python
def check_tier_2_to_3(user):
    profitable_backtests = [b for b in user.backtests if b.profit > 0]
    return (
        len(user.backtests) >= 10 and
        len(profitable_backtests) >= 3 and
        user.tutorials_completed.includes("candles_101") and
        user.quiz_scores.get("candlestick_patterns", 0) >= 70
    )
```

**Teaching Purpose**:
- 10 backtests = muscle memory with the tool
- 3 profitable = understanding that random doesn't work
- Tutorial + quiz = foundational candle knowledge

---

### GATE: Tier 3 → Tier 4

**ID**: `gate_tier_3_to_4`

**Requirements**:
```yaml
all_of:
  - type: performance
    metric: "best_backtest_vs_hodl"
    condition: ">= 15"  # Must beat HODL by 15%
    duration_days: 30
  - type: count
    action: "backtest_run"
    minimum: 25
  - type: tutorial_complete
    module: "all_basic_modules"
  - type: rolling_metric
    metric: "win_rate"
    window: 10  # Last 10 backtests
    condition: ">= 50"
```

**Evaluation Logic**:
```python
def check_tier_3_to_4(user):
    # Check if any backtest beats HODL by 15%
    best_vs_hodl = max([b.return_pct - b.hodl_return_pct for b in user.backtests])
    
    # Check win rate of last 10
    last_10 = user.backtests[-10:]
    win_rate = len([b for b in last_10 if b.profit > 0]) / 10 * 100
    
    return (
        best_vs_hodl >= 15 and
        len(user.backtests) >= 25 and
        user.all_basic_tutorials_complete() and
        win_rate >= 50
    )
```

**Teaching Purpose**:
- Beating HODL = you can add value over passive
- 50% win rate = consistency matters
- All tutorials = comprehensive knowledge

---

### GATE: Tier 4 → Tier 5

**ID**: `gate_tier_4_to_5`

**Requirements**:
```yaml
any_of:  # Can do EITHER path
  - path: "performance"
    all_of:
      - type: performance
        metric: "sharpe_ratio"
        condition: ">= 2.0"
        duration_days: 180
  - path: "gauntlet"
    all_of:
      - type: gauntlet_complete
        challenges: "all_7"
```

**Evaluation Logic**:
```python
def check_tier_4_to_5(user):
    # Path 1: Performance-based
    six_month_backtests = [b for b in user.backtests if b.duration_days >= 180]
    best_sharpe = max([b.sharpe_ratio for b in six_month_backtests], default=0)
    
    # Path 2: Gauntlet
    gauntlet_complete = len(user.gauntlet_completed) == 7
    
    return best_sharpe >= 2.0 or gauntlet_complete
```

**Teaching Purpose**:
- Sharpe > 2.0 = truly skilled at risk-adjusted returns
- Gauntlet = alternative path for those who learn differently

---

## INDIVIDUAL ITEM GATES

### RSI Indicator Unlock

**ID**: `gate_unlock_rsi`

**Requirements**:
```yaml
any_of:
  - type: tutorial_complete
    module: "rsi_tutorial"
  - type: quiz_pass
    quiz: "rsi_understanding"
    minimum_score: 80
```

---

### 1-Minute Timeframe Unlock

**ID**: `gate_unlock_1m`

**Requirements**:
```yaml
all_of:
  - type: tier_minimum
    tier: 4
  - type: acknowledgment
    message: "1m data is noisy and dangerous for beginners"
  - type: count
    action: "backtest_with_15m_or_longer"
    minimum: 20
```

**Rationale**: 1-minute data is often harmful for new traders (noise, overtrading). Gate ensures they've practiced with larger timeframes first.

---

### Order Book Data Unlock

**ID**: `gate_unlock_orderbook`

**Requirements**:
```yaml
all_of:
  - type: tier_minimum
    tier: 5
  - type: tutorial_complete
    module: "order_flow_basics"
  - type: quiz_pass
    quiz: "order_book_reading"
    minimum_score: 75
```

---

## PAPER TRADING GATES

### Paper Trading: Intermediate Assets

**ID**: `gate_paper_intermediate_assets`

**Requirements**:
```yaml
all_of:
  - type: paper_trade_count
    minimum: 10
  - type: paper_pnl
    condition: "> 0"  # Net positive
```

---

### Paper Trading: Leverage Feature

**ID**: `gate_paper_leverage`

**Requirements**:
```yaml
all_of:
  - type: tier_minimum
    tier: 4
  - type: paper_trade_count
    minimum: 50
  - type: paper_max_drawdown
    condition: "< 20%"
    window: "last_20_trades"
  - type: acknowledgment
    message: "Leverage amplifies losses. You can lose more than your position."
```

---

## GATE EVALUATION ENGINE

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GATE EVALUATION ENGINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   Gate      │     │   User       │     │  Result     │  │
│  │   Config    │ ──▶ │   State      │ ──▶ │  Evaluator  │  │
│  │   (YAML)    │     │   (DB)       │     │             │  │
│  └─────────────┘     └──────────────┘     └─────────────┘  │
│                                                  │          │
│                                                  ▼          │
│                                          ┌─────────────┐   │
│                                          │   Gate      │   │
│                                          │   Result    │   │
│                                          │             │   │
│                                          │ - passed    │   │
│                                          │ - progress  │   │
│                                          │ - blocking  │   │
│                                          └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Gate Result Schema

```typescript
interface GateResult {
  gateId: string
  passed: boolean
  progress: {
    current: number
    required: number
    percentage: number
  }
  blockingRequirements: string[]  // Human-readable list of what's missing
  estimatedTimeToComplete?: string  // "~3 more backtests"
}
```

### Example Evaluation

```typescript
// User tries to access RSI indicator
const result = evaluateGate("gate_unlock_rsi", user)

// Result:
{
  gateId: "gate_unlock_rsi",
  passed: false,
  progress: {
    current: 0,
    required: 1,
    percentage: 0
  },
  blockingRequirements: [
    "Complete the RSI tutorial module",
    "OR pass the RSI understanding quiz with 80%+"
  ],
  estimatedTimeToComplete: "~10 minutes"
}
```

---

## GATE PROGRESS TRACKING

For gates with counts or rolling metrics, track partial progress:

```typescript
interface GateProgress {
  gateId: string
  userId: string
  
  // For count-based gates
  currentCount?: number
  requiredCount?: number
  
  // For performance gates
  currentMetric?: number
  requiredMetric?: number
  
  // For rolling/window gates
  recentValues?: number[]  // Last N values
  
  // Meta
  lastUpdated: Date
  firstActivity: Date
}
```

---

## UI DISPLAY OF GATES

### Locked Item Overlay
```
┌─────────────────────────────────┐
│  🔒 RSI Indicator               │
│                                 │
│  Requirements:                  │
│  ○ Complete RSI tutorial        │
│    OR                           │
│  ○ Pass RSI quiz (80%+)         │
│                                 │
│  [Start Tutorial]               │
└─────────────────────────────────┘
```

### Partial Progress
```
┌─────────────────────────────────┐
│  ⏳ Tier 3 Progress             │
│                                 │
│  ✓ Run 10 backtests (12/10)    │
│  ✓ 3 profitable (5/3)          │
│  ○ Complete Candles 101         │
│  ○ Pass patterns quiz (70%+)    │
│                                 │
│  ████████░░░░░░░░ 50% complete  │
└─────────────────────────────────┘
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE GATE EVALUATION ENGINE

Context:
- Gates are challenges that unlock features
- Each gate has conditions that must be met
- Progress should be tracked and displayed
- Multiple gate types: count, performance, tutorial, quiz, etc.

Requirements:
1. Create gate configuration schema (YAML or JSON)
2. Build gate evaluator that checks conditions against user state
3. Implement progress tracking for partial completion
4. Create API endpoints for gate status checks
5. Build UI components for displaying gate requirements
6. Handle "any_of" and "all_of" logic combinations
7. Support acknowledgment gates (user must accept warning)

Core functions needed:
- evaluateGate(gateId, userId) → GateResult
- getGateProgress(gateId, userId) → GateProgress
- updateGateProgress(gateId, userId, action) → void
- getAllGatesForUser(userId) → GateResult[]

Event handlers:
- onBacktestComplete → update relevant gates
- onPaperTradeComplete → update relevant gates
- onTutorialComplete → update relevant gates
- onQuizPass → update relevant gates

Deliverables:
- GateConfig data structure
- GateEvaluator service
- GateProgress model
- Gate-related API endpoints
- LockOverlay component
- GateProgressCard component

Reference:
- See 04-armory-tiers.md for tier gates
- See 11-progression-database.md for database schema
- See 12-api-endpoints.md for API specs
```

---

## ACCEPTANCE CRITERIA

- [ ] All gates are defined in configuration
- [ ] Gate evaluator correctly processes all gate types
- [ ] Progress is tracked and persisted
- [ ] UI shows clear requirements for locked items
- [ ] Partial progress is visible where applicable
- [ ] Gate completion triggers appropriate unlocks
- [ ] "Any of" and "All of" logic works correctly
- [ ] Acknowledgment gates require user confirmation
- [ ] Gate status is cached and updated efficiently

---

*Related Documents:*
- `03-armory-overview.md` - Armory context
- `04-armory-tiers.md` - Tier-specific gates
- `11-progression-database.md` - Data storage
- `13-special-mechanics.md` - Gauntlet challenges
