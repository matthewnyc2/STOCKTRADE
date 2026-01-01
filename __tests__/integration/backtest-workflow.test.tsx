/**
 * @jest-environment @testing-library/react
 */
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupServer } from 'msw/node'
import { rest } from 'msw'

import App from '../src/app/layout'
import { AuthProvider } from '../src/contexts/AuthContext'
import { Toaster } from '../src/components/ui/toast'

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1,
}

// Mock WebSocket module
jest.mock('../src/lib/websocket', () => ({
  connectWebSocket: () => mockWebSocket,
}))

// Mock API handlers
const server = setupServer(
  rest.get('/api/backtests', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          strategyId: '1',
          status: 'completed',
          createdAt: '2024-01-01T00:00:00Z',
          results: {
            totalTrades: 10,
            winRate: 0.6,
            profitFactor: 1.5,
            sharpeRatio: 1.2,
          },
        },
      ])
    )
  }),

  rest.post('/api/backtests', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.json({
        id: '1',
        strategyId: body.strategyId,
        status: 'running',
        createdAt: new Date().toISOString(),
        parameters: body.parameters,
      })
    )
  }),

  rest.get('/api/backtests/:id', (req, res, ctx) => {
    const { id } = req.params
    return res(
      ctx.json({
        id,
        strategyId: '1',
        status: 'completed',
        createdAt: '2024-01-01T00:00:00Z',
        results: {
          totalTrades: 10,
          winRate: 0.6,
          profitFactor: 1.5,
          sharpeRatio: 1.2,
          equity: [10000, 10500, 11000, 10800, 11200, 11500, 12000, 11800, 12200, 12500],
          trades: [
            {
              id: '1',
              symbol: 'AAPL',
              entryDate: '2024-01-01',
              exitDate: '2024-01-05',
              entryPrice: 150,
              exitPrice: 155,
              quantity: 100,
              pnl: 500,
              type: 'BUY',
            },
          ],
        },
      })
    )
  }),

  rest.get('/api/strategies', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          name: 'Moving Average Crossover',
          type: 'technical',
          status: 'active',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ])
    )
  })
)

beforeAll(() => {
  server.listen()
})

afterEach(() => {
  server.resetHandlers()
  jest.clearAllMocks()
})

afterAll(() => {
  server.close()
})

const createTestRouter = (initialEntries = ['/backtest']) => {
  return createMemoryRouter(
    [
      {
        path: '/',
        element: (
          <QueryClientProvider client={new QueryClient()}>
            <AuthProvider>
              <App />
              <Toaster />
            </AuthProvider>
          </QueryClientProvider>
        ),
        children: [
          {
            path: '/laboratory',
            element: <div>Laboratory Page</div>,
          },
          {
            path: '/dashboard',
            element: <div>Dashboard Page</div>,
          },
          {
            path: '/backtest',
            element: <div>Backtest Page</div>,
          },
        ],
      },
    ],
    { initialEntries }
  )
}

describe('Backtest Execution Workflow', () => {
  it('should configure, run backtest, and verify results display', async () => {
    const router = createTestRouter(['/backtest'])

    render(<RouterProvider router={router} />)

    // Navigate to Backtest page
    await waitFor(() => {
      expect(screen.getByText('Backtest Page')).toBeInTheDocument()
    })

    // Select strategy
    const strategySelect = screen.getByLabelText(/Strategy/i)
    fireEvent.change(strategySelect, { target: { value: '1' } })

    // Configure backtest parameters
    const startDateInput = screen.getByLabelText(/Start Date/i)
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

    const endDateInput = screen.getByLabelText(/End Date/i)
    fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })

    const initialCapitalInput = screen.getByLabelText(/Initial Capital/i)
    fireEvent.change(initialCapitalInput, { target: { value: '10000' } })

    const commissionInput = screen.getByLabelText(/Commission/i)
    fireEvent.change(commissionInput, { target: { value: '0.001' } })

    // Run backtest
    const runBacktestBtn = screen.getByRole('button', { name: /Run Backtest/i })
    fireEvent.click(runBacktestBtn)

    // Verify backtest is running
    await waitFor(() => {
      expect(screen.getByText('Running backtest...')).toBeInTheDocument()
    })

    // Mock WebSocket message for progress
    const progressMessage = {
      type: 'backtest_progress',
      data: {
        id: '1',
        progress: 50,
        current: '2024-06-15',
      },
    }

    const handleWebSocketMessage = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(progressMessage) })
    }

    // Verify progress update
    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument()
      expect(screen.getByText('2024-06-15')).toBeInTheDocument()
    })

    // Complete backtest
    const completionMessage = {
      type: 'backtest_complete',
      data: {
        id: '1',
        results: {
          totalTrades: 10,
          winRate: 0.6,
          profitFactor: 1.5,
          sharpeRatio: 1.2,
          equity: [10000, 10500, 11000, 10800, 11200, 11500, 12000, 11800, 12200, 12500],
          trades: [
            {
              id: '1',
              symbol: 'AAPL',
              entryDate: '2024-01-01',
              exitDate: '2024-01-05',
              entryPrice: 150,
              exitPrice: 155,
              quantity: 100,
              pnl: 500,
              type: 'BUY',
            },
          ],
        },
      },
    }

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(completionMessage) })
    }

    // Verify results display
    await waitFor(() => {
      expect(screen.getByText('Backtest Complete')).toBeInTheDocument()
      expect(screen.getByText('Total Trades: 10')).toBeInTheDocument()
      expect(screen.getByText('Win Rate: 60%')).toBeInTheDocument()
      expect(screen.getByText('Profit Factor: 1.5')).toBeInTheDocument()
      expect(screen.getByText('Sharpe Ratio: 1.2')).toBeInTheDocument()
    })

    // Verify equity chart is displayed
    expect(screen.getByTestId('equity-chart')).toBeInTheDocument()

    // Verify trade list is displayed
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('BUY')).toBeInTheDocument()
    expect(screen.getByText('$500')).toBeInTheDocument()
  })

  it('should handle backtest configuration errors', async () => {
    const router = createTestRouter(['/backtest'])
    render(<RouterProvider router={router} />)

    // Navigate to Backtest page
    await waitFor(() => {
      expect(screen.getByText('Backtest Page')).toBeInTheDocument()
    })

    // Try to run backtest without selecting strategy
    const runBacktestBtn = screen.getByRole('button', { name: /Run Backtest/i })
    fireEvent.click(runBacktestBtn)

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/Please select a strategy/i)).toBeInTheDocument()
    })

    // Select strategy
    const strategySelect = screen.getByLabelText(/Strategy/i)
    fireEvent.change(strategySelect, { target: { value: '1' } })

    // Set invalid date range
    const startDateInput = screen.getByLabelText(/Start Date/i)
    fireEvent.change(startDateInput, { target: { value: '2024-12-31' } })

    const endDateInput = screen.getByLabelText(/End Date/i)
    fireEvent.change(endDateInput, { target: { value: '2024-01-01' } })

    // Try to run backtest with invalid dates
    fireEvent.click(runBacktestBtn)

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/End date must be after start date/i)).toBeInTheDocument()
    })
  })

  it('should handle backtest execution errors', async () => {
    server.use(
      rest.post('/api/backtests', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Backtest execution failed' }))
      })
    )

    const router = createTestRouter(['/backtest'])
    render(<RouterProvider router={router} />)

    // Navigate to Backtest page
    await waitFor(() => {
      expect(screen.getByText('Backtest Page')).toBeInTheDocument()
    })

    // Configure and run backtest
    const strategySelect = screen.getByLabelText(/Strategy/i)
    fireEvent.change(strategySelect, { target: { value: '1' } })

    const startDateInput = screen.getByLabelText(/Start Date/i)
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

    const endDateInput = screen.getByLabelText(/End Date/i)
    fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })

    const runBacktestBtn = screen.getByRole('button', { name: /Run Backtest/i })
    fireEvent.click(runBacktestBtn)

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/Backtest execution failed/i)).toBeInTheDocument()
    })

    // Verify retry button works
    const retryBtn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(retryBtn)

    // Verify form is reset
    expect(strategySelect).toHaveValue('1')
    expect(startDateInput).toHaveValue('2024-01-01')
    expect(endDateInput).toHaveValue('2024-12-31')
  })

  it('should allow saving backtest results', async () => {
    const router = createTestRouter(['/backtest'])
    render(<RouterProvider router={router} />)

    // Navigate to Backtest page and complete backtest
    await waitFor(() => {
      expect(screen.getByText('Backtest Page')).toBeInTheDocument()
    })

    // (Simulate completing backtest as in previous test)
    const strategySelect = screen.getByLabelText(/Strategy/i)
    fireEvent.change(strategySelect, { target: { value: '1' } })

    const startDateInput = screen.getByLabelText(/Start Date/i)
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

    const endDateInput = screen.getByLabelText(/End Date/i)
    fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })

    const runBacktestBtn = screen.getByRole('button', { name: /Run Backtest/i })
    fireEvent.click(runBacktestBtn)

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Backtest Complete')).toBeInTheDocument()
    })

    // Click save button
    const saveBtn = screen.getByRole('button', { name: /Save Results/i })
    fireEvent.click(saveBtn)

    // Verify success message
    await waitFor(() => {
      expect(screen.getByText(/Backtest results saved successfully/i)).toBeInTheDocument()
    })
  })

  it('should compare multiple backtest results', async () => {
    const router = createTestRouter(['/backtest'])
    render(<RouterProvider router={router} />)

    // Navigate to Backtest page
    await waitFor(() => {
      expect(screen.getByText('Backtest Page')).toBeInTheDocument()
    })

    // Configure and run first backtest
    const strategySelect = screen.getByLabelText(/Strategy/i)
    fireEvent.change(strategySelect, { target: { value: '1' } })

    const startDateInput = screen.getByLabelText(/Start Date/i)
    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })

    const endDateInput = screen.getByLabelText(/End Date/i)
    fireEvent.change(endDateInput, { target: { value: '2024-06-30' } })

    const runBacktestBtn = screen.getByRole('button', { name: /Run Backtest/i })
    fireEvent.click(runBacktestBtn)

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('Backtest Complete')).toBeInTheDocument()
    })

    // Configure and run second backtest with different parameters
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } })
    fireEvent.change(endDateInput, { target: { value: '2024-12-31' } })
    fireEvent.click(runBacktestBtn)

    // Wait for second completion
    await waitFor(() => {
      expect(screen.getAllByText('Backtest Complete')).toHaveLength(2)
    })

    // Click compare button
    const compareBtn = screen.getByRole('button', { name: /Compare/i })
    fireEvent.click(compareBtn)

    // Verify comparison view
    await waitFor(() => {
      expect(screen.getByText('Backtest Comparison')).toBeInTheDocument()
      expect(screen.getAllByText('Total Trades')).toHaveLength(2)
    })
  })
})