/**
 * Git Branch Management Interface
 * Provides comprehensive branch and task tree management with agent assignment
 */

import React, { useState, useEffect } from 'react';
import { mcpApi, Agent } from '../api/enhanced';

// Core Type Definitions
export interface GitBranch {
  id: string;
  git_branch_name: string;
  git_branch_description: string;
  project_id: string;
  created_at: string;
  status: 'active' | 'archived' | 'deleted';
  assigned_agents: string[];
}

export interface CreateBranchData {
  git_branch_name: string;
  git_branch_description: string;
  branch_type: 'feature' | 'bugfix' | 'hotfix' | 'release' | 'experiment';
  parent_branch?: string;
  initial_agents: string[];
  template?: string;
}

export interface BranchStatistics {
  total_tasks: number;
  completed_tasks: number;
  progress_percentage: number;
  assigned_agents: string[];
  last_activity: string;
  health_score: number;
  blockers: number;
  estimated_completion: string;
}

export interface DetailedBranchStatistics {
  basic: BranchStatistics;
  tasks: {
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
    by_assignee: Record<string, number>;
    completion_trend: DataPoint[];
  };
  agents: {
    utilization: Record<string, number>;
    performance: Record<string, AgentPerformance>;
  };
  timeline: {
    created_at: string;
    first_task_at: string;
    last_activity_at: string;
    estimated_completion: string;
  };
  health: {
    score: number;
    factors: HealthFactor[];
    recommendations: string[];
  };
}

export interface DataPoint {
  date: string;
  value: number;
}

export interface AgentPerformance {
  completed_tasks: number;
  success_rate: number;
  average_completion_time: number;
}

export interface HealthFactor {
  name: string;
  score: number;
  weight: number;
  description: string;
}


export interface AgentAssignment {
  agent_id: string;
  agent_name: string;
  role: 'primary' | 'secondary' | 'reviewer' | 'consultant';
  assigned_at: string;
  workload_percentage: number;
  specialization: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  status: string;
}

export interface BranchAction {
  type: 'assign_agent' | 'archive' | 'restore' | 'merge' | 'delete' | 'statistics';
  data?: any;
}

// Props interface for the main component
export interface GitBranchManagerProps {
  project: Project;
  branches: GitBranch[];
  selectedBranch: GitBranch | null;
  onSelectBranch: (branch: GitBranch) => void;
  onCreateBranch: (branchData: CreateBranchData) => Promise<void>;
  onUpdateBranch: (branchId: string, updates: Partial<GitBranch>) => Promise<void>;
  onDeleteBranch: (branchId: string) => Promise<void>;
  onArchiveBranch: (branchId: string) => Promise<void>;
  onRestoreBranch: (branchId: string) => Promise<void>;
  onAssignAgent: (branchId: string, agentId: string) => Promise<void>;
  onUnassignAgent: (branchId: string, agentId: string) => Promise<void>;
  onGetStatistics: (branchId: string) => Promise<void>;
}

// Branch Tree Visualization Component
interface BranchTreeProps {
  branches: GitBranch[];
  selectedBranch: GitBranch | null;
  branchStatistics: Record<string, BranchStatistics>;
  onSelectBranch: (branch: GitBranch) => void;
  onBranchAction: (branchId: string, action: BranchAction) => void;
}

function BranchTree({
  branches,
  selectedBranch,
  branchStatistics,
  onSelectBranch,
  onBranchAction
}: BranchTreeProps) {
  const [expandedBranches, setExpandedBranches] = useState<Set<string>>(new Set(['main']));

  const getBranchIcon = (branch: GitBranch) => {
    if (branch.git_branch_name === 'main') return '🏠';
    if (branch.git_branch_name.startsWith('feature/')) return '🚀';
    if (branch.git_branch_name.startsWith('bugfix/')) return '🐛';
    if (branch.git_branch_name.startsWith('hotfix/')) return '🔥';
    if (branch.git_branch_name.startsWith('release/')) return '📦';
    return '🌿';
  };

  const getBranchStatusColor = (branch: GitBranch, stats?: BranchStatistics) => {
    if (!stats) return 'border-gray-300';
    if (stats.health_score >= 80) return 'border-green-500';
    if (stats.health_score >= 60) return 'border-yellow-500';
    return 'border-red-500';
  };

  return (
    <div className="space-y-2">
      {branches.map(branch => {
        const stats = branchStatistics[branch.id];
        const isSelected = selectedBranch?.id === branch.id;

        return (
          <div key={branch.id} className="space-y-1">
            <div
              className={`border-l-4 p-3 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                isSelected ? 'bg-blue-50 border-blue-500' : `bg-white ${getBranchStatusColor(branch, stats)}`
              }`}
              onClick={() => onSelectBranch(branch)}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-lg">{getBranchIcon(branch)}</span>
                  <div>
                    <div className="font-medium">{branch.git_branch_name}</div>
                    <div className="text-sm text-gray-600">{branch.git_branch_description}</div>
                  </div>
                </div>
                
                {stats && (
                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-center">
                      <div className="font-semibold">{stats.completed_tasks}/{stats.total_tasks}</div>
                      <div className="text-xs text-gray-500">Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold">{stats.progress_percentage}%</div>
                      <div className="text-xs text-gray-500">Progress</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold">{stats.assigned_agents.length}</div>
                      <div className="text-xs text-gray-500">Agents</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold">{stats.health_score}%</div>
                      <div className="text-xs text-gray-500">Health</div>
                    </div>
                  </div>
                )}
              </div>

              {stats && stats.assigned_agents.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {stats.assigned_agents.map(agentId => (
                    <span
                      key={agentId}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                    >
                      {agentId}
                    </span>
                  ))}
                </div>
              )}

              {stats && stats.blockers > 0 && (
                <div className="mt-2 text-sm text-red-600">
                  ⚠️ {stats.blockers} blocker{stats.blockers > 1 ? 's' : ''} detected
                </div>
              )}

              <div className="mt-2 flex justify-between items-center">
                <div className="text-xs text-gray-500">
                  Last activity: {stats ? new Date(stats.last_activity).toLocaleDateString() : 'Unknown'}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onBranchAction(branch.id, { type: 'statistics' });
                    }}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Stats
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onBranchAction(branch.id, { type: 'assign_agent' });
                    }}
                    className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded text-blue-800"
                  >
                    Assign Agent
                  </button>
                  {branch.git_branch_name !== 'main' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onBranchAction(branch.id, { type: 'archive' });
                      }}
                      className="px-2 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 rounded text-yellow-800"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Branch Creation Dialog Component
interface BranchCreationDialogProps {
  project: Project;
  existingBranches: GitBranch[];
  onCreateBranch: (branchData: CreateBranchData) => Promise<void>;
  onCancel: () => void;
}

function BranchCreationDialog({
  project,
  existingBranches,
  onCreateBranch,
  onCancel
}: BranchCreationDialogProps) {
  const [branchData, setBranchData] = useState<CreateBranchData>({
    git_branch_name: '',
    git_branch_description: '',
    branch_type: 'feature',
    parent_branch: 'main',
    initial_agents: [],
    template: ''
  });

  const [namePrefix, setNamePrefix] = useState('feature/');
  const [customName, setCustomName] = useState('');

  const branchTemplates = {
    feature: {
      prefix: 'feature/',
      description: 'New feature development',
      suggested_agents: ['@coding_agent', '@test_orchestrator_agent']
    },
    bugfix: {
      prefix: 'bugfix/',
      description: 'Bug fix development',
      suggested_agents: ['@debugger_agent', '@test_orchestrator_agent']
    },
    hotfix: {
      prefix: 'hotfix/',
      description: 'Critical production fix',
      suggested_agents: ['@debugger_agent', '@security_auditor_agent']
    },
    release: {
      prefix: 'release/',
      description: 'Release preparation',
      suggested_agents: ['@test_orchestrator_agent', '@devops_agent']
    },
    experiment: {
      prefix: 'experiment/',
      description: 'Experimental development',
      suggested_agents: ['@prototyping_agent']
    }
  };

  useEffect(() => {
    const template = branchTemplates[branchData.branch_type];
    setNamePrefix(template.prefix);
    setBranchData(prev => ({
      ...prev,
      git_branch_name: template.prefix + customName,
      initial_agents: template.suggested_agents
    }));
  }, [branchData.branch_type, customName]);

  const isNameValid = (name: string) => {
    if (!name || name.length < 3) return false;
    if (existingBranches.some(b => b.git_branch_name === name)) return false;
    return /^[a-z0-9-_/]+$/.test(name);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Create New Branch</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Branch Type
            </label>
            <select
              value={branchData.branch_type}
              onChange={(e) => setBranchData(prev => ({ 
                ...prev, 
                branch_type: e.target.value as any 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {Object.entries(branchTemplates).map(([type, template]) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)} - {template.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Branch Name
            </label>
            <div className="flex">
              <span className="inline-flex items-center px-3 py-2 border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm rounded-l-md">
                {namePrefix}
              </span>
              <input
                type="text"
                value={customName}
                onChange={(e) => {
                  const value = e.target.value.toLowerCase().replace(/[^a-z0-9-_]/g, '');
                  setCustomName(value);
                }}
                placeholder="branch-name"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-r-md"
              />
            </div>
            {!isNameValid(branchData.git_branch_name) && branchData.git_branch_name && (
              <div className="text-sm text-red-600 mt-1">
                Branch name must be unique, at least 3 characters, and contain only lowercase letters, numbers, hyphens, and underscores.
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={branchData.git_branch_description}
              onChange={(e) => setBranchData(prev => ({ 
                ...prev, 
                git_branch_description: e.target.value 
              }))}
              placeholder="Describe the purpose of this branch..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parent Branch
            </label>
            <select
              value={branchData.parent_branch}
              onChange={(e) => setBranchData(prev => ({ 
                ...prev, 
                parent_branch: e.target.value 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {existingBranches.map(branch => (
                <option key={branch.id} value={branch.git_branch_name}>
                  {branch.git_branch_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Initial Agents
            </label>
            <div className="space-y-2">
              {branchData.initial_agents.map((agent, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="flex-1 px-3 py-2 bg-gray-50 border rounded">{agent}</span>
                  <button
                    onClick={() => {
                      setBranchData(prev => ({
                        ...prev,
                        initial_agents: prev.initial_agents.filter((_, i) => i !== idx)
                      }));
                    }}
                    className="px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <div className="text-sm text-gray-500">
                Suggested agents based on branch type
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onCreateBranch(branchData)}
            disabled={!isNameValid(branchData.git_branch_name) || !branchData.git_branch_description}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Create Branch
          </button>
        </div>
      </div>
    </div>
  );
}

// Main GitBranchManager Component
export function GitBranchManager({
  project,
  branches,
  selectedBranch,
  onSelectBranch,
  onCreateBranch,
  onUpdateBranch,
  onDeleteBranch,
  onArchiveBranch,
  onRestoreBranch,
  onAssignAgent,
  onUnassignAgent,
  onGetStatistics
}: GitBranchManagerProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [branchStatistics, setBranchStatistics] = useState<Record<string, BranchStatistics>>({});
  const [selectedBranchStats, setSelectedBranchStats] = useState<DetailedBranchStatistics | null>(null);
  const [showStatsDialog, setShowStatsDialog] = useState(false);
  const [showAgentDialog, setShowAgentDialog] = useState(false);
  const [agentDialogBranchId, setAgentDialogBranchId] = useState<string | null>(null);
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState({
    branches: false,
    statistics: false,
    operations: false
  });

  // Load branch statistics for all branches
  useEffect(() => {
    const loadBranchStatistics = async () => {
      if (!branches.length) return;
      
      setLoading(prev => ({ ...prev, statistics: true }));
      try {
        const statsPromises = branches.map(async (branch) => {
          const stats = await mcpApi.getBranchStatistics(project.id, branch.id);
          return { branchId: branch.id, stats };
        });
        
        const results = await Promise.all(statsPromises);
        const statsMap = results.reduce((acc, { branchId, stats }) => {
          if (stats) {
            acc[branchId] = stats;
          }
          return acc;
        }, {} as Record<string, BranchStatistics>);
        
        setBranchStatistics(statsMap);
      } catch (error) {
        console.error('Failed to load branch statistics:', error);
      } finally {
        setLoading(prev => ({ ...prev, statistics: false }));
      }
    };

    loadBranchStatistics();
  }, [branches, project.id]);

  // Load available agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agents = await mcpApi.getAgents(project.id);
        setAvailableAgents(agents);
      } catch (error) {
        console.error('Failed to load agents:', error);
      }
    };

    loadAgents();
  }, [project.id]);

  const handleBranchAction = async (branchId: string, action: BranchAction) => {
    switch (action.type) {
      case 'statistics':
        await handleShowStatistics(branchId);
        break;
      case 'assign_agent':
        setAgentDialogBranchId(branchId);
        setShowAgentDialog(true);
        break;
      case 'archive':
        await onArchiveBranch(branchId);
        break;
      default:
        console.warn('Unknown action:', action.type);
    }
  };

  const handleShowStatistics = async (branchId: string) => {
    setLoading(prev => ({ ...prev, statistics: true }));
    try {
      await onGetStatistics(branchId);
      setShowStatsDialog(true);
    } catch (error) {
      console.error('Failed to get detailed statistics:', error);
    } finally {
      setLoading(prev => ({ ...prev, statistics: false }));
    }
  };

  const handleCreateBranch = async (branchData: CreateBranchData) => {
    try {
      setLoading(prev => ({ ...prev, operations: true }));
      await onCreateBranch(branchData);
      setShowCreateDialog(false);
    } catch (error) {
      console.error('Failed to create branch:', error);
    } finally {
      setLoading(prev => ({ ...prev, operations: false }));
    }
  };

  const handleAssignAgent = async (agentId: string) => {
    if (!agentDialogBranchId) return;
    
    try {
      setLoading(prev => ({ ...prev, operations: true }));
      await onAssignAgent(agentDialogBranchId, agentId);
      setShowAgentDialog(false);
      setAgentDialogBranchId(null);
    } catch (error) {
      console.error('Failed to assign agent:', error);
    } finally {
      setLoading(prev => ({ ...prev, operations: false }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">Git Branches</h2>
          <p className="text-gray-600">Manage branches and task trees for {project.name}</p>
        </div>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Create Branch
        </button>
      </div>

      {/* Loading State */}
      {loading.branches && (
        <div className="text-center py-8">
          <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
          <div className="mt-2 text-gray-600">Loading branches...</div>
        </div>
      )}

      {/* Branch Tree */}
      {!loading.branches && branches.length > 0 && (
        <BranchTree
          branches={branches}
          selectedBranch={selectedBranch}
          branchStatistics={branchStatistics}
          onSelectBranch={onSelectBranch}
          onBranchAction={handleBranchAction}
        />
      )}

      {/* Empty State */}
      {!loading.branches && branches.length === 0 && (
        <div className="text-center py-12 border rounded-lg bg-gray-50">
          <div className="text-gray-500 mb-4">No branches found</div>
          <button
            onClick={() => setShowCreateDialog(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Create First Branch
          </button>
        </div>
      )}

      {/* Branch Creation Dialog */}
      {showCreateDialog && (
        <BranchCreationDialog
          project={project}
          existingBranches={branches}
          onCreateBranch={handleCreateBranch}
          onCancel={() => setShowCreateDialog(false)}
        />
      )}

      {/* Agent Assignment Dialog */}
      {showAgentDialog && agentDialogBranchId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Assign Agent to Branch</h3>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {availableAgents.map(agent => (
                <div
                  key={agent.id}
                  className="border rounded-lg p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => handleAssignAgent(agent.id)}
                >
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-sm text-gray-600">Status: {agent.status}</div>
                  {agent.call_agent && (
                    <div className="text-xs text-gray-500 mt-1">
                      Type: {agent.call_agent}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {availableAgents.length === 0 && (
              <div className="text-center py-4 text-gray-500">
                No available agents found
              </div>
            )}

            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => {
                  setShowAgentDialog(false);
                  setAgentDialogBranchId(null);
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Panel */}
      {selectedBranch && (
        <div className="border rounded-lg p-4 bg-white">
          <h3 className="font-medium mb-2">
            Branch Details: {selectedBranch.git_branch_name}
          </h3>
          <p className="text-gray-600 mb-4">{selectedBranch.git_branch_description}</p>
          
          {branchStatistics[selectedBranch.id] && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-green-600">
                  {branchStatistics[selectedBranch.id].progress_percentage}%
                </div>
                <div className="text-sm text-gray-500">Progress</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-blue-600">
                  {branchStatistics[selectedBranch.id].completed_tasks}/{branchStatistics[selectedBranch.id].total_tasks}
                </div>
                <div className="text-sm text-gray-500">Tasks</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-purple-600">
                  {branchStatistics[selectedBranch.id].assigned_agents.length}
                </div>
                <div className="text-sm text-gray-500">Agents</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-orange-600">
                  {branchStatistics[selectedBranch.id].health_score}%
                </div>
                <div className="text-sm text-gray-500">Health</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default GitBranchManager;