# TDD SPECIFICATIONS - CRYPTO QUANT LABORATORY

## ARCHITECT'S ORDERS TO ORCHESTRATOR

**YOUR ROLE:** Test Maker - Create tests that Jules sessions will solve
**JULES ROLE:** Test Solvers - Make the tests pass

## WHY THESE TESTS MUST EXIST

1. **Dashboard Priority #1** - User needs functional trading interface
2. **Dependencies Broken** - numpy missing, imports failing, tests can't run
3. **Data Acquisition Required** - Real-time and historical data for trading
4. **Backend APIs Down** - Frontend has no working endpoints
5. **Modularity Missing** - Code not extensible for new data sources

## WHAT TESTS TO CREATE

### FOUNDATION TESTS (Fix First)
```python
# tests/test_foundation.py
def test_all_dependencies_installed():
    """WHY: numpy missing breaks entire test suite"""
    import numpy, pandas, fastapi, sqlalchemy
    
def test_basic_imports_work():
    """WHY: Import chain broken in services/__init__.py"""
    from api.main import app
    from services.genetic_optimizer import GeneticOptimizer
    
def test_database_connection():
    """WHY: Data persistence required for all features"""
    from core.database import get_db
    # Test connection works
```

### DASHBOARD TESTS (Priority #1)
```python
# tests/test_dashboard.py
def test_dashboard_page_loads():
    """WHY: Main user interface must work"""
    # Test frontend dashboard renders
    
def test_dashboard_components_render():
    """WHY: Trading widgets must display"""
    # Test charts, tables, controls load
    
def test_real_time_data_updates():
    """WHY: Live trading data required"""
    # Test WebSocket updates dashboard
```

### DATA ACQUISITION TESTS
```python
# tests/test_data_acquisition.py
def test_current_market_data_fetch():
    """WHY: Real-time prices needed for trading"""
    # Test live data API works
    
def test_historical_data_fetch():
    """WHY: Backtesting requires past data"""
    # Test historical data retrieval
    
def test_trader_data_fetch():
    """WHY: User specifically requested trader data"""
    # Test trader information API
    
def test_data_source_extensibility():
    """WHY: Must support multiple APIs (Binance, CoinGecko, etc)"""
    # Test plugin architecture for data sources
```

### API TESTS
```python
# tests/test_api_endpoints.py
def test_all_endpoints_respond():
    """WHY: Frontend needs working backend"""
    # Test all API routes return 200
    
def test_websocket_connection():
    """WHY: Real-time updates required"""
    # Test WebSocket connects and streams data
```

## JULES SESSION ASSIGNMENTS

**Jules-1: Foundation-Fixer**
- Make test_foundation.py pass
- Fix numpy dependency
- Fix import chain issues
- Ensure basic app startup

**Jules-2: Dashboard-Builder**
- Make test_dashboard.py pass
- Fix frontend dashboard rendering
- Implement real-time updates
- Modular dashboard components

**Jules-3: Database-Architect**
- Fix database connection issues
- Ensure models work properly
- Test data persistence

**Jules-4: Current-Data-Specialist**
- Implement current market data API
- Real-time price feeds
- Multiple exchange support

**Jules-5: Historical-Data-Specialist**
- Implement historical data retrieval
- Backtesting data support
- Efficient data storage

**Jules-6: Trader-Data-Specialist**
- Implement trader data acquisition
- User-specified trader information
- Extensible trader data sources

**Jules-7: WebSocket-Specialist**
- Fix WebSocket connections
- Real-time data streaming
- Dashboard live updates

## EXECUTION ORDER

1. **ORCHESTRATOR**: Create all test files with failing tests
2. **ORCHESTRATOR**: Launch 7 Jules sessions with specific assignments
3. **JULES SESSIONS**: Work in parallel to make tests pass
4. **ARCHITECT**: Supervise and approve all work

## SUCCESS CRITERIA

- All tests pass
- Dashboard loads and functions
- Data acquisition system works
- Code is modular and extensible
- Real-time features operational
