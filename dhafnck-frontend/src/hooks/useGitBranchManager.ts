/**
 * Custom hook for Git Branch Management
 * Provides state management and API integration for the GitBranchManager component
 */

import { useState, useEffect, useCallback } from 'react';
import { mcpApi, Agent } from '../api/enhanced';
import { 
  GitBranch, 
  BranchStatistics, 
  DetailedBranchStatistics, 
  CreateBranchData,
  AgentAssignment
} from '../components/GitBranchManager';

interface GitBranchManagerState {
  branches: GitBranch[];
  selectedBranch: GitBranch | null;
  branchStatistics: Record<string, BranchStatistics>;
  detailedStatistics: Record<string, DetailedBranchStatistics>;
  agentAssignments: Record<string, AgentAssignment[]>;
  availableAgents: Agent[];
  loading: {
    branches: boolean;
    statistics: boolean;
    operations: boolean;
    agents: boolean;
  };
  error: string | null;
}

export function useGitBranchManager(projectId: string) {
  const [state, setState] = useState<GitBranchManagerState>({
    branches: [],
    selectedBranch: null,
    branchStatistics: {},
    detailedStatistics: {},
    agentAssignments: {},
    availableAgents: [],
    loading: {
      branches: false,
      statistics: false,
      operations: false,
      agents: false
    },
    error: null
  });

  // Load branches for the project
  const loadBranches = useCallback(async () => {
    if (!projectId) return;

    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, branches: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('list', { project_id: projectId });
      
      if (response.success && response.data?.git_branches) {
        const branches = response.data.git_branches;
        setState(prev => ({
          ...prev,
          branches,
          selectedBranch: prev.selectedBranch 
            ? branches.find((b: GitBranch) => b.id === prev.selectedBranch?.id) || null
            : null
        }));

        // Load statistics for each branch
        await loadBranchStatistics(branches);
      } else {
        throw new Error(response.error || 'Failed to load branches');
      }
    } catch (error) {
      console.error('Failed to load branches:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load branches'
      }));
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, branches: false }
      }));
    }
  }, [projectId]);

  // Load branch statistics
  const loadBranchStatistics = useCallback(async (branches: GitBranch[]) => {
    if (!branches.length) return;

    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, statistics: true }
    }));

    try {
      const statisticsPromises = branches.map(async (branch: GitBranch) => {
        try {
          const response = await mcpApi.manageGitBranch('get_statistics', { 
            project_id: projectId, 
            git_branch_id: branch.id 
          });
          
          if (response.success && response.data) {
            return { branchId: branch.id, stats: response.data };
          }
          return { branchId: branch.id, stats: null };
        } catch (error) {
          console.warn(`Failed to load statistics for branch ${branch.id}:`, error);
          return { branchId: branch.id, stats: null };
        }
      });

      const statisticsResults = await Promise.all(statisticsPromises);
      const branchStats = statisticsResults.reduce((acc, { branchId, stats }) => {
        if (stats) {
          acc[branchId] = stats;
        }
        return acc;
      }, {} as Record<string, BranchStatistics>);

      setState(prev => ({
        ...prev,
        branchStatistics: branchStats
      }));
    } catch (error) {
      console.error('Failed to load branch statistics:', error);
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, statistics: false }
      }));
    }
  }, [projectId]);

  // Load available agents
  const loadAgents = useCallback(async () => {
    if (!projectId) return;

    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, agents: true }
    }));

    try {
      const response = await mcpApi.manageAgent('list', { project_id: projectId });
      
      if (response.success && response.data?.agents) {
        setState(prev => ({
          ...prev,
          availableAgents: response.data.agents
        }));
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, agents: false }
      }));
    }
  }, [projectId]);

  // Load agent assignments for a specific branch
  const loadAgentAssignments = useCallback(async (branchId: string) => {
    try {
      // This would typically call a specific endpoint for agent assignments
      // For now, we'll derive it from the branch statistics
      const stats = state.branchStatistics[branchId];
      if (stats && stats.assigned_agents) {
        const assignments: AgentAssignment[] = stats.assigned_agents.map(agentId => ({
          agent_id: agentId,
          agent_name: state.availableAgents.find(a => a.id === agentId)?.name || agentId,
          role: 'secondary' as const,
          assigned_at: new Date().toISOString(),
          workload_percentage: 50,
          specialization: []
        }));

        setState(prev => ({
          ...prev,
          agentAssignments: {
            ...prev.agentAssignments,
            [branchId]: assignments
          }
        }));
      }
    } catch (error) {
      console.error('Failed to load agent assignments:', error);
    }
  }, [state.branchStatistics, state.availableAgents]);

  // Create a new branch
  const createBranch = useCallback(async (branchData: CreateBranchData) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('create', {
        project_id: projectId,
        git_branch_name: branchData.git_branch_name,
        git_branch_description: branchData.git_branch_description
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to create branch');
      }

      // Assign initial agents if specified
      if (branchData.initial_agents.length > 0 && response.data?.git_branch) {
        const newBranchId = response.data.git_branch.id;
        
        for (const agentId of branchData.initial_agents) {
          try {
            await mcpApi.manageGitBranch('assign_agent', {
              project_id: projectId,
              git_branch_id: newBranchId,
              agent_id: agentId
            });
          } catch (error) {
            console.warn(`Failed to assign agent ${agentId} to new branch:`, error);
          }
        }
      }

      // Reload branches to get the updated list
      await loadBranches();
    } catch (error) {
      console.error('Failed to create branch:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to create branch'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranches]);

  // Update a branch
  const updateBranch = useCallback(async (branchId: string, updates: Partial<GitBranch>) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('update', {
        project_id: projectId,
        git_branch_id: branchId,
        ...updates
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to update branch');
      }

      await loadBranches();
    } catch (error) {
      console.error('Failed to update branch:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to update branch'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranches]);

  // Delete a branch
  const deleteBranch = useCallback(async (branchId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('delete', {
        project_id: projectId,
        git_branch_id: branchId
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to delete branch');
      }

      await loadBranches();
    } catch (error) {
      console.error('Failed to delete branch:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to delete branch'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranches]);

  // Archive a branch
  const archiveBranch = useCallback(async (branchId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('archive', {
        project_id: projectId,
        git_branch_id: branchId
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to archive branch');
      }

      await loadBranches();
    } catch (error) {
      console.error('Failed to archive branch:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to archive branch'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranches]);

  // Restore a branch
  const restoreBranch = useCallback(async (branchId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('restore', {
        project_id: projectId,
        git_branch_id: branchId
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to restore branch');
      }

      await loadBranches();
    } catch (error) {
      console.error('Failed to restore branch:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to restore branch'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranches]);

  // Assign agent to branch
  const assignAgent = useCallback(async (branchId: string, agentId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('assign_agent', {
        project_id: projectId,
        git_branch_id: branchId,
        agent_id: agentId
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to assign agent');
      }

      // Reload branch statistics to reflect the new assignment
      await loadBranchStatistics(state.branches);
      await loadAgentAssignments(branchId);
    } catch (error) {
      console.error('Failed to assign agent:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to assign agent'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranchStatistics, loadAgentAssignments, state.branches]);

  // Unassign agent from branch
  const unassignAgent = useCallback(async (branchId: string, agentId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, operations: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('unassign_agent', {
        project_id: projectId,
        git_branch_id: branchId,
        agent_id: agentId
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to unassign agent');
      }

      await loadBranchStatistics(state.branches);
      await loadAgentAssignments(branchId);
    } catch (error) {
      console.error('Failed to unassign agent:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to unassign agent'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, operations: false }
      }));
    }
  }, [projectId, loadBranchStatistics, loadAgentAssignments, state.branches]);

  // Get detailed statistics for a branch
  const getStatistics = useCallback(async (branchId: string) => {
    setState(prev => ({ 
      ...prev, 
      loading: { ...prev.loading, statistics: true },
      error: null
    }));

    try {
      const response = await mcpApi.manageGitBranch('get_statistics', {
        project_id: projectId,
        git_branch_id: branchId
      });

      if (response.success && response.data) {
        setState(prev => ({
          ...prev,
          detailedStatistics: {
            ...prev.detailedStatistics,
            [branchId]: response.data
          }
        }));
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to get statistics');
      }
    } catch (error) {
      console.error('Failed to get statistics:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to get statistics'
      }));
      throw error;
    } finally {
      setState(prev => ({ 
        ...prev, 
        loading: { ...prev.loading, statistics: false }
      }));
    }
  }, [projectId]);

  // Select a branch
  const selectBranch = useCallback((branch: GitBranch | null) => {
    setState(prev => ({
      ...prev,
      selectedBranch: branch
    }));

    // Load agent assignments for the selected branch
    if (branch) {
      loadAgentAssignments(branch.id);
    }
  }, [loadAgentAssignments]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null
    }));
  }, []);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    await Promise.all([
      loadBranches(),
      loadAgents()
    ]);
  }, [loadBranches, loadAgents]);

  // Initial load
  useEffect(() => {
    if (projectId) {
      refreshAll();
    }
  }, [projectId, refreshAll]);

  return {
    // State
    state,
    
    // Actions
    actions: {
      loadBranches,
      loadBranchStatistics,
      loadAgents,
      loadAgentAssignments,
      createBranch,
      updateBranch,
      deleteBranch,
      archiveBranch,
      restoreBranch,
      assignAgent,
      unassignAgent,
      getStatistics,
      selectBranch,
      clearError,
      refreshAll
    },

    // Computed values
    computed: {
      hasError: !!state.error,
      isLoading: Object.values(state.loading).some(Boolean),
      totalBranches: state.branches.length,
      activeBranches: state.branches.filter(b => b.status === 'active').length,
      archivedBranches: state.branches.filter(b => b.status === 'archived').length,
      totalAgents: state.availableAgents.length,
      assignedAgents: new Set(
        Object.values(state.branchStatistics)
          .flatMap(stats => stats.assigned_agents)
      ).size
    }
  };
}

export default useGitBranchManager;