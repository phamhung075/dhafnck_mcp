import { useEffect, useState, useCallback, useMemo } from 'react';
import { mcpApi } from '../api/enhanced';
import type { Project } from '../types/application';
import { CrossProjectAnalytics } from './CrossProjectAnalytics';
import { ProjectCreationWizard } from './ProjectCreationWizard';
import { ProjectOverviewCard } from './ProjectOverviewCard';
import { ProjectSearchFilter } from './ProjectSearchFilter';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

// Type Definitions
export interface ProjectHealthStatus {
  overall_score: number;
  task_completion_rate: number;
  agent_utilization: number;
  blocker_count: number;
  last_activity: string;
  health_trend: 'improving' | 'stable' | 'declining';
  issues: ProjectIssue[];
}

export interface ProjectIssue {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

export interface ProjectStatistics {
  total_tasks: number;
  completed_tasks: number;
  active_branches: number;
  assigned_agents: number;
  days_since_creation: number;
  estimated_completion: string;
}

export interface CreateProjectData {
  name: string;
  description: string;
  template_id?: string;
  initial_branches: string[];
  assigned_agents: string[];
  estimated_duration: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  tags: string[];
}

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  default_branches: string[];
  recommended_agents: string[];
  initial_tasks: TaskTemplate[];
}

export interface TaskTemplate {
  title: string;
  description: string;
  priority: string;
}

export interface CrossProjectAnalytics {
  summary: {
    total_projects: number;
    active_projects: number;
    completed_projects: number;
    average_health_score: number;
    total_tasks: number;
    completed_tasks: number;
  };
  trends: {
    project_creation_rate: MetricTrend[];
    task_completion_rate: MetricTrend[];
    health_score_trend: MetricTrend[];
    agent_utilization: MetricTrend[];
  };
  comparisons: ProjectComparison[];
  insights: AnalyticsInsight[];
}

export interface MetricTrend {
  date: string;
  value: number;
}

export interface ProjectComparison {
  project_id: string;
  project_name: string;
  health_score: number;
  task_completion_rate: number;
  agent_utilization: number;
  days_active: number;
}

export interface AnalyticsInsight {
  type: 'recommendation' | 'warning' | 'success';
  title: string;
  description: string;
  action_required: boolean;
}

// Main Component Props
interface ProjectDashboardProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (project: Project) => void;
  onCreateProject: (projectData: CreateProjectData) => Promise<void>;
  onUpdateProject: (projectId: string, updates: Partial<Project>) => Promise<void>;
  onDeleteProject: (projectId: string) => Promise<void>;
  onRunHealthCheck: (projectId: string) => Promise<void>;
  onCleanupProject: (projectId: string) => Promise<void>;
  onRebalanceAgents: (projectId: string) => Promise<void>;
}

export function ProjectDashboard({
  projects,
  selectedProject,
  onSelectProject,
  onCreateProject,
  onUpdateProject,
  onDeleteProject,
  onRunHealthCheck,
  onCleanupProject,
  onRebalanceAgents
}: ProjectDashboardProps) {
  const [view, setView] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [filteredProjects, setFilteredProjects] = useState<Project[]>(projects);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [projectHealthStatuses, setProjectHealthStatuses] = useState<Record<string, ProjectHealthStatus>>({});
  const [projectStatistics, setProjectStatistics] = useState<Record<string, ProjectStatistics>>({});
  const [crossProjectAnalytics, setCrossProjectAnalytics] = useState<CrossProjectAnalytics | null>(null);
  const [hasLoadedHealth, setHasLoadedHealth] = useState(false);
  const [loading, setLoading] = useState({
    projects: false,
    health: false,
    analytics: false,
  });

  // Memoize projects to prevent unnecessary re-renders
  const memoizedProjects = useMemo(() => projects, [projects]);

  // Sync filteredProjects with projects when projects change
  useEffect(() => {
    setFilteredProjects(memoizedProjects);
  }, [memoizedProjects]);

  const projectTemplates: ProjectTemplate[] = [
    {
      id: 'web-app',
      name: 'Web Application',
      description: 'Full-stack web application with frontend and backend',
      default_branches: ['main', 'feature/frontend', 'feature/backend'],
      recommended_agents: ['@coding_agent', '@ui_designer_agent', '@test_orchestrator_agent'],
      initial_tasks: [
        { title: 'Setup project structure', description: 'Initialize project structure and dependencies', priority: 'high' },
        { title: 'Design system architecture', description: 'Plan system architecture and data flow', priority: 'high' },
        { title: 'Create basic UI components', description: 'Build foundational UI components', priority: 'medium' }
      ]
    },
    {
      id: 'api-service',
      name: 'API Service',
      description: 'RESTful API service with database integration',
      default_branches: ['main', 'feature/api', 'feature/database'],
      recommended_agents: ['@coding_agent', '@devops_agent', '@security_auditor_agent'],
      initial_tasks: [
        { title: 'Define API endpoints', description: 'Design and document API endpoints', priority: 'high' },
        { title: 'Setup database schema', description: 'Design and implement database schema', priority: 'high' },
        { title: 'Implement authentication', description: 'Add user authentication and authorization', priority: 'medium' }
      ]
    },
    {
      id: 'ml-project',
      name: 'Machine Learning Project',
      description: 'Data science and machine learning project',
      default_branches: ['main', 'feature/data-processing', 'feature/model-training'],
      recommended_agents: ['@brainjs_ml_agent', '@deep_research_agent', '@test_orchestrator_agent'],
      initial_tasks: [
        { title: 'Data collection and cleaning', description: 'Gather and preprocess training data', priority: 'high' },
        { title: 'Model development', description: 'Develop and train machine learning models', priority: 'high' },
        { title: 'Model evaluation', description: 'Evaluate model performance and accuracy', priority: 'medium' }
      ]
    }
  ];

  const loadProjectHealthData = useCallback(async () => {
    setLoading(prev => ({ ...prev, health: true }));
    
    try {
      const healthPromises = memoizedProjects.map(async (project: Project) => {
        try {
          // Disable API calls to prevent infinite loops
          // const healthResult = await mcpApi.manageProject('project_health_check', { project_id: project.id });
          // const statsResult = await mcpApi.manageGitBranch('get_statistics', { project_id: project.id });
          
          // Mock health status - use deterministic values based on project ID
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
          return null;
        }
      });

      const results = await Promise.all(healthPromises);
      
      const healthStatuses: Record<string, ProjectHealthStatus> = {};
      const statistics: Record<string, ProjectStatistics> = {};
      
      results.forEach(result => {
        if (result) {
          healthStatuses[result.projectId] = result.healthStatus;
          statistics[result.projectId] = result.statistics;
        }
      });

      setProjectHealthStatuses(healthStatuses);
      setProjectStatistics(statistics);
    } catch (error) {
      console.error('Failed to load project health data:', error);
    } finally {
      setLoading(prev => ({ ...prev, health: false }));
    }
  }, [memoizedProjects]);

  // Load project health data when projects change - only once
  useEffect(() => {
    // Only load once when projects are available and we haven't loaded yet
    if (memoizedProjects.length > 0 && !hasLoadedHealth) {
      // Use a timeout to ensure this runs after the component is fully mounted
      const timeoutId = setTimeout(() => {
        loadProjectHealthData();
        setHasLoadedHealth(true);
      }, 100);
      
      return () => clearTimeout(timeoutId);
    }
  }, [memoizedProjects.length, hasLoadedHealth]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadCrossProjectAnalytics = async () => {
    setLoading(prev => ({ ...prev, analytics: true }));
    
    try {
      // Mock analytics data - in real implementation, this would come from API
      const analytics: CrossProjectAnalytics = {
        summary: {
          total_projects: projects.length,
          active_projects: projects.length, // Assume all projects are active for now
          completed_projects: 0, // No status field in current Project type
          average_health_score: Object.values(projectHealthStatuses).reduce((acc, health) => acc + health.overall_score, 0) / Object.values(projectHealthStatuses).length || 0,
          total_tasks: Object.values(projectStatistics).reduce((acc, stats) => acc + stats.total_tasks, 0),
          completed_tasks: Object.values(projectStatistics).reduce((acc, stats) => acc + stats.completed_tasks, 0)
        },
        trends: {
          project_creation_rate: generateMockTrend(),
          task_completion_rate: generateMockTrend(),
          health_score_trend: generateMockTrend(),
          agent_utilization: generateMockTrend()
        },
        comparisons: projects.map(project => ({
          project_id: project.id,
          project_name: project.name,
          health_score: projectHealthStatuses[project.id]?.overall_score || 0,
          task_completion_rate: projectHealthStatuses[project.id]?.task_completion_rate || 0,
          agent_utilization: projectHealthStatuses[project.id]?.agent_utilization || 0,
          days_active: projectStatistics[project.id]?.days_since_creation || 0
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

      setCrossProjectAnalytics(analytics);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(prev => ({ ...prev, analytics: false }));
    }
  };

  const generateMockTrend = useCallback((): MetricTrend[] => {
    const days = 30;
    const trends: MetricTrend[] = [];
    const baseDate = new Date('2024-01-01'); // Use fixed base date to avoid changing data
    for (let i = days; i >= 0; i--) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() + (30 - i));
      trends.push({
        date: date.toISOString().split('T')[0],
        value: 70 + Math.sin(i * 0.2) * 20 // Deterministic pattern instead of random
      });
    }
    return trends;
  }, []);

  const handleCreateProject = async (projectData: CreateProjectData) => {
    try {
      await onCreateProject(projectData);
      setShowCreateWizard(false);
      await loadProjectHealthData();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const handleRunHealthCheck = async (projectId: string) => {
    try {
      await onRunHealthCheck(projectId);
      await loadProjectHealthData();
    } catch (error) {
      console.error('Failed to run health check:', error);
    }
  };

  const handleFilterChange = useCallback((filtered: Project[]) => {
    setFilteredProjects(filtered);
  }, []);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Project Dashboard</h1>
          <p className="text-gray-600">Manage and monitor all your projects</p>
        </div>
        
        <div className="flex gap-2">
          <div className="flex border rounded-lg overflow-hidden">
            <button
              onClick={() => setView('grid')}
              className={`px-3 py-2 text-sm ${view === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setView('list')}
              className={`px-3 py-2 text-sm ${view === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              List
            </button>
            <button
              onClick={() => {
                setView('analytics');
                loadCrossProjectAnalytics();
              }}
              className={`px-3 py-2 text-sm ${view === 'analytics' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              Analytics
            </button>
          </div>
          
          <Dialog open={showCreateWizard} onOpenChange={setShowCreateWizard}>
            <DialogTrigger asChild>
              <Button>Create Project</Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
              </DialogHeader>
              <ProjectCreationWizard
                onCreateProject={handleCreateProject}
                onCancel={() => setShowCreateWizard(false)}
                templates={projectTemplates}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Analytics View */}
      {view === 'analytics' && crossProjectAnalytics && (
        <CrossProjectAnalytics
          projects={projects}
          analytics={crossProjectAnalytics}
          onRefreshAnalytics={loadCrossProjectAnalytics}
          timeRange="30d"
          onTimeRangeChange={() => {}}
        />
      )}

      {/* Project View */}
      {view !== 'analytics' && (
        <>
          {/* Search and Filter */}
          <ProjectSearchFilter
            projects={projects}
            onFilterChange={handleFilterChange}
          />

          {/* Loading State */}
          {loading.health && (
            <div className="text-center py-8">
              <div className="text-lg">Loading project health data...</div>
            </div>
          )}

          {/* Projects Grid/List */}
          {!loading.health && (
            <>
              {view === 'grid' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredProjects.map(project => (
                    <ProjectOverviewCard
                      key={project.id}
                      project={project}
                      healthStatus={projectHealthStatuses[project.id] || {
                        overall_score: 0,
                        task_completion_rate: 0,
                        agent_utilization: 0,
                        blocker_count: 0,
                        last_activity: new Date().toISOString(),
                        health_trend: 'stable',
                        issues: []
                      }}
                      statistics={projectStatistics[project.id] || {
                        total_tasks: 0,
                        completed_tasks: 0,
                        active_branches: 0,
                        assigned_agents: 0,
                        days_since_creation: 0,
                        estimated_completion: 'Unknown'
                      }}
                      onSelect={() => onSelectProject(project)}
                      onEdit={() => console.log('Edit project:', project.id)}
                      onRunHealthCheck={() => handleRunHealthCheck(project.id)}
                      onViewDetails={() => console.log('View details:', project.id)}
                      isSelected={selectedProject?.id === project.id}
                    />
                  ))}
                </div>
              )}

              {view === 'list' && (
                <Card className="p-6">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3 px-2">Project Name</th>
                          <th className="text-left py-3 px-2">Health Score</th>
                          <th className="text-left py-3 px-2">Tasks</th>
                          <th className="text-left py-3 px-2">Branches</th>
                          <th className="text-left py-3 px-2">Agents</th>
                          <th className="text-left py-3 px-2">Last Activity</th>
                          <th className="text-left py-3 px-2">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredProjects.map(project => {
                          const health = projectHealthStatuses[project.id];
                          const stats = projectStatistics[project.id];
                          
                          return (
                            <tr key={project.id} className="border-b hover:bg-gray-50">
                              <td className="py-3 px-2">
                                <div>
                                  <div className="font-medium">{project.name}</div>
                                  <div className="text-sm text-gray-600">{project.description}</div>
                                </div>
                              </td>
                              <td className="py-3 px-2">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 bg-gray-200 rounded-full h-2">
                                    <div 
                                      className="bg-blue-600 h-2 rounded-full" 
                                      style={{ width: `${health?.overall_score || 0}%` }}
                                    />
                                  </div>
                                  <span className="text-sm">{health?.overall_score || 0}%</span>
                                </div>
                              </td>
                              <td className="py-3 px-2">
                                {stats?.completed_tasks || 0}/{stats?.total_tasks || 0}
                              </td>
                              <td className="py-3 px-2">{stats?.active_branches || 0}</td>
                              <td className="py-3 px-2">{stats?.assigned_agents || 0}</td>
                              <td className="py-3 px-2">
                                {health?.last_activity ? new Date(health.last_activity).toLocaleDateString() : 'Unknown'}
                              </td>
                              <td className="py-3 px-2">
                                <div className="flex gap-1">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleRunHealthCheck(project.id)}
                                  >
                                    Health Check
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => onSelectProject(project)}
                                  >
                                    View
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}

              {filteredProjects.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-gray-500 text-lg mb-4">No projects match your filters</div>
                  <Button onClick={() => setShowCreateWizard(true)}>
                    Create Your First Project
                  </Button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}