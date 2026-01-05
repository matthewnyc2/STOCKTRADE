# 08 - CANDLES CURRICULUM: DETAILED CONTENT

## Overview

This document contains the complete educational content for the Candlesticks track. Each module includes learning content, examples, quiz questions, and game scenarios.

---

## MODULE 2.1: WHAT IS A CANDLE?

### LEARN IT

#### Section 1: The Basics

```
WHAT IS A CANDLE?

A candlestick is a way to visualize price movement over a specific time period.

Instead of just showing where the price ended up, a candle tells you 
FOUR important pieces of information:

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                         ─┬─  HIGH (the highest price)       │
│                          │   reached during this period     │
│                          │                                  │
│                    ┌─────┴─────┐                           │
│                    │           │ CLOSE (where price        │
│                    │   BODY    │ ended) - if green/white   │
│                    │           │                            │
│                    │           │ OPEN (where price          │
│                    └─────┬─────┘ started) - if green/white │
│                          │                                  │
│                          │                                  │
│                         ─┴─  LOW (the lowest price)        │
│                              reached during this period    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

These four prices are called "OHLC" - Open, High, Low, Close.
```

#### Section 2: Body and Wicks

```
THE BODY

The thick rectangle in the middle is called the BODY.
It shows the range between the OPEN and CLOSE prices.

• A TALL body means the price moved a lot from open to close
• A SHORT body means the price stayed relatively flat

THE WICKS (OR SHADOWS)

The thin lines above and below the body are called WICKS or SHADOWS.

• The UPPER WICK shows how high the price went before coming back down
• The LOWER WICK shows how low the price went before coming back up

LONG WICKS indicate the price was rejected from those levels.
```

#### Section 3: Color Meaning

```
CANDLE COLORS

🟢 GREEN (or white) candle:
   The price CLOSED HIGHER than it opened.
   This is considered BULLISH (buyers won this period).

🔴 RED (or black) candle:
   The price CLOSED LOWER than it opened.
   This is considered BEARISH (sellers won this period).

Example:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     GREEN CANDLE              RED CANDLE                   │
│                                                             │
│         │                         │                        │
│     ┌───┴───┐                 ┌───┴───┐                   │
│     │ CLOSE │                 │ OPEN  │                   │
│     │       │                 │       │                   │
│     │       │                 │       │                   │
│     │ OPEN  │                 │ CLOSE │                   │
│     └───┬───┘                 └───┬───┘                   │
│         │                         │                        │
│                                                             │
│  Price went UP              Price went DOWN                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Section 4: Timeframes

```
WHAT DOES "ONE CANDLE" REPRESENT?

A candle represents ONE PERIOD of time. The timeframe determines how long:

• 1-MINUTE candle: OHLC for the past minute
• 15-MINUTE candle: OHLC for the past 15 minutes
• 1-HOUR candle: OHLC for the past hour
• 1-DAY candle: OHLC for the past day

The SAME price action looks DIFFERENT at different timeframes:

Many small candles on 1m chart = ONE candle on 1h chart

This is why TIMEFRAME MATTERS when analyzing charts.
```

---

### SEE IT: Examples

#### Example 1: Reading a Real Candle

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  This is a 1-HOUR candle for BTC:                          │
│                                                             │
│              │                                              │
│          ┌───┴───┐  ← High: $67,500                        │
│          │       │                                          │
│          │ GREEN │  ← Close: $67,400                       │
│          │       │                                          │
│          │       │  ← Open: $67,100                        │
│          └───┬───┘                                          │
│              │      ← Low: $67,000                          │
│                                                             │
│  What this tells us:                                        │
│  • Price started the hour at $67,100                       │
│  • Dropped briefly to $67,000                              │
│  • Rallied up to $67,500                                   │
│  • Settled at $67,400 when the hour ended                  │
│  • Overall: BULLISH hour (closed higher than opened)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Example 2: Body Size Meaning

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  BIG BODY               vs          SMALL BODY              │
│                                                             │
│      │                                  │                   │
│  ┌───┴───┐                          ┌──┴──┐                │
│  │       │                          │     │                │
│  │       │                          └──┬──┘                │
│  │       │                             │                   │
│  │       │                                                  │
│  └───┬───┘                                                  │
│      │                                                      │
│                                                             │
│  Strong conviction!         Indecision / equilibrium       │
│  Buyers dominated.          Neither side won clearly.      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### PLAY IT: Quiz Questions

#### Question Bank (randomize, show 10)

```yaml
questions:
  - id: "2.1.1"
    type: "multiple_choice"
    question: "What does OHLC stand for?"
    options:
      - "Open, High, Low, Close"
      - "Over, High, Low, Closed"
      - "Opening, Highest, Lowest, Closing"
      - "Order, Hold, Limit, Cancel"
    correct: 0
    explanation: "OHLC stands for Open, High, Low, Close - the four prices shown in a candlestick."
    xp: 10
    money: 100
    
  - id: "2.1.2"
    type: "multiple_choice"
    question: "A green candle means..."
    options:
      - "The price closed higher than it opened"
      - "The price closed lower than it opened"
      - "The price didn't change"
      - "The volume was high"
    correct: 0
    explanation: "Green candles indicate bullish price action - the close is higher than the open."
    xp: 10
    money: 100
    
  - id: "2.1.3"
    type: "identify"
    question: "Click on the HIGH price in this candle"
    image: "candle_identify_high.svg"
    correct_zone: "top_wick_tip"
    explanation: "The high is at the very top of the upper wick."
    xp: 15
    money: 150
    
  - id: "2.1.4"
    type: "multiple_choice"
    question: "A candle with a long lower wick suggests..."
    options:
      - "Price was rejected at lower levels - buyers stepped in"
      - "Price will continue going down"
      - "The candle is bullish"
      - "Volume was low"
    correct: 0
    explanation: "Long lower wicks show that sellers pushed price down but buyers pushed it back up."
    xp: 15
    money: 150
    
  - id: "2.1.5"
    type: "build_candle"
    question: "Build a candle with these values: Open=$100, High=$110, Low=$95, Close=$105"
    correct_candle:
      open: 100
      high: 110
      low: 95
      close: 105
      color: "green"
    explanation: "Since close ($105) > open ($100), this is a green candle."
    xp: 20
    money: 200
    
  - id: "2.1.6"
    type: "fill_blank"
    question: "A candle with a very small body is said to show _____"
    correct_answers: ["indecision", "equilibrium", "balance"]
    explanation: "When open and close are nearly equal, neither buyers nor sellers dominated."
    xp: 10
    money: 100
    
  - id: "2.1.7"
    type: "true_false"
    question: "A 1-hour candle and a 1-day candle will always show the same high price."
    correct: false
    explanation: "A 1-day candle shows the highest price of the entire day, while any single 1-hour candle only shows the highest price during that hour."
    xp: 10
    money: 100
    
  - id: "2.1.8"
    type: "order"
    question: "Put these in order from shortest to longest timeframe:"
    items: ["1 day", "15 minutes", "4 hours", "1 minute"]
    correct_order: [3, 1, 2, 0]  # 1min, 15min, 4hr, 1day
    explanation: "1 minute < 15 minutes < 4 hours < 1 day"
    xp: 15
    money: 150
```

---

### MASTER IT: Speed Round

```yaml
master_challenge:
  name: "Candle Basics Speedrun"
  description: "Answer 20 candle identification questions in under 2 minutes"
  time_limit: 120  # seconds
  questions: 20
  pass_threshold: 16  # 80%
  perfect_threshold: 20
  
  rewards:
    pass: 
      xp: 100
      money: 1000
    perfect:
      xp: 200
      money: 2500
      badge: "Candle Reader I"
```

---

## MODULE 2.2: READING CANDLE CHARTS

### LEARN IT

#### Section 1: From Candle to Chart

```
HOW CHARTS FORM

When you line up many candles side by side, you get a CHART.

Each candle represents one time period. Reading left to right,
you're reading forward through time.

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Time flows left → right                                   │
│                                                             │
│  Past ←──────────────────────────────────────────→ Present │
│                                                             │
│   │      │   │                     │                       │
│   │  ┌┴┐ │  ┌┴┐    │      │    │ ┌┴┐                      │
│  ┌┴┐ │ │ ├┐ │ │   ┌┴┐    ┌┴┐  ┌┴┐│ │                      │
│  │ │ │ │ ││ │ │   │ │    │ │  │ ││ │                      │
│  │ │ └┬┘ │└┬┘ │   │ │    │ │  │ │└┬┘                      │
│  └┬┘  │  │ │  └┬┘ └┬┘    └┬┘  └┬┘ │                       │
│   │   │  │ │   │   │      │    │  │                       │
│                                                             │
│  Each bar = one time period (1 hour, 1 day, etc.)          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Section 2: Trends

```
READING TRENDS

When you look at a chart, ask yourself:
"Are the candles generally going UP, DOWN, or SIDEWAYS?"

UPTREND:                  DOWNTREND:              SIDEWAYS:
Higher highs              Lower highs             Highs/lows stay
Higher lows               Lower lows              in a range

     ╱                         ╲                   ─────────
    ╱                           ╲                  
   ╱                             ╲                 ─────────
  ╱                               ╲                
                                                   ─────────
"Stairs going up"      "Stairs going down"       "A hallway"
```

#### Section 3: Support and Resistance

```
SUPPORT AND RESISTANCE

SUPPORT: A price level where buying tends to come in.
         Think of it as a "floor" that holds up the price.

RESISTANCE: A price level where selling tends to come in.
            Think of it as a "ceiling" that caps the price.

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ════════════════════════════════  ← RESISTANCE            │
│         │                                                   │
│        ┌┴┐    │     │                                      │
│        │ │   ┌┴┐   ┌┴┐   Price keeps bouncing              │
│        └┬┘   │ │   │ │   off these levels                  │
│         │    └┬┘   └┬┘                                      │
│                │     │                                      │
│  ════════════════════════════════  ← SUPPORT               │
│                                                             │
└─────────────────────────────────────────────────────────────┘

When price BREAKS through support or resistance, 
it often moves strongly in that direction.
```

---

### SEE IT: Examples

```
EXAMPLE: Real BTC Chart with Annotations

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  $68,000 ─────────────────────────────────┐                │
│                         Resistance zone → │                │
│                    ╱╲      ╱╲             │                │
│                   ╱  ╲    ╱  ╲   Price rejected here      │
│                  ╱    ╲  ╱    ╲           │                │
│  $65,000 ──────╱──────╲╱──────────────────┘                │
│              ╱                                              │
│             ╱         ← Uptrend: higher lows               │
│            ╱                                                │
│  $62,000 ─╱─────────────────────────────────────           │
│         ╱  Support held here twice →                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Analysis:
• Overall trend: UP (making higher lows)
• Resistance at ~$68,000 (tested twice, rejected)
• Support at ~$62,000 (held twice)
• Trade idea: Buy at support, sell at resistance (range trading)
```

---

### PLAY IT: Quiz Questions

```yaml
questions:
  - id: "2.2.1"
    type: "chart_analysis"
    question: "Is this chart showing an uptrend, downtrend, or sideways?"
    chart: "trend_identification_1.svg"
    options: ["Uptrend", "Downtrend", "Sideways"]
    correct: 0
    explanation: "The chart shows higher highs and higher lows - classic uptrend."
    xp: 15
    money: 150
    
  - id: "2.2.2"
    type: "click_zone"
    question: "Click on the major support level in this chart"
    chart: "support_identification.svg"
    correct_zone: "horizontal_line_bottom"
    explanation: "Support is at the level where price bounced multiple times."
    xp: 20
    money: 200
    
  - id: "2.2.3"
    type: "prediction"
    question: "Price is approaching resistance. What's MOST likely to happen?"
    chart: "approaching_resistance.svg"
    options:
      - "Price will probably bounce down from resistance"
      - "Price will definitely break through"
      - "Resistance doesn't matter"
      - "The chart will restart"
    correct: 0
    explanation: "Price often bounces from established resistance, though breakouts do occur."
    xp: 15
    money: 150
```

---

## MODULE 2.3: SINGLE CANDLE PATTERNS

### LEARN IT

#### The Doji

```
THE DOJI
═════════

A Doji has a very small or nonexistent body.
The open and close are at (nearly) the same price.

       │
   ────┼────   The cross shape shows:
       │       • Price moved up and down (wicks)
               • But ended where it started (tiny body)

MEANING: INDECISION
• Buyers and sellers are in equilibrium
• Often appears at turning points
• The trend may be about to change

TYPES OF DOJI:

Standard    Dragonfly    Gravestone    Long-legged
   │            │             │             │
───┼───     ────┴─────    ────┬────    ────┼────
   │                          │             │
                                           
Neutral    Bullish at     Bearish at    Extreme
           bottoms        tops          indecision
```

#### Hammer / Hanging Man

```
HAMMER (at bottom of downtrend)
═══════════════════════════════

      ┌─┐
      │ │      Small body at the TOP
      └┬┘
       │
       │       Long lower wick
       │       (at least 2x the body)
       │

MEANING: Potential bullish reversal
• Sellers pushed price down hard (long wick)
• But buyers pushed it all the way back up
• Shows buying strength returning

─────────────────────────────────────

HANGING MAN (at top of uptrend)
════════════════════════════════

      ┌─┐
      │ │      Same shape as hammer
      └┬┘      BUT appears after an uptrend
       │
       │
       │

MEANING: Potential bearish reversal
• Context matters: same shape, opposite meaning
• Shows sellers are starting to fight back
```

---

### PLAY IT: Pattern Recognition Game

```yaml
game_mode:
  name: "Pattern Spotter"
  description: "Identify candle patterns as they appear"
  
  mechanics:
    - Show a candle or small group of candles
    - Player must identify the pattern
    - Correct = earn money/points
    - Wrong = lose a life (3 lives)
    - Speed bonus for fast answers
  
  rounds:
    - round: 1
      patterns: ["doji", "hammer", "shooting_star"]
      time_per_question: 10
      reward_per_correct: 100
      
    - round: 2
      patterns: ["doji", "hammer", "shooting_star", "marubozu", "spinning_top"]
      time_per_question: 8
      reward_per_correct: 150
      
    - round: 3
      patterns: "all_single_candle"
      time_per_question: 6
      reward_per_correct: 200
      bonus_for_streak: 50  # per correct in a row

  pass_requirement:
    game_mode: 2000  # dollars earned
    professional_mode: 70  # percent correct
```

---

## CONTENT DELIVERY FORMAT

### For Developers: Content Structure

```typescript
interface ModuleContent {
  id: string
  title: string
  track: string
  order: number
  
  learnIt: {
    sections: Section[]
    estimatedMinutes: number
  }
  
  seeIt: {
    examples: Example[]
    estimatedMinutes: number
  }
  
  playIt: {
    questions: Question[]
    gameConfig?: GameConfig
    passThreshold: {
      gameMode: number      // dollars to earn
      professionalMode: number  // percentage
    }
  }
  
  masterIt?: {
    challenge: Challenge
    rewards: Rewards
  }
  
  unlocks: string[]  // What completing this module unlocks
  prerequisites: string[]  // What must be completed first
}

interface Section {
  id: string
  title: string
  content: string  // Markdown with special diagram syntax
  diagrams?: Diagram[]
  interactive?: InteractiveElement[]
}

interface Question {
  id: string
  type: 'multiple_choice' | 'true_false' | 'identify' | 'build_candle' | 
        'fill_blank' | 'order' | 'chart_analysis' | 'click_zone' | 'prediction'
  question: string
  image?: string
  options?: string[]
  correct: number | boolean | string | number[] | Zone
  explanation: string
  xp: number
  money: number
}
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE CANDLES CURRICULUM CONTENT

Context:
- This is Track 2 of the Tutorial system
- Contains 7 modules on candlestick analysis
- Each module has Learn/See/Play/Master sections
- Content provided in this document

Requirements:
1. Create content data structure for all modules
2. Build renderers for different content types:
   - Text with diagrams
   - Interactive candle builder
   - Pattern recognition exercises
   - Chart analysis questions
3. Implement quiz engine supporting all question types
4. Create game mode wrapper (earn money for correct)
5. Build progress tracking per module

Content creation:
- Parse diagram ASCII art or create SVG equivalents
- Create interactive candle building component
- Build pattern recognition with click zones
- Generate random variations for replayability

Deliverables:
- candlesContent.ts (all module data)
- CandleDiagram component
- InteractiveCandleBuilder component
- PatternRecognition component
- QuizEngine service
- GameModeWrapper component

Reference:
- See 07-tutorial-overview.md for tutorial structure
- See 09-learn-play-system.md for game mechanics
- See 11-progression-database.md for progress storage
```

---

## ACCEPTANCE CRITERIA

- [ ] All 7 Candles modules have complete content
- [ ] Learn It sections render with proper diagrams
- [ ] See It examples are clear and annotated
- [ ] All question types work correctly
- [ ] Game mode converts scores to money
- [ ] Professional mode shows percentages
- [ ] Master challenges work with timers
- [ ] Progress saves correctly
- [ ] Unlocks trigger when modules complete

---

*Related Documents:*
- `07-tutorial-overview.md` - Tutorial system
- `09-learn-play-system.md` - Game/test mechanics
- `05-armory-gates.md` - How tutorials unlock Armory items
