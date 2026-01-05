# 09 - LEARN-PLAY SYSTEM: THE DUAL MODE MECHANICS

## Overview

The Learn-Play system is the core educational game mechanic. Every educational interaction has two presentation modes that share the same underlying logic but feel completely different to the user.

---

## THE DUAL MODE CONCEPT

### Why Two Modes?

Different users have different motivations:
- **Gamers** want to WIN, EARN, COMPETE
- **Professionals** want to LEARN, PASS, CERTIFY

Same content, different emotional wrapper.

### The Modes

| Aspect | GAME MODE 🎮 | PROFESSIONAL MODE 📊 |
|--------|--------------|----------------------|
| **Tone** | Playful, competitive | Serious, educational |
| **Progress metric** | Virtual dollars earned | Percentage score |
| **Correct answer** | "You earned $500!" | "Correct! +10 points" |
| **Wrong answer** | "You lost $200!" | "Incorrect. The answer was..." |
| **Completion** | "You made $2,450!" | "Score: 87%" |
| **Unlock text** | "Earn $2,000 to advance" | "Score 70% to pass" |
| **Failure text** | "Not enough profit. Try again?" | "Below passing. Review and retry?" |
| **Leaderboard** | "Top Earners" | "Top Scores" |

---

## GAME MODE: THE EXPERIENCE

### The Metaphor

In game mode, you're a **trader making decisions**. Every correct answer is a profitable trade. Every wrong answer is a loss. The goal is to make money.

### UI Treatment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   💰 YOUR WALLET: $1,750                    🎯 GOAL: $2,000            │
│   ═══════════════════════════════════════════════════════════════════  │
│                                                                         │
│   QUESTION 7 of 10                                                      │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   What does this candle pattern indicate?                       │  │
│   │                                                                 │  │
│   │              [Candle Image]                                     │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   PLACE YOUR BET: This question is worth $250                          │
│                                                                         │
│   [ A. Bullish reversal ]                                              │
│   [ B. Bearish reversal ]                                              │
│   [ C. Continuation ]                                                  │
│   [ D. Indecision ]                                                    │
│                                                                         │
│   ⏱️ 0:08 remaining                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Correct Answer Response (Game Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          💰 PROFITABLE TRADE!                          │
│                                                                         │
│                              +$250                                      │
│                                                                         │
│   (Animated coins falling / stacking)                                  │
│                                                                         │
│   The hammer pattern at the bottom of a downtrend often                │
│   signals a bullish reversal.                                          │
│                                                                         │
│   💰 WALLET: $1,750 → $2,000                                           │
│                                                                         │
│                         [ NEXT TRADE → ]                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Wrong Answer Response (Game Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                           📉 TRADE LOSS                                │
│                                                                         │
│                              -$150                                      │
│                                                                         │
│   (Animated red flash / coins dropping)                                │
│                                                                         │
│   The correct answer was: A. Bullish reversal                          │
│                                                                         │
│   The hammer pattern at the bottom of a downtrend often                │
│   signals a bullish reversal.                                          │
│                                                                         │
│   💰 WALLET: $1,750 → $1,600                                           │
│                                                                         │
│                         [ NEXT TRADE → ]                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Complete (Game Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        🏆 TRADING SESSION COMPLETE!                    │
│                                                                         │
│                     TOTAL PROFIT: $2,450                               │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   Trades Won: 8/10              Win Rate: 80%                  │  │
│   │   Best Streak: 5 in a row       Bonus: +$200                   │  │
│   │   Time Bonus: Completed fast    Bonus: +$150                   │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│                     ✅ MODULE PASSED (Goal: $2,000)                    │
│                                                                         │
│                +150 XP earned       Next module unlocked!              │
│                                                                         │
│   [ TRY FOR HIGHER SCORE ]    [ CONTINUE TO NEXT MODULE → ]           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PROFESSIONAL MODE: THE EXPERIENCE

### The Metaphor

In professional mode, you're a **student taking an assessment**. Every correct answer builds your score. The goal is to demonstrate competency.

### UI Treatment

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   📊 SCORE: 70%                              ✓ PASS: 70%               │
│   ═══════════════════════════════════════════════════════════════════  │
│                                                                         │
│   QUESTION 7 of 10                                                      │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   What does this candle pattern indicate?                       │  │
│   │                                                                 │  │
│   │              [Candle Image]                                     │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Select the best answer:                                              │
│                                                                         │
│   ○ A. Bullish reversal                                                │
│   ○ B. Bearish reversal                                                │
│   ○ C. Continuation                                                    │
│   ○ D. Indecision                                                      │
│                                                                         │
│   ⏱️ 0:08 remaining (optional timer)                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Correct Answer Response (Professional Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            ✓ CORRECT                                   │
│                                                                         │
│   The hammer pattern at the bottom of a downtrend often                │
│   signals a bullish reversal.                                          │
│                                                                         │
│   📊 SCORE: 70% → 80%                                                  │
│                                                                         │
│                         [ NEXT QUESTION → ]                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Wrong Answer Response (Professional Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            ✗ INCORRECT                                 │
│                                                                         │
│   The correct answer was: A. Bullish reversal                          │
│                                                                         │
│   The hammer pattern at the bottom of a downtrend often                │
│   signals a bullish reversal.                                          │
│                                                                         │
│   📊 SCORE: 70% (unchanged - wrong answers don't subtract)             │
│                                                                         │
│                         [ NEXT QUESTION → ]                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Complete (Professional Mode)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        📊 ASSESSMENT COMPLETE                          │
│                                                                         │
│                        FINAL SCORE: 80%                                │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   Correct: 8/10                                                │  │
│   │   Incorrect: 2/10                                              │  │
│   │                                                                 │  │
│   │   Review missed questions?  [YES]  [NO]                        │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│                     ✅ PASSED (Requirement: 70%)                       │
│                                                                         │
│                +150 XP earned       Next module unlocked!              │
│                                                                         │
│   [ RETAKE FOR HIGHER SCORE ]    [ CONTINUE TO NEXT MODULE → ]        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## THE UNDERLYING ENGINE

Both modes share the same core logic:

```typescript
interface AssessmentEngine {
  // Same for both modes
  questions: Question[]
  currentIndex: number
  answers: Answer[]
  startTime: Date
  
  // Methods
  submitAnswer(questionId: string, answer: any): AnswerResult
  calculateScore(): ScoreResult
  checkPassCondition(): boolean
  getNextQuestion(): Question | null
}

interface AnswerResult {
  correct: boolean
  explanation: string
  
  // Mode-specific display values
  gameModeDisplay: {
    moneyChange: number  // +250 or -150
    newTotal: number
    animation: 'coins_up' | 'coins_down'
  }
  
  professionalModeDisplay: {
    scoreChange: number  // +10 or 0
    newPercentage: number
    animation: 'check' | 'x'
  }
}

interface ScoreResult {
  correctCount: number
  totalQuestions: number
  percentage: number
  
  // Game mode
  totalMoney: number
  bonuses: Bonus[]
  
  // Professional mode
  score: number
  
  // Shared
  passed: boolean
  xpEarned: number
}
```

---

## CONVERSION FORMULAS

### Money Calculation (Game Mode)

```typescript
function calculateMoney(question: Question, correct: boolean): number {
  const baseValue = question.money  // e.g., 250
  
  if (correct) {
    // Full value for correct
    return baseValue
  } else {
    // Lose partial value for wrong (less punishing)
    return -Math.floor(baseValue * 0.6)  // Lose 60% of question value
  }
}

function calculateBonuses(session: Session): Bonus[] {
  const bonuses: Bonus[] = []
  
  // Streak bonus: 3+ correct in a row
  if (session.longestStreak >= 3) {
    bonuses.push({
      name: 'Hot Streak',
      amount: session.longestStreak * 50
    })
  }
  
  // Time bonus: finish under par time
  if (session.timeElapsed < session.parTime) {
    bonuses.push({
      name: 'Speed Bonus',
      amount: 150
    })
  }
  
  // Perfect bonus: 100% correct
  if (session.correctCount === session.totalQuestions) {
    bonuses.push({
      name: 'Perfect Trade',
      amount: 500
    })
  }
  
  return bonuses
}
```

### Score Calculation (Professional Mode)

```typescript
function calculateScore(session: Session): number {
  return Math.round((session.correctCount / session.totalQuestions) * 100)
}

// Note: Professional mode doesn't subtract for wrong answers
// It's purely percentage-based
```

### Pass Threshold Equivalence

For any module to feel "fair" in both modes, the pass thresholds must be calibrated:

```typescript
// Example: 10 questions, each worth $250
// Game mode goal: $2,000
// This means: need 8 correct (8 × 250 = 2000) with no losses
// Or: 9 correct with 1 wrong (9 × 250 - 150 = 2100)

// Professional mode: 70% pass
// This means: need 7 correct

// These are roughly equivalent difficulty:
// - Game mode rewards perfect play with bonuses
// - Professional mode is more forgiving (no penalty for wrong)
```

---

## ADAPTIVE DIFFICULTY

### Within a Module

Questions can have varying difficulty and rewards:

```typescript
interface Question {
  difficulty: 'easy' | 'medium' | 'hard'
  
  // Game mode: harder = more money
  money: {
    easy: 100,
    medium: 250,
    hard: 500
  }
  
  // Professional mode: all worth same
  points: 1  // Always 1 point
  
  // But harder questions might give more XP
  xp: {
    easy: 5,
    medium: 10,
    hard: 20
  }
}
```

### Dynamic Difficulty Adjustment (Optional)

```typescript
function selectNextQuestion(session: Session): Question {
  const recentPerformance = session.answers.slice(-5)
  const recentAccuracy = recentPerformance.filter(a => a.correct).length / 5
  
  if (recentAccuracy > 0.8) {
    // Player is doing well, increase difficulty
    return selectFromPool('hard')
  } else if (recentAccuracy < 0.4) {
    // Player is struggling, decrease difficulty
    return selectFromPool('easy')
  } else {
    return selectFromPool('medium')
  }
}
```

---

## MODE SWITCHING

Users can switch modes in settings:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   ASSESSMENT MODE                                                       │
│                                                                         │
│   How would you like to experience assessments?                         │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                                                                 │  │
│   │   ● GAME MODE 🎮                                               │  │
│   │     Earn virtual money for correct answers.                    │  │
│   │     Feel like a trader making profitable decisions.            │  │
│   │                                                                 │  │
│   │   ○ PROFESSIONAL MODE 📊                                       │  │
│   │     Traditional quiz with percentage scores.                   │  │
│   │     Focused on learning and certification.                     │  │
│   │                                                                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   Note: Your progress is the same either way.                          │
│   You can switch modes at any time.                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## LEADERBOARDS (OPTIONAL)

Both modes can have leaderboards:

### Game Mode Leaderboard

```
TOP EARNERS: Single Candle Patterns

1. TraderJoe        $4,250 🏆
2. CryptoQueen      $3,900
3. YOU              $2,450 ← Your best
4. ChartMaster      $2,400
5. NewbieTrader     $2,100
```

### Professional Mode Leaderboard

```
TOP SCORES: Single Candle Patterns

1. StudyPro         98% 🏆
2. DiligentDan      95%
3. YOU              87% ← Your best
4. QuizWhiz         85%
5. Learner101       82%
```

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE LEARN-PLAY DUAL MODE SYSTEM

Context:
- Every assessment has two modes: Game and Professional
- Same questions, different presentation
- Game mode: earn virtual money
- Professional mode: score percentage
- User can switch modes in settings

Requirements:
1. Create AssessmentEngine that handles both modes
2. Build UI components for each mode:
   - GameModeAssessment
   - ProfessionalModeAssessment
3. Implement score/money calculation
4. Create animations for each mode
5. Build pass/fail determination
6. Handle mode switching
7. Persist user's mode preference

Core components:
- AssessmentEngine (shared logic)
- QuestionRenderer (mode-agnostic)
- AnswerFeedback (mode-specific)
- ScoreSummary (mode-specific)
- ModeSwitch (settings)

State management:
- Current mode (from user settings)
- Assessment state (questions, answers, scores)
- Pass/fail status

Animations needed:
- Coins falling (game mode correct)
- Coins dropping (game mode wrong)
- Checkmark appear (professional correct)
- X appear (professional wrong)
- Money counter increment
- Percentage counter increment

Deliverables:
- assessmentEngine.ts
- GameModeAssessment component
- ProfessionalModeAssessment component
- AnswerAnimation component
- ScoreSummary component
- useAssessmentMode hook

Reference:
- See 07-tutorial-overview.md for tutorial structure
- See 08-candles-curriculum.md for content format
- See 11-progression-database.md for saving progress
```

---

## ACCEPTANCE CRITERIA

- [ ] Both modes use the same question data
- [ ] Game mode shows money earned/lost
- [ ] Professional mode shows percentage score
- [ ] Animations match the mode
- [ ] Pass thresholds are equivalent
- [ ] User can switch modes in settings
- [ ] Mode preference persists
- [ ] Progress is shared between modes
- [ ] Leaderboards show mode-appropriate metrics
- [ ] XP earned is consistent regardless of mode

---

*Related Documents:*
- `07-tutorial-overview.md` - Tutorial structure
- `08-candles-curriculum.md` - Content format
- `10-leaderboard.md` - Leaderboard system
- `11-progression-database.md` - State storage
