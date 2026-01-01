# Crypto Quant Laboratory

A comprehensive quantitative analysis platform for cryptocurrency trading, featuring advanced algorithms for market analysis, backtesting, and automated trading strategies.

## 🎯 Project Overview

The Crypto Quant Laboratory is a full-stack trading platform that combines sophisticated quantitative analysis tools with real-time market data processing. It provides traders and quantitative analysts with powerful tools to:

- Analyze market patterns and liquidity
- Build and test trading strategies
- Monitor whale activities and liquidations
- Apply machine learning and AI models for predictions
- Manage portfolios and execute trades

## ✨ Key Features

### Market Analysis
- **Liquidity Hunting**: Detect stop-loss clusters, liquidity voids, and market maker sweep predictions
- **Liquidation Tracking**: Monitor real-time liquidation cascades and market volatility
- **Whale Activity**: Track large wallet movements and potential market impacts
- **Shadow Analysis**: Advanced market manipulation pattern detection

### Trading Strategies
- **Strategy Builder**: Visual strategy composer with drag-and-drop interface
- **Genetic Optimization**: Automated strategy optimization using genetic algorithms
- **Backtesting Engine**: Comprehensive backtesting with Monte Carlo simulations
- **Portfolio Management**: Multi-symbol portfolio tracking and optimization

### AI & Machine Learning
- **AI Reasoning**: Advanced AI-powered market analysis and reasoning
- **Machine Learning Models**: Predictive models for price movements and volatility
- **Signal Generation**: Automated trading signals with confidence scores
- **Arbitrage Detection**: Dark arbitrage opportunity identification

### Real-time Features
- **WebSocket Streaming**: Real-time market data and alerts
- **Live Dashboards**: Interactive dashboards with multiple views
- **Alert System**: Customizable alerts for market events
- **Performance Monitoring**: Real-time strategy and portfolio performance

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher (for frontend)
- SQLite (default) or PostgreSQL/MySQL (for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd STOCKTRADE
   ```

2. **Set up backend**
   ```bash
   # Create and activate virtual environment
   python -m venv venv

   # On Windows (Git Bash/Cygwin)
   source venv/Scripts/activate

   # On Linux/Mac
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

4. **Configure environment**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   # Start backend
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

   # In another terminal, start frontend
   cd frontend
   npm run dev
   ```

### Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **WebSocket Test**: http://localhost:8000/ws/test

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (SQLite/PG)   │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - REST API      │    │ - User Data     │
│ - Lab Composer  │    │ - WebSocket     │    │ - Market Data   │
│ - Charts        │    │ - Services      │    │ - Strategy Data │
│ - Settings      │    │ - Models        │    │ - Backtest      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Backend Technology Stack

- **FastAPI**: Modern, fast web framework for APIs
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Default database (easily switchable to PostgreSQL)
- **Uvicorn**: ASGI server
- **WebSocket**: Real-time communication
- **Redis**: Optional caching and sessions
- **Pytest**: Testing framework

### Frontend Technology Stack

- **Next.js**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript
- **Chart.js/Recharts**: Data visualization
- **Tailwind CSS**: Utility-first CSS framework
- **Socket.IO**: WebSocket client
- **React Query**: Data fetching and caching

## 📁 Folder Structure

```
STOCKTRADE/
├── api/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # Main application entry point
│   ├── ai.py              # AI-related endpoints
│   ├── backtests.py       # Backtesting endpoints
│   ├── genetic.py         # Genetic algorithm endpoints
│   ├── liquidations.py    # Liquidation tracking
│   ├── market_data.py     # Market data endpoints
│   ├── ml.py              # Machine learning endpoints
│   ├── portfolio.py       # Portfolio management
│   ├── settings.py        # Settings management
│   ├── shadow.py          # Shadow API (liquidity hunting)
│   ├── signals.py         # Trading signals
│   ├── strategies.py      # Strategy management
│   └── whales.py          # Whale tracking
├── core/                  # Core functionality
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connection
│   ├── middleware.py      # Middleware setup
│   └── websocket.py       # WebSocket manager
├── models/                # Data models and schemas
│   ├── arbitrage.py       # Arbitrage models
│   ├── backtest.py        # Backtest models
│   ├── liquidation.py     # Liquidation models
│   ├── market_data.py     # Market data models
│   ├── ml.py              # ML model schemas
│   ├── portfolio.py       # Portfolio models
│   ├── settings.py        # Settings models
│   ├── signal.py          # Signal models
│   ├── strategy.py        # Strategy models
│   └── whale.py           # Whale activity models
├── services/              # Business logic
│   ├── __init__.py
│   ├── ai_service.py      # AI service layer
│   ├── backtest_service.py # Backtesting engine
│   ├── genetic_optimizer.py # Genetic algorithms
│   ├── liquidity_hunter.py # Liquidity analysis
│   ├── ml_service.py      # ML models
│   ├── portfolio_service.py # Portfolio management
│   ├── signal_service.py   # Signal generation
│   ├── strategy_service.py # Strategy execution
│   └── whale_tracker.py    # Whale monitoring
├── data/                  # Data files and storage
│   ├── crypto_quant.db    # SQLite database
│   └── migrations/        # Database migrations
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_api.py        # API tests
│   ├── test_services.py   # Service tests
│   └── test_models.py     # Model tests
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities and helpers
│   │   └── types/         # TypeScript types
│   ├── public/            # Static assets
│   └── package.json       # Frontend dependencies
├── docs/                  # Documentation
│   ├── API.md             # API documentation
│   ├── DEPLOYMENT.md      # Deployment guide
│   ├── DEVELOPER.md       # Developer guide
│   ├── USER.md            # User guide
│   └── LIQUIDITY_HUNTING_API.md # Liquidity API docs
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── run_dev.sh            # Development startup script
└── venv/                 # Python virtual environment
```

## 🔌 API Endpoints

The API is organized into logical modules:

- **`/api/ai`**: AI reasoning and predictions
- **`/api/backtests`**: Backtesting operations
- **`/api/genetic`**: Genetic algorithm optimization
- **`/api/liquidations`**: Liquidation tracking
- **`/api/market-data`**: Market data endpoints
- **`/api/ml`**: Machine learning models
- **`/api/portfolio`**: Portfolio management
- **`/api/settings`**: Application settings
- **`/api/shadow`**: Liquidity hunting (Shadow API)
- **`/api/signals`**: Trading signals
- **`/api/strategies`**: Strategy management
- **`/api/whales`**: Whale tracking

For detailed API documentation, see [API.md](./docs/API.md) or visit `/docs` when running the application.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## 📊 Development

### Code Quality

- **Black**: Code formatting
- **Ruff**: Fast linter and formatter
- **Pydantic**: Type safety and validation

```bash
# Format code
black .

# Check formatting
black . --check

# Lint code
ruff check .

# Auto-fix issues
ruff check . --fix
```

### Database Migrations

For production deployments with PostgreSQL:

```bash
# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🚀 Deployment

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment instructions.

## 🤝 Contributing

See [DEVELOPER.md](./docs/DEVELOPER.md) for contribution guidelines.

## 📖 User Guide

See [USER.md](./docs/USER.md) for detailed user instructions and tutorials.

## 📈 Performance

The platform is optimized for:

- **Low-latency processing**: Async/await throughout
- **Real-time updates**: WebSocket streaming
- **Efficient queries**: Database indexing
- **Scalable architecture**: Microservices-ready design

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- **API Documentation**: http://localhost:8000/docs
- **GitHub Repository**: [Your repository URL]
- **Issue Tracker**: [Your issues URL]
- **Discord Community**: [Your community URL]

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Check the documentation in the `/docs` folder

---

Built with ❤️ for the quantitative trading community