import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import Cookies from 'js-cookie';
import {
  taskApiV2,
  projectApiV2,
  agentApiV2,
  isAuthenticated,
  getCurrentUserId
} from '../../services/apiV2';

// Mock js-cookie
vi.mock('js-cookie', () => ({
  default: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn()
  }
}));

// Mock fetch globally
global.fetch = vi.fn();

// Mock process.env
vi.mock('process', () => ({
  env: {
    REACT_APP_API_URL: 'http://test-api.com'
  }
}));

describe('apiV2.ts', () => {
  const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInVzZXJfaWQiOiJ1c2VyLTEyMyIsIm5hbWUiOiJUZXN0IFVzZXIiLCJpYXQiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockReset();
    (Cookies.get as any).mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Authentication Helpers', () => {
    describe('isAuthenticated', () => {
      it('should return true when token exists', () => {
        (Cookies.get as any).mockReturnValue(mockToken);

        const result = isAuthenticated();

        expect(result).toBe(true);
        expect(Cookies.get).toHaveBeenCalledWith('access_token');
      });

      it('should return false when token does not exist', () => {
        (Cookies.get as any).mockReturnValue(null);

        const result = isAuthenticated();

        expect(result).toBe(false);
      });
    });

    describe('getCurrentUserId', () => {
      it('should extract user ID from JWT token', () => {
        (Cookies.get as any).mockReturnValue(mockToken);

        const userId = getCurrentUserId();

        expect(userId).toBe('user-123');
      });

      it('should return null when no token exists', () => {
        (Cookies.get as any).mockReturnValue(null);

        const userId = getCurrentUserId();

        expect(userId).toBeNull();
      });

      it('should return null for invalid token format', () => {
        (Cookies.get as any).mockReturnValue('invalid-token');

        const userId = getCurrentUserId();

        expect(userId).toBeNull();
      });

      it('should handle malformed JWT payload', () => {
        (Cookies.get as any).mockReturnValue('header.invalidbase64.signature');

        const userId = getCurrentUserId();

        expect(userId).toBeNull();
      });

      it('should use user_id field if sub is not present', () => {
        const tokenWithUserId = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlci00NTYiLCJuYW1lIjoiVGVzdCBVc2VyIiwiaWF0IjoxNTE2MjM5MDIyfQ.vYD6h5b8_3olg6eKvLkYLpH6hR-WzG65P0-qGLKNc7M';
        (Cookies.get as any).mockReturnValue(tokenWithUserId);

        const userId = getCurrentUserId();

        expect(userId).toBe('user-456');
      });
    });
  });

  describe('Task API V2', () => {
    beforeEach(() => {
      (Cookies.get as any).mockReturnValue(mockToken);
    });

    describe('getTasks', () => {
      it('should fetch tasks with authentication', async () => {
        const mockTasks = [
          { id: '1', title: 'Task 1' },
          { id: '2', title: 'Task 2' }
        ];
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockTasks)
        });

        const result = await taskApiV2.getTasks();

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/tasks/',
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockTasks);
      });

      it('should handle 401 authentication error', async () => {
        (global.fetch as any).mockResolvedValue({
          ok: false,
          status: 401,
          json: vi.fn().mockResolvedValue({ detail: 'Token expired' })
        });

        await expect(taskApiV2.getTasks()).rejects.toThrow('Authentication required. Please log in again.');
      });

      it('should handle generic errors', async () => {
        (global.fetch as any).mockResolvedValue({
          ok: false,
          status: 500,
          json: vi.fn().mockResolvedValue({ detail: 'Server error' })
        });

        await expect(taskApiV2.getTasks()).rejects.toThrow('Server error');
      });

      it('should handle response without detail', async () => {
        (global.fetch as any).mockResolvedValue({
          ok: false,
          status: 400,
          json: vi.fn().mockRejectedValue(new Error('Parse error'))
        });

        await expect(taskApiV2.getTasks()).rejects.toThrow('Request failed with status 400');
      });
    });

    describe('getTask', () => {
      const taskId = 'task-123';

      it('should fetch a specific task', async () => {
        const mockTask = { id: taskId, title: 'Test Task' };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockTask)
        });

        const result = await taskApiV2.getTask(taskId);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/tasks/${taskId}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockTask);
      });
    });

    describe('createTask', () => {
      const taskData = {
        title: 'New Task',
        description: 'Task description',
        status: 'todo',
        priority: 'high',
        git_branch_id: 'branch-123'
      };

      it('should create a new task', async () => {
        const mockCreatedTask = { id: 'new-id', ...taskData };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockCreatedTask)
        });

        const result = await taskApiV2.createTask(taskData);

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/tasks/',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(taskData)
          }
        );
        expect(result).toEqual(mockCreatedTask);
      });

      it('should handle minimal task data', async () => {
        const minimalData = { title: 'Minimal Task' };
        const mockCreatedTask = { id: 'new-id', ...minimalData };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockCreatedTask)
        });

        const result = await taskApiV2.createTask(minimalData);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body).toEqual(minimalData);
        expect(result).toEqual(mockCreatedTask);
      });
    });

    describe('updateTask', () => {
      const taskId = 'task-123';
      const updates = {
        title: 'Updated Task',
        status: 'in_progress',
        progress_percentage: 50
      };

      it('should update a task', async () => {
        const mockUpdatedTask = { id: taskId, ...updates };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockUpdatedTask)
        });

        const result = await taskApiV2.updateTask(taskId, updates);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/tasks/${taskId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(updates)
          }
        );
        expect(result).toEqual(mockUpdatedTask);
      });
    });

    describe('deleteTask', () => {
      const taskId = 'task-123';

      it('should delete a task', async () => {
        const mockResponse = { success: true };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockResponse)
        });

        const result = await taskApiV2.deleteTask(taskId);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/tasks/${taskId}`,
          {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('completeTask', () => {
      const taskId = 'task-123';
      const completionData = {
        completion_summary: 'Task completed successfully',
        testing_notes: 'All tests passed'
      };

      it('should complete a task', async () => {
        const mockCompletedTask = { 
          id: taskId, 
          status: 'done',
          ...completionData
        };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockCompletedTask)
        });

        const result = await taskApiV2.completeTask(taskId, completionData);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/tasks/${taskId}/complete`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(completionData)
          }
        );
        expect(result).toEqual(mockCompletedTask);
      });

      it('should handle completion without testing notes', async () => {
        const minimalData = { completion_summary: 'Done' };
        const mockResponse = { id: taskId, status: 'done' };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockResponse)
        });

        await taskApiV2.completeTask(taskId, minimalData);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body).toEqual(minimalData);
      });
    });
  });

  describe('Project API V2', () => {
    beforeEach(() => {
      (Cookies.get as any).mockReturnValue(mockToken);
    });

    describe('getProjects', () => {
      it('should fetch projects with authentication', async () => {
        const mockProjects = [
          { id: '1', name: 'Project 1' },
          { id: '2', name: 'Project 2' }
        ];
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockProjects)
        });

        const result = await projectApiV2.getProjects();

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/projects/',
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockProjects);
      });
    });

    describe('createProject', () => {
      const projectData = {
        name: 'New Project',
        description: 'Project description'
      };

      it('should create a new project', async () => {
        const mockCreatedProject = { id: 'proj-123', ...projectData };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockCreatedProject)
        });

        const result = await projectApiV2.createProject(projectData);

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/projects/',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(projectData)
          }
        );
        expect(result).toEqual(mockCreatedProject);
      });
    });

    describe('updateProject', () => {
      const projectId = 'proj-123';
      const updates = {
        name: 'Updated Project',
        description: 'Updated description',
        status: 'active'
      };

      it('should update a project', async () => {
        const mockUpdatedProject = { id: projectId, ...updates };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockUpdatedProject)
        });

        const result = await projectApiV2.updateProject(projectId, updates);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/projects/${projectId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(updates)
          }
        );
        expect(result).toEqual(mockUpdatedProject);
      });
    });

    describe('deleteProject', () => {
      const projectId = 'proj-123';

      it('should delete a project', async () => {
        const mockResponse = { success: true };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockResponse)
        });

        const result = await projectApiV2.deleteProject(projectId);

        expect(global.fetch).toHaveBeenCalledWith(
          `http://test-api.com/api/v2/projects/${projectId}`,
          {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Agent API V2', () => {
    beforeEach(() => {
      (Cookies.get as any).mockReturnValue(mockToken);
    });

    describe('getAgents', () => {
      it('should fetch agents with authentication', async () => {
        const mockAgents = [
          { id: '1', name: '@test_agent' },
          { id: '2', name: '@coding_agent' }
        ];
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockAgents)
        });

        const result = await agentApiV2.getAgents();

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/agents/',
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            }
          }
        );
        expect(result).toEqual(mockAgents);
      });
    });

    describe('registerAgent', () => {
      const agentData = {
        name: '@new_agent',
        project_id: 'proj-123',
        call_agent: 'agent_config'
      };

      it('should register a new agent', async () => {
        const mockRegisteredAgent = { id: 'agent-123', ...agentData };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockRegisteredAgent)
        });

        const result = await agentApiV2.registerAgent(agentData);

        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api.com/api/v2/agents/',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${mockToken}`
            },
            body: JSON.stringify(agentData)
          }
        );
        expect(result).toEqual(mockRegisteredAgent);
      });

      it('should handle minimal agent data', async () => {
        const minimalData = {
          name: '@minimal_agent',
          project_id: 'proj-123'
        };
        const mockResponse = { id: 'agent-456', ...minimalData };
        (global.fetch as any).mockResolvedValue({
          ok: true,
          json: vi.fn().mockResolvedValue(mockResponse)
        });

        const result = await agentApiV2.registerAgent(minimalData);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body).toEqual(minimalData);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      (Cookies.get as any).mockReturnValue(mockToken);
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      await expect(taskApiV2.getTasks()).rejects.toThrow('Network error');
    });

    it('should handle JSON parsing errors in response', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: vi.fn().mockRejectedValue(new Error('Invalid JSON'))
      });

      await expect(taskApiV2.getTasks()).rejects.toThrow('Invalid JSON');
    });

    it('should handle missing authorization header when no token', async () => {
      (Cookies.get as any).mockReturnValue(null);
      
      const mockResponse = { tasks: [] };
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse)
      });

      await taskApiV2.getTasks();

      const fetchCall = (global.fetch as any).mock.calls[0];
      expect(fetchCall[1].headers).toEqual({
        'Content-Type': 'application/json'
      });
      expect(fetchCall[1].headers['Authorization']).toBeUndefined();
    });
  });

  describe('Environment Configuration', () => {
    it('should use default API URL when env variable not set', async () => {
      // Clear the mocked env variable
      delete (process as any).env.REACT_APP_API_URL;
      
      // Re-import the module to test default value
      vi.resetModules();
      const { taskApiV2: freshTaskApiV2 } = await import('../../services/apiV2');
      
      (Cookies.get as any).mockReturnValue(mockToken);
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue([])
      });

      await freshTaskApiV2.getTasks();

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v2/tasks/',
        expect.any(Object)
      );
    });
  });
});