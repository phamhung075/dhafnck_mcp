/**
 * ContextManagementDemo Component
 * Integration example showing how all context management components work together
 */

import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { useContextManagement } from '../hooks/useContextManagement';

// Import all the context management components
import { ContextDetailsPanel } from './ContextDetailsPanel';
import { ContextDelegationWorkflow } from './ContextDelegationWorkflow';
import { DelegationQueueViewer } from './DelegationQueueViewer';
import { ContextInheritanceDebugger } from './ContextInheritanceDebugger';

// Import types
import {
  HierarchicalContext,
  DelegationPattern,
  DelegationTarget
} from '../types/context-delegation';

interface ContextManagementDemoProps {
  projectId?: string;
  taskId?: string;
}

export function ContextManagementDemo({
  projectId = 'demo-project-1',
  taskId = 'demo-task-1'
}: ContextManagementDemoProps) {
  const [activeView, setActiveView] = useState<'details' | 'delegation' | 'queue' | 'debugger'>('details');
  const [selectedContext, setSelectedContext] = useState<HierarchicalContext | null>(null);

  // Use the context management hook
  const { state, actions } = useContextManagement(projectId, taskId, {
    autoRefresh: true,
    refreshInterval: 30000
  });

  // Mock data for demonstration
  const mockContext: HierarchicalContext = {
    context_id: taskId,
    level: 'task',
    data: {
      title: 'Implement User Authentication',
      description: 'Add JWT-based authentication with login, logout, and session management',
      status: 'in_progress',
      priority: 'high',
      assignees: ['john.doe', 'jane.smith'],
      labels: ['authentication', 'security', 'backend'],
      estimated_effort: '3 days',
      due_date: '2024-01-15',
      next_steps: [
        'Design authentication flow',
        'Implement JWT token handling',
        'Add password validation',
        'Create login UI components',
        'Write integration tests'
      ]
    },
    metadata: {
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-10T10:30:00Z',
      user_id: 'user-123',
      project_id: projectId,
      git_branch_name: 'feature/auth',
      version: 1
    }
  };

  const mockInheritanceChain = [
    {
      level: 'global' as const,
      context_id: 'global_singleton',
      data: {
        title: 'Global Configuration',
        coding_standards: 'ESLint + Prettier',
        security_requirements: 'OWASP Top 10 compliance'
      },
      effective_properties: ['coding_standards', 'security_requirements'],
      overridden_properties: []
    },
    {
      level: 'project' as const,
      context_id: projectId,
      data: {
        title: 'Authentication Service',
        description: 'Microservice for user authentication',
        tech_stack: 'Node.js + Express + JWT',
        database: 'PostgreSQL'
      },
      effective_properties: ['tech_stack', 'database'],
      overridden_properties: []
    },
    {
      level: 'task' as const,
      context_id: taskId,
      data: mockContext.data,
      effective_properties: ['title', 'description', 'status', 'priority'],
      overridden_properties: []
    }
  ];

  const mockAvailablePatterns: DelegationPattern[] = [
    {
      type: 'reusable_component',
      name: 'JWT Authentication Pattern',
      description: 'Reusable JWT authentication implementation',
      required_fields: ['implementation', 'usage_guide'],
      optional_fields: ['tags', 'category']
    },
    {
      type: 'best_practice',
      name: 'Security Best Practice',
      description: 'Security implementation guidelines',
      required_fields: ['implementation', 'usage_guide'],
      optional_fields: ['tags', 'category']
    },
    {
      type: 'configuration',
      name: 'Authentication Configuration',
      description: 'Standard auth configuration pattern',
      required_fields: ['implementation', 'usage_guide'],
      optional_fields: ['tags', 'category']
    }
  ];

  const mockAvailableTargets: DelegationTarget[] = [
    {
      level: 'project',
      context_id: projectId,
      display_name: 'Authentication Service Project',
      description: 'Share with all tasks in this project',
      permissions: ['read', 'write']
    },
    {
      level: 'global',
      context_id: 'global_singleton',
      display_name: 'Global Organization Context',
      description: 'Share across all projects in organization',
      permissions: ['read', 'write']
    }
  ];

  // Override the state with our mock data for demo purposes
  const demoState = {
    ...state,
    selectedContext: selectedContext || mockContext,
    inheritanceChain: mockInheritanceChain,
    availablePatterns: mockAvailablePatterns,
    availableTargets: mockAvailableTargets
  };

  const views = [
    {
      id: 'details' as const,
      label: 'Context Details',
      icon: '📊',
      description: 'View and edit context information'
    },
    {
      id: 'delegation' as const,
      label: 'Delegation Workflow',
      icon: '🔄',
      description: 'Delegate patterns to higher levels'
    },
    {
      id: 'queue' as const,
      label: 'Delegation Queue',
      icon: '📋',
      description: 'Manage pending delegations'
    },
    {
      id: 'debugger' as const,
      label: 'Inheritance Debugger',
      icon: '🔍',
      description: 'Debug inheritance chain'
    }
  ];

  const renderActiveView = () => {
    switch (activeView) {
      case 'details':
        return (
          <ContextDetailsPanel
            context={demoState.selectedContext}
            resolvedContext={demoState.resolvedContext}
            inheritanceChain={demoState.inheritanceChain}
            onUpdateContext={actions.updateContext}
            onAddInsight={actions.addInsight}
            onAddProgress={actions.addProgress}
            onUpdateNextSteps={actions.updateNextSteps}
            onForceRefresh={() => actions.refreshContext(taskId)}
          />
        );

      case 'delegation':
        return (
          <ContextDelegationWorkflow
            sourceContext={demoState.selectedContext!}
            availableTargets={demoState.availableTargets}
            onDelegate={actions.delegateContext}
            onPreviewDelegation={actions.previewDelegation}
            delegationHistory={demoState.delegationHistory}
            availablePatterns={demoState.availablePatterns}
          />
        );

      case 'queue':
        return (
          <DelegationQueueViewer
            pendingDelegations={demoState.delegationQueue}
            onApproveDelegation={actions.approveDelegation}
            onRejectDelegation={actions.rejectDelegation}
            onViewDelegationDetails={(id: string) => console.log('View delegation:', id)}
            userRole="admin"
            queueStats={{
              total_pending: demoState.delegationQueue.length,
              average_approval_time: 2.5,
              rejection_rate: 0.15
            }}
          />
        );

      case 'debugger':
        return (
          <ContextInheritanceDebugger
            contextId={taskId}
            level="task"
            validationResult={demoState.validationResults[taskId] || null}
            onValidate={actions.validateInheritance}
            onRepairInheritance={actions.repairInheritance}
            onOptimizePerformance={actions.optimizePerformance}
            onClearCache={actions.clearCache}
          />
        );

      default:
        return <div>Unknown view: {activeView}</div>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Context Management System</h1>
            <p className="text-gray-600 mt-2">
              Complete context details panel and delegation workflow demonstration
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="outline">Project: {projectId}</Badge>
            <Badge variant="outline">Task: {taskId}</Badge>
          </div>
        </div>

        {/* System Status */}
        <Separator className="my-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Context Status</span>
            <p className="font-medium">
              {demoState.loading.context ? 'Loading...' : 'Ready'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Delegations</span>
            <p className="font-medium">{demoState.delegationQueue.length} pending</p>
          </div>
          <div>
            <span className="text-gray-500">Insights</span>
            <p className="font-medium">
              {Object.values(demoState.insights).flat().length} total
            </p>
          </div>
          <div>
            <span className="text-gray-500">Inheritance</span>
            <p className="font-medium">{demoState.inheritanceChain.length} levels</p>
          </div>
        </div>
      </Card>

      {/* Navigation */}
      <Card className="p-4">
        <div className="flex space-x-2 overflow-x-auto">
          {views.map(view => (
            <Button
              key={view.id}
              variant={activeView === view.id ? 'default' : 'outline'}
              onClick={() => setActiveView(view.id)}
              className="whitespace-nowrap"
            >
              <span className="mr-2">{view.icon}</span>
              {view.label}
            </Button>
          ))}
        </div>
        
        <p className="text-sm text-gray-600 mt-2">
          {views.find(v => v.id === activeView)?.description}
        </p>
      </Card>

      {/* Loading States */}
      {Object.values(demoState.loading).some(Boolean) && (
        <Card className="p-4">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">
              Loading {Object.entries(demoState.loading)
                .filter(([, loading]) => loading)
                .map(([operation]) => operation)
                .join(', ')}...
            </span>
          </div>
        </Card>
      )}

      {/* Error Display */}
      {Object.values(demoState.errors).some(Boolean) && (
        <Card className="p-4 bg-red-50 border-red-200">
          <h3 className="font-medium text-red-800 mb-2">Errors</h3>
          <div className="space-y-1">
            {Object.entries(demoState.errors)
              .filter(([, error]) => error)
              .map(([operation, error]) => (
                <p key={operation} className="text-sm text-red-600">
                  {operation}: {error}
                </p>
              ))}
          </div>
        </Card>
      )}

      {/* Main Content */}
      <div className="min-h-96">
        {renderActiveView()}
      </div>

      {/* Integration Notes */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h3 className="font-medium text-blue-800 mb-3">Integration Notes</h3>
        <div className="text-sm text-blue-700 space-y-2">
          <p>
            This demo shows the complete context management system from Prompt 3B:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><strong>ContextDetailsPanel:</strong> Tabbed interface with Overview, Data, Inheritance, Insights, Progress, and Next Steps</li>
            <li><strong>ContextDelegationWorkflow:</strong> Step-by-step wizard for delegating patterns to higher levels</li>
            <li><strong>DelegationQueueViewer:</strong> Admin interface for approving/rejecting delegations</li>
            <li><strong>ContextInheritanceDebugger:</strong> Performance monitoring and validation tools</li>
            <li><strong>useContextManagement:</strong> Centralized state management with API integration</li>
          </ul>
          <p className="mt-3">
            All components are fully integrated with the enhanced MCP API and provide a complete
            context management solution for hierarchical project organization.
          </p>
        </div>
      </Card>
    </div>
  );
}