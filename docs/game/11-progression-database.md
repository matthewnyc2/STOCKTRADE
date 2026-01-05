# 11 - PROGRESSION DATABASE SCHEMA

## Overview

This document specifies the complete database schema for storing all progression, unlock, and achievement state across the gamified trading system.

---

## CORE TABLES

### users_progression

The main table tracking a user's overall game state.

```sql
CREATE TABLE users_progression (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Tier progression
  current_tier INTEGER NOT NULL DEFAULT 1 CHECK (current_tier BETWEEN 1 AND 5),
  current_xp INTEGER NOT NULL DEFAULT 0,
  lifetime_xp INTEGER NOT NULL DEFAULT 0,
  
  -- Prestige system
  prestige_count INTEGER NOT NULL DEFAULT 0,
  prestige_bonuses JSONB DEFAULT '{}',
  
  -- Timestamps
  tier_2_unlocked_at TIMESTAMPTZ,
  tier_3_unlocked_at TIMESTAMPTZ,
  tier_4_unlocked_at TIMESTAMPTZ,
  tier_5_unlocked_at TIMESTAMPTZ,
  last_prestige_at TIMESTAMPTZ,
  
  -- Settings
  assessment_mode VARCHAR(20) DEFAULT 'game' CHECK (assessment_mode IN ('game', 'professional')),
  
  -- Meta
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- Index for quick lookups
CREATE INDEX idx_users_progression_user_id ON users_progression(user_id);
CREATE INDEX idx_users_progression_tier ON users_progression(current_tier);
```

---

### armory_unlocks

Tracks what each user has unlocked in the Armory.

```sql
CREATE TABLE armory_unlocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Unlock type
  unlock_type VARCHAR(50) NOT NULL, -- 'asset', 'timeframe', 'indicator', 'exotic', 'duration'
  unlock_key VARCHAR(100) NOT NULL, -- 'BTC', '1m', 'RSI', 'orderbook', '365'
  
  -- How it was unlocked
  unlock_source VARCHAR(50) NOT NULL, -- 'tier_advancement', 'gate_completion', 'tutorial', 'purchase'
  source_reference VARCHAR(100), -- gate_id, tutorial_id, etc.
  
  -- Timestamps
  unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id, unlock_type, unlock_key)
);

CREATE INDEX idx_armory_unlocks_user ON armory_unlocks(user_id);
CREATE INDEX idx_armory_unlocks_type ON armory_unlocks(unlock_type);
```

---

### gates_progress

Tracks progress toward completing gates.

```sql
CREATE TABLE gates_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  gate_id VARCHAR(100) NOT NULL, -- 'gate_tier_1_to_2', 'gate_unlock_rsi', etc.
  
  -- Progress tracking
  is_complete BOOLEAN NOT NULL DEFAULT FALSE,
  completed_at TIMESTAMPTZ,
  
  -- For count-based gates
  current_count INTEGER DEFAULT 0,
  required_count INTEGER,
  
  -- For metric-based gates
  current_value DECIMAL(10,4),
  required_value DECIMAL(10,4),
  
  -- For multi-requirement gates
  requirements_status JSONB DEFAULT '{}', -- {"req1": true, "req2": false, ...}
  
  -- Timestamps
  first_progress_at TIMESTAMPTZ,
  last_progress_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id, gate_id)
);

CREATE INDEX idx_gates_progress_user ON gates_progress(user_id);
CREATE INDEX idx_gates_progress_gate ON gates_progress(gate_id);
CREATE INDEX idx_gates_progress_incomplete ON gates_progress(user_id) WHERE is_complete = FALSE;
```

---

### tutorial_progress

Tracks progress through tutorial modules.

```sql
CREATE TABLE tutorial_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Module identification
  track_id VARCHAR(50) NOT NULL, -- 'foundations', 'candlesticks', 'technical_analysis'
  module_id VARCHAR(50) NOT NULL, -- '2.1', '2.2', etc.
  
  -- Section completion
  learn_it_complete BOOLEAN DEFAULT FALSE,
  learn_it_completed_at TIMESTAMPTZ,
  
  see_it_complete BOOLEAN DEFAULT FALSE,
  see_it_completed_at TIMESTAMPTZ,
  
  play_it_complete BOOLEAN DEFAULT FALSE,
  play_it_completed_at TIMESTAMPTZ,
  play_it_best_score INTEGER, -- percentage or money depending on mode
  play_it_attempts INTEGER DEFAULT 0,
  
  master_it_complete BOOLEAN DEFAULT FALSE,
  master_it_completed_at TIMESTAMPTZ,
  master_it_best_score INTEGER,
  
  -- Overall
  module_complete BOOLEAN DEFAULT FALSE,
  module_completed_at TIMESTAMPTZ,
  
  -- XP tracking
  xp_earned INTEGER DEFAULT 0,
  
  -- Timestamps
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id, track_id, module_id)
);

CREATE INDEX idx_tutorial_progress_user ON tutorial_progress(user_id);
CREATE INDEX idx_tutorial_progress_module ON tutorial_progress(track_id, module_id);
```

---

### quiz_attempts

Stores individual quiz/assessment attempts.

```sql
CREATE TABLE quiz_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Quiz identification
  quiz_type VARCHAR(50) NOT NULL, -- 'module_play_it', 'module_master_it', 'standalone_quiz'
  quiz_id VARCHAR(100) NOT NULL, -- module_id or quiz_id
  
  -- Mode
  assessment_mode VARCHAR(20) NOT NULL, -- 'game' or 'professional'
  
  -- Results
  questions_total INTEGER NOT NULL,
  questions_correct INTEGER NOT NULL,
  percentage_score DECIMAL(5,2) NOT NULL,
  
  -- Game mode specifics
  money_earned INTEGER, -- virtual dollars
  money_lost INTEGER,
  bonuses JSONB, -- {"streak": 200, "speed": 150}
  total_money INTEGER,
  
  -- Timing
  time_allowed_seconds INTEGER,
  time_taken_seconds INTEGER,
  
  -- Pass/fail
  passed BOOLEAN NOT NULL,
  pass_threshold INTEGER NOT NULL, -- percentage or money required
  
  -- XP earned
  xp_earned INTEGER NOT NULL DEFAULT 0,
  
  -- Timestamps
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  -- Detailed answers (optional, for review)
  answers_detail JSONB -- [{"q": "q1", "given": "A", "correct": "B", "is_correct": false}, ...]
);

CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_id);
CREATE INDEX idx_quiz_attempts_quiz ON quiz_attempts(quiz_type, quiz_id);
CREATE INDEX idx_quiz_attempts_date ON quiz_attempts(completed_at);
```

---

### backtest_results

Stores backtest results for leaderboard and gate evaluation.

```sql
CREATE TABLE backtest_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Strategy info
  strategy_id UUID, -- if linked to a saved strategy
  strategy_name VARCHAR(200),
  
  -- Configuration
  assets JSONB NOT NULL, -- ["BTC", "ETH"]
  timeframe VARCHAR(20) NOT NULL, -- "1h", "15m"
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  duration_days INTEGER NOT NULL,
  indicators JSONB, -- ["RSI", "MACD"]
  
  -- Results
  total_return DECIMAL(10,4) NOT NULL, -- percentage
  hodl_return DECIMAL(10,4), -- for comparison
  return_vs_hodl DECIMAL(10,4), -- total_return - hodl_return
  
  sharpe_ratio DECIMAL(6,4),
  sortino_ratio DECIMAL(6,4),
  max_drawdown DECIMAL(6,4),
  win_rate DECIMAL(5,2),
  
  total_trades INTEGER,
  winning_trades INTEGER,
  losing_trades INTEGER,
  avg_trade_duration_hours DECIMAL(10,2),
  
  -- Equity curve data (for charts)
  equity_curve JSONB, -- [{date, value}, ...]
  
  -- Leaderboard
  submitted_to_leaderboard BOOLEAN DEFAULT FALSE,
  leaderboard_rank INTEGER,
  submitted_at TIMESTAMPTZ,
  
  -- Validation
  is_validated BOOLEAN DEFAULT FALSE,
  validation_hash VARCHAR(64), -- for reproducibility check
  
  -- XP tracking
  xp_earned INTEGER DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_backtest_results_user ON backtest_results(user_id);
CREATE INDEX idx_backtest_results_return ON backtest_results(total_return DESC);
CREATE INDEX idx_backtest_results_leaderboard ON backtest_results(submitted_to_leaderboard, total_return DESC);
```

---

### paper_trades

Stores paper trading history.

```sql
CREATE TABLE paper_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Trade details
  asset VARCHAR(20) NOT NULL,
  side VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
  entry_price DECIMAL(20,8) NOT NULL,
  exit_price DECIMAL(20,8),
  quantity DECIMAL(20,8) NOT NULL,
  
  -- P&L
  pnl_absolute DECIMAL(20,8),
  pnl_percentage DECIMAL(10,4),
  is_profitable BOOLEAN,
  
  -- Status
  status VARCHAR(20) NOT NULL, -- 'open', 'closed', 'cancelled'
  
  -- Strategy link (optional)
  strategy_id UUID,
  strategy_name VARCHAR(200),
  
  -- Timestamps
  opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at TIMESTAMPTZ,
  
  -- XP
  xp_earned INTEGER DEFAULT 0
);

CREATE INDEX idx_paper_trades_user ON paper_trades(user_id);
CREATE INDEX idx_paper_trades_status ON paper_trades(user_id, status);
CREATE INDEX idx_paper_trades_date ON paper_trades(opened_at);
```

---

### achievements

Stores earned achievements/badges.

```sql
CREATE TABLE achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  achievement_id VARCHAR(100) NOT NULL, -- 'first_backtest', 'top_100', etc.
  achievement_name VARCHAR(200) NOT NULL,
  achievement_category VARCHAR(50), -- 'tutorial', 'backtest', 'leaderboard', 'streak'
  
  -- Badge info
  badge_icon VARCHAR(50), -- emoji or icon key
  badge_rarity VARCHAR(20), -- 'common', 'rare', 'epic', 'legendary'
  
  -- Reward
  xp_reward INTEGER DEFAULT 0,
  
  -- Timestamps
  earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_achievements_user ON achievements(user_id);
CREATE INDEX idx_achievements_category ON achievements(achievement_category);
```

---

### daily_challenges

Tracks daily challenge completion.

```sql
CREATE TABLE daily_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Challenge definition
  challenge_date DATE NOT NULL,
  challenge_id VARCHAR(100) NOT NULL,
  challenge_text TEXT NOT NULL,
  challenge_type VARCHAR(50) NOT NULL, -- 'backtest', 'paper_trade', 'tutorial'
  challenge_requirements JSONB NOT NULL,
  xp_reward INTEGER NOT NULL,
  
  -- Created for scheduling
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(challenge_date)
);

CREATE TABLE daily_challenge_completions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  challenge_id UUID NOT NULL REFERENCES daily_challenges(id),
  
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  xp_earned INTEGER NOT NULL,
  
  UNIQUE(user_id, challenge_id)
);

CREATE INDEX idx_daily_challenges_date ON daily_challenges(challenge_date);
CREATE INDEX idx_daily_completions_user ON daily_challenge_completions(user_id);
```

---

### gauntlet_progress

Tracks progress through The Gauntlet (7-challenge series).

```sql
CREATE TABLE gauntlet_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Challenge tracking (1-7)
  challenge_1_complete BOOLEAN DEFAULT FALSE,
  challenge_1_completed_at TIMESTAMPTZ,
  
  challenge_2_complete BOOLEAN DEFAULT FALSE,
  challenge_2_completed_at TIMESTAMPTZ,
  
  challenge_3_complete BOOLEAN DEFAULT FALSE,
  challenge_3_completed_at TIMESTAMPTZ,
  
  challenge_4_complete BOOLEAN DEFAULT FALSE,
  challenge_4_completed_at TIMESTAMPTZ,
  
  challenge_5_complete BOOLEAN DEFAULT FALSE,
  challenge_5_completed_at TIMESTAMPTZ,
  
  challenge_6_complete BOOLEAN DEFAULT FALSE,
  challenge_6_completed_at TIMESTAMPTZ,
  
  challenge_7_complete BOOLEAN DEFAULT FALSE,
  challenge_7_completed_at TIMESTAMPTZ,
  
  -- Overall
  gauntlet_complete BOOLEAN DEFAULT FALSE,
  gauntlet_completed_at TIMESTAMPTZ,
  
  -- Timestamps
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(user_id)
);

CREATE INDEX idx_gauntlet_user ON gauntlet_progress(user_id);
```

---

### xp_transactions

Audit log of all XP earned.

```sql
CREATE TABLE xp_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- XP details
  xp_amount INTEGER NOT NULL,
  xp_source VARCHAR(50) NOT NULL, -- 'tutorial', 'backtest', 'paper_trade', 'achievement', 'daily'
  source_id VARCHAR(100), -- specific ID of what earned the XP
  description TEXT,
  
  -- Multipliers applied
  multiplier DECIMAL(3,2) DEFAULT 1.0,
  multiplier_reason VARCHAR(100), -- 'first_of_day', 'streak_7_days'
  
  -- Balance after
  balance_after INTEGER NOT NULL,
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_xp_transactions_user ON xp_transactions(user_id);
CREATE INDEX idx_xp_transactions_date ON xp_transactions(created_at);
```

---

### leaderboard_snapshots

For historical leaderboard data.

```sql
CREATE TABLE leaderboard_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Snapshot info
  snapshot_date DATE NOT NULL,
  metric VARCHAR(50) NOT NULL, -- 'total_return', 'sharpe_ratio', etc.
  period_days INTEGER NOT NULL, -- 30, 90, 365
  
  -- Rankings (top 100)
  rankings JSONB NOT NULL, -- [{rank, strategy_id, user_id, value}, ...]
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(snapshot_date, metric, period_days)
);

CREATE INDEX idx_leaderboard_snapshots_date ON leaderboard_snapshots(snapshot_date);
```

---

## VIEWS

### user_complete_status

Aggregated view of user's complete game state.

```sql
CREATE VIEW user_complete_status AS
SELECT 
  up.user_id,
  up.current_tier,
  up.current_xp,
  up.lifetime_xp,
  up.prestige_count,
  up.assessment_mode,
  
  -- Unlock counts
  (SELECT COUNT(*) FROM armory_unlocks au WHERE au.user_id = up.user_id AND au.unlock_type = 'asset') as assets_unlocked,
  (SELECT COUNT(*) FROM armory_unlocks au WHERE au.user_id = up.user_id AND au.unlock_type = 'timeframe') as timeframes_unlocked,
  (SELECT COUNT(*) FROM armory_unlocks au WHERE au.user_id = up.user_id AND au.unlock_type = 'indicator') as indicators_unlocked,
  
  -- Tutorial progress
  (SELECT COUNT(*) FROM tutorial_progress tp WHERE tp.user_id = up.user_id AND tp.module_complete = TRUE) as tutorials_completed,
  
  -- Backtest stats
  (SELECT COUNT(*) FROM backtest_results br WHERE br.user_id = up.user_id) as total_backtests,
  (SELECT COUNT(*) FROM backtest_results br WHERE br.user_id = up.user_id AND br.total_return > 0) as profitable_backtests,
  (SELECT MAX(total_return) FROM backtest_results br WHERE br.user_id = up.user_id) as best_return,
  
  -- Paper trading stats
  (SELECT COUNT(*) FROM paper_trades pt WHERE pt.user_id = up.user_id AND pt.status = 'closed') as paper_trades_closed,
  (SELECT SUM(pnl_absolute) FROM paper_trades pt WHERE pt.user_id = up.user_id AND pt.status = 'closed') as paper_total_pnl,
  
  -- Achievement count
  (SELECT COUNT(*) FROM achievements a WHERE a.user_id = up.user_id) as achievements_earned
  
FROM users_progression up;
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE PROGRESSION DATABASE

Context:
- This is the complete state storage for the game system
- Uses Supabase/PostgreSQL
- Must support efficient queries for UI display
- Must support gate evaluation queries

Requirements:
1. Create all tables as specified
2. Set up proper indexes for performance
3. Implement Row Level Security (RLS) for user data
4. Create the aggregated views
5. Set up triggers for:
   - Auto-updating updated_at timestamps
   - Auto-calculating derived fields
6. Create migration files

RLS Policies needed:
- Users can only see/modify their own data
- Leaderboard data is public read
- Daily challenges are public read

Triggers needed:
- On tier change: check if unlocks should be granted
- On XP change: check if tier should advance
- On backtest complete: update gate progress
- On paper trade close: update gate progress

Deliverables:
- Migration files for all tables
- RLS policies
- Trigger functions
- View definitions
- Seed data for testing

Reference:
- See 04-armory-tiers.md for tier thresholds
- See 05-armory-gates.md for gate requirements
- See 12-api-endpoints.md for query patterns
```

---

## ACCEPTANCE CRITERIA

- [ ] All tables created with proper constraints
- [ ] Indexes support common query patterns
- [ ] RLS policies protect user data
- [ ] Views provide convenient aggregations
- [ ] Triggers maintain data consistency
- [ ] Foreign keys maintain referential integrity
- [ ] Migration files are versioned and reversible

---

*Related Documents:*
- `04-armory-tiers.md` - Tier requirements
- `05-armory-gates.md` - Gate logic
- `12-api-endpoints.md` - API layer
