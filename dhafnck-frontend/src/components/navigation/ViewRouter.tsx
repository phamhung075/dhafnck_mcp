import { useCallback, useMemo, useState } from 'react';
import { useAppSelector, useAppDispatch, sessionActions } from '../../store/store';
import { Project as ApiProject, mcpApi } from '../../api/enhanced';
import { AgentManagement } from '../AgentManagement';
import { ComplianceDashboard } from '../ComplianceDashboard';
import { ConnectionMonitor } from '../ConnectionMonitor';
import { ContextTree } from '../ContextTree';
import { GitBranchManager } from '../GitBranchManager';
import { ProjectDashboard } from '../ProjectDashboard';
import ProjectList from '../ProjectList';
import { SystemHealthDashboard } from '../SystemHealthDashboard';
import TaskList from '../TaskList';
import { TaskDetailView } from '../TaskDetailView';

export function ViewRouter() {
  const { currentView } = useAppSelector(state => state.ui);
  const { projects } = useAppSelector(state => state.data);
  const { selectedProject } = useAppSelector(state => state.session);
  const { health, compliance, connection } = useAppSelector(state => state.system);

  // Memoize projects array to prevent unnecessary re-renders
  const memoizedProjects = useMemo(() => projects || [], [projects]);

  // Placeholder functions for ProjectDashboard - wrapped in useCallback to prevent re-renders
  const handleSelectProject = useCallback((project: any) => {
    console.log('Select project:', project);
  }, []);

  const handleCreateProject = useCallback(async (projectData: any) => {
    console.log('Create project:', projectData);
  }, []);

  const handleUpdateProject = useCallback(async (projectId: string, updates: any) => {
    console.log('Update project:', projectId, updates);
  }, []);

  const handleDeleteProject = useCallback(async (projectId: string) => {
    console.log('Delete project:', projectId);
  }, []);

  const handleRunHealthCheck = useCallback(async (projectId: string) => {
    console.log('Health check:', projectId);
  }, []);

  const handleCleanupProject = useCallback(async (projectId: string) => {
    console.log('Cleanup project:', projectId);
  }, []);

  const handleRebalanceAgents = useCallback(async (projectId: string) => {
    console.log('Rebalance agents:', projectId);
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView />;
      
      case 'projects':
        return <ProjectDashboard 
          projects={memoizedProjects}
          selectedProject={selectedProject}
          onSelectProject={handleSelectProject}
          onCreateProject={handleCreateProject}
          onUpdateProject={handleUpdateProject}
          onDeleteProject={handleDeleteProject}
          onRunHealthCheck={handleRunHealthCheck}
          onCleanupProject={handleCleanupProject}
          onRebalanceAgents={handleRebalanceAgents}
        />;
      
      case 'agents':
        return <AgentManagement 
          project={selectedProject as any || { id: '', name: 'Default', description: '', created_at: '', updated_at: '' }}
          branches={[]}
          agents={[]}
          onAssignAgent={() => Promise.resolve()}
          onUnassignAgent={() => Promise.resolve()}
          onRegisterAgent={() => Promise.resolve()}
          onUnregisterAgent={() => Promise.resolve()}
        />;
      
      case 'contexts':
        return <ContextTree 
          contexts={[]}
          selectedContext={null}
          onContextSelect={() => {}}
          onResolveContext={() => Promise.resolve()}
          onDelegate={() => Promise.resolve()}
          onValidateInheritance={() => Promise.resolve()}
        />;
      
      case 'health':
        return <SystemHealthDashboard 
          connectionStatus={{ 
            ...connection, 
            response_time: 100, 
            status: connection.status === 'unknown' ? 'healthy' : 
                   connection.status === 'critical' ? 'down' : 
                   connection.status as 'healthy' | 'degraded' | 'down'
          }}
          complianceStatus={{
            compliance_score: compliance?.compliance_rate || 0,
            violations: [],
            timestamp: new Date().toISOString(),
            audit_trail: []
          } as any}
          performanceMetrics={{ 
            averageResponseTime: 100, 
            requestCount: 0, 
            successCount: 0, 
            errorCount: 0, 
            queueLength: 0,
            frontend: { 
              page_load_time: 0, 
              first_contentful_paint: 0, 
              largest_contentful_paint: 0, 
              cumulative_layout_shift: 0 
            },
            api: { 
              avg_response_time: 0, 
              p95_response_time: 0, 
              error_rate: 0, 
              success_rate: 100 
            },
            system: { 
              memory_usage: 0, 
              cache_hit_ratio: 100, 
              active_connections: 0 
            }
          }}
          alerts={[]}
          onRefreshHealth={() => Promise.resolve()}
          onRunDiagnostics={() => Promise.resolve()}
          onResolveAlert={() => Promise.resolve()}
          refreshInterval={30000}
        />;
      
      case 'compliance':
        if (!compliance) {
          return <div>Loading compliance data...</div>;
        }
        return <ComplianceDashboard 
          complianceStatus={compliance as any}
          violations={[]}
          auditTrail={[]}
          onRunAudit={() => Promise.resolve()}
          onResolveViolation={() => Promise.resolve()}
          onExportAuditReport={() => Promise.resolve()}
          onUpdateCompliancePolicy={() => Promise.resolve()}
        />;
      
      case 'connections':
        return <ConnectionMonitor 
          connectionStatus={connection as any}
          connectionHistory={[]}
          serverCapabilities={{ features: [], version: '1.0' } as any}
          onTestConnection={() => Promise.resolve()}
          onRestartConnection={() => Promise.resolve()}
          onUpdateConnectionSettings={() => Promise.resolve()}
          onRegisterForUpdates={() => Promise.resolve()}
        />;
      
      case 'monitoring':
        return <MonitoringView connection={connection} compliance={compliance} />;
      
      case 'tasks':
        return <TaskManagementView />;
      
      case 'rules':
        return <RuleManagementView />;
      
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="h-full">
      {renderView()}
    </div>
  );
}

// Main Dashboard combining multiple views
function DashboardView() {
  const { selectedProject } = useAppSelector(state => state.session);
  const { health, compliance, connection } = useAppSelector(state => state.system);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of system status and recent activity
        </p>
      </div>

      {/* Quick Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">System Health</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {health?.overall_score || 0}%
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              (health?.overall_score || 0) >= 80 ? 'bg-green-100 text-green-600' :
              (health?.overall_score || 0) >= 50 ? 'bg-yellow-100 text-yellow-600' :
              'bg-red-100 text-red-600'
            }`}>
              🏥
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Compliance Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {compliance ? `${(compliance.compliance_rate * 100).toFixed(1)}%` : '0%'}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              (compliance?.compliance_rate || 0) >= 0.9 ? 'bg-green-100 text-green-600' :
              (compliance?.compliance_rate || 0) >= 0.7 ? 'bg-yellow-100 text-yellow-600' :
              'bg-red-100 text-red-600'
            }`}>
              🛡️
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Connection</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                {connection.status}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              connection.status === 'healthy' ? 'bg-green-100 text-green-600' :
              connection.status === 'degraded' ? 'bg-yellow-100 text-yellow-600' :
              'bg-red-100 text-red-600'
            }`}>
              🔗
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health Panel */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              System Health
            </h2>
          </div>
          <div className="p-6">
            <SystemHealthDashboard 
              connectionStatus={connection as any}
              complianceStatus={compliance as any}
              performanceMetrics={{ averageResponseTime: 100, requestCount: 0 } as any}
              alerts={[]}
              onRefreshHealth={() => Promise.resolve()}
              onRunDiagnostics={() => Promise.resolve()}
              onResolveAlert={() => Promise.resolve()}
              refreshInterval={30000}
            />
          </div>
        </div>

        {/* Project Overview */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Project Overview
            </h2>
          </div>
          <div className="p-6">
            {selectedProject ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <p>Project: {selectedProject.name}</p>
                <p className="text-sm mt-2">Project dashboard details would be displayed here</p>
              </div>
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                <p>No project selected</p>
                <p className="text-sm mt-2">Select a project to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// System Monitoring aggregated view
function MonitoringView({ connection, compliance }: { connection: any; compliance: any }) {
  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          System Monitoring
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Comprehensive system health and performance monitoring
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <SystemHealthDashboard 
            connectionStatus={connection as any}
            complianceStatus={compliance as any}
            performanceMetrics={{ averageResponseTime: 100, requestCount: 0 } as any}
            alerts={[]}
            onRefreshHealth={() => Promise.resolve()}
            onRunDiagnostics={() => Promise.resolve()}
            onResolveAlert={() => Promise.resolve()}
            refreshInterval={30000}
          />
        </div>
        <div className="space-y-6">
          <ComplianceDashboard 
            complianceStatus={compliance as any}
            violations={[]}
            auditTrail={[]}
            onRunAudit={() => Promise.resolve()}
            onResolveViolation={() => Promise.resolve()}
            onExportAuditReport={() => Promise.resolve()}
            onUpdateCompliancePolicy={() => Promise.resolve()}
          />
          <ConnectionMonitor 
            connectionStatus={connection as any}
            connectionHistory={[]}
            serverCapabilities={{ features: [], version: '1.0' } as any}
            onTestConnection={() => Promise.resolve()}
            onRestartConnection={() => Promise.resolve()}
            onUpdateConnectionSettings={() => Promise.resolve()}
            onRegisterForUpdates={() => Promise.resolve()}
          />
        </div>
      </div>
    </div>
  );
}

// Task Management view placeholder
function TaskManagementView() {
  const { selectedProject, selectedBranch } = useAppSelector(state => state.session);
  const { projects } = useAppSelector(state => state.data);
  const dispatch = useAppDispatch();
  const [selectedTask, setSelectedTask] = useState<any>(null);

  // Handle project/branch selection from ProjectList
  const handleProjectBranchSelect = useCallback(async (projectId: string, branchId?: string) => {
    // Fetch the full project details from API since ProjectList manages its own data
    try {
      const response = await mcpApi.manageProject('get', { project_id: projectId });
      if (response.success && response.data) {
        const project = response.data;
        dispatch(sessionActions.setSelectedProject(project));
        
        if (branchId) {
          // Fetch branches for this project
          const branchResponse = await mcpApi.manageGitBranch('list', { project_id: projectId });
          if (branchResponse.success && branchResponse.data) {
            const branch = branchResponse.data.find((b: any) => b.id === branchId);
            if (branch) {
              dispatch(sessionActions.setSelectedBranch(branch));
            }
          }
        }
      }
    } catch (error) {
      console.error('Error selecting project/branch:', error);
    }
  }, [dispatch]);

  // Handle task selection
  const handleTaskSelect = useCallback((task: any) => {
    setSelectedTask(task);
  }, []);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Task Management
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Manage tasks and workflows across projects and branches
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Project/Branch Selection - Left Panel */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Projects & Branches
              </h2>
            </div>
            <div className="p-4">
              <ProjectList 
                onSelect={handleProjectBranchSelect}
              />
            </div>
          </div>
        </div>

        {/* Task List - Middle Panel */}
        <div className="lg:col-span-5">
          {selectedBranch ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Tasks
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {selectedProject?.name} / {selectedBranch.git_branch_name}
                </p>
              </div>
              <div className="p-4">
                <TaskList 
                  projectId={selectedProject!.id}
                  taskTreeId={selectedBranch.id}
                  onTaskSelect={handleTaskSelect}
                  selectedTaskId={selectedTask?.id}
                />
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 text-center">
              <div className="text-gray-500 dark:text-gray-400 py-8">
                <div className="text-4xl mb-4">📋</div>
                <p className="text-lg font-medium mb-2">Select a branch to view tasks</p>
                <p className="text-sm">Choose a project and branch from the left panel</p>
              </div>
            </div>
          )}
        </div>

        {/* Task Details/Subtasks - Right Panel */}
        <div className="lg:col-span-4">
          {selectedTask ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Task Details
                </h2>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
              <div className="p-4">
                <TaskDetailView 
                  task={selectedTask}
                  open={true}
                  onOpenChange={(open) => {
                    if (!open) setSelectedTask(null);
                  }}
                />
              </div>
            </div>
          ) : selectedBranch ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 text-center">
              <div className="text-gray-500 dark:text-gray-400 py-8">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-lg font-medium mb-2">Select a task to view details</p>
                <p className="text-sm">Choose a task from the middle panel</p>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 text-center">
              <div className="text-gray-500 dark:text-gray-400 py-8">
                <div className="text-4xl mb-4">📂</div>
                <p className="text-lg font-medium mb-2">No task selected</p>
                <p className="text-sm">Select a project, branch, and task to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Rule Management view placeholder
function RuleManagementView() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Rules & Policies
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Configure system rules and compliance policies
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Rule Management
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Rule management interface will be implemented here
          </p>
          <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400">
            <p>• Configure system operation rules</p>
            <p>• Manage compliance policies</p>
            <p>• Set up validation rules</p>
            <p>• Monitor rule effectiveness</p>
          </div>
        </div>
      </div>
    </div>
  );
}