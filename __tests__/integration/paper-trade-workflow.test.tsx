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
  rest.get('/api/portfolio', (req, res, ctx) => {
    return res(
      ctx.json({
        balance: 10000,
        positions: [
          {
            id: '1',
            symbol: 'AAPL',
            quantity: 100,
            averagePrice: 150.25,
            currentPrice: 155.00,
            pnl: 475,
            pnlPercent: 3.16,
          },
        ],
        orders: [],
      })
    )
  }),

  rest.post('/api/orders', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.json({
        id: '1',
        type: body.type,
        symbol: body.symbol,
        quantity: body.quantity,
        price: body.price,
        status: 'filled',
        filledAt: new Date().toISOString(),
      })
    )
  }),

  rest.get('/api/market-data/:symbol', (req, res, ctx) => {
    const { symbol } = req.params
    return res(
      ctx.json({
        symbol,
        price: 155.00,
        change: 4.75,
        changePercent: 3.16,
        volume: 1000000,
        previousClose: 150.25,
      })
    )
  }),

  rest.get('/api/portfolio/history', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          type: 'buy',
          symbol: 'AAPL',
          quantity: 100,
          price: 150.25,
          timestamp: new Date().toISOString(),
        },
      ])
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

const createTestRouter = (initialEntries = ['/dashboard']) => {
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

describe('Paper Trading Workflow', () => {
  it('should execute paper trade and verify position updates', async () => {
    const router = createTestRouter(['/dashboard'])

    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Check portfolio section
    const portfolioSection = screen.getByTestId('portfolio-section')
    expect(within(portfolioSection).getByText('Portfolio')).toBeInTheDocument()

    // Find trade button for AAPL
    const tradeBtn = within(portfolioSection).getByRole('button', { name: /Trade AAPL/i })
    fireEvent.click(tradeBtn)

    // Verify trade modal appears
    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    // Place buy order
    const quantityInput = screen.getByLabelText(/Quantity/i)
    fireEvent.change(quantityInput, { target: { value: '100' } })

    const priceInput = screen.getByLabelText(/Price/i)
    fireEvent.change(priceInput, { target: { value: '150.25' } })

    const buyBtn = screen.getByRole('button', { name: /Buy/i })
    fireEvent.click(buyBtn)

    // Verify order is placed
    await waitFor(() => {
      expect(screen.getByText('Order Placed')).toBeInTheDocument()
    })

    // Mock WebSocket message for filled order
    const fillMessage = {
      type: 'order_filled',
      data: {
        id: '1',
        type: 'buy',
        symbol: 'AAPL',
        quantity: 100,
        price: 150.25,
        timestamp: new Date().toISOString(),
      },
    }

    const handleWebSocketMessage = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(fillMessage) })
    }

    // Verify position appears in portfolio
    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('150.25')).toBeInTheDocument()
    })

    // Place sell order
    const sellBtn = within(portfolioSection).getByRole('button', { name: /Sell AAPL/i })
    fireEvent.click(sellBtn)

    // Verify trade modal appears
    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    // Set sell quantity
    fireEvent.change(quantityInput, { target: { value: '50' } })
    fireEvent.change(priceInput, { target: { value: '155.00' } })

    const submitSellBtn = screen.getByRole('button', { name: /Sell/i })
    fireEvent.click(submitSellBtn)

    // Verify partial position update
    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument()
      expect(screen.getByText('50')).toBeInTheDocument() // Partial sell
    })
  })

  it('should update P&L in real-time via WebSocket', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // (Simulate opening a position first)
    const portfolioSection = screen.getByTestId('portfolio-section')
    const tradeBtn = within(portfolioSection).getByRole('button', { name: /Trade AAPL/i })
    fireEvent.click(tradeBtn)

    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    const quantityInput = screen.getByLabelText(/Quantity/i)
    fireEvent.change(quantityInput, { target: { value: '100' } })

    const priceInput = screen.getByLabelText(/Price/i)
    fireEvent.change(priceInput, { target: { value: '150.25' } })

    const buyBtn = screen.getByRole('button', { name: /Buy/i })
    fireEvent.click(buyBtn)

    // Mock WebSocket message for price update
    const priceUpdateMessage = {
      type: 'price_update',
      data: {
        symbol: 'AAPL',
        price: 160.00,
        change: 9.75,
        changePercent: 6.49,
      },
    }

    const handleWebSocketMessage = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(priceUpdateMessage) })
    }

    // Verify P&L updates
    await waitFor(() => {
      expect(screen.getByText('$975.00')).toBeInTheDocument() // $9.75 profit per share
      expect(screen.getByText('6.49%')).toBeInTheDocument()
    })

    // Mock another price update
    const priceUpdateMessage2 = {
      type: 'price_update',
      data: {
        symbol: 'AAPL',
        price: 145.00,
        change: -5.25,
        changePercent: -3.49,
      },
    }

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(priceUpdateMessage2) })
    }

    // Verify P&L updates to loss
    await waitFor(() => {
      expect(screen.getByText('-$525.00')).toBeInTheDocument() // -$5.25 loss per share
      expect(screen.getByText('-3.49%')).toBeInTheDocument()
    })
  })

  it('should handle order execution errors', async () => {
    server.use(
      rest.post('/api/orders', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Insufficient funds' }))
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Try to place order with insufficient funds
    const portfolioSection = screen.getByTestId('portfolio-section')
    const tradeBtn = within(portfolioSection).getByRole('button', { name: /Trade AAPL/i })
    fireEvent.click(tradeBtn)

    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    const quantityInput = screen.getByLabelText(/Quantity/i)
    fireEvent.change(quantityInput, { target: { value: '100000' } }) // Large quantity

    const priceInput = screen.getByLabelText(/Price/i)
    fireEvent.change(priceInput, { target: { value: '150.25' } })

    const buyBtn = screen.getByRole('button', { name: /Buy/i })
    fireEvent.click(buyBtn)

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/Insufficient funds/i)).toBeInTheDocument()
    })

    // Verify order form is reset
    expect(quantityInput).toHaveValue('')
    expect(priceInput).toHaveValue('')
  })

  it('should handle order cancellation', async () => {
    server.use(
      rest.post('/api/orders', async (req, res, ctx) => {
        const body = await req.json()
        return res(
          ctx.json({
            id: '1',
            type: body.type,
            symbol: body.symbol,
            quantity: body.quantity,
            price: body.price,
            status: 'pending',
            createdAt: new Date().toISOString(),
          })
        )
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Place pending order
    const portfolioSection = screen.getByTestId('portfolio-section')
    const tradeBtn = within(portfolioSection).getByRole('button', { name: /Trade AAPL/i })
    fireEvent.click(tradeBtn)

    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    const quantityInput = screen.getByLabelText(/Quantity/i)
    fireEvent.change(quantityInput, { target: { value: '100' } })

    const priceInput = screen.getByLabelText(/Price/i)
    fireEvent.change(priceInput, { target: { value: '150.25' } })

    const buyBtn = screen.getByRole('button', { name: /Buy/i })
    fireEvent.click(buyBtn)

    // Verify pending order
    await waitFor(() => {
      expect(screen.getByText('Order Pending')).toBeInTheDocument()
    })

    // Cancel order
    const cancelBtn = screen.getByRole('button', { name: /Cancel/i })
    fireEvent.click(cancelBtn)

    // Verify order is cancelled
    await waitFor(() => {
      expect(screen.getByText('Order Cancelled')).toBeInTheDocument()
    })

    // Verify order is removed from active orders
    expect(screen.queryByText('Order Pending')).not.toBeInTheDocument()
  })

  it('should display portfolio performance metrics', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify portfolio summary displays
    expect(screen.getByText('Total Balance: $10,000.00')).toBeInTheDocument()

    // (Simulate position and P&L)
    const priceUpdateMessage = {
      type: 'price_update',
      data: {
        symbol: 'AAPL',
        price: 160.00,
        change: 9.75,
        changePercent: 6.49,
      },
    }

    const handleWebSocketMessage = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    if (handleWebSocketMessage) {
      handleWebSocketMessage({ data: JSON.stringify(priceUpdateMessage) })
    }

    // Verify portfolio value updates
    await waitFor(() => {
      expect(screen.getByText('Total Value: $10,975.00')).toBeInTheDocument()
      expect(screen.getByText('Total P&L: $975.00')).toBeInTheDocument()
      expect(screen.getByText('Total Return: 9.75%')).toBeInTheDocument()
    })
  })

  it('should handle order modifications', async () => {
    server.use(
      rest.post('/api/orders', async (req, res, ctx) => {
        const body = await req.json()
        return res(
          ctx.json({
            id: '1',
            type: body.type,
            symbol: body.symbol,
            quantity: body.quantity,
            price: body.price,
            status: 'pending',
            createdAt: new Date().toISOString(),
          })
        )
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Place pending buy order
    const portfolioSection = screen.getByTestId('portfolio-section')
    const tradeBtn = within(portfolioSection).getByRole('button', { name: /Trade AAPL/i })
    fireEvent.click(tradeBtn)

    await waitFor(() => {
      expect(screen.getByText('Place Order')).toBeInTheDocument()
    })

    const quantityInput = screen.getByLabelText(/Quantity/i)
    fireEvent.change(quantityInput, { target: { value: '100' } })

    const priceInput = screen.getByLabelText(/Price/i)
    fireEvent.change(priceInput, { target: { value: '150.25' } })

    const buyBtn = screen.getByRole('button', { name: /Buy/i })
    fireEvent.click(buyBtn)

    // Verify pending order
    await waitFor(() => {
      expect(screen.getByText('Order Pending')).toBeInTheDocument()
    })

    // Modify order
    const modifyBtn = screen.getByRole('button', { name: /Modify/i })
    fireEvent.click(modifyBtn)

    // Update quantity and price
    fireEvent.change(quantityInput, { target: { value: '150' } })
    fireEvent.change(priceInput, { target: { value: '149.50' } })

    const updateBtn = screen.getByRole('button', { name: /Update Order/i })
    fireEvent.click(updateBtn)

    // Verify order is updated
    await waitFor(() => {
      expect(screen.getByText('Order Updated')).toBeInTheDocument()
      expect(screen.getByText('150')).toBeInTheDocument()
      expect(screen.getByText('149.50')).toBeInTheDocument()
    })
  })
})