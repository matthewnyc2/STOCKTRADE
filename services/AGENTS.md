# SERVICES LAYER KNOWLEDGE

**Generated:** 2026-01-03

## OVERVIEW
Business logic core: BacktestEngine, MLFactory, StrategyManager, MultiSourceManager for real-time market data and strategy execution.

## STRUCTURE
```
services/
├── backtest_engine.py     # Historical simulation with slippage/commission
├── strategy_manager.py      # Strategy lifecycle, cloning, versioning
├── ml_factory.py          # ML model training (God module - needs split)
├── multi_source_manager.py  # Exchange failover (Binance → CoinGecko → fallbacks)
├── market_data_manager.py   # Price cache, OHLCV serving
├── historical_data_manager.py  # Gap detection, backfill orchestration
├── exchange_adapters.py    # Unified exchange API interface
├── background_tasks.py     # SQLite task queue for long-running ops
├── genetic_optimizer.py     # Strategy parameter evolution
├── liquidity_hunter.py     # Dark pool/liquidity analysis
├── constellation_detector.py  # Whale clustering (BFS algorithm)
└── dark_arbitrage.py       # Cross-exchange arbitrage scanning
```

## WHERE TO LOOK
| Task | Location | Notes |
|-------|----------|-------|
| Trading simulation | backtest_engine.py | Walk-forward with friction modeling |
| Strategy lifecycle | strategy_manager.py | Clone, snapshot, version management |
| ML orchestration | ml_factory.py | LSTM training, feature engineering (needs refactor) |
| Market resilience | multi_source_manager.py | Source priority, health tracking, failover |
| Data gaps | historical_data_manager.py | Detects missing candles, backfills |
| Real-time pipelines | data_pipeline.py | Buffer → Validator → Enricher → Storage |
| Long-running ops | background_tasks.py | Task queue with SQLite persistence |
| Whale patterns | constellation_detector.py | BFS clustering, pattern classification |

## CONVENTIONS

### Service Patterns
- **Manager/Orchestrator Pattern**: BacktestEngine, StrategyManager, MultiSourceManager
- **Configuration-Driven**: BacktestConfig, PipelineConfig separate params from logic
- **Singleton Access**: get_strategy_manager(), get_task_queue() for shared state
- **Context-Managed DB**: `with get_db_context() as session:` for transactions

### Dependency Injection
- **Web Layer**: FastAPI Depends() for services
- **Internal Composition**: Services instantiate own components (e.g., RealTimeDataPipeline creates validators)
- **Session Handling**: Most services use get_db_context() internally, not injected

### Real-Time & Async
- **All I/O Async**: External APIs, DB, WebSocket all use async/await
- **Background Tasks**: Offload to background_tasks.py for long-running (genetic optimization, backfill)
- **WebSocket Integration**: StrategyExecutor broadcasts via WebSocketManager

## ANTI-PATTERNS

### Architecture Debt
- **God Module**: services/ml_factory.py (1552 lines) - combines model architecture + training + features
- **Refactor**: Split into services/ml/ package (models.py, engine.py, features.py, factory.py)
- **Fat Routers**: api/*.py mix business logic that should be in services/
- **Rule**: Keep API thin - HTTP layer only, no domain logic
