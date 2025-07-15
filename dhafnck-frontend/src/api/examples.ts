/**
 * Usage Examples for Enhanced MCP API Wrapper
 * Demonstrates all 23 MCP tool methods and common patterns
 */

import { mcpApi, McpApiError } from './enhanced';

// Use the Project type from enhanced.ts
type Project = {
  id: string;
  name: string;
  description?: string;
  task_trees?: Record<string, any>;
};

// ===== AGENT MANAGEMENT EXAMPLES =====

/**
 * Example: Agent workflow - register, assign, and work
 */
export async function agentWorkflowExample() {
  try {
    // 1. Call a specific agent
    console.log('Calling agent...');
    const agentCall = await mcpApi.callAgent('@coding_agent');
    console.log('Agent response:', agentCall.data);

    // 2. List all agents in a project
    const agents = await mcpApi.getAgents('project-123');
    console.log('Available agents:', agents);

    // 3. Register a new agent
    const newAgent = await mcpApi.registerAgent('project-123', 'Custom Agent', '@custom_agent');
    console.log('Registered agent:', newAgent);

    // 4. Assign agent to a branch
    if (newAgent) {
      const assigned = await mcpApi.assignAgentToBranch('project-123', newAgent.id, 'branch-456');
      console.log('Agent assigned:', assigned);
    }

  } catch (error) {
    if (error instanceof McpApiError) {
      console.error(`Agent operation failed: ${error.code} - ${error.message}`);
    } else {
      console.error('Unexpected error:', error);
    }
  }
}

// ===== CONTEXT MANAGEMENT EXAMPLES =====

/**
 * Example: Hierarchical context with inheritance and delegation
 */
export async function contextManagementExample() {
  try {
    // 1. Resolve task context with inheritance
    console.log('Resolving task context...');
    const context = await mcpApi.resolveTaskContext('task-789', false);
    console.log('Resolved context:', context);

    // 2. Update task context
    const contextData = {
      progress: 'Implementation started',
      discoveries: ['Found reusable utility function'],
      decisions: ['Using React Query for state management']
    };
    
    await mcpApi.updateTaskContext('task-789', contextData, true);
    console.log('Context updated');

    // 3. Delegate pattern to project level
    const reusablePattern = {
      pattern_name: 'authentication_flow',
      implementation: 'JWT + refresh token pattern',
      usage_guide: 'Use for all protected routes'
    };

    await mcpApi.delegateToProject('task-789', reusablePattern, 'Reusable auth pattern');
    console.log('Pattern delegated to project');

    // 4. Validate context inheritance
    const validation = await mcpApi.validateContextInheritance('task', 'task-789');
    console.log('Context validation:', validation.data);

    // 5. Check delegation queue
    const delegations = await mcpApi.manageDelegationQueue('list');
    console.log('Pending delegations:', delegations.data);

  } catch (error) {
    console.error('Context management error:', error);
  }
}

// ===== SYSTEM OPERATIONS EXAMPLES =====

/**
 * Example: System monitoring and compliance
 */
export async function systemOperationsExample() {
  try {
    // 1. System health check
    console.log('Checking system health...');
    const health = await mcpApi.getSystemHealth(true);
    console.log('System status:', health);

    // 2. Get server capabilities
    const capabilities = await mcpApi.getServerCapabilities();
    console.log('Server capabilities:', capabilities);

    // 3. Validate operation for compliance
    const compliance = await mcpApi.validateOperation('edit_file', '/src/config.ts', 'const API_KEY = "test"');
    console.log('Compliance check:', compliance);

    // 4. Get rule hierarchy
    const ruleHierarchy = await mcpApi.getRuleHierarchy();
    console.log('Rule hierarchy:', ruleHierarchy);

    // 5. Sync rules
    const rulesSynced = await mcpApi.syncRules('client-123');
    console.log('Rules synced:', rulesSynced);

  } catch (error) {
    console.error('System operations error:', error);
  }
}

// ===== PROJECT & BRANCH MANAGEMENT EXAMPLES =====

/**
 * Example: Complete project setup workflow
 */
export async function projectManagementExample() {
  try {
    // 1. List all projects
    console.log('Listing projects...');
    const projects = await mcpApi.getProjects();
    console.log('Available projects:', projects);

    // 2. Create new project
    const newProject = await mcpApi.createProject('My New Project', 'A sample project for demonstration');
    console.log('Created project:', newProject);

    if (newProject) {
      // 3. Create a branch in the project
      const newBranch = await mcpApi.createBranch(newProject.id, 'feature/new-feature', 'Implementing new feature');
      console.log('Created branch:', newBranch);

      if (newBranch) {
        // 4. Get branch statistics
        const stats = await mcpApi.getBranchStatistics(newProject.id, newBranch.id);
        console.log('Branch statistics:', stats);

        // 5. Assign agent to branch (assuming we have an agent)
        const agents = await mcpApi.getAgents(newProject.id);
        if (agents.length > 0) {
          await mcpApi.assignAgentToBranch(newProject.id, agents[0].id, newBranch.id);
          console.log('Agent assigned to branch');
        }
      }

      // 6. Check project health
      const projectHealth = await mcpApi.getProjectHealth(newProject.id);
      console.log('Project health:', projectHealth);

      // 7. Rebalance agents if needed
      await mcpApi.rebalanceProjectAgents(newProject.id);
      console.log('Agents rebalanced');
    }

  } catch (error) {
    console.error('Project management error:', error);
  }
}

// ===== TASK MANAGEMENT EXAMPLES =====

/**
 * Example: Complete task lifecycle with subtasks
 */
export async function taskManagementExample() {
  try {
    // Assume we have a branch ID
    const branchId = 'branch-456';

    // 1. Get next recommended task
    console.log('Getting next task...');
    let nextTask = await mcpApi.getNextTask(branchId, true);
    
    if (!nextTask) {
      // 2. Create a new task if none available
      console.log('Creating new task...');
      nextTask = await mcpApi.createTask(
        branchId, 
        'Implement User Authentication', 
        'Add JWT-based authentication with login and logout functionality',
        'high'
      );
    }

    if (nextTask) {
      console.log('Working on task:', nextTask);

      // 3. Create subtasks for the main task
      const subtask1 = await mcpApi.createSubtask(nextTask.id, 'Create login form', 'React form with validation');
      const subtask2 = await mcpApi.createSubtask(nextTask.id, 'Implement JWT service', 'Token management utilities');
      const subtask3 = await mcpApi.createSubtask(nextTask.id, 'Add logout functionality', 'Clear tokens and redirect');

      console.log('Created subtasks:', [subtask1, subtask2, subtask3]);

      // 4. Update subtask progress
      if (subtask1) {
        await mcpApi.updateSubtaskProgress(nextTask.id, subtask1.id, 50, 'Form structure completed, adding validation');
        console.log('Updated subtask progress');
      }

      // 5. Complete a subtask
      if (subtask1) {
        await mcpApi.completeSubtask(
          nextTask.id, 
          subtask1.id, 
          'Login form completed with full validation and error handling',
          'UI foundation ready for authentication flow'
        );
        console.log('Completed subtask');
      }

      // 6. Search for related tasks
      const relatedTasks = await mcpApi.searchTasks('authentication', branchId, 10);
      console.log('Related tasks:', relatedTasks);

      // 7. Add task dependency if needed
      if (relatedTasks.length > 0) {
        await mcpApi.addTaskDependency(nextTask.id, relatedTasks[0].id);
        console.log('Added task dependency');
      }

      // 8. Eventually complete the main task
      // await mcpApi.completeTask(
      //   nextTask.id,
      //   'User authentication fully implemented with JWT tokens, secure storage, and proper error handling',
      //   'Tested login/logout flows, validated token refresh, confirmed security compliance'
      // );

    }

  } catch (error) {
    console.error('Task management error:', error);
  }
}

// ===== COMPREHENSIVE WORKFLOW EXAMPLE =====

/**
 * Example: End-to-end development workflow
 */
export async function comprehensiveWorkflowExample() {
  try {
    console.log('Starting comprehensive workflow...');

    // 1. System health check
    const isHealthy = await mcpApi.healthCheck();
    if (!isHealthy) {
      throw new Error('System is not healthy');
    }

    // 2. Switch to appropriate agent
    await mcpApi.callAgent('@task_planning_agent');

    // 3. Get or create project
    let projects = await mcpApi.getProjects();
    let project: Project | null = projects.find(p => p.name === 'Demo Project') || null;
    
    if (!project) {
      project = await mcpApi.createProject('Demo Project', 'Demonstration project for MCP API');
    }

    if (!project) {
      throw new Error('Could not create or find project');
    }

    // 4. Create feature branch
    const branch = await mcpApi.createBranch(project.id, 'feature/api-integration', 'Integrating MCP API');
    
    if (!branch) {
      throw new Error('Could not create branch');
    }

    // 5. Switch to coding agent
    await mcpApi.callAgent('@coding_agent');

    // 6. Create and work on tasks
    const task = await mcpApi.createTask(
      branch.id,
      'Integrate MCP API',
      'Add comprehensive MCP API integration with error handling',
      'high'
    );

    if (task) {
      // Create subtasks
      await mcpApi.createSubtask(task.id, 'Set up API client', 'Configure MCP API wrapper');
      await mcpApi.createSubtask(task.id, 'Add error handling', 'Implement retry logic and error recovery');
      await mcpApi.createSubtask(task.id, 'Write tests', 'Add comprehensive test coverage');

      // Update context with progress
      await mcpApi.updateTaskContext(task.id, {
        progress: 'API integration in progress',
        architecture_decisions: ['Using enhanced API wrapper', 'Implementing circuit breaker pattern'],
        next_steps: ['Complete error handling', 'Add monitoring']
      });
    }

    // 7. Monitor and validate
    const projectHealth = await mcpApi.getProjectHealth(project.id);
    const branchStats = await mcpApi.getBranchStatistics(project.id, branch.id);
    
    console.log('Workflow completed successfully');
    console.log('Project health:', projectHealth);
    console.log('Branch statistics:', branchStats);

  } catch (error) {
    console.error('Comprehensive workflow error:', error);
  }
}

// ===== ERROR HANDLING PATTERNS =====

/**
 * Example: Robust error handling patterns
 */
export async function errorHandlingExample() {
  try {
    // Example of handling different error types
    await mcpApi.callAgent('@nonexistent_agent');

  } catch (error) {
    if (error instanceof McpApiError) {
      switch (error.code) {
        case 'MISSING_REQUIRED_PARAM':
          console.error('Parameter missing:', error.message);
          // Handle missing parameter
          break;
          
        case 'NETWORK_ERROR':
          console.error('Network issue:', error.message);
          // Implement retry logic or offline mode
          break;
          
        case 'RATE_LIMIT':
          console.error('Rate limited:', error.message);
          // Wait and retry based on error.details.retryAfter
          break;
          
        case 'CIRCUIT_BREAKER_OPEN':
          console.error('Service unavailable:', error.message);
          // Switch to backup mode or notify user
          break;
          
        default:
          console.error('API error:', error.code, error.message);
          // Generic error handling
      }
    } else {
      console.error('Unexpected error:', error);
    }
  }
}

// ===== PERFORMANCE MONITORING EXAMPLE =====

/**
 * Example: Performance monitoring and optimization
 */
export async function performanceMonitoringExample() {
  // Reset metrics for clean measurement
  mcpApi.resetPerformanceMetrics();

  // Perform several operations
  await mcpApi.getSystemHealth();
  await mcpApi.getProjects();
  await mcpApi.getTasks();

  // Check performance metrics
  const metrics = mcpApi.getPerformanceMetrics();
  console.log('Performance Metrics:', {
    totalRequests: metrics.requestCount,
    successRate: `${(metrics.successCount / metrics.requestCount * 100).toFixed(2)}%`,
    averageResponseTime: `${metrics.averageResponseTime.toFixed(2)}ms`,
    currentQueueLength: metrics.queueLength,
    memoryUsage: metrics.memoryUsage ? `${(metrics.memoryUsage / 1024 / 1024).toFixed(2)}MB` : 'N/A'
  });

  // Check circuit breaker status
  const circuitStatus = mcpApi.getCircuitBreakerStatus();
  console.log('Circuit Breaker Status:', circuitStatus);
}

// Export all examples for easy testing
export const examples = {
  agentWorkflow: agentWorkflowExample,
  contextManagement: contextManagementExample,
  systemOperations: systemOperationsExample,
  projectManagement: projectManagementExample,
  taskManagement: taskManagementExample,
  comprehensiveWorkflow: comprehensiveWorkflowExample,
  errorHandling: errorHandlingExample,
  performanceMonitoring: performanceMonitoringExample
};