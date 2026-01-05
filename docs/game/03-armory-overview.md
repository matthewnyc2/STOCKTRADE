# 03 - THE ARMORY: OVERVIEW

## Overview

The Armory is where users **acquire data** for their trading experiments. But it's not a boring data download page - it's a **video game equipment shop** where you prepare for battle against the market.

---

## THE CORE METAPHOR

### You Are a Warrior

In RPGs, before you fight the dragon, you go to the shop:
- Buy a sword (your strategy)
- Get armor (risk management)
- Stock up on potions (historical data)
- Learn spells (indicators)

In STOCKTRADE, before you backtest or paper trade:
- Choose your assets (your battlefield)
- Select your timeframe (your weapon type)
- Set your historical depth (your ammunition)
- Pick your indicators (your skills)

### The Armory Is:
- A gatekeeper (you can't access everything immediately)
- A teacher (unlocks require demonstrated knowledge)
- A reward system (progress feels meaningful)
- A preview (see what you're working toward)

---

## THE FIVE PILLARS OF DATA

Every data acquisition has five dimensions:

### 1. ASSETS (The Roster)
*"Which coins do you want to trade?"*

- Starts with just BTC, ETH, and one choice
- Unlocks more as you progress
- Eventually: 50+ coins, custom additions
- Game feel: "Unlocking new characters"

### 2. TIMEFRAMES (The Weapons)
*"What candle intervals?"*

- 1-minute (sniper rifle - precision, danger)
- 15-minute (assault rifle - balanced)
- 1-hour (shotgun - reliable, forgiving)
- 4-hour (sword - classic)
- 1-day (battle axe - slow but powerful)

Not all timeframes available immediately. 1-minute is dangerous for beginners.

### 3. DURATION (The Map Size)
*"How far back in history?"*

- 7 days: Tutorial area
- 30 days: First real zone
- 90 days: Mid-game content
- 1 year: Late game
- 3+ years: Endgame content

More history = more data = better backtests = harder to unlock.

### 4. INDICATORS (The Skills)
*"What technical analysis tools?"*

Basic (Tier 1):
- SMA, EMA
- Volume
- Basic price action

Intermediate (Tier 2-3):
- RSI, MACD
- Bollinger Bands
- ATR, OBV

Advanced (Tier 4-5):
- Ichimoku Cloud
- Fibonacci levels
- VWAP, Order Flow
- Custom indicator builder

### 5. EXOTIC DATA (Legendary Gear)
*"The powerful stuff"*

Only for advanced users:
- Order book snapshots
- Funding rates
- On-chain metrics
- Sentiment data
- Whale alerts
- Cross-exchange data

---

## THE ACQUISITION FLOW

When a user wants data for a backtest or analysis:

```
Step 1: Enter the Armory
        │
        ▼
Step 2: See your available equipment (based on tier)
        │
        ▼
Step 3: Build your "Loadout"
        - Select assets
        - Choose timeframe
        - Set duration
        - Add indicators
        │
        ▼
Step 4: Review loadout summary
        - Estimated data points
        - Processing time
        - Any locked items highlighted
        │
        ▼
Step 5: "Acquire Data" button
        │
        ▼
Step 6: Data fetched/processed
        │
        ▼
Step 7: Proceed to Backtest/Analysis with this loadout
```

---

## THE GATING PHILOSOPHY

### Why Gate Data?

1. **Prevent overwhelm**: Beginners don't need 3 years of 1-minute candles
2. **Teach incrementally**: Force users to learn before accessing complex data
3. **Create goals**: "I want to unlock order book data" is motivating
4. **Ensure competence**: Users who unlock advanced data have proven they can handle it

### The Golden Rule
> Every gate should make the user say "That taught me something" not "That was annoying."

### Types of Gates

| Gate Type | What It Tests | Example |
|-----------|---------------|---------|
| **Knowledge** | Understanding | "Pass quiz on RSI before unlocking RSI data" |
| **Volume** | Engagement | "Run 10 backtests to unlock Tier 2" |
| **Skill** | Ability | "Beat benchmark by 15%" |
| **Consistency** | Discipline | "5 profitable paper trades in a row" |
| **Risk** | Caution | "Max drawdown under 15% across 20 trades" |

See `05-armory-gates.md` for complete gate specifications.

---

## STATE MANAGEMENT

The Armory needs to track:

```typescript
interface ArmoryState {
  // What user has unlocked
  unlockedAssets: string[]           // ["BTC", "ETH", "SOL", ...]
  unlockedTimeframes: string[]       // ["1h", "4h", "1d", ...]
  maxHistoricalDays: number          // 7, 30, 90, 365, etc.
  unlockedIndicators: string[]       // ["SMA", "EMA", "RSI", ...]
  hasExoticAccess: boolean           // Tier 5 only
  
  // Current loadout being built
  currentLoadout: {
    assets: string[]
    timeframe: string
    durationDays: number
    indicators: string[]
    exoticData?: string[]
  }
  
  // Progress tracking
  currentTier: 1 | 2 | 3 | 4 | 5
  xpEarned: number
  xpToNextTier: number
  gatesCompleted: string[]           // IDs of completed gates
  gatesInProgress: {                 // Partial progress
    [gateId: string]: {
      current: number
      required: number
    }
  }
}
```

---

## RELATIONSHIP TO OTHER MODULES

### Armory → Backtest
- User builds loadout in Armory
- Clicks "Acquire Data"
- Data is fetched and processed
- User is redirected to Backtest with data ready

### Armory → Paper Trading
- User selects assets for paper trading
- Armory validates they have access
- Paper trading uses only unlocked assets

### Backtest/Paper Trading → Armory (Feedback Loop)
- Results from backtests update gate progress
- Paper trading P&L feeds into tier advancement
- Achievements earned unlock new Armory content

### Tutorial → Armory
- Completing tutorial modules unlocks Armory content
- "Finish RSI tutorial" unlocks RSI indicator

---

## VISUAL DESIGN PRINCIPLES

### The Shop Feel
- Items on shelves (cards in a grid)
- Locked items have padlock overlay
- Unlocked items glow/shine
- Equipped items (current loadout) are highlighted

### Progress is Visible
- Clear indication of current tier
- Progress bar to next tier always visible
- Locked items show what's needed to unlock
- "Coming soon" for items not yet in system

### Satisfying Interactions
- Unlock animation (chest opening, item revealing)
- Sound effect when item unlocked
- Confetti for tier advancement
- Items "slot into" loadout visually

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE ARMORY OVERVIEW PAGE

Context:
- The Armory is where users acquire data for backtesting
- It's gamified like an RPG equipment shop
- Users can only access what they've unlocked
- Unlocks come from completing challenges/tutorials

Requirements:
1. Create Armory page at /app/armory
2. Display user's current tier and progress
3. Show 5 categories: Assets, Timeframes, Duration, Indicators, Exotic
4. Each category shows: available items, locked items, unlock requirements
5. Allow user to build a "loadout" by selecting from available items
6. Show loadout summary with data point estimates
7. "Acquire Data" button that fetches/processes data
8. Locked items have clear visual treatment
9. Progress toward next unlock is visible
10. Smooth animations for unlock events

State management:
- Fetch user's ArmoryState from API
- Update local state as user builds loadout
- Validate selections against unlocks
- Submit loadout to data acquisition service

Deliverables:
- ArmoryPage component
- CategoryCard component (for each of 5 pillars)
- ItemSelector component (for picking assets, indicators, etc.)
- LoadoutSummary component
- LockOverlay component
- UnlockAnimation component
- useArmoryState hook

Reference:
- See 04-armory-tiers.md for tier requirements
- See 05-armory-gates.md for unlock conditions
- See 06-armory-ui.md for detailed wireframes
- See 12-api-endpoints.md for API specs
```

---

## ACCEPTANCE CRITERIA

- [ ] User can see their current tier and progress
- [ ] All 5 data pillars are displayed as categories
- [ ] Available items can be selected for loadout
- [ ] Locked items show clear lock state and unlock requirement
- [ ] User can build a complete loadout
- [ ] Data point estimate is calculated and shown
- [ ] "Acquire Data" initiates data fetch process
- [ ] Attempting to select locked items shows helpful message
- [ ] Unlock animations play when gates are completed
- [ ] State persists across sessions

---

*Related Documents:*
- `00-overview.md` - System context
- `02-hero-dashboard.md` - Navigation from dashboard
- `04-armory-tiers.md` - Detailed tier progression
- `05-armory-gates.md` - Gate mechanics
- `06-armory-ui.md` - UI wireframes
