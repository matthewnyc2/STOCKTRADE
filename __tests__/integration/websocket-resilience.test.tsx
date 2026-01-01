/**
 * @jest-environment @testing-library/react
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupServer } from 'msw/node'
import { rest } from 'msw'

import App from '../src/app/layout'
import { AuthProvider } from '../src/contexts/AuthContext'
import { Toaster } from '../src/components/ui/toast'

// Mock WebSocket implementation that simulates disconnection
class MockWebSocket {
  private listeners: { [event: string]: Function[] } = {}
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false

  constructor(private url: string) {
    this.connect()
  }

  private connect() {
    this.isConnecting = true

    // Simulate connection delay
    setTimeout(() => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.readyState = 1
        this.isConnecting = false

        // Emit open event
        this.emit('open')

        // Emit initial data
        this.emit('message', {
          data: JSON.stringify({
            type: 'connection_status',
            data: { connected: true }
          })
        })
      } else {
        this.emit('error', new Error('Max reconnection attempts reached'))
      }
    }, 500)
  }

  addEventListener(event: string, listener: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(listener)
  }

  removeEventListener(event: string, listener: Function) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(l => l !== listener)
    }
  }

  private emit(event: string, data?: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(listener => listener(data))
    }
  }

  send(data: string) {
    this.emit('message', {
      data: JSON.stringify({
        type: 'echo',
        data: JSON.parse(data)
      })
    })
  }

  close() {
    this.readyState = 3
    this.emit('close')
  }

  disconnect() {
    this.close()
  }

  simulateReconnect() {
    this.reconnectAttempts++
    this.connect()
  }

  readyState = 0
}

// Global WebSocket mock
let mockWebSocketInstance: MockWebSocket

jest.mock('../src/lib/websocket', () => ({
  connectWebSocket: (url: string) => {
    mockWebSocketInstance = new MockWebSocket(url)
    return mockWebSocketInstance
  },
}))

// Mock API handlers
const server = setupServer(
  rest.get('/api/portfolio', (req, res, ctx) => {
    return res(
      ctx.json({
        balance: 10000,
        positions: [],
        orders: [],
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

describe('WebSocket Resilience', () => {
  beforeEach(() => {
    mockWebSocketInstance = new MockWebSocket('ws://localhost:3001')
  })

  afterEach(() => {
    if (mockWebSocketInstance) {
      mockWebSocketInstance.close()
    }
  })

  it('should handle WebSocket connection and disconnection gracefully', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify WebSocket connects
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Disconnect WebSocket
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    // Verify disconnection is detected
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    // Verify reconnect attempt is made
    await waitFor(() => {
      expect(screen.getByText('Reconnecting...')).toBeInTheDocument()
    })

    // Simulate successful reconnection
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    // Verify reconnection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  it('should handle multiple WebSocket disconnections and reconnections', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Simulate multiple disconnections
    for (let i = 0; i < 3; i++) {
      act(() => {
        mockWebSocketInstance.disconnect()
      })

      await waitFor(() => {
        expect(screen.getByText('Disconnected')).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(screen.getByText('Reconnecting...')).toBeInTheDocument()
      })

      act(() => {
        mockWebSocketInstance.simulateReconnect()
      })

      await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument()
      })
    }
  })

  it('should handle WebSocket reconnection with exponential backoff', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Disconnect and verify reconnection delays
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    // Mock exponential backoff delays
    jest.useFakeTimers()

    // Fast forward timers
    act(() => {
      jest.advanceTimersByTime(1000)
    })

    expect(screen.getByText('Reconnecting...')).toBeInTheDocument()

    act(() => {
      jest.advanceTimersByTime(2000)
    })

    // Simulate successful reconnection
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    jest.useRealTimers()

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  it('should handle WebSocket reconnection failures gracefully', async () => {
    // Create a WebSocket that fails to reconnect
    class FailingMockWebSocket extends MockWebSocket {
      connect() {
        this.isConnecting = true

        // Simulate connection failure
        setTimeout(() => {
          this.isConnecting = false
          this.emit('error', new Error('Connection failed'))
          this.emit('close')
        }, 500)
      }
    }

    const originalConnectWebSocket = require('../src/lib/websocket').connectWebSocket
    jest.mock('../src/lib/websocket', () => ({
      connectWebSocket: (url: string) => new FailingMockWebSocket(url),
    }))

    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Disconnect
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    // Verify failure is handled
    await waitFor(() => {
      expect(screen.getByText('Connection Failed')).toBeInTheDocument()
    })

    // Verify manual reconnect button appears
    expect(screen.getByRole('button', { name: /Reconnect/i })).toBeInTheDocument()

    // Manual reconnect
    const reconnectBtn = screen.getByRole('button', { name: /Reconnect/i })
    fireEvent.click(reconnectBtn)

    // Verify reconnection attempt
    await waitFor(() => {
      expect(screen.getByText('Reconnecting...')).toBeInTheDocument()
    })
  })

  it('should maintain data integrity during reconnection', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Send some data through WebSocket
    act(() => {
      mockWebSocketInstance.send(JSON.stringify({
        type: 'test_message',
        data: { message: 'Hello World' }
      }))
    })

    // Verify message is received
    await waitFor(() => {
      expect(screen.getByText('Hello World')).toBeInTheDocument()
    })

    // Disconnect while waiting for messages
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    // Reconnect and verify data integrity
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Verify previous data is still there
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('should handle WebSocket message queue during disconnection', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Disconnect WebSocket
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    // Send messages during disconnection (should be queued)
    act(() => {
      mockWebSocketInstance.send(JSON.stringify({
        type: 'queued_message_1',
        data: { message: 'Queued 1' }
      }))
    })

    act(() => {
      mockWebSocketInstance.send(JSON.stringify({
        type: 'queued_message_2',
        data: { message: 'Queued 2' }
      }))
    })

    // Verify messages are not displayed yet
    expect(screen.queryByText('Queued 1')).not.toBeInTheDocument()
    expect(screen.queryByText('Queued 2')).not.toBeInTheDocument()

    // Reconnect
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    // Verify queued messages are processed
    await waitFor(() => {
      expect(screen.getByText('Queued 1')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Queued 2')).toBeInTheDocument()
    })
  })

  it('should display WebSocket connection status indicators', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Verify connection status indicator shows connected
    const statusIndicator = screen.getByTestId('connection-status')
    expect(statusIndicator).toHaveTextContent('Connected')
    expect(statusIndicator).toHaveClass('bg-green-500')

    // Disconnect
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    // Verify status indicator updates
    await waitFor(() => {
      expect(statusIndicator).toHaveTextContent('Disconnected')
      expect(statusIndicator).toHaveClass('bg-red-500')
    })

    // Reconnect
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    // Verify status indicator updates back
    await waitFor(() => {
      expect(statusIndicator).toHaveTextContent('Connected')
      expect(statusIndicator).toHaveClass('bg-green-500')
    })
  })

  it('should handle WebSocket authentication during reconnection', async () => {
    const router = createTestRouter(['/dashboard'])
    render(<RouterProvider router={router} />)

    // Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
    })

    // Initial connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    // Disconnect
    act(() => {
      mockWebSocketInstance.disconnect()
    })

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    // Reconnect with auth message
    act(() => {
      mockWebSocketInstance.simulateReconnect()
    })

    // Send authentication message
    act(() => {
      mockWebSocketInstance.send(JSON.stringify({
        type: 'auth',
        data: { token: 'test-token' }
      }))
    })

    // Verify auth is processed
    await waitFor(() => {
      expect(screen.getByText('Authenticated')).toBeInTheDocument()
    })
  })
})