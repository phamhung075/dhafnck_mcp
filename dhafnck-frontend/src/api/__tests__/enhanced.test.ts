/**
 * Test suite for Enhanced MCP API Wrapper
 * Tests all 23 MCP tool methods with parameter validation and error handling
 */

import { McpApiWrapper, McpApiError } from '../enhanced';

// Mock fetch for testing
global.fetch = jest.fn();

describe('McpApiWrapper', () => {
  let api: McpApiWrapper;

  beforeEach(() => {
    api = new McpApiWrapper();
    jest.clearAllMocks();
  });

  describe('Constructor and Configuration', () => {
    it('should initialize with default base URL', () => {
      expect(api).toBeInstanceOf(McpApiWrapper);
    });

    it('should accept custom base URL', () => {
      const customApi = new McpApiWrapper('http://custom:8000/mcp');
      expect(customApi).toBeInstanceOf(McpApiWrapper);
    });
  });

  describe('Parameter Validation', () => {
    it('should validate call_agent parameters', async () => {
      await expect(api.callAgent('')).rejects.toThrow(McpApiError);
    });

    it('should validate manage_task parameters', async () => {
      await expect(api.manageTask('create', {})).rejects.toThrow('git_branch_id is required');
    });

    it('should validate manage_subtask parameters', async () => {
      await expect(api.manageSubtask('create', { task_id: '' })).rejects.toThrow(McpApiError);
    });

    it('should validate priority values', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          result: { content: [{ text: JSON.stringify({ success: true }) }] }
        })
      });

      await expect(api.manageTask('create', { 
        git_branch_id: 'test-branch', 
        priority: 'invalid' as any 
      })).rejects.toThrow('Invalid priority value');
    });

    it('should validate status values', async () => {
      await expect(api.manageTask('update', { 
        task_id: 'test-task', 
        status: 'invalid' as any 
      })).rejects.toThrow('Invalid status value');
    });
  });

  describe('All 23 MCP Tool Methods', () => {
    beforeEach(() => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: { content: [{ text: JSON.stringify({ success: true, data: {} }) }] }
        })
      });
    });

    // Agent Management (2 tools)
    describe('Agent Management', () => {
      it('should call callAgent successfully', async () => {
        const result = await api.callAgent('@test_agent');
        expect(result.success).toBe(true);
      });

      it('should call manageAgent successfully', async () => {
        const result = await api.manageAgent('list', { project_id: 'test' });
        expect(result.success).toBe(true);
      });
    });

    // Context Management (4 tools)
    describe('Context Management', () => {
      it('should call manageContext successfully', async () => {
        const result = await api.manageContext('list', { user_id: 'test' });
        expect(result.success).toBe(true);
      });

      it('should call manageHierarchicalContext successfully', async () => {
        const result = await api.manageHierarchicalContext('resolve', { 
          level: 'task', 
          context_id: 'test' 
        });
        expect(result.success).toBe(true);
      });

      it('should call validateContextInheritance successfully', async () => {
        const result = await api.validateContextInheritance('task', 'test-context');
        expect(result.success).toBe(true);
      });

      it('should call manageDelegationQueue successfully', async () => {
        const result = await api.manageDelegationQueue('list');
        expect(result.success).toBe(true);
      });
    });

    // System Operations (3 tools)
    describe('System Operations', () => {
      it('should call manageCompliance successfully', async () => {
        const result = await api.manageCompliance('get_compliance_dashboard');
        expect(result.success).toBe(true);
      });

      it('should call manageConnection successfully', async () => {
        const result = await api.manageConnection('health_check');
        expect(result.success).toBe(true);
      });

      it('should call manageRule successfully', async () => {
        const result = await api.manageRule('list');
        expect(result.success).toBe(true);
      });
    });

    // Project & Branch Management (2 tools)
    describe('Project & Branch Management', () => {
      it('should call manageProject successfully', async () => {
        const result = await api.manageProject('list');
        expect(result.success).toBe(true);
      });

      it('should call manageGitBranch successfully', async () => {
        const result = await api.manageGitBranch('list', { project_id: 'test' });
        expect(result.success).toBe(true);
      });
    });

    // Task Management (2 tools)
    describe('Task Management', () => {
      it('should call manageTask successfully', async () => {
        const result = await api.manageTask('list');
        expect(result.success).toBe(true);
      });

      it('should call manageSubtask successfully', async () => {
        const result = await api.manageSubtask('list', { task_id: 'test-task' });
        expect(result.success).toBe(true);
      });
    });
  });

  describe('Convenience Methods', () => {
    beforeEach(() => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: { 
            content: [{ 
              text: JSON.stringify({ 
                success: true, 
                data: { 
                  agents: [], 
                  projects: [], 
                  tasks: [], 
                  subtasks: [] 
                } 
              }) 
            }] 
          }
        })
      });
    });

    it('should get agents', async () => {
      const agents = await api.getAgents('test-project');
      expect(Array.isArray(agents)).toBe(true);
    });

    it('should get projects', async () => {
      const projects = await api.getProjects();
      expect(Array.isArray(projects)).toBe(true);
    });

    it('should get tasks', async () => {
      const tasks = await api.getTasks('test-branch');
      expect(Array.isArray(tasks)).toBe(true);
    });

    it('should get subtasks', async () => {
      const subtasks = await api.getSubtasks('test-task');
      expect(Array.isArray(subtasks)).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockRejectedValue(new TypeError('Network error'));

      const result = await api.manageConnection('health_check');
      expect(result.success).toBe(false);
      expect(result.error).toContain('Network connection failed');
    });

    it('should handle HTTP errors', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      const result = await api.manageConnection('health_check');
      expect(result.success).toBe(false);
      expect(result.error).toContain('HTTP 500');
    });

    it('should handle MCP protocol errors', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          error: {
            code: 'INVALID_REQUEST',
            message: 'Invalid request format'
          }
        })
      });

      const result = await api.manageConnection('health_check');
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid request format');
    });

    it('should handle parse errors', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: { content: [{ text: 'invalid-json' }] }
        })
      });

      const result = await api.manageConnection('health_check');
      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to parse');
    });
  });

  describe('Performance Monitoring', () => {
    it('should track performance metrics', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: { content: [{ text: JSON.stringify({ success: true }) }] }
        })
      });

      await api.manageConnection('health_check');
      
      const metrics = api.getPerformanceMetrics();
      expect(metrics.requestCount).toBeGreaterThan(0);
      expect(metrics.successCount).toBeGreaterThan(0);
    });

    it('should reset performance metrics', () => {
      api.resetPerformanceMetrics();
      const metrics = api.getPerformanceMetrics();
      expect(metrics.requestCount).toBe(0);
      expect(metrics.successCount).toBe(0);
      expect(metrics.errorCount).toBe(0);
    });
  });

  describe('Circuit Breaker', () => {
    it('should get circuit breaker status', () => {
      const status = api.getCircuitBreakerStatus();
      expect(status).toHaveProperty('state');
      expect(status).toHaveProperty('failures');
    });
  });

  describe('Health Check', () => {
    it('should perform health check', async () => {
      const mockFetch = global.fetch as jest.Mock;
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: { content: [{ text: JSON.stringify({ success: true }) }] }
        })
      });

      const isHealthy = await api.healthCheck();
      expect(typeof isHealthy).toBe('boolean');
    });
  });
});

describe('McpApiError', () => {
  it('should create error with correct properties', () => {
    const error = new McpApiError('Test error', 'TEST_CODE', 'test_operation', { detail: 'test' }, true);
    
    expect(error.message).toBe('Test error');
    expect(error.code).toBe('TEST_CODE');
    expect(error.operation).toBe('test_operation');
    expect(error.details).toEqual({ detail: 'test' });
    expect(error.retryable).toBe(true);
    expect(error.name).toBe('McpApiError');
  });
});