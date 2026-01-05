# Crypto Quant Laboratory - QWEN Context

## Project Overview

The Crypto Quant Laboratory is a comprehensive quantitative analysis platform for cryptocurrency trading. It combines sophisticated quantitative analysis tools with real-time market data processing, providing traders and quantitative analysts with powerful tools for market analysis, backtesting, and automated trading strategies.

## Architecture

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

## Key Features

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

## API Structure

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
- **`/api/traders`**: Trader management

## WebSocket Channels

The application supports real-time communication through multiple WebSocket channels:
- `signals` - Live signal updates
- `portfolio` - Portfolio updates
- `whales` - Whale activity alerts
- `ai-reasoning` - AI reasoning stream
- `price-ticker` - Real-time price updates
- `genetic-progress` - Genetic algorithm optimization progress
- `arbitrage` - Dark arbitrage opportunity alerts
- `liquidations` - Real-time liquidation feed and cascade alerts

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (for frontend)
- SQLite (default) or PostgreSQL/MySQL (for production)

### Installation
1. **Set up backend**:
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

2. **Set up frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Configure environment**:
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

#### Development Mode
- **Windows Batch**: Run `start.bat` to start both backend and frontend
- **PowerShell**: Run `start.ps1` to start both backend and frontend
- **Linux/Mac**: Run `./run_dev.sh` for backend development server

#### Docker Deployment
The application supports containerized deployment with Docker Compose:
```bash
# Start all services (backend, database, redis, nginx)
docker-compose up -d

# For production deployment
docker-compose --profile production up -d
```

## Configuration

### Environment Variables
The application uses several environment variables defined in `.env`:
- `DATABASE_URL`: Database connection string
- `API_KEY`: Secret API key for authentication
- `RATE_LIMIT_MAX_REQUESTS`: Rate limiting configuration
- `DEBUG`: Debug mode toggle
- `LOG_LEVEL`: Logging level
- `REDIS_URL`: Redis connection URL

### Code Quality Tools
The project uses:
- **Black**: Code formatting
- **Ruff**: Fast linter and formatter
- **Pytest**: Testing framework

Commands:
```bash
# Format code
black .

# Check formatting
black . --check

# Lint code
ruff check .

# Run tests
pytest tests/ -v
```

## Testing

Run the test suite with:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## Deployment

The application supports multiple deployment options:
1. **Docker Compose**: Production-ready with PostgreSQL, Redis, and Nginx
2. **Direct Python**: For development and simple deployments
3. **Cloud Platforms**: Compatible with containerized cloud platforms

## File Structure

```
STOCKTRADE/
├── api/                    # FastAPI application
├── core/                  # Core functionality
├── models/                # Data models and schemas
├── services/              # Business logic
├── data/                  # Data files and storage
├── tests/                 # Test suite
├── frontend/              # Next.js frontend
├── docs/                  # Documentation
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── run_dev.sh            # Development startup script
└── venv/                 # Python virtual environment
```

## Development Conventions

1. **Code Formatting**: Use Black with line-length of 100
2. **Linting**: Use Ruff with the configured rules
3. **Async/Await**: Use asynchronous programming throughout for performance
4. **Type Safety**: Use Pydantic models for data validation
5. **Testing**: Write comprehensive tests with pytest
6. **Documentation**: Follow docstring conventions for all functions and classes

## Performance Considerations

The platform is optimized for:
- **Low-latency processing**: Async/await throughout
- **Real-time updates**: WebSocket streaming
- **Efficient queries**: Database indexing
- **Scalable architecture**: Microservices-ready design

## Key Files and Directories

- `api/main.py`: Main FastAPI application entry point
- `core/websocket.py`: WebSocket connection management
- `core/database.py`: Database connection and session management
- `requirements.txt`: Python dependencies
- `docker-compose.yml`: Docker configuration for multi-service deployment
- `start.bat` / `start.ps1` / `run_dev.sh`: Application startup scripts
- `.env.example`: Environment variable template
- `pyproject.toml`: Project configuration for black, ruff, and pytest