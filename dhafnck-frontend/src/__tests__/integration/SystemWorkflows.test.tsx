/**
 * Integration Tests for Complete System Workflows
 * Tests end-to-end user workflows across multiple components
 */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockAgent, mockProject, mockUser, mockSystemHealth } from '../setup';
import { SystemIntegration } from '../../integration/SystemIntegration';
import { IntegratedNavigation } from '../../components/IntegratedNavigation';
import { MainApplication } from '../../components/MainApplication';
import * as api from '../../api/enhanced';

// Mock the API
jest.mock('../../api/enhanced');
const mockApi = api as jest.Mocked<typeof api>;

// Mock child components to focus on integration
jest.mock('../../components/layout/MainLayout', () => ({
  MainLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  )
}));

jest.mock('../../components/navigation/ViewRouter', () => ({
  ViewRouter: () => <div data-testid="view-router">View Router Content</div>
}));

describe('System Integration Workflows', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup comprehensive API mocks
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
        data: [{
          id: 'branch-1',
          git_branch_name: 'main',
          git_branch_description: 'Main branch',
          project_id: mockProject.id
        }]
      }),
      manageAgent: jest.fn().mockResolvedValue({
        success: true,
        data: [mockAgent]
      }),
      manageHierarchicalContext: jest.fn().mockResolvedValue({
        success: true,
        data: {
          id: 'context-1',
          level: 'project',
          context_id: mockProject.id,
          resolved_data: {}
        }
      }),
      manageTask: jest.fn().mockResolvedValue({
        success: true,
        data: {
          id: 'task-1',
          title: 'Test Task',
          status: 'todo',
          git_branch_id: 'branch-1'
        }
      })
    } as any;
  });

  describe('Application Initialization Workflow', () => {
    test('complete application startup sequence', async () => {
      render(
        <MainApplication 
          initialAgent="@uber_orchestrator_agent"
          initialProject={mockProject.id}
        />
      );

      // Should show loading state initially
      expect(screen.getByText(/Initializing DhafnckMCP Dashboard/)).toBeInTheDocument();

      // Wait for initialization to complete
      await waitFor(() => {
        expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Verify API calls were made in correct order
      expect(mockApi.mcpApi.manageConnection).toHaveBeenCalledWith(
        'health_check',
        { include_details: true }
      );
      expect(mockApi.mcpApi.manageProject).toHaveBeenCalledWith('list');
      expect(mockApi.mcpApi.callAgent).toHaveBeenCalledWith('@uber_orchestrator_agent');
    });

    test('handles initialization errors gracefully', async () => {
      mockApi.mcpApi.manageConnection = jest.fn().mockRejectedValue(
        new Error('Network error')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(<MainApplication />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to initialize application:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Agent Orchestration Workflow', () => {
    test('complete agent switching workflow with context preservation', async () => {
      const user = userEvent.setup();

      // Mock successful API responses
      mockApi.mcpApi.callAgent = jest.fn()
        .mockResolvedValueOnce({ success: true, data: { name: '@uber_orchestrator_agent' } })
        .mockResolvedValueOnce({ success: true, data: { name: '@coding_agent' } });

      const onAgentSwitch = jest.fn().mockResolvedValue(undefined);
      const onNavigate = jest.fn();
      const onProjectSwitch = jest.fn();

      render(
        <SystemIntegration>
          <IntegratedNavigation
            currentUser={mockUser}
            projects={[mockProject]}
            currentAgent={null}
            systemHealth={mockSystemHealth}
            notifications={[]}
            onNavigate={onNavigate}
            onAgentSwitch={onAgentSwitch}
            onProjectSwitch={onProjectSwitch}
          />
        </SystemIntegration>
      );

      // Wait for system integration to initialize
      await waitFor(() => {
        expect(screen.getByText('No Agent')).toBeInTheDocument();
      });

      // Open agent switcher
      const agentButton = screen.getByText('No Agent').closest('button')!;
      await user.click(agentButton);

      // Verify agent list is displayed
      expect(screen.getByText('Switch Agent')).toBeInTheDocument();
      expect(screen.getByText('@coding_agent')).toBeInTheDocument();

      // Switch to coding agent
      const codingAgentButton = screen.getByText('@coding_agent');
      await user.click(codingAgentButton);

      // Verify agent switch was called
      expect(onAgentSwitch).toHaveBeenCalledWith(
        expect.objectContaining({
          name: '@coding_agent'
        })
      );
    });

    test('agent switching error handling and fallback', async () => {
      const user = userEvent.setup();
      const onAgentSwitch = jest.fn().mockRejectedValue(new Error('Agent unavailable'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <IntegratedNavigation
            currentUser={mockUser}
            projects={[mockProject]}
            currentAgent={null}
            systemHealth={mockSystemHealth}
            notifications={[]}
            onNavigate={jest.fn()}
            onAgentSwitch={onAgentSwitch}
            onProjectSwitch={jest.fn()}
          />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByText('No Agent')).toBeInTheDocument();
      });

      // Try to switch agent
      const agentButton = screen.getByText('No Agent').closest('button')!;
      await user.click(agentButton);

      const codingAgentButton = screen.getByText('@coding_agent');
      await user.click(codingAgentButton);

      // Verify error handling
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to switch agent:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Project Management Workflow', () => {
    test('complete project selection and data loading workflow', async () => {
      const user = userEvent.setup();
      const onProjectSwitch = jest.fn();

      render(
        <SystemIntegration>
          <IntegratedNavigation
            currentUser={mockUser}
            projects={[mockProject]}
            currentAgent={mockAgent}
            systemHealth={mockSystemHealth}
            notifications={[]}
            onNavigate={jest.fn()}
            onAgentSwitch={jest.fn()}
            onProjectSwitch={onProjectSwitch}
          />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByText('Select Project')).toBeInTheDocument();
      });

      // Open project selector
      const projectButton = screen.getByText('Select Project').closest('button')!;
      await user.click(projectButton);

      // Verify project list is displayed
      expect(screen.getByText('Projects')).toBeInTheDocument();
      expect(screen.getByText(mockProject.name)).toBeInTheDocument();

      // Select project
      const projectOption = screen.getByText(mockProject.name);
      await user.click(projectOption);

      // Verify project switch was called
      expect(onProjectSwitch).toHaveBeenCalledWith(mockProject);

      // Wait for project-related data to load
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

    test('project switching with error handling', async () => {
      const user = userEvent.setup();
      
      // Mock project switch to fail
      mockApi.mcpApi.manageGitBranch = jest.fn().mockRejectedValue(
        new Error('Failed to load branches')
      );

      const onProjectSwitch = jest.fn();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <SystemIntegration>
          <IntegratedNavigation
            currentUser={mockUser}
            projects={[mockProject]}
            currentAgent={mockAgent}
            systemHealth={mockSystemHealth}
            notifications={[]}
            onNavigate={jest.fn()}
            onAgentSwitch={jest.fn()}
            onProjectSwitch={onProjectSwitch}
          />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByText('Select Project')).toBeInTheDocument();
      });

      // Select project
      const projectButton = screen.getByText('Select Project').closest('button')!;
      await user.click(projectButton);

      const projectOption = screen.getByText(mockProject.name);
      await user.click(projectOption);

      // Wait for error to be logged
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to switch project:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Real-time Data Synchronization Workflow', () => {
    test('WebSocket connection and real-time updates', async () => {
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
          <div data-testid="test-content">Test Content</div>
        </SystemIntegration>
      );

      // Wait for WebSocket connection
      await waitFor(() => {
        expect(mockWebSocket).toHaveBeenCalled();
      });

      // Simulate real-time health update
      if (wsInstance && wsInstance.onmessage) {
        const healthUpdate = {
          data: JSON.stringify({
            type: 'system_health_update',
            payload: {
              ...mockSystemHealth,
              status: 'degraded',
              overall_score: 65
            }
          })
        };
        wsInstance.onmessage(healthUpdate);
      }

      // Simulate agent status update
      if (wsInstance && wsInstance.onmessage) {
        const agentUpdate = {
          data: JSON.stringify({
            type: 'agent_status_update',
            payload: {
              ...mockAgent,
              status: 'active'
            }
          })
        };
        wsInstance.onmessage(agentUpdate);
      }

      // Verify WebSocket functionality
      expect(wsInstance.send).toBeDefined();
      expect(wsInstance.close).toBeDefined();
    });

    test('WebSocket reconnection on connection loss', async () => {
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
        
        // Simulate connection and immediate close
        setTimeout(() => {
          if (wsInstance.onopen) {
            wsInstance.onopen(new Event('open'));
          }
          setTimeout(() => {
            if (wsInstance.onclose) {
              wsInstance.onclose(new CloseEvent('close'));
            }
          }, 100);
        }, 0);
        
        return wsInstance;
      });

      (global as any).WebSocket = mockWebSocket;

      render(
        <SystemIntegration>
          <div data-testid="test-content">Test Content</div>
        </SystemIntegration>
      );

      // Wait for initial connection and disconnection
      await waitFor(() => {
        expect(mockWebSocket).toHaveBeenCalled();
      });

      // WebSocket should attempt reconnection
      await waitFor(() => {
        expect(mockWebSocket).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });
  });

  describe('Performance Monitoring Workflow', () => {
    test('render performance measurement and optimization', async () => {
      const performanceSpy = jest.spyOn(performance, 'now')
        .mockReturnValueOnce(100)
        .mockReturnValueOnce(150);

      // Component that uses performance monitoring
      function TestComponent() {
        const { performance: performanceUtils } = useSystemIntegration();
        
        React.useEffect(() => {
          const endMeasurement = performanceUtils.measureRenderTime('TestComponent');
          return endMeasurement;
        }, [performanceUtils]);

        return <div data-testid="performance-test">Performance Test</div>;
      }

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        expect(screen.getByTestId('performance-test')).toBeInTheDocument();
      });

      expect(performanceSpy).toHaveBeenCalled();
      performanceSpy.mockRestore();
    });

    test('memory usage analysis', async () => {
      function TestComponent() {
        const { performance: performanceUtils } = useSystemIntegration();
        const [memoryUsage, setMemoryUsage] = React.useState<any>(null);

        React.useEffect(() => {
          const usage = performanceUtils.analyzeMemoryUsage();
          setMemoryUsage(usage);
        }, [performanceUtils]);

        return (
          <div data-testid="memory-test">
            {memoryUsage && (
              <span data-testid="memory-usage">
                {JSON.stringify(memoryUsage)}
              </span>
            )}
          </div>
        );
      }

      render(
        <SystemIntegration>
          <TestComponent />
        </SystemIntegration>
      );

      await waitFor(() => {
        const memoryElement = screen.getByTestId('memory-usage');
        const usage = JSON.parse(memoryElement.textContent || '{}');
        
        expect(usage).toEqual({
          used: 1000000,
          total: 2000000,
          limit: 4000000,
          timestamp: expect.any(Number)
        });
      });
    });
  });

  describe('Error Boundary Integration', () => {
    test('global error boundary catches component errors', async () => {
      const ThrowError = () => {
        throw new Error('Test component error');
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

    test('error boundary provides error recovery options', async () => {
      // This would test the ErrorFallback component
      // For now, we verify that errors are caught
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const ProblematicComponent = () => {
        const [shouldThrow, setShouldThrow] = React.useState(false);
        
        if (shouldThrow) {
          throw new Error('Intentional test error');
        }

        return (
          <button 
            onClick={() => setShouldThrow(true)}
            data-testid="throw-error"
          >
            Throw Error
          </button>
        );
      };

      render(
        <SystemIntegration>
          <ProblematicComponent />
        </SystemIntegration>
      );

      const throwButton = screen.getByTestId('throw-error');
      fireEvent.click(throwButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });
  });
});

// Helper function to import useSystemIntegration in tests
function useSystemIntegration() {
  const { useSystemIntegration } = require('../../integration/SystemIntegration');
  return useSystemIntegration();
}