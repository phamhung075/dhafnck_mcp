import React, { useState, useEffect, useMemo } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Dialog } from './ui/dialog';
import { Alert } from './ui/alert';
import { Table } from './ui/table';
import { mcpApi } from '../api/enhanced';
import type { Project, Branch } from '../api/enhanced';

// Agent Types and Interfaces
export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  call_agent: string;
  description?: string;
  capabilities?: string[];
  max_concurrent_tasks: number;
  status: 'active' | 'inactive' | 'busy' | 'error';
  created_at: string;
  updated_at: string;
}

export interface GitBranch {
  id: string;
  name: string;
  description: string;
  project_id: string;
  assigned_agents?: string[];
}

export interface AgentAssignment {
  agent_id: string;
  branch_id: string;
  role: 'primary' | 'secondary' | 'reviewer';
  assigned_at: string;
  workload_percentage: number;
}

export interface RegisterAgentData {
  name: string;
  agent_type: string;
  call_agent: string;
  description: string;
  capabilities: string[];
  max_concurrent_tasks: number;
}

export interface AgentPerformanceMetrics {
  agent_id: string;
  tasks_completed: number;
  success_rate: number;
  average_completion_time: number;
  current_workload: number;
  efficiency_score: number;
  user_satisfaction: number;
}

export interface WorkloadAnalysis {
  overloaded_agents: string[];
  underutilized_agents: string[];
  optimal_agents: string[];
  overall_efficiency: number;
}

export interface RebalancingRecommendation {
  action: 'reassign' | 'add_agent' | 'remove_agent';
  agent_id: string;
  source_branch?: string;
  target_branch?: string;
  reason: string;
}

// Main Props Interface
export interface AgentManagementProps {
  project: Project;
  branches: GitBranch[];
  agents: Agent[];
  onAssignAgent: (agentId: string, branchId: string) => Promise<void>;
  onUnassignAgent: (agentId: string, branchId: string) => Promise<void>;
  onRegisterAgent: (agentData: RegisterAgentData) => Promise<void>;
  onUnregisterAgent: (agentId: string) => Promise<void>;
}

// Agent Management State
interface AgentManagementState {
  agents: Agent[];
  assignments: AgentAssignment[];
  performanceMetrics: Record<string, AgentPerformanceMetrics>;
  workloadAnalysis: WorkloadAnalysis | null;
  loading: {
    agents: boolean;
    assignments: boolean;
    registration: boolean;
    rebalancing: boolean;
  };
  errors: {
    [key: string]: string;
  };
}

// Custom Hook for Agent Management
export function useAgentManagement(projectId: string) {
  const [state, setState] = useState<AgentManagementState>({
    agents: [],
    assignments: [],
    performanceMetrics: {},
    workloadAnalysis: null,
    loading: {
      agents: false,
      assignments: false,
      registration: false,
      rebalancing: false,
    },
    errors: {},
  });

  const setLoading = (key: keyof AgentManagementState['loading'], value: boolean) => {
    setState(prev => ({
      ...prev,
      loading: { ...prev.loading, [key]: value }
    }));
  };

  const setError = (key: string, message: string) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, [key]: message }
    }));
  };

  const clearError = (key: string) => {
    setState(prev => {
      const newErrors = { ...prev.errors };
      delete newErrors[key];
      return { ...prev, errors: newErrors };
    });
  };

  const refreshAgents = async () => {
    setLoading('agents', true);
    clearError('agents');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'list',
        project_id: projectId
      });
      
      if (response.success && response.data) {
        const data = response.data as any;
        setState(prev => ({ ...prev, agents: data.agents || [] }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('agents', `Failed to load agents: ${message}`);
    } finally {
      setLoading('agents', false);
    }
  };

  const refreshAssignments = async () => {
    setLoading('assignments', true);
    clearError('assignments');
    try {
      // Note: This would need to be implemented in the backend
      // For now, we'll simulate the data structure
      setState(prev => ({ ...prev, assignments: [] }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('assignments', `Failed to load assignments: ${message}`);
    } finally {
      setLoading('assignments', false);
    }
  };

  const registerAgent = async (agentData: RegisterAgentData) => {
    setLoading('registration', true);
    clearError('registration');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'register',
        project_id: projectId,
        ...agentData
      });
      
      if (response.success) {
        await refreshAgents();
        return true;
      } else {
        throw new Error(response.error || 'Registration failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('registration', `Failed to register agent: ${message}`);
      return false;
    } finally {
      setLoading('registration', false);
    }
  };

  const unregisterAgent = async (agentId: string) => {
    setLoading('agents', true);
    clearError('agents');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'unregister',
        project_id: projectId,
        agent_id: agentId
      });
      
      if (response.success) {
        await refreshAgents();
        return true;
      } else {
        throw new Error(response.error || 'Unregistration failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('agents', `Failed to unregister agent: ${message}`);
      return false;
    } finally {
      setLoading('agents', false);
    }
  };

  const assignAgent = async (agentId: string, branchId: string) => {
    setLoading('assignments', true);
    clearError('assignments');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'assign',
        project_id: projectId,
        agent_id: agentId,
        git_branch_id: branchId
      });
      
      if (response.success) {
        await refreshAssignments();
        return true;
      } else {
        throw new Error(response.error || 'Assignment failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('assignments', `Failed to assign agent: ${message}`);
      return false;
    } finally {
      setLoading('assignments', false);
    }
  };

  const unassignAgent = async (agentId: string, branchId: string) => {
    setLoading('assignments', true);
    clearError('assignments');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'unassign',
        project_id: projectId,
        agent_id: agentId,
        git_branch_id: branchId
      });
      
      if (response.success) {
        await refreshAssignments();
        return true;
      } else {
        throw new Error(response.error || 'Unassignment failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('assignments', `Failed to unassign agent: ${message}`);
      return false;
    } finally {
      setLoading('assignments', false);
    }
  };

  const analyzeWorkload = async () => {
    setLoading('rebalancing', true);
    clearError('rebalancing');
    try {
      // Simulate workload analysis
      const analysis: WorkloadAnalysis = {
        overloaded_agents: [],
        underutilized_agents: [],
        optimal_agents: state.agents.map(a => a.id),
        overall_efficiency: 0.85
      };
      setState(prev => ({ ...prev, workloadAnalysis: analysis }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('rebalancing', `Failed to analyze workload: ${message}`);
    } finally {
      setLoading('rebalancing', false);
    }
  };

  const rebalanceAgents = async () => {
    setLoading('rebalancing', true);
    clearError('rebalancing');
    try {
      const response = await mcpApi.executeToolWithRetry('mcp__dhafnck_mcp_http__manage_agent', {
        action: 'rebalance',
        project_id: projectId
      });
      
      if (response.success) {
        await refreshAgents();
        await refreshAssignments();
        await analyzeWorkload();
        return true;
      } else {
        throw new Error(response.error || 'Rebalancing failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setError('rebalancing', `Failed to rebalance agents: ${message}`);
      return false;
    } finally {
      setLoading('rebalancing', false);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    if (projectId) {
      refreshAgents();
      refreshAssignments();
    }
  }, [projectId]);

  return {
    state,
    actions: {
      registerAgent,
      unregisterAgent,
      assignAgent,
      unassignAgent,
      refreshAgents,
      refreshAssignments,
      analyzeWorkload,
      rebalanceAgents,
    }
  };
}

// Agent Registry Table Component
interface AgentRegistryTableProps {
  agents: Agent[];
  onEditAgent: (agent: Agent) => void;
  onDeleteAgent: (agentId: string) => void;
  onViewPerformance: (agentId: string) => void;
  loading?: boolean;
}

function AgentRegistryTable({
  agents,
  onEditAgent,
  onDeleteAgent,
  onViewPerformance,
  loading = false
}: AgentRegistryTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof Agent>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const filteredAndSortedAgents = useMemo(() => {
    let filtered = agents.filter(agent =>
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.agent_type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    filtered.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      const modifier = sortDirection === 'asc' ? 1 : -1;
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return aVal.localeCompare(bVal) * modifier;
      }
      
      // Handle undefined values
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return -1 * modifier;
      if (bVal === undefined) return 1 * modifier;
      
      // At this point, both aVal and bVal are defined
      return (aVal! < bVal! ? -1 : aVal! > bVal! ? 1 : 0) * modifier;
    });

    return filtered;
  }, [agents, searchTerm, sortField, sortDirection]);

  const handleSort = (field: keyof Agent) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getStatusBadgeVariant = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'default';
      case 'busy': return 'secondary';
      case 'inactive': return 'outline';
      case 'error': return 'destructive';
      default: return 'outline';
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Agent Registry</h3>
          <Input
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th 
                  className="text-left p-2 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('name')}
                >
                  Name {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="text-left p-2 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('agent_type')}
                >
                  Type {sortField === 'agent_type' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="text-left p-2 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('status')}
                >
                  Status {sortField === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th className="text-left p-2">Max Tasks</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAndSortedAgents.map((agent) => (
                <tr key={agent.id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{agent.name}</div>
                      <div className="text-sm text-gray-500">{agent.call_agent}</div>
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant="outline">{agent.agent_type}</Badge>
                  </td>
                  <td className="p-2">
                    <Badge variant={getStatusBadgeVariant(agent.status)}>
                      {agent.status}
                    </Badge>
                  </td>
                  <td className="p-2">{agent.max_concurrent_tasks}</td>
                  <td className="p-2">
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onEditAgent(agent)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onViewPerformance(agent.id)}
                      >
                        Performance
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => onDeleteAgent(agent.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAndSortedAgents.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            {searchTerm ? 'No agents match your search' : 'No agents registered'}
          </div>
        )}
      </div>
    </Card>
  );
}

// Branch Assignment Matrix Component
interface BranchAssignmentMatrixProps {
  branches: GitBranch[];
  agents: Agent[];
  assignments: AgentAssignment[];
  onToggleAssignment: (agentId: string, branchId: string) => Promise<void>;
  loading?: boolean;
}

function BranchAssignmentMatrix({
  branches,
  agents,
  assignments,
  onToggleAssignment,
  loading = false
}: BranchAssignmentMatrixProps) {
  const isAssigned = (agentId: string, branchId: string) => {
    return assignments.some(a => a.agent_id === agentId && a.branch_id === branchId);
  };

  const getWorkloadColor = (workload: number) => {
    if (workload >= 80) return 'bg-red-100 border-red-300';
    if (workload >= 60) return 'bg-yellow-100 border-yellow-300';
    if (workload >= 40) return 'bg-blue-100 border-blue-300';
    return 'bg-green-100 border-green-300';
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: 16 }).map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Branch Assignment Matrix</h3>
        
        <div className="overflow-x-auto">
          <div className="grid gap-2" style={{ gridTemplateColumns: `120px repeat(${branches.length}, 1fr)` }}>
            {/* Header */}
            <div className="p-2 font-semibold"></div>
            {branches.map(branch => (
              <div key={branch.id} className="p-2 font-semibold text-sm text-center border-b">
                {branch.name}
              </div>
            ))}
            
            {/* Agent rows */}
            {agents.map(agent => (
              <React.Fragment key={agent.id}>
                <div className="p-2 font-medium text-sm border-r">
                  {agent.name}
                </div>
                {branches.map(branch => {
                  const assigned = isAssigned(agent.id, branch.id);
                  const assignment = assignments.find(a => a.agent_id === agent.id && a.branch_id === branch.id);
                  const workload = assignment?.workload_percentage || 0;
                  
                  return (
                    <div
                      key={`${agent.id}-${branch.id}`}
                      className={`p-2 text-center border cursor-pointer transition-colors ${
                        assigned 
                          ? `${getWorkloadColor(workload)} hover:opacity-80`
                          : 'hover:bg-gray-100'
                      }`}
                      onClick={() => onToggleAssignment(agent.id, branch.id)}
                    >
                      {assigned && (
                        <div className="text-xs">
                          <div>{assignment?.role}</div>
                          <div>{workload}%</div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
        </div>

        <div className="flex space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300"></div>
            <span>Low workload (&lt;40%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-300"></div>
            <span>Medium workload (40-60%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300"></div>
            <span>High workload (60-80%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-100 border border-red-300"></div>
            <span>Overloaded (&gt;80%)</span>
          </div>
        </div>
      </div>
    </Card>
  );
}

// Agent Registration Form Component
interface AgentRegistrationFormProps {
  onSubmit: (data: RegisterAgentData) => Promise<boolean>;
  onCancel: () => void;
  loading?: boolean;
}

function AgentRegistrationForm({ onSubmit, onCancel, loading = false }: AgentRegistrationFormProps) {
  const [formData, setFormData] = useState<RegisterAgentData>({
    name: '',
    agent_type: '',
    call_agent: '',
    description: '',
    capabilities: [],
    max_concurrent_tasks: 5
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const agentTypes = [
    'coding-agent',
    'debugger-agent',
    'test-orchestrator-agent',
    'ui-designer-agent',
    'security-auditor-agent',
    'devops-agent',
    'documentation-agent',
    'uber-orchestrator-agent'
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Agent name is required';
    }
    if (!formData.agent_type) {
      newErrors.agent_type = 'Agent type is required';
    }
    if (!formData.call_agent.trim()) {
      newErrors.call_agent = 'Call agent string is required';
    }
    if (formData.max_concurrent_tasks < 1) {
      newErrors.max_concurrent_tasks = 'Max concurrent tasks must be at least 1';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const success = await onSubmit(formData);
    if (success) {
      onCancel(); // Close form on success
    }
  };

  const handleInputChange = (field: keyof RegisterAgentData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="text-lg font-semibold">Register New Agent</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Agent Name *</label>
            <Input
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Main Coding Agent"
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && <div className="text-red-500 text-sm mt-1">{errors.name}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Agent Type *</label>
            <select
              value={formData.agent_type}
              onChange={(e) => handleInputChange('agent_type', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md ${errors.agent_type ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="">Select agent type</option>
              {agentTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            {errors.agent_type && <div className="text-red-500 text-sm mt-1">{errors.agent_type}</div>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Call Agent String *</label>
          <Input
            value={formData.call_agent}
            onChange={(e) => handleInputChange('call_agent', e.target.value)}
            placeholder="e.g., @coding_agent"
            className={errors.call_agent ? 'border-red-500' : ''}
          />
          {errors.call_agent && <div className="text-red-500 text-sm mt-1">{errors.call_agent}</div>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Describe the agent's purpose and capabilities"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            rows={3}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Max Concurrent Tasks</label>
          <Input
            type="number"
            value={formData.max_concurrent_tasks}
            onChange={(e) => handleInputChange('max_concurrent_tasks', parseInt(e.target.value) || 1)}
            min="1"
            max="20"
            className={errors.max_concurrent_tasks ? 'border-red-500' : ''}
          />
          {errors.max_concurrent_tasks && <div className="text-red-500 text-sm mt-1">{errors.max_concurrent_tasks}</div>}
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? 'Registering...' : 'Register Agent'}
          </Button>
        </div>
      </form>
    </Card>
  );
}

// Workload Balancing Panel Component
interface WorkloadBalancingPanelProps {
  analysis: WorkloadAnalysis | null;
  recommendations: RebalancingRecommendation[];
  onExecuteRebalancing: () => Promise<boolean>;
  onAnalyzeWorkload: () => Promise<void>;
  loading?: boolean;
}

function WorkloadBalancingPanel({
  analysis,
  recommendations,
  onExecuteRebalancing,
  onAnalyzeWorkload,
  loading = false
}: WorkloadBalancingPanelProps) {
  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 0.8) return 'text-green-600';
    if (efficiency >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getEfficiencyBg = (efficiency: number) => {
    if (efficiency >= 0.8) return 'bg-green-100';
    if (efficiency >= 0.6) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Workload Balancing</h3>
          <Button 
            onClick={onAnalyzeWorkload}
            disabled={loading}
            variant="outline"
          >
            {loading ? 'Analyzing...' : 'Analyze Workload'}
          </Button>
        </div>

        {analysis && (
          <div className="space-y-4">
            <div className={`p-4 rounded-lg ${getEfficiencyBg(analysis.overall_efficiency)}`}>
              <div className="flex justify-between items-center">
                <span className="font-medium">Overall Efficiency</span>
                <span className={`text-lg font-bold ${getEfficiencyColor(analysis.overall_efficiency)}`}>
                  {(analysis.overall_efficiency * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-medium text-red-800 mb-2">Overloaded Agents</h4>
                <div className="text-2xl font-bold text-red-600">
                  {analysis.overloaded_agents.length}
                </div>
                {analysis.overloaded_agents.length > 0 && (
                  <div className="text-sm text-red-600 mt-1">
                    Agents need workload reduction
                  </div>
                )}
              </div>

              <div className="p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium text-yellow-800 mb-2">Underutilized Agents</h4>
                <div className="text-2xl font-bold text-yellow-600">
                  {analysis.underutilized_agents.length}
                </div>
                {analysis.underutilized_agents.length > 0 && (
                  <div className="text-sm text-yellow-600 mt-1">
                    Agents can take more tasks
                  </div>
                )}
              </div>

              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">Optimal Agents</h4>
                <div className="text-2xl font-bold text-green-600">
                  {analysis.optimal_agents.length}
                </div>
                <div className="text-sm text-green-600 mt-1">
                  Agents well-balanced
                </div>
              </div>
            </div>

            {recommendations.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium">Rebalancing Recommendations</h4>
                {recommendations.map((rec, index) => (
                  <div key={index} className="p-3 bg-blue-50 rounded border">
                    <div className="font-medium">{rec.action.toUpperCase()}</div>
                    <div className="text-sm text-gray-600">{rec.reason}</div>
                  </div>
                ))}
                
                <Button 
                  onClick={onExecuteRebalancing}
                  disabled={loading}
                  className="w-full mt-4"
                >
                  {loading ? 'Rebalancing...' : 'Execute Rebalancing'}
                </Button>
              </div>
            )}
          </div>
        )}

        {!analysis && !loading && (
          <div className="text-center py-8 text-gray-500">
            Click "Analyze Workload" to assess agent distribution
          </div>
        )}
      </div>
    </Card>
  );
}

// Main Agent Management Component
export function AgentManagement({
  project,
  branches,
  agents,
  onAssignAgent,
  onUnassignAgent,
  onRegisterAgent,
  onUnregisterAgent
}: AgentManagementProps) {
  const [activeTab, setActiveTab] = useState<'registry' | 'assignments' | 'registration' | 'workload'>('registry');
  const [showRegistrationForm, setShowRegistrationForm] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const { state, actions } = useAgentManagement(project.id);

  const tabs = [
    { id: 'registry', label: 'Agent Registry', count: state.agents.length },
    { id: 'assignments', label: 'Branch Assignments', count: state.assignments.length },
    { id: 'workload', label: 'Workload Balance', count: null },
  ];

  const handleToggleAssignment = async (agentId: string, branchId: string) => {
    const isAssigned = state.assignments.some(a => a.agent_id === agentId && a.branch_id === branchId);
    
    if (isAssigned) {
      await actions.unassignAgent(agentId, branchId);
    } else {
      await actions.assignAgent(agentId, branchId);
    }
  };

  // Mock recommendations for demo
  const mockRecommendations: RebalancingRecommendation[] = [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Agent Management</h2>
          <p className="text-gray-600">Project: {project.name}</p>
        </div>
        
        <Button onClick={() => setShowRegistrationForm(true)}>
          Register New Agent
        </Button>
      </div>

      {/* Error Display */}
      {Object.entries(state.errors).map(([key, error]) => (
        <Alert key={key} variant="destructive">
          <strong>{key}:</strong> {error}
        </Alert>
      ))}

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== null && (
                <Badge variant="secondary" className="ml-2">
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'registry' && (
        <AgentRegistryTable
          agents={state.agents}
          onEditAgent={setSelectedAgent}
          onDeleteAgent={actions.unregisterAgent}
          onViewPerformance={(agentId) => console.log('View performance for', agentId)}
          loading={state.loading.agents}
        />
      )}

      {activeTab === 'assignments' && (
        <BranchAssignmentMatrix
          branches={branches}
          agents={state.agents}
          assignments={state.assignments}
          onToggleAssignment={handleToggleAssignment}
          loading={state.loading.assignments}
        />
      )}

      {activeTab === 'workload' && (
        <WorkloadBalancingPanel
          analysis={state.workloadAnalysis}
          recommendations={mockRecommendations}
          onExecuteRebalancing={actions.rebalanceAgents}
          onAnalyzeWorkload={actions.analyzeWorkload}
          loading={state.loading.rebalancing}
        />
      )}

      {/* Registration Form Modal */}
      {showRegistrationForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-2xl w-full mx-4">
            <AgentRegistrationForm
              onSubmit={actions.registerAgent}
              onCancel={() => setShowRegistrationForm(false)}
              loading={state.loading.registration}
            />
          </div>
        </div>
      )}
    </div>
  );
}