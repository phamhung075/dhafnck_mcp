import { mcpApi as api } from '../api/enhanced';
import { store } from '../store/store';
import { systemActions, sessionActions, dataActions, uiActions } from '../store/store';
import type { Project, GitBranch, Task, Agent, CreateProjectData } from '../types/application';

export class APIOrchestrator {
  private retryCount = 3;
  private retryDelay = 1000;
  private requestQueue = new Map<string, Promise<any>>();

  // Execute operation with retry logic and error handling
  async executeWithRetry<T>(
    operation: () => Promise<T>,
    operationKey?: string
  ): Promise<T> {
    // Deduplicate concurrent requests
    if (operationKey && this.requestQueue.has(operationKey)) {
      return this.requestQueue.get(operationKey)!;
    }

    const execute = async (): Promise<T> => {
      let lastError: any;
      
      for (let attempt = 1; attempt <= this.retryCount; attempt++) {
        try {
          const result = await operation();
          return result;
        } catch (error: any) {
          lastError = error;
          
          // Don't retry on authentication errors or client errors (4xx)
          if (error.status >= 400 && error.status < 500) {
            throw error;
          }
          
          if (attempt < this.retryCount) {
            const delay = this.retryDelay * Math.pow(2, attempt - 1); // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }
      
      throw lastError;
    };

    const promise = execute();
    
    if (operationKey) {
      this.requestQueue.set(operationKey, promise);
      promise.finally(() => this.requestQueue.delete(operationKey));
    }
    
    return promise;
  }

  // Initialize a new project with complete setup
  async initializeProject(projectData: CreateProjectData): Promise<{
    project: Project;
    mainBranch: GitBranch;
    agents: Agent[];
  }> {
    return this.executeWithRetry(async () => {
      const dispatch = store.dispatch;
      
      try {
        dispatch(systemActions.setLoading({ key: 'project_creation', loading: true }));
        
        // 1. Create project
        const projectResponse = await api.manageProject('create', {
          name: projectData.name,
          description: projectData.description
        });
        const project = projectResponse.data?.project;
        
        if (!project?.id) {
          throw new Error('Project creation failed - no project ID returned');
        }

        // 2. Create main branch
        const branchResponse = await api.manageGitBranch('create', {
          project_id: project.id,
          git_branch_name: 'main',
          git_branch_description: 'Main development branch'
        });
        const mainBranch = branchResponse.data?.git_branch;

        // 3. Initialize project context
        await api.manageContext('create', {
          task_id: project.id, // Using project ID as context ID
          data_title: project.name,
          data_description: project.description || 'Project context',
          data_status: 'active',
          data_priority: 'medium'
        });

        // 4. Assign initial agents if specified
        const agents: Agent[] = [];
        if (projectData.initial_agents && projectData.initial_agents.length > 0) {
          for (const agentId of projectData.initial_agents) {
            try {
              await api.manageGitBranch('assign_agent', {
                project_id: project.id,
                git_branch_id: mainBranch.id,
                agent_id: agentId
              });
              
              agents.push({
                id: agentId,
                name: agentId,
                status: 'active',
                project_id: project.id
              });
            } catch (error) {
              console.warn(`Failed to assign agent ${agentId}:`, error);
            }
          }
        }

        // 5. Update Redux store
        dispatch(dataActions.addProject(project));
        dispatch(dataActions.addBranch({ projectId: project.id, branch: mainBranch }));
        dispatch(dataActions.setAgents({ projectId: project.id, agents }));

        // 6. Show success notification
        dispatch(uiActions.addUINotification({
          id: `project_created_${Date.now()}`,
          type: 'success',
          title: 'Project Created',
          message: `Successfully created project "${project.name}" with main branch and ${agents.length} agents.`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 5000
        }));

        return { project, mainBranch, agents };
        
      } catch (error: any) {
        dispatch(uiActions.addUINotification({
          id: `project_creation_error_${Date.now()}`,
          type: 'error',
          title: 'Project Creation Failed',
          message: `Failed to create project: ${error.message || error}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: false
        }));
        throw error;
      } finally {
        dispatch(systemActions.setLoading({ key: 'project_creation', loading: false }));
      }
    }, `create_project_${projectData.name}`);
  }

  // Switch agent and update context
  async switchAgentAndContext(
    agentName: string, 
    projectId?: string, 
    taskId?: string
  ): Promise<void> {
    return this.executeWithRetry(async () => {
      const dispatch = store.dispatch;
      
      try {
        dispatch(systemActions.setLoading({ key: 'agent_switch', loading: true }));
        
        // 1. Switch agent
        await api.callAgent(agentName);
        
        // 2. Resolve context if provided
        let contextResolved = false;
        if (taskId) {
          try {
            await api.manageHierarchicalContext('resolve', {
              level: 'task',
              context_id: taskId
            });
            contextResolved = true;
          } catch (error) {
            console.warn('Failed to resolve task context:', error);
          }
        } else if (projectId) {
          try {
            await api.manageHierarchicalContext('resolve', {
              level: 'project',
              context_id: projectId
            });
            contextResolved = true;
          } catch (error) {
            console.warn('Failed to resolve project context:', error);
          }
        }
        
        // 3. Update session state
        dispatch(sessionActions.setCurrentAgent({
          id: agentName,
          name: agentName,
          status: 'active',
          project_id: projectId || '',
          last_activity: new Date().toISOString()
        }));
        
        // 4. Show success notification
        dispatch(uiActions.addUINotification({
          id: `agent_switch_${Date.now()}`,
          type: 'success',
          title: 'Agent Switched',
          message: `Successfully switched to ${agentName}${contextResolved ? ' with context resolved' : ''}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 3000
        }));
        
      } catch (error: any) {
        dispatch(uiActions.addUINotification({
          id: `agent_switch_error_${Date.now()}`,
          type: 'error',
          title: 'Agent Switch Failed',
          message: `Failed to switch to ${agentName}: ${error.message || error}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: false
        }));
        throw error;
      } finally {
        dispatch(systemActions.setLoading({ key: 'agent_switch', loading: false }));
      }
    }, `switch_agent_${agentName}`);
  }

  // Create and manage a complete task workflow
  async createTaskWorkflow(
    projectId: string,
    branchId: string,
    taskData: {
      title: string;
      description?: string;
      priority?: string;
      assignees?: string[];
      subtasks?: Array<{ title: string; description?: string }>;
    }
  ): Promise<{ task: Task; subtasks: Task[] }> {
    return this.executeWithRetry(async () => {
      const dispatch = store.dispatch;
      
      try {
        dispatch(systemActions.setLoading({ key: 'task_creation', loading: true }));
        
        // 1. Create main task
        const taskResponse = await api.manageTask('create', {
          git_branch_id: branchId,
          title: taskData.title,
          description: taskData.description,
          priority: taskData.priority || 'medium',
          assignees: taskData.assignees
        });
        const task = taskResponse.data?.task;

        // 2. Create subtasks if provided
        const subtasks: Task[] = [];
        if (taskData.subtasks && taskData.subtasks.length > 0) {
          for (const subtaskData of taskData.subtasks) {
            try {
              const subtaskResponse = await api.manageSubtask('create', {
                task_id: task.id,
                title: subtaskData.title,
                description: subtaskData.description
              });
              if (subtaskResponse.data?.subtask) {
                subtasks.push(subtaskResponse.data.subtask);
              }
            } catch (error) {
              console.warn('Failed to create subtask:', error);
            }
          }
        }

        // 3. Initialize task context
        try {
          await api.manageContext('create', {
            task_id: task.id,
            data_title: task.title,
            data_description: task.description || '',
            data_status: task.status,
            data_priority: task.priority
          });
        } catch (error) {
          console.warn('Failed to create task context:', error);
        }

        // 4. Update Redux store
        dispatch(dataActions.addTask({ branchId, task }));
        
        // 5. Show success notification
        dispatch(uiActions.addUINotification({
          id: `task_created_${Date.now()}`,
          type: 'success',
          title: 'Task Created',
          message: `Created task "${task.title}" with ${subtasks.length} subtasks`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 4000
        }));

        return { task, subtasks };
        
      } catch (error: any) {
        dispatch(uiActions.addUINotification({
          id: `task_creation_error_${Date.now()}`,
          type: 'error',
          title: 'Task Creation Failed',
          message: `Failed to create task: ${error.message || error}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: false
        }));
        throw error;
      } finally {
        dispatch(systemActions.setLoading({ key: 'task_creation', loading: false }));
      }
    }, `create_task_${taskData.title}_${branchId}`);
  }

  // Comprehensive system health check with notifications
  async performSystemHealthCheck(): Promise<void> {
    return this.executeWithRetry(async () => {
      const dispatch = store.dispatch;
      
      try {
        dispatch(systemActions.setLoading({ key: 'health_check', loading: true }));
        
        // 1. Basic health check
        const healthResponse = await api.manageConnection('health_check', { 
          include_details: true 
        });
        if (healthResponse.data) {
          dispatch(systemActions.setSystemHealth(healthResponse.data));
        }

        // 2. Get compliance status
        try {
          const complianceResponse = await api.manageCompliance('get_compliance_dashboard');
          if (complianceResponse.data) {
            dispatch(systemActions.setComplianceStatus(complianceResponse.data));
          }
        } catch (error) {
          console.warn('Failed to get compliance status:', error);
        }

        // 3. Get server capabilities
        try {
          const capabilities = await api.manageConnection('server_capabilities', {
            include_details: true
          });
          // Store capabilities in session or system state if needed
        } catch (error) {
          console.warn('Failed to get server capabilities:', error);
        }

        // 4. Analyze health and show appropriate notifications
        const overallHealth = healthResponse.data?.overall_score || 0;
        if (overallHealth >= 80) {
          dispatch(uiActions.addUINotification({
            id: `health_good_${Date.now()}`,
            type: 'success',
            title: 'System Health Excellent',
            message: `All systems are running optimally (${overallHealth}%)`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: true,
            duration: 3000
          }));
        } else if (overallHealth >= 50) {
          dispatch(uiActions.addUINotification({
            id: `health_warning_${Date.now()}`,
            type: 'warning',
            title: 'System Health Degraded',
            message: `Some systems need attention (${overallHealth}%)`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: false
          }));
        } else {
          dispatch(uiActions.addUINotification({
            id: `health_critical_${Date.now()}`,
            type: 'error',
            title: 'System Health Critical',
            message: `Multiple systems are failing (${overallHealth}%). Immediate attention required.`,
            timestamp: new Date().toISOString(),
            read: false,
            autoClose: false
          }));
        }
        
      } catch (error: any) {
        dispatch(uiActions.addUINotification({
          id: `health_check_error_${Date.now()}`,
          type: 'error',
          title: 'Health Check Failed',
          message: `Unable to check system health: ${error.message || error}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: false
        }));
        throw error;
      } finally {
        dispatch(systemActions.setLoading({ key: 'health_check', loading: false }));
      }
    }, 'system_health_check');
  }

  // Batch data refresh operation
  async refreshAllData(): Promise<void> {
    return this.executeWithRetry(async () => {
      const dispatch = store.dispatch;
      
      try {
        dispatch(systemActions.setLoading({ key: 'data_refresh', loading: true }));
        
        // Run multiple operations in parallel
        const [
          projects,
          healthData,
          complianceData
        ] = await Promise.allSettled([
          api.manageProject('list'),
          api.manageConnection('health_check', { include_details: true }),
          api.manageCompliance('get_compliance_dashboard')
        ]);

        // Process results
        if (projects.status === 'fulfilled' && projects.value.success && projects.value.data) {
          dispatch(dataActions.setProjects(projects.value.data));
        } else {
          console.error('Failed to refresh projects:', projects.status === 'rejected' ? projects.reason : 'No data returned');
        }

        if (healthData.status === 'fulfilled' && healthData.value.success && healthData.value.data) {
          dispatch(systemActions.setSystemHealth(healthData.value.data));
        } else {
          console.error('Failed to refresh health data:', healthData.status === 'rejected' ? healthData.reason : 'No data returned');
        }

        if (complianceData.status === 'fulfilled' && complianceData.value.success && complianceData.value.data) {
          dispatch(systemActions.setComplianceStatus(complianceData.value.data));
        } else {
          console.error('Failed to refresh compliance data:', complianceData.status === 'rejected' ? complianceData.reason : 'No data returned');
        }

        // Show success notification
        const successCount = [projects, healthData, complianceData].filter(
          result => result.status === 'fulfilled'
        ).length;
        
        dispatch(uiActions.addUINotification({
          id: `data_refresh_${Date.now()}`,
          type: successCount === 3 ? 'success' : 'warning',
          title: 'Data Refresh Complete',
          message: `${successCount}/3 data sources refreshed successfully`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: true,
          duration: 3000
        }));
        
      } catch (error: any) {
        dispatch(uiActions.addUINotification({
          id: `data_refresh_error_${Date.now()}`,
          type: 'error',
          title: 'Data Refresh Failed',
          message: `Failed to refresh data: ${error.message || error}`,
          timestamp: new Date().toISOString(),
          read: false,
          autoClose: false
        }));
        throw error;
      } finally {
        dispatch(systemActions.setLoading({ key: 'data_refresh', loading: false }));
      }
    }, 'refresh_all_data');
  }

  // Clean up completed operations and clear cache
  cleanup(): void {
    this.requestQueue.clear();
  }
}

// Export singleton instance
export const apiOrchestrator = new APIOrchestrator();