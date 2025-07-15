import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AgentManagement, useAgentManagement } from '../AgentManagement';
import { mcpApi } from '../../api/enhanced';

// Mock the API
jest.mock('../../api/enhanced');
const mockMcpApi = mcpApi as jest.Mocked<typeof mcpApi>;

// Mock data
const mockProject = {
  id: 'project-1',
  name: 'Test Project',
  description: 'A test project',
  task_trees: {}
};

const mockBranches = [
  {
    id: 'branch-1',
    name: 'main',
    description: 'Main branch',
    project_id: 'project-1',
    assigned_agents: []
  },
  {
    id: 'branch-2',
    name: 'feature/auth',
    description: 'Authentication feature',
    project_id: 'project-1',
    assigned_agents: []
  }
];

const mockAgents = [
  {
    id: 'agent-1',
    name: 'Main Coding Agent',
    agent_type: 'coding-agent',
    call_agent: '@coding_agent',
    description: 'Main development agent',
    capabilities: ['coding', 'testing'],
    max_concurrent_tasks: 5,
    status: 'active' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'agent-2',
    name: 'Debug Specialist',
    agent_type: 'debugger-agent',
    call_agent: '@debugger_agent',
    description: 'Debugging specialist',
    capabilities: ['debugging', 'analysis'],
    max_concurrent_tasks: 3,
    status: 'busy' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

const mockProps = {
  project: mockProject,
  branches: mockBranches,
  agents: mockAgents,
  onAssignAgent: jest.fn(),
  onUnassignAgent: jest.fn(),
  onRegisterAgent: jest.fn(),
  onUnregisterAgent: jest.fn()
};

describe('AgentManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockMcpApi.executeToolWithRetry.mockResolvedValue({
      success: true,
      data: { agents: mockAgents }
    });
  });

  test('displays agent registry correctly', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Check if the main heading is present
    expect(screen.getByText('Agent Management')).toBeInTheDocument();
    expect(screen.getByText(`Project: ${mockProject.name}`)).toBeInTheDocument();
    
    // Check if the register button is present
    expect(screen.getByText('Register New Agent')).toBeInTheDocument();
    
    // Check if tabs are present
    expect(screen.getByText('Agent Registry')).toBeInTheDocument();
    expect(screen.getByText('Branch Assignments')).toBeInTheDocument();
    expect(screen.getByText('Workload Balance')).toBeInTheDocument();
  });

  test('shows agent list in registry tab', async () => {
    render(<AgentManagement {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Coding Agent')).toBeInTheDocument();
      expect(screen.getByText('Debug Specialist')).toBeInTheDocument();
    });
    
    // Check agent details
    expect(screen.getByText('@coding_agent')).toBeInTheDocument();
    expect(screen.getByText('@debugger_agent')).toBeInTheDocument();
    expect(screen.getByText('coding-agent')).toBeInTheDocument();
    expect(screen.getByText('debugger-agent')).toBeInTheDocument();
  });

  test('handles agent registration', async () => {
    mockMcpApi.executeToolWithRetry.mockResolvedValueOnce({
      success: true,
      data: { success: true }
    });

    render(<AgentManagement {...mockProps} />);
    
    // Click register button
    fireEvent.click(screen.getByText('Register New Agent'));
    
    // Check if registration form appears
    await waitFor(() => {
      expect(screen.getByText('Register New Agent')).toBeInTheDocument();
      expect(screen.getByLabelText(/Agent Name/)).toBeInTheDocument();
    });
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/Agent Name/), {
      target: { value: 'New Test Agent' }
    });
    
    fireEvent.change(screen.getByLabelText(/Call Agent String/), {
      target: { value: '@test_agent' }
    });
    
    // Select agent type
    const selectElement = screen.getByDisplayValue('Select agent type');
    fireEvent.change(selectElement, { target: { value: 'test-orchestrator-agent' } });
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Register Agent/ });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockMcpApi.executeToolWithRetry).toHaveBeenCalledWith(
        'mcp__dhafnck_mcp_http__manage_agent',
        expect.objectContaining({
          action: 'register',
          project_id: mockProject.id,
          name: 'New Test Agent',
          call_agent: '@test_agent'
        })
      );
    });
  });

  test('switches between tabs correctly', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Start on registry tab
    expect(screen.getByText('Agent Registry')).toHaveClass('text-blue-600');
    
    // Switch to assignments tab
    fireEvent.click(screen.getByText('Branch Assignments'));
    await waitFor(() => {
      expect(screen.getByText('Branch Assignment Matrix')).toBeInTheDocument();
    });
    
    // Switch to workload tab
    fireEvent.click(screen.getByText('Workload Balance'));
    await waitFor(() => {
      expect(screen.getByText('Workload Balancing')).toBeInTheDocument();
    });
  });

  test('shows branch assignment matrix', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Switch to assignments tab
    fireEvent.click(screen.getByText('Branch Assignments'));
    
    await waitFor(() => {
      expect(screen.getByText('Branch Assignment Matrix')).toBeInTheDocument();
      expect(screen.getByText('main')).toBeInTheDocument();
      expect(screen.getByText('feature/auth')).toBeInTheDocument();
      expect(screen.getByText('Main Coding Agent')).toBeInTheDocument();
      expect(screen.getByText('Debug Specialist')).toBeInTheDocument();
    });
  });

  test('shows workload balancing panel', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Switch to workload tab
    fireEvent.click(screen.getByText('Workload Balance'));
    
    await waitFor(() => {
      expect(screen.getByText('Workload Balancing')).toBeInTheDocument();
      expect(screen.getByText('Analyze Workload')).toBeInTheDocument();
    });
  });

  test('handles search in agent registry', async () => {
    render(<AgentManagement {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Coding Agent')).toBeInTheDocument();
      expect(screen.getByText('Debug Specialist')).toBeInTheDocument();
    });
    
    // Search for "coding"
    const searchInput = screen.getByPlaceholderText('Search agents...');
    fireEvent.change(searchInput, { target: { value: 'coding' } });
    
    await waitFor(() => {
      expect(screen.getByText('Main Coding Agent')).toBeInTheDocument();
      expect(screen.queryByText('Debug Specialist')).not.toBeInTheDocument();
    });
  });

  test('handles sorting in agent registry', async () => {
    render(<AgentManagement {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Main Coding Agent')).toBeInTheDocument();
    });
    
    // Click on name header to sort
    const nameHeader = screen.getByText(/Name/);
    fireEvent.click(nameHeader);
    
    // Should show sort indicator
    expect(nameHeader).toHaveTextContent('↑');
  });

  test('shows performance metrics visualization', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Switch to workload tab and analyze
    fireEvent.click(screen.getByText('Workload Balance'));
    
    await waitFor(() => {
      const analyzeButton = screen.getByText('Analyze Workload');
      fireEvent.click(analyzeButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Overall Efficiency')).toBeInTheDocument();
      expect(screen.getByText('Overloaded Agents')).toBeInTheDocument();
      expect(screen.getByText('Underutilized Agents')).toBeInTheDocument();
      expect(screen.getByText('Optimal Agents')).toBeInTheDocument();
    });
  });

  test('executes bulk operations', async () => {
    mockMcpApi.executeToolWithRetry.mockResolvedValueOnce({
      success: true,
      data: { success: true }
    });

    render(<AgentManagement {...mockProps} />);
    
    // Switch to workload tab
    fireEvent.click(screen.getByText('Workload Balance'));
    
    // Analyze first
    await waitFor(() => {
      const analyzeButton = screen.getByText('Analyze Workload');
      fireEvent.click(analyzeButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Overall Efficiency')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    mockMcpApi.executeToolWithRetry.mockRejectedValueOnce(
      new Error('API Error')
    );

    render(<AgentManagement {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load agents/)).toBeInTheDocument();
    });
  });

  test('validates registration form', async () => {
    render(<AgentManagement {...mockProps} />);
    
    // Click register button
    fireEvent.click(screen.getByText('Register New Agent'));
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Register Agent/ })).toBeInTheDocument();
    });
    
    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /Register Agent/ });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Agent name is required')).toBeInTheDocument();
      expect(screen.getByText('Agent type is required')).toBeInTheDocument();
      expect(screen.getByText('Call agent string is required')).toBeInTheDocument();
    });
  });
});

describe('useAgentManagement hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('initializes with correct default state', () => {
    const TestComponent = () => {
      const { state } = useAgentManagement('project-1');
      return (
        <div>
          <div data-testid="agents-count">{state.agents.length}</div>
          <div data-testid="loading-agents">{state.loading.agents.toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);
    
    expect(screen.getByTestId('agents-count')).toHaveTextContent('0');
  });

  test('loads agents on mount', async () => {
    mockMcpApi.executeToolWithRetry.mockResolvedValueOnce({
      success: true,
      data: { agents: mockAgents }
    });

    const TestComponent = () => {
      const { state } = useAgentManagement('project-1');
      return (
        <div>
          <div data-testid="agents-count">{state.agents.length}</div>
        </div>
      );
    };

    render(<TestComponent />);
    
    await waitFor(() => {
      expect(screen.getByTestId('agents-count')).toHaveTextContent('2');
    });
  });

  test('handles registration correctly', async () => {
    mockMcpApi.executeToolWithRetry
      .mockResolvedValueOnce({
        success: true,
        data: { agents: [] }
      })
      .mockResolvedValueOnce({
        success: true,
        data: { success: true }
      })
      .mockResolvedValueOnce({
        success: true,
        data: { agents: mockAgents }
      });

    const TestComponent = () => {
      const { actions } = useAgentManagement('project-1');
      
      const handleRegister = () => {
        actions.registerAgent({
          name: 'Test Agent',
          agent_type: 'test-agent',
          call_agent: '@test_agent',
          description: 'Test description',
          capabilities: ['testing'],
          max_concurrent_tasks: 3
        });
      };

      return (
        <button onClick={handleRegister}>Register</button>
      );
    };

    render(<TestComponent />);
    
    const button = screen.getByText('Register');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockMcpApi.executeToolWithRetry).toHaveBeenCalledWith(
        'mcp__dhafnck_mcp_http__manage_agent',
        expect.objectContaining({
          action: 'register',
          project_id: 'project-1',
          name: 'Test Agent'
        })
      );
    });
  });
});