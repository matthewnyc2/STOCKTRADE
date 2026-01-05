# Data Initialization System - Quick Reference

## Quick Start

### 1. Initialize Data on First Run

```bash
# Set environment variable for auto-initialization
export AUTO_INITIALIZE_DATA=true

# Start the API server
python -m uvicorn api.main:app --reload
```

Or manually via API:

```bash
curl -X POST http://localhost:8000/api/v1/admin/data/initialize
```

### 2. Sync Exchanges

```bash
# Sync all enabled exchanges
curl -X POST http://localhost:8000/api/v1/admin/data/sync

# Sync specific exchange
curl -X POST http://localhost:8000/api/v1/admin/data/refresh/binance
```

### 3. Check Status

```bash
# Get overall status
curl http://localhost:8000/api/v1/admin/data/status

# Get exchange sync status
curl http://localhost:8000/api/v1/admin/data/sync/binance
```

## File Locations

| File | Purpose |
|------|---------|
| `services/data_initializer.py` | Initialization logic |
| `services/exchange_sync.py` | Exchange sync |
| `services/background_tasks.py` | Task queue |
| `api/admin/data.py` | Admin API |
| `frontend/src/app/admin/data/page.tsx` | Admin UI |

## Key Functions

### Data Initializer

```python
from services.data_initializer import (
    initialize_reference_data,  # Initialize everything
    get_initialization_status,  # Check status
    is_initialized,             # Boolean check
)

# Initialize
result = initialize_reference_data()
print(result['success'])

# Check status
status = get_initialization_status()
print(status['data_counts'])
```

### Exchange Sync

```python
from services.exchange_sync import ExchangeSync

sync = ExchangeSync()

# Sync specific exchange
result = await sync.sync_binance_pairs()

# Sync all exchanges
result = await sync.sync_all_exchanges()

# Get sync status
status = sync.get_sync_status('binance')

# Get quality metrics
metrics = sync.get_data_quality_metrics()
```

### Background Tasks

```python
from services.background_tasks import run_background_task

# Run task in background
task_id = await run_background_task(
    name="Sync Binance",
    func=sync.sync_binance_pairs,
    auto_run=True
)

# Check task status
queue = get_task_queue()
task = queue.get_task(task_id)
print(task['status'])
```

## API Endpoints

### POST /api/v1/admin/data/initialize

Initialize all reference data.

```json
{
  "force": false,
  "components": ["exchanges", "coins", "trading_pairs", "templates"]
}
```

### POST /api/v1/admin/data/sync

Trigger synchronization.

```json
{
  "exchanges": ["binance", "coingecko"],
  "force": false
}
```

### GET /api/v1/admin/data/status

Get data status.

```json
{
  "initialized": true,
  "initialized_at": "2026-01-01T00:00:00",
  "data_counts": {
    "exchanges": 3,
    "coins": 15,
    "trading_pairs": 6
  },
  "quality_metrics": { ... }
}
```

## Database Tables

| Table | Purpose |
|-------|---------|
| `exchanges` | Exchange configurations |
| `coins` | Cryptocurrency listings |
| `trading_pairs` | Trading pair mappings |
| `strategy_templates` | Strategy templates |
| `system_metadata` | Initialization tracking |
| `sync_status` | Sync status tracking |
| `sync_locks` | Sync operation locks |
| `background_tasks` | Background task queue |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_INITIALIZE_DATA` | `false` | Auto-initialize on startup |
| `COINGECKO_API_KEY` | `""` | CoinGecko API key |

## Adding New Exchange

1. Add to `DEFAULT_EXCHANGES` in `data_initializer.py`
2. Implement sync method in `ExchangeSync` class
3. Add routing in `sync_exchange()` method
4. Update API endpoints if needed

Example:

```python
# In data_initializer.py
DEFAULT_EXCHANGES.append({
    "id": "new_exchange",
    "name": "New Exchange",
    "type": "cex",
    "enabled": True,
    "api_base": "https://api.newexchange.com",
    "ws_base": "wss://ws.newexchange.com",
    "supports_spot": True,
    "supports_futures": False,
    "rate_limit": 100,
})

# In exchange_sync.py
async def sync_new_exchange_pairs(self):
    # Implementation
    pass

async def sync_exchange(self, exchange_id: str):
    # ... existing cases
    elif exchange_id == "new_exchange":
        return await self.sync_new_exchange_pairs()
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tables don't exist | Run initialization |
| Sync fails | Check API credentials, rate limits |
| Tasks stuck | Cancel and retry, check logs |
| Old data showing | Run sync, check last_sync_at |

## Testing

```bash
# Run all tests
pytest tests/test_data_initialization.py -v

# Run specific test
pytest tests/test_data_initialization.py::TestDataInitializer::test_initialize_exchanges -v
```

## UI Access

Navigate to: `http://localhost:3000/admin/data`

Features:
- Initialize data button
- Sync all exchanges button
- Per-exchange refresh buttons
- Status cards and metrics
- Task progress tracking
