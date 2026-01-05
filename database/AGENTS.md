# DATABASE LAYER KNOWLEDGE

**Generated:** 2026-01-03

## OVERVIEW
Data persistence: SQLAlchemy 2.0 with Repository Pattern, BaseRepository<T>, JSONB for flexible metadata, automatic migrations.

## STRUCTURE
```
database/
├── base.py                 # BaseRepository<T> generic CRUD
├── connection.py            # DatabaseConnection singleton, session management
├── migrate.py              # Custom migration runner
├── seed.py                 # Data seeding, initialization
├── models/                 # SQLAlchemy ORM definitions
│   ├── __init__.py         # BaseModel common fields (id, timestamps)
│   ├── strategy.py          # Strategy, StrategyLayer, Performance metrics
│   ├── backtest.py          # BacktestResult, Trade, EquityPoint
│   ├── user.py             # User, Auth credentials
│   ├── market.py           # Market, Coin, TradingPair
│   ├── price.py            # OHLCV candles (timescale data)
│   ├── signal.py           # Signal tracking, subscriptions
│   ├── whale.py            # WhaleWallet, WhaleMovement, patterns
│   └── ...
└── repositories/           # Domain-specific data access
    ├── strategy_repository.py
    ├── backtest_repository.py
    ├── user_repository.py
    ├── whale_repository.py
    └── ...
```

## WHERE TO LOOK
| Task | Location | Notes |
|-------|----------|-------|
| Generic CRUD | base.py | BaseRepository<T> with get, create, update, delete |
| Session management | connection.py | get_db_context(), auto-commit/rollback |
| Model definitions | models/*.py | SQLAlchemy 2.0 with Mapped types |
| Domain queries | repositories/*.py | Extended BaseRepository with complex queries |
| Migrations | migrations/versions/ | YYYYMMDDHHMMSS_description.py pattern |
| Seeding | seed.py | Initial data, strategy templates |

## CONVENTIONS

### Repository Pattern
- **Generic Base**: BaseRepository<T> provides create, get, get_many, update, delete, query
- **Domain Repos**: Inherit and extend (e.g., get_by_tag, search_by_filters)
- **Async Sessions**: Use `async with get_db_context() as session:` for transactions
- **Auto-Commit/Rollback**: Context manager ensures ACID compliance

### Model Patterns
- **Common Base**: All models inherit from BaseModel (id, created_at, updated_at)
- **JSONB Columns**: Extensive use for flexible metadata (strategy params, tags, metrics)
- **Mapped Types**: SQLAlchemy 2.0 syntax (`Mapped[str]`, `mapped_column`)
- **Foreign Keys**: Proper relationships with lazy/eager loading

### Session Management
- **Context Managers**: Preferred over manual session handling
- **Depends Injection**: FastAPI endpoints use `Depends(get_db)` for sessions
- **Service Layer**: Uses `get_db_context()` internally for transactions

## ANTI-PATTERNS

### Dual Model Layers
- **Redundancy**: Both /models/ (Pydantic) and /database/models/ (SQLAlchemy) exist
- **Risk**: Type mapping hell, logic duplication
- **Refactor**: Consolidate - use /database/models/ for persistence, /models/ for Pydantic only

### Anti-Patterns
- **Raw SQL in Repos**: Prefer SQLAlchemy ORM over text() queries unless performance-critical
- **Missing Migrations**: Always create migration after model changes
- **Sync I/O**: All DB operations must be async
- **PyCache in Git**: __pycache__ files tracked (violates .gitignore)
