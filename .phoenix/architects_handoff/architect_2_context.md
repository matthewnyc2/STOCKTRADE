# Architect 2 Context: Frontend Types Split

**Generated**: 2026-01-03
**Architect ID**: 2
**Feature**: Split `frontend/src/types/api.ts` (1,446 lines) into domain-specific files
**Priority**: HIGH
**Complexity**: MEDIUM

---

## Current State

**File**: `frontend/src/types/api.ts` (1,446 lines)

**Structure**:
- **Lines 1-10**: Imports
- **Lines 11-144**: Enums (StrategyType, RiskLevel, SignalStatus, etc.)
- **Lines 146-321**: Shadow/Liquidity types (LiquidityCluster, SweepRecommendation)
- **Lines 323-421**: Strategy types (Strategy, Layer, LogicGate)
- **Lines 423-461**: Portfolio types (Portfolio, Position, AssetAllocation)
- **Lines 463-525**: Whale types (Whale, WhaleWallet, WhalePattern)
- **Lines 527-618**: ML types (MLModel, TrainingConfig, PredictionResult)
- **Lines 647-715**: Onboarding types (OnboardingStep, UserProfile)
- **Lines 717-746**: Base types (ApiResponse, PaginatedResponse, ErrorResponse)
- **Lines 748-840**: AI types (AIReasoning, AIRecommendation)
- **Lines 842-889**: Market types (MarketData, Ticker, OrderBook)
- **Lines 891-1098**: Additional strategy types (StrategyTemplate, LayerConfig, etc.)
- **Lines 1100-1332**: ApiClient class (HTTP wrapper, auth, error handling)
- **Lines 1334-1442**: ApiEndpoints object (endpoint URLs, methods)

**Dependencies**:
- Internal: Frontend components, hooks, lib utilities
- External: No external dependencies (pure TypeScript)

**Importing Files**: 73 files import from `@/types/api`

---

## Desired State

**File Structure**:
```
frontend/src/types/
├── enums.ts             # All enums (StrategyType, RiskLevel, etc.)
├── base.ts              # Base types (ApiResponse, PaginatedResponse)
├── strategies.ts        # Strategy, Layer, LogicGate, templates
├── shadow.ts            # Liquidity clusters, sweep recommendations
├── whales.ts            # Whale, Wallet, Pattern types
├── ml.ts                # MLModel, TrainingConfig, PredictionResult
├── ai.ts                # AIReasoning, AIRecommendation
├── market.ts            # MarketData, Ticker, OrderBook
├── portfolio.ts         # Portfolio, Position, AssetAllocation
├── onboarding.ts        # OnboardingStep, UserProfile
├── api.ts               # Barrel file (re-exports all types)
```

**Infrastructure Moved**:
```
frontend/src/lib/
└── api-client-base.ts   # ApiClient class (moved from types/api.ts)

frontend/src/constants/
└── endpoints.ts         # ApiEndpoints object (moved from types/api.ts)
```

**Separation of Concerns**:
- Each domain file contains related types only
- Infrastructure (ApiClient, ApiEndpoints) separated from types
- Barrel file maintains backward compatibility

---

## Specific Tasks

### Task 1: Create enums.ts
- Extract all enums (lines 11-144)
- Export: StrategyType, RiskLevel, SignalStatus, Timeframe, etc.
- Ensure no dependencies on other type files
- Add documentation comments

### Task 2: Create base.ts
- Extract base types (lines 717-746)
- Export: ApiResponse, PaginatedResponse, ErrorResponse
- Keep generic, infrastructure-level types
- No domain-specific types

### Task 3: Create strategies.ts
- Extract strategy types (lines 323-421 + 891-1098)
- Export: Strategy, Layer, LogicGate, StrategyTemplate, LayerConfig
- Import enums from enums.ts
- Import base types from base.ts

### Task 4: Create shadow.ts
- Extract shadow/liquidity types (lines 146-321)
- Export: LiquidityCluster, SweepRecommendation, LiquidityMap
- Import enums from enums.ts
- Import base types from base.ts

### Task 5: Create whales.ts
- Extract whale types (lines 463-525)
- Export: Whale, WhaleWallet, WhalePattern, WhaleAlert
- Import enums from enums.ts
- Import base types from base.ts

### Task 6: Create ml.ts
- Extract ML types (lines 527-618)
- Export: MLModel, TrainingConfig, PredictionResult, TrainingProgress
- Import enums from enums.ts
- Import base types from base.ts

### Task 7: Create ai.ts
- Extract AI types (lines 748-840)
- Export: AIReasoning, AIRecommendation, AIInsight
- Import enums from enums.ts
- Import base types from base.ts

### Task 8: Create market.ts
- Extract market types (lines 842-889)
- Export: MarketData, Ticker, OrderBook, Candle
- Import enums from enums.ts
- Import base types from base.ts

### Task 9: Create portfolio.ts
- Extract portfolio types (lines 423-461)
- Export: Portfolio, Position, AssetAllocation, Performance
- Import enums from enums.ts
- Import base types from base.ts

### Task 10: Create onboarding.ts
- Extract onboarding types (lines 647-715)
- Export: OnboardingStep, UserProfile, UserSettings
- Import enums from enums.ts
- Import base types from base.ts

### Task 11: Move ApiClient to lib/
- Move ApiClient class (lines 1100-1332)
- Create `frontend/src/lib/api-client-base.ts`
- Export ApiClient
- Update internal imports (if any)

### Task 12: Move ApiEndpoints to constants/
- Move ApiEndpoints object (lines 1334-1442)
- Create `frontend/src/constants/endpoints.ts`
- Export ApiEndpoints
- Ensure TypeScript typing

### Task 13: Create Barrel File (CRITICAL)
- Rename original `api.ts` to `api.ts.bak`
- Create new `api.ts` with re-exports
- Export all types from all domain files
- Export ApiClient from lib
- Export ApiEndpoints from constants
- **This must maintain 100% backward compatibility**

### Task 14: Test Barrel File
- Run `npm run build` to verify no import errors
- Run `npm run typecheck` to verify type checking
- Verify all 73 importing files still work
- Fix any missing re-exports

### Task 15: Delete Original File
- Delete `frontend/src/types/api.ts.bak`
- Verify no remaining references
- Confirm all tests pass

### Task 16: Update Imports (Optional)
- Gradually update imports in domain files
- Change `from '@/types/api'` to `from '@/types/strategies'`
- One file at a time, verify after each
- This is post-refactoring optimization

---

## Critical Considerations

### Barrel File Backward Compatibility
- **CRITICAL**: All 73 importing files must continue to work without modification
- Barrel file must re-export ALL symbols
- Verify with `npm run build` before deleting original file
- DO NOT skip this step

### Type Dependencies
- Domain files depend on enums.ts and base.ts
- Ensure circular dependencies are avoided
- enums.ts must have no dependencies
- base.ts must have no dependencies

### Import Path Updates
- ApiClient moves to `@/lib/api-client-base.ts`
- ApiEndpoints moves to `@/constants/endpoints.ts`
- Update imports in lib files first
- Verify no broken references

### TypeScript Compilation
- Each file must compile independently
- Run `tsc --noEmit` after creating each file
- Fix type errors before proceeding
- DO NOT accumulate type errors

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Breaking imports (73 files) | HIGH | Barrel file with full re-exports, test build before delete |
| Missing re-exports in barrel | HIGH | Compile and typecheck before deleting original |
| Circular dependencies | MEDIUM | enums.ts and base.ts have no deps, verify with tsc |
| ApiClient/ApiEndpoints broken links | MEDIUM | Update imports in lib files before moving |

---

## Success Criteria

- [ ] All 10 domain type files created
- [ ] enums.ts and base.ts have no dependencies
- [ ] ApiClient moved to lib/api-client-base.ts
- [ ] ApiEndpoints moved to constants/endpoints.ts
- [ ] Barrel file (api.ts) re-exports all symbols
- [ ] npm run build passes without errors
- [ ] npm run typecheck passes
- [ ] All 73 importing files still work
- [ ] Original api.ts.bak deleted
- [ ] No broken imports in codebase
- [ ] Linter clean (npm run lint)

---

## Notes

- **DO NOT** delete original api.ts before testing barrel file
- **DO NOT** skip barrel file verification
- **DO NOT** update all 73 imports at once (optional gradual migration)
- **DO** test build after each file creation
- **DO** keep enums.ts and base.ts dependency-free
- **DO** add documentation comments to each type

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 1)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 1)
- Codebase knowledge: `AGENTS.md` (Frontend Types section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the file structure/imports
2. CODE_WRITER: Create the domain file with proper exports
3. Regression Check: Run build/typecheck after each file

**Order of Execution**: Tasks 1-10 (parallel), 11-12 (sequential), 13 (CRITICAL), 14 (verify), 15 (cleanup), 16 (optional post-refactor)
