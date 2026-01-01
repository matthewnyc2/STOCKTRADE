# API Documentation

## Overview

This document provides comprehensive documentation for the Crypto Quant Laboratory API. The API is built using FastAPI and provides RESTful endpoints for all platform functionality, along with WebSocket support for real-time data streaming.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.your-domain.com`

## Authentication

Currently, the API uses API key authentication for production deployments. Development mode allows open access.

### API Key Usage

Include your API key in the request headers:

```
Authorization: Bearer your-api-key-here
```

### Rate Limiting

- Default: 100 requests per minute per API key
- Can be configured via environment variables

## REST API Endpoints

### Health Check

#### GET /

Health check endpoint to verify service availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "crypto-quant-lab"
}
```

---

## API Modules

### 1. AI API (`/api/ai`)

Provides AI-powered market analysis and reasoning capabilities.

#### GET /api/ai/reasoning/{symbol}

Get AI reasoning and analysis for a specific symbol.

**Parameters:**
- `symbol` (path, required): Trading symbol (e.g., "BTCUSD")
- `timeframe` (query, optional): Analysis timeframe (default: "1h")

**Response:**
```json
{
  "symbol": "BTCUSD",
  "timeframe": "1h",
  "analysis": {
    "trend": "bullish",
    "confidence": 0.85,
    "key_levels": {
      "support": 42000,
      "resistance": 45000
    },
    "reasoning": "Technical indicators show strong upward momentum...",
    "recommendations": ["Buy on dips", "Stop loss at 41000"]
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### POST /api/ai/predict

Get AI predictions for price movements.

**Request Body:**
```json
{
  "symbol": "BTCUSD",
  "timeframe": "1h",
  "horizon": "24h",
  "features": {
    "rsi": 65.5,
    "macd": 150.3,
    "volume": 25000000
  }
}
```

**Response:**
```json
{
  "predictions": {
    "price_target": 46000,
    "probability": 0.72,
    "confidence_interval": [44000, 48000],
    "volatility_forecast": 0.15
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### 2. Backtests API (`/api/backtests`)

Comprehensive backtesting engine for trading strategies.

#### POST /api/backtests/create

Create and run a backtest.

**Request Body:**
```json
{
  "strategy_id": "strategy-123",
  "symbol": "BTCUSD",
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-12-31T23:59:59Z",
  "initial_capital": 10000,
  "parameters": {
    "stop_loss": 0.02,
    "take_profit": 0.05,
    "entry_threshold": 1.5
  }
}
```

**Response:**
```json
{
  "backtest_id": "backtest-456",
  "status": "running",
  "progress": 0.0,
  "estimated_completion": "2024-01-01T12:15:00Z"
}
```

#### GET /api/backtests/{backtest_id}

Get backtest status and results.

**Response:**
```json
{
  "backtest_id": "backtest-456",
  "status": "completed",
  "progress": 1.0,
  "results": {
    "total_return": 0.285,
    "sharpe_ratio": 1.45,
    "max_drawdown": 0.12,
    "win_rate": 0.62,
    "total_trades": 156,
    "profitable_trades": 97
  },
  "equity_curve": [
    {"date": "2023-01-01", "value": 10000},
    {"date": "2023-01-02", "value": 10150}
  ],
  "trades": [
    {
      "entry_date": "2023-01-01",
      "exit_date": "2023-01-05",
      "type": "long",
      "entry_price": 42000,
      "exit_price": 45000,
      "pnl": 714.29,
      "return": 0.0714
    }
  ]
}
```

#### GET /api/backtests

List all backtests with pagination.

**Query Parameters:**
- `page` (optional, default=1): Page number
- `limit` (optional, default=10): Results per page
- `status` (optional): Filter by status

**Response:**
```json
{
  "backtests": [
    {
      "id": "backtest-456",
      "strategy_name": "MA Crossover",
      "symbol": "BTCUSD",
      "status": "completed",
      "created_at": "2024-01-01T12:00:00Z",
      "total_return": 0.285
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25
  }
}
```

---

### 3. Genetic Algorithm API (`/api/genetic`)

Automated strategy optimization using genetic algorithms.

#### POST /api/genetic/optimize

Start genetic algorithm optimization.

**Request Body:**
```json
{
  "strategy_id": "strategy-123",
  "symbol": "BTCUSD",
  "population_size": 50,
  "generations": 100,
  "mutation_rate": 0.1,
  "fitness_function": "sharpe_ratio",
  "constraints": {
    "max_position_size": 0.1,
    "max_drawdown": 0.2
  }
}
```

**Response:**
```json
{
  "optimization_id": "gen-opt-789",
  "status": "running",
  "progress": 0.0,
  "best_fitness": 0.0,
  "population": []
}
```

#### GET /api/genetic/{optimization_id}

Get optimization progress and results.

**Response:**
```json
{
  "optimization_id": "gen-opt-789",
  "status": "completed",
  "progress": 1.0,
  "best_fitness": 1.45,
  "best_individual": {
    "parameters": {
      "short_ma": 10,
      "long_ma": 30,
      "rsi_threshold": 70,
      "stop_loss": 0.02
    },
    "fitness": 1.45,
    "backtest_id": "backtest-789"
  },
  "convergence_history": [
    {"generation": 0, "fitness": 0.5},
    {"generation": 10, "fitness": 0.9},
    {"generation": 20, "fitness": 1.2}
  ]
}
```

---

### 4. Liquidations API (`/api/liquidations`)

Real-time liquidation tracking and cascade prediction.

#### GET /api/liquidations/{symbol}

Get recent liquidations for a symbol.

**Query Parameters:**
- `limit` (optional, default=50): Number of liquidations to return

**Response:**
```json
{
  "symbol": "BTCUSD",
  "liquidations": [
    {
      "id": "liq-123",
      "side": "long",
      "price": 43000,
      "size": 0.5,
      "liquidated_price": 41000,
      "pnl": -1000,
      "timestamp": "2024-01-01T12:00:00Z",
      "exchange": "binance"
    }
  ]
}
```

#### GET /api/liquidations/cascade/{symbol}

Get cascade risk analysis.

**Response:**
```json
{
  "symbol": "BTCUSD",
  "current_price": 42500,
  "cascade_risk": "high",
  "liquidation_levels": [
    {
      "price": 42000,
      "liquidations": 250,
      "size": 1250,
      "cascade_probability": 0.8
    },
    {
      "price": 41000,
      "liquidations": 180,
      "size": 900,
      "cascade_probability": 0.6
    }
  ],
  "estimated_impact": {
    "worst_case": 0.15,
    "expected": 0.08,
    "best_case": 0.03
  }
}
```

---

### 5. Market Data API (`/api/market-data`)

Historical and real-time market data.

#### GET /api/market-data/klines/{symbol}

Get historical kline/candlestick data.

**Query Parameters:**
- `interval` (required): Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `limit` (optional, default=500): Number of candles
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp

**Response:**
```json
{
  "symbol": "BTCUSD",
  "interval": "1h",
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "open": 42000,
      "high": 42500,
      "low": 41800,
      "close": 42200,
      "volume": 25000
    }
  ]
}
```

#### GET /api/market-data/ticker/{symbol}

Get real-time ticker data.

**Response:**
```json
{
  "symbol": "BTCUSD",
  "last_price": 42200,
  "bid": 42190,
  "ask": 42210,
  "volume_24h": 25000000,
  "high_24h": 43000,
  "low_24h": 41000,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### 6. Machine Learning API (`/api/ml`)

Machine learning model endpoints.

#### POST /api/ml/train

Train a machine learning model.

**Request Body:**
```json
{
  "model_type": "lstm",
  "symbol": "BTCUSD",
  "features": ["close", "volume", "rsi", "macd"],
  "target": "price_change",
  "training_period": "6m",
  "hyperparameters": {
    "layers": 3,
    "units": 50,
    "dropout": 0.2
  }
}
```

**Response:**
```json
{
  "model_id": "ml-model-123",
  "status": "training",
  "accuracy": 0.0,
  "estimated_completion": "2024-01-01T14:00:00Z"
}
```

#### GET /api/ml/predict/{model_id}

Get predictions from a trained model.

**Response:**
```json
{
  "model_id": "ml-model-123",
  "predictions": [
    {
      "timestamp": "2024-01-02T12:00:00Z",
      "predicted_change": 0.02,
      "confidence": 0.75
    }
  ]
}
```

---

### 7. Portfolio API (`/api/portfolio`)

Portfolio management and analytics.

#### GET /api/portfolio

Get current portfolio status.

**Response:**
```json
{
  "total_value": 125000,
  "total_return": 0.25,
  "positions": [
    {
      "symbol": "BTCUSD",
      "quantity": 2.5,
      "entry_price": 40000,
      "current_price": 42200,
      "unrealized_pnl": 5500,
      "percentage": 0.75
    }
  ],
  "performance": {
    "daily": 0.015,
    "weekly": 0.08,
    "monthly": 0.22
  }
}
```

#### POST /api/portfolio/adjust

Adjust portfolio positions.

**Request Body:**
```json
{
  "symbol": "BTCUSD",
  "action": "buy",
  "size": 0.5,
  "type": "market",
  "price": null
}
```

---

### 8. Settings API (`/api/settings`)

Application settings management.

#### GET /api/settings

Get all user settings.

**Response:**
```json
{
  "notifications": {
    "email": true,
    "push": true,
    "liquidation_alerts": true
  },
  "trading": {
    "default_leverage": 10,
    "max_loss_per_trade": 0.02
  },
  "ui": {
    "theme": "dark",
    "chart_style": "candlestick"
  }
}
```

#### PUT /api/settings

Update user settings.

**Request Body:**
```json
{
  "notifications": {
    "email": false,
    "push": true
  }
}
```

---

### 9. Shadow API (`/api/shadow`)

Advanced liquidity hunting and market manipulation detection. See [LIQUIDITY_HUNTING_API.md](./LIQUIDITY_HUNTING_API.md) for detailed documentation.

#### Key Endpoints:
- `GET /api/shadow/liquidity-map/{symbol}`: Complete liquidity analysis
- `GET /api/shadow/sweep-probability/{symbol}`: Sweep probability prediction
- `GET /api/shadow/clusters/{symbol}`: Stop-loss clusters
- `GET /api/shadow/voids/{symbol}`: Liquidity voids
- `POST /api/shadow/cascade-risk/{symbol}`: Cascade risk calculation

---

### 10. Signals API (`/api/signals`)

Trading signals generation and management.

#### GET /api/signals

Get active trading signals.

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `type` (optional): Filter by signal type

**Response:**
```json
{
  "signals": [
    {
      "id": "signal-123",
      "symbol": "BTCUSD",
      "type": "buy",
      "strength": "strong",
      "confidence": 0.85,
      "price": 42200,
      "target": 45000,
      "stop_loss": 41000,
      "timestamp": "2024-01-01T12:00:00Z",
      "reason": "RSI oversold with bullish divergence"
    }
  ]
}
```

---

### 11. Strategies API (`/api/strategies`)

Strategy management and execution.

#### GET /api/strategies

List all strategies.

**Response:**
```json
{
  "strategies": [
    {
      "id": "strategy-123",
      "name": "Moving Average Crossover",
      "type": "trend",
      "symbol": "BTCUSD",
      "status": "active",
      "parameters": {
        "short_ma": 10,
        "long_ma": 30
      },
      "performance": {
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "win_rate": 0.55
      }
    }
  ]
}
```

#### POST /api/strategies

Create a new strategy.

**Request Body:**
```json
{
  "name": "RSI Strategy",
  "type": "momentum",
  "symbol": "BTCUSD",
  "conditions": [
    {
      "indicator": "rsi",
      "operator": "<",
      "value": 30
    }
  ],
  "actions": {
    "entry": "market",
    "exit": "condition",
    "stop_loss": 0.02
  }
}
```

---

### 12. Whales API (`/api/whales`)

Large wallet activity monitoring.

#### GET /api/whales/{symbol}

Get recent whale transactions.

**Query Parameters:**
- `threshold` (optional, default=1000): Transaction size threshold

**Response:**
```json
{
  "symbol": "BTCUSD",
  "whales": [
    {
      "hash": "0x123...456",
      "transaction_hash": "0x789...012",
      "amount": 1500,
      "value_usd": 63300000,
      "type": "in",
      "timestamp": "2024-01-01T12:00:00Z",
      "exchange": "unknown"
    }
  ]
}
```

---

## WebSocket API

### Connection

Connect to WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?channels=signals,portfolio,liquidations');
```

### Available Channels

1. **signals**: Live trading signals
2. **portfolio**: Portfolio updates
3. **whales**: Whale activity alerts
4. **ai-reasoning**: AI reasoning stream
5. **price-ticker**: Real-time price updates
6. **genetic-progress**: Genetic algorithm optimization progress
7. **arbitrage**: Dark arbitrage opportunity alerts
8. **liquidations**: Real-time liquidation feed

### Message Format

#### Subscribe/Unsubscribe

```json
{
  "action": "subscribe",
  "channel": "signals"
}
```

#### Ping/Pong

```json
{
  "action": "ping"
}
```

#### Data Messages

**Signal Update:**
```json
{
  "channel": "signals",
  "type": "new_signal",
  "data": {
    "symbol": "BTCUSD",
    "type": "buy",
    "price": 42200,
    "confidence": 0.85
  }
}
```

**Liquidation Alert:**
```json
{
  "channel": "liquidations",
  "type": "large_liq",
  "data": {
    "symbol": "BTCUSD",
    "size": 500,
    "price": 41000,
    "side": "long"
  }
}
```

**Portfolio Update:**
```json
{
  "channel": "portfolio",
  "type": "position_update",
  "data": {
    "total_value": 125000,
    "return_pct": 0.25
  }
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns error responses in JSON format.

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid parameter value",
    "details": {
      "parameter": "symbol",
      "value": "INVALID",
      "expected": "Valid trading symbol"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

- `INVALID_PARAMETER`: Invalid request parameter
- `UNAUTHORIZED`: Missing or invalid API key
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `INTERNAL_ERROR`: Server error
- `NOT_FOUND`: Resource not found
- `METHOD_NOT_ALLOWED`: HTTP method not allowed

---

## Data Models

### Basic Types

- **Price**: Float representing price value
- **Volume**: Float representing trading volume
- **Timestamp**: ISO 8601 datetime string
- **Percentage**: Float between 0 and 1 (e.g., 0.5 = 50%)
- **Symbol**: String representing trading pair (e.g., "BTCUSD")

### Response Pagination

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

---

## Example cURL Commands

### Health Check
```bash
curl http://localhost:8000/
```

### Get Market Data
```bash
curl "http://localhost:8000/api/market-data/klines/BTCUSD?interval=1h&limit=10"
```

### Create Backtest
```bash
curl -X POST "http://localhost:8000/api/backtests/create" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-123",
    "symbol": "BTCUSD",
    "initial_capital": 10000
  }'
```

### Get Signals
```bash
curl "http://localhost:8000/api/signals"
```

### WebSocket Test
```bash
curl http://localhost:8000/ws/test
```

---

## Rate Limiting

- **Development**: No limits
- **Production**: 100 requests/minute per API key
- **WebSocket**: 100 messages/second per connection

Rate limit headers in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## Webhooks

Webhook endpoints are available for real-time notifications. Configure webhooks in settings.

### Example Webhook Payload

```json
{
  "event": "new_signal",
  "data": {
    "symbol": "BTCUSD",
    "type": "buy",
    "price": 42200,
    "confidence": 0.85
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Testing API

Use the provided test endpoints:

- **WebSocket Test**: `/ws/test` - Interactive HTML test page
- **API Sandbox**: `/docs` - Swagger UI for testing endpoints

---

## Performance Notes

- All endpoints use async processing for high performance
- Database queries are optimized with proper indexing
- WebSocket connections support thousands of concurrent clients
- API responses include caching headers where appropriate
- Large responses are paginated by default