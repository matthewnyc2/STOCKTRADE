/**
 * @jest-environment @testing-library/react
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'
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

// Mock ErrorBoundary component
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) => (
  <div role="alert">
    <h2>Something went wrong</h2>
    <pre>{error.message}</pre>
    <button onClick={resetErrorBoundary}>Try again</button>
  </div>
)

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
        },
      ])
    )
  }),

  rest.get('/api/portfolio', (req, res, ctx) => {
    return res(
      ctx.json({
        balance: 10000,
        positions: [],
        orders: [],
      })
    )
  }),

  rest.get('/api/market-data/:symbol', (req, res, ctx) => {
    const { symbol } = req.params
    return res(
      ctx.json({
        symbol,
        price: 150.00,
        change: 0.00,
        changePercent: 0.00,
        volume: 1000000,
        previousClose: 150.00,
      })
    )
  }),

  rest.get('/api/user/profile', (req, res, ctx) => {
    return res(
      ctx.json({
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        mode: 'game',
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

const createTestRouter = (initialEntries = ['/dashboard']) => {
  return createMemoryRouter(
    [
      {
        path: '/',
        element: (
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <QueryClientProvider client={new QueryClient()}>
              <AuthProvider>
                <App />
                <Toaster />
              </AuthProvider>
            </QueryClientProvider>
          </ErrorBoundary>
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

describe('Error Handling', () => {
  it('should handle API failures with error boundaries', async () => {
    // Simulate API failure
    server.use(
      rest.get('/api/strategies', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Internal server error' }))
      })
    )

    const router = createTestRouter(['/laboratory'])
    render(<RouterProvider router={router} />)

    // Navigate to Laboratory
    await waitFor(() => {
      expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
    })

    // Try to load strategies (should fail)
    const loadStrategiesBtn = screen.getByRole('button', { name: /Load Strategies/i })
    fireEvent.click(loadStrategiesBtn)

    // Verify error boundary catches the error
    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText('Internal server error')).toBeInTheDocument()
    })

    // Verify retry button works
    const retryBtn = screen.getByRole('button', { name: /Try again/i })
    fireEvent.click(retryBtn)

    // Verify user can continue using the app
    expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
  })

  it('should handle network errors gracefully', async () => {
    // Simulate network error
    server.use(
      rest.get('/api/portfolio', (req, res, ctx) => {
        return res.networkError('Failed to connect')
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify network error is handled
    await waitFor(() => {
      expect(screen.getByText('Network Error')).toBeInTheDocument()
      expect(screen.getByText('Failed to connect to the server')).toBeInTheDocument()
    })

    // Verify retry button
    const retryBtn = screen.getByRole('button', { name: /Retry/i })
    fireEvent.click(retryBtn)

    // Verify loading state
    expect(screen.getByText('Loading portfolio...')).toBeInTheDocument()
  })

  it('should handle WebSocket connection errors', async () => {
    // Mock WebSocket that fails to connect
    const failingWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      readyState: 3, // Closed
    }

    jest.mock('../src/lib/websocket', () => ({
      connectWebSocket: () => failingWebSocket,
    }))

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify WebSocket connection error is displayed
    await waitFor(() => {
      expect(screen.getByText('WebSocket Connection Failed')).toBeInTheDocument()
      expect(screen.getByText('Unable to connect to real-time data')).toBeInTheDocument()
    })

    // Verify manual reconnect option
    const reconnectBtn = screen.getByRole('button', { name: /Reconnect/i })
    expect(reconnectBtn).toBeInTheDocument()

    // Click reconnect
    fireEvent.click(reconnectBtn)

    // Verify loading state
    expect(screen.getByText('Connecting...')).toBeInTheDocument()
  })

  it('should handle authentication errors', async () => {
    // Simulate authentication error
    server.use(
      rest.get('/api/user/profile', (req, res, ctx) => {
        return res(ctx.status(401), ctx.json({ error: 'Unauthorized' }))
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify authentication error is handled
    await waitFor(() => {
      expect(screen.getByText('Authentication Error')).toBeInTheDocument()
      expect(screen.getByText('Please log in again')).toBeInTheDocument()
    })

    // Verify login prompt
    expect(screen.getByRole('button', { name: /Login/i })).toBeInTheDocument()

    // Click login
    fireEvent.click(screen.getByRole('button', { name: /Login/i }))

    // Verify redirect to login
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('should handle data validation errors', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Try to submit invalid data
    const submitBtn = screen.getByRole('button', { name: /Submit/i })
    fireEvent.click(submitBtn)

    // Verify validation error
    await waitFor(() => {
      expect(screen.getByText('Validation Error')).toBeInTheDocument()
      expect(screen.getByText('Please fill in all required fields')).toBeInTheDocument()
    })

    // Verify form shows validation errors
    expect(screen.getByText('This field is required')).toBeInTheDocument()

    // Fix validation errors and retry
    const inputField = screen.getByLabelText(/Required Field/i)
    fireEvent.change(inputField, { target: { value: 'Valid value' } })

    fireEvent.click(submitBtn)

    // Verify submission succeeds
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })

  it('should handle timeout errors', async () => {
    // Mock API with timeout
    server.use(
      rest.get('/api/market-data/AAPL', (req, res, ctx) => {
        return res(
          ctx.delay(5000), // 5 second delay
          ctx.json({
            symbol: 'AAPL',
            price: 150.00,
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

    // Request market data
    const refreshBtn = screen.getByRole('button', { name: /Refresh Data/i })
    fireEvent.click(refreshBtn)

    // Verify timeout error after 5 seconds
    await waitFor(
      () => {
        expect(screen.getByText('Request Timeout')).toBeInTheDocument()
        expect(screen.getByText('Request took too long to complete')).toBeInTheDocument()
      },
      { timeout: 6000 }
    )

    // Verify retry option
    const retryBtn = screen.getByRole('button', { name: /Retry/i })
    expect(retryBtn).toBeInTheDocument()
  })

  it('should handle rate limiting errors', async () => {
    // Mock rate limiting
    server.use(
      rest.get('/api/market-data/:symbol', (req, res, ctx) => {
        return res(
          ctx.status(429),
          ctx.json({
            error: 'Rate limit exceeded',
            retryAfter: 60,
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

    // Try to request market data
    const refreshBtn = screen.getByRole('button', { name: /Refresh Data/i })
    fireEvent.click(refreshBtn)

    // Verify rate limit error
    await waitFor(() => {
      expect(screen.getByText('Rate Limit Exceeded')).toBeInTheDocument()
      expect(screen.getByText('Please wait 60 seconds before trying again')).toBeInTheDocument()
    })

    // Verify countdown timer
    expect(screen.getByText('60s')).toBeInTheDocument()
  })

  it('should handle file upload errors', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Mock file upload error
    const uploadBtn = screen.getByRole('button', { name: /Upload File/i })
    fireEvent.click(uploadBtn)

    // Select invalid file
    const fileInput = screen.getByLabelText(/Upload File/i)
    const invalidFile = new File(['invalid content'], 'test.txt', { type: 'text/plain' })

    fireEvent.change(fileInput, { target: { files: [invalidFile] } })

    // Verify upload error
    await waitFor(() => {
      expect(screen.getByText('Upload Error')).toBeInTheDocument()
      expect(screen.getByText('Invalid file type')).toBeInTheDocument()
    })

    // Verify retry option
    const retryBtn = screen.getByRole('button', { name: /Try Again/i })
    expect(retryBtn).toBeInTheDocument()
  })

  it('should handle concurrent request errors', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Trigger multiple rapid requests
    const refreshBtn = screen.getByRole('button', { name: /Refresh Data/i })

    fireEvent.click(refreshBtn)
    fireEvent.click(refreshBtn)
    fireEvent.click(refreshBtn)

    // Verify debounce/cancel logic works
    await waitFor(() => {
      expect(screen.queryAllByText('Loading...')).toHaveLength(1) // Only one should be active
    })

    // Verify only one request completes
    await waitFor(() => {
      expect(screen.getByText('Data Updated')).toBeInTheDocument()
    })
  })

  it('should handle unexpected errors without crashing', async () => {
    // Simulate unexpected error
    const originalError = console.error
    console.error = jest.fn()

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Trigger an unexpected error
    act(() => {
      throw new Error('Unexpected error occurred')
    })

    // Verify error boundary catches the error
    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    // Verify app continues to work
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument()

    console.error = originalError
  })

  it('should provide helpful error messages to users', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Simulate API error with helpful message
    server.use(
      rest.get('/api/portfolio', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({
            error: 'Database connection failed',
            suggestion: 'Please try again in a few moments',
          })
        )
      })
    )

    // Trigger error
    const refreshBtn = screen.getByRole('button', { name: /Refresh Data/i })
    fireEvent.click(refreshBtn)

    // Verify helpful error message
    await waitFor(() => {
      expect(screen.getByText('Database connection failed')).toBeInTheDocument()
      expect(screen.getByText('Please try again in a few moments')).toBeInTheDocument()
    })
  })
})