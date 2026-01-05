# API LAYER KNOWLEDGE

**Generated:** 2026-01-03

## OVERVIEW
FastAPI routers organized by domain (auth, strategies, signals, backtests). ResponseWrapperMiddleware auto-wraps all JSON responses.

## STRUCTURE
```
api/
├── main.py           # FastAPI app, lifespan, middleware, router mounting
├── auth.py           # JWT, password hashing, user registration/login
├── strategies.py      # Strategy CRUD, lifecycle, favorite, clone (1122 lines - fat)
├── backtests.py       # Backtest execution, results, metrics
├── signals.py         # Signal generation, subscription, history
├── markets.py         # Market metadata, trading pairs, exchanges
├── market_data.py     # OHLCV data, current prices, historical
├── whales.py          # Whale wallet tracking, patterns, movements
├── genetic.py         # ML optimization trigger, task management
├── ml.py             # Model training, prediction endpoints
├── portfolio.py       # Portfolio data, P&L, allocation
├── liquidations.py    # Liquidation monitoring, alerts
├── shadow.py          # Dark arbitrage, cross-exchange scanning (1297 lines - fat)
├── admin/             # Admin sub-package
│   ├── routes.py      # System health, user management (886 lines)
│   └── data.py       # Data sync, exchange configuration
└── templates.py       # Strategy template CRUD, seeding
```

## WHERE TO LOOK
| Task | Location | Notes |
|-------|----------|-------|
| Auth flow | auth.py | JWT creation, password hashing, registration |
| Strategy management | strategies.py | CRUD, cloning, versioning, favorites |
| Backtest execution | backtests.py | Run backtests, retrieve results, metrics |
| Signal delivery | signals.py | Real-time generation, WebSocket broadcast |
| Market data API | market_data.py | OHLCV, current prices, caching |
| Admin endpoints | admin/routes.py | Health checks, user management |
| Data sync | admin/data.py | Background task orchestration, exchange sync |

## CONVENTIONS

### Router Patterns
- **APIRouter Grouping**: Each file exports router, mounted in main.py with prefix
- **Pydantic Validation**: All request/response use Pydantic models
- **Dependency Injection**: `Depends(get_db)`, `Depends(get_current_user)`, `Depends(require_admin)`
- **Response Models**: Endpoints define `response_model=...` for automatic serialization
- **Status Codes**: Appropriate HTTP codes (200, 201, 401, 403, 422)

### Response Envelope
- **Automatic Wrapping**: ResponseWrapperMiddleware wraps all JSON responses in `{success, data, meta}`
- **Manual Wraps**: Use `ApiResponse.success(data=...)` and `ApiResponse.error(...)` when needed

## ANTI-PATTERNS

### Fat Routers
- **Mixed Concerns**: api/shadow.py (1297 lines), api/strategies.py (1122 lines) combine routing + Pydantic models + business logic
- **Refactor**: Extract Pydantic models to models/*.py (e.g., models/shadow_schema.py)
- **Rule**: API layer = HTTP handling only. Move logic to services/

### Anti-Patterns
- **Inline Logic**: Complex calculations in endpoints (move to services/)
- **Pydantic in Routers**: Request/response models should be in models/, not inline
- **Controller Bloat**: Flat api/ directory (no sub-grouping) - consider api/v1/, api/v2/
