# STOCKTRADE API Contract

**Version:** 1.0.0
**Last Updated:** 2026-01-01

## Table of Contents

1. [General Standards](#general-standards)
2. [Authentication](#authentication)
3. [Common Types](#common-types)
4. [Strategy Endpoints](#strategy-endpoints)
5. [Signal Endpoints](#signal-endpoints)
6. [Market Data Endpoints](#market-data-endpoints)
7. [Portfolio Endpoints](#portfolio-endpoints)
8. [Backtest Endpoints](#backtest-endpoints)
9. [Trader Endpoints](#trader-endpoints)
10. [Whale Tracking Endpoints](#whale-tracking-endpoints)
11. [ML & AI Endpoints)
12. [WebSocket Events](#websocket-events)

---

## General Standards

### Base URL
```
Development: http://localhost:8000
Production: https://api.stocktrade.io
```

### Response Format

**Success Response:**
```typescript
{
  success: true,
  data: T,
  meta?: {
    page?: number,
    limit?: number,
    total?: number,
    timestamp: string
  }
}
```

**Error Response:**
```typescript
{
  success: false,
  error: {
    code: string,
    message: string,
    details?: any,
    timestamp: string
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## Authentication

### Login
```http
POST /auth/login
```

**Request:**
```typescript
{
  email: string,
  password: string
}
```

**Response:**
```typescript
{
  access_token: string,
  refresh_token: string,
  user: User
}
```

### Refresh Token
```http
POST /auth/refresh
```

**Request:**
```typescript
{
  refresh_token: string
}
```

---

## Common Types

```typescript
// Primitive Types
type UUID = string;
type Timestamp = string; // ISO 8601
type Symbol = string; // e.g., "BTCUSDT"

// User
interface User {
  id: UUID;
  email: string;
  username: string;
  created_at: Timestamp;
  updated_at: Timestamp;
}

// Asset
interface Asset {
  symbol: Symbol;
  name: string;
  type: 'crypto' | 'stock' | 'forex';
  base_currency: string;
  quote_currency: string;
}

// Price Data
interface PriceData {
  symbol: Symbol;
  timestamp: Timestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Technical Indicators
interface TechnicalIndicators {
  symbol: Symbol;
  timestamp: Timestamp;
  sma_20?: number;
  sma_50?: number;
  ema_12?: number;
  ema_26?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  bollinger_upper?: number;
  bollinger_lower?: number;
  atr?: number;
}

// Signal
interface Signal {
  id: UUID;
  symbol: Symbol;
  type: 'buy' | 'sell' | 'hold';
  strength: number; // 0-100
  confidence: number; // 0-1
  reasoning: string;
  indicators: TechnicalIndicators;
  created_at: Timestamp;
  expires_at?: Timestamp;
}

// Position
interface Position {
  id: UUID;
  symbol: Symbol;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
  opened_at: Timestamp;
  closed_at?: Timestamp;
  status: 'open' | 'closed';
}

// Portfolio
interface Portfolio {
  id: UUID;
  user_id: UUID;
  name: string;
  cash_balance: number;
  total_value: number;
  positions: Position[];
  created_at: Timestamp;
  updated_at: Timestamp;
}
```

---

## Strategy Endpoints

### List Strategies
```http
GET /api/strategies
```

**Query Params:**
```typescript
{
  page?: number; // default: 1
  limit?: number; // default: 20
  status?: 'active' | 'inactive' | 'all';
  sort?: 'created_at' | 'updated_at' | 'name';
  order?: 'asc' | 'desc';
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    items: Strategy[],
    total: number,
    page: number,
    limit: number
  }
}
```

### Get Strategy
```http
GET /api/strategies/{strategy_id}
```

**Response:**
```typescript
{
  success: true,
  data: Strategy
}
```

### Create Strategy
```http
POST /api/strategies
```

**Request:**
```typescript
{
  name: string;
  description?: string;
  layers: StrategyLayer[];
  config: StrategyConfig;
}
```

**Response:**
```typescript
{
  success: true,
  data: Strategy
}
```

### Update Strategy
```http
PUT /api/strategies/{strategy_id}
```

**Request:** (same as Create)

### Delete Strategy
```http
DELETE /api/strategies/{strategy_id}
```

### Activate Strategy
```http
POST /api/strategies/{strategy_id}/activate
```

### Deactivate Strategy
```http
POST /api/strategies/{strategy_id}/deactivate
```

### Strategy Templates
```http
GET /api/strategies/templates
```

**Response:**
```typescript
{
  success: true,
  data: StrategyTemplate[]
}
```

### Create from Template
```http
POST /api/strategies/from-template
```

**Request:**
```typescript
{
  template_id: string;
  name: string;
  config_overrides?: Record<string, any>;
}
```

---

## Signal Endpoints

### Get Current Signals
```http
GET /api/signals
```

**Query Params:**
```typescript
{
  symbols?: Symbol[];
  strategy_id?: UUID;
  min_confidence?: number; // 0-1
  signal_type?: 'buy' | 'sell' | 'hold';
}
```

### Get Signal History
```http
GET /api/signals/history
```

**Query Params:**
```typescript
{
  symbol: Symbol;
  start_date?: Timestamp;
  end_date?: Timestamp;
  limit?: number;
}
```

### Stream Signals (SSE)
```http
GET /api/signals/stream
```

**Event Types:**
```typescript
{
  event: 'signal' | 'update' | 'expiration';
  data: Signal;
}
```

---

## Market Data Endpoints

### Get Current Price
```http
GET /api/market-data/price/{symbol}
```

**Response:**
```typescript
{
  success: true,
  data: {
    symbol: Symbol;
    price: number;
    change_24h: number;
    change_24h_percent: number;
    volume_24h: number;
    timestamp: Timestamp;
  }
}
```

### Get Historical Prices
```http
GET /api/market-data/history/{symbol}
```

**Query Params:**
```typescript
{
  interval: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
  start_date?: Timestamp;
  end_date?: Timestamp;
  limit?: number; // default: 500, max: 1000
}
```

**Response:**
```typescript
{
  success: true,
  data: PriceData[]
}
```

### Get Technical Indicators
```http
GET /api/market-data/indicators/{symbol}
```

**Query Params:**
```typescript
{
  indicators?: string[]; // e.g., ['sma', 'rsi', 'macd']
  period?: number; // default: 14
}
```

### Get Multiple Symbols
```http
POST /api/market-data/batch
```

**Request:**
```typescript
{
  symbols: Symbol[];
}
```

---

## Portfolio Endpoints

### Get Portfolio
```http
GET /api/portfolio
```

**Response:**
```typescript
{
  success: true,
  data: Portfolio
}
```

### Get Positions
```http
GET /api/portfolio/positions
```

**Query Params:**
```typescript
{
  status?: 'open' | 'closed' | 'all';
  symbol?: Symbol;
}
```

### Create Position
```http
POST /api/portfolio/positions
```

**Request:**
```typescript
{
  symbol: Symbol;
  side: 'long' | 'short';
  quantity: number;
  type?: 'market' | 'limit';
  price?: number; // required for limit orders
  stop_loss?: number;
  take_profit?: number;
}
```

### Close Position
```http
POST /api/portfolio/positions/{position_id}/close
```

**Request:**
```typescript
{
  quantity?: number; // partial close, defaults to full
}
```

### Get Performance
```http
GET /api/portfolio/performance
```

**Query Params:**
```typescript
{
  period: '1d' | '1w' | '1m' | '3m' | '1y' | 'all';
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    total_return: number;
    total_return_percent: number;
    daily_return: number;
    win_rate: number;
    sharpe_ratio: number;
    max_drawdown: number;
    profit_factor: number;
    trades: {
      total: number;
      winning: number;
      losing: number;
    };
    equity_curve: {
      date: Timestamp;
      value: number;
    }[];
  }
}
```

---

## Backtest Endpoints

### Create Backtest
```http
POST /api/backtests
```

**Request:**
```typescript
{
  strategy_id: UUID;
  symbol: Symbol;
  start_date: Timestamp;
  end_date: Timestamp;
  initial_capital: number; // default: 10000
  commission?: number; // default: 0.001 (0.1%)
  slippage?: number; // default: 0
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    id: UUID;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number; // 0-100
  }
}
```

### Get Backtest Results
```http
GET /api/backtests/{backtest_id}
```

**Response:**
```typescript
{
  success: true,
  data: {
    id: UUID;
    status: string;
    strategy_id: UUID;
    symbol: Symbol;
    period: {
      start: Timestamp;
      end: Timestamp;
    };
    metrics: BacktestMetrics;
    trades: Trade[];
    equity_curve: {
      date: Timestamp;
      value: number;
    }[];
  }
}
```

### List Backtests
```http
GET /api/backtests
```

**Query Params:**
```typescript
{
  strategy_id?: UUID;
  status?: string;
  page?: number;
  limit?: number;
}
```

---

## Trader Endpoints

### Get Traders
```http
GET /api/traders
```

**Response:**
```typescript
{
  success: true,
  data: Trader[]
}
```

### Get Trader Profile
```http
GET /api/traders/{trader_id}
```

### Follow Trader
```http
POST /api/traders/{trader_id}/follow
```

### Unfollow Trader
```http
DELETE /api/traders/{trader_id}/follow
```

---

## Whale Tracking Endpoints

### Get Whale Activity
```http
GET /api/whales/activity
```

**Query Params:**
```typescript
{
  symbol?: Symbol;
  min_amount?: number;
  start_date?: Timestamp;
  end_date?: Timestamp;
}
```

**Response:**
```typescript
{
  success: true,
  data: WhaleActivity[]
}
```

### Get Whale Alerts
```http
GET /api/whales/alerts
```

### Get Whale Ranking
```http
GET /api/whales/ranking/{symbol}
```

**Response:**
```typescript
{
  success: true,
  data: {
    symbol: Symbol;
    whales: {
      address: string;
      holdings: number;
      value_usd: number;
      rank: number;
      change_24h: number;
    }[];
  }
}
```

---

## ML & AI Endpoints

### Get AI Reasoning
```http
POST /ai/reason
```

**Request:**
```typescript
{
  symbol: Symbol;
  context?: string;
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    symbol: Symbol;
    reasoning: string;
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    key_factors: string[];
    timestamp: Timestamp;
  }
}
```

### Train ML Model
```http
POST /api/ml/train
```

**Request:**
```typescript
{
  model_type: 'classification' | 'regression' | 'lstm';
  features: string[];
  target: string;
  symbol: Symbol;
  train_start: Timestamp;
  train_end: Timestamp;
}
```

### Get ML Predictions
```http
POST /api/ml/predict
```

**Request:**
```typescript
{
  model_id: UUID;
  symbols: Symbol[];
}
```

---

## WebSocket Events

### Connection
```
ws://localhost:8000/ws
```

### Subscribe to Updates
```typescript
// Client sends
{
  action: 'subscribe';
  channels: ('prices' | 'signals' | 'positions' | 'whales')[];
  symbols?: Symbol[];
}

// Server acknowledges
{
  type: 'subscribed';
  channels: string[];
}
```

### Price Update Event
```typescript
{
  type: 'price_update';
  data: {
    symbol: Symbol;
    price: number;
    change_24h_percent: number;
    volume_24h: number;
    timestamp: Timestamp;
  };
}
```

### Signal Event
```typescript
{
  type: 'signal';
  data: Signal;
}
```

### Position Update Event
```typescript
{
  type: 'position_update';
  data: {
    position_id: UUID;
    symbol: Symbol;
    current_price: number;
    unrealized_pnl: number;
  };
}
```

### Whale Activity Event
```typescript
{
  type: 'whale_activity';
  data: {
    symbol: Symbol;
    address: string;
    amount: number;
    transaction_hash: string;
    timestamp: Timestamp;
  };
}
```

---

## Complete Type Definitions

```typescript
// Strategy Types
interface Strategy {
  id: UUID;
  user_id: UUID;
  name: string;
  description?: string;
  layers: StrategyLayer[];
  config: StrategyConfig;
  status: 'active' | 'inactive' | 'archived';
  created_at: Timestamp;
  updated_at: Timestamp;
}

interface StrategyLayer {
  id: UUID;
  strategy_id: UUID;
  type: 'indicator' | 'ml' | 'custom';
  name: string;
  weight: number; // 0-1
  config: Record<string, any>;
}

interface StrategyConfig {
  risk_level: 'low' | 'medium' | 'high';
  max_position_size: number;
  stop_loss_percent?: number;
  take_profit_percent?: number;
  rebalance_interval?: string;
}

interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  layers: Omit<StrategyLayer, 'id' | 'strategy_id'>[];
  default_config: StrategyConfig;
}

// Backtest Types
interface BacktestMetrics {
  total_return: number;
  total_return_percent: number;
  annualized_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  win_rate: number;
  profit_factor: number;
  calmar_ratio: number;
  trades: {
    total: number;
    winning: number;
    losing: number;
    avg_win: number;
    avg_loss: number;
    largest_win: number;
    largest_loss: number;
  };
}

interface Trade {
  id: UUID;
  backtest_id: UUID;
  symbol: Symbol;
  side: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_percent: number;
  entry_date: Timestamp;
  exit_date: Timestamp;
  duration_hours: number;
}

// Whale Types
interface WhaleActivity {
  id: UUID;
  symbol: Symbol;
  address: string;
  amount: number;
  value_usd: number;
  transaction_type: 'inflow' | 'outflow';
  transaction_hash: string;
  timestamp: Timestamp;
}

interface Trader {
  id: UUID;
  username: string;
  avatar_url?: string;
  stats: {
    followers: number;
    win_rate: number;
    total_return: number;
    trades_count: number;
  };
}

// ML Types
interface MLModel {
  id: UUID;
  name: string;
  model_type: string;
  features: string[];
  target: string;
  accuracy?: number;
  trained_at: Timestamp;
  status: 'training' | 'ready' | 'failed';
}
```
