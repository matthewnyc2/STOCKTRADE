# 12 - API ENDPOINTS SPECIFICATION

## Overview

This document specifies all API endpoints needed for the gamified trading system. Organized by domain.

---

## BASE CONFIGURATION

```
Base URL: /api/v1
Authentication: Bearer token (Supabase Auth)
Content-Type: application/json
```

---

## PROGRESSION ENDPOINTS

### GET /progression/status

Get user's complete progression status.

**Response:**
```json
{
  "tier": {
    "current": 3,
    "name": "Journeyman",
    "xp": 8450,
    "xpToNextTier": 15000,
    "percentageToNext": 56.3
  },
  "prestige": {
    "count": 0,
    "bonuses": {}
  },
  "stats": {
    "totalBacktests": 47,
    "profitableBacktests": 29,
    "winRate": 61.7,
    "bestReturn": 89.3,
    "paperTradesPnl": 12450.00,
    "tutorialsCompleted": 8,
    "achievementsEarned": 12
  },
  "settings": {
    "assessmentMode": "game"
  }
}
```

---

### GET /progression/xp-history

Get recent XP transactions.

**Query params:**
- `limit` (optional, default 20)
- `offset` (optional, default 0)

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "amount": 150,
      "source": "tutorial",
      "description": "Completed module 2.3",
      "multiplier": 1.25,
      "multiplierReason": "streak_7_days",
      "balanceAfter": 8450,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 234,
  "hasMore": true
}
```

---

### POST /progression/settings

Update progression settings.

**Request:**
```json
{
  "assessmentMode": "professional"
}
```

**Response:**
```json
{
  "success": true,
  "settings": {
    "assessmentMode": "professional"
  }
}
```

---

## ARMORY ENDPOINTS

### GET /armory/status

Get user's armory status (unlocks and limits).

**Response:**
```json
{
  "tier": 3,
  "unlocks": {
    "assets": ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK", "MATIC", "SHIB"],
    "timeframes": ["5m", "15m", "1h", "4h", "1d"],
    "indicators": ["SMA", "EMA", "RSI", "MACD", "VOLUME", "BB", "STOCH", "ATR"],
    "maxDurationDays": 90,
    "exoticAccess": false
  },
  "limits": {
    "maxAssets": 25,
    "maxTimeframes": 5,
    "maxIndicators": 10
  }
}
```

---

### GET /armory/available

Get all available items (unlocked and locked).

**Response:**
```json
{
  "assets": {
    "unlocked": ["BTC", "ETH", ...],
    "locked": [
      {
        "key": "ATOM",
        "unlockRequirement": "Reach Tier 4",
        "gateId": "gate_tier_4"
      }
    ]
  },
  "timeframes": {
    "unlocked": ["15m", "1h", "4h", "1d"],
    "locked": [
      {
        "key": "1m",
        "unlockRequirement": "Reach Tier 4 and acknowledge risk",
        "gateId": "gate_unlock_1m"
      }
    ]
  },
  "indicators": {
    "unlocked": [...],
    "locked": [...]
  },
  "durations": {
    "available": [7, 30, 90],
    "locked": [
      {
        "days": 365,
        "unlockRequirement": "Reach Tier 4",
        "gateId": "gate_tier_4"
      }
    ]
  },
  "exotic": {
    "available": [],
    "locked": [
      {
        "key": "orderbook",
        "unlockRequirement": "Reach Tier 5",
        "gateId": "gate_tier_5"
      }
    ]
  }
}
```

---

### POST /armory/acquire

Request data acquisition for a loadout.

**Request:**
```json
{
  "assets": ["BTC", "ETH", "SOL", "AVAX"],
  "timeframe": "15m",
  "durationDays": 90,
  "indicators": ["RSI", "MACD", "EMA"],
  "indicatorConfigs": {
    "EMA": {"periods": [20, 50, 200]}
  }
}
```

**Response:**
```json
{
  "acquisitionId": "uuid",
  "status": "processing",
  "estimatedSeconds": 12,
  "estimatedDataPoints": 34560
}
```

---

### GET /armory/acquisition/:id

Check acquisition status.

**Response:**
```json
{
  "acquisitionId": "uuid",
  "status": "complete",
  "dataPoints": 34560,
  "processingTimeSeconds": 11.3,
  "dataUrl": "/api/v1/data/uuid"
}
```

---

## GATES ENDPOINTS

### GET /gates/status

Get status of all gates for the user.

**Response:**
```json
{
  "gates": [
    {
      "gateId": "gate_tier_2_to_3",
      "name": "Advance to Tier 3",
      "passed": false,
      "progress": {
        "percentage": 75,
        "requirements": [
          {"id": "backtests_10", "label": "Run 10 backtests", "current": 12, "required": 10, "complete": true},
          {"id": "profitable_3", "label": "3 profitable backtests", "current": 5, "required": 3, "complete": true},
          {"id": "candles_101", "label": "Complete Candles 101", "complete": false},
          {"id": "patterns_quiz", "label": "Pass patterns quiz (70%+)", "complete": false}
        ]
      }
    }
  ]
}
```

---

### POST /gates/check

Manually trigger gate evaluation.

**Request:**
```json
{
  "gateId": "gate_tier_2_to_3"
}
```

**Response:**
```json
{
  "gateId": "gate_tier_2_to_3",
  "passed": true,
  "newlyPassed": true,
  "rewards": {
    "tierAdvancement": 3,
    "unlocks": ["ATOM", "ichimoku", "90_days"],
    "xpEarned": 500
  }
}
```

---

### POST /gates/acknowledge

Acknowledge a warning gate (e.g., 1m timeframe risk).

**Request:**
```json
{
  "gateId": "gate_unlock_1m",
  "acknowledged": true
}
```

---

## TUTORIAL ENDPOINTS

### GET /tutorial/tracks

Get all tutorial tracks with progress.

**Response:**
```json
{
  "tracks": [
    {
      "id": "foundations",
      "name": "Foundations",
      "description": "The basics every trader must know",
      "modulesTotal": 5,
      "modulesComplete": 5,
      "percentComplete": 100,
      "isUnlocked": true
    },
    {
      "id": "candlesticks",
      "name": "Candlesticks",
      "description": "Master the language of price action",
      "modulesTotal": 7,
      "modulesComplete": 2,
      "percentComplete": 28.6,
      "isUnlocked": true
    },
    {
      "id": "technical_analysis",
      "name": "Technical Analysis",
      "description": "Indicators, trends, and signals",
      "modulesTotal": 8,
      "modulesComplete": 0,
      "percentComplete": 0,
      "isUnlocked": false,
      "unlockRequirement": "Complete Candlesticks track"
    }
  ]
}
```

---

### GET /tutorial/track/:trackId

Get modules within a track.

**Response:**
```json
{
  "track": {
    "id": "candlesticks",
    "name": "Candlesticks",
    "modules": [
      {
        "id": "2.1",
        "title": "What is a Candle?",
        "isComplete": true,
        "bestScore": 2450,
        "bestScoreMode": "game",
        "isUnlocked": true
      },
      {
        "id": "2.2",
        "title": "Reading Candle Charts",
        "isComplete": true,
        "bestScore": 94,
        "bestScoreMode": "professional",
        "isUnlocked": true
      },
      {
        "id": "2.3",
        "title": "Single Candle Patterns",
        "isComplete": false,
        "inProgress": true,
        "sectionsComplete": ["learn_it", "see_it"],
        "isUnlocked": true
      },
      {
        "id": "2.4",
        "title": "Two-Candle Patterns",
        "isComplete": false,
        "isUnlocked": false,
        "unlockRequirement": "Complete module 2.3"
      }
    ]
  }
}
```

---

### GET /tutorial/module/:trackId/:moduleId

Get module content.

**Response:**
```json
{
  "module": {
    "id": "2.1",
    "trackId": "candlesticks",
    "title": "What is a Candle?",
    "learnIt": {
      "sections": [
        {
          "id": "basics",
          "title": "The Basics",
          "content": "...",
          "diagrams": [...]
        }
      ]
    },
    "seeIt": {
      "examples": [...]
    },
    "playIt": {
      "passThreshold": {
        "game": 2000,
        "professional": 70
      },
      "questionCount": 10
    },
    "masterIt": {
      "available": true,
      "timeLimit": 120,
      "questionCount": 20
    }
  },
  "progress": {
    "learnItComplete": true,
    "seeItComplete": true,
    "playItComplete": false,
    "masterItComplete": false
  }
}
```

---

### POST /tutorial/module/:trackId/:moduleId/complete-section

Mark a section as complete.

**Request:**
```json
{
  "section": "learn_it"
}
```

**Response:**
```json
{
  "success": true,
  "xpEarned": 25,
  "newTotal": 8475
}
```

---

### GET /tutorial/quiz/:trackId/:moduleId/:section

Get quiz questions for play_it or master_it.

**Response:**
```json
{
  "quiz": {
    "id": "2.1_play_it",
    "mode": "game",
    "timeLimit": null,
    "questions": [
      {
        "id": "2.1.1",
        "type": "multiple_choice",
        "question": "What does OHLC stand for?",
        "options": ["Open, High, Low, Close", ...],
        "money": 250,
        "xp": 10
      }
    ],
    "passThreshold": 2000
  }
}
```

---

### POST /tutorial/quiz/:trackId/:moduleId/:section/submit

Submit quiz results.

**Request:**
```json
{
  "answers": [
    {"questionId": "2.1.1", "answer": 0},
    {"questionId": "2.1.2", "answer": 1}
  ],
  "timeElapsed": 180
}
```

**Response:**
```json
{
  "results": {
    "questionsTotal": 10,
    "questionsCorrect": 8,
    "percentage": 80,
    "moneyEarned": 2450,
    "bonuses": [
      {"name": "Hot Streak", "amount": 200},
      {"name": "Speed Bonus", "amount": 150}
    ],
    "totalMoney": 2800,
    "passed": true,
    "xpEarned": 150
  },
  "sectionComplete": true,
  "moduleComplete": false,
  "unlocksTriggered": []
}
```

---

## LEADERBOARD ENDPOINTS

### GET /leaderboard

Get leaderboard with filters.

**Query params:**
- `metric` (default: "total_return") - total_return, sharpe_ratio, win_rate, max_drawdown
- `period` (default: 90) - 30, 90, 365, 0 (all time)
- `asset` (optional) - filter by asset
- `page` (default: 1)
- `limit` (default: 50)

**Response:**
```json
{
  "leaderboard": {
    "metric": "total_return",
    "period": 90,
    "entries": [
      {
        "rank": 1,
        "strategyId": "uuid",
        "strategyName": "MomentumAlpha",
        "userId": "uuid",
        "username": "traderpro",
        "totalReturn": 342.5,
        "sharpeRatio": 2.84,
        "winRate": 68.4,
        "maxDrawdown": -12.3,
        "previousRank": 1,
        "rankChange": 0
      }
    ],
    "total": 1247,
    "page": 1,
    "hasMore": true
  },
  "userBest": {
    "rank": 42,
    "strategyName": "RSI_Bounce_v2",
    "totalReturn": 67.3
  }
}
```

---

### GET /leaderboard/strategy/:id

Get strategy detail.

**Response:**
```json
{
  "strategy": {
    "id": "uuid",
    "name": "MomentumAlpha",
    "creator": {
      "id": "uuid",
      "username": "traderpro"
    },
    "metrics": {
      "totalReturn": 342.5,
      "sharpeRatio": 2.84,
      "winRate": 68.4,
      "maxDrawdown": -12.3,
      "totalTrades": 47,
      "avgTradeDuration": 6.2
    },
    "config": {
      "assets": ["BTC", "ETH", "SOL"],
      "timeframe": "1h",
      "periodDays": 90
    },
    "equityCurve": [...],
    "ranks": {
      "byReturn": 1,
      "bySharpe": 3,
      "byWinRate": 12
    },
    "isPublic": false,
    "submittedAt": "2024-01-10T15:30:00Z"
  }
}
```

---

### POST /leaderboard/submit

Submit a backtest to the leaderboard.

**Request:**
```json
{
  "backtestId": "uuid",
  "strategyName": "My_Strategy_v2",
  "isPublic": false
}
```

**Response:**
```json
{
  "success": true,
  "rank": 42,
  "message": "Your strategy ranked #42 out of 1247"
}
```

---

### GET /leaderboard/me

Get user's strategies on the leaderboard.

**Response:**
```json
{
  "strategies": [
    {
      "id": "uuid",
      "name": "RSI_Bounce_v2",
      "rank": 42,
      "previousRank": 45,
      "totalReturn": 67.3,
      "submittedAt": "2024-01-12T10:00:00Z"
    }
  ]
}
```

---

## ACHIEVEMENTS ENDPOINTS

### GET /achievements

Get user's achievements.

**Response:**
```json
{
  "earned": [
    {
      "id": "first_backtest",
      "name": "First Blood",
      "description": "Complete your first backtest",
      "icon": "🎯",
      "rarity": "common",
      "earnedAt": "2024-01-05T12:00:00Z"
    }
  ],
  "available": [
    {
      "id": "top_100",
      "name": "Top 100",
      "description": "Get a strategy in the top 100",
      "icon": "🏅",
      "rarity": "rare",
      "progress": {
        "current": 142,
        "target": 100
      }
    }
  ]
}
```

---

## DAILY CHALLENGE ENDPOINTS

### GET /daily-challenge

Get today's challenge.

**Response:**
```json
{
  "challenge": {
    "id": "uuid",
    "date": "2024-01-15",
    "text": "Backtest any strategy on DOGE using 1h candles",
    "type": "backtest",
    "requirements": {
      "asset": "DOGE",
      "timeframe": "1h"
    },
    "xpReward": 500,
    "timeRemaining": "14:32:15"
  },
  "isComplete": false,
  "streak": {
    "current": 5,
    "best": 12
  }
}
```

---

### POST /daily-challenge/complete

Mark daily challenge as complete.

**Request:**
```json
{
  "challengeId": "uuid",
  "proofId": "backtest_uuid"
}
```

**Response:**
```json
{
  "success": true,
  "xpEarned": 500,
  "streakBonus": 50,
  "newStreak": 6
}
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE API LAYER

Context:
- RESTful API for the game system
- Uses Supabase for database
- Authentication via Supabase Auth
- All endpoints require authentication except leaderboard reads

Requirements:
1. Implement all endpoints as specified
2. Use proper HTTP status codes
3. Implement rate limiting
4. Add request validation
5. Handle errors consistently
6. Log all requests for debugging
7. Add OpenAPI/Swagger documentation

Error format:
{
  "error": {
    "code": "GATE_NOT_PASSED",
    "message": "You must complete gate X to access this feature",
    "details": {...}
  }
}

Middleware needed:
- Auth verification
- Rate limiting
- Request logging
- Error handling

Deliverables:
- All route handlers
- Middleware functions
- OpenAPI spec
- Postman collection for testing

Reference:
- See 11-progression-database.md for data models
- See 05-armory-gates.md for gate logic
```

---

## ACCEPTANCE CRITERIA

- [ ] All endpoints implemented and tested
- [ ] Authentication works correctly
- [ ] Rate limiting prevents abuse
- [ ] Error responses are consistent
- [ ] Swagger docs are generated
- [ ] Postman collection works

---

*Related Documents:*
- `11-progression-database.md` - Database schema
- `05-armory-gates.md` - Gate logic
- All feature documents for business logic
