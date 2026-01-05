# Data Initialization and Synchronization System

## Overview

The STOCKTRADE project includes a comprehensive data initialization and synchronization system for managing reference data from cryptocurrency exchanges. This system handles:

- Initial setup of exchanges, coins, trading pairs, and strategy templates
- Ongoing synchronization with external APIs (Binance, CoinGecko)
- Background task processing for long-running sync operations
- Data quality metrics and monitoring
- Extensible architecture for adding new exchanges

## Architecture

```
STOCKTRADE/
├── services/
│   ├── data_initializer.py      # Core initialization logic
│   ├── exchange_sync.py         # Exchange synchronization
│   └── background_tasks.py      # Task queue and management
├── api/admin/
│   └── data.py                  # Admin API endpoints
├── frontend/src/app/admin/data/
│   └── page.tsx                 # Admin UI
└── tests/
    └── test_data_initialization.py  # Test suite
```

## Components

### 1. Data Initializer Service (`services/data_initializer.py`)

Handles first-run initialization of reference data.

#### Key Functions

- `is_initialized()` - Check if system has been initialized
- `initialize_exchanges()` - Set up default exchanges (Binance, CoinGecko, Kraken)
- `initialize_coins()` - Populate common cryptocurrencies (BTC, ETH, SOL, etc.)
- `initialize_trading_pairs()` - Create default trading pairs
- `initialize_templates()` - Load strategy templates
- `initialize_reference_data()` - Master initialization function
- `get_initialization_status()` - Get current initialization state

#### Default Data

**Exchanges:**
- Binance (CEX with spot and futures)
- CoinGecko (aggregator)
- Kraken (CEX, disabled by default)

**Coins (15 default):**
BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, LTC, BCH

**Trading Pairs:**
- BTC/USDT, ETH/USDT, SOL/USDT on Binance

**Strategy Templates:**
- SMA Crossover
- RSI Reversal
- MACD Momentum

### 2. Exchange Sync Service (`services/exchange_sync.py`)

Handles synchronization with external exchanges.

#### Class: ExchangeSync

**Methods:**
- `sync_binance_pairs()` - Sync trading pairs from Binance API
- `sync_coingecko_listings()` - Sync coin listings from CoinGecko API
- `sync_exchange(exchange_id)` - Sync specific exchange
- `sync_all_exchanges(exchanges)` - Sync multiple exchanges
- `get_sync_status(exchange_id)` - Get sync status
- `get_data_quality_metrics()` - Get quality metrics

#### Sync Status Tracking

The system tracks:
- Last sync timestamp
- Records synchronized
- Sync duration
- Error messages
- Current status (pending, running, success, failed)

#### Locking Mechanism

Prevents concurrent syncs of the same exchange using database locks.

### 3. Background Tasks Service (`services/background_tasks.py`)

Provides async task queue for long-running operations.

#### Class: TaskQueue

**Methods:**
- `create_task(name, func, args, kwargs, auto_run)` - Create new task
- `run_task(task_id)` - Start task execution
- `get_task(task_id)` - Get task status
- `get_all_tasks(status)` - List all tasks
- `update_progress(task_id, progress, message)` - Update progress
- `cancel_task(task_id)` - Cancel pending task
- `cleanup_old_tasks(max_age_hours, keep_recent)` - Remove old tasks

#### Task Status Flow

```
pending -> running -> success
                      -> failed
                      -> cancelled
```

#### Persistence

Tasks are persisted to database for recovery after restart.

### 4. Admin API (`api/admin/data.py`)

RESTful API endpoints for data management.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/admin/data/initialize` | Initialize all reference data |
| POST | `/api/v1/admin/data/sync` | Trigger exchange synchronization |
| POST | `/api/v1/admin/data/refresh/{exchange_id}` | Refresh specific exchange |
| GET | `/api/v1/admin/data/status` | Get data status and metrics |
| GET | `/api/v1/admin/data/sync/{exchange_id}` | Get exchange sync status |
| GET | `/api/v1/admin/data/tasks/{task_id}` | Get task status |
| GET | `/api/v1/admin/data/tasks` | List all tasks |
| POST | `/api/v1/admin/data/tasks/cleanup` | Clean up old tasks |
| GET | `/api/v1/admin/data/metrics/quality` | Get quality metrics |

#### Request/Response Models

```python
class InitializeRequest(BaseModel):
    force: bool = False
    components: Optional[List[str]] = None

class SyncRequest(BaseModel):
    exchanges: Optional[List[str]] = None
    force: bool = False

class DataStatusResponse(BaseModel):
    initialized: bool
    initialized_at: Optional[str]
    data_counts: dict
    sync_status: Optional[list]
    quality_metrics: Optional[dict]
```

### 5. Admin UI (`frontend/src/app/admin/data/page.tsx`)

React-based admin interface for data management.

#### Features

- Data initialization status display
- One-click initialization button
- Sync all exchanges button
- Per-exchange sync controls
- Real-time task progress tracking
- Data quality metrics dashboard
- Exchange sync status cards
- Trading pairs by exchange table

#### UI Components

- `StatusCard` - Metric display card
- `ExchangeSyncCard` - Per-exchange status and controls
- Toast notifications for operations

## Database Schema

### Tables Created

```sql
-- Exchanges
CREATE TABLE exchanges (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    api_base TEXT,
    ws_base TEXT,
    supports_spot BOOLEAN DEFAULT 0,
    supports_futures BOOLEAN DEFAULT 0,
    rate_limit INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coins
CREATE TABLE coins (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    coingecko_id TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Pairs
CREATE TABLE trading_pairs (
    id TEXT PRIMARY KEY,
    base_symbol TEXT NOT NULL,
    quote_symbol TEXT NOT NULL,
    exchange_id TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
    UNIQUE(base_symbol, quote_symbol, exchange_id)
);

-- Strategy Templates
CREATE TABLE strategy_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Metadata
CREATE TABLE system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync Status
CREATE TABLE sync_status (
    exchange_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    last_sync_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync Locks
CREATE TABLE sync_locks (
    exchange_id TEXT PRIMARY KEY,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_by TEXT DEFAULT 'system'
);

-- Background Tasks
CREATE TABLE background_tasks (
    task_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    message TEXT,
    result TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## Usage

### Manual Initialization

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/data/initialize \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

**Via Python:**
```python
from services.data_initializer import initialize_reference_data

result = initialize_reference_data()
print(f"Initialization: {result['success']}")
```

### Synchronization

**Sync all exchanges:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/data/sync \
  -H "Content-Type: application/json"
```

**Sync specific exchange:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/data/refresh/binance
```

**Via Python:**
```python
from services.exchange_sync import ExchangeSync

sync_service = ExchangeSync()
result = await sync_service.sync_binance_pairs()
print(f"Synced {result['records_synced']} pairs")
```

### Check Status

**Get overall status:**
```bash
curl http://localhost:8000/api/v1/admin/data/status
```

**Get exchange sync status:**
```bash
curl http://localhost:8000/api/v1/admin/data/sync/binance
```

**Via Python:**
```python
from services.data_initializer import get_initialization_status

status = get_initialization_status()
print(f"Initialized: {status['initialized']}")
print(f"Coins: {status['data_counts']['coins']}")
```

## Auto-Initialization on Startup

Set the environment variable to enable auto-initialization:

```bash
export AUTO_INITIALIZE_DATA=true
```

This will automatically initialize reference data on first API startup.

## Adding New Exchanges

### 1. Add Exchange to Defaults

In `services/data_initializer.py`:

```python
DEFAULT_EXCHANGES = [
    # ... existing exchanges
    {
        "id": "kraken",
        "name": "Kraken",
        "type": "cex",
        "enabled": True,
        "api_base": "https://api.kraken.com",
        "ws_base": "wss://ws.kraken.com",
        "supports_spot": True,
        "supports_futures": True,
        "rate_limit": 600,
    },
]
```

### 2. Implement Sync Method

In `services/exchange_sync.py`:

```python
async def sync_kraken_pairs(self) -> Dict[str, Any]:
    """Sync trading pairs from Kraken."""
    exchange_id = "kraken"
    start_time = datetime.utcnow()

    # Your sync logic here

    return {
        "exchange": exchange_id,
        "status": SyncStatus.SUCCESS.value,
        "records_synced": count,
        "duration_seconds": duration,
    }
```

### 3. Add to Router

Update `sync_exchange` method:

```python
async def sync_exchange(self, exchange_id: str):
    if exchange_id == "binance":
        return await self.sync_binance_pairs()
    elif exchange_id == "coingecko":
        return await self.sync_coingecko_listings()
    elif exchange_id == "kraken":
        return await self.sync_kraken_pairs()
    # ...
```

## Testing

Run the test suite:

```bash
pytest tests/test_data_initialization.py -v
```

### Test Coverage

- Data initialization functions
- Exchange sync operations
- Background task management
- API endpoints
- Integration workflows

## Monitoring

### Data Quality Metrics

Track:
- Total exchanges and enabled count
- Total coins and enabled count
- Trading pairs per exchange
- Sync success rates
- Sync durations

### Health Checks

Monitor:
- Last successful sync time
- Failed sync attempts
- Error messages
- Task queue backlog

## Best Practices

1. **Initialize First**: Always run initialization before first sync
2. **Sync Regularly**: Set up scheduled syncs (cron, celery beat)
3. **Monitor Errors**: Check sync status for failures
4. **Rate Limits**: Respect API rate limits to avoid bans
5. **Incremental Syncs**: Sync new data only when possible
6. **Background Tasks**: Use background tasks for long-running syncs
7. **Cleanup**: Regularly clean up old tasks and logs

## Troubleshooting

### Initialization Fails

- Check database permissions
- Verify tables don't already exist
- Check for constraint violations

### Sync Fails

- Verify API credentials
- Check network connectivity
- Review rate limit status
- Check API endpoint availability

### Tasks Stuck

- Check for crashed processes
- Verify database connectivity
- Review task error messages
- Cancel and retry stuck tasks

## Future Enhancements

- [ ] Webhook notifications for sync completion
- [ ] Scheduled automatic syncs
- [ ] Sync conflict resolution
- [ ] Data versioning and rollback
- [ ] Real-time sync progress via WebSocket
- [ ] Historical sync data retention
- [ ] Sync analytics and reporting
- [ ] Multi-region sync support
- [ ] Exchange failover mechanisms
