# 06 - ARMORY UI: WIREFRAMES & COMPONENTS

## Overview

This document provides detailed UI specifications for the Armory section, including wireframes, component breakdowns, and interaction patterns.

---

## MAIN ARMORY PAGE LAYOUT

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Dashboard                    ⚔️ THE ARMORY          [Tier Badge] │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  YOUR ARSENAL                                                              │
│  ════════════                                                              │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   📊 ASSETS  │  │  ⏱️ TIME     │  │  📈 INDICATORS│ │  🔮 EXOTIC   │   │
│  │              │  │              │  │              │  │              │   │
│  │   12 / 25    │  │   5 / 8      │  │   8 / 14     │  │   🔒 Tier 5  │   │
│  │   unlocked   │  │   unlocked   │  │   unlocked   │  │   required   │   │
│  │              │  │              │  │              │  │              │   │
│  │  [Select →]  │  │  [Select →]  │  │  [Select →]  │  │  [Preview]   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                            │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                                                            │
│  HISTORICAL DEPTH                                                          │
│  ────────────────                                                          │
│  ○ 7 days    ○ 30 days    ● 90 days (current max)    ○ 1 year 🔒          │
│                                                                            │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      YOUR LOADOUT                                   │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │                                                                     │  │
│  │  Assets:      BTC, ETH, SOL, AVAX                     [Edit]       │  │
│  │  Timeframe:   15-minute candles                       [Edit]       │  │
│  │  Duration:    90 days                                 [Edit]       │  │
│  │  Indicators:  RSI, MACD, EMA(20,50,200)              [Edit]       │  │
│  │                                                                     │  │
│  │  ─────────────────────────────────────────────────────────────     │  │
│  │                                                                     │  │
│  │  📊 Estimated Data Points: 34,560                                  │  │
│  │  ⏱️  Processing Time: ~12 seconds                                   │  │
│  │  💾 Storage: ~2.3 MB                                               │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│            [ Cancel ]              [ ⚔️ ACQUIRE DATA & PROCEED ]          │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  NEXT UNLOCK: Beat HODL by 15% for Tier 4                                 │
│  ████████████████░░░░░░░░  67% complete                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ASSET SELECTION MODAL

When user clicks "Select" on Assets:

```
┌────────────────────────────────────────────────────────────────┐
│  SELECT YOUR ASSETS                                    [X]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Quick Select:  [Top 10]  [Your Favorites]  [Clear All]       │
│                                                                │
│  Search: [________________________] 🔍                         │
│                                                                │
│  AVAILABLE (12 unlocked)                                       │
│  ───────────────────────                                       │
│                                                                │
│  [✓] BTC    [✓] ETH    [✓] SOL    [ ] BNB    [ ] XRP         │
│  [ ] ADA    [ ] DOGE   [✓] AVAX   [ ] DOT    [ ] LINK        │
│  [ ] MATIC  [ ] SHIB                                          │
│                                                                │
│  LOCKED (13 remaining)                                         │
│  ─────────────────────                                         │
│                                                                │
│  [🔒] ATOM   [🔒] UNI    [🔒] NEAR   [🔒] APT    [🔒] ARB    │
│  [🔒] OP     [🔒] INJ    [🔒] SEI    [🔒] TIA    [🔒] SUI    │
│  [🔒] FET    [🔒] RNDR   [🔒] WLD                              │
│                                                                │
│  🔒 Unlock more at Tier 4 (13 additional assets)              │
│                                                                │
│  ─────────────────────────────────────────────────────────    │
│  Selected: 4 assets                                           │
│                                                                │
│            [ Cancel ]                    [ Confirm Selection ] │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## TIMEFRAME SELECTION

```
┌────────────────────────────────────────────────────────────────┐
│  SELECT TIMEFRAME                                      [X]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Choose your candle interval:                                  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  [ ] 1 minute   🔒 Tier 4 required                     │  │
│  │      ⚠️ High noise, advanced users only                 │  │
│  │                                                         │  │
│  │  [ ] 5 minutes  ✓ Available                            │  │
│  │      Good for short-term scalping strategies            │  │
│  │                                                         │  │
│  │  [●] 15 minutes ✓ Available  ⭐ RECOMMENDED            │  │
│  │      Balanced signal-to-noise ratio                     │  │
│  │                                                         │  │
│  │  [ ] 1 hour     ✓ Available                            │  │
│  │      Classic swing trading timeframe                    │  │
│  │                                                         │  │
│  │  [ ] 4 hours    ✓ Available                            │  │
│  │      Strong trends, less noise                          │  │
│  │                                                         │  │
│  │  [ ] 1 day      ✓ Available                            │  │
│  │      Position trading, macro trends                     │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  💡 Tip: Start with 15m or 1h. Faster timeframes have more   │
│     noise and require more sophisticated strategies.          │
│                                                                │
│            [ Cancel ]                    [ Confirm Selection ] │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## INDICATOR SELECTION

```
┌────────────────────────────────────────────────────────────────┐
│  SELECT INDICATORS                                     [X]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  TREND INDICATORS                                              │
│  ─────────────────                                             │
│  [✓] SMA (Simple Moving Average)           ✓ Available        │
│  [✓] EMA (Exponential Moving Average)      ✓ Available        │
│  [ ] Ichimoku Cloud                        🔒 Tier 3          │
│                                                                │
│  MOMENTUM INDICATORS                                           │
│  ────────────────────                                          │
│  [✓] RSI (Relative Strength Index)         ✓ Available        │
│  [✓] MACD                                  ✓ Available        │
│  [ ] Stochastic                            🔒 Tier 3          │
│                                                                │
│  VOLATILITY INDICATORS                                         │
│  ──────────────────────                                        │
│  [ ] Bollinger Bands                       ✓ Available        │
│  [ ] ATR (Average True Range)              🔒 Tier 3          │
│                                                                │
│  VOLUME INDICATORS                                             │
│  ──────────────────                                            │
│  [✓] Volume                                ✓ Available        │
│  [ ] OBV (On-Balance Volume)               🔒 Tier 3          │
│  [ ] Volume Profile                        🔒 Tier 4          │
│                                                                │
│  ─────────────────────────────────────────────────────────    │
│  Selected: 5 indicators                                       │
│  ⚠️ More indicators = more data = longer processing           │
│                                                                │
│            [ Cancel ]                    [ Confirm Selection ] │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## INDICATOR CONFIGURATION (When Selected)

For indicators with parameters:

```
┌────────────────────────────────────────────────────────────────┐
│  CONFIGURE: EMA (Exponential Moving Average)           [X]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Period(s) to calculate:                                       │
│                                                                │
│  [ 20 ]  [ 50 ]  [ 200 ]  [+ Add Period]                      │
│                                                                │
│  Quick Presets:                                                │
│  [Classic (20/50/200)]  [Short (9/21)]  [Ribbon (8 EMAs)]     │
│                                                                │
│  Preview:                                                      │
│  ┌──────────────────────────────────────────────────────┐     │
│  │                                                      │     │
│  │   (Small chart showing EMAs on price)               │     │
│  │                                                      │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  💡 Common uses:                                              │
│  • 20 EMA: Short-term trend                                   │
│  • 50 EMA: Medium-term trend                                  │
│  • 200 EMA: Long-term trend / major support-resistance        │
│                                                                │
│            [ Cancel ]                    [ Apply Settings ]    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## LOCK OVERLAY COMPONENT

When hovering/clicking a locked item:

```
┌───────────────────────────────────┐
│                                   │
│           🔒                      │
│                                   │
│     ICHIMOKU CLOUD                │
│                                   │
│  ─────────────────────────────   │
│                                   │
│  Unlock Requirements:             │
│                                   │
│  ○ Reach Tier 3                   │
│    (Currently Tier 2)             │
│                                   │
│  ○ Complete Ichimoku tutorial     │
│                                   │
│  ─────────────────────────────   │
│                                   │
│  [View Tutorial]  [Check Progress]│
│                                   │
└───────────────────────────────────┘
```

---

## LOADOUT SUMMARY COMPONENT

```typescript
interface LoadoutSummary {
  assets: Asset[]
  timeframe: string
  durationDays: number
  indicators: Indicator[]
  
  // Calculated
  estimatedDataPoints: number
  estimatedProcessingTime: string
  estimatedStorage: string
}
```

Visual:
```
┌─────────────────────────────────────────────────────────────┐
│  📦 YOUR LOADOUT                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ASSETS                                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                          │
│  │ BTC │ │ ETH │ │ SOL │ │ AVAX│           [Edit]         │
│  └─────┘ └─────┘ └─────┘ └─────┘                          │
│                                                             │
│  TIMEFRAME           DURATION                               │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │  15 minute  │    │   90 days   │        [Edit]         │
│  └─────────────┘    └─────────────┘                        │
│                                                             │
│  INDICATORS                                                 │
│  ┌─────┐ ┌──────┐ ┌──────────────────┐                    │
│  │ RSI │ │ MACD │ │ EMA (20,50,200) │     [Edit]         │
│  └─────┘ └──────┘ └──────────────────┘                    │
│                                                             │
│  ═════════════════════════════════════════════════════════ │
│                                                             │
│  📊 Data Points:     34,560 candles                        │
│  ⏱️  Processing:      ~12 seconds                           │
│  💾 Storage:         ~2.3 MB                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ACQUIRE DATA FLOW

### Step 1: Click "Acquire Data"

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ⚔️ PREPARING YOUR ARSENAL                                  │
│                                                             │
│  ████████████████░░░░░░░░░░░░░░░░  45%                     │
│                                                             │
│  Fetching BTC data...                                       │
│                                                             │
│  ✓ ETH complete                                            │
│  ✓ SOL complete                                            │
│  → BTC in progress                                         │
│  ○ AVAX pending                                            │
│                                                             │
│  [Cancel]                                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Complete

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│               ✓ ARSENAL READY                              │
│                                                             │
│  Your data has been acquired and processed.                 │
│                                                             │
│  📊 34,560 data points loaded                              │
│  ⏱️  Completed in 11.3 seconds                              │
│                                                             │
│  ─────────────────────────────────────────────────────     │
│                                                             │
│  Where would you like to go?                                │
│                                                             │
│  [ 🧪 Run Backtest ]     [ 📊 Paper Trading ]              │
│                                                             │
│  [ 📈 View Charts ]      [ ← Back to Armory ]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## COMPONENT HIERARCHY

```
ArmoryPage
├── ArmoryHeader
│   ├── BackButton
│   └── TierBadge
├── ArsenalOverview
│   ├── CategoryCard (Assets)
│   ├── CategoryCard (Timeframes)
│   ├── CategoryCard (Indicators)
│   └── CategoryCard (Exotic)
├── HistoricalDepthSelector
├── LoadoutSummary
│   ├── AssetPills
│   ├── TimeframeBadge
│   ├── IndicatorPills
│   └── DataEstimates
├── ActionButtons
│   ├── CancelButton
│   └── AcquireButton
├── ProgressFooter
│   └── NextUnlockProgress
└── Modals
    ├── AssetSelectionModal
    ├── TimeframeSelectionModal
    ├── IndicatorSelectionModal
    ├── IndicatorConfigModal
    ├── LockOverlayModal
    └── AcquisitionProgressModal
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE ARMORY UI COMPONENTS

Context:
- The Armory is the data acquisition section
- Users select assets, timeframes, indicators, and duration
- Some items are locked based on tier/gates
- Final selection is a "loadout" for backtesting

Requirements:
1. Create main ArmoryPage layout
2. Build CategoryCard component for each data pillar
3. Implement modal dialogs for each selection type
4. Create LoadoutSummary component with live calculations
5. Build LockOverlay component for locked items
6. Implement data acquisition progress UI
7. Add proper animations and transitions
8. Make everything responsive

Key interactions:
- Click category → open selection modal
- Select items → update loadout summary
- Click locked item → show requirements
- Click "Acquire" → show progress, then redirect

State management:
- Current loadout (local state)
- User unlocks (from API/context)
- Data acquisition status (async)

Deliverables:
- All components listed in hierarchy
- Responsive styling
- Animation definitions
- Integration with gate system

Reference:
- See 03-armory-overview.md for concepts
- See 05-armory-gates.md for lock logic
- See 12-api-endpoints.md for data fetching
```

---

## ACCEPTANCE CRITERIA

- [ ] Main Armory page displays all 5 data categories
- [ ] Each category shows unlocked/total count
- [ ] Selection modals work for each category
- [ ] Locked items display with clear requirements
- [ ] Loadout summary updates in real-time
- [ ] Data point estimates are calculated correctly
- [ ] "Acquire Data" initiates fetch process
- [ ] Progress modal shows during acquisition
- [ ] Completion modal offers navigation options
- [ ] All components are responsive
- [ ] Animations enhance user experience

---

*Related Documents:*
- `03-armory-overview.md` - Armory concepts
- `04-armory-tiers.md` - What's unlocked at each tier
- `05-armory-gates.md` - Lock conditions
- `12-api-endpoints.md` - API specifications
