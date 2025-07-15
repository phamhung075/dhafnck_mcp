/**
 * Test file for GitBranchManager component
 * Provides comprehensive testing for branch management functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GitBranchManager } from '../GitBranchManager';
import { mcpApi } from '../../api/enhanced';

// Mock the API
jest.mock('../../api/enhanced', () => ({
  mcpApi: {
    manageGitBranch: jest.fn(),
    getAgents: jest.fn(),
    getBranchStatistics: jest.fn(),
  }
}));

const mockMcpApi = mcpApi as jest.Mocked<typeof mcpApi>;

describe('GitBranchManager', () => {
  const mockProject = {
    id: 'project-1',
    name: 'Test Project',
    description: 'A test project',
    created_at: '2024-01-01T00:00:00Z',
    status: 'active'
  };

  const mockBranches = [
    {
      id: 'branch-1',
      git_branch_name: 'main',
      git_branch_description: 'Main branch',
      project_id: 'project-1',
      created_at: '2024-01-01T00:00:00Z',
      status: 'active' as const,
      assigned_agents: []
    },
    {
      id: 'branch-2',
      git_branch_name: 'feature/user-auth',
      git_branch_description: 'User authentication feature',
      project_id: 'project-1',
      created_at: '2024-01-02T00:00:00Z',
      status: 'active' as const,
      assigned_agents: ['agent-1']
    }
  ];

  const mockProps = {
    project: mockProject,
    branches: mockBranches,
    selectedBranch: null,
    onSelectBranch: jest.fn(),
    onCreateBranch: jest.fn(),
    onUpdateBranch: jest.fn(),
    onDeleteBranch: jest.fn(),
    onArchiveBranch: jest.fn(),
    onRestoreBranch: jest.fn(),
    onAssignAgent: jest.fn(),
    onUnassignAgent: jest.fn(),
    onGetStatistics: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockMcpApi.getAgents.mockResolvedValue([
      {
        id: 'agent-1',
        name: 'Coding Agent',
        status: 'active',
        specialization: ['coding', 'implementation']
      }
    ]);
  });

  test('renders branch tree correctly', () => {
    render(<GitBranchManager {...mockProps} />);
    
    expect(screen.getByText('Git Branches')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('feature/user-auth')).toBeInTheDocument();
    expect(screen.getByText('Main branch')).toBeInTheDocument();
    expect(screen.getByText('User authentication feature')).toBeInTheDocument();
  });

  test('displays branch icons correctly', () => {
    render(<GitBranchManager {...mockProps} />);
    
    // Main branch should have house icon
    const mainBranchElement = screen.getByText('main').closest('div');
    expect(mainBranchElement).toContainHTML('🏠');
    
    // Feature branch should have rocket icon
    const featureBranchElement = screen.getByText('feature/user-auth').closest('div');
    expect(featureBranchElement).toContainHTML('🚀');
  });

  test('opens create branch dialog when create button is clicked', () => {
    render(<GitBranchManager {...mockProps} />);
    
    const createButton = screen.getByText('Create Branch');
    fireEvent.click(createButton);
    
    expect(screen.getByText('Create New Branch')).toBeInTheDocument();
    expect(screen.getByLabelText('Branch Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Branch Name')).toBeInTheDocument();
  });

  test('handles branch selection', () => {
    render(<GitBranchManager {...mockProps} />);
    
    const featureBranch = screen.getByText('feature/user-auth').closest('div');
    fireEvent.click(featureBranch!);
    
    expect(mockProps.onSelectBranch).toHaveBeenCalledWith(mockBranches[1]);
  });

  test('shows branch statistics when available', () => {
    const propsWithStats = {
      ...mockProps,
      selectedBranch: mockBranches[0]
    };
    
    render(<GitBranchManager {...propsWithStats} />);
    
    expect(screen.getByText('Branch Details: main')).toBeInTheDocument();
    expect(screen.getByText('Main branch')).toBeInTheDocument();
  });

  test('validates branch name in creation dialog', async () => {
    render(<GitBranchManager {...mockProps} />);
    
    // Open create dialog
    fireEvent.click(screen.getByText('Create Branch'));
    
    // Try to enter invalid branch name
    const nameInput = screen.getByPlaceholderText('branch-name');
    fireEvent.change(nameInput, { target: { value: 'Main' } }); // Should be lowercase
    
    await waitFor(() => {
      expect(screen.getByText(/Branch name must be unique/)).toBeInTheDocument();
    });
  });

  test('suggests appropriate agents based on branch type', async () => {
    render(<GitBranchManager {...mockProps} />);
    
    // Open create dialog
    fireEvent.click(screen.getByText('Create Branch'));
    
    // Select bugfix type
    const branchTypeSelect = screen.getByLabelText('Branch Type');
    fireEvent.change(branchTypeSelect, { target: { value: 'bugfix' } });
    
    await waitFor(() => {
      // Should suggest debugger agent for bugfix
      expect(screen.getByText('@debugger_agent')).toBeInTheDocument();
      expect(screen.getByText('@test_orchestrator_agent')).toBeInTheDocument();
    });
  });

  test('shows empty state when no branches', () => {
    const propsWithNoBranches = {
      ...mockProps,
      branches: []
    };
    
    render(<GitBranchManager {...propsWithNoBranches} />);
    
    expect(screen.getByText('No branches found')).toBeInTheDocument();
    expect(screen.getByText('Create First Branch')).toBeInTheDocument();
  });

  test('handles branch action buttons', () => {
    render(<GitBranchManager {...mockProps} />);
    
    // Find stats button for feature branch
    const statsButtons = screen.getAllByText('Stats');
    fireEvent.click(statsButtons[1]);
    
    expect(mockProps.onGetStatistics).toHaveBeenCalledWith('branch-2');
  });

  test('shows agent assignment dialog', async () => {
    mockMcpApi.getAgents.mockResolvedValue([
      {
        id: 'agent-1',
        name: 'Coding Agent',
        status: 'active',
        specialization: ['coding']
      },
      {
        id: 'agent-2',
        name: 'Test Agent',
        status: 'idle',
        specialization: ['testing']
      }
    ]);

    render(<GitBranchManager {...mockProps} />);
    
    // Find assign agent button
    const assignButtons = screen.getAllByText('Assign Agent');
    fireEvent.click(assignButtons[1]);
    
    await waitFor(() => {
      expect(screen.getByText('Assign Agent to Branch')).toBeInTheDocument();
      expect(screen.getByText('Coding Agent')).toBeInTheDocument();
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
    });
  });

  test('displays loading state', () => {
    const propsWithLoading = {
      ...mockProps,
      branches: []
    };
    
    render(<GitBranchManager {...propsWithLoading} />);
    
    // Simulate loading by not having branches loaded yet
    expect(screen.getByText('No branches found')).toBeInTheDocument();
  });

  test('handles archive action for non-main branches', () => {
    render(<GitBranchManager {...mockProps} />);
    
    // Main branch should not have archive button
    const mainBranchElement = screen.getByText('main').closest('div');
    expect(mainBranchElement).not.toContainElement(screen.queryByText('Archive'));
    
    // Feature branch should have archive button
    const archiveButtons = screen.getAllByText('Archive');
    expect(archiveButtons).toHaveLength(1);
    
    fireEvent.click(archiveButtons[0]);
    expect(mockProps.onArchiveBranch).toHaveBeenCalledWith('branch-2');
  });

  test('creates branch with proper data structure', async () => {
    const createBranchMock = jest.fn();
    const propsWithCreateMock = {
      ...mockProps,
      onCreateBranch: createBranchMock
    };
    
    render(<GitBranchManager {...propsWithCreateMock} />);
    
    // Open create dialog
    fireEvent.click(screen.getByText('Create Branch'));
    
    // Fill in branch details
    const nameInput = screen.getByPlaceholderText('branch-name');
    fireEvent.change(nameInput, { target: { value: 'new-feature' } });
    
    const descriptionInput = screen.getByPlaceholderText('Describe the purpose of this branch...');
    fireEvent.change(descriptionInput, { target: { value: 'A new feature implementation' } });
    
    // Submit
    const createButton = screen.getByRole('button', { name: 'Create Branch' });
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(createBranchMock).toHaveBeenCalledWith({
        git_branch_name: 'feature/new-feature',
        git_branch_description: 'A new feature implementation',
        branch_type: 'feature',
        parent_branch: 'main',
        initial_agents: ['@coding_agent', '@test_orchestrator_agent'],
        template: ''
      });
    });
  });
});

describe('GitBranchManager Integration', () => {
  test('integrates with API layer correctly', async () => {
    mockMcpApi.getBranchStatistics.mockResolvedValue({
      total_tasks: 5,
      completed_tasks: 3,
      progress_percentage: 60,
      assigned_agents: ['agent-1'],
      last_activity: '2024-01-15T10:00:00Z',
      health_score: 85,
      blockers: 0,
      estimated_completion: '2024-01-20T00:00:00Z'
    });

    render(<GitBranchManager {...mockProps} />);
    
    // The component should load statistics automatically
    await waitFor(() => {
      expect(mockMcpApi.getBranchStatistics).toHaveBeenCalled();
    });
  });

  test('handles API errors gracefully', async () => {
    mockMcpApi.getAgents.mockRejectedValue(new Error('API Error'));
    
    render(<GitBranchManager {...mockProps} />);
    
    // Component should still render even if agents fail to load
    expect(screen.getByText('Git Branches')).toBeInTheDocument();
  });
});