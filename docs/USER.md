# User Guide

This guide provides comprehensive instructions for using the Crypto Quant Laboratory platform, covering all features and functionality.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Strategy Composer](#strategy-composer)
4. [Backtesting](#backtesting)
5. [Portfolio Management](#portfolio-management)
6. [Market Analysis Tools](#market-analysis-tools)
7. [Real-time Monitoring](#real-time-monitoring)
8. [Trading Signals](#trading-signals)
9. [Game Mode vs Pro Mode](#game-mode-vs-pro-mode)
10. [Settings and Configuration](#settings-and-configuration)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Account Setup

1. **Register an Account**
   - Visit the platform URL
   - Click "Sign Up"
   - Enter your email and create a password
   - Verify your email address

2. **Complete Profile**
   - Add trading preferences
   - Set up notification preferences
   - Configure initial settings

3. **Initial Configuration**
   ```markdown
   - Default symbols: BTCUSD, ETHUSD
   - Timeframe: 1h
   - Risk level: Medium
   - Initial capital: $10,000 (simulated)
   ```

### First Steps

1. **Explore the Dashboard**
   - View market overview
   - Check portfolio status
   - Review recent signals

2. **Create Your First Strategy**
   - Navigate to Strategy Composer
   - Use the "Quick Start" template
   - Configure basic parameters
   - Run backtest

3. **Join Real-time Monitoring**
   - Open WebSocket connection
   - Select relevant channels
   - Monitor live data streams

## Dashboard Overview

### Main Dashboard Elements

```
┌─────────────────────────────────────────────────────────────┐
│ Market Overview           Portfolio Summary              │
│ BTC: $42,200 (+2.3%)       Total Value: $125,456         │
│ ETH: $2,250 (+1.8%)        Daily P&L: +$1,234 (+0.99%)   │
│ Volume: $28.5B             Win Rate: 62.3%               │
│ └─────────────────────────────────────────────────────────┘
│ Active Strategies           Recent Signals                │
│ 1. MA Crossover (Running)  • BTCUSD - BUY (85%)         │
│ 2. RSI Strategy (Idle)    • ETHUSD - SELL (72%)         │
│ 3. Whale Tracker (Active)  • SOLUSD - BUY (91%)         │
│ └─────────────────────────────────────────────────────────┘
│ Market Alerts              Quick Actions                  │
│ • Large whale detected     • New Strategy              │
│ • Liquidation cascade      • Backtest Engine            │
│ • Volatility spike         • Portfolio Analysis          │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Menu

- **Dashboard**: Overview of all features
- **Lab**: Strategy composer and AI tools
- **Backtest**: Historical testing
- **Portfolio**: Portfolio management
- **Markets**: Real-time market data
- **Signals**: Trading signals
- **Settings**: Configuration options

### Customizing Your Dashboard

1. **Widget Layout**
   - Drag and drop widgets
   - Resize as needed
   - Show/hide specific widgets

2. **Time Preferences**
   - Set default timeframe
   - Configure chart types
   - Adjust date ranges

3. **Color Scheme**
   - Light/Dark mode
   - Custom accent colors
   - Chart color preferences

## Strategy Composer

### Interface Overview

The Strategy Composer is a visual drag-and-drop interface for creating trading strategies.

#### Components Panel

```
┌─────────────────────────────────────────────────────────────┐
│ Components                                         │
├─────────────────────────────────────────────────────────┤
│ 📊 Technical Indicators                           │
│ ├─ Moving Average (MA)                           │
│ ├─ RSI (Relative Strength Index)                  │
│ ├─ MACD (Moving Average Convergence Divergence)    │
│ ├─ Bollinger Bands                               │
│ ├─ Stochastic Oscillator                         │
│ └─ Fibonacci Retracement                         │
│                                                     │
│ 🎯 Signal Generators                              │
│ ├─ Price Action                                  │
│ ├─ Volume Analysis                               │
│ ├─ Support/Resistance                            │
│ └─ Chart Patterns                                 │
│                                                     │
│ ⚙️ Actions                                        │
│ ├─ Enter Position                                 │
│ ├─ Exit Position                                  │
│ ├─ Set Stop Loss                                  │
│ ├─ Set Take Profit                               │
│ └─ Send Alert                                     │
│                                                     │
│ 🔧 Logic Gates                                     │
│ ├─ AND Gate                                       │
│ ├─ OR Gate                                        │
│ ├─ NOT Gate                                       │
│ └─ Time-based Conditions                          │
└─────────────────────────────────────────────────────────────┘
```

### Creating a Simple Strategy

1. **Moving Average Crossover Strategy**
   ```markdown
   Steps:
   1. Drag "Moving Average" to canvas
      - Set period: 20 (Short MA)
      - Type: Exponential

   2. Drag another "Moving Average"
      - Set period: 50 (Long MA)
      - Type: Simple

   3. Drag "Enter Position" action
      - Connect to MA crossover signal

   4. Add "Stop Loss" action
      - Set percentage: 2%

   5. Connect components:
      Short MA crosses above Long MA → Enter Long
      Price drops 2% → Exit Position
   ```

2. **RSI Oversold Strategy**
   ```markdown
   Components:
   - RSI indicator (period 14)
   - Price action component
   - Enter Position action
   - Exit Position action

   Logic:
   RSI < 30 AND Price making higher lows → Buy
   RSI > 70 OR Stop loss hit → Sell
   ```

### Advanced Strategy Features

1. **Strategy Parameters**
   - Configurable inputs
   - Default values
   - Min/max ranges

2. **Multiple Timeframe Analysis**
   - Primary: 1h
   - Secondary: 4h for trend
   - Tertiary: 15m for entry

3. **Risk Management Rules**
   - Position size calculator
   - Maximum drawdown limits
   - Risk per trade settings

### Strategy Templates

1. **Trend Following**
   ```markdown
   Components:
   - 200 SMA (trend filter)
   - 20 EMA (entry signal)
   - MACD (confirmation)
   - Volume filter

   Rules:
   - Price above 200 SMA → Only long
   - 20 EMA crosses above 200 EMA → Enter long
   - MACD bullish crossover → Confirm
   - Volume > average volume → Validate
   ```

2. **Mean Reversion**
   ```markdown
   Components:
   - Bollinger Bands
   - RSI
   - Stochastic

   Rules:
   - Price below lower Bollinger Band → Potential buy
   - RSI < 30 → Oversold confirmation
   - Stochastic < 20 → Additional confirmation
   - RSI crosses above 30 → Exit
   ```

## Backtesting

### Backtesting Interface

```
┌─────────────────────────────────────────────────────────────┐
│ Backtest Configuration                              │
├─────────────────────────────────────────────────────────┤
│ Strategy: MA Crossover v2                          │
│ Symbol: BTCUSD                                        │
│ Timeframe: 1h                                         │
│ Period: Jan 2023 - Dec 2023 (1 year)                 │
│ Initial Capital: $10,000                             │
│ └─────────────────────────────────────────────────────────┤
│ Parameters                                           │
│ Short MA Period: 10                                   │
│ Long MA Period: 30                                    │
│ Stop Loss: 2%                                         │
│ Take Profit: 5%                                       │
│ Commission: 0.1%                                     │
│ └─────────────────────────────────────────────────────────┤
│ Actions                                              │
│ ▶️ Start Backtest           📊 View Results          │
│ 🔄 Save Template            📁 Load Strategy          │
└─────────────────────────────────────────────────────────────┘
```

### Running a Backtest

1. **Configure Test Parameters**
   ```markdown
   - Select strategy from library
   - Choose trading symbols
   - Set date range
   - Define initial capital
   - Configure fees and commissions
   ```

2. **Run Backtest**
   - Click "Start Backtest"
   - Monitor progress
   - View preliminary results

3. **Analyze Results**
   ```markdown
   Performance Metrics:
   - Total Return: 28.5%
   - Annualized Return: 28.5%
   - Sharpe Ratio: 1.45
   - Max Drawdown: 12.3%
   - Win Rate: 62.1%
   - Profit Factor: 1.8
   - Total Trades: 156

   Trade Analysis:
   - Winning trades: 97
   - Losing trades: 59
   - Average win: 3.2%
   - Average loss: -2.1%
   - Largest win: 8.5%
   - Largest loss: -5.2%
   ```

### Advanced Backtesting Features

1. **Monte Carlo Simulation**
   - Run 1000+ simulations
   - Statistical confidence intervals
   - Risk probability analysis

2. **Parameter Optimization**
   - Grid search parameters
   - Genetic algorithm optimization
   - Custom fitness functions

3. **Portfolio Backtesting**
   - Multi-symbol strategies
   - Correlation analysis
   - Portfolio-level metrics

## Portfolio Management

### Portfolio Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Portfolio Summary                                   │
├─────────────────────────────────────────────────────────┤
│ Total Value: $125,456.78                            │
│ Cash: $25,000.00                                    │
│ Invested: $100,456.78                               │
│ Daily P&L: +$1,234.56 (+0.99%)                     │
│ Total P&L: +$25,456.78 (+25.46%)                   │
│ └─────────────────────────────────────────────────────────┤
│ Positions                                           │
│ Symbol   | Size   | Entry | Current | P&L    | %   │
│ BTCUSD   | 2.0    | 40K   | 42.2K   | +4.4K  | +5.5%│
│ ETHUSD   | 10.0   | 2.1K  | 2.25K   | +1.5K  | +7.1%│
│ SOLUSD   | 50.0   | 95    | 100     | +250   | +2.6%│
│ └─────────────────────────────────────────────────────────┤
│ Performance Metrics                                  │
│ Sharpe Ratio: 1.23                                  │
│ Sortino Ratio: 1.56                                 │
│ Beta: 1.05                                          │
│ Alpha: 0.08                                         │
└─────────────────────────────────────────────────────────────┘
```

### Managing Positions

1. **Opening Positions**
   ```markdown
   Manual Entry:
   - Select trading symbol
   - Choose order type (Market/Limit)
   - Set position size
   - Configure stop loss/take profit
   - Review and execute

   Strategy Entry:
   - Wait for strategy signal
   - Confirm signal strength
   - Execute trade automatically
   ```

2. **Position Management**
   - View real-time P&L
   - Adjust stop losses
   - Take partial profits
   - Close positions manually

3. **Risk Management**
   ```markdown
   Position Size Calculator:
   - Risk per trade: 1-2% of portfolio
   - Stop distance determines size
   - Example: $1000 portfolio, 1% risk = $10
   - If stop is 2% away: position = $10 / 0.02 = $500

   Portfolio Protection:
   - Max drawdown limit: 15%
   - Daily loss limit: 5%
   - Correlation limits
   ```

### Performance Analysis

1. **Performance Charts**
   - Equity curve over time
   - Drawdown visualization
   - Risk/return scatter plot

2. **Trade History**
   - Export to CSV/Excel
   - Filter by symbol/strategy
   - Analyze trade patterns

3. **Reporting**
   - Generate monthly reports
   - Performance benchmarks
   - Tax reports (export ready)

## Market Analysis Tools

### Liquidity Hunting Tool

The Liquidity Hunting tool identifies market manipulation patterns and liquidity levels.

```
┌─────────────────────────────────────────────────────────────┐
│ Liquidity Analysis - BTCUSD                           │
├─────────────────────────────────────────────────────────┤
│ Current Price: $42,200                                │
│ Sweep Probability: 72%                                 │
│ Risk Level: HIGH                                      │
│ └─────────────────────────────────────────────────────────┤
│ Liquidity Clusters                                    │
│ Level        | Orders | Value   | Sweep Prob | Risk     │
│ 41,800       | 1,250  | 52.5M   | 85%       | CRITICAL │
│ 41,500       | 980    | 40.7M   | 75%       | HIGH     │
│ 42,500       | 1,100  | 46.8M   | 60%       | MEDIUM   │
│ 43,000       | 750    | 32.3M   | 40%       | LOW      │
│ └─────────────────────────────────────────────────────────┤
│ Voids (Liquidity Gaps)                               │
│ From     | To       | Size   | Impact Risk             │
│ 41,200   | 41,400   | 2.1M   | Medium                 │
│ 42,800   | 43,200   | 3.5M   | High                  │
│ └─────────────────────────────────────────────────────────┤
│ Psychological Levels                                 │
│ Round Number: 40,000   | Orders: 2,100   | Value: 84M   │
│ Round Number: 45,000   | Orders: 1,800   | Value: 81M   │
└─────────────────────────────────────────────────────────────┘
```

### Using the Tool

1. **Analyze Liquidity Map**
   - View cluster concentrations
   - Check sweep probabilities
   - Identify key levels

2. **Cascade Risk Assessment**
   - Evaluate cascade potential
   - Calculate worst-case scenarios
   - Plan mitigation strategies

3. **Set Alerts**
   - Price level alerts
   - Sweep probability thresholds
   - Volume anomalies

### Whale Activity Monitor

Track large wallet movements and potential market impacts.

```
┌─────────────────────────────────────────────────────────────┐
│ Recent Whale Activity                                 │
├─────────────────────────────────────────────────────────┤
│ Time        | Symbol  | Amount    | Value     | Type │
│ 12:30:15    | BTCUSD  | +1,500    | $63.3M    | IN  │
│ 12:28:42    | ETHUSD  | -5,000    | $11.25M   | OUT │
│ 12:25:11    | BTCUSD  | +2,000    | $84.4M    | IN  │
│ 12:20:33    | SOLUSD  | +50,000   | $5M       | IN  │
│ └─────────────────────────────────────────────────────────┤
│ Alerts                                                │
│ • Large BTC accumulation detected (>1000 BTC)          │
│ • ETH whale distribution pattern identified          │
│ • Unusual SOL whale activity                          │
└─────────────────────────────────────────────────────────────┘
```

## Real-time Monitoring

### WebSocket Channels

The platform provides real-time data through WebSocket connections.

1. **Connecting to WebSocket**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws?channels=signals,portfolio,liquidations');
   ```

2. **Available Channels**
   - `signals`: Trading signals updates
   - `portfolio`: Portfolio value changes
   - `liquidations`: Real-time liquidations
   - `whales`: Whale activity alerts
   - `ai-reasoning`: AI analysis stream
   - `price-ticker`: Price updates
   - `genetic-progress`: Optimization status
   - `arbitrage`: Arbitrage opportunities

3. **Message Examples**
   ```json
   // Signal Update
   {
     "channel": "signals",
     "type": "new_signal",
     "data": {
       "symbol": "BTCUSD",
       "type": "BUY",
       "strength": "STRONG",
       "confidence": 0.85,
       "price": 42200,
       "target": 45000,
       "stop_loss": 41000,
       "timestamp": "2024-01-01T12:00:00Z"
     }
   }

   // Liquidation Alert
   {
     "channel": "liquidations",
     "type": "large_liq",
     "data": {
       "symbol": "BTCUSD",
       "side": "LONG",
       "size": 500,
       "price": 41000,
       "value": $20.5M,
       "timestamp": "2024-01-01T12:00:00Z"
     }
   }
   ```

### Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Real-time Feed                                       │
├─────────────────────────────────────────────────────────┤
│ [12:45:23] BTC Signal: STRONG BUY (88%)              │
│ [12:45:15] Whale: +2000 BTC ($84.4M) to Binance      │
│ [12:44:58] Liquidation: $15M long BTC @ 41500       │
│ [12:44:32] AI Analysis: Trend reversal detected       │
│ [12:44:15] Arbitrage: ETH/BTC 0.5% opportunity       │
│ [12:43:58] Portfolio: New ATH $125,456               │
│ └─────────────────────────────────────────────────────────┤
│ Active Alerts                                        │
│ 🔴 High liquidation risk at 41800                   │
│ 🟡 Whale accumulation pattern detected              │
│ 🟡 AI suggests trend reversal in 4-6 hours           │
│ └─────────────────────────────────────────────────────────┤
│ Quick Actions                                        │
│ ▶️ Start Trade              🔔 Configure Alerts        │
│ 📊 View Analysis           ⚙️ Settings              │
└─────────────────────────────────────────────────────────────┘
```

## Trading Signals

### Signal Types

1. **Technical Signals**
   - Based on technical indicators
   - Generated by strategies
   - Include confidence scores

2. **AI Signals**
   - Machine learning predictions
   - Sentiment analysis
   - Multi-factor analysis

3. **Whale Signals**
   - Large wallet movements
   - Exchange inflows/outflows
   - Pattern recognition

### Signal Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Active Signals                                        │
├─────────────────────────────────────────────────────────┤
│ BTCUSD - STRONG BUY (87%)       [12:45] Active 5m      │
│ Entry: $42,200 | Target: $45,000 | SL: $41,000        │
│ Strategy: MA Crossover v2 | Confidence: High           │
│ └─────────────────────────────────────────────────────────┤
│ ETHUSD - SELL (72%)            [12:44] Active 15m     │
│ Entry: $2,250 | Target: $2,100 | SL: $2,350           │
│ Reason: RSI overbought + whale distribution          │
│ └─────────────────────────────────────────────────────────┤
│ SOLUSD - WEAK BUY (65%)        [12:43] Active 30m    │
│ Entry: $100 | Target: $110 | SL: $95                │
│ AI Prediction: +10% in 24h                           │
└─────────────────────────────────────────────────────────────┘
```

### Signal Management

1. **Signal Filtering**
   - By symbol
   - By confidence level
   - By strategy source
   - By time active

2. **Signal Actions**
   - Manual trade execution
   - Add to watchlist
   - Set price alerts
   - Share with community

3. **Signal History**
   - Review past signals
   - Track success rate
   - Analyze performance

## Game Mode vs Pro Mode

### Game Mode

**Purpose**: Learn and practice with virtual funds

**Features**:
- $100,000 virtual starting capital
- All strategies available
- Real-time market data
- Full feature access
- No real money risk

**Limitations**:
- Cannot withdraw funds
- Cannot deposit real money
- Trades are simulated
- Cannot connect to exchanges

**Best For**:
- Learning the platform
- Testing new strategies
- Practicing trading
- Understanding market dynamics

### Pro Mode

**Purpose**: Real trading with actual funds

**Features**:
- Connect to real exchanges
- Deposit/withdraw real funds
- Execute live trades
- Real risk and rewards
- API access for automation

**Requirements**:
- Verified account
- KYC/AML completed
- Connected exchange accounts
- Risk assessment completed

**Security Features**:
- Two-factor authentication
- API key encryption
- Transaction signing
- Audit trail

### Mode Comparison

| Feature                | Game Mode      | Pro Mode       |
|------------------------|---------------|---------------|
| Starting Capital        | $100,000      | Your deposit  |
| Market Data            | Real-time     | Real-time     |
| Strategy Testing       | Full access   | Full access   |
| Trade Execution       | Simulated     | Real          |
| Withdrawals            | No            | Yes           |
| API Access             | Limited       | Full          |
| Risk Management        | Virtual       | Real          |
| Account Security       | Basic         | Advanced      |

### Switching Between Modes

1. **Game to Pro**
   - Complete KYC verification
   - Connect exchange accounts
   - Review risk disclosure
   - Set up security measures
   - Transfer funds (optional)

2. **Pro to Game**
   - Withdraw all funds
   - Disconnect exchanges
   - Reset positions
   - Return to virtual portfolio

## Settings and Configuration

### Account Settings

1. **Profile Management**
   - Update personal information
   - Change profile picture
   - Set display name

2. **Security Settings**
   ```markdown
   - Two-factor authentication (2FA)
   - API key management
   - Password requirements
   - Session timeout
   - Login notifications
   ```

3. **Notification Preferences**
   ```markdown
   Email Notifications:
   - Daily digest
   - Signal alerts
   - Portfolio updates
   - Security alerts

   Push Notifications:
   - Mobile alerts
   - Desktop notifications
   - Sound alerts

   WebSocket Alerts:
   - Real-time updates
   - Custom channels
   ```

### Trading Settings

1. **Default Parameters**
   - Default symbols
   - Timeframe preferences
   - Position sizing rules
   - Stop loss defaults
   - Take profit defaults

2. **Risk Management**
   ```markdown
   Account Level:
   - Maximum drawdown: 15%
   - Daily loss limit: 5%
   - Max position size: 10%

   Trade Level:
   - Risk per trade: 1-2%
   - Max leverage: 10x
   - Minimum risk/reward: 1:2
   ```

3. **Exchange Integration**
   - Configure API connections
   - Set trading fees
   - Configure order types
   - Set withdrawal limits

### Interface Settings

1. **Display Preferences**
   - Theme (Light/Dark/Custom)
   - Language
   - Date format
   - Number format
   - Chart styles

2. **Dashboard Layout**
   - Widget selection
   - Layout presets
   - Default views
   - Refresh intervals

3. **Chart Settings**
   - Default indicators
   - Color schemes
   - Zoom levels
   - Grid preferences

## Troubleshooting

### Common Issues

1. **WebSocket Connection Problems**
   ```markdown
   Symptoms:
   - Real-time data not updating
   - Signals not appearing
   - Connection errors

   Solutions:
   1. Check internet connection
   2. Refresh the page
   3. Clear browser cache
   4. Disable ad blockers
   5. Check WebSocket URL

   Test connection:
   http://localhost:8000/ws/test
   ```

2. **Strategy Backtest Errors**
   ```markdown
   Symptoms:
   - Backtest fails to start
   - Incorrect results
   - Slow performance

   Solutions:
   1. Check data availability
   2. Validate strategy logic
   3. Reduce time range
   4. Check for infinite loops
   5. Review parameter ranges

   Debug mode:
   Enable debug logging for detailed error messages
   ```

3. **Portfolio Sync Issues**
   ```markdown
   Symptoms:
   - Portfolio values not updating
   - Missing positions
   - Incorrect P&L calculations

   Solutions:
   1. Refresh portfolio data
   2. Check exchange API status
   3. Verify API permissions
   4. Re-sync exchange data
   5. Check for duplicate trades
   ```

4. **Performance Problems**
   ```markdown
   Symptoms:
   - Slow page loading
   - Lagging charts
   - High memory usage

   Solutions:
   1. Clear browser cache
   2. Disable unnecessary extensions
   3. Reduce chart history
   4. Use simple chart styles
   5. Close other tabs
   6. Update browser
   ```

### Error Messages

1. **API Key Errors**
   ```
   Error: "Invalid API Key"
   Cause: Invalid or expired API key
   Solution: Check API key in settings, regenerate if needed

   Error: "Insufficient Permissions"
   Cause: API key lacks required permissions
   Solution: Update API key permissions in exchange settings
   ```

2. **Data Errors**
   ```
   Error: "No market data available"
   Cause: Symbol not found or data unavailable
   Solution: Check symbol spelling, verify data source

   Error: "Historical data incomplete"
   Cause: Missing data for selected period
   Solution: Reduce time range or check data provider
   ```

3. **Strategy Errors**
   ```
   Error: "Invalid strategy parameters"
   Cause: Parameter values outside allowed range
   Solution: Check parameter constraints

   Error: "Strategy logic error"
   Cause: Invalid conditions or actions
   Solution: Review strategy components
   ```

### Getting Help

1. **In-App Help**
   - Help button (? icon)
   - Context-sensitive help
   - Tutorial videos
   - Documentation links

2. **Support Channels**
   ```markdown
   - Discord Community: Real-time help
   - Email Support: support@cryptoquant.com
   - GitHub Issues: Bug reports
   - Documentation: Knowledge base

   Response Times:
   - Discord: Immediate
   - Email: 24 hours
   - GitHub: 3-5 days
   ```

3. **FAQ**
   **Q: How do I connect to an exchange?**
   A: Go to Settings > Exchanges > Add Exchange and follow the API setup wizard.

   **Q: Why are my backtest results different from live trading?**
   A: Backtests use historical data with perfect execution. Live trading includes slippage, fees, and market impact.

   **Q: How accurate are the trading signals?**
   A: Signals are based on multiple factors and have confidence scores. Past performance doesn't guarantee future results.

   **Q: Can I use my own data?**
   A: Currently, the platform uses integrated data sources. Custom data imports are planned for future updates.

### Advanced Troubleshooting

1. **Log Analysis**
   ```bash
   # View application logs
   tail -f logs/app.log

   # Check for errors
   grep "ERROR" logs/app.log

   # Monitor performance
   grep "PERFORMANCE" logs/app.log
   ```

2. **Database Issues**
   ```sql
   -- Check database connections
   SELECT count(*) FROM pg_stat_activity;

   -- Check table sizes
   SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables WHERE schemaname = 'public';

   -- Check index usage
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC;
   ```

3. **Network Diagnostics**
   ```bash
   # Test WebSocket connection
   curl -I http://localhost:8000/ws

   # Check latency
   ping api.cryptoquant.com

   # Test API endpoints
   curl http://localhost:8000/health
   ```

### Best Practices

1. **Regular Backups**
   - Export portfolio data weekly
   - Save strategy templates
   - Document custom configurations

2. **Security Measures**
   - Use 2FA
   - Rotate API keys regularly
   - Keep software updated
   - Monitor account activity

3. **Performance Optimization**
   - Monitor system resources
   - Close unnecessary applications
   - Use stable internet connection
   - Keep browser updated

4. **Data Management**
   - Regular data verification
   - Clean up old strategies
   - Archive old backtests
   - Maintain adequate storage space

---

For additional help and support, visit our [Discord community](https://discord.gg/cryptoquant) or check the [developer documentation](./DEVELOPER.md).