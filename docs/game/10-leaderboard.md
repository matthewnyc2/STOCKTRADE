# 10 - LEADERBOARD SYSTEM

## Overview

The Leaderboard is where strategies compete. Your strategies are ranked against the community, creating motivation to improve and iterate. The leaderboard makes the abstract (backtesting) feel competitive and real.

---

## THE CORE CONCEPT

### Not People vs People - Strategies vs Strategies

The leaderboard doesn't rank users directly. It ranks **strategies**. A single user might have multiple strategies on the board:

```
STRATEGY LEADERBOARD

1. AlphaHunter_v3      +342.5%    (by @traderpro)
2. MomentumKing        +287.2%    (by @quantwiz)
3. MY_RSI_STRATEGY     +156.8%    ← YOUR STRATEGY
4. AlphaHunter_v2      +143.1%    (by @traderpro)  ← same user
5. TrendRider          +98.4%     (by @chartmaster)
```

This rewards **good strategy design** not just participation.

---

## LEADERBOARD CATEGORIES

### By Performance Metric

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   LEADERBOARD CATEGORIES                                               │
│                                                                         │
│   [Total Return]  [Sharpe Ratio]  [Win Rate]  [Max Drawdown]           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

| Category | What It Measures | Best For |
|----------|------------------|----------|
| **Total Return** | Raw percentage gain | Aggressive traders |
| **Sharpe Ratio** | Risk-adjusted return | Smart traders |
| **Win Rate** | % of profitable trades | Consistent traders |
| **Max Drawdown** | Smallest peak-to-trough | Conservative traders |

### By Timeframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   TIME PERIODS                                                          │
│                                                                         │
│   [30 Days]  [90 Days]  [1 Year]  [All Time]                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### By Asset Class

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   ASSET FILTER                                                          │
│                                                                         │
│   [All Assets]  [BTC Only]  [ETH Only]  [Altcoins]  [Custom...]       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## MAIN LEADERBOARD UI

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Back                         🏆 LEADERBOARD                [Your Rank] │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  FILTERS:                                                                  │
│  Metric: [Total Return ▼]  Period: [90 Days ▼]  Asset: [All ▼]           │
│                                                                            │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                                                            │
│  YOUR BEST: #42 overall    Strategy: "RSI_Bounce_v2"    Return: +67.3%   │
│                                                                            │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                                                            │
│  TOP STRATEGIES                                                            │
│                                                                            │
│  ┌────┬────────────────────────┬───────────┬────────────┬──────────────┐  │
│  │RANK│ STRATEGY               │  RETURN   │ SHARPE    │ CREATOR      │  │
│  ├────┼────────────────────────┼───────────┼────────────┼──────────────┤  │
│  │ 🥇 │ MomentumAlpha          │  +342.5%  │   2.84    │ @traderpro   │  │
│  │ 🥈 │ TrendSurfer_Pro        │  +287.2%  │   2.21    │ @quantwiz    │  │
│  │ 🥉 │ VolatilityBreaker      │  +234.8%  │   1.98    │ @chartking   │  │
│  │ 4  │ SmartMoney_v4          │  +198.3%  │   2.45    │ @alphatrader │  │
│  │ 5  │ DipBuyer               │  +176.9%  │   1.56    │ @hodlmaster  │  │
│  │ 6  │ CrossoverKing          │  +165.2%  │   1.89    │ @signalseeker│  │
│  │ 7  │ RSI_Divergence         │  +154.7%  │   2.12    │ @techtrader  │  │
│  │ 8  │ BreakoutHunter         │  +142.1%  │   1.67    │ @breakoutbob │  │
│  │ 9  │ PatternMaster          │  +138.6%  │   1.95    │ @candle_pro  │  │
│  │ 10 │ Scalper_Elite          │  +127.4%  │   1.78    │ @quicktrade  │  │
│  └────┴────────────────────────┴───────────┴────────────┴──────────────┘  │
│                                                                            │
│  [← Previous]     Page 1 of 24     [Next →]                              │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│  💡 Your strategy "RSI_Bounce_v2" is #42. You need +12.3% more to reach  │
│     #40 (held by "MeanRevert_Basic" at +79.6%)                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## STRATEGY DETAIL VIEW

When clicking on a strategy:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   MomentumAlpha                                         🥇 RANK #1        │
│   by @traderpro                                                            │
│                                                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│                                                                            │
│   PERFORMANCE SUMMARY                                                      │
│                                                                            │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │ TOTAL RETURN │  │ SHARPE RATIO │  │   WIN RATE   │  │ MAX DRAWDOWN │  │
│   │              │  │              │  │              │  │              │  │
│   │   +342.5%    │  │    2.84      │  │    68.4%     │  │   -12.3%     │  │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                            │
│   EQUITY CURVE                                                             │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                          ╱         │  │
│   │                                                    ╱────╱          │  │
│   │                                              ╱────╱                │  │
│   │                                    ╱────────╱                      │  │
│   │                          ╱────────╱                                │  │
│   │                ╱────────╱                                          │  │
│   │      ╱────────╱                                                    │  │
│   │ ────╱                                                              │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   STRATEGY DETAILS                                                         │
│   ─────────────────                                                        │
│   Assets: BTC, ETH, SOL                                                    │
│   Timeframe: 1 hour                                                        │
│   Backtest Period: 90 days                                                 │
│   Total Trades: 47                                                         │
│   Avg Trade Duration: 6.2 hours                                            │
│                                                                            │
│   ⚠️ Strategy logic is private (creator has not shared)                   │
│                                                                            │
│   ────────────────────────────────────────────────────────────────────    │
│                                                                            │
│   [ 👀 View Similar ]  [ ⭐ Save to Watchlist ]  [ 📊 Compare to Yours ]  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## YOUR STRATEGIES SECTION

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   📊 YOUR STRATEGIES                                                       │
│                                                                            │
│   ┌──────────────────────┬───────────┬──────────┬───────────┬──────────┐  │
│   │ STRATEGY             │  RETURN   │   RANK   │  CHANGE   │  STATUS  │  │
│   ├──────────────────────┼───────────┼──────────┼───────────┼──────────┤  │
│   │ RSI_Bounce_v2        │  +67.3%   │   #42    │   ↑3      │ Active   │  │
│   │ EMA_Cross_Basic      │  +34.2%   │   #156   │   ↓12     │ Active   │  │
│   │ Volume_Spike_v1      │  +12.1%   │   #423   │   ─       │ Inactive │  │
│   │ Failed_Experiment    │  -8.4%    │   N/A    │   ─       │ Negative │  │
│   └──────────────────────┴───────────┴──────────┴───────────┴──────────┘  │
│                                                                            │
│   [ + Create New Strategy ]                                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## LEADERBOARD MECHANICS

### How Strategies Get Ranked

1. **Submit for Ranking**: After a backtest, user chooses to "Submit to Leaderboard"
2. **Validation**: System verifies the backtest is valid (no look-ahead, proper data)
3. **Ranking**: Strategy is ranked among all submissions
4. **Updates**: Rankings update periodically (hourly? daily?)

### Ranking Algorithm

```typescript
interface StrategySubmission {
  strategyId: string
  userId: string
  strategyName: string
  
  // Backtest results
  backtestId: string
  assets: string[]
  timeframe: string
  periodDays: number
  
  // Metrics
  totalReturn: number      // Primary ranking metric
  sharpeRatio: number
  winRate: number
  maxDrawdown: number
  totalTrades: number
  
  // Timestamps
  submittedAt: Date
  lastValidatedAt: Date
}

function calculateRank(strategies: StrategySubmission[], metric: string): StrategyRanking[] {
  // Sort by selected metric
  const sorted = strategies.sort((a, b) => {
    if (metric === 'totalReturn') return b.totalReturn - a.totalReturn
    if (metric === 'sharpeRatio') return b.sharpeRatio - a.sharpeRatio
    if (metric === 'winRate') return b.winRate - a.winRate
    if (metric === 'maxDrawdown') return a.maxDrawdown - b.maxDrawdown  // Lower is better
    return 0
  })
  
  return sorted.map((strategy, index) => ({
    ...strategy,
    rank: index + 1
  }))
}
```

### Validation Rules

To prevent gaming:
- Minimum 20 trades required
- Minimum 30-day backtest period
- No duplicate submissions (same strategy, same period)
- Results must be reproducible
- Future: On-chain verification for paper trading

---

## ACHIEVEMENTS & BADGES

### Leaderboard-Related Achievements

| Achievement | Requirement | Badge |
|-------------|-------------|-------|
| First Blood | Get any strategy on the leaderboard | 🎯 |
| Top 100 | Have a strategy in top 100 | 🏅 |
| Top 10 | Have a strategy in top 10 | 🥇 |
| #1 | Hold the #1 spot | 👑 |
| Consistent | Top 100 for 30 consecutive days | 🔥 |
| Multi-Champ | 3 strategies in top 50 simultaneously | 🌟 |
| Sharpe Shooter | Sharpe ratio > 3.0 | 🎯 |
| Win Machine | Win rate > 80% in top 100 | 🤖 |

---

## SOCIAL FEATURES

### Strategy Sharing (Optional)

Users can choose to share strategy logic:

```
SHARING OPTIONS

○ Private - Only I can see the strategy details
● Anonymous - Others can see performance but not my username
○ Public - Full transparency, others can learn from my strategy
○ Paid - Charge X credits for others to view details
```

### Comments & Discussion

```
COMMENTS on MomentumAlpha

@chartmaster: "Impressive Sharpe ratio. How do you handle choppy markets?"

@traderpro (creator): "I add a volatility filter - only trade when ATR > X"

@newbie123: "Is this still working in current market conditions?"
```

---

## LEADERBOARD TYPES

### Global Leaderboard
- All users, all strategies
- The main competition

### Friends Leaderboard
- Only your followed users
- More personal competition

### Tier Leaderboard
- Only users at your tier level
- Fair competition for newer users

### Weekly Challenge Leaderboard
- Specific challenge (e.g., "Best BTC strategy this week")
- Fresh start every week

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE LEADERBOARD SYSTEM

Context:
- Strategies compete on the leaderboard, not users directly
- Multiple ranking metrics (return, sharpe, win rate, drawdown)
- Filter by timeframe and asset class
- Users can have multiple strategies ranked

Requirements:
1. Create leaderboard data model
2. Build ranking algorithm with multiple metrics
3. Implement strategy submission from backtest
4. Create main leaderboard UI with filters
5. Build strategy detail view
6. Show user's own strategies section
7. Implement rank change tracking (↑↓)
8. Add achievements for leaderboard milestones

Data model:
```typescript
interface LeaderboardEntry {
  id: string
  strategyId: string
  userId: string
  strategyName: string
  
  metrics: {
    totalReturn: number
    sharpeRatio: number
    winRate: number
    maxDrawdown: number
  }
  
  rank: {
    byReturn: number
    bySharpe: number
    byWinRate: number
    byDrawdown: number
  }
  
  previousRank: number  // For showing ↑↓
  submittedAt: Date
}
```

Deliverables:
- LeaderboardPage component
- LeaderboardTable component
- StrategyDetail component
- YourStrategies component
- RankBadge component
- StrategySubmission flow
- LeaderboardFilters component
- useLeaderboard hook

API endpoints:
- GET /leaderboard?metric=X&period=Y&asset=Z
- GET /leaderboard/strategy/:id
- POST /leaderboard/submit
- GET /leaderboard/me

Reference:
- See 02-hero-dashboard.md for leaderboard preview
- See 11-progression-database.md for state storage
- See 12-api-endpoints.md for full API specs
```

---

## ACCEPTANCE CRITERIA

- [ ] Leaderboard displays ranked strategies
- [ ] Multiple sort metrics work (return, sharpe, etc.)
- [ ] Filters work (timeframe, asset)
- [ ] Strategy detail view shows full stats
- [ ] User can see their own strategies' ranks
- [ ] Rank changes (↑↓) are shown
- [ ] Strategy submission from backtest works
- [ ] Achievements trigger at milestones
- [ ] Performance is acceptable (pagination for large lists)
- [ ] UI is engaging and competitive feeling

---

*Related Documents:*
- `02-hero-dashboard.md` - Leaderboard preview on dashboard
- `03-armory-overview.md` - Data for backtesting
- `11-progression-database.md` - State storage
- `12-api-endpoints.md` - API specifications
