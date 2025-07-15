/**
 * Git Branch Manager Wrapper Component
 * Demonstrates full integration with the existing project dashboard
 */

import React, { useState } from 'react';
import { GitBranchManager } from './GitBranchManager';
import { AgentAssignmentInterface } from './AgentAssignmentInterface';
import { BranchStatisticsDashboard } from './BranchStatisticsDashboard';
import useGitBranchManager from '../hooks/useGitBranchManager';

interface GitBranchManagerWrapperProps {
  projectId: string;
  projectName?: string;
  onBack?: () => void;
}

export function GitBranchManagerWrapper({ 
  projectId, 
  projectName = 'Project',
  onBack 
}: GitBranchManagerWrapperProps) {
  const [showAgentInterface, setShowAgentInterface] = useState(false);
  const [showStatsDashboard, setShowStatsDashboard] = useState(false);
  const [selectedBranchForAgents, setSelectedBranchForAgents] = useState<string | null>(null);
  const [selectedBranchForStats, setSelectedBranchForStats] = useState<string | null>(null);

  const {
    state,
    actions,
    computed
  } = useGitBranchManager(projectId);

  const handleCreateBranch = async (branchData: any) => {
    await actions.createBranch(branchData);
  };

  const handleUpdateBranch = async (branchId: string, updates: any) => {
    await actions.updateBranch(branchId, updates);
  };

  const handleDeleteBranch = async (branchId: string) => {
    await actions.deleteBranch(branchId);
  };

  const handleArchiveBranch = async (branchId: string) => {
    await actions.archiveBranch(branchId);
  };

  const handleRestoreBranch = async (branchId: string) => {
    await actions.restoreBranch(branchId);
  };

  const handleAssignAgent = async (branchId: string, agentId: string) => {
    await actions.assignAgent(branchId, agentId);
  };

  const handleUnassignAgent = async (branchId: string, agentId: string) => {
    await actions.unassignAgent(branchId, agentId);
  };

  const handleGetStatistics = async (branchId: string) => {
    await actions.getStatistics(branchId);
    setSelectedBranchForStats(branchId);
    setShowStatsDashboard(true);
  };

  const handleShowAgentInterface = (branchId: string) => {
    setSelectedBranchForAgents(branchId);
    setShowAgentInterface(true);
  };

  const handleUpdateAgentAssignment = async (agentId: string, updates: any) => {
    // This would typically call an API to update the assignment
    console.log('Update agent assignment:', agentId, updates);
  };

  const project = {
    id: projectId,
    name: projectName,
    description: `Git branches for ${projectName}`,
    created_at: new Date().toISOString(),
    status: 'active'
  };

  if (state.error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800 mb-2">
            <span>⚠️</span>
            <h3 className="font-medium">Error Loading Git Branches</h3>
          </div>
          <p className="text-red-700 text-sm">{state.error}</p>
          <div className="mt-3 flex gap-2">
            <button
              onClick={actions.clearError}
              className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded hover:bg-red-200"
            >
              Dismiss
            </button>
            <button
              onClick={actions.refreshAll}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            {onBack && (
              <button
                onClick={onBack}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                ← Back
              </button>
            )}
            <h1 className="text-2xl font-bold">Git Branch Management</h1>
          </div>
          <p className="text-gray-600 mt-1">{projectName}</p>
        </div>
        
        {/* Summary Cards */}
        <div className="flex gap-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">{computed.totalBranches}</div>
            <div className="text-xs text-gray-500">Total Branches</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">{computed.activeBranches}</div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">{computed.totalAgents}</div>
            <div className="text-xs text-gray-500">Total Agents</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-orange-600">{computed.assignedAgents}</div>
            <div className="text-xs text-gray-500">Assigned</div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {computed.isLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-800">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
            <span>Loading branch data...</span>
          </div>
        </div>
      )}

      {/* Main Git Branch Manager */}
      <GitBranchManager
        project={project}
        branches={state.branches}
        selectedBranch={state.selectedBranch}
        onSelectBranch={actions.selectBranch}
        onCreateBranch={handleCreateBranch}
        onUpdateBranch={handleUpdateBranch}
        onDeleteBranch={handleDeleteBranch}
        onArchiveBranch={handleArchiveBranch}
        onRestoreBranch={handleRestoreBranch}
        onAssignAgent={handleAssignAgent}
        onUnassignAgent={handleUnassignAgent}
        onGetStatistics={handleGetStatistics}
      />

      {/* Action Buttons for Selected Branch */}
      {state.selectedBranch && (
        <div className="bg-gray-50 border rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium">Branch Actions</h3>
              <p className="text-sm text-gray-600">
                Actions for {state.selectedBranch.git_branch_name}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleShowAgentInterface(state.selectedBranch!.id)}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
              >
                Manage Agents
              </button>
              <button
                onClick={() => handleGetStatistics(state.selectedBranch!.id)}
                className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded hover:bg-green-200"
              >
                View Statistics
              </button>
              <button
                onClick={actions.refreshAll}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
              >
                Refresh All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agent Assignment Interface Modal */}
      {showAgentInterface && selectedBranchForAgents && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Agent Management</h3>
              <button
                onClick={() => {
                  setShowAgentInterface(false);
                  setSelectedBranchForAgents(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <AgentAssignmentInterface
              branch={state.branches.find(b => b.id === selectedBranchForAgents)!}
              availableAgents={state.availableAgents}
              currentAssignments={state.agentAssignments[selectedBranchForAgents] || []}
              onAssignAgent={(agentId) => handleAssignAgent(selectedBranchForAgents, agentId)}
              onUnassignAgent={(agentId) => handleUnassignAgent(selectedBranchForAgents, agentId)}
              onUpdateAssignment={handleUpdateAgentAssignment}
            />
          </div>
        </div>
      )}

      {/* Statistics Dashboard Modal */}
      {showStatsDashboard && selectedBranchForStats && state.detailedStatistics[selectedBranchForStats] && (
        <BranchStatisticsDashboard
          branch={state.branches.find(b => b.id === selectedBranchForStats)!}
          statistics={state.detailedStatistics[selectedBranchForStats]}
          onRefreshStatistics={() => handleGetStatistics(selectedBranchForStats)}
          onClose={() => {
            setShowStatsDashboard(false);
            setSelectedBranchForStats(null);
          }}
        />
      )}
    </div>
  );
}

export default GitBranchManagerWrapper;