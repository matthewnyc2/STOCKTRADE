/**
 * @jest-environment @testing-library/react
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupServer } from 'msw/node'
import { rest } from 'msw'

import App from '../src/app/layout'
import { AuthProvider } from '../src/contexts/AuthContext'
import { Toaster } from '../src/components/ui/toast'

// Mock API handlers
const server = setupServer(
  rest.get('/api/user/settings', (req, res, ctx) => {
    const mode = req.url.searchParams.get('mode') || 'game'
    return res(
      ctx.json({
        mode,
        preferences: {
          theme: 'light',
          notifications: true,
          tradingMode: mode,
        },
      })
    )
  }),

  rest.put('/api/user/settings', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.json({
        mode: body.mode,
        preferences: {
          theme: body.preferences?.theme || 'light',
          notifications: body.preferences?.notifications || true,
          tradingMode: body.mode,
        },
      })
    )
  }),

  rest.get('/api/game/features', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'virtual_funds',
          name: 'Virtual Funds',
          description: 'Trade with play money',
          enabled: true,
        },
        {
          id: 'tutorial_hints',
          name: 'Tutorial Hints',
          description: 'Get helpful tips while trading',
          enabled: true,
        },
        {
          id: 'leaderboard',
          name: 'Leaderboard',
          description: 'Compare with other traders',
          enabled: true,
        },
      ])
    )
  }),

  rest.get('/api/pro/features', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'advanced_indicators',
          name: 'Advanced Indicators',
          description: 'Access professional trading indicators',
          enabled: true,
        },
        {
          id: 'paper_trading',
          name: 'Paper Trading',
          description: 'Real market simulation',
          enabled: true,
        },
        {
          id: 'api_access',
          name: 'API Access',
          description: 'Direct API integration',
          enabled: true,
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
          status: 'inactive',
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

describe('Mode Switching', () => {
  it('should switch from Game Mode to Pro Mode and verify UI changes', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify starting in Game Mode
    expect(screen.getByText('Game Mode')).toBeInTheDocument()
    expect(screen.getByText('Virtual Balance: $10,000')).toBeInTheDocument()

    // Find and click mode switcher
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    // Verify confirmation dialog appears
    await waitFor(() => {
      expect(screen.getByText('Switch to Pro Mode?')).toBeInTheDocument()
      expect(screen.getByText('This will enable real trading capabilities.')).toBeInTheDocument()
    })

    // Confirm switch
    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify loading state
    await waitFor(() => {
      expect(screen.getByText('Switching modes...')).toBeInTheDocument()
    })

    // Verify switch to Pro Mode
    await waitFor(() => {
      expect(screen.getByText('Pro Mode')).toBeInTheDocument()
      expect(screen.getByText('Real Trading Enabled')).toBeInTheDocument()
    })

    // Verify UI changes
    expect(screen.queryByText('Virtual Balance: $10,000')).not.toBeInTheDocument()
    expect(screen.getByText('Available Balance: $0.00')).toBeInTheDocument()

    // Verify Pro features are visible
    expect(screen.getByText('Advanced Indicators')).toBeInTheDocument()
    expect(screen.getByText('API Access')).toBeInTheDocument()
  })

  it('should switch from Pro Mode to Game Mode and verify UI changes', async () => {
    // Start in Pro Mode
    server.use(
      rest.get('/api/user/settings', (req, res, ctx) => {
        return res(
          ctx.json({
            mode: 'pro',
            preferences: {
              theme: 'light',
              notifications: true,
              tradingMode: 'pro',
            },
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

    // Verify starting in Pro Mode
    expect(screen.getByText('Pro Mode')).toBeInTheDocument()
    expect(screen.getByText('Real Trading Enabled')).toBeInTheDocument()

    // Find and click mode switcher
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Game Mode/i })
    fireEvent.click(modeSwitcher)

    // Verify confirmation dialog appears
    await waitFor(() => {
      expect(screen.getByText('Switch to Game Mode?')).toBeInTheDocument()
      expect(screen.getByText('This will disable real trading.')).toBeInTheDocument()
    })

    // Confirm switch
    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify loading state
    await waitFor(() => {
      expect(screen.getByText('Switching modes...')).toBeInTheDocument()
    })

    // Verify switch to Game Mode
    await waitFor(() => {
      expect(screen.getByText('Game Mode')).toBeInTheDocument()
      expect(screen.getByText('Virtual Balance: $10,000')).toBeInTheDocument()
    })

    // Verify UI changes
    expect(screen.queryByText('Real Trading Enabled')).not.toBeInTheDocument()
    expect(screen.getByText('Tutorial Hints')).toBeInTheDocument()
  })

  it('should persist mode choice across page reloads', async () => {
    // Set initial mode to Pro
    server.use(
      rest.get('/api/user/settings', (req, res, ctx) => {
        return res(
          ctx.json({
            mode: 'pro',
            preferences: {
              theme: 'light',
              notifications: true,
              tradingMode: 'pro',
            },
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

    // Verify Pro Mode
    expect(screen.getByText('Pro Mode')).toBeInTheDocument()

    // Navigate to Laboratory
    const laboratoryLink = screen.getByRole('link', { name: /Laboratory/i })
    fireEvent.click(laboratoryLink)

    await waitFor(() => {
      expect(screen.getByText('Laboratory Page')).toBeInTheDocument()
    })

    // Verify Pro Mode is still active
    expect(screen.getByText('Pro Mode')).toBeInTheDocument()

    // Navigate to Dashboard again
    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
    fireEvent.click(dashboardLink)

    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify Pro Mode is still active
    expect(screen.getByText('Pro Mode')).toBeInTheDocument()
  })

  it('should handle mode switch errors gracefully', async () => {
    server.use(
      rest.put('/api/user/settings', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Failed to update mode' }))
      })
    )

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Try to switch modes
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    // Confirm switch
    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to update mode/i)).toBeInTheDocument()
    })

    // Verify mode remains unchanged
    expect(screen.getByText('Game Mode')).toBeInTheDocument()
  })

  it('should show different features based on mode', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify Game Mode features
    expect(screen.getByText('Tutorial Hints')).toBeInTheDocument()
    expect(screen.getByText('Leaderboard')).toBeInTheDocument()

    // Switch to Pro Mode
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify Pro Mode features
    await waitFor(() => {
      expect(screen.getByText('Advanced Indicators')).toBeInTheDocument()
      expect(screen.getByText('Paper Trading')).toBeInTheDocument()
      expect(screen.getByText('API Access')).toBeInTheDocument()
    })

    // Verify Game Mode features are hidden
    expect(screen.queryByText('Tutorial Hints')).not.toBeInTheDocument()
    expect(screen.queryByText('Leaderboard')).not.toBeInTheDocument()
  })

  it('should display appropriate trading interface based on mode', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify Game Mode trading interface
    expect(screen.getByText('Virtual Balance: $10,000')).toBeInTheDocument()
    expect(screen.getByText('No Real Money Risk')).toBeInTheDocument()

    // Switch to Pro Mode
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify Pro Mode trading interface
    await waitFor(() => {
      expect(screen.getByText('Available Balance: $0.00')).toBeInTheDocument()
      expect(screen.getByText('Real Money Trading')).toBeInTheDocument()
    })
  })

  it('should handle mode switch during active trading session', async () => {
    // Mock WebSocket for real-time updates
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      readyState: 1,
    }

    jest.mock('../src/lib/websocket', () => ({
      connectWebSocket: () => mockWebSocket,
    }))

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Simulate open position in Game Mode
    const openPositionBtn = screen.getByRole('button', { name: /Open Position/i })
    fireEvent.click(openPositionBtn)

    // Verify position is opened
    await waitFor(() => {
      expect(screen.getByText('Position Opened')).toBeInTheDocument()
    })

    // Switch to Pro Mode
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify warning about switching with open position
    await waitFor(() => {
      expect(screen.getByText('Warning: Open positions will be closed')).toBeInTheDocument()
    })

    // Confirm switch anyway
    const proceedBtn = screen.getByRole('button', { name: /Proceed/i })
    fireEvent.click(proceedBtn)

    // Verify position is closed
    await waitFor(() => {
      expect(screen.queryByText('Position Opened')).not.toBeInTheDocument()
    })
  })

  it('should show mode-specific documentation and tutorials', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify Game Mode tutorial section
    expect(screen.getByText('Getting Started Guide')).toBeInTheDocument()

    // Switch to Pro Mode
    const modeSwitcher = screen.getByRole('button', { name: /Switch to Pro Mode/i })
    fireEvent.click(modeSwitcher)

    const confirmBtn = screen.getByRole('button', { name: /Confirm/i })
    fireEvent.click(confirmBtn)

    // Verify Pro Mode documentation section
    await waitFor(() => {
      expect(screen.getByText('Pro Trading Manual')).toBeInTheDocument()
      expect(screen.getByText('API Documentation')).toBeInTheDocument()
    })
  })
})