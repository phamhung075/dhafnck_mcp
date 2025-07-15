/**
 * Enhanced MCP API Foundation Layer
 * Provides robust error handling, performance monitoring, and retry logic
 * for all 23 MCP tools in the DhafnckMCP system
 */

import { config } from '../config';

// Core Type Definitions
export interface McpResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: Record<string, any>;
}

export interface RequestOptions {
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

export interface ApiRequest {
  toolName: string;
  arguments: Record<string, any>;
  options?: RequestOptions;
}

export interface PerformanceMetrics {
  requestCount: number;
  successCount: number;
  errorCount: number;
  averageResponseTime: number;
  queueLength: number;
  memoryUsage?: number;
}

// Error Types
export class McpApiError extends Error {
  public code: string;
  public operation: string;
  public details?: any;
  public retryable: boolean;

  constructor(message: string, code: string, operation: string, details?: any, retryable = false) {
    super(message);
    this.name = 'McpApiError';
    this.code = code;
    this.operation = operation;
    this.details = details;
    this.retryable = retryable;
  }
}

// Circuit Breaker States
enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

interface CircuitBreakerOptions {
  failureThreshold: number;
  resetTimeout: number;
  monitoringPeriod: number;
}

class CircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failures = 0;
  private lastFailureTime?: number;
  private readonly options: CircuitBreakerOptions;

  constructor(options: Partial<CircuitBreakerOptions> = {}) {
    this.options = {
      failureThreshold: 5,
      resetTimeout: 60000, // 1 minute
      monitoringPeriod: 10000, // 10 seconds
      ...options
    };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitBreakerState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitBreakerState.HALF_OPEN;
      } else {
        throw new McpApiError(
          'Circuit breaker is OPEN - service unavailable',
          'CIRCUIT_BREAKER_OPEN',
          'circuit_breaker'
        );
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldAttemptReset(): boolean {
    return this.lastFailureTime 
      ? (Date.now() - this.lastFailureTime) > this.options.resetTimeout
      : false;
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = CircuitBreakerState.CLOSED;
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.failures >= this.options.failureThreshold) {
      this.state = CircuitBreakerState.OPEN;
    }
  }
}

// Main API Wrapper Class
export class McpApiWrapper {
  private baseUrl: string;
  private headers: Record<string, string>;
  private rpcId: number;
  private performanceMetrics: PerformanceMetrics;
  private circuitBreaker: CircuitBreaker;
  private requestQueue: Array<{ id: string; timestamp: number }> = [];
  private requestCache: Map<string, { data: any; timestamp: number }> = new Map();
  private pendingRequests: Map<string, Promise<any>> = new Map();
  private cacheTimeout = config.cache.timeout;

  constructor(baseUrl: string = config.mcp.baseUrl) {
    this.baseUrl = baseUrl;
    this.headers = {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "MCP-Protocol-Version": "2025-06-18"
    };
    this.rpcId = 1;
    this.performanceMetrics = {
      requestCount: 0,
      successCount: 0,
      errorCount: 0,
      averageResponseTime: 0,
      queueLength: 0
    };
    this.circuitBreaker = new CircuitBreaker();
  }

  private getRpcId(): number {
    return this.rpcId++;
  }

  private getCacheKey(toolName: string, args: any): string {
    return `${toolName}:${JSON.stringify(args)}`;
  }

  private isCacheableRequest(toolName: string, args: any): boolean {
    // Cache read-only operations
    const cacheableActions = ['list', 'get', 'health_check', 'status', 'get_compliance_dashboard'];
    const action = args.action || '';
    
    // Special cases
    if (toolName === 'manage_connection' && ['health_check', 'status', 'server_capabilities'].includes(action)) {
      return true;
    }
    if (toolName === 'manage_compliance' && action === 'get_compliance_dashboard') {
      return true;
    }
    
    return cacheableActions.includes(action);
  }

  /**
   * Enhanced parameter validation for all MCP tools
   */
  private validateToolParameters(toolName: string, args: any): void {
    if (!args) {
      throw new McpApiError(`Missing parameters for ${toolName}`, 'MISSING_PARAMS', toolName);
    }

    // Tool-specific validation rules
    const validationRules: Record<string, (params: any) => void> = {
      'call_agent': (params) => {
        if (!params.name_agent) {
          throw new McpApiError('name_agent parameter is required', 'MISSING_REQUIRED_PARAM', 'call_agent');
        }
      },
      
      'manage_agent': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_agent');
        }
        if (['register'].includes(params.action) && !params.project_id) {
          throw new McpApiError('project_id is required for register action', 'MISSING_REQUIRED_PARAM', 'manage_agent');
        }
        if (['assign', 'unassign'].includes(params.action) && (!params.project_id || !params.agent_id || !params.git_branch_id)) {
          throw new McpApiError('project_id, agent_id, and git_branch_id are required for assign/unassign actions', 'MISSING_REQUIRED_PARAM', 'manage_agent');
        }
      },

      'manage_task': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_task');
        }
        if (params.action === 'create' && !params.git_branch_id) {
          throw new McpApiError('git_branch_id is required for create action', 'MISSING_REQUIRED_PARAM', 'manage_task');
        }
        if (['update', 'get', 'delete', 'complete'].includes(params.action) && !params.task_id) {
          throw new McpApiError('task_id is required for this action', 'MISSING_REQUIRED_PARAM', 'manage_task');
        }
        if (['add_dependency', 'remove_dependency'].includes(params.action) && (!params.task_id || !params.dependency_id)) {
          throw new McpApiError('task_id and dependency_id are required for dependency actions', 'MISSING_REQUIRED_PARAM', 'manage_task');
        }
      },

      'manage_subtask': (params) => {
        if (!params.action || !params.task_id) {
          throw new McpApiError('action and task_id parameters are required', 'MISSING_REQUIRED_PARAM', 'manage_subtask');
        }
        if (['update', 'get', 'delete', 'complete'].includes(params.action) && !params.subtask_id) {
          throw new McpApiError('subtask_id is required for this action', 'MISSING_REQUIRED_PARAM', 'manage_subtask');
        }
        if (params.action === 'create' && !params.title) {
          throw new McpApiError('title is required for create action', 'MISSING_REQUIRED_PARAM', 'manage_subtask');
        }
      },

      'manage_context': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_context');
        }
        if (['create', 'get', 'update', 'delete'].includes(params.action) && !params.task_id) {
          throw new McpApiError('task_id is required for this action', 'MISSING_REQUIRED_PARAM', 'manage_context');
        }
      },

      'manage_hierarchical_context': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_hierarchical_context');
        }
        if (['resolve', 'update', 'create', 'delegate'].includes(params.action) && !params.context_id) {
          throw new McpApiError('context_id is required for this action', 'MISSING_REQUIRED_PARAM', 'manage_hierarchical_context');
        }
      },

      'validate_context_inheritance': (params) => {
        if (!params.level || !params.context_id) {
          throw new McpApiError('level and context_id parameters are required', 'MISSING_REQUIRED_PARAM', 'validate_context_inheritance');
        }
        if (!['project', 'task'].includes(params.level)) {
          throw new McpApiError('level must be "project" or "task"', 'INVALID_PARAM_VALUE', 'validate_context_inheritance');
        }
      },

      'manage_delegation_queue': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_delegation_queue');
        }
        if (['approve', 'reject'].includes(params.action) && !params.delegation_id) {
          throw new McpApiError('delegation_id is required for approve/reject actions', 'MISSING_REQUIRED_PARAM', 'manage_delegation_queue');
        }
      },

      'manage_compliance': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_compliance');
        }
        if (params.action === 'validate_compliance' && !params.operation) {
          throw new McpApiError('operation is required for validate_compliance action', 'MISSING_REQUIRED_PARAM', 'manage_compliance');
        }
        if (params.action === 'execute_with_compliance' && !params.command) {
          throw new McpApiError('command is required for execute_with_compliance action', 'MISSING_REQUIRED_PARAM', 'manage_compliance');
        }
      },

      'manage_connection': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_connection');
        }
        if (params.action === 'register_updates' && !params.session_id) {
          throw new McpApiError('session_id is required for register_updates action', 'MISSING_REQUIRED_PARAM', 'manage_connection');
        }
      },

      'manage_rule': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_rule');
        }
      },

      'manage_project': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_project');
        }
        if (params.action === 'create' && !params.name) {
          throw new McpApiError('name is required for create action', 'MISSING_REQUIRED_PARAM', 'manage_project');
        }
        if (['get', 'update', 'project_health_check', 'cleanup_obsolete', 'validate_integrity', 'rebalance_agents'].includes(params.action) && !params.project_id) {
          throw new McpApiError('project_id is required for this action', 'MISSING_REQUIRED_PARAM', 'manage_project');
        }
      },

      'manage_git_branch': (params) => {
        if (!params.action) {
          throw new McpApiError('action parameter is required', 'MISSING_REQUIRED_PARAM', 'manage_git_branch');
        }
        if (params.action === 'create' && (!params.project_id || !params.git_branch_name)) {
          throw new McpApiError('project_id and git_branch_name are required for create action', 'MISSING_REQUIRED_PARAM', 'manage_git_branch');
        }
        if (['assign_agent', 'unassign_agent'].includes(params.action) && (!params.project_id || !params.agent_id)) {
          throw new McpApiError('project_id and agent_id are required for agent assignment actions', 'MISSING_REQUIRED_PARAM', 'manage_git_branch');
        }
      }
    };

    // Apply validation if rule exists
    const validator = validationRules[toolName];
    if (validator) {
      validator(args);
    }

    // General parameter type validation
    if (args.priority && !['low', 'medium', 'high', 'urgent', 'critical'].includes(args.priority)) {
      throw new McpApiError('Invalid priority value', 'INVALID_PARAM_VALUE', toolName);
    }

    if (args.status && !['todo', 'in_progress', 'blocked', 'review', 'testing', 'done', 'cancelled'].includes(args.status)) {
      throw new McpApiError('Invalid status value', 'INVALID_PARAM_VALUE', toolName);
    }

    if (args.security_level && !['public', 'internal', 'restricted', 'confidential', 'secret'].includes(args.security_level)) {
      throw new McpApiError('Invalid security_level value', 'INVALID_PARAM_VALUE', toolName);
    }

    if (args.level && !['global', 'project', 'task'].includes(args.level)) {
      throw new McpApiError('Invalid level value', 'INVALID_PARAM_VALUE', toolName);
    }
  }

  /**
   * Core MCP protocol request method with comprehensive error handling
   */
  private async makeRequest<T>(toolName: string, args: any, options: RequestOptions = {}): Promise<McpResponse<T>> {
    // Create cache key for read-only operations
    const cacheKey = this.getCacheKey(toolName, args);
    const isCacheable = this.isCacheableRequest(toolName, args);
    
    // Check cache for GET-like operations
    if (isCacheable) {
      const cached = this.requestCache.get(cacheKey);
      if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
        console.log(`Cache hit for ${toolName}:${args.action || ''}`);
        return cached.data;
      }
      
      // Check if there's already a pending request for the same data
      const pending = this.pendingRequests.get(cacheKey);
      if (pending) {
        console.log(`Deduplicating request for ${toolName}:${args.action || ''}`);
        return pending;
      }
    }

    const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    const startTime = Date.now();

    // Validate parameters before making request
    this.validateToolParameters(toolName, args);

    // Add to request queue for monitoring
    this.requestQueue.push({ id: requestId, timestamp: startTime });
    this.performanceMetrics.queueLength = this.requestQueue.length;

    // Create promise for deduplication
    const requestPromise = (async () => {
      try {
        const result = await this.circuitBreaker.execute(async () => {
        const body = {
          jsonrpc: "2.0",
          method: "tools/call",
          params: {
            name: toolName,
            arguments: args
          },
          id: this.getRpcId(),
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || config.mcp.timeout);

        try {
          const response = await fetch(this.baseUrl, {
            method: "POST",
            headers: { ...this.headers, ...options.headers },
            body: JSON.stringify(body),
            signal: controller.signal
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new McpApiError(
              `HTTP ${response.status}: ${response.statusText}`,
              'HTTP_ERROR',
              toolName,
              { status: response.status, statusText: response.statusText },
              response.status >= 500 // Server errors are retryable
            );
          }

          const data = await response.json();
          
          // Handle MCP protocol errors
          if (data.error) {
            throw new McpApiError(
              data.error.message || 'MCP protocol error',
              data.error.code || 'MCP_ERROR',
              toolName,
              data.error,
              false // Protocol errors are typically not retryable
            );
          }

          // Parse tool result
          if (data.result?.content?.[0]?.text) {
            try {
              const toolResult = JSON.parse(data.result.content[0].text);
              return {
                success: toolResult.success || false,
                data: toolResult,
                metadata: {
                  requestId,
                  responseTime: Date.now() - startTime,
                  toolName
                }
              };
            } catch (parseError) {
              throw new McpApiError(
                'Failed to parse tool result',
                'PARSE_ERROR',
                toolName,
                { parseError, rawData: data.result.content[0].text }
              );
            }
          }

          return {
            success: false,
            error: 'No tool result in response',
            metadata: {
              requestId,
              responseTime: Date.now() - startTime,
              toolName
            }
          };

        } catch (error: unknown) {
          clearTimeout(timeoutId);
          
          if (error instanceof Error && error.name === 'AbortError') {
            throw new McpApiError(
              'Request timeout',
              'TIMEOUT',
              toolName,
              { timeout: options.timeout || 30000 },
              true
            );
          }
          
          throw error;
        }
      });
      
      // Cache successful results
      if (isCacheable) {
        this.requestCache.set(cacheKey, { data: result, timestamp: Date.now() });
        // Clean old cache entries
        this.cleanCache();
      }
      
      return result;
    } catch (error: unknown) {
      this.updatePerformanceMetrics(startTime, false);
      throw await this.handleApiError(error, toolName);
    } finally {
      // Remove from queue and pending requests
      this.requestQueue = this.requestQueue.filter(req => req.id !== requestId);
      this.performanceMetrics.queueLength = this.requestQueue.length;
      if (isCacheable) {
        this.pendingRequests.delete(cacheKey);
      }
      
      this.updatePerformanceMetrics(startTime, true);
    }
  })();

  // Store pending request for deduplication
  if (isCacheable) {
    this.pendingRequests.set(cacheKey, requestPromise);
  }
  
  return requestPromise;
}

  /**
   * Comprehensive error classification and handling
   */
  private async handleApiError(error: unknown, operation: string): Promise<never> {
    if (error instanceof McpApiError) {
      throw error;
    }

    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new McpApiError(
        'Network connection failed',
        'NETWORK_ERROR',
        operation,
        { originalError: error.message },
        true
      );
    }

    // Rate limiting detection
    if (error && typeof error === 'object' && 'status' in error && error.status === 429) {
      const retryAfter = (error as any).headers?.['retry-after'] || 60;
      throw new McpApiError(
        'Rate limit exceeded',
        'RATE_LIMIT',
        operation,
        { retryAfter },
        true
      );
    }

    // Default error
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    throw new McpApiError(
      errorMessage,
      'UNKNOWN_ERROR',
      operation,
      { originalError: error },
      false
    );
  }

  /**
   * Retry logic with exponential backoff
   */
  private async retryRequest<T>(
    fn: () => Promise<T>, 
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: Error = new Error('Unknown retry error');

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: unknown) {
        lastError = error as Error;

        // Don't retry if error is not retryable
        if (error instanceof McpApiError && !error.retryable) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt === maxRetries) {
          break;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError;
  }

  /**
   * Update performance metrics
   */
  private updatePerformanceMetrics(startTime: number, success: boolean): void {
    const responseTime = Date.now() - startTime;
    
    this.performanceMetrics.requestCount++;
    if (success) {
      this.performanceMetrics.successCount++;
    } else {
      this.performanceMetrics.errorCount++;
    }

    // Update rolling average response time
    const totalResponseTime = this.performanceMetrics.averageResponseTime * (this.performanceMetrics.requestCount - 1);
    this.performanceMetrics.averageResponseTime = (totalResponseTime + responseTime) / this.performanceMetrics.requestCount;

    // Update memory usage if available
    if (typeof window !== 'undefined' && 'performance' in window && 'memory' in (window.performance as any)) {
      this.performanceMetrics.memoryUsage = (window.performance as any).memory.usedJSHeapSize;
    }
  }

  /**
   * Clean expired cache entries
   */
  private cleanCache(): void {
    const now = Date.now();
    const entriesToDelete: string[] = [];
    
    this.requestCache.forEach((value, key) => {
      if (now - value.timestamp > this.cacheTimeout) {
        entriesToDelete.push(key);
      }
    });
    
    entriesToDelete.forEach(key => this.requestCache.delete(key));
  }

  // Public API methods

  /**
   * Execute a tool with automatic retry and error handling
   */
  public async executeToolWithRetry<T>(
    toolName: string,
    args: any,
    options: RequestOptions = {}
  ): Promise<McpResponse<T>> {
    const maxRetries = options.retries || config.mcp.retries;
    
    return this.retryRequest(
      () => this.makeRequest<T>(toolName, args, options),
      maxRetries
    );
  }

  /**
   * Execute a tool without retry (for operations that should not be retried)
   */
  public async executeTool<T>(
    toolName: string,
    args: any,
    options: RequestOptions = {}
  ): Promise<McpResponse<T>> {
    return this.makeRequest<T>(toolName, args, options);
  }


  /**
   * Reset performance metrics
   */
  public resetPerformanceMetrics(): void {
    this.performanceMetrics = {
      requestCount: 0,
      successCount: 0,
      errorCount: 0,
      averageResponseTime: 0,
      queueLength: this.requestQueue.length
    };
  }

  /**
   * Health check method
   */
  public async healthCheck(): Promise<boolean> {
    try {
      const result = await this.executeTool('manage_connection', { action: 'health_check' });
      return result.success;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get circuit breaker status
   */
  public getCircuitBreakerStatus(): { state: string; failures: number } {
    return {
      state: (this.circuitBreaker as any).state,
      failures: (this.circuitBreaker as any).failures
    };
  }

  // ===== ALL 23 MCP TOOL METHODS =====

  // --- Agent Management (2 tools) ---
  
  /**
   * Call/invoke a specific agent by name
   */
  async callAgent(agentName: string): Promise<McpResponse<AgentCallResponse>> {
    return this.executeToolWithRetry('call_agent', { name_agent: agentName });
  }

  /**
   * Manage agent operations (register, assign, list, update, etc.)
   */
  async manageAgent(action: string, params: AgentParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_agent', { action, ...params });
  }

  // --- Context Management (4 tools) ---
  
  /**
   * Manage context operations (create, get, update, delete, etc.)
   */
  async manageContext(action: string, params: ContextParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_context', { action, ...params });
  }

  /**
   * Manage hierarchical context with inheritance
   */
  async manageHierarchicalContext(action: string, params: HierarchicalParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_hierarchical_context', { action, ...params });
  }

  /**
   * Validate context inheritance chain
   */
  async validateContextInheritance(level: string, contextId: string): Promise<McpResponse<ContextInheritanceValidation>> {
    return this.executeToolWithRetry('validate_context_inheritance', { level, context_id: contextId });
  }

  /**
   * Manage delegation queue operations
   */
  async manageDelegationQueue(action: string, params: DelegationParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_delegation_queue', { action, ...params });
  }

  // --- System Operations (3 tools) ---
  
  /**
   * Manage compliance operations (validate, audit, execute with compliance)
   */
  async manageCompliance(action: string, params: ComplianceParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_compliance', { action, ...params });
  }

  /**
   * Manage connection operations (health check, capabilities, status)
   */
  async manageConnection(action: string, params: ConnectionParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_connection', { action, ...params });
  }

  /**
   * Manage rule operations (list, info, hierarchy, sync, etc.)
   */
  async manageRule(action: string, params: RuleParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_rule', { action, ...params });
  }

  // --- Project & Branch Management (2 tools) ---
  
  /**
   * Manage project operations (create, get, list, update, health check, etc.)
   */
  async manageProject(action: string, params: ProjectParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_project', { action, ...params });
  }

  /**
   * Manage git branch operations (create, get, list, assign agents, etc.)
   */
  async manageGitBranch(action: string, params: BranchParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_git_branch', { action, ...params });
  }

  // --- Task Management (2 tools) ---
  
  /**
   * Manage task operations (create, get, list, update, complete, dependencies, etc.)
   */
  async manageTask(action: string, params: TaskParams = {}): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_task', { action, ...params });
  }

  /**
   * Manage subtask operations (create, get, list, update, complete, etc.)
   */
  async manageSubtask(action: string, params: SubtaskParams): Promise<McpResponse<any>> {
    return this.executeToolWithRetry('manage_subtask', { action, ...params });
  }

  // ===== CONVENIENCE METHODS FOR COMMON OPERATIONS =====
  
  // --- Agent Convenience Methods ---
  
  /**
   * Get all agents for a project
   */
  async getAgents(projectId?: string): Promise<Agent[]> {
    const result = await this.manageAgent('list', { project_id: projectId });
    return result.data?.agents || [];
  }

  /**
   * Register a new agent
   */
  async registerAgent(projectId: string, name: string, callAgent?: string): Promise<Agent | null> {
    const result = await this.manageAgent('register', { 
      project_id: projectId, 
      name, 
      call_agent: callAgent 
    });
    return result.data?.agent || null;
  }

  /**
   * Assign agent to a branch
   */
  async assignAgentToBranch(projectId: string, agentId: string, branchId: string): Promise<boolean> {
    const result = await this.manageAgent('assign', { 
      project_id: projectId, 
      agent_id: agentId, 
      git_branch_id: branchId 
    });
    return result.success;
  }

  // --- Context Convenience Methods ---
  
  /**
   * Resolve task context with full inheritance
   */
  async resolveTaskContext(taskId: string, forceRefresh: boolean = false): Promise<any> {
    const result = await this.manageHierarchicalContext('resolve', { 
      level: 'task', 
      context_id: taskId, 
      force_refresh: forceRefresh 
    });
    return result.data?.resolved_context || null;
  }

  /**
   * Update task context data
   */
  async updateTaskContext(taskId: string, data: Record<string, any>, propagate: boolean = true): Promise<boolean> {
    const result = await this.manageHierarchicalContext('update', {
      level: 'task',
      context_id: taskId,
      data,
      propagate_changes: propagate
    });
    return result.success;
  }

  /**
   * Delegate context data to project level
   */
  async delegateToProject(taskId: string, data: Record<string, any>, reason: string): Promise<boolean> {
    const result = await this.manageHierarchicalContext('delegate', {
      level: 'task',
      context_id: taskId,
      delegate_to: 'project',
      delegate_data: data,
      delegation_reason: reason
    });
    return result.success;
  }

  // --- System Convenience Methods ---
  
  /**
   * Enhanced health check with details
   */
  async getSystemHealth(includeDetails: boolean = true): Promise<ConnectionStatus | null> {
    const result = await this.manageConnection('health_check', { include_details: includeDetails });
    return result.data?.status || null;
  }

  /**
   * Get server capabilities
   */
  async getServerCapabilities(): Promise<any> {
    const result = await this.manageConnection('server_capabilities');
    return result.data?.capabilities || null;
  }

  /**
   * Validate operation for compliance
   */
  async validateOperation(operation: string, filePath?: string, content?: string): Promise<ComplianceStatus | null> {
    const result = await this.manageCompliance('validate_compliance', {
      operation,
      file_path: filePath,
      content,
      security_level: 'public'
    });
    return result.data || null;
  }

  /**
   * Get rule hierarchy
   */
  async getRuleHierarchy(): Promise<any> {
    const result = await this.manageRule('analyze_hierarchy');
    return result.data?.hierarchy || null;
  }

  /**
   * Sync rules with client
   */
  async syncRules(clientId?: string): Promise<boolean> {
    const result = await this.manageRule('sync_client', { target: clientId });
    return result.success;
  }

  // --- Project Convenience Methods ---
  
  /**
   * Get all projects
   */
  async getProjects(): Promise<Project[]> {
    const result = await this.manageProject('list');
    return result.data?.projects || [];
  }

  /**
   * Create a new project
   */
  async createProject(name: string, description?: string): Promise<Project | null> {
    const result = await this.manageProject('create', { name, description });
    return result.data?.project || null;
  }

  /**
   * Get project health metrics
   */
  async getProjectHealth(projectId: string): Promise<any> {
    const result = await this.manageProject('project_health_check', { project_id: projectId });
    return result.data || null;
  }

  /**
   * Rebalance agents across project
   */
  async rebalanceProjectAgents(projectId: string): Promise<boolean> {
    const result = await this.manageProject('rebalance_agents', { project_id: projectId });
    return result.success;
  }

  // --- Branch Convenience Methods ---
  
  /**
   * Get branch statistics
   */
  async getBranchStatistics(projectId: string, branchId: string): Promise<any> {
    const result = await this.manageGitBranch('get_statistics', { 
      project_id: projectId, 
      git_branch_id: branchId 
    });
    return result.data || null;
  }

  /**
   * Archive a branch
   */
  async archiveBranch(projectId: string, branchId: string): Promise<boolean> {
    const result = await this.manageGitBranch('archive', { 
      project_id: projectId, 
      git_branch_id: branchId 
    });
    return result.success;
  }

  /**
   * Create a new branch
   */
  async createBranch(projectId: string, branchName: string, description?: string): Promise<any> {
    const result = await this.manageGitBranch('create', {
      project_id: projectId,
      git_branch_name: branchName,
      git_branch_description: description
    });
    return result.data?.git_branch || null;
  }

  // --- Task Convenience Methods ---
  
  /**
   * Get next recommended task
   */
  async getNextTask(branchId: string, includeContext: boolean = true): Promise<Task | null> {
    const result = await this.manageTask('next', { 
      git_branch_id: branchId, 
      include_context: includeContext 
    });
    return result.data?.task || null;
  }

  /**
   * Search tasks
   */
  async searchTasks(query: string, branchId?: string, limit: number = 50): Promise<Task[]> {
    const result = await this.manageTask('search', { 
      query, 
      git_branch_id: branchId, 
      limit 
    });
    return result.data?.tasks || [];
  }

  /**
   * Get all tasks for a branch
   */
  async getTasks(branchId?: string): Promise<Task[]> {
    const result = await this.manageTask('list', { git_branch_id: branchId });
    return result.data?.tasks || [];
  }

  /**
   * Create a new task
   */
  async createTask(branchId: string, title: string, description?: string, priority: string = 'medium'): Promise<Task | null> {
    const result = await this.manageTask('create', {
      git_branch_id: branchId,
      title,
      description,
      priority
    });
    return result.data?.task || null;
  }

  /**
   * Complete a task
   */
  async completeTask(taskId: string, summary: string, testingNotes?: string): Promise<boolean> {
    const result = await this.manageTask('complete', { 
      task_id: taskId, 
      completion_summary: summary, 
      testing_notes: testingNotes 
    });
    return result.success;
  }

  /**
   * Add task dependency
   */
  async addTaskDependency(taskId: string, dependencyId: string): Promise<boolean> {
    const result = await this.manageTask('add_dependency', { 
      task_id: taskId, 
      dependency_id: dependencyId 
    });
    return result.success;
  }

  // --- Subtask Convenience Methods ---
  
  /**
   * Get all subtasks for a task
   */
  async getSubtasks(taskId: string): Promise<any[]> {
    const result = await this.manageSubtask('list', { task_id: taskId });
    return result.data?.subtasks || [];
  }

  /**
   * Create a new subtask
   */
  async createSubtask(taskId: string, title: string, description?: string): Promise<any> {
    const result = await this.manageSubtask('create', { 
      task_id: taskId, 
      title, 
      description 
    });
    return result.data?.subtask || null;
  }

  /**
   * Update subtask progress
   */
  async updateSubtaskProgress(taskId: string, subtaskId: string, percentage: number, notes?: string): Promise<boolean> {
    const result = await this.manageSubtask('update', {
      task_id: taskId,
      subtask_id: subtaskId,
      progress_percentage: percentage,
      progress_notes: notes
    });
    return result.success;
  }

  /**
   * Complete a subtask
   */
  async completeSubtask(taskId: string, subtaskId: string, summary: string, impact?: string): Promise<boolean> {
    const result = await this.manageSubtask('complete', {
      task_id: taskId,
      subtask_id: subtaskId,
      completion_summary: summary,
      impact_on_parent: impact
    });
    return result.success;
  }

  // --- Rule Convenience Methods ---
  
  /**
   * Get all rules
   */
  async getRules(): Promise<Rule[]> {
    const result = await this.manageRule('list');
    return result.data?.rules || [];
  }

  /**
   * Create a new rule
   */
  async createRule(ruleData: Partial<Rule>): Promise<Rule | null> {
    const result = await this.manageRule('create', { 
      target: ruleData.name,
      content: JSON.stringify(ruleData)
    });
    return result.data?.rule || null;
  }

  /**
   * Update an existing rule
   */
  async updateRule(ruleId: string, ruleData: Partial<Rule>): Promise<Rule | null> {
    const result = await this.manageRule('update', { 
      target: ruleId,
      content: JSON.stringify(ruleData)
    });
    return result.data?.rule || null;
  }

  /**
   * Delete a rule
   */
  async deleteRule(ruleId: string): Promise<boolean> {
    const result = await this.manageRule('delete', { target: ruleId });
    return result.success;
  }

  /**
   * Validate a rule
   */
  async validateRule(ruleId: string): Promise<any> {
    const result = await this.manageRule('validate', { target: ruleId });
    return result.data?.validation || { success: false, error: 'Validation failed' };
  }

  /**
   * Get current performance metrics
   */
  getPerformanceMetrics(): PerformanceMetrics {
    return { ...this.performanceMetrics };
  }

  /**
   * Clear all cached requests
   */
  clearCache(): void {
    this.requestCache.clear();
    console.log('API cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; entries: string[] } {
    return {
      size: this.requestCache.size,
      entries: Array.from(this.requestCache.keys())
    };
  }
}

// Export default instance
export const mcpApi = new McpApiWrapper();

// Export convenience functions for direct use
export const listRules = () => mcpApi.getRules();
export const createRule = (ruleData: Partial<Rule>) => mcpApi.createRule(ruleData);
export const updateRule = (ruleId: string, ruleData: Partial<Rule>) => mcpApi.updateRule(ruleId, ruleData);
export const deleteRule = (ruleId: string) => mcpApi.deleteRule(ruleId);
export const validateRule = (ruleId: string) => mcpApi.validateRule(ruleId);

// Tool-specific interfaces (extending existing types)
export interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  subtasks?: Subtask[];
  [key: string]: any;
}

export interface Subtask {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  [key: string]: any;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  task_trees?: Record<string, Branch>;
}

export interface Branch {
  id: string;
  name: string;
  description: string;
}

export interface Rule {
  id: string;
  name: string;
  description?: string;
  type?: string;
  content?: string;
  [key: string]: any;
}

// --- Additional Type Definitions for MCP Tools ---

export interface Agent {
  id: string;
  name: string;
  project_id: string;
  call_agent?: string;
  status: 'active' | 'idle' | 'busy' | 'error';
}

export interface AgentCallResponse {
  success: boolean;
  agent_info: any;
  capabilities: any;
}

export interface HierarchicalContext {
  id: string;
  level: 'global' | 'project' | 'task';
  context_id: string;
  data: Record<string, any>;
  inheritance_chain: string[];
}

export interface ContextInheritanceValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  inheritance_chain: string[];
  cache_metrics?: any;
  resolution_timing?: any;
}

export interface ConnectionStatus {
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  last_check: string;
}

export interface ComplianceStatus {
  compliance_score: number;
  violations: ComplianceViolation[];
}

export interface ComplianceViolation {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  remediation?: string;
}

// Parameter interfaces for type safety
export interface AgentParams {
  project_id?: string;
  agent_id?: string;
  name?: string;
  call_agent?: string;
  git_branch_id?: string;
}

export interface ContextParams {
  task_id?: string;
  user_id?: string;
  project_id?: string;
  git_branch_name?: string;
  property_path?: string;
  value?: any;
  content?: string;
  agent?: string;
  category?: string;
  importance?: string;
  next_steps?: string[] | string;
  [key: string]: any;
}

export interface HierarchicalParams {
  level?: string;
  context_id?: string;
  data?: Record<string, any>;
  delegate_to?: string;
  delegate_data?: Record<string, any>;
  delegation_reason?: string;
  force_refresh?: boolean;
  propagate_changes?: boolean;
}

export interface DelegationParams {
  delegation_id?: string;
  rejection_reason?: string;
  target_level?: string;
  target_id?: string;
}

export interface ComplianceParams {
  operation?: string;
  file_path?: string;
  content?: string;
  user_id?: string;
  security_level?: string;
  audit_required?: boolean;
  command?: string;
  timeout?: number;
  limit?: number;
}

export interface ConnectionParams {
  include_details?: boolean;
  session_id?: string;
  connection_id?: string;
  client_info?: Record<string, any>;
}

export interface RuleParams {
  target?: string;
  content?: string;
}

export interface ProjectParams {
  project_id?: string;
  name?: string;
  description?: string;
  user_id?: string;
  force?: boolean;
}

export interface BranchParams {
  project_id?: string;
  git_branch_id?: string;
  git_branch_name?: string;
  git_branch_description?: string;
  agent_id?: string;
}

export interface TaskParams {
  task_id?: string;
  git_branch_id?: string;
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  details?: string;
  estimated_effort?: string;
  assignees?: string[] | string;
  labels?: string[] | string;
  due_date?: string;
  dependencies?: string[] | string;
  dependency_id?: string;
  completion_summary?: string;
  testing_notes?: string;
  include_context?: boolean;
  limit?: number;
  query?: string;
  context_id?: string;
  force_full_generation?: boolean;
}

export interface SubtaskParams {
  task_id: string;
  subtask_id?: string;
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  assignees?: string[];
  progress_notes?: string;
  progress_percentage?: number;
  blockers?: string;
  completion_summary?: string;
  impact_on_parent?: string;
  insights_found?: string[];
}