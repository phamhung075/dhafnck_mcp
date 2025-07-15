import { useState, useEffect, useCallback, useRef } from 'react';
import { mcpApi, Project, McpResponse } from '../api/enhanced';
import { 
  ProjectHealthStatus, 
  ProjectStatistics, 
  CrossProjectAnalytics, 
  CreateProjectData,
  ProjectIssue,
  MetricTrend,
  ProjectComparison,
  AnalyticsInsight
} from '../components/ProjectDashboard';

interface ProjectDashboardState {
  projects: Project[];
  selectedProject: Project | null;
  projectHealthStatuses: Record<string, ProjectHealthStatus>;
  projectStatistics: Record<string, ProjectStatistics>;
  crossProjectAnalytics: CrossProjectAnalytics | null;
  loading: {
    projects: boolean;
    health: boolean;
    analytics: boolean;
    operations: Record<string, boolean>;
  };
  errors: {
    projects: string | null;
    health: string | null;
    analytics: string | null;
    operations: Record<string, string>;
  };
}

interface ProjectDashboardActions {
  loadProjects: () => Promise<void>;
  selectProject: (project: Project | null) => void;
  createProject: (projectData: CreateProjectData) => Promise<Project | null>;
  updateProject: (projectId: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  runHealthCheck: (projectId: string) => Promise<void>;
  cleanupProject: (projectId: string) => Promise<void>;
  rebalanceAgents: (projectId: string) => Promise<void>;
  loadProjectHealthData: () => Promise<void>;
  loadCrossProjectAnalytics: () => Promise<void>;
  refreshProject: (projectId: string) => Promise<void>;
  bulkOperations: {
    runHealthChecks: (projectIds: string[]) => Promise<void>;
    rebalanceAgents: (projectIds: string[]) => Promise<void>;
    cleanup: (projectIds: string[]) => Promise<void>;
  };
}

export function useProjectDashboard(): {
  state: ProjectDashboardState;
  actions: ProjectDashboardActions;
} {
  const [state, setState] = useState<ProjectDashboardState>({
    projects: [],
    selectedProject: null,
    projectHealthStatuses: {},
    projectStatistics: {},
    crossProjectAnalytics: null,
    loading: {
      projects: false,
      health: false,
      analytics: false,
      operations: {}
    },
    errors: {
      projects: null,
      health: null,
      analytics: null,
      operations: {}
    }
  });
  
  // Use ref to store projects to avoid dependency issues
  const projectsRef = useRef<Project[]>([]);

  // Helper function to update loading state
  const setLoading = useCallback((key: keyof ProjectDashboardState['loading'] | string, value: boolean) => {
    setState(prev => ({
      ...prev,
      loading: {
        ...prev.loading,
        ...(typeof key === 'string' && key.includes('.') 
          ? { operations: { ...prev.loading.operations, [key]: value } }
          : { [key]: value })
      }
    }));
  }, []);

  // Helper function to set errors
  const setError = useCallback((key: keyof ProjectDashboardState['errors'] | string, error: string | null) => {
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        ...(typeof key === 'string' && key.includes('.') 
          ? { operations: { ...prev.errors.operations, [key]: error || '' } }
          : { [key]: error })
      }
    }));
  }, []);

  // Generate mock health status for a project
  const generateMockHealthStatus = useCallback((project: Project): ProjectHealthStatus => {
    const baseScore = Math.floor(Math.random() * 40) + 60; // 60-100
    const issues: ProjectIssue[] = [];
    
    // Generate mock issues based on health score
    if (baseScore < 80) {
      if (Math.random() > 0.5) {
        issues.push({
          id: `issue-${Date.now()}-1`,
          title: 'High memory usage detected',
          severity: baseScore < 70 ? 'high' : 'medium',
          description: 'Application is consuming more memory than expected'
        });
      }
      if (Math.random() > 0.7) {
        issues.push({
          id: `issue-${Date.now()}-2`,
          title: 'Slow API response times',
          severity: 'medium',
          description: 'Some API endpoints are responding slower than normal'
        });
      }
    }
    
    return {
      overall_score: baseScore,
      task_completion_rate: Math.floor(Math.random() * 30) + 70,
      agent_utilization: Math.floor(Math.random() * 20) + 80,
      blocker_count: Math.floor(Math.random() * 5),
      last_activity: new Date().toISOString(),
      health_trend: ['improving', 'stable', 'declining'][Math.floor(Math.random() * 3)] as any,
      issues
    };
  }, []);

  // Generate mock statistics for a project
  const generateMockStatistics = useCallback((project: Project): ProjectStatistics => {
    const totalTasks = Math.floor(Math.random() * 20) + 10;
    const completedTasks = Math.floor(Math.random() * totalTasks);
    
    return {
      total_tasks: totalTasks,
      completed_tasks: completedTasks,
      active_branches: Math.floor(Math.random() * 5) + 1,
      assigned_agents: Math.floor(Math.random() * 3) + 1,
      days_since_creation: Math.floor(Math.random() * 30) + 1,
      estimated_completion: `${Math.ceil((totalTasks - completedTasks) / 5)} weeks`
    };
  }, []);

  // Generate mock trend data
  const generateMockTrend = useCallback((): MetricTrend[] => {
    const days = 30;
    const trends: MetricTrend[] = [];
    let baseValue = 50 + Math.random() * 30;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Add some random variation
      baseValue += (Math.random() - 0.5) * 10;
      baseValue = Math.max(0, Math.min(100, baseValue));
      
      trends.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(baseValue)
      });
    }
    return trends;
  }, []);

  // Load projects from API
  const loadProjects = useCallback(async () => {
    setLoading('projects', true);
    setError('projects', null);
    
    try {
      const result = await mcpApi.manageProject('list');
      
      if (result.success && result.data?.projects) {
        projectsRef.current = result.data.projects;
        setState(prev => ({
          ...prev,
          projects: result.data.projects
        }));
      } else {
        throw new Error(result.error || 'Failed to load projects');
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      setError('projects', error instanceof Error ? error.message : 'Failed to load projects');
    } finally {
      setLoading('projects', false);
    }
  }, [setLoading, setError]);

  // Load health data for all projects
  const loadProjectHealthData = useCallback(async () => {
    if (projectsRef.current.length === 0) return;
    
    setLoading('health', true);
    setError('health', null);
    
    try {
      const healthPromises = projectsRef.current.map(async (project: Project) => {
        try {
          // Disable API calls to prevent infinite loops - use mock data only
          // const healthResult = await mcpApi.manageProject('project_health_check', { project_id: project.id });
          
          // Use deterministic mock data based on project ID
          const projectHash = project.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
          
          const healthStatus: ProjectHealthStatus = {
            overall_score: 60 + (projectHash % 40),
            task_completion_rate: 70 + (projectHash % 30),
            agent_utilization: 80 + (projectHash % 20),
            blocker_count: projectHash % 5,
            last_activity: (project as any).updated_at || new Date().toISOString(),
            health_trend: ['improving', 'stable', 'declining'][projectHash % 3] as any,
            issues: []
          };
          
          const statistics: ProjectStatistics = {
            total_tasks: 10 + (projectHash % 20),
            completed_tasks: 5 + (projectHash % 15),
            active_branches: 1 + (projectHash % 5),
            assigned_agents: 1 + (projectHash % 3),
            days_since_creation: 1 + (projectHash % 30),
            estimated_completion: '2-3 weeks'
          };

          return { projectId: project.id, healthStatus, statistics };
        } catch (error) {
          console.error(`Failed to load health data for project ${project.id}:`, error);
          
          // Return fallback mock data on error
          return {
            projectId: project.id,
            healthStatus: {
              overall_score: 75,
              task_completion_rate: 80,
              agent_utilization: 85,
              blocker_count: 1,
              last_activity: new Date().toISOString(),
              health_trend: 'stable' as any,
              issues: []
            },
            statistics: {
              total_tasks: 15,
              completed_tasks: 10,
              active_branches: 2,
              assigned_agents: 1,
              days_since_creation: 7,
              estimated_completion: '2 weeks'
            }
          };
        }
      });

      const results = await Promise.all(healthPromises);
      
      const healthStatuses: Record<string, ProjectHealthStatus> = {};
      const statistics: Record<string, ProjectStatistics> = {};
      
      results.forEach(result => {
        healthStatuses[result.projectId] = result.healthStatus;
        statistics[result.projectId] = result.statistics;
      });

      setState(prev => ({
        ...prev,
        projectHealthStatuses: healthStatuses,
        projectStatistics: statistics
      }));
    } catch (error) {
      console.error('Failed to load project health data:', error);
      setError('health', error instanceof Error ? error.message : 'Failed to load health data');
    } finally {
      setLoading('health', false);
    }
  }, [setLoading, setError]);

  // Load cross-project analytics
  const loadCrossProjectAnalytics = useCallback(async () => {
    setLoading('analytics', true);
    setError('analytics', null);
    
    try {
      // Generate mock analytics data
      const analytics: CrossProjectAnalytics = {
        summary: {
          total_projects: projectsRef.current.length,
          active_projects: projectsRef.current.length, // All projects are considered active since no status field
          completed_projects: 0, // No way to determine completed projects without status field
          average_health_score: Object.values(state.projectHealthStatuses).reduce((acc, health) => acc + health.overall_score, 0) / Object.values(state.projectHealthStatuses).length || 0,
          total_tasks: Object.values(state.projectStatistics).reduce((acc, stats) => acc + stats.total_tasks, 0),
          completed_tasks: Object.values(state.projectStatistics).reduce((acc, stats) => acc + stats.completed_tasks, 0)
        },
        trends: {
          project_creation_rate: generateMockTrend(),
          task_completion_rate: generateMockTrend(),
          health_score_trend: generateMockTrend(),
          agent_utilization: generateMockTrend()
        },
        comparisons: projectsRef.current.map(project => ({
          project_id: project.id,
          project_name: project.name,
          health_score: state.projectHealthStatuses[project.id]?.overall_score || 0,
          task_completion_rate: state.projectHealthStatuses[project.id]?.task_completion_rate || 0,
          agent_utilization: state.projectHealthStatuses[project.id]?.agent_utilization || 0,
          days_active: state.projectStatistics[project.id]?.days_since_creation || 0
        })),
        insights: [
          {
            type: 'recommendation',
            title: 'Consider Agent Rebalancing',
            description: 'Some projects have low agent utilization. Rebalancing could improve efficiency.',
            action_required: true
          },
          {
            type: 'warning',
            title: 'High Blocker Count',
            description: 'Several projects have blocking issues that need attention.',
            action_required: true
          }
        ]
      };

      setState(prev => ({
        ...prev,
        crossProjectAnalytics: analytics
      }));
    } catch (error) {
      console.error('Failed to load analytics:', error);
      setError('analytics', error instanceof Error ? error.message : 'Failed to load analytics');
    } finally {
      setLoading('analytics', false);
    }
  }, [state.projectHealthStatuses, state.projectStatistics, setLoading, setError, generateMockTrend]);

  // Select a project
  const selectProject = useCallback((project: Project | null) => {
    setState(prev => ({ ...prev, selectedProject: project }));
  }, []);

  // Create a new project
  const createProject = useCallback(async (projectData: CreateProjectData): Promise<Project | null> => {
    setLoading('operations.create', true);
    setError('operations.create', null);
    
    try {
      const result = await mcpApi.manageProject('create', {
        name: projectData.name,
        description: projectData.description
      });
      
      if (result.success && result.data?.project) {
        await loadProjects();
        return result.data.project;
      } else {
        throw new Error(result.error || 'Failed to create project');
      }
    } catch (error) {
      console.error('Failed to create project:', error);
      setError('operations.create', error instanceof Error ? error.message : 'Failed to create project');
      return null;
    } finally {
      setLoading('operations.create', false);
    }
  }, [setLoading, setError, loadProjects]);

  // Update a project
  const updateProject = useCallback(async (projectId: string, updates: Partial<Project>) => {
    setLoading(`operations.update.${projectId}`, true);
    setError(`operations.update.${projectId}`, null);
    
    try {
      const result = await mcpApi.manageProject('update', { 
        project_id: projectId, 
        ...updates 
      });
      
      if (result.success) {
        await loadProjects();
      } else {
        throw new Error(result.error || 'Failed to update project');
      }
    } catch (error) {
      console.error('Failed to update project:', error);
      setError(`operations.update.${projectId}`, error instanceof Error ? error.message : 'Failed to update project');
    } finally {
      setLoading(`operations.update.${projectId}`, false);
    }
  }, [setLoading, setError, loadProjects]);

  // Delete a project
  const deleteProject = useCallback(async (projectId: string) => {
    setLoading(`operations.delete.${projectId}`, true);
    setError(`operations.delete.${projectId}`, null);
    
    try {
      // Note: Delete operation might not be available in the API
      // This is a placeholder implementation
      console.log('Delete project:', projectId);
      
      // Remove from local state for now
      setState(prev => ({
        ...prev,
        projects: prev.projects.filter(p => p.id !== projectId),
        selectedProject: prev.selectedProject?.id === projectId ? null : prev.selectedProject
      }));
    } catch (error) {
      console.error('Failed to delete project:', error);
      setError(`operations.delete.${projectId}`, error instanceof Error ? error.message : 'Failed to delete project');
    } finally {
      setLoading(`operations.delete.${projectId}`, false);
    }
  }, [setLoading, setError]);

  // Run health check for a project
  const runHealthCheck = useCallback(async (projectId: string) => {
    setLoading(`operations.health.${projectId}`, true);
    setError(`operations.health.${projectId}`, null);
    
    try {
      const result = await mcpApi.manageProject('project_health_check', { project_id: projectId });
      
      if (result.success) {
        await loadProjectHealthData();
      } else {
        throw new Error(result.error || 'Failed to run health check');
      }
    } catch (error) {
      console.error('Failed to run health check:', error);
      setError(`operations.health.${projectId}`, error instanceof Error ? error.message : 'Failed to run health check');
    } finally {
      setLoading(`operations.health.${projectId}`, false);
    }
  }, [setLoading, setError, loadProjectHealthData]);

  // Cleanup a project
  const cleanupProject = useCallback(async (projectId: string) => {
    setLoading(`operations.cleanup.${projectId}`, true);
    setError(`operations.cleanup.${projectId}`, null);
    
    try {
      const result = await mcpApi.manageProject('cleanup_obsolete', { project_id: projectId });
      
      if (result.success) {
        await loadProjectHealthData();
      } else {
        throw new Error(result.error || 'Failed to cleanup project');
      }
    } catch (error) {
      console.error('Failed to cleanup project:', error);
      setError(`operations.cleanup.${projectId}`, error instanceof Error ? error.message : 'Failed to cleanup project');
    } finally {
      setLoading(`operations.cleanup.${projectId}`, false);
    }
  }, [setLoading, setError, loadProjectHealthData]);

  // Rebalance agents for a project
  const rebalanceAgents = useCallback(async (projectId: string) => {
    setLoading(`operations.rebalance.${projectId}`, true);
    setError(`operations.rebalance.${projectId}`, null);
    
    try {
      const result = await mcpApi.manageProject('rebalance_agents', { project_id: projectId });
      
      if (result.success) {
        await loadProjectHealthData();
      } else {
        throw new Error(result.error || 'Failed to rebalance agents');
      }
    } catch (error) {
      console.error('Failed to rebalance agents:', error);
      setError(`operations.rebalance.${projectId}`, error instanceof Error ? error.message : 'Failed to rebalance agents');
    } finally {
      setLoading(`operations.rebalance.${projectId}`, false);
    }
  }, [setLoading, setError, loadProjectHealthData]);

  // Refresh a specific project
  const refreshProject = useCallback(async (projectId: string) => {
    setLoading(`operations.refresh.${projectId}`, true);
    
    try {
      await runHealthCheck(projectId);
    } finally {
      setLoading(`operations.refresh.${projectId}`, false);
    }
  }, [setLoading, runHealthCheck]);

  // Bulk operations
  const bulkOperations = {
    runHealthChecks: useCallback(async (projectIds: string[]) => {
      setLoading('operations.bulk.health', true);
      
      try {
        await Promise.all(projectIds.map(id => runHealthCheck(id)));
      } finally {
        setLoading('operations.bulk.health', false);
      }
    }, [setLoading, runHealthCheck]),

    rebalanceAgents: useCallback(async (projectIds: string[]) => {
      setLoading('operations.bulk.rebalance', true);
      
      try {
        await Promise.all(projectIds.map(id => rebalanceAgents(id)));
      } finally {
        setLoading('operations.bulk.rebalance', false);
      }
    }, [setLoading, rebalanceAgents]),

    cleanup: useCallback(async (projectIds: string[]) => {
      setLoading('operations.bulk.cleanup', true);
      
      try {
        await Promise.all(projectIds.map(id => cleanupProject(id)));
      } finally {
        setLoading('operations.bulk.cleanup', false);
      }
    }, [setLoading, cleanupProject])
  };

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Load health data when projects change
  const [hasLoadedHealthData, setHasLoadedHealthData] = useState(false);
  
  useEffect(() => {
    if (projectsRef.current.length > 0 && !hasLoadedHealthData) {
      loadProjectHealthData();
      setHasLoadedHealthData(true);
    }
  }, [projectsRef.current.length, hasLoadedHealthData, loadProjectHealthData]);

  return {
    state,
    actions: {
      loadProjects,
      selectProject,
      createProject,
      updateProject,
      deleteProject,
      runHealthCheck,
      cleanupProject,
      rebalanceAgents,
      loadProjectHealthData,
      loadCrossProjectAnalytics,
      refreshProject,
      bulkOperations
    }
  };
}