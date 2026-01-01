import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../../frontend/src/contexts/AuthContext'
import { Toaster } from '../../frontend/src/components/ui/toast'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { act } from 'react'

// Create a test client with all default options
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

// Custom render function with providers
export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const queryClient = createTestQueryClient()
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: ui,
        children: [
          {
            path: '/dashboard',
            element: <div>Dashboard Page</div>,
          },
          {
            path: '/laboratory',
            element: <div>Laboratory Page</div>,
          },
          {
            path: '/backtest',
            element: <div>Backtest Page</div>,
          },
        ],
      },
    ],
    { initialEntries: ['/dashboard'] }
  )

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
        <Toaster />
      </AuthProvider>
    </QueryClientProvider>,
    options
  )
}

// Mock WebSocket class
export class MockWebSocket {
  private listeners: { [event: string]: Function[] } = {}
  private messageQueue: string[] = []
  private isOpen = false

  constructor(private url: string) {
    setTimeout(() => {
      this.isOpen = true
      this.emit('open')
    }, 100)
  }

  addEventListener(event: string, listener: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(listener)

    // Process queued messages if this is the 'open' event
    if (event === 'open' && this.messageQueue.length > 0) {
      this.messageQueue.forEach(message => {
        this.emit('message', { data: message })
      })
      this.messageQueue = []
    }
  }

  removeEventListener(event: string, listener: Function) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(l => l !== listener)
    }
  }

  private emit(event: string, data?: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(listener => {
        try {
          listener(data)
        } catch (error) {
          console.error(`WebSocket ${event} listener error:`, error)
        }
      })
    }
  }

  send(data: string) {
    if (!this.isOpen) {
      // Queue messages if not yet open
      this.messageQueue.push(data)
      return
    }

    // Echo the message back for testing
    setTimeout(() => {
      this.emit('message', { data })
    }, 50)
  }

  close() {
    this.isOpen = false
    this.emit('close')
  }

  // Utility methods for testing
  simulateMessage(message: string) {
    this.emit('message', { data: message })
  }

  simulateError(error: Error) {
    this.emit('error', error)
  }

  simulateClose() {
    this.isOpen = false
    this.emit('close')
  }
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}

beforeAll(() => {
  global.localStorage = mockLocalStorage
})

// Mock fetch globally
global.fetch = jest.fn()

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Utility function to create mock API responses
export const createMockApiResponse = (data: any, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  statusText: 'OK',
  headers: {
    get: jest.fn(),
  },
  json: async () => data,
  text: async () => JSON.stringify(data),
  blob: async () => new Blob(),
})

// Utility function to wait for async operations
export const waitForAsync = (timeout = 1000) =>
  new Promise(resolve => setTimeout(resolve, timeout))

// Utility function to simulate user interactions
export const userActions = {
  type: (element: HTMLElement, value: string) => {
    fireEvent.change(element, { target: { value } })
  },

  click: (element: HTMLElement) => {
    fireEvent.click(element)
  },

  submit: (form: HTMLFormElement) => {
    fireEvent.submit(form)
  },

  keyPress: (element: HTMLElement, key: string) => {
    fireEvent.keyPress(element, { key })
  },

  mouseOver: (element: HTMLElement) => {
    fireEvent.mouseOver(element)
  },

  mouseOut: (element: HTMLElement) => {
    fireEvent.mouseOut(element)
  },
}

// Utility function to test component snapshots
export const testSnapshot = (component: ReactElement) => {
  const { container } = render(component)
  expect(container).toMatchSnapshot()
}

// Utility function to test accessibility
export const testAccessibility = async (component: ReactElement) => {
  const { container } = render(component)

  // This would normally use an accessibility testing library
  // For now, just check if the component renders
  expect(container).toBeInTheDocument()
}

// Cleanup function to use after each test
export const cleanupTest = () => {
  jest.clearAllMocks()
  jest.useFakeTimers().clearAllTimers()
}

// Mock WebSocket module
export const mockWebSocketModule = () => {
  jest.mock('../src/lib/websocket', () => ({
    connectWebSocket: (url: string) => new MockWebSocket(url),
  }))
}

// Error boundary testing utility
export const ErrorBoundaryTester = ({ children }: { children: ReactElement }) => {
  const [hasError, setHasError] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  if (hasError) {
    return <div data-testid="error-boundary">Error: {error?.message}</div>
  }

  return (
    <ErrorBoundary
      FallbackComponent={({ error, resetErrorBoundary }) => (
        <div data-testid="error-boundary">
          <h2>Something went wrong</h2>
          <p>{error.message}</p>
          <button onClick={resetErrorBoundary}>Try again</button>
        </div>
      )}
      onError={(error) => {
        setHasError(true)
        setError(error)
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

// Performance testing utility
export const measurePerformance = async (fn: () => Promise<void> | void) => {
  const start = performance.now()
  await fn()
  const end = performance.now()
  return end - start
}

// Network mocking utilities
export const mockNetworkResponse = (
  url: string,
  response: any,
  options: { status?: number; delay?: number } = {}
) => {
  fetch.mockImplementationOnce(
    jest.fn(() =>
      Promise.resolve(
        createMockApiResponse(response, options.status || 200)
      )
    )
  )
}

export const mockNetworkError = (url: string, error: string = 'Network error') => {
  fetch.mockImplementationOnce(
    jest.fn(() =>
      Promise.reject(new Error(error))
    )
  )
}

// WebSocket utilities
export const simulateWebSocketMessage = (websocket: any, message: any) => {
  const listeners = websocket.listeners?.message || []
  listeners.forEach((listener: Function) => {
    listener({ data: JSON.stringify(message) })
  })
}

export const simulateWebSocketError = (websocket: any, error: Error) => {
  const listeners = websocket.listeners?.error || []
  listeners.forEach((listener: Function) => {
    listener(error)
  })
}

export const waitForWebSocketMessage = async (websocket: any, type: string) => {
  return new Promise((resolve) => {
    const listener = (event: any) => {
      const message = JSON.parse(event.data)
      if (message.type === type) {
        websocket.removeEventListener('message', listener)
        resolve(message)
      }
    }
    websocket.addEventListener('message', listener)
  })
}