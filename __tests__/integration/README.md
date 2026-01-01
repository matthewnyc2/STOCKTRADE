# Integration Tests

This directory contains comprehensive integration tests for the STOCKTRADE frontend application.

## Test Structure

### 1. Strategy Workflow Tests (`strategy-workflow.test.tsx`)
Tests the end-to-end workflow from strategy creation to signal generation.

**Test Coverage:**
- Creating strategies from templates
- Activating strategies
- Navigating between pages
- Real-time signal updates via WebSocket
- Error handling for strategy operations

### 2. Backtest Workflow Tests (`backtest-workflow.test.tsx`)
Tests the backtest execution and results display workflow.

**Test Coverage:**
- Configuring backtest parameters
- Running backtests with progress tracking
- Displaying results and charts
- Comparing multiple backtests
- Saving backtest results

### 3. Paper Trading Workflow Tests (`paper-trade-workflow.test.tsx`)
Tests the paper trading execution and portfolio management workflow.

**Test Coverage:**
- Placing buy/sell orders
- Position management
- Real-time P&L updates
- Order modification and cancellation
- Portfolio performance metrics

### 4. WebSocket Resilience Tests (`websocket-resilience.test.tsx`)
Tests WebSocket connection handling and reconnection logic.

**Test Coverage:**
- Connection establishment
- Disconnection handling
- Reconnection with exponential backoff
- Message queuing during disconnection
- Data integrity during reconnection

### 5. Mode Switching Tests (`mode-switching.test.tsx`)
Tests switching between Game Mode and Pro Mode.

**Test Coverage:**
- Mode switching UI flow
- Feature availability based on mode
- Persistent mode preference
- Trading interface differences
- Active position handling during mode switch

### 6. Error Handling Tests (`error-handling.test.tsx`)
Tests error boundaries and error recovery mechanisms.

**Test Coverage:**
- API failure handling
- Network error recovery
- WebSocket connection errors
- Authentication errors
- Data validation errors
- Timeout and rate limiting errors

## Test Utilities

### `test-utils.ts`
Provides common utilities for testing:
- Custom render function with providers
- Mock WebSocket implementation
- LocalStorage mock
- Network mocking utilities
- Performance measurement
- Accessibility testing utilities

### `setup.ts`
Global test setup file:
- Mocks for external libraries
- JSDOM environment setup
- Common test configuration
- Suppression of console errors

## Running Tests

### Run all integration tests:
```bash
npm run test:integration
```

### Run integration tests in watch mode:
```bash
npm run test:integration:watch
```

### Run integration tests with coverage:
```bash
npm run test:integration:coverage
```

### Run all tests including unit tests:
```bash
npm test
```

## Test Environment

Integration tests use:
- **Jest** as the test runner
- **Testing Library** for React component testing
- **MSW** (Mock Service Worker) for API mocking
- **JSDOM** for browser environment simulation
- **React Query** mocking for data fetching

## Mock Data

All tests use mock data to simulate:
- API responses
- WebSocket messages
- User sessions
- Portfolio data
- Market data
- Trading signals

## Error Scenarios

Tests cover various error scenarios:
- Network failures
- API timeouts
- Authentication errors
- Validation errors
- WebSocket disconnections
- Rate limiting

## Performance Considerations

Tests are designed to:
- Run quickly with mocked dependencies
- Avoid actual network calls
- Use fake timers for async operations
- Clean up between tests
- Minimize test flakiness

## Adding New Tests

When adding new integration tests:

1. **Create a new test file** in the integration directory
2. **Use the test utilities** from `test-utils.ts`
3. **Mock all external dependencies**
4. **Test happy and error paths**
5. **Document test coverage** in this README
6. **Follow the naming convention**: `feature-workflow.test.tsx`

## Best Practices

1. **Test user behavior, not implementation**
2. **Mock external dependencies**
3. **Test error boundaries**
4. **Use meaningful test descriptions**
5. **Keep tests isolated**
6. **Test both success and failure scenarios**
7. **Update mocks when API changes**
8. **Run tests before committing**