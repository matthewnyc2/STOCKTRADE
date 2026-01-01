import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'

// Polyfill for TextEncoder/TextDecoder
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock lightweight-charts
const mockSeries = {
  setData: jest.fn(),
  update: jest.fn(),
  priceScale: jest.fn(() => ({
    applyOptions: jest.fn(),
  })),
}

jest.mock('lightweight-charts', () => ({
  createChart: jest.fn(() => ({
    addCandlestickSeries: jest.fn(() => mockSeries),
    addAreaSeries: jest.fn(() => mockSeries),
    addHistogramSeries: jest.fn(() => mockSeries),
    addLineSeries: jest.fn(() => mockSeries),
    remove: jest.fn(),
    applyOptions: jest.fn(),
    resize: jest.fn(),
    timeScale: jest.fn(() => ({
      fitContent: jest.fn(),
      scrollToPosition: jest.fn(),
      setVisibleRange: jest.fn(),
      getVisibleRange: jest.fn(),
    })),
  })),
}))

// Mock framer-motion globally
jest.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: {
      div: ({ children, ...props }) => React.createElement('div', props, children),
      button: ({ children, ...props }) => React.createElement('button', props, children),
      span: ({ children, ...props }) => React.createElement('span', props, children),
    },
    AnimatePresence: ({ children }) => React.createElement(React.Fragment, null, children),
  }
})

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pop: jest.fn(),
    reload: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn().mockResolvedValue(undefined),
    query: {},
    pathname: '/',
    asPath: '/',
    isFallback: false,
  }),
}))

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn((key, queryFn, options) => {
    return {
      data: undefined,
      error: null,
      isError: false,
      isFetching: false,
      isLoading: false,
      isSuccess: false,
      refetch: jest.fn(),
      status: 'idle',
    }
  }),
  useMutation: jest.fn(() => ({
    mutate: jest.fn(),
    mutateAsync: jest.fn(),
    isLoading: false,
    isError: false,
    error: null,
    isSuccess: false,
  })),
  useQueryClient: () => ({
    invalidateQueries: jest.fn(),
    removeQueries: jest.fn(),
    resetQueries: jest.fn(),
    setQueryData: jest.fn(),
    getQueryData: jest.fn(),
  }),
}))

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}

global.localStorage = localStorageMock

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

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

// Suppress console errors during tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    // Filter out certain error messages
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('useImperativeHandle') ||
        args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Warning: render'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

// Reset all mocks after each test
afterEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers().clearAllTimers()
})