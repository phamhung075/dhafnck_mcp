/**
 * Unit Tests for SystemIntegration Component
 * Tests unified state management, WebSocket connections, and performance monitoring
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render, mockAgent, mockProject, mockSystemHealth } from '../setup';
import { SystemIntegration, useSystemIntegration } from '../../integration/SystemIntegration';
import * as api from '../../api/enhanced';

// Mock the API
jest.mock('../../api/enhanced');
const mockApi = api as jest.Mocked<typeof api>;

// Test component that uses SystemIntegration context
function TestComponent() {
  const {
    state,
    actions,
    performance
  } = useSystemIntegration();

  return (
    <div>
      <div data-testid="system-state">
        {JSON.stringify({
          agentCount: state.agents.available.length,
          projectCount: state.projects.list.length,
          currentAgent: state.agents.current?.name,
          systemHealth: state.monitoring.systemHealth?.status
        })}
      </div>
      <button
        data-testid="switch-agent"
        onClick={() => actions.switchAgent(mockAgent)}
      >
        Switch Agent
      </button>
      <button
        data-testid="switch-project"
        onClick={() => actions.switchProject(mockProject)}
      >
        Switch Project
      </button>
      <button
        data-testid="refresh-health"
        onClick={() => actions.refreshSystemHealth()}
      >
        Refresh Health
      </button>
      <button
        data-testid="measure-performance"
        onClick={() => performance.measureRenderTime('TestComponent')}
      >
        Measure Performance
      </button>
    </div>
  );
}

describe('SystemIntegration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default API mocks
    mockApi.mcpApi = {
      manageConnection: jest.fn().mockResolvedValue({
        success: true,
        data: mockSystemHealth
      }),
      manageProject: jest.fn().mockResolvedValue({
        success: true,
        data: [mockProject]
      }),
      manageRule: jest.fn().mockResolvedValue({
        success: true,
        data: []
      }),
      callAgent: jest.fn().mockResolvedValue({
        success: true,
        data: mockAgent
      }),
      manageGitBranch: jest.fn().mockResolvedValue({
        success: true,
        data: []
      }),
      manageAgent: jest.fn().mockResolvedValue({
        success: true,
        data: []
      }),
      manageHierarchicalContext: jest.fn().mockResolvedValue({
        success: true,
        data: {}
      })
    } as any;
  });

  describe('Initialization', () => {
    test('shows loading state during initialization', async () => {
      // Make API calls slow to test loading state
      mockApi.mcpApi.manageConnection = jest.fn(() => 
        new Promise(resolve => setTimeout(() => resolve({
          success: true,
          data: mockSystemHealth
        }), 100))
      );

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      // Should show loading initially
      expect(screen.getByText(/Initializing System Integration/)).toBeInTheDocument();
      expect(screen.getByText(/Setting up unified state management/)).toBeInTheDocument();

      // Wait for initialization to complete
      await waitFor(() => {
        expect(screen.getByTestId('system-state')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    test('initializes with system health check', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(mockApi.mcpApi.manageConnection).toHaveBeenCalledWith(
          'health_check',
          { include_details: true }
        );
      });
    });

    test('loads initial projects and rules', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(mockApi.mcpApi.manageProject).toHaveBeenCalledWith('list');
        expect(mockApi.mcpApi.manageRule).toHaveBeenCalledWith('list');
      });
    });

    test('handles initialization errors gracefully', async () => {
      mockApi.mcpApi.manageConnection = jest.fn().mockRejectedValue(
        new Error('Connection failed')
      );

      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'System initialization failed:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('State Management', () => {
    test('provides initial state correctly', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        const stateElement = screen.getByTestId('system-state');
        const state = JSON.parse(stateElement.textContent || '{}');
        
        expect(state).toEqual({
          agentCount: 0,
          projectCount: 1,
          currentAgent: null,
          systemHealth: 'healthy'
        });
      });
    });

    test('updates state when data is loaded', async () => {
      const projectsData = [mockProject, { ...mockProject, id: 'project-2', name: 'Project 2' }];
      mockApi.mcpApi.manageProject = jest.fn().mockResolvedValue({
        success: true,
        data: projectsData
      });

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        const stateElement = screen.getByTestId('system-state');
        const state = JSON.parse(stateElement.textContent || '{}');
        expect(state.projectCount).toBe(2);
      });
    });
  });

  describe('Agent Management', () => {
    test('switches agent successfully', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('switch-agent')).toBeInTheDocument();
      });

      const switchButton = screen.getByTestId('switch-agent');
      switchButton.click();

      await waitFor(() => {
        expect(mockApi.mcpApi.callAgent).toHaveBeenCalledWith(mockAgent.name);
      });
    });

    test('handles agent switch errors', async () => {
      mockApi.mcpApi.callAgent = jest.fn().mockRejectedValue(
        new Error('Agent switch failed')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('switch-agent')).toBeInTheDocument();
      });

      const switchButton = screen.getByTestId('switch-agent');
      switchButton.click();

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to switch agent:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Project Management', () => {
    test('switches project and loads related data', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('switch-project')).toBeInTheDocument();
      });

      const switchButton = screen.getByTestId('switch-project');
      switchButton.click();

      await waitFor(() => {
        expect(mockApi.mcpApi.manageGitBranch).toHaveBeenCalledWith(
          'list',
          { project_id: mockProject.id }
        );
        expect(mockApi.mcpApi.manageAgent).toHaveBeenCalledWith(
          'list',
          { project_id: mockProject.id }
        );
      });
    });

    test('handles project switch errors', async () => {
      mockApi.mcpApi.manageGitBranch = jest.fn().mockRejectedValue(
        new Error('Failed to load branches')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('switch-project')).toBeInTheDocument();
      });

      const switchButton = screen.getByTestId('switch-project');
      switchButton.click();

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to switch project:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Health Monitoring', () => {
    test('refreshes system health', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('refresh-health')).toBeInTheDocument();
      });

      const refreshButton = screen.getByTestId('refresh-health');
      refreshButton.click();

      await waitFor(() => {
        expect(mockApi.mcpApi.manageConnection).toHaveBeenCalledWith(
          'health_check',
          { include_details: true }
        );
      });
    });

    test('handles health check errors', async () => {
      // Clear initial calls
      jest.clearAllMocks();
      
      mockApi.mcpApi.manageConnection = jest.fn()
        .mockResolvedValueOnce({ success: true, data: mockSystemHealth }) // For initialization
        .mockRejectedValueOnce(new Error('Health check failed')); // For manual refresh

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('refresh-health')).toBeInTheDocument();
      });

      const refreshButton = screen.getByTestId('refresh-health');
      refreshButton.click();

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to refresh system health:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Performance Monitoring', () => {
    test('measures render performance', async () => {
      const performanceSpy = jest.spyOn(performance, 'now')
        .mockReturnValueOnce(100)
        .mockReturnValueOnce(150);

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('measure-performance')).toBeInTheDocument();
      });

      const measureButton = screen.getByTestId('measure-performance');
      measureButton.click();

      expect(performanceSpy).toHaveBeenCalled();
      performanceSpy.mockRestore();
    });

    test('analyzes memory usage', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        const { performance } = useSystemIntegration();
        const memoryUsage = performance.analyzeMemoryUsage();
        
        expect(memoryUsage).toEqual({
          used: 1000000,
          total: 2000000,
          limit: 4000000,
          timestamp: expect.any(Number)
        });
      });
    });
  });

  describe('WebSocket Integration', () => {
    test('establishes WebSocket connection on mount', async () => {
      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      // Wait for WebSocket to be created
      await waitFor(() => {
        expect(global.WebSocket).toHaveBeenCalled();
      });
    });

    test('handles WebSocket connection events', async () => {
      let wsInstance: any;
      const mockWebSocket = jest.fn().mockImplementation((url) => {
        wsInstance = {
          url,
          readyState: WebSocket.OPEN,
          onopen: null,
          onclose: null,
          onmessage: null,
          onerror: null,
          send: jest.fn(),
          close: jest.fn()
        };
        
        // Simulate successful connection
        setTimeout(() => {
          if (wsInstance.onopen) {
            wsInstance.onopen(new Event('open'));
          }
        }, 0);
        
        return wsInstance;
      });

      (global as any).WebSocket = mockWebSocket;

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(mockWebSocket).toHaveBeenCalled();
      });

      // Test message handling
      if (wsInstance && wsInstance.onmessage) {
        const testMessage = {
          data: JSON.stringify({
            type: 'system_health_update',
            payload: { status: 'degraded' }
          })
        };
        wsInstance.onmessage(testMessage);
      }
    });
  });

  describe('Error Boundaries', () => {
    test('catches and handles component errors', async () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <ThrowError />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Hook Usage', () => {
    test('throws error when used outside of SystemIntegration provider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const TestComponentOutsideProvider = () => {
        try {
          useSystemIntegration();
          return <div>Should not render</div>;
        } catch (error) {
          return <div data-testid="hook-error">{(error as Error).message}</div>;
        }
      };

      render(<TestComponentOutsideProvider />);

      expect(screen.getByTestId('hook-error')).toHaveTextContent(
        'useSystemIntegration must be used within SystemIntegration'
      );

      consoleSpy.mockRestore();
    });
  });
});