# TESTS LAYER KNOWLEDGE

**Generated:** 2026-01-03

## OVERVIEW
Backend: pytest with pytest-asyncio, fixtures, contract testing. Frontend: Jest unit/integration + Playwright E2E, MSW mocking, MockWebSocket.

## STRUCTURE
```
tests/
├── conftest.py                    # Global fixtures, async config
├── test_api.py                    # FastAPI contract tests
├── test_backtest_engine.py         # Backtest logic, metrics validation
├── test_backtest_integration.py     # End-to-end backtest workflow
├── test_database.py                # Repository layer tests
├── test_data_acquisition.py       # Market data fetching tests
├── test_binance_integration.py     # External API integration
├── deployment/
│   └── test_docker_build.py       # Infrastructure tests
└── ... (40+ test files)

__tests__/ (Frontend)
├── utils/
│   └── test-utils.ts              # MockWebSocket, renderWithProviders
├── integration/
│   ├── backtest-workflow.test.tsx  # MSW-based workflow tests
│   └── README.md                 # Integration test docs
└── ... (Jest + Playwright tests)
```

## WHERE TO LOOK
| Task | Location | Notes |
|-------|----------|-------|
| Global fixtures | conftest.py | DB session, sample data generators |
| API contracts | test_api.py | Status codes, validation errors |
| Backtest logic | test_backtest_engine.py | Engine accuracy, metrics calculation |
| Integration workflows | test_backtest_integration.py | Full backtest execution flow |
| Data layer | test_database.py | Repository CRUD tests |
| External APIs | test_binance_integration.py | Real API contract validation |
| Infrastructure | deployment/ | Docker, compose orchestration |
| Frontend utils | __tests__/utils/test-utils.ts | MockWebSocket, rendering wrappers |
| Frontend workflows | __tests__/integration/ | User journey tests with MSW |

## CONVENTIONS

### Backend (Pytest)
- **Async Tests**: pytest-asyncio with auto mode
- **Fixtures**: Heavy use for data generation (sample_price_data)
- **Class Structure**: Test classes prefixed with `Test` (e.g., `class TestHealthCheck`)
- **Contract Validation**: Focus on status codes, schema validation

### Frontend (Jest/Playwright)
- **MSW Mocking**: API calls mocked via Mock Service Worker
- **Custom Renderers**: `renderWithProviders` for Auth, Query, Router, Toast contexts
- **MockWebSocket**: Simulates connection drops, message queuing, reconnections
- **Workflow Tests**: Organized by user flows (backtest, paper-trade)

## ANTI-PATTERNS

### Anti-Patterns
- **Skipping Tests**: Legacy mocking with `addListener`/`removeListener` (deprecated)
- **No Coverage Tests**: Missing tests for critical paths
- **Brittle Setup**: Hardcoded sleeps instead of health checks in integration tests

### Test Organization
- **Split Test Locations**: Both /tests/ and root-level /__tests__/ exist
- **Standardize**: Move all backend tests to /tests/, keep frontend in /__tests__/ only
