# Market Data Storage System

## Overview

The Market Data Storage System provides a comprehensive infrastructure for managing cryptocurrency market metadata including coins, exchanges, trading pairs, and cached price data.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (api/markets.py)              │
│  - GET /api/v1/markets              - Market overview       │
│  - GET /api/v1/markets/coins        - List coins            │
│  - GET /api/v1/markets/coins/{sym}  - Coin details          │
│  - GET /api/v1/markets/exchanges    - List exchanges        │
│  - GET /api/v1/markets/pairs        - Trading pairs         │
│  - POST /api/v1/markets/sync        - Sync from exchanges   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Layer (services/market_data_manager.py) │
│  - MarketDataManager                                        │
│  - sync_coins_from_exchange()                               │
│  - update_price_cache()                                     │
│  - get_market_overview()                                    │
│  - search_coins()                                           │
│  - get_popular_coins()                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Repository Layer (database/repositories/market.py) │
│  - CoinRepository                                           │
│  - ExchangeRepository                                       │
│  - MarketPairRepository                                     │
│  - StoredPriceDataRepository                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Model Layer (models/market.py)                 │
│  - Coin (Pydantic)                                          │
│  - Exchange (Pydantic)                                      │
│  - MarketPair (Pydantic)                                    │
│  - StoredPriceData (Pydantic)                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           ORM Layer (database/models/market.py)             │
│  - CoinModel (SQLAlchemy)                                   │
│  - ExchangeModel (SQLAlchemy)                               │
│  - MarketPairModel (SQLAlchemy)                             │
│  - StoredPriceDataModel (SQLAlchemy)                        │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Coins Table

Stores metadata about tradeable assets/cryptocurrencies.

```sql
CREATE TABLE coins (
    id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) DEFAULT 'crypto',
    base_currency VARCHAR(20),
    quote_currency VARCHAR(20),
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    coingecko_id VARCHAR(100),
    coinmarketcap_id VARCHAR(100),
    market_cap NUMERIC(20,2),
    volume_24h NUMERIC(20,2),
    circulating_supply NUMERIC(20,2),
    total_supply NUMERIC(20,2),
    logo_url TEXT,
    website TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coins_symbol ON coins(symbol);
CREATE INDEX idx_coins_type ON coins(type);
CREATE INDEX idx_coins_exchange ON coins(exchange);
CREATE INDEX idx_coins_symbol_active ON coins(symbol, is_active);
```

### Exchanges Table

Stores exchange metadata and API configuration.

```sql
CREATE TABLE exchanges (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(10) DEFAULT 'cex',
    api_endpoint TEXT,
    websocket_endpoint TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    api_key VARCHAR(500),
    api_secret VARCHAR(500),
    rate_limit_per_minute INTEGER,
    rate_limit_per_second INTEGER,
    supports_websocket BOOLEAN DEFAULT FALSE,
    supports_rest BOOLEAN DEFAULT TRUE,
    supports_historical BOOLEAN DEFAULT FALSE,
    logo_url TEXT,
    website TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exchanges_type ON exchanges(type);
CREATE INDEX idx_exchanges_active ON exchanges(is_active);
```

### Market Pairs Table

Links base and quote coins on specific exchanges.

```sql
CREATE TABLE market_pairs (
    id VARCHAR(50) PRIMARY KEY,
    exchange_id VARCHAR(50) REFERENCES exchanges(id),
    base_coin_id VARCHAR(20) REFERENCES coins(symbol),
    quote_coin_id VARCHAR(20) REFERENCES coins(symbol),
    symbol VARCHAR(50),
    min_tick_size NUMERIC(20,8),
    min_lot_size NUMERIC(20,8),
    max_lot_size NUMERIC(20,8),
    current_price NUMERIC(20,8),
    volume_24h NUMERIC(20,2),
    price_change_24h_percent NUMERIC(10,4),
    is_active BOOLEAN DEFAULT TRUE,
    is_trading BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_pairs_exchange ON market_pairs(exchange_id, is_active);
CREATE INDEX idx_market_pairs_base_quote ON market_pairs(base_coin_id, quote_coin_id);
CREATE INDEX idx_market_pairs_symbol ON market_pairs(symbol);
```

### Cached Prices Table

Stores recent price data with TTL for fast access.

```sql
CREATE TABLE cached_prices (
    id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(20),
    exchange VARCHAR(50),
    price NUMERIC(20,8) NOT NULL,
    bid_price NUMERIC(20,8),
    ask_price NUMERIC(20,8),
    volume_24h NUMERIC(20,2),
    price_change_24h NUMERIC(20,8),
    price_change_percent_1h NUMERIC(10,4),
    price_change_percent_24h NUMERIC(10,4),
    price_change_percent_7d NUMERIC(10,4),
    market_cap NUMERIC(20,2),
    market_cap_rank INTEGER,
    ttl_seconds INTEGER DEFAULT 60,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cached_prices_symbol_exchange ON cached_prices(symbol, exchange);
CREATE INDEX idx_cached_prices_updated ON cached_prices(updated_at);
```

## API Endpoints

### Market Overview

```http
GET /api/v1/markets
```

Returns market summary including total coins, exchanges, pairs, and top performers.

**Response:**
```json
{
  "total_coins": 15,
  "active_coins": 15,
  "total_exchanges": 3,
  "active_exchanges": 3,
  "total_pairs": 6,
  "active_pairs": 6,
  "total_market_cap": 2500000000000,
  "total_24h_volume": 100000000000,
  "top_gainers_24h": [...],
  "top_losers_24h": [...],
  "top_by_volume": [...],
  "top_by_market_cap": [...]
}
```

### Coins

```http
GET /api/v1/markets/coins?type=crypto&limit=100&sort_by=market_cap
```

Query parameters:
- `type`: Asset type filter (crypto, stock, forex)
- `exchange`: Filter by exchange
- `active_only`: Only active coins (default: true)
- `limit`: Max results (1-500)
- `sort_by`: Sort field (market_cap, volume, symbol)

### Coin Details

```http
GET /api/v1/markets/coins/{symbol}
```

### Search Coins

```http
GET /api/v1/markets/coins/search/{query}?limit=50
```

### Popular Coins

```http
GET /api/v1/markets/coins/popular?by=market_cap&limit=100
```

Query parameters:
- `by`: Sort metric (market_cap, volume, gainers, losers)
- `limit`: Max results

### Exchanges

```http
GET /api/v1/markets/exchanges?type=cex&active_only=true
```

### Trading Pairs

```http
GET /api/v1/markets/pairs?base_coin=BTC&quote_coin=USDT&exchange=binance&limit=100
```

### Sync Market Data

```http
POST /api/v1/markets/sync
```

Body:
```json
{
  "exchange": "coingecko",
  "force_refresh": false,
  "include_historical": false
}
```

### Update Price Cache

```http
POST /api/v1/markets/cache/update?symbols=BTC,ETH,SOL
```

## Usage Examples

### Python Client

```python
import httpx

# Get market overview
response = httpx.get("http://localhost:8000/api/v1/markets")
overview = response.json()
print(f"Total coins: {overview['total_coins']}")

# Get coins by type
response = httpx.get("http://localhost:8000/api/v1/markets/coins?type=crypto&limit=10")
coins = response.json()
for coin in coins:
    print(f"{coin['symbol']}: {coin['name']} - ${coin.get('market_cap', 0):,.0f}")

# Search coins
response = httpx.get("http://localhost:8000/api/v1/markets/coins/search/bitcoin")
results = response.json()

# Get trading pairs
response = httpx.get("http://localhost:8000/api/v1/markets/pairs?base_coin=BTC&quote_coin=USDT")
pairs = response.json()

# Sync from exchange
response = httpx.post("http://localhost:8000/api/v1/markets/sync", json={
    "exchange": "coingecko",
    "force_refresh": False
})
sync_result = response.json()
print(f"Synced {sync_result['coins_added']} new coins")
```

### Service Layer

```python
from services.market_data_manager import get_market_data_manager

manager = get_market_data_manager()

# Get market overview
overview = manager.get_market_overview()

# Search coins
coins = manager.search_coins("bitcoin", limit=10)

# Get popular coins
top_coins = manager.get_popular_coins(by="market_cap", limit=100)

# Get trading pairs
pairs = manager.get_available_pairs(base_coin="BTC", quote_coin="USDT")

# Sync from exchange
sync_result = manager.sync_coins_from_exchange(exchange="coingecko")

# Update price cache
updated = manager.update_price_cache(symbols=["BTC", "ETH", "SOL"])
```

## Database Migration

To create the tables in your database:

```bash
# Run the migration
python -m alembic upgrade head

# Or use the migrate script
python database/migrate.py
```

## Seeding Initial Data

Populate the database with common cryptocurrency data:

```bash
python database/seed_market_data.py
```

This will seed:
- 3 exchanges (CoinGecko, Binance, Uniswap V3)
- 15 popular cryptocurrencies
- 6 common trading pairs

## Repository Methods

### CoinRepository

```python
# Get by symbol
coin = coin_repo.get_by_symbol("BTC")

# Get active coins
coins = coin_repo.get_active_coins(limit=100)

# Get coins by type
crypto_coins = coin_repo.get_coins_by_type("crypto")

# Get coins by exchange
binance_coins = coin_repo.get_coins_by_exchange("binance")

# Search coins
results = coin_repo.search_coins("bitcoin")

# Upsert (insert or update)
coin_repo.upsert_coin({"symbol": "BTC", "name": "Bitcoin"})

# Bulk upsert
coin_repo.bulk_upsert_coins([...])

# Top by market cap
top_coins = coin_repo.get_top_by_market_cap(limit=100)

# Top gainers/losers
gainers = coin_repo.get_top_gainers_24h(limit=20)
losers = coin_repo.get_top_losers_24h(limit=20)
```

### ExchangeRepository

```python
# Get by ID
exchange = exchange_repo.get("binance")

# Get active exchanges
exchanges = exchange_repo.get_active_exchanges()

# Get by type
cex_exchanges = exchange_repo.get_by_type("cex")

# Get exchanges with WebSocket
ws_exchanges = exchange_repo.get_exchanges_with_websocket()

# Upsert
exchange_repo.upsert_exchange({...})
```

### MarketPairRepository

```python
# Get by symbol
pair = pair_repo.get_by_symbol("BTC/USDT")

# Get pairs by exchange
binance_pairs = pair_repo.get_by_exchange("binance")

# Get available pairs
pairs = pair_repo.get_available_pairs(base_coin="BTC", quote_coin="USDT")

# Get pairs for a coin
btc_pairs = pair_repo.get_pairs_for_coin("BTC")

# Upsert
pair_repo.upsert_pair({...})

# Top pairs by volume
top_pairs = pair_repo.get_top_pairs_by_volume(limit=100)
```

### StoredPriceDataRepository

```python
# Get latest price
price = price_cache_repo.get_latest_price("BTC", exchange="binance")

# Get stale prices
stale = price_cache_repo.get_stale_prices(stale_seconds=60)

# Upsert price cache
price_cache_repo.upsert_price({...})

# Bulk upsert
price_cache_repo.bulk_upsert_prices([...])

# Delete stale prices
deleted = price_cache_repo.delete_stale_prices(stale_seconds=3600)
```

## Scaling Considerations

### Indexing Strategy

- Composite indexes on common query patterns (symbol + is_active)
- Separate indexes for filtering (type, is_active)
- Covering indexes for sorting (market_cap DESC)

### Caching Strategy

- Price cache with configurable TTL (default 60 seconds)
- Automatic cleanup of stale entries
- In-memory caching layer can be added (Redis)

### Data Partitioning

For large-scale deployments:

1. **Horizontal Partitioning by Exchange**
   - Each exchange gets its own partition
   - Queries filtered by exchange are faster

2. **Time-based Partitioning for Prices**
   - Cached prices partitioned by date
   - Old data can be archived efficiently

3. **Read Replicas**
   - Write operations go to primary
   - Read operations go to replicas
   - Reduces load on primary database

### Performance Optimization

1. **Bulk Operations**
   - Use `bulk_upsert_*` methods for multiple records
   - Reduces database round trips

2. **Query Optimization**
   - Use specific filters instead of fetching all
   - Limit result sets with pagination

3. **Connection Pooling**
   - Configure appropriate pool size
   - Reuse connections efficiently

## Security Considerations

1. **API Credentials**
   - Store API keys/secrets encrypted
   - Use environment variables for sensitive data
   - Never commit credentials to version control

2. **Rate Limiting**
   - Respect exchange rate limits
   - Implement exponential backoff
   - Cache data to reduce API calls

3. **Input Validation**
   - All inputs validated via Pydantic models
   - SQL injection protection via SQLAlchemy
   - Type safety with Python type hints

## Future Enhancements

1. **Additional Exchanges**
   - Coinbase Pro
   - Kraken
   - OKX
   - Bybit

2. **Advanced Features**
   - Real-time WebSocket price feeds
   - Order book data storage
   - Funding rates for perpetual futures
   - Liquidation cascade tracking

3. **Analytics**
   - Historical correlation analysis
   - Market sentiment indicators
   - On-chain metrics integration

4. **Multi-asset Support**
   - Stock market data
   - Forex pairs
   - Commodity futures
   - Index funds

## Troubleshooting

### Sync Fails

```python
# Check exchange is active
exchange = exchange_repo.get("coingecko")
assert exchange.is_active

# Check API credentials
assert exchange.api_key or exchange.api_endpoint

# Check rate limits
print(f"Rate limit: {exchange.rate_limit_per_minute}/min")
```

### Price Cache Outdated

```python
# Check cache age
price = price_cache_repo.get_latest_price("BTC")
age = datetime.utcnow() - price.updated_at
if age.total_seconds() > 60:
    # Update cache
    manager.update_price_cache(symbols=["BTC"])
```

### Database Connection Issues

```python
# Test connection
from database.connection import test_connection
test_connection()

# Check pool settings
from database.connection import engine
print(f"Pool size: {engine.pool.size()}")
```

## Files Created

1. **models/market.py** - Pydantic models for market data
2. **database/models/market.py** - SQLAlchemy ORM models
3. **database/repositories/market.py** - Repository implementations
4. **services/market_data_manager.py** - High-level service
5. **api/markets.py** - FastAPI endpoints
6. **database/migrations/versions/add_market_tables.py** - Migration script
7. **database/seed_market_data.py** - Seed data script

## Integration with Existing Code

The market data system integrates seamlessly with existing code:

- **services/market_data.py** - Historical price data fetching
- **api/market_data.py** - Price data endpoints (OHLCV)
- **models/market_data.py** - Price data models

The new system focuses on metadata while the existing system handles time-series price data.
