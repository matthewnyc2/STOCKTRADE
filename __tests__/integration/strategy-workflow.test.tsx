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
  rest.get('/api/strategies', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          name: 'Moving Average Crossover',
          type: 'technical',
          status: 'inactive',
          createdAt: '2024-01-01T00:00:00Z',
          indicators: {
            fastMA: 20,
            slowMA: 50,
          },
        },
      ])
    )
  }),

  rest.post('/api/strategies', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.json({
        id: '1',
        name: body.name,
        type: body.type,
        status: 'inactive',
        createdAt: new Date().toISOString(),
        indicators: body.indicators,
      })
    )
  }),

  rest.put('/api/strategies/:id/activate', (req, res, ctx) => {
    return res(
      ctx.json({
        id: req.params.id,
        status: 'active',
      })
    )
  }),

  rest.get('/api/signals', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          strategyId: '1',
          symbol: 'AAPL',
          signal: 'BUY',
          price: 150.25,
          timestamp: new Date().toISOString(),
          confidence: 0.85,
        },
      ])
    )
  }),

  rest.post('/api/backtests', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.json({
        id: '1',
        status: 'completed',
        results: {
          totalTrades: 10,
          winRate: 0.6,
          profitFactor: 1.5,
          sharpeRatio: 1.2,
          equity: [10000, 10500, 11000, 10800, 11200, 11500, 12000, 11800, 12200, 12500],
        },
      })
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

const createTestRouter = (initialEntries = ['/laboratory']) => {
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

describe('Strategy Creation to Signal Generation Workflow', () => {
  it('should create strategy, activate it, and verify signals appear in dashboard', async () => {
    const router = createTestRouter(['/laboratory'])

    render(<RouterProvider router={router} />)

    // Navigate to Laboratory
    await waitFor(() => {
      expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
    })

    // Create strategy from template
    const createStrategyBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(createStrategyBtn)

    // Fill in strategy form
    const strategyNameInput = screen.getByLabelText(/Strategy Name/i)
    fireEvent.change(strategyNameInput, { target: { value: 'MA Crossover Strategy' } })

    const fastMAInput = screen.getByLabelText(/Fast MA Period/i)
    fireEvent.change(fastMAInput, { target: { value: '20' } })

    const slowMAInput = screen.getByLabelText(/Slow MA Period/i)
    fireEvent.change(slowMAInput, { target: { value: '50' } })

    const submitBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(submitBtn)

    // Verify strategy is created
    await waitFor(() => {
      expect(screen.getByText('MA Crossover Strategy')).toBeInTheDocument()
    })

    // Activate strategy
    const activateBtn = screen.getByRole('button', { name: /Activate/i })
    fireEvent.click(activateBtn)

    // Verify strategy is activated
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    // Navigate to Dashboard
    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
    fireEvent.click(dashboardLink)

    // Verify signals appear
    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
      expect(screen.getByText('BUY')).toBeInTheDocument()
      expect(screen.getByText('150.25')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
    })

    // Verify WebSocket connection is established
    expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('message', expect.any(Function))
  })

  it('should handle strategy creation errors gracefully', async () => {
    server.use(
      rest.post('/api/strategies', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Failed to create strategy' }))
      })
    )

    const router = createTestRouter(['/laboratory'])
    render(<RouterProvider router={router} />)

    // Navigate to Laboratory
    await waitFor(() => {
      expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
    })

    // Create strategy (should fail)
    const createStrategyBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(createStrategyBtn)

    // Fill and submit form
    const strategyNameInput = screen.getByLabelText(/Strategy Name/i)
    fireEvent.change(strategyNameInput, { target: { value: 'Test Strategy' } })

    const submitBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(submitBtn)

    // Verify error message appears
    await waitFor(() => {
      expect(screen.getByText(/Failed to create strategy/i)).toBeInTheDocument()
    })

    // Verify retry button works
    const retryBtn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(retryBtn)

    // Verify form is reset
    expect(strategyNameInput).toHaveValue('')
  })

  it('should handle strategy activation errors gracefully', async () => {
    server.use(
      rest.put('/api/strategies/:id/activate', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Failed to activate strategy' }))
      })
    )

    const router = createTestRouter(['/laboratory'])
    render(<RouterProvider router={router} />)

    // Navigate to Laboratory and create strategy
    await waitFor(() => {
      expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
    })

    const createStrategyBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(createStrategyBtn)

    // Fill and submit form
    const strategyNameInput = screen.getByLabelText(/Strategy Name/i)
    fireEvent.change(strategyNameInput, { target: { value: 'Test Strategy' } })

    const submitBtn = screen.getByRole('button', { name: /Create Strategy/i })
    fireEvent.click(submitBtn)

    // Wait for strategy to be created
    await waitFor(() => {
      expect(screen.getByText('Test Strategy')).toBeInTheDocument()
    })

    // Activate strategy (should fail)
    const activateBtn = screen.getByRole('button', { name: /Activate/i })
    fireEvent.click(activateBtn)

    // Verify error message appears
    await waitFor(() => {
      expect(screen.getByText(/Failed to activate strategy/i)).toBeInTheDocument()
    })
  })

  it('should update signals in real-time via WebSocket', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Mock WebSocket message event
    const mockMessage = {
      type: 'signal',
      data: {
        id: '2',
        strategyId: '1',
        symbol: 'GOOGL',
        signal: 'SELL',
        price: 2800.50,
        timestamp: new Date().toISOString(),
        confidence: 0.92,
      },
    }

    // Simulate receiving a WebSocket message
    const handleWebSocketMessage = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(mockMessage) })
    }

    // Verify new signal appears
    await waitFor(() => {
      expect(screen.getByText('GOOGL')).toBeInTheDocument()
      expect(screen.getByText('SELL')).toBeInTheDocument()
      expect(screen.getByText('2800.50')).toBeInTheDocument()
      expect(screen.getByText('92%')).toBeInTheDocument()
    })

    // Verify previous signals are still there
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('BUY')).toBeInTheDocument()
  })
})