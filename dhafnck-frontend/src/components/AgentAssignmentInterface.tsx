/**
 * Agent Assignment Interface Component
 * Provides detailed agent assignment and management for git branches
 */

import React, { useState, useEffect } from 'react';
import { mcpApi, Agent } from '../api/enhanced';
import { GitBranch, AgentAssignment } from './GitBranchManager';

interface AgentAssignmentProps {
  branch: GitBranch;
  availableAgents: Agent[];
  currentAssignments: AgentAssignment[];
  onAssignAgent: (agentId: string) => Promise<void>;
  onUnassignAgent: (agentId: string) => Promise<void>;
  onUpdateAssignment: (agentId: string, updates: Partial<AgentAssignment>) => Promise<void>;
}

export function AgentAssignmentInterface({
  branch,
  availableAgents,
  currentAssignments,
  onAssignAgent,
  onUnassignAgent,
  onUpdateAssignment
}: AgentAssignmentProps) {
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [editingAssignment, setEditingAssignment] = useState<string | null>(null);
  const [assignmentUpdates, setAssignmentUpdates] = useState<Partial<AgentAssignment>>({});

  const unassignedAgents = availableAgents.filter(
    agent => !currentAssignments.some(assignment => assignment.agent_id === agent.id)
  );

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'primary': return 'bg-blue-100 text-blue-800';
      case 'secondary': return 'bg-green-100 text-green-800';
      case 'reviewer': return 'bg-purple-100 text-purple-800';
      case 'consultant': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAgentTypeIcon = (agent: Agent) => {
    if (!agent.call_agent) return '🤖';
    if (agent.call_agent.includes('debugger')) return '🐛';
    if (agent.call_agent.includes('test')) return '🧪';
    if (agent.call_agent.includes('security')) return '🔒';
    if (agent.call_agent.includes('ui')) return '🎨';
    if (agent.call_agent.includes('coding')) return '💻';
    return '🤖';
  };

  const handleAssignAgent = async (agent: Agent, role: string = 'secondary') => {
    try {
      await onAssignAgent(agent.id);
      setShowAssignDialog(false);
      setSelectedAgent(null);
    } catch (error) {
      console.error('Failed to assign agent:', error);
    }
  };

  const handleUpdateAssignment = async (agentId: string) => {
    try {
      await onUpdateAssignment(agentId, assignmentUpdates);
      setEditingAssignment(null);
      setAssignmentUpdates({});
    } catch (error) {
      console.error('Failed to update assignment:', error);
    }
  };

  const startEditingAssignment = (assignment: AgentAssignment) => {
    setEditingAssignment(assignment.agent_id);
    setAssignmentUpdates({
      role: assignment.role,
      workload_percentage: assignment.workload_percentage
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="font-medium">Agent Assignments for {branch.git_branch_name}</h4>
        <button
          onClick={() => setShowAssignDialog(true)}
          disabled={unassignedAgents.length === 0}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Assign Agent
        </button>
      </div>

      {/* Current Assignments */}
      <div className="space-y-3">
        {currentAssignments.map(assignment => (
          <div key={assignment.agent_id} className="border rounded-lg p-3 bg-white">
            {editingAssignment === assignment.agent_id ? (
              // Edit Mode
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getAgentTypeIcon(availableAgents.find(a => a.id === assignment.agent_id) || {} as Agent)}</span>
                    <div className="font-medium">{assignment.agent_name}</div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleUpdateAssignment(assignment.agent_id)}
                      className="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-800"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setEditingAssignment(null);
                        setAssignmentUpdates({});
                      }}
                      className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      Cancel
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Role</label>
                    <select
                      value={assignmentUpdates.role || assignment.role}
                      onChange={(e) => setAssignmentUpdates(prev => ({ ...prev, role: e.target.value as any }))}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
                    >
                      <option value="primary">Primary</option>
                      <option value="secondary">Secondary</option>
                      <option value="reviewer">Reviewer</option>
                      <option value="consultant">Consultant</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Workload %</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={assignmentUpdates.workload_percentage || assignment.workload_percentage}
                      onChange={(e) => setAssignmentUpdates(prev => ({ 
                        ...prev, 
                        workload_percentage: parseInt(e.target.value) 
                      }))}
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
                    />
                  </div>
                </div>
              </div>
            ) : (
              // View Mode
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{getAgentTypeIcon(availableAgents.find(a => a.id === assignment.agent_id) || {} as Agent)}</span>
                    <div className="font-medium">{assignment.agent_name}</div>
                  </div>
                  <div className="flex gap-2 mt-1">
                    <span className={`px-2 py-1 text-xs rounded ${getRoleColor(assignment.role)}`}>
                      {assignment.role}
                    </span>
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                      {assignment.workload_percentage}% workload
                    </span>
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                      {availableAgents.find(a => a.id === assignment.agent_id)?.status || 'unknown'}
                    </span>
                  </div>
                  {assignment.specialization.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      Skills: {assignment.specialization.join(', ')}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 mt-1">
                    Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => startEditingAssignment(assignment)}
                    className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onUnassignAgent(assignment.agent_id)}
                    className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded text-red-800"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {currentAssignments.length === 0 && (
        <div className="text-center py-6 text-gray-500 border rounded-lg bg-gray-50">
          No agents assigned to this branch
        </div>
      )}

      {/* Assignment Dialog */}
      {showAssignDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Assign Agent to Branch</h3>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {unassignedAgents.map(agent => {
                const isSelected = selectedAgent?.id === agent.id;
                return (
                  <div
                    key={agent.id}
                    className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                      isSelected ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{getAgentTypeIcon(agent)}</span>
                      <div className="font-medium">{agent.name}</div>
                      <span className={`px-2 py-1 text-xs rounded ${
                        agent.status === 'active' ? 'bg-green-100 text-green-800' :
                        agent.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        agent.status === 'idle' ? 'bg-gray-100 text-gray-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                    {agent.call_agent && (
                      <div className="text-xs text-gray-500 mt-1">
                        Type: {agent.call_agent}
                      </div>
                    )}
                    {(agent as any).specialization?.length > 0 && (
                      <div className="text-xs text-gray-500 mt-1">
                        Skills: {(agent as any).specialization.join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {unassignedAgents.length === 0 && (
              <div className="text-center py-4 text-gray-500">
                All available agents are already assigned
              </div>
            )}

            {/* Role Selection for Assignment */}
            {selectedAgent && (
              <div className="mt-4 p-3 bg-blue-50 rounded">
                <div className="text-sm font-medium mb-2">Assign as:</div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleAssignAgent(selectedAgent, 'primary')}
                    className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded text-blue-800"
                  >
                    Primary Agent
                  </button>
                  <button
                    onClick={() => handleAssignAgent(selectedAgent, 'secondary')}
                    className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 rounded text-green-800"
                  >
                    Secondary Agent
                  </button>
                  <button
                    onClick={() => handleAssignAgent(selectedAgent, 'reviewer')}
                    className="px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 rounded text-purple-800"
                  >
                    Reviewer
                  </button>
                  <button
                    onClick={() => handleAssignAgent(selectedAgent, 'consultant')}
                    className="px-3 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 rounded text-yellow-800"
                  >
                    Consultant
                  </button>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => {
                  setShowAssignDialog(false);
                  setSelectedAgent(null);
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assignment Summary */}
      {currentAssignments.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm font-medium mb-2">Assignment Summary</div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <div className="text-gray-600">Total Agents</div>
              <div className="font-semibold">{currentAssignments.length}</div>
            </div>
            <div>
              <div className="text-gray-600">Total Workload</div>
              <div className="font-semibold">
                {currentAssignments.reduce((sum, a) => sum + a.workload_percentage, 0)}%
              </div>
            </div>
            <div>
              <div className="text-gray-600">Primary Agents</div>
              <div className="font-semibold">
                {currentAssignments.filter(a => a.role === 'primary').length}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Active Agents</div>
              <div className="font-semibold">
                {currentAssignments.filter(a => 
                  availableAgents.find(agent => agent.id === a.agent_id)?.status === 'active'
                ).length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentAssignmentInterface;