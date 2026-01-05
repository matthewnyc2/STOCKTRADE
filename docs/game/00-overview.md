# STOCKTRADE GAME SYSTEM - MASTER OVERVIEW

## Document Index

This folder contains modular specifications for the gamified trading education and data acquisition system. Each document is self-contained but references related documents.

### Document Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ENTRY POINTS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  01-splash-page.md          The Scrooge McDuck money bin splash         │
│  02-hero-dashboard.md       Main dashboard with metrics & navigation    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           THE ARMORY                                    │
│                    (Data Acquisition System)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  03-armory-overview.md      Core concept and philosophy                 │
│  04-armory-tiers.md         Detailed tier progression (1-5)             │
│  05-armory-gates.md         Gate mechanics and unlock conditions        │
│  06-armory-ui.md            UI wireframes and component specs           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EDUCATION SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  07-tutorial-overview.md    Tutorial section structure                  │
│  08-candles-curriculum.md   Complete candles education path             │
│  09-learn-play-system.md    The learn-it / play-it dual mode system     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPETITION & PROGRESS                           │
├─────────────────────────────────────────────────────────────────────────┤
│  10-leaderboard.md          Strategy leaderboard system                 │
│  11-progression-database.md Database schema for all progression         │
│  12-api-endpoints.md        Complete API specification                  │
│  13-special-mechanics.md    Bounties, gauntlet, prestige, recipes       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## THE CORE PHILOSOPHY

### The Metaphor
This is not a trading app. This is a **video game** where the final boss is the market itself.

- Data is not downloaded, it is **acquired**
- Knowledge is not learned, it is **unlocked**
- Strategies are not created, they are **forged**
- Profits are not made, they are **conquered**

### The Two Modes

Every educational and testing component has TWO presentation modes:

| Mode | Tone | Progress Metric | Unlock Mechanism |
|------|------|-----------------|------------------|
| **GAME MODE** | Playful, competitive | Virtual money earned | "Win" enough to advance |
| **PROFESSIONAL MODE** | Serious, educational | Test scores | Pass with required % |

The underlying logic is IDENTICAL. Only the skin changes.

### The Flow

```
User arrives
     │
     ▼
┌─────────────┐
│ Splash Page │ ──── Scrooge McDuck money bin with animated M
└─────────────┘
     │
     ▼
┌─────────────┐
│    Hero     │ ──── Dashboard with big buttons, metrics, live ticker
│  Dashboard  │
└─────────────┘
     │
     ├──────────────────┬──────────────────┬──────────────────┐
     ▼                  ▼                  ▼                  ▼
┌─────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐
│ ARMORY  │      │  TUTORIAL │      │  BACKTEST │      │  PAPER    │
│ (Data)  │      │  (Learn)  │      │  (Test)   │      │  TRADING  │
└─────────┘      └───────────┘      └───────────┘      └───────────┘
     │                  │                  │                  │
     └──────────────────┴──────────────────┴──────────────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │    LEADERBOARD    │
                    │  (Your strategies │
                    │   compete here)   │
                    └───────────────────┘
```

---

## CROSS-CUTTING CONCERNS

### State That Must Persist

All documents assume a central `user_progression` state that tracks:
- Current tier (1-5)
- XP earned
- Gates passed
- Assets unlocked
- Indicators unlocked
- Timeframes unlocked
- Tutorial progress
- Candle mastery levels
- Strategy performance history
- Leaderboard positions

See `11-progression-database.md` for full schema.

### Shared Components

These UI components appear across multiple features:
- **Progress Bar** - Shows advancement toward next unlock
- **Lock Overlay** - Grays out unavailable features with unlock hint
- **XP Toast** - Animated notification when XP is earned
- **Tier Badge** - User's current tier displayed consistently
- **Money Counter** - Animated counting for game mode earnings

---

## IMPLEMENTATION ORDER

Recommended build sequence:

1. **Phase 1: Foundation**
   - `11-progression-database.md` (need state before anything)
   - `12-api-endpoints.md` (basic tier/unlock checks)
   - `01-splash-page.md` (first thing users see)

2. **Phase 2: Core Loop**
   - `02-hero-dashboard.md` (navigation hub)
   - `03-armory-overview.md` + `04-armory-tiers.md` (data acquisition)
   - `06-armory-ui.md` (armory interface)

3. **Phase 3: Education**
   - `07-tutorial-overview.md` (tutorial structure)
   - `08-candles-curriculum.md` (first educational track)
   - `09-learn-play-system.md` (the game/test dual mode)

4. **Phase 4: Competition**
   - `10-leaderboard.md` (strategy rankings)
   - `05-armory-gates.md` (unlock conditions)
   - `13-special-mechanics.md` (bounties, gauntlet, prestige)

---

## RELATED EXISTING CODE

The game system integrates with existing STOCKTRADE modules:

| Existing Module | Integration Point |
|-----------------|-------------------|
| `/paper-trading` | Paper trade results feed into gate evaluation |
| `/backtest` | Backtest results determine tier progression |
| `/laboratory` | Strategy creation earns XP |
| `/dashboard` | Shows current tier and progress |

---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Armory** | The data acquisition section (game name for data store) |
| **Gate** | A challenge that must be passed to unlock features |
| **Tier** | User's overall progression level (1-5) |
| **Loadout** | A specific combination of assets/timeframes/indicators for a mission |
| **XP** | Experience points earned through activity |
| **Prestige** | Optional reset for cosmetic rewards |
| **The Gauntlet** | A series of 7 challenges that unlock Tier 5 |

---

*Last Updated: Document creation date*
*Related: All documents in /docs/game/*
