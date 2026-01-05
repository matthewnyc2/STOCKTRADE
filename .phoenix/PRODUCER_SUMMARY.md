# Phoenix Producer Summary - StockTrade Platform Refactoring

**Generated**: 2026-01-03
**Status**: Producer Phase Complete, Ready to Spawn Architects
**Estimated Duration**: 5-10 days for full completion

---

## Executive Summary

The Producer phase has completed:
- ✅ Codebase exploration (8 parallel explore agents)
- ✅ Delta analysis (current vs desired state documented)
- ✅ Risk assessment (9 major risks identified with mitigation)
- ✅ Architect decomposition (7 features defined)

**Findings**:
- 6 "God Modules" totaling ~7,300 lines
- 73 frontend files importing from monolithic type file
- Pre-existing test failures (deployment, admin, frontend toolchain)
- 9 critical security/CI/CD issues
- Missing features in Whale Tracking and Historical Data Manager

**Critical Path**: Fix test infrastructure → Refactor → Verify 100% test pass rate

---

## Architecture Overview

### Current Technical Debt

| Category | Files | Lines | Issue |
|-----------|--------|-------|-------|
| **God Modules** | 6 | 7,300+ | Monolithic, unmaintainable |
| **Fat Routers** | 2 | 2,419 | Business logic in API layer |
| **Component Overload** | 2 | 2,340 | Exceeds 300-line limit |
| **Dual Model Layers** | ~20 | ~2,000 | Duplication, manual mapping |
| **Security/CI/CD Issues** | 5+ | N/A | Vulnerabilities, invalid config |

### Pre-Existing Failures

**Backend Tests** (772 tests collected):
- ❌ Deployment: `KeyError: 'backend'` (docker-compose mismatch)
- ❌ Admin: 404 Not Found (routes not mounted)
- ✅ Other tests: Status unknown (need baseline)

**Frontend Tests** (73 test files):
- ❌ Toolchain conflict: Vitest vs Jest
- ❌ Syntax errors: `axe-core.test.ts`, `auth.ts`
- ❌ Environment: TestEnvironment constructor error
- ❌ No tests can run currently

---

## Architect Decomposition

### 7 Architects with Specific Responsibilities

| Architect | Feature | Tasks | Complexity |
|-----------|----------|--------|------------|
| **1** | ML Factory Refactoring | 8 tasks | MEDIUM |
| **2** | Frontend Types Split | 12 tasks | HIGH |
| **3** | Fat Router Cleanup | 10 tasks | HIGH |
| **4** | Component Split | 10 tasks | MEDIUM |
| **5** | Model Consolidation | 8 tasks | MEDIUM |
| **6** | Security & CI/CD | 8 tasks | LOW |
| **7** | Feature Implementation | 8 tasks | HIGH |
| **Final** | Verification | 5 tasks | N/A |

**Total**: 69 tasks across 7 architects

---

## Detailed Architect Briefs

### Architect 1: ML Factory Refactoring

**Objective**: Split `services/ml_factory.py` (1,550 lines) → `services/ml/` package

**Tasks**:
1. Create package structure (`services/ml/`)
2. Extract models (`LSTMLayer`, `LSTMModel` → `models.py`)
3. Extract engine (`TrainingEngine` → `engine.py`)
4. Extract features (`FeatureEngine` → `features.py`)
5. Extract factory (`MLFactory` → `factory.py`)
6. Update package init
7. Update imports across codebase
8. Delete original file

**Risk**: Threading safety, import path breaks

**Estimated Time**: 4-6 hours

---

### Architect 2: Frontend Types Split

**Objective**: Split `frontend/src/types/api.ts` (1,446 lines) → 10 domain files

**Tasks**:
1. Create enums.ts (StrategyType, SignalType, etc.)
2. Create base.ts (ApiError, ApiResponse)
3. Create strategies.ts (Strategy, Signal, Backtest)
4. Create shadow.ts (Arbitrage, Constellation, Liquidity)
5. Create whales.ts (Whale, Activity, Ranking)
6. Create ml.ts (MLModel, Training, Prediction)
7. Create ai.ts (AIReasoning, Analysis)
8. Create market.ts (Price, Coin, Exchange)
9. Create portfolio.ts (Portfolio, Position, Metrics)
10. Create onboarding.ts (OnboardingData, APIKeys)
11. Move ApiClient to lib/api-client-base.ts
12. Move ApiEndpoints to constants/endpoints.ts
13. Create barrel file for backward compatibility

**Critical**: Barrel file must maintain all existing exports to prevent breaking 73 importing files

**Risk**: Breaking imports (73 files)

**Estimated Time**: 6-8 hours

---

### Architect 3: Fat Router Cleanup

**Objective**: Extract business logic from `api/strategies.py` and `api/shadow.py`

**Tasks for strategies.py** (1,122 lines):
1. Extract inline Pydantic models to `models/strategy.py`
2. Move `model_to_strategy` to `services/strategy_manager.py`
3. Move `create_from_template` to `services/strategy_manager.py`
4. Move `clone_strategy` to `services/strategy_manager.py`
5. Move `update_layer_weights` to `database/repositories/strategy_layer.py`
6. Clean up router (~300 lines remaining)

**Tasks for shadow.py** (1,297 lines):
1. Extract inline Pydantic models to `models/arbitrage.py`
2. Move `_generate_recommendations` to `services/liquidity_hunter.py`
3. Move sweep probability logic to `services/liquidity_hunter.py`
4. Move round number logic to `services/liquidity_hunter.py`
5. Remove mock data from endpoints
6. Clean up router (~300 lines remaining)

**Risk**: Complex business logic, feature regression

**Estimated Time**: 8-10 hours

---

### Architect 4: Component Split

**Objective**: Split `ModernCharts.tsx` (1,186 lines) and `ModernWidgets.tsx` (1,154 lines)

**Tasks for ModernCharts**:
1. Create charts/ directory structure
2. Extract types.ts (prop interfaces)
3. Extract constants.ts (CHART_COLORS)
4. Extract utils.ts (formatting helpers)
5. Extract PerformanceChart.tsx (~200 lines)
6. Extract MetricGauge.tsx (~170 lines)
7. Extract ProgressBar.tsx (~110 lines)
8. Extract Sparkline.tsx (~130 lines)
9. Extract DonutChart.tsx (~250 lines)
10. Create barrel file (charts/index.ts)

**Tasks for ModernWidgets**:
1. Create widgets/ directory structure
2. Extract types.ts (prop interfaces)
3. Extract utils.ts (trend helpers)
4. Extract animations.ts (Framer Motion variants)
5. Extract MetricCard.tsx (~150 lines)
6. Extract PortfolioSummaryCard.tsx (~160 lines)
7. Extract PerformanceCard.tsx (~110 lines)
8. Extract ActivityFeed.tsx (~120 lines)
9. Extract QuickActions.tsx (~120 lines)
10. Extract Layout.tsx (~70 lines)
11. Create barrel file (widgets/index.ts)

**Risk**: Component prop dependencies, rendering errors

**Estimated Time**: 6-8 hours

---

### Architect 5: Model Consolidation

**Objective**: Unify dual model layers, fix drawdown logic

**Tasks**:
1. Centralize enums (move from database/models/ to models/)
2. Update all DB models to import enums from models/
3. Add `from_attributes = True` to all Pydantic models
4. Replace manual mapping with `.model_validate()`
5. Delete `model_to_strategy` functions
6. Verify type conversions
7. Fix positive drawdown logic (ensure ALWAYS negative)
8. Run comprehensive tests

**Risk**: Data mapping errors, type mismatches

**Estimated Time**: 4-6 hours

---

### Architect 6: Security & CI/CD

**Objective**: Fix vulnerabilities, clean up configuration

**Backend Security**:
1. Remove default SECRET_KEY in `api/auth.py`
2. Add validation (raise error if SECRET_KEY missing in production)
3. Update documentation (.env.example, README)

**Frontend Security**:
1. Import ProtectedRoute in `frontend/src/app/admin/layout.tsx`
2. Wrap children in ProtectedRoute component
3. Test with non-admin user

**CI/CD Cleanup**:
1. Fix Python version: 3.14 → 3.12 in all workflows
2. Remove `continue-on-error: true` from test/lint steps
3. Remove tracked `__pycache__` files
4. Delete artifact files (nul, =1.24.0, C:Users/matt/AppData/Local/)

**Risk**: Breaking changes, security regression

**Estimated Time**: 2-3 hours

---

### Architect 7: Feature Implementation

**Objective**: Complete Whale Tracking and Historical Data Manager

**Whale Tracking Tasks**:
1. Enhance `classify_whale_pattern` with BFS behavioral detection
2. Add multi-step sequence detection (Accumulate → Wash → Manipulate)
3. Update constellation detection with behavioral clustering
4. Add tests for new patterns

**Historical Data Manager Tasks**:
1. Implement `get_ohlcv` for CoinGeckoDataSource
2. Implement `get_ohlcv` for KrakenDataSource
3. Add startTime/endTime parameters to BinanceDataSource.get_ohlcv
4. Create background task for continuous gap detection
5. Implement precise backfill with specific time ranges
6. Add tests for new functionality

**Risk**: Complex algorithms, data accuracy

**Estimated Time**: 8-10 hours

---

### Final Verification

**Objective**: Ensure 100% test pass rate, clean linting

**Tasks**:
1. Fix backend test failures (deployment, admin)
2. Fix frontend test infrastructure (toolchain, syntax errors)
3. Run full backend test suite (pytest tests/)
4. Run full frontend test suite (npm test, npm run test:e2e)
5. Run linters (ruff check ., npm run lint)
6. Verify all architectural changes
7. Final sanity check

**Risk**: Pre-existing failures masking regressions

**Estimated Time**: 4-6 hours

---

## Execution Strategy

### Phase 1: Fix Foundation (CRITICAL FIRST)

**Priority**: HIGHEST
**Duration**: 1-2 days

1. **Fix Test Infrastructure** (Final Verification Architect)
   - Fix frontend toolchain conflict (Vitest vs Jest)
   - Fix syntax errors (axe-core.test.ts, auth.ts)
   - Fix admin route mounting (404 errors)
   - Fix docker-compose service names
   - Get baseline test results

2. **Security & CI/CD** (Architect 6)
   - Quick wins, low risk
   - Fixes CI pipeline
   - Enables automated testing during refactor

**Success Criteria**:
- Frontend tests can run
- Backend tests can run
- CI/CD pipeline works with Python 3.12
- Baseline test results documented

### Phase 2: Backend Refactoring (Architects 1, 3, 5, 7)

**Priority**: HIGH
**Duration**: 3-4 days

Order of execution (dependencies):
1. **Architect 5** (Model Consolidation) - Foundation for other changes
2. **Architect 1** (ML Factory) - Independent
3. **Architect 3** (Fat Routers) - Depends on model consolidation
4. **Architect 7** (Features) - Independent

**Success Criteria**:
- All backend lints clean
- All backend tests pass (baseline + new)
- No regressions in core features

### Phase 3: Frontend Refactoring (Architects 2, 4)

**Priority**: MEDIUM
**Duration**: 2-3 days

Order of execution:
1. **Architect 2** (Types Split) - Use barrel file for compatibility
2. **Architect 4** (Component Split) - Independent

**Success Criteria**:
- All frontend lints clean
- All frontend tests pass
- Build succeeds
- Barrel file maintains backward compatibility

### Phase 4: Final Verification

**Priority**: HIGHEST
**Duration**: 1 day

**Tasks**:
- Run full test suite (backend + frontend)
- Run all linters
- Verify all architectural changes
- Document completion
- Output: `COMPLETION_ACHIEVED`

---

## Resource Requirements

### Human Resources

If executed by agents (Phoenix system):
- 7 Phoenix Architects (one per feature area)
- Each Architect spawns multiple Conductors
- Each Conductor uses Test Writer + Code Writer pattern
- Estimated 50+ total agent sessions

If executed by humans:
- 2 Senior Engineers (backend + frontend)
- 1 DevOps Engineer (CI/CD, deployment)
- 1 QA Engineer (test infrastructure)
- Estimated 2-3 weeks for full completion

### Compute Resources

- Development machine (for refactoring)
- CI/CD pipeline (for testing)
- Staging environment (for verification)
- Database backup (for rollback safety)

---

## Risk Management

### Stop Conditions

STOP refactoring immediately if:
- [ ] Test pass rate drops below 70%
- [ ] Production incidents occur
- [ ] Security vulnerabilities introduced
- [ ] Data corruption detected
- [ ] Multiple unrelated failures

### Rollback Plan

1. **Git revert**: `git revert <commit>` or `git reset --hard HEAD~N`
2. **Database restore**: Restore from backup if migration applied
3. **Service restart**: Restart backend/frontend services
4. **Verification**: Run smoke tests to confirm rollback

### Daily Checkpoints

At end of each day:
- [ ] Document progress
- [ ] Run full test suite
- [ ] Update risk assessment
- [ ] Review next day's plan

---

## Success Criteria

### Technical Criteria

- [ ] All backend tests pass (`pytest tests/`)
- [ ] All frontend tests pass (`npm test`, `npm run test:e2e`)
- [ ] Linting clean (`ruff check .`, `npm run lint`)
- [ ] All God Modules split into focused modules (< 300 lines each)
- [ ] All fat routers cleaned (business logic moved to services)
- [ ] Dual model layers consolidated (automated mapping)
- [ ] Security vulnerabilities fixed
- [ ] CI/CD pipeline working correctly
- [ ] Whale Tracking with BFS behavioral patterns
- [ ] Historical Data Manager with active gap detection
- [ ] No functionality added beyond requirements

### Output Criteria

- [ ] Final message contains: `COMPLETION_ACHIEVED`
- [ ] All architectural debt documented
- [ ] Test results attached
- [ ] Migration guide provided

---

## Next Steps

### Immediate Actions (Producer Handoff Complete)

1. **Spawn Architect 1**: ML Factory Refactoring
2. **Spawn Architect 2**: Frontend Types Split
3. **Spawn Architect 3**: Fat Router Cleanup
4. **Spawn Architect 4**: Component Split
5. **Spawn Architect 5**: Model Consolidation
6. **Spawn Architect 6**: Security & CI/CD
7. **Spawn Architect 7**: Feature Implementation

Each Architect will:
1. Read context from `.phoenix/architects_handoff/architect_N_context.md`
2. Analyze existing code
3. Create edit tasks
4. Spawn Conductors for each task
5. Orchestrate Test Writer → Code Writer pairs
6. Verify completion
7. Create completion report

---

## Notes

- **Scope Creep**: DO NOT add any features beyond stated requirements
- **Pattern Compliance**: Follow existing project patterns, don't introduce new conventions
- **Minimal Changes**: Make only changes necessary to achieve stated goals
- **Test-First**: All changes must be test-first (or test-update-first)
- **Regression Testing**: Every change must be verified against existing functionality
- **Documentation**: All changes must be documented in code and architect logs

---

## File Organization

```
.phoenix/
├── phoenix_edit_plan.md          # Master edit plan
├── current_state_analysis.md     # (not created, delta covers this)
├── desired_state_spec.md         # (not created, delta covers this)
├── delta_breakdown.md            # Detailed changes required
├── risk_assessment.md           # Risk analysis and mitigation
└── architects_handoff/           # Architect context files
    ├── architect_1_context.md   # ML Factory
    ├── architect_2_context.md   # Frontend Types
    ├── architect_3_context.md   # Fat Routers
    ├── architect_4_context.md   # Component Split
    ├── architect_5_context.md   # Model Consolidation
    ├── architect_6_context.md   # Security & CI/CD
    └── architect_7_context.md   # Feature Implementation
```

---

**Producer Phase Complete. Ready to spawn 7 Architects.**
