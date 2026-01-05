# Data Initialization System - Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STOCKTRADE Platform                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer (FastAPI)                          │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │           Admin Data API (/api/v1/admin/data)                │  │   │
│  │  │                                                              │  │   │
│  │  │  POST /initialize    POST /sync    GET /status               │  │   │
│  │  │  POST /refresh/{id}  GET /tasks/{id}  GET /tasks             │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Service Layer                                 │   │
│  │                                                                      │   │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                │   │
│  │  │  Data Initializer    │  │   Exchange Sync      │                │   │
│  │  │                      │  │                      │                │   │
│  │  │  • is_initialized()  │  │  • sync_binance()    │                │   │
│  │  │  • init_exchanges()  │  │  • sync_coingecko()  │                │   │
│  │  │  • init_coins()      │  │  • sync_all()        │                │   │
│  │  │  • init_templates()  │  │  • get_status()      │                │   │
│  │  └──────────────────────┘  └──────────────────────┘                │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │              Background Tasks (TaskQueue)                    │  │   │
│  │  │                                                              │  │   │
│  │  │  • create_task()  • run_task()  • get_task()  • cleanup()   │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      External APIs                                   │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │   │
│  │  │     Binance      │  │   CoinGecko      │  │   Kraken*        │  │   │
│  │  │                  │  │                  │  │                  │  │   │
│  │  │  /api/v3/exchange│  │  /api/v3/coins   │  │  /0/public/      │  │   │
│  │  │  /api/v3/ticker  │  │  /coins/markets  │  │                  │  │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Database (SQLite)                               │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌─────────────┐        │   │
│  │  │exchanges │ │  coins   │ │trading_pairs │ │   templates │        │   │
│  │  └──────────┘ └──────────┘ └──────────────┘ └─────────────┘        │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │sync_status   │ │sync_locks    │ │system_metadata│                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  │  ┌──────────────────────────────────────────────────────┐          │   │
│  │  │            background_tasks                           │          │   │
│  │  └──────────────────────────────────────────────────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  Admin Data Page (/admin/data)                       │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │Initialize   │  │Sync All     │  │Refresh      │                 │   │
│  │  │Button       │  │Button       │  │Controls     │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Metrics Dashboard                         │  │   │
│  │  │                                                              │  │   │
│  │  │  Exchanges: 3    Coins: 15    Pairs: 150+    Templates: 3    │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                  Exchange Sync Status Cards                  │  │   │
│  │  │                                                              │  │   │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │   │
│  │  │  │  Binance   │  │CoinGecko   │  │  Kraken    │             │  │   │
│  │  │  │ ✓ Success  │  │ ✓ Success  │  │ • Pending  │             │  │   │
│  │  │  │ 150 pairs  │  │ 250 coins  │  │            │             │  │   │
│  │  │  │ 2m ago     │  │ 5m ago     │  │ Never      │             │  │   │
│  │  │  └────────────┘  └────────────┘  └────────────┘             │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Initialization Flow

```
User Request (POST /initialize)
         │
         ▼
API Endpoint Handler
         │
         ├─► Check if already initialized
         │
         ├─► initialize_exchanges()
         │    └─► INSERT INTO exchanges
         │
         ├─► initialize_coins()
         │    └─► INSERT INTO coins
         │
         ├─► initialize_trading_pairs()
         │    └─► INSERT INTO trading_pairs
         │
         └─► initialize_templates()
              └─► INSERT INTO strategy_templates
         │
         ▼
Update system_metadata
         │
         ▼
Return results to user
```

### Sync Flow

```
User Request (POST /sync)
         │
         ▼
API Endpoint Handler
         │
         ├─► Create background task
         │
         ├─► Return task_id immediately
         │
         ▼
Background Task Execution
         │
         ├─► Acquire sync lock
         │
         ├─► Fetch from exchange API
         │    │
         │    ├─► Binance: /api/v3/exchangeInfo
         │    └─► CoinGecko: /api/v3/coins/markets
         │
         ├─► Process and insert data
         │    │
         │    ├─► Check for existing records
         │    ├─► INSERT new records
         │    └─► Update sync_status
         │
         ├─► Release sync lock
         │
         └─► Mark task complete
         │
         ▼
Frontend polls task status
         │
         ▼
Display results to user
```

## Component Interactions

### 1. Startup Flow

```
FastAPI App Start
         │
         ▼
lifespan() function
         │
         ├─► init_db()
         │
         ├─► Check AUTO_INITIALIZE_DATA
         │    │
         │    └─► If true and not initialized:
         │         └─► initialize_reference_data()
         │
         └─► App ready
```

### 2. API Request Flow

```
Frontend Request
         │
         ▼
FastAPI Router (/api/v1/admin/data)
         │
         ▼
Endpoint Handler (e.g., sync())
         │
         ├─► Validate request
         │
         ├─► Call service layer
         │    │
         │    ├─► ExchangeSync.sync_all_exchanges()
         │    │    │
         │    │    └─► Returns task_id
         │    │
         │    └─► BackgroundTasks.create_task()
         │
         └─► Return response (task_id)
```

### 3. Background Task Flow

```
TaskQueue.create_task()
         │
         ▼
Task created in DB (status: pending)
         │
         ▼
auto_run=True → asyncio.create_task()
         │
         ▼
Task execution (status: running)
         │
         ├─► Execute function
         │    │
         │    ├─► Success → status: success
         │    ├─► Failed → status: failed
         │    └─► Cancelled → status: cancelled
         │
         ├─► Update task in DB
         │
         └─► Frontend polls status
```

## Key Design Decisions

### 1. Extensibility

- **Plugin Architecture**: Add new exchanges by implementing sync methods
- **Configuration-Driven**: Exchanges defined in config, not hardcoded
- **Status Tracking**: All exchanges use same sync status table

### 2. Reliability

- **Database Locks**: Prevent concurrent syncs of same exchange
- **Task Persistence**: Tasks survive server restarts
- **Error Handling**: Detailed error messages in sync_status

### 3. Performance

- **Async Operations**: All sync operations are async
- **Background Tasks**: Long-running ops don't block API
- **Incremental Updates**: Only insert new records

### 4. Monitoring

- **Quality Metrics**: Track data completeness
- **Sync History**: Last sync time, duration, records
- **Task Progress**: Real-time progress tracking

## Extension Points

### Adding New Exchange

1. **Define Exchange Config** (data_initializer.py)
2. **Implement Sync Method** (exchange_sync.py)
3. **Add Router Logic** (exchange_sync.sync_exchange)
4. **Update UI** (optional - admin/data/page.tsx)

### Adding New Metrics

1. **Query in get_data_quality_metrics()**
2. **Add to response schema**
3. **Display in UI cards**

### Adding New Background Task Type

1. **Define task function**
2. **Use run_background_task() helper**
3. **Poll task status from frontend**

## Security Considerations

- **API Keys**: Store in environment variables
- **Rate Limits**: Respect exchange rate limits
- **Input Validation**: Validate all user inputs
- **Error Messages**: Don't expose sensitive data

## Performance Considerations

- **Batch Inserts**: Insert multiple records at once
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache exchange API responses
- **Pagination**: Paginate large API responses
