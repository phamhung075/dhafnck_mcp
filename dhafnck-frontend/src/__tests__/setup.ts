/**
 * Test Setup Configuration
 * Global configuration for Jest testing environment
 */

import '@testing-library/jest-dom';

// Mock WebSocket for testing
class MockWebSocket {
  public readyState = WebSocket.OPEN;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string) {
    // Mock send functionality
  }

  close() {
    setTimeout(() => {
      if (this.onclose) {
        this.onclose(new CloseEvent('close'));
      }
    }, 0);
  }
}

// Replace WebSocket in global scope
(global as any).WebSocket = MockWebSocket;

// Mock fetch for API calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
  })
) as jest.Mock;

// Mock performance API
Object.defineProperty(global, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000,
    },
  },
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Console error suppression for known React warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An invalid form control')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Test utilities
export const mockAgent = {
  id: '@test_agent',
  name: '@test_agent',
  status: 'active' as const,
  project_id: 'test-project',
};

export const mockProject = {
  id: 'test-project',
  name: 'Test Project',
  description: 'A test project for unit testing',
  status: 'active' as const,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockUser = {
  id: 'test-user',
  name: 'Test User',
  email: 'test@example.com',
  role: 'admin' as const,
  preferences: {
    theme: 'auto' as const,
    notifications: true,
    autoRefresh: true,
    refreshInterval: 30000,
    sidebarCollapsed: false,
    defaultView: 'dashboard' as const
  }
};

export const mockSystemHealth = {
  status: 'healthy' as const,
  overall_score: 95,
  uptime: 3600,
  version: '1.0.0',
  environment: 'test',
  last_check: new Date().toISOString(),
  components: {
    database: { status: 'healthy', score: 95 },
    redis: { status: 'healthy', score: 98 },
    websocket: { status: 'healthy', score: 92 },
  },
  dependencies: {
    database: 'healthy',
    redis: 'healthy',
    websocket: 'healthy',
  },
  metrics: {
    cpu_usage: 25.5,
    memory_usage: 60.2,
    active_connections: 10,
  },
};

export const mockNotification = {
  id: 'test-notification',
  title: 'Test Notification',
  message: 'This is a test notification',
  type: 'info' as const,
  level: 'info' as const,
  timestamp: new Date().toISOString(),
  read: false,
};

// Custom render function with providers
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

export const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      system: (state = {
        health: null,
        compliance: null,
        connection: { status: 'unknown', latency: 0, uptime_percentage: 0, active_connections: 0, last_check: '', error_rate: 0 },
        notifications: [],
        loading: {},
        errors: {}
      }, action) => state,
      session: (state = {
        currentUser: null,
        currentAgent: null,
        selectedProject: null,
        selectedBranch: null,
        selectedContext: null,
        preferences: {
          theme: 'auto',
          notifications: true,
          autoRefresh: true,
          refreshInterval: 30000,
          sidebarCollapsed: false,
          defaultView: 'dashboard'
        },
        recentActivity: []
      }, action) => state,
      data: (state = {
        projects: [],
        branches: {},
        tasks: {},
        agents: {},
        contexts: [],
        rules: []
      }, action) => state,
      ui: (state = {
        currentView: 'dashboard',
        sidebarOpen: true,
        theme: 'auto',
        modalStack: [],
        commandPaletteOpen: false,
        notifications: []
      }, action) => state
    },
    preloadedState: initialState,
  });
};

export const renderWithProviders = (ui: React.ReactElement, options: { initialState?: any; store?: any } = {}) => {
  const { initialState, store = createMockStore(initialState), ...renderOptions } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <Provider store={store}>{children}</Provider>;
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
};

// Re-export everything
export * from '@testing-library/react';
export { renderWithProviders as render };