# TASK TRACKING - ORCHESTRATOR REFERENCE

## Task 1: WebSocket Fix
**Tests:** 1 total
- tests/test_websocket_fix.py::test_websocket_ping_pong
**Status:** Not Started
**Jules Session:** None
**Notes:** Single test - create PR when complete

## Task 2: Binance Integration  
**Tests:** 2 total
- tests/test_binance_integration.py::test_binance_client_exists
- tests/test_binance_integration.py::test_binance_get_current_price
**Status:** Not Started
**Jules Session:** None
**Notes:** Feed tests one at a time. PR only after both pass.

## Task 3: CoinGecko Integration
**Tests:** 2 total
- tests/test_coingecko_integration.py::test_coingecko_client_exists
- tests/test_coingecko_integration.py::test_coingecko_get_current_price
**Status:** Not Started
**Jules Session:** None
**Notes:** Feed tests one at a time. PR only after both pass.

## Task 4: Historical Storage
**Tests:** 3 total
- tests/test_historical_storage.py::test_historical_data_model_exists
- tests/test_historical_storage.py::test_save_historical_price
- tests/test_historical_storage.py::test_query_historical_prices
**Status:** Not Started
**Jules Session:** None
**Notes:** Feed tests one at a time. PR only after all 3 pass.

## Task 5: Trader Tracking
**Tests:** 3 total
- tests/test_trader_tracking.py::test_trader_model_exists
- tests/test_trader_tracking.py::test_track_trader_performance
- tests/test_trader_tracking.py::test_get_top_performers
**Status:** Not Started
**Jules Session:** None
**Notes:** Feed tests one at a time. PR only after all 3 pass.

## Task 6: Data Source Manager
**Tests:** 3 total
- tests/test_data_source_manager.py::test_data_source_manager_exists
- tests/test_data_source_manager.py::test_register_data_source
- tests/test_data_source_manager.py::test_get_price_from_multiple_sources
**Status:** Not Started
**Jules Session:** None
**Notes:** Feed tests one at a time. PR only after all 3 pass.

## Task 7: Foundation Tests
**Tests:** 3 total (existing - must stay passing)
- tests/test_foundation.py::test_all_dependencies_installed
- tests/test_foundation.py::test_basic_imports_work
- tests/test_foundation.py::test_database_connection
**Status:** Currently Passing
**Jules Session:** None
**Notes:** Monitor only. If breaks, fix immediately.

## Task 8: Dashboard Tests
**Tests:** 3 total (existing - must stay passing)
- tests/test_dashboard.py::test_dashboard_page_loads
- tests/test_dashboard.py::test_dashboard_components_render
- tests/test_dashboard.py::test_real_time_data_updates
**Status:** Currently Passing
**Jules Session:** None
**Notes:** Monitor only. If breaks, fix immediately.

## Task 9: Data Acquisition Tests
**Tests:** 4 total (existing - must stay passing)
- tests/test_data_acquisition.py::test_current_market_data_fetch
- tests/test_data_acquisition.py::test_historical_data_fetch
- tests/test_data_acquisition.py::test_trader_data_fetch
- tests/test_data_acquisition.py::test_data_source_extensibility
**Status:** Currently Passing
**Jules Session:** None
**Notes:** Monitor only. If breaks, fix immediately.

## Task 10: Fix Warnings
**Tests:** All tests must run without warnings
**Status:** Not Started
**Jules Session:** None
**Notes:** Fix SQLAlchemy and datetime deprecation warnings

---

## ORCHESTRATOR WORKFLOW

### When Jules Session is AWAITING_USER_FEEDBACK:
1. Read the question from Jules
2. Share full project context
3. Answer the question with specifics
4. Use sendMessage API

### When Jules Session is FAILED:
1. Delete the failed session
2. Launch new session with same task
3. Increment retry count
4. If retry > 3: Escalate to Architect

### When Jules Session is COMPLETED:
1. Run the specific test for that task
2. If test passes:
   - If more tests in task: Feed next test to same session
   - If all tests pass: Create PR and mark task complete
   - Assign new task to this Jules session
3. If test fails:
   - Send feedback to Jules with test output
   - Ask Jules to fix

### Continuous Actions:
- Check session status every 15 seconds
- Run full test suite every 5 minutes
- Report progress to Architect
- Update this tracking file
