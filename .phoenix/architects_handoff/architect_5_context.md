# Architect 5 Context: Model Consolidation

**Generated**: 2026-01-03
**Architect ID**: 5
**Feature**: Unify dual model layers, fix drawdown logic, enable automated ORM-to-Pydantic mapping
**Priority**: HIGH
**Complexity**: MEDIUM

---

## Current State

### Dual Model Layers

**Issue**: Two parallel model layers with 1:1 mapping but duplicated enums

**database/models/** (SQLAlchemy ORM):
- `strategy.py`: StrategyType, RiskLevel, Status enums + Strategy ORM class
- `portfolio.py`: Portfolio, Position ORM classes
- `market_data.py`: MarketData, Ticker ORM classes
- etc. (13 ORM classes total)

**models/** (Pydantic schemas):
- `strategy.py`: StrategyType, RiskLevel, Status enums + Strategy Pydantic class
- `portfolio.py`: Portfolio, Position Pydantic classes
- `market_data.py`: MarketData, Ticker Pydantic classes
- etc. (13 Pydantic classes total)

**Problems**:
- Enums defined in both layers (risk of desynchronization)
- Manual conversion functions (`model_to_strategy`)
- No automatic ORM-to-Pydantic mapping
- Boilerplate code for data conversion

### Manual Mapping Functions

**Example**: `api/strategies.py` has `model_to_strategy()` function
```python
def model_to_strategy(db_model: database.models.strategy.Strategy) -> Strategy:
    return Strategy(
        id=db_model.id,
        name=db_model.name,
        type=db_model.type,  # Manual mapping
        risk_level=db_model.risk_level,  # Manual mapping
        # ... 20+ more fields
    )
```

**Issues**:
- Boilerplate code
- Error-prone (field names must match exactly)
- No automatic validation
- Maintenance burden

### Positive Drawdown Bug

**Issue**: Backtest drawdown is positive (should be negative)

**Location**: `models/backtest.py` or `database/models/backtest.py`

**Current Logic**:
```python
drawdown = max_drawdown - current_drawdown  # WRONG: can be positive
```

**Correct Logic**:
```python
drawdown = current_drawdown - peak  # Always negative or zero
```

**Impact**:
- Incorrect backtest results
- Misleading performance metrics
- Potential trading decisions based on wrong data

---

## Desired State

### Centralized Enums

**Single Source of Truth**: All enums defined in `models/` only

**database/models/**:
- Remove enum definitions
- Import enums from `models/`
- Use imported enums in ORM classes

**models/**:
- Keep all enum definitions
- Export enums for use in ORM classes
- Single source of truth

**Example**:
```python
# models/strategy.py
class StrategyType(str, Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    # ...

# database/models/strategy.py
from models.strategy import StrategyType  # Import from models/

class Strategy(BaseModel):
    type: Mapped[StrategyType] = mapped_column(Enum(StrategyType))
```

### Automated Mapping with from_attributes

**Enable**: All Pydantic models use `from_attributes = True`

**Before** (manual):
```python
strategy = model_to_strategy(db_strategy)
```

**After** (automated):
```python
strategy = Strategy.model_validate(db_strategy)
```

**Configuration**:
```python
# models/strategy.py
class Strategy(BaseModel):
    id: int
    name: str
    type: StrategyType
    # ...

    class Config:
        from_attributes = True  # Enable ORM-to-Pydantic mapping
```

### Delete Manual Mapping Functions

**Remove**: All `model_to_*` functions

**Locations**:
- `api/strategies.py`: `model_to_strategy()`
- `services/strategy_manager.py`: `model_to_strategy()`
- Any other manual conversion functions

**Replace**:
```python
# Old
strategy = model_to_strategy(db_strategy)

# New
strategy = Strategy.model_validate(db_strategy)
```

### Fix Drawdown Logic

**Correct**: Drawdown calculation to be negative or zero

**Location**: `models/backtest.py` or `database/models/backtest.py`

**Formula**:
```python
drawdown = (current_value - peak_value) / peak_value
# Always negative or zero (current_value <= peak_value)
```

---

## Specific Tasks

### Task 1: Centralize Enums in models/
- Identify all enums in database/models/
- Identify all enums in models/
- Remove enums from database/models/
- Keep enums in models/ only
- Export enums from models/

### Task 2: Update database/models/ to Import Enums
- Update all ORM classes to import enums from models/
- Example: `from models.strategy import StrategyType`
- Verify enum types match
- Ensure no breaking changes

### Task 3: Add from_attributes to All Pydantic Models
- Update `models/strategy.py`: Add `Config.from_attributes = True`
- Update `models/portfolio.py`: Add `Config.from_attributes = True`
- Update `models/backtest.py`: Add `Config.from_attributes = True`
- Update all 13 Pydantic models
- Verify all models support `.model_validate()`

### Task 4: Replace model_to_strategy in api/strategies.py
- Find all uses of `model_to_strategy()`
- Replace with `Strategy.model_validate(db_strategy)`
- Remove `model_to_strategy()` function
- Verify API endpoints still work

### Task 5: Replace model_to_strategy in services/strategy_manager.py
- Find all uses of `model_to_strategy()`
- Replace with `Strategy.model_validate(db_strategy)`
- Remove `model_to_strategy()` function
- Verify service methods still work

### Task 6: Delete All Manual Mapping Functions
- Search for all `model_to_*` functions across codebase
- Replace with `.model_validate()` calls
- Delete all manual conversion functions
- Verify no remaining uses

### Task 7: Fix Drawdown Logic
- Locate drawdown calculation in backtest models
- Identify current (buggy) formula
- Replace with correct formula: `(current - peak) / peak`
- Ensure drawdown is negative or zero
- Add comment explaining the fix

### Task 8: Update All ORM-to-Pydantic Conversions
- Search for all manual ORM-to-Pydantic conversions
- Replace with `.model_validate()` calls
- Verify all conversions work
- Check for edge cases (nested models, JSON fields)

### Task 9: Test Model Conversions
- Run pytest tests for model conversions
- Test Strategy model conversion
- Test Portfolio model conversion
- Test Backtest model conversion
- Test all 13 model conversions
- Verify all tests pass

### Task 10: Test Drawdown Fix
- Run backtest tests
- Verify drawdown is negative or zero
- Verify backtest results are correct
- Compare with historical backtest results
- Verify no regression

### Task 11: Integration Tests
- Run full strategy creation workflow
- Run full backtest workflow
- Run full portfolio management workflow
- Verify end-to-end functionality
- Check for any data mapping errors

---

## Critical Considerations

### Enum Synchronization
- **CRITICAL**: Ensure enums in models/ match ORM enum types exactly
- Verify enum values are identical
- Verify enum names are identical
- Test database serialization/deserialization

### from_attributes Compatibility
- SQLAlchemy 2.0 required for `from_attributes`
- Verify SQLAlchemy version
- Check for deprecated patterns
- Test with different ORM field types (JSON, Array, etc.)

### Nested Model Mapping
- Some models have nested structures (layers, parameters)
- `.model_validate()` must handle nested models
- Test with complex nested structures
- Verify JSON column mappings work

### Drawdown Calculation
- **CRITICAL**: Drawdown must be negative or zero
- Verify formula: `(current - peak) / peak`
- Test with different scenarios (profit, loss, flat)
- Compare with existing backtest data

### Backward Compatibility
- API responses must remain identical
- Database schema unchanged
- Frontend type definitions unchanged
- Verify no breaking changes for consumers

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Enum desynchronization | HIGH | Centralize enums, test database serialization |
| from_attributes incompatibility | MEDIUM | Verify SQLAlchemy 2.0, test all model types |
| Nested model mapping errors | MEDIUM | Test complex nested structures, verify JSON fields |
| Drawdown regression | HIGH | Compare backtest results before/after fix |
| API response changes | MEDIUM | Compare API responses, verify identical output |

---

## Success Criteria

### Enum Centralization
- [ ] All enums defined only in models/
- [ ] database/models/ imports enums from models/
- [ ] No enum duplication
- [ ] Database serialization works correctly

### Automated Mapping
- [ ] All Pydantic models have `from_attributes = True`
- [ ] All manual mapping functions deleted
- [ ] All conversions use `.model_validate()`
- [ ] All model conversions work correctly

### Drawdown Fix
- [ ] Drawdown calculation corrected
- [ ] Drawdown is negative or zero
- [ ] Backtest results are accurate
- [ ] No regression in backtest performance

### Tests
- [ ] All model conversion tests pass
- [ ] All backtest tests pass
- [ ] All integration tests pass
- [ ] No data mapping errors

---

## Notes

- **DO NOT** change enum values (centralize only)
- **DO NOT** change database schema
- **DO NOT** modify API contracts
- **DO** verify drawdown is negative after fix
- **DO** test with existing backtest data
- **DO NOT** skip nested model testing

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 3)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 5)
- Codebase knowledge: `AGENTS.md` (Model Consolidation section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the model conversion
2. CODE_WRITER: Implement the change (centralize enum, add from_attributes, fix drawdown)
3. Regression Check: Run tests after each change

**Order of Execution**: Tasks 1-2 (enums) sequential, Task 3 (from_attributes) sequential, Tasks 4-6 (delete manual mapping) sequential, Task 7 (drawdown fix) sequential, Tasks 8-11 (verification) sequential
