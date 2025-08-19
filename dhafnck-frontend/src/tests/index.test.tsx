import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';
import reportWebVitals from '../reportWebVitals';

// Mock dependencies
jest.mock('react-dom/client');
jest.mock('../App', () => ({
  __esModule: true,
  default: () => <div>Mocked App</div>,
}));
jest.mock('../reportWebVitals');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div data-testid="browser-router">{children}</div>,
}));

// Mock CSS imports
jest.mock('tailwindcss/tailwind.css', () => ({}));
jest.mock('../index.css', () => ({}));
jest.mock('../styles/theme.css', () => ({}));
jest.mock('../theme/global.scss', () => ({}));

describe('index.tsx', () => {
  let mockRoot: any;
  let mockRender: jest.Mock;
  let container: HTMLElement;

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Create a mock container
    container = document.createElement('div');
    container.id = 'root';
    document.body.appendChild(container);

    // Mock ReactDOM.createRoot
    mockRender = jest.fn();
    mockRoot = {
      render: mockRender,
    };
    (ReactDOM.createRoot as jest.Mock).mockReturnValue(mockRoot);
  });

  afterEach(() => {
    // Clean up DOM
    document.body.removeChild(container);
  });

  it('creates root with correct element', () => {
    // Import index to trigger execution
    require('../index');

    expect(ReactDOM.createRoot).toHaveBeenCalledWith(container);
  });

  it('renders App component wrapped in providers', () => {
    require('../index');

    expect(mockRender).toHaveBeenCalledTimes(1);
    
    // Get the rendered component
    const renderedComponent = mockRender.mock.calls[0][0];
    
    // Check structure
    expect(renderedComponent.type).toBe(React.StrictMode);
    expect(renderedComponent.props.children.type.name).toBe('BrowserRouter');
    expect(renderedComponent.props.children.props.children.type.name).toBe('default');
  });

  it('calls reportWebVitals', () => {
    require('../index');

    expect(reportWebVitals).toHaveBeenCalledTimes(1);
    expect(reportWebVitals).toHaveBeenCalledWith();
  });

  it('handles missing root element gracefully', () => {
    // Remove root element
    document.body.removeChild(container);

    // Mock getElementById to return null
    const originalGetElementById = document.getElementById;
    document.getElementById = jest.fn().mockReturnValue(null);

    // Should throw when trying to create root with null
    expect(() => {
      require('../index');
    }).toThrow();

    // Restore original function
    document.getElementById = originalGetElementById;
  });

  it('imports all required CSS files', () => {
    // This test verifies that CSS imports don't throw errors
    expect(() => {
      require('../index');
    }).not.toThrow();
  });

  it('wraps App in React.StrictMode', () => {
    require('../index');

    const renderedComponent = mockRender.mock.calls[0][0];
    expect(renderedComponent.type).toBe(React.StrictMode);
  });

  it('wraps App in BrowserRouter', () => {
    require('../index');

    const renderedComponent = mockRender.mock.calls[0][0];
    const browserRouter = renderedComponent.props.children;
    
    expect(browserRouter.type).toBeDefined();
    expect(browserRouter.props.children.type.name).toBe('default'); // App component
  });

  it('renders only once', () => {
    require('../index');

    expect(ReactDOM.createRoot).toHaveBeenCalledTimes(1);
    expect(mockRender).toHaveBeenCalledTimes(1);
  });

  it('maintains correct component hierarchy', () => {
    require('../index');

    const renderedComponent = mockRender.mock.calls[0][0];
    
    // Verify the complete hierarchy
    // StrictMode > BrowserRouter > App
    const strictMode = renderedComponent;
    const browserRouter = strictMode.props.children;
    const app = browserRouter.props.children;

    expect(strictMode.type).toBe(React.StrictMode);
    expect(browserRouter.type.name).toBe('BrowserRouter');
    expect(app.type.name).toBe('default'); // Default export from App
  });
});