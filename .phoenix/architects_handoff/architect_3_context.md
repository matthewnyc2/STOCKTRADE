# Architect 3 Context: Fat Router Cleanup

**Generated**: 2026-01-03
**Architect ID**: 3
**Feature**: Extract business logic from api/strategies.py (1,122 lines) and api/shadow.py (1,297 lines)
**Priority**: HIGH
**Complexity**: HIGH

---

## Current State

### api/strategies.py (1,122 lines)

**Structure**:
- **Lines 1-78**: Imports and dependencies
- **Lines 80-140**: `model_to_strategy()` helper function
- **Lines 142-262**: Inline Pydantic models (StrategyCreate, StrategyUpdate, LayerCreate, etc.)
- **Lines 263-293**: `create_from_template()` helper function
- **Lines 295-450**: Strategy CRUD endpoints
- **Lines 452-580**: Layer management endpoints
- **Lines 582-680**: Logic gate and parameter endpoints
- **Lines 681-683**: Raw SQL `update_layer_weights()` function
- **Lines 684-1122**: Additional endpoints and helpers

**Issues**:
- Inline Pydantic models (~120 lines)
- Business logic in endpoints (model_to_strategy, create_from_template)
- Raw SQL for layer weight updates
- Mixing concerns: routing + models + business logic + DB access

### api/shadow.py (1,297 lines)

**Structure**:
- **Lines 1-150**: Imports and dependencies
- **Lines 151-350**: Inline Pydantic models (response wrappers, calculation requests)
- **Lines 351-550**: Liquidity analysis endpoints
- **Lines 551-650**: Sweep probability calculations (inline numpy)
- **Lines 651-850**: Heuristic engines (_generate_recommendations)
- **Lines 851-1050**: Liquidity map generation (inline logic)
- **Lines 1051-1150**: Round number level detection
- **Lines 1151-1297**: Additional analytics and mock data

**Issues**:
- Inline Pydantic models (~200 lines)
- Mock data generation in endpoints
- Heuristic engines in router (_generate_recommendations)
- Mathematical operations (numpy) in endpoints
- No clear separation between analytics and routing

---

## Desired State

### api/strategies.py (~300 lines)

**Structure**:
- **Lines 1-30**: Imports (models, services, DB)
- **Lines 31-300**: Router endpoints only (CRUD + DI)
- Business logic moved to services/strategy_manager.py
- Pydantic models moved to models/strategy.py
- Raw SQL moved to database/repositories/strategy_layer.py

**Separation of Concerns**:
- Router: Endpoint definitions, dependency injection, response formatting
- Service: Business logic (model_to_strategy, create_from_template, clone_strategy)
- Repository: Database access (update_layer_weights, custom queries)
- Models: Pydantic schemas (StrategyCreate, LayerCreate, etc.)

### api/shadow.py (~300 lines)

**Structure**:
- **Lines 1-30**: Imports (models, services, DB)
- **Lines 31-300**: Router endpoints only (analytics + DI)
- Heuristics moved to services/liquidity_hunter.py
- Pydantic models moved to models/arbitrage.py
- Mock data removed or moved to seed files

**Separation of Concerns**:
- Router: Endpoint definitions, dependency injection
- Service: Heuristic engines, mathematical operations, recommendations
- Models: Pydantic schemas (LiquidityCluster, SweepRecommendation, etc.)

---

## Specific Tasks

### api/strategies.py Cleanup

#### Task 1: Extract Pydantic Models to models/strategy.py
- Move StrategyCreate, StrategyUpdate, LayerCreate, LayerUpdate
- Move LogicGateUpdate, StrategyUpdateEnhanced
- Move all request/response models (~120 lines)
- Export from models/strategy.py
- Update imports in api/strategies.py

#### Task 2: Move model_to_strategy to services/strategy_manager.py
- Extract `model_to_strategy()` function (lines 79-140)
- Move to StrategyManager class or standalone function
- Add proper imports (from database.models.strategy import Strategy)
- Update api/strategies.py to use StrategyManager.model_to_strategy()

#### Task 3: Move create_from_template to services/strategy_manager.py
- Extract `create_from_template()` function (lines 263-293)
- Move to StrategyManager.create_from_template()
- Ensure all dependencies (template loading, layer copying) are available
- Update api/strategies.py endpoint to call StrategyManager

#### Task 4: Extract clone_strategy logic
- Identify cloning logic in api/strategies.py
- Move to StrategyManager.clone_strategy()
- Ensure deep copy of layers, parameters, tags
- Update endpoint to use service method

#### Task 5: Move update_layer_weights to repository
- Extract raw SQL function (lines 679-683)
- Create `database/repositories/strategy_layer.py`
- Move to StrategyLayerRepository.update_weights()
- Use SQLAlchemy ORM instead of raw SQL if possible
- Update api/strategies.py to use repository

#### Task 6: Clean api/strategies.py Router
- Remove all moved code
- Keep only endpoint definitions
- Add dependency injection (StrategyManager, repositories)
- Ensure router is ~300 lines
- Verify all endpoints still work

### api/shadow.py Cleanup

#### Task 7: Extract Pydantic Models to models/arbitrage.py
- Move response wrappers (LiquidityAnalysisResponse, etc.)
- Move calculation requests (SweepCalculationRequest, etc.)
- Move liquidity map models (LiquidityMap, LiquidityZone)
- Export from models/arbitrage.py
- Update imports in api/shadow.py

#### Task 8: Move _generate_recommendations to services/liquidity_hunter.py
- Extract heuristic engine (lines 728-774)
- Move to LiquidityHunter.generate_recommendations()
- Ensure all dependencies (market data, analysis context) are available
- Update api/shadow.py endpoint to call service

#### Task 9: Move sweep probability logic to services/liquidity_hunter.py
- Extract numpy calculations (lines 957-979)
- Move to LiquidityHunter.calculate_sweep_probability()
- Keep mathematical logic in service layer
- Update endpoint to use service method

#### Task 10: Move get_round_number_levels to services/liquidity_hunter.py
- Extract round number detection (lines 1189-1216)
- Move to LiquidityHunter.get_round_number_levels()
- Update endpoint to use service method

#### Task 11: Remove Mock Data
- Identify mock data generation in endpoints
- Remove mock data endpoints or replace with real data
- Ensure all analytics return actual data
- Update tests to use real data or seed files

#### Task 12: Clean api/shadow.py Router
- Remove all moved code
- Keep only endpoint definitions
- Add dependency injection (LiquidityHunter, repositories)
- Ensure router is ~300 lines
- Verify all endpoints still work

### Verification Tasks

#### Task 13: Update Imports Across Codebase
- Find all imports from api/strategies.py (models, functions)
- Update to import from models/strategy.py or services/strategy_manager.py
- Find all imports from api/shadow.py
- Update to import from models/arbitrage.py or services/liquidity_hunter.py
- Verify no broken references

#### Task 14: Test Strategy Endpoints
- Run pytest tests for strategies
- Test create, read, update, delete strategies
- Test create_from_template
- Test clone_strategy
- Test update_layer_weights
- Verify all tests pass

#### Task 15: Test Shadow Endpoints
- Run pytest tests for shadow/liquidity
- Test liquidity analysis endpoints
- Test sweep probability calculations
- Test recommendation generation
- Test round number levels
- Verify all tests pass

#### Task 16: Integration Tests
- Run full workflow test for strategy creation
- Run full workflow test for strategy cloning
- Run full workflow test for liquidity analysis
- Verify end-to-end functionality

---

## Critical Considerations

### Business Logic Complexity
- `model_to_strategy` has complex mapping logic
- `create_from_template` handles template loading, layer copying
- `clone_strategy` must deep copy all nested objects
- **CRITICAL**: Test each function thoroughly before moving

### Database Access Patterns
- Raw SQL `update_layer_weights` must be converted to ORM
- Ensure SQLAlchemy 2.0 syntax (async, select(), etc.)
- Preserve exact behavior of raw SQL
- Test database operations after migration

### Dependency Injection
- Services must be injected via FastAPI `Depends()`
- Repositories must be injected via `Depends(get_db)`
- Ensure proper session management
- Test async patterns

### Mock Data Removal
- Some endpoints may rely on mock data for development
- Remove mock data only if real data is available
- Update tests to use seed data instead
- Verify analytics still work with real data

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Business logic regression | HIGH | Test-first approach, write tests before moving |
| Database query breakage | HIGH | Compare raw SQL to ORM output, verify exact results |
| Missing dependencies after move | MEDIUM | Map all imports, verify each function has access |
| Feature regression | HIGH | Run full integration tests after each move |
| Mock data removal breaking tests | MEDIUM | Replace with seed data, update test expectations |

---

## Success Criteria

### api/strategies.py
- [ ] Router is ~300 lines
- [ ] All Pydantic models moved to models/strategy.py
- [ ] All business logic moved to StrategyManager
- [ ] Raw SQL moved to StrategyLayerRepository
- [ ] All strategy tests pass
- [ ] create_from_template works
- [ ] clone_strategy works
- [ ] update_layer_weights works

### api/shadow.py
- [ ] Router is ~300 lines
- [ ] All Pydantic models moved to models/arbitrage.py
- [ ] All heuristics moved to LiquidityHunter
- [ ] Mock data removed or replaced
- [ ] All shadow tests pass
- [ ] sweep probability calculations work
- [ ] recommendation generation works
- [ ] round number levels work

### General
- [ ] All imports updated across codebase
- [ ] Integration tests pass
- [ ] No broken references
- [ ] Linter clean (ruff check .)
- [ ] Type checker clean (mypy or pyright)

---

## Notes

- **DO NOT** move code without testing it first
- **DO NOT** change business logic during refactoring (pure extraction)
- **DO** preserve exact behavior of functions
- **DO** use SQLAlchemy 2.0 async patterns
- **DO** run tests after each function move
- **DO NOT** delete code until all tests pass

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 2)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 2)
- Codebase knowledge: `AGENTS.md` (Fat Routers section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the function/endpoint
2. CODE_WRITER: Move the code to appropriate layer
3. Regression Check: Run tests after each move

**Order of Execution**: Tasks 1-6 (strategies) sequential, Tasks 7-12 (shadow) sequential, Tasks 13-16 (verification) sequential
