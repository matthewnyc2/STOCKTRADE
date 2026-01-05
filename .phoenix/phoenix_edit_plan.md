# Phoenix Edit Plan - StockTrade Platform Refactoring

**Generated**: 2026-01-03
**Objective**: Finalize StockTrade platform by fixing architectural debt, implementing missing logic, gathering necessary market data, and ensuring 100% test passing rates.

## Executive Summary

This Phoenix operation addresses critical architectural debt in the StockTrade crypto trading platform. The refactoring targets 7 major areas:

1. **God Modules** - Split monolithic files into maintainable packages
2. **Fat Routers** - Extract business logic and Pydantic models from API layer
3. **Component Overload** - Break down large frontend components
4. **Model Layer Consolidation** - Unify dual model layers
5. **Security & CI/CD** - Fix vulnerabilities and pipeline issues
6. **Feature Implementation** - Complete Whale Tracking and Historical Data Manager
7. **Test Infrastructure** - Ensure all tests pass

---

## Current State Analysis

### 1. God Modules

| File | Lines | Issue | Impact |
|------|-------|-------|--------|
| `services/ml_factory.py` | 1,550 | Custom NumPy LSTM + training + features + orchestration | Unmaintainable, high coupling |
| `frontend/src/types/api.ts` | 1,446 | All TypeScript definitions in one file | Navigation issues, coupling |
| `api/shadow.py` | 1,297 | Analytics + business logic + models | Violates single responsibility |
| `api/strategies.py` | 1,122 | Strategy lifecycle + mapping + models | Violates layered architecture |
| `frontend/src/components/dashboard/ModernCharts.tsx` | 1,186 | 5 chart components + shared code | Exceeds 300-line limit |
| `frontend/src/components/dashboard/ModernWidgets.tsx` | 1,154 | 9 widget components + shared code | Exceeds 300-line limit |

### 2. Technical Debt

- **Dual Model Layers**: SQLAlchemy models (`database/models/`) and Pydantic models (`models/`) with duplication
- **Fat Routers**: Business logic and Pydantic models defined inline in API routes
- **Enum Duplication**: Same enums defined in both layers
- **Manual Mapping**: `model_to_strategy` functions instead of Pydantic's `from_attributes=True`

### 3. Security Issues

- **Backend**: `require_admin` works but uses hardcoded default SECRET_KEY
- **Frontend**: Admin pages have NO route guard - accessible to any user
- **CI/CD**: Python 3.14 (doesn't exist), `continue-on-error: true` on all critical steps

### 4. Feature Gaps

- **Whale Tracking**: BFS exists for connectivity but not behavioral patterns
- **Historical Data**: Gap detection is batch-only, no active monitoring
- **Exchange Support**: Only Binance has OHLCV; CoinGecko/Kraken lack historical candles

### 5. Test Failures

- **Backend**: 772 tests collected, failures in deployment (docker-compose) and admin (404s)
- **Frontend**: Toolchain conflicts (Vitest vs Jest), syntax errors, environment issues

---

## Desired State

### 1. God Modules Refactored

```
services/ml_factory.py (1,550 lines)
    ↓
services/ml/
    ├── models.py          (LSTMModel, LSTMLayer)
    ├── engine.py          (TrainingEngine, TrainingProgress)
    ├── features.py        (FeatureEngine)
    ├── factory.py         (MLFactory orchestration)
    └── __init__.py

frontend/src/types/api.ts (1,446 lines)
    ↓
frontend/src/types/
    ├── enums.ts           (All enums)
    ├── base.ts            (ApiError, ApiResponse)
    ├── strategies.ts       (Strategy, Signal, Backtest)
    ├── shadow.ts          (Arbitrage, Constellation, Liquidity)
    ├── whales.ts          (Whale, Activity, Ranking)
    ├── ml.ts              (MLModel, Training, Prediction)
    ├── ai.ts              (AIReasoning, Analysis)
    ├── market.ts          (Price, Coin, Exchange)
    ├── portfolio.ts       (Portfolio, Position, Metrics)
    ├── onboarding.ts      (OnboardingData, APIKeys)
    └── api.ts (barrel)   (Re-exports all)
```

### 2. Fat Routers Cleaned

```
api/strategies.py (1,122 lines)
    ↓
models/strategy.py (extracted inline Pydantic models)
services/strategy_manager.py (enhanced with creation logic)
api/strategies.py (~300 lines, routing only)

api/shadow.py (1,297 lines)
    ↓
models/arbitrage.py (extracted inline Pydantic models)
services/liquidity_hunter.py (enhanced with analytics logic)
api/shadow.py (~300 lines, routing only)
```

### 3. Components Split

```
frontend/src/components/dashboard/ModernCharts.tsx (1,186 lines)
    ↓
frontend/src/components/dashboard/charts/
    ├── types.ts
    ├── constants.ts
    ├── utils.ts
    ├── PerformanceChart.tsx
    ├── MetricGauge.tsx
    ├── ProgressBar.tsx
    ├── Sparkline.tsx
    ├── DonutChart.tsx
    └── index.ts

frontend/src/components/dashboard/ModernWidgets.tsx (1,154 lines)
    ↓
frontend/src/components/dashboard/widgets/
    ├── types.ts
    ├── utils.ts
    ├── animations.ts
    ├── MetricCard.tsx
    ├── PortfolioSummaryCard.tsx
    ├── PerformanceCard.tsx
    ├── ActivityFeed.tsx
    ├── ActivityItem.tsx
    ├── QuickActions.tsx
    ├── Layout.tsx
    └── index.ts
```

### 4. Model Layers Consolidated

- **Persistence**: `database/models/` for SQLAlchemy only (repositories use this)
- **Domain**: `models/` for Pydantic only (services and API use this)
- **Conversion**: Pydantic models use `from_attributes = True` for automatic ORM mapping
- **Enums**: Defined once in `models/`, imported by `database/models/`

### 5. Security & CI/CD Fixed

- **Admin Guard**: `ProtectedRoute` wraps all admin pages
- **Secret Key**: Mandatory environment variable, no defaults
- **CI/CD**: Python 3.12, `continue-on-error` removed from critical steps
- **Artifacts**: Tracked `__pycache__` and junk files removed

### 6. Features Implemented

- **Whale Tracking**: BFS for behavioral pattern detection (Accumulate → Wash → Manipulate)
- **Historical Data**: Active gap monitoring background task, precise backfill with startTime/endTime
- **Exchange Support**: CoinGecko and Kraken OHLCV implementations

### 7. Tests Passing

- **Backend**: All 772 tests pass
- **Frontend**: All tests pass (toolchain resolved)
- **Linting**: `ruff check .` and `npm run lint` clean

---

## Risk Assessment

### High Risk Areas

1. **Breaking Imports** - 73 files import from `frontend/src/types/api.ts`
2. **Fat Router Logic** - Complex business logic in `api/strategies.py` may have dependencies
3. **Dual Model Consistency** - Manual mapping functions may have edge cases
4. **Admin Routes 404** - Tests expect `/api/admin/*` endpoints that may not exist

### Medium Risk Areas

1. **ML Factory Threading** - ThreadPoolExecutor state management
2. **Chart Component Props** - Shared dependencies may break
3. **Drawdown Logic** - Needs verification after refactor
4. **Test Infrastructure** - Frontend toolchain conflicts need resolution

### Low Risk Areas

1. **Frontend Components** - Well-encapsulated, easier to split
2. **CI/CD Updates** - Configuration-only changes
3. **Security Guards** - Defensive programming, low impact
4. **Enum Centralization** - Pure refactoring, no logic change

---

## Success Criteria

- [ ] All backend tests (`pytest tests/`) pass
- [ ] All frontend tests (`npm test` and `npm run test:e2e`) pass
- [ ] Linting clean: `ruff check .` and `npm run lint`
- [ ] No functionality added beyond these requirements
- [ ] Output: `COMPLETION_ACHIEVED`

---

## Architect Decomposition

The refactoring will be decomposed into **7 Architects**, each owning a major feature area:

1. **Architect 1**: Split `services/ml_factory.py` into `services/ml/` package
2. **Architect 2**: Split `frontend/src/types/api.ts` into domain-specific files
3. **Architect 3**: Refactor fat routers (`api/shadow.py`, `api/strategies.py`)
4. **Architect 4**: Split `ModernCharts.tsx` and `ModernWidgets.tsx`
5. **Architect 5**: Consolidate dual model layers and fix drawdown logic
6. **Architect 6**: Implement security fixes and CI/CD cleanup
7. **Architect 7**: Implement Whale Tracking and Historical Data Manager

Each Architect will spawn Conductors to orchestrate Test Writer → Code Writer pairs for each atomic task.

---

## Workflow Notes

- **TDD**: All changes will be implemented test-first (or test-update-first for existing code)
- **Regression Testing**: Each Conductor will run relevant tests after every edit
- **Pattern Compliance**: All refactoring will follow existing project patterns (no new conventions)
- **Minimal Changes**: Only make changes necessary for the stated requirements
- **No Scope Creep**: Do not add "helpful" features or optimizations
