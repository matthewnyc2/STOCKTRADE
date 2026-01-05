# 02 - HERO DASHBOARD SPECIFICATION

## Overview

The Hero Dashboard is the **command center** of the entire application. After the splash page sets the emotional tone, the dashboard is where users LIVE. It must feel like a video game main menu AND a professional trading terminal had a baby.

---

## THE VISION

### First Impression
When the dashboard loads, the user should feel:
- "I am in control"
- "There's so much I can do here"
- "I want to explore everything"
- "This looks powerful but not overwhelming"

### The Aesthetic
- **Dark theme** (traders prefer dark)
- **Neon accents** (game feel)
- **Live data movement** (the market never sleeps)
- **Big, bold buttons** (clear actions)
- **Metrics everywhere** (data-rich but organized)

---

## LAYOUT STRUCTURE

```
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                     │
│ [M Logo]  STOCKTRADE          [🔔 Alerts] [⚙️ Settings] [👤 Profile/Tier] │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         HERO SECTION                                │  │
│  │                                                                     │  │
│  │   Live ticker tape scrolling across...                             │  │
│  │   ═══════════════════════════════════════════════════════════════  │  │
│  │                                                                     │  │
│  │   YOUR JOURNEY                              MARKET PULSE            │  │
│  │   ┌──────────────────────┐                 ┌──────────────────┐    │  │
│  │   │ TIER 3: JOURNEYMAN   │                 │ ▲ BTC $67,432    │    │  │
│  │   │ ████████░░░░ 67%     │                 │ ▼ ETH $3,421     │    │  │
│  │   │ Next: Beat HODL +15% │                 │ ▲ SOL $142       │    │  │
│  │   └──────────────────────┘                 │ [Live Candle]    │    │  │
│  │                                            └──────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      MAIN ACTION BUTTONS                            │  │
│  │                                                                     │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │   │             │  │             │  │             │  │           │ │  │
│  │   │   ⚔️ THE    │  │  📚 LEARN   │  │  🧪 TEST    │  │  📊 TRADE │ │  │
│  │   │   ARMORY    │  │             │  │             │  │           │ │  │
│  │   │             │  │             │  │             │  │           │ │  │
│  │   │ Acquire     │  │ Master the  │  │ Backtest    │  │  Paper    │ │  │
│  │   │ Your Data   │  │ Fundamentals│  │ Strategies  │  │  Trading  │ │  │
│  │   │             │  │             │  │             │  │           │ │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      METRICS & LEADERBOARD                          │  │
│  │                                                                     │  │
│  │  YOUR STATS                    │  LEADERBOARD PREVIEW               │  │
│  │  ─────────────                 │  ────────────────────              │  │
│  │  Backtests Run: 47             │  1. AlphaHunter    +342%          │  │
│  │  Win Rate: 62%                 │  2. MomentumKing   +287%          │  │
│  │  Best Strategy: +89%           │  3. YOUR STRAT     +156%  ← YOU   │  │
│  │  Paper P&L: +$12,450           │  4. TrendRider     +143%          │  │
│  │                                │  [View Full Leaderboard →]         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ FOOTER: Daily Challenge: "Backtest DOGE on 1h candles" [+500 XP]  [GO →] │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## COMPONENT BREAKDOWN

### 1. HEADER BAR

**Elements:**
- M Logo (links to splash/home)
- App name: "STOCKTRADE"
- Notification bell with count badge
- Settings gear
- User avatar with tier badge overlay

**Behavior:**
- Sticky on scroll
- Logo pulses subtly when new achievement earned
- Bell shows unread count
- Clicking avatar opens profile/progression panel

---

### 2. LIVE TICKER TAPE

**What it shows:**
```
BTC $67,432.10 ▲2.3%  |  ETH $3,421.05 ▼0.8%  |  SOL $142.33 ▲5.1%  |  ...
```

**Behavior:**
- Smooth horizontal scroll (marquee style, but classy)
- Green for up, red for down
- Click any symbol to see quick chart modal
- Shows top 10-20 coins by default
- Can be customized in settings
- Updates every 5-10 seconds (not too frantic)

---

### 3. YOUR JOURNEY CARD

**Elements:**
- Current tier name and icon
- Progress bar to next tier (percentage)
- Text showing next unlock requirement
- Optional: Animated effects when close to unlock

**Example States:**
```
TIER 1: INITIATE
████░░░░░░░░░░░░ 25%
Next: Complete the tutorial

TIER 3: JOURNEYMAN  
████████████░░░░ 78%
Next: Beat HODL by 15% (currently +10.2%)

TIER 5: SHADOW MASTER ✓
████████████████ MAX
All unlocks achieved!
```

---

### 4. MARKET PULSE (MINI CHART)

**What it shows:**
- A small, live candlestick chart
- Default: BTC/USD, 1-hour candles, last 24 hours
- Key metrics: current price, 24h change, volume

**Behavior:**
- Updates in real-time (WebSocket if possible)
- Click to expand to full chart view
- User can change the displayed asset
- Shows last few candles with proper coloring

**Visual Style:**
- Dark background
- Green/red candles
- Subtle grid lines
- Clean, minimal - this is a preview, not full chart

---

### 5. MAIN ACTION BUTTONS

These are the **heart of the dashboard**. Big, bold, impossible to miss.

#### Button: THE ARMORY ⚔️
- **Icon**: Crossed swords or shield
- **Subtitle**: "Acquire Your Data"
- **Leads to**: Data acquisition/loadout page
- **Color**: Gold/bronze (treasure)
- **State**: Always accessible

#### Button: LEARN 📚
- **Icon**: Open book or graduation cap  
- **Subtitle**: "Master the Fundamentals"
- **Leads to**: Tutorial section with Candles, etc.
- **Color**: Blue (knowledge)
- **State**: Shows progress badge (e.g., "3/12 complete")

#### Button: TEST 🧪
- **Icon**: Laboratory flask or target
- **Subtitle**: "Backtest Strategies"
- **Leads to**: Backtest engine
- **Color**: Purple (experimentation)
- **State**: Shows "X strategies tested"

#### Button: TRADE 📊
- **Icon**: Chart with candlesticks
- **Subtitle**: "Paper Trading"
- **Leads to**: Paper trading simulator
- **Color**: Green (money/go)
- **State**: Shows current P&L or "Start Trading"

**Button Behavior:**
- Hover: Subtle glow/lift effect
- Click: Satisfying press animation
- Locked state: Gray overlay with lock icon + unlock requirement
- Achievement: Brief sparkle when returning after completion

---

### 6. YOUR STATS PANEL

**Metrics to display:**
- Backtests Run (total count)
- Win Rate (% of profitable backtests)
- Best Strategy (highest return %)
- Paper P&L (cumulative paper trading result)
- Tutorial Progress (X/Y modules complete)
- Current Streak (days active)

**Behavior:**
- Numbers animate when they change
- Click any stat to see detailed breakdown
- Compare to community average (optional)

---

### 7. LEADERBOARD PREVIEW

**What it shows:**
- Top 3-5 strategies by performance
- User's best strategy highlighted if in top ranks
- "Your rank" indicator even if not in top 5

**Example:**
```
🥇 AlphaHunter       +342.5%  (user: @traderpro)
🥈 MomentumKing      +287.2%  (user: @quantwiz)
🥉 YOUR STRATEGY     +156.8%  ← YOU'RE #3!
4. TrendRider        +143.1%  (user: @chartmaster)
5. MeanReversion     +98.4%   (user: @statistician)

[View Full Leaderboard →]
```

**Behavior:**
- Click any strategy to see details
- "View Full" goes to complete leaderboard page
- Updates periodically (not real-time, too resource-intensive)
- Celebration animation if user enters top 10

---

### 8. DAILY CHALLENGE FOOTER

**What it shows:**
- One daily challenge with XP reward
- Clear call-to-action button

**Example Challenges:**
- "Backtest any strategy on DOGE using 1h candles" [+500 XP]
- "Complete the RSI tutorial module" [+300 XP]
- "Run 3 paper trades today" [+400 XP]
- "Create a strategy using only volume data" [+750 XP]

**Behavior:**
- New challenge at midnight UTC
- Timer showing time remaining
- Click "GO" to navigate to relevant section
- Completed challenges show checkmark and "Claimed"
- Streak bonus for consecutive daily completions

---

## RESPONSIVE DESIGN

### Desktop (1200px+)
- Full layout as shown above
- 4 action buttons in a row
- Side-by-side stats and leaderboard

### Tablet (768px - 1199px)
- 2x2 grid for action buttons
- Stats and leaderboard stack vertically
- Ticker tape remains full width

### Mobile (< 768px)
- Single column layout
- Action buttons: 2x2 grid, smaller
- Collapsible sections for stats/leaderboard
- Ticker tape: simpler, fewer items
- Bottom navigation bar for quick access

---

## REAL-TIME ELEMENTS

Things that should update without page refresh:
1. Ticker tape prices (5-10 second interval)
2. Mini chart candles (1-minute updates)
3. User stats (when action completes elsewhere)
4. Notification count
5. Daily challenge timer

---

## ANIMATIONS & MICRO-INTERACTIONS

### On Page Load
- Elements fade/slide in sequentially (staggered)
- Ticker tape begins scrolling
- Numbers "count up" to their values
- Progress bar fills to current percentage

### User Interactions
- Button hover: Glow + slight lift
- Button click: Press down + release
- Card hover: Subtle shadow increase
- Achievement earned: Confetti burst + sound

### Background Ambient
- Subtle particle effect (floating dots/lines)
- Gentle gradient shift in background
- Occasional "gleam" across metallic elements

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE STOCKTRADE HERO DASHBOARD

Context:
- This is the main navigation hub after the splash page
- Combines video game main menu + trading terminal aesthetics
- Must feel powerful, data-rich, but not overwhelming

Requirements:
1. Create dashboard at /app/dashboard or root page
2. Implement header with logo, notifications, settings, profile
3. Add scrolling ticker tape with live crypto prices
4. Show user's tier/progression card
5. Include mini live candlestick chart (start with static, add WebSocket later)
6. Create 4 large action buttons (Armory, Learn, Test, Trade)
7. Display user stats panel with key metrics
8. Add leaderboard preview showing top strategies
9. Footer with daily challenge and CTA
10. Make fully responsive (desktop, tablet, mobile)
11. Add smooth animations and micro-interactions

Tech suggestions:
- Use existing component library (shadcn/ui, etc.)
- Chart: lightweight-charts or TradingView widget
- Animations: Framer Motion
- Real-time: Start with polling, upgrade to WebSocket

State needed:
- User tier and progression (from API)
- User stats (backtests, win rate, etc.)
- Market data (prices for ticker)
- Leaderboard data (top strategies)
- Daily challenge (from API)

Deliverables:
- Dashboard page component
- Header component
- TickerTape component
- ProgressionCard component
- MiniChart component
- ActionButton component (reusable)
- StatsPanel component
- LeaderboardPreview component
- DailyChallenge component

Reference:
- See 01-splash-page.md for what precedes this
- See 03-armory-overview.md for Armory section
- See 07-tutorial-overview.md for Learn section
- See 10-leaderboard.md for full leaderboard
```

---

## ACCEPTANCE CRITERIA

- [ ] Dashboard loads in < 3 seconds
- [ ] All 4 main action buttons are visible without scrolling (desktop)
- [ ] Ticker tape scrolls smoothly with real or mock price data
- [ ] User's tier and progress are prominently displayed
- [ ] Mini chart shows candlestick data correctly
- [ ] Stats display accurate user metrics
- [ ] Leaderboard shows top strategies
- [ ] Daily challenge is visible and actionable
- [ ] Responsive design works on all screen sizes
- [ ] Animations enhance but don't distract
- [ ] Navigation to all sections works correctly

---

*Related Documents:*
- `00-overview.md` - System context
- `01-splash-page.md` - What precedes this
- `03-armory-overview.md` - The Armory section
- `07-tutorial-overview.md` - The Learn section
- `10-leaderboard.md` - Full leaderboard spec
