# Architect 1 Context: ML Factory Refactoring

**Generated**: 2026-01-03
**Architect ID**: 1
**Feature**: Split `services/ml_factory.py` into `services/ml/` package
**Priority**: HIGH
**Complexity**: MEDIUM

---

## Current State

**File**: `services/ml_factory.py` (1,550 lines)

**Structure**:
- **Lines 1-198**: Enums & Config (TrainingConfig, TrainingProgress, PredictionResult)
- **Lines 199-451**: Model Architecture (LSTMLayer, LSTMModel - custom NumPy implementation)
- **Lines 452-670**: Training Engine (TrainingEngine - backpropagation, validation)
- **Lines 671-1023**: Feature Engineering (FeatureEngine - technical indicators, sequences)
- **Lines 1024-1545**: Orchestration (MLFactory - ThreadPoolExecutor, persistence)
- **Lines 1546-1552**: Global accessor (get_ml_factory())

**Dependencies**:
- External: `numpy` (heavy), `dataclasses`, `concurrent.futures`
- Internal: `database.connection.get_db_context`, `database.models.MLModel`, `models.ml`, `services.indicators`

---

## Desired State

**Package Structure**:
```
services/ml/
├── __init__.py          # Package exports, get_ml_factory()
├── models.py             # LSTMLayer, LSTMModel, helper functions
├── engine.py             # TrainingEngine, TrainingProgress, TrainingTaskStatus
├── features.py           # FeatureEngine, create_sequences
└── factory.py            # MLFactory, TrainingConfig, PredictionResult
```

**Separation of Concerns**:
- `models.py`: Pure NumPy model architecture (no I/O)
- `engine.py`: Training loop, backpropagation (no DB access)
- `features.py`: Data transformation (indicators → ML-ready features)
- `factory.py`: Orchestration (threading, DB, persistence, API-facing)

---

## Specific Tasks

### Task 1: Create Package Structure
- Create `services/ml/` directory
- Create `__init__.py` with package exports
- Verify directory structure

### Task 2: Extract Models (services/ml/models.py)
- Move `LSTMLayer` class
- Move `LSTMModel` class
- Move helper functions: `_sigmoid`, `_tanh`, `_calculate_loss`
- Add type hints for NumPy arrays
- Ensure no external dependencies (pure NumPy)

### Task 3: Extract Engine (services/ml/engine.py)
- Move `TrainingEngine` class
- Move `TrainingProgress` dataclass
- Move `TrainingTaskStatus` enum
- Ensure no DB access (training logic only)
- Preserve threading safety (if any)

### Task 4: Extract Features (services/ml/features.py)
- Move `FeatureEngine` class
- Move `create_sequences` function
- Import `services.indicators.calculate_all_indicators`
- Preserve feature engineering logic (~50+ indicators)

### Task 5: Extract Factory (services/ml/engine.py → factory.py)
- Move `MLFactory` class
- Move `TrainingConfig` dataclass
- Move `PredictionResult` dataclass
- Keep `ThreadPoolExecutor` orchestration
- Keep DB session handling
- Keep pickle/JSON persistence

### Task 6: Update Package Init (services/ml/__init__.py)
- Import and re-export: `MLFactory`, `TrainingEngine`, `FeatureEngine`, etc.
- Keep `get_ml_factory()` function
- Maintain backward compatibility

### Task 7: Update Imports Across Codebase
- Find all imports of `from services.ml_factory import ...`
- Update to `from services.ml import ...`
- Verify no breaking changes

### Task 8: Delete Original File
- Delete `services/ml_factory.py`
- Verify all imports resolved

---

## Critical Considerations

### Threading Safety
- `MLFactory` uses `ThreadPoolExecutor` for background training
- Ensure cross-module access is thread-safe
- Test concurrent training jobs

### NumPy Type Safety
- Original code has type errors (NDArray[float64] vs None)
- Preserve existing behavior (even with errors)
- DO NOT fix type errors (outside scope)

### Persistence
- Models saved as `.pkl` (weights) + `.json` (metadata)
- Preserve exact file format
- Preserve database sync (MLModel table)

### Backward Compatibility
- `get_ml_factory()` must return same object
- API endpoints using MLFactory must continue working
- No changes to public interface

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Threading state broken | HIGH | Test concurrent training jobs |
| Import path broken | MEDIUM | Update all imports, verify build |
| NumPy types changed | LOW | Preserve existing behavior |
| Persistence logic lost | MEDIUM | Verify model save/load after refactor |

---

## Success Criteria

- [ ] All classes/functions moved to appropriate modules
- [ ] `services/ml/__init__.py` exports all public API
- [ ] All imports updated across codebase
- [ ] `get_ml_factory()` returns working MLFactory instance
- [ ] Backend tests for ML training pass
- [ ] ML model training and prediction works as before
- [ ] No regressions in ML features
- [ ] Linter clean (ruff check .)

---

## Notes

- **DO NOT** fix NumPy type errors (existing behavior must be preserved)
- **DO NOT** change public interface of MLFactory
- **DO NOT** introduce new features (pure refactoring only)
- **DO** follow existing code patterns (async/await, error handling)
- **DO** add tests for cross-module interactions

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 1)
- Risk assessment: `.phoenix/risk_assessment.md` (Section 3)
- Codebase knowledge: `AGENTS.md` (ML Factory section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create/update test for the task
2. CODE_WRITER: Implement the minimal change to pass test
3. Regression Check: Run relevant tests after each change

**Order of Execution**: Tasks 1-8 sequentially (each depends on previous)
