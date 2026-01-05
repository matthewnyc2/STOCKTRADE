# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-03
**Commit:** ef6480c
**Branch:** master

## OVERVIEW
Full-stack crypto trading platform with Python/FastAPI backend and Next.js frontend. Features: backtesting, signal generation, whale tracking, node-based strategy composer, ML optimization, and real-time market data with multi-exchange failover.

## STRUCTURE
```
STOCKTRADE/
├── api/               # FastAPI routers (endpoints)
├── core/               # Cross-cutting concerns (auth, config, error handling, websockets)
├── database/           # SQLAlchemy models + repositories + migrations
│   ├── models/         # ORM table definitions (BaseModel inheritance)
│   └── repositories/   # Generic BaseRepository + domain-specific repos
├── services/           # Business logic layer (backtest engine, ML factory, whale detector)
├── models/             # Pydantic schemas (request/response models)
├── tests/              # Backend pytest suite
├── __tests__/          # Frontend Jest/Playwright tests
├── frontend/           # Next.js 14 application
│   └── src/
│       ├── app/         # App Router pages (admin, alpha-lab, dashboard, etc.)
│       ├── components/   # React components (UI, dashboard, laboratory, signals)
│       ├── hooks/       # React hooks (API clients, WebSocket, polling)
│       └── lib/        # Utilities (API client, chart config, node definitions)
└── docs/               # Architecture docs (DATA_SYSTEM, API_CONTRACT, etc.)
```

## WHERE TO LOOK

| Task | Location | Notes |
|-------|----------|-------|
| FastAPI entry point | `api/main.py` | Lifespan, middleware, router mounting |
| Business logic | `services/` | BacktestEngine, StrategyManager, MLFactory, ConstellationDetector |
| Data models | `database/models/` | SQLAlchemy 2.0 with `Mapped` types |
| Data access | `database/repositories/` | BaseRepository<T> pattern |
| API endpoints | `api/*.py` | Routers organized by domain (auth, strategies, backtests, etc.) |
| Pydantic schemas | `models/*.py` | Request/response validation |
| Core utilities | `core/` | Response wrapper, error handling, security, config, websockets |
| Frontend routing | `frontend/src/app/` | Next.js App Router |
| Frontend components | `frontend/src/components/` | UI library + feature components |
| Frontend hooks | `frontend/src/hooks/` | useApi, useWebSocket, domain hooks |
| Node editor | `frontend/src/components/laboratory/NodeEditor.tsx` | ReactFlow-based visual composer |
| Market data | `services/market_data_manager.py`, `services/multi_source_manager.py` | Failover, backfill, gap detection |
| Background tasks | `services/background_tasks.py` | SQLite-backed task queue for long-running ops |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|---------|------|----------|--------|------|
| FastAPI | Class | api/main.py | - | Application factory |
| BaseRepository | Generic | database/base.py | 12+ | Generic CRUD for all repos |
| BaseModel | Base | database/models/__init__.py | 13 | Common ORM fields (id, timestamps, to_dict) |
| BacktestEngine | Class | services/backtest_engine.py | 5 | Historical simulation with slippage/commission |
| StrategyManager | Class | services/strategy_manager.py | 8 | Strategy lifecycle, cloning, versioning |
| MLFactory | Class | services/ml_factory.py | 3 | ML model training orchestration |
| MultiSourceManager | Class | services/multi_source_manager.py | 4 | Exchange failover with health tracking |
| WebSocketManager | Class | core/websocket.py | 6 | Multi-channel real-time broadcasting |
| ApiResponse | Class | core/response.py | - | Standardized response envelope |
| ApiException | Base | core/error_handlers.py | 8 | Custom exception hierarchy |
| ResponseWrapperMiddleware | Class | core/response.py | - | Auto-wrap all JSON responses |

## CONVENTIONS

### Backend (Python/FastAPI)
- **Layered architecture:** API → Service → Repository → Model
- **Async everywhere:** All I/O (DB, APIs, WebSockets) uses async/await
- **Repository pattern:** BaseRepository<T> for CRUD, specialized repos extend it
- **Pydantic everywhere:** Request validation, response models, config
- **Dependency injection:** FastAPI `Depends()` for DB sessions, services, auth
- **Context managers:** `get_db_context()` for transaction handling (auto-commit/rollback)
- **JSON columns:** Extensive use of PostgreSQL JSONB for flexible metadata (strategy params, tags)
- **Response envelope:** All API responses wrapped via ResponseWrapperMiddleware → `{success, data, meta}`

### Frontend (Next.js/TypeScript)
- **App Router:** Next.js 14 with server components
- **Atomic UI:** components/ui/ base components using CVA for variants
- **Domain components:** Feature folders (dashboard, laboratory, signals)
- **Hooks pattern:** useApi/useMutation for HTTP, domain hooks for feature logic
- **WebSocket safety:** useWebSocketSafe with MockWebSocket for testing
- **Render wrapper:** renderWithProviders (Auth, Query, Router, Toast contexts)
- **Tailwind utility:** `cn()` function from clsx + tailwind-merge

### Testing
- **Backend:** Pytest with pytest-asyncio (auto mode)
- **Frontend:** Jest (unit/integration) + Playwright (E2E, accessibility)
- **MSW:** Mock Service Worker for API mocking in frontend tests
- **Workflow tests:** Integration tests organized by user workflows (backtest, paper-trade)

### Formatting/Linting
- **Python:** Black (100 char line limit), Ruff (target 3.11)
- **TypeScript:** Prettier (no semicolons, single quotes, 100 char width)
- **ESLint:** next/core-web-vitals + next/typescript

## ANTI-PATTERNS (THIS PROJECT)

### Workflow
- **Never** add functionality beyond current test/task requirements (scope creep)
- **Never** add unrequested "helpful" features
- **Never** delete/edit files without reading contents first
- **Never** proceed without explicit "APPROVED" comments from Architect (multi-agent workflow)
- **Never** anticipate future tests or guess requirements

### Architectural
- **"And" functions:** Split any function requiring "and" in description
- **Multi-tasking functions:** One task per function, one function per file when possible
- **Premature optimization:** Only optimize after functional completion + tests
- **Data assumptions:** Validate inputs, handle edge cases (Fail Fast)

### Technical
- **Hardcoded secrets:** API keys must remain local (never shared/hardcoded)
- **Side-effect pollution:** DB ops must not affect tables outside scope
- **Sync I/O in endpoints:** Non-async I/O is an anti-pattern
- **Positive drawdown:** Backtest drawdown MUST be negative (logic error)
- **Pycache in Git:** __pycache__ files are tracked (violates .gitignore)

### Legacy
- **Legacy mocking:** addListener/removeListener in Jest are deprecated
- **Outdated tools:** package-lock.json shows deprecated dependencies (Glob < v9, Rimraf < v4)

## UNIQUE STYLES

### Backend
- **God Module:** services/ml_factory.py (1552 lines) combines model architecture + training + feature engineering (needs split)
- **Fat routers:** api/shadow.py (1297 lines), api/strategies.py (1122 lines) mix routing + Pydantic models + logic
- **Dual model layers:** Both /models/ and /database/models/ exist (redundancy risk)

### Frontend
- **Type bottleneck:** frontend/src/types/api.ts (1446 lines) - monolithic type dump
- **Component overload:** ModernCharts.tsx (1186 lines), ModernWidgets.tsx (1154 lines) export 5-8 components each
- **UI mode duality:** "Game Mode" vs "Pro Mode" - same logic, different terminology/styling via uiMode prop
- **Node-based strategies:** ReactFlow visual composer with typed ports (Boolean, Number, Signal)

### Infrastructure
- **Multi-exchange failover:** Binance (primary) → CoinGecko (secondary) → Kraken/KuCoin/Bybit (fallback)
- **Custom task queue:** SQLite-backed background_tasks.py for long-running ops
- **Gap detection:** HistoricalDataManager actively identifies missing candles and backfills

## COMMANDS

```bash
# Development
./run_dev.sh              # Start backend (venv, uvicorn)
cd frontend && npm run dev  # Start Next.js dev server

# Backend
docker-compose up -d        # Start TimescaleDB + Redis
pytest tests/               # Run backend tests
ruff check .              # Lint Python
black .                   # Format Python

# Frontend
cd frontend
npm test                  # Jest unit/integration
npm run test:e2e          # Playwright E2E
npm run lint              # ESLint
npm run format            # Prettier

# Database
python database/migrate.py upgrade   # Run pending migrations
python database/seed.py           # Seed initial data

# Contract testing
npm run test:contract       # Verify API contract + OpenAPI schema
```

## NOTES

### Cleanup Needed
- Remove artifact files: =1.24.0, nul, C:Users/matt/AppData/Local/
- Fix python-version: 3.14 (doesn't exist) in CI/CD workflows
- Remove continue-on-error: true from critical test/lint steps
- Consolidate /models/ and /database/models/

### Architecture Debt
- Split services/ml_factory.py into package (models/, engine/, features/, factory/)
- Split frontend/src/types/api.ts into domain files (strategies/, whale/, market/, ml/)
- Extract Pydantic models from api/*.py to models/
- Split ModernCharts.tsx/ModernWidgets.tsx into individual component files

### Security
- require_admin in api/admin/routes.py is a placeholder (accepts any token)
- No frontend route guard for admin pages (relies on 401/403)

### CI/CD
- Unpinned GitHub Actions (@main versions)
- Fragile service startup (hardcoded sleep 10 vs health check)
- Redundant pip install in contract-test.yml

### Domain Patterns
- **Strategy composition:** Layers + Logic Gates (AND/OR/WEIGHTED) for ensemble decisions
- **Backtest realism:** Slippage + commission injected on every trade
- **Whale tracking:** Ranking + pattern detection (ACCUMULATOR, DISTRIBUTOR, SNIPER, MANIPULATOR)
- **Node editor:** Topological sort for execution order, type-safe port connections
- **Real-time:** Hybrid polling (5-min cache) + WebSocket streaming
