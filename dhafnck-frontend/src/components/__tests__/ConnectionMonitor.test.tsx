import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ConnectionMonitor } from '../ConnectionMonitor';

// Mock data
const mockConnectionStatus = {
  status: 'healthy' as const,
  response_time: 45,
  last_check: '2024-01-15T10:00:00Z',
  uptime: 86400, // 24 hours in seconds
  connection_pool: {
    active: 5,
    idle: 3,
    total: 10,
    peak_usage: 8
  },
  error_rate: 0.5,
  throughput: 150
};

const mockConnectionHistory = [
  {
    timestamp: '2024-01-15T10:00:00Z',
    event_type: 'connected' as const,
    duration: 100,
    response_time: 45
  },
  {
    timestamp: '2024-01-15T09:55:00Z',
    event_type: 'disconnected' as const,
    error_message: 'Connection timeout',
    response_time: 0
  }
];

const mockServerCapabilities = {
  version: '2.1.0',
  features: ['real_time_updates', 'advanced_diagnostics', 'compliance_monitoring'],
  tools: ['manage_task', 'manage_compliance', 'manage_connection'],
  authentication: {
    enabled: true,
    methods: ['bearer_token', 'api_key']
  },
  rate_limiting: {
    enabled: true,
    requests_per_minute: 100
  },
  health_check: {
    interval: 30,
    timeout: 10
  }
};

const mockProps = {
  connectionStatus: mockConnectionStatus,
  connectionHistory: mockConnectionHistory,
  serverCapabilities: mockServerCapabilities,
  onTestConnection: jest.fn(),
  onRestartConnection: jest.fn(),
  onUpdateConnectionSettings: jest.fn(),
  onRegisterForUpdates: jest.fn()
};

describe('ConnectionMonitor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders connection monitor with status', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    expect(screen.getByText('Connection Monitor')).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('45ms')).toBeInTheDocument();
  });

  test('displays connection pool information', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    expect(screen.getByText('5')).toBeInTheDocument(); // Active
    expect(screen.getByText('3')).toBeInTheDocument(); // Idle
    expect(screen.getByText('10')).toBeInTheDocument(); // Total
  });

  test('shows performance metrics', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    expect(screen.getByText('150 req/min')).toBeInTheDocument(); // Throughput
    expect(screen.getByText('0.5%')).toBeInTheDocument(); // Error rate
  });

  test('can switch between tabs', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // Click on history tab
    fireEvent.click(screen.getByText('History'));
    expect(screen.getByText('Connection History')).toBeInTheDocument();
    
    // Click on capabilities tab
    fireEvent.click(screen.getByText('Capabilities'));
    expect(screen.getByText('Server Information')).toBeInTheDocument();
  });

  test('displays connection history', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // Switch to history tab
    fireEvent.click(screen.getByText('History'));
    
    expect(screen.getByText('CONNECTED')).toBeInTheDocument();
    expect(screen.getByText('DISCONNECTED')).toBeInTheDocument();
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  test('shows server capabilities', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // Switch to capabilities tab
    fireEvent.click(screen.getByText('Capabilities'));
    
    expect(screen.getByText('2.1.0')).toBeInTheDocument();
    expect(screen.getByText('MCP 2025-06-18')).toBeInTheDocument();
    expect(screen.getByText('manage_task')).toBeInTheDocument();
    expect(screen.getByText('real_time_updates')).toBeInTheDocument();
  });

  test('displays authentication status', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // Switch to capabilities tab
    fireEvent.click(screen.getByText('Capabilities'));
    
    expect(screen.getByText('Status: Enabled')).toBeInTheDocument();
    expect(screen.getByText('Methods: bearer_token, api_key')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  test('shows rate limiting information', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // Switch to capabilities tab
    fireEvent.click(screen.getByText('Capabilities'));
    
    expect(screen.getByText('Status: Enabled')).toBeInTheDocument();
    expect(screen.getByText('Limit: 100 requests/minute')).toBeInTheDocument();
  });

  test('can test connection', async () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);
    
    await waitFor(() => {
      expect(mockProps.onTestConnection).toHaveBeenCalled();
    });
  });

  test('can restart connection', async () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    const restartButton = screen.getByText('Restart Connection');
    fireEvent.click(restartButton);
    
    await waitFor(() => {
      expect(mockProps.onRestartConnection).toHaveBeenCalled();
    });
  });

  test('can run diagnostics', async () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    const diagnosticsButton = screen.getByText('Run Diagnostics');
    fireEvent.click(diagnosticsButton);
    
    // Should trigger diagnostic functionality
    expect(diagnosticsButton).toBeInTheDocument();
  });

  test('shows WebSocket connection status', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    expect(screen.getByText('Connect')).toBeInTheDocument();
  });

  test('can register for updates', async () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    const connectButton = screen.getByText('Connect');
    fireEvent.click(connectButton);
    
    await waitFor(() => {
      expect(mockProps.onRegisterForUpdates).toHaveBeenCalledWith(expect.stringMatching(/^session_/));
    });
  });

  test('displays uptime correctly', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // 86400 seconds = 24 hours
    expect(screen.getByText('24h')).toBeInTheDocument();
  });

  test('shows connection pool utilization', () => {
    render(<ConnectionMonitor {...mockProps} />);
    
    // 5/10 = 50% utilization
    expect(screen.getByText('Pool utilization: 50%')).toBeInTheDocument();
  });

  test('handles degraded connection status', () => {
    const degradedProps = {
      ...mockProps,
      connectionStatus: {
        ...mockConnectionStatus,
        status: 'degraded' as const,
        error_rate: 5.0
      }
    };
    
    render(<ConnectionMonitor {...degradedProps} />);
    
    expect(screen.getByText('DEGRADED')).toBeInTheDocument();
  });

  test('handles down connection status', () => {
    const downProps = {
      ...mockProps,
      connectionStatus: {
        ...mockConnectionStatus,
        status: 'down' as const,
        response_time: 0,
        error_rate: 100
      }
    };
    
    render(<ConnectionMonitor {...downProps} />);
    
    expect(screen.getByText('DOWN')).toBeInTheDocument();
    expect(screen.getByText('Connection is down. Check server status and network connectivity.')).toBeInTheDocument();
  });
});