import * as api from '../../api';
import * as apiV2 from '../../services/apiV2';

// Mock services/apiV2
jest.mock('../../services/apiV2', () => ({
  taskApiV2: {
    getTasks: jest.fn(),
    createTask: jest.fn(),
    updateTask: jest.fn(),
    deleteTask: jest.fn(),
    completeTask: jest.fn()
  },
  projectApiV2: {
    getProjects: jest.fn()
  },
  agentApiV2: {
    getAgents: jest.fn()
  },
  isAuthenticated: jest.fn()
}));

// Mock fetch globally
global.fetch = jest.fn();

describe('api.ts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as any).mockReset();
    (apiV2.isAuthenticated as any).mockReturnValue(false);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Task Management', () => {
    describe('listTasks', () => {
      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        const mockTasks = [
          { id: '1', title: 'Task 1', status: 'todo' },
          { id: '2', title: 'Task 2', status: 'done' }
        ];
        (apiV2.taskApiV2.getTasks as any).mockResolvedValue(mockTasks);

        const result = await api.listTasks();

        expect(apiV2.taskApiV2.getTasks).toHaveBeenCalled();
        expect(result).toEqual(mockTasks);
        expect(global.fetch).not.toHaveBeenCalled();
      });

      it('should fall back to V1 API when V2 fails', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        (apiV2.taskApiV2.getTasks as any).mockRejectedValue(new Error('V2 API error'));
        
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  tasks: [
                    { id: '1', title: 'Task 1', status: 'todo' }
                  ]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listTasks();

        expect(apiV2.taskApiV2.getTasks).toHaveBeenCalled();
        expect(global.fetch).toHaveBeenCalled();
        expect(result).toHaveLength(1);
        expect(result[0].id).toBe('1');
      });

      it('should use V1 API when not authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(false);
        
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  tasks: [
                    { id: '1', title: 'Task 1', status: 'todo' }
                  ]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listTasks();

        expect(apiV2.taskApiV2.getTasks).not.toHaveBeenCalled();
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/mcp/',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'MCP-Protocol-Version': '2025-06-18'
            })
          })
        );
        expect(result).toHaveLength(1);
      });

      it('should handle empty response', async () => {
        const mockResponse = {
          result: {
            content: []
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listTasks();

        expect(result).toEqual([]);
      });

      it('should sanitize task data', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  tasks: [{
                    id: '1',
                    title: 'Task 1',
                    _events: 'should be removed',
                    _eventsCount: 42,
                    _maxListeners: 10,
                    assignees: ['user1', { id: 'user2' }, { name: 'user3' }],
                    subtasks: ['sub1', { id: 'sub2' }, { value: 'sub3' }]
                  }]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listTasks();

        expect(result).toHaveLength(1);
        const task = result[0];
        expect(task._events).toBeUndefined();
        expect(task._eventsCount).toBeUndefined();
        expect(task._maxListeners).toBeUndefined();
        expect(task.assignees).toEqual(['user1', 'user2', 'user3']);
        expect(task.subtasks).toEqual(['sub1', 'sub2', 'sub3']);
      });
    });

    describe('createTask', () => {
      const newTask = {
        title: 'New Task',
        description: 'Task description',
        status: 'todo',
        priority: 'high'
      };

      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        const mockCreatedTask = { id: '123', ...newTask };
        (apiV2.taskApiV2.createTask as any).mockResolvedValue(mockCreatedTask);

        const result = await api.createTask(newTask);

        expect(apiV2.taskApiV2.createTask).toHaveBeenCalledWith({
          title: newTask.title,
          description: newTask.description,
          status: newTask.status,
          priority: newTask.priority,
          git_branch_id: undefined
        });
        expect(result).toEqual(mockCreatedTask);
      });

      it('should fall back to V1 API when V2 fails', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        (apiV2.taskApiV2.createTask as any).mockRejectedValue(new Error('V2 API error'));
        
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  task: { id: '123', ...newTask }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.createTask(newTask);

        expect(apiV2.taskApiV2.createTask).toHaveBeenCalled();
        expect(global.fetch).toHaveBeenCalled();
        expect(result).toMatchObject(newTask);
        expect(result?.id).toBe('123');
      });
    });

    describe('updateTask', () => {
      const taskId = '123';
      const updates = {
        title: 'Updated Task',
        status: 'in_progress'
      };

      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        const mockUpdatedTask = { id: taskId, ...updates };
        (apiV2.taskApiV2.updateTask as any).mockResolvedValue(mockUpdatedTask);

        const result = await api.updateTask(taskId, updates);

        expect(apiV2.taskApiV2.updateTask).toHaveBeenCalledWith(taskId, {
          title: updates.title,
          description: undefined,
          status: updates.status,
          priority: undefined,
          progress_percentage: undefined
        });
        expect(result).toEqual(mockUpdatedTask);
      });

      it('should handle error response', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false,
                error: 'Task not found'
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        await expect(api.updateTask(taskId, updates)).rejects.toThrow('Task not found');
      });

      it('should handle success without task data', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.updateTask(taskId, updates);

        expect(result).toMatchObject({ id: taskId, ...updates });
      });
    });

    describe('deleteTask', () => {
      const taskId = '123';

      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        (apiV2.taskApiV2.deleteTask as any).mockResolvedValue(undefined);

        const result = await api.deleteTask(taskId);

        expect(apiV2.taskApiV2.deleteTask).toHaveBeenCalledWith(taskId);
        expect(result).toBe(true);
      });

      it('should return true on successful deletion', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteTask(taskId);

        expect(result).toBe(true);
      });

      it('should return false on failed deletion', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteTask(taskId);

        expect(result).toBe(false);
      });
    });

    describe('completeTask', () => {
      const taskId = '123';
      const completionSummary = 'Task completed successfully';
      const testingNotes = 'All tests passed';

      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        const mockCompletedTask = { 
          id: taskId, 
          status: 'done',
          completion_summary: completionSummary
        };
        (apiV2.taskApiV2.completeTask as any).mockResolvedValue(mockCompletedTask);

        const result = await api.completeTask(taskId, completionSummary, testingNotes);

        expect(apiV2.taskApiV2.completeTask).toHaveBeenCalledWith(taskId, {
          completion_summary: completionSummary,
          testing_notes: testingNotes
        });
        expect(result).toEqual(mockCompletedTask);
      });

      it('should handle completion without testing notes', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  task: { id: taskId, status: 'done' }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.completeTask(taskId, completionSummary);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'complete',
          task_id: taskId,
          completion_summary: completionSummary
        });
        expect(body.params.arguments.testing_notes).toBeUndefined();
        expect(result?.status).toBe('done');
      });
    });

    describe('searchTasks', () => {
      it('should search tasks with query', async () => {
        const query = 'test query';
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  tasks: [
                    { id: '1', title: 'Test Task 1' },
                    { id: '2', title: 'Test Task 2' }
                  ]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.searchTasks(query);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'search',
          query: query,
          limit: 50
        });
        expect(result).toHaveLength(2);
      });

      it('should search with git_branch_id and custom limit', async () => {
        const query = 'test';
        const branchId = 'branch-123';
        const limit = 10;
        
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: { tasks: [] }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        await api.searchTasks(query, branchId, limit);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'search',
          query: query,
          git_branch_id: branchId,
          limit: limit
        });
      });
    });
  });

  describe('Subtask Management', () => {
    describe('listSubtasks', () => {
      const taskId = 'task-123';

      it('should list subtasks for a task', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  subtasks: [
                    { id: 'sub1', title: 'Subtask 1' },
                    { id: 'sub2', title: 'Subtask 2' }
                  ]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listSubtasks(taskId);

        expect(result).toHaveLength(2);
        expect(result[0].id).toBe('sub1');
        expect(result[1].id).toBe('sub2');
      });

      it('should sanitize subtask data', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  subtasks: [{
                    id: 'sub1',
                    title: 'Subtask 1',
                    _events: 'should be removed',
                    _eventsCount: 10,
                    _maxListeners: 5
                  }]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listSubtasks(taskId);

        expect(result).toHaveLength(1);
        const subtask = result[0];
        expect(subtask._events).toBeUndefined();
        expect(subtask._eventsCount).toBeUndefined();
        expect(subtask._maxListeners).toBeUndefined();
      });
    });

    describe('updateSubtask', () => {
      const taskId = 'task-123';
      const subtaskId = 'sub-456';
      const updates = { title: 'Updated Subtask', status: 'done' };

      it('should update subtask successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  subtask: {
                    id: subtaskId,
                    ...updates
                  }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.updateSubtask(taskId, subtaskId, updates);

        expect(result).toMatchObject({ id: subtaskId, ...updates });
      });

      it('should handle nested subtask structure', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  subtask: {
                    subtask: {
                      id: subtaskId,
                      ...updates
                    }
                  }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.updateSubtask(taskId, subtaskId, updates);

        expect(result).toMatchObject({ id: subtaskId, ...updates });
      });

      it('should handle error response', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false,
                error: { message: 'Subtask not found' }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        await expect(api.updateSubtask(taskId, subtaskId, updates))
          .rejects.toThrow('Subtask not found');
      });
    });

    describe('completeSubtask', () => {
      const taskId = 'task-123';
      const subtaskId = 'sub-456';
      const completionSummary = 'Subtask completed';
      const impactOnParent = 'Task is now 50% complete';
      const challengesOvercome = ['Challenge 1', 'Challenge 2'];

      it('should complete subtask with all parameters', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  subtask: {
                    id: subtaskId,
                    status: 'done'
                  }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.completeSubtask(
          taskId,
          subtaskId,
          completionSummary,
          impactOnParent,
          challengesOvercome
        );

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'complete',
          task_id: taskId,
          subtask_id: subtaskId,
          completion_summary: completionSummary,
          impact_on_parent: impactOnParent,
          challenges_overcome: challengesOvercome
        });
        expect(result).toMatchObject({ id: subtaskId, status: 'done' });
      });

      it('should complete subtask with minimal parameters', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.completeSubtask(taskId, subtaskId, completionSummary);

        expect(result).toMatchObject({ id: subtaskId, status: 'done' });
      });
    });
  });

  describe('Dependency Management', () => {
    const taskId = 'task-123';
    const dependencyId = 'dep-456';

    describe('addDependency', () => {
      it('should add dependency successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.addDependency(taskId, dependencyId);

        expect(result).toBe(true);
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'add_dependency',
          task_id: taskId,
          dependency_id: dependencyId
        });
      });
    });

    describe('removeDependency', () => {
      it('should remove dependency successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.removeDependency(taskId, dependencyId);

        expect(result).toBe(true);
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'remove_dependency',
          task_id: taskId,
          dependency_id: dependencyId
        });
      });
    });
  });

  describe('Context Management', () => {
    describe('getTaskContext', () => {
      const taskId = 'task-123';

      it('should get task context with inheritance', async () => {
        const mockContext = {
          id: taskId,
          level: 'task',
          data: { some: 'data' },
          inherited: { project: 'context' }
        };
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify(mockContext)
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.getTaskContext(taskId);

        expect(result).toEqual(mockContext);
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'resolve',
          level: 'task',
          context_id: taskId,
          force_refresh: false,
          include_inherited: true
        });
      });

      it('should handle context not found', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false,
                error: { message: 'Context not found' }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.getTaskContext(taskId);

        expect(result).toBeNull();
      });
    });

    describe('addTaskInsight', () => {
      const taskId = 'task-123';
      const content = 'Important insight';
      const category = 'performance';
      const importance = 'high';

      it('should add task insight', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true, insight_id: 'insight-123' })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.addTaskInsight(taskId, content, category, importance);

        expect(result).toMatchObject({ success: true });
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'add_insight',
          level: 'task',
          context_id: taskId,
          content: content,
          category: category,
          importance: importance
        });
      });

      it('should use default values for category and importance', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        await api.addTaskInsight(taskId, content);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments.category).toBe('general');
        expect(body.params.arguments.importance).toBe('medium');
      });
    });

    describe('addTaskProgress', () => {
      const taskId = 'task-123';
      const content = 'Made significant progress';

      it('should add task progress', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.addTaskProgress(taskId, content);

        expect(result).toMatchObject({ success: true });
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'add_progress',
          level: 'task',
          context_id: taskId,
          content: content
        });
      });
    });

    describe('updateGlobalContext', () => {
      const contextData = {
        theme: 'dark',
        features: ['auth', 'tasks']
      };

      it('should update global context', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true, context_id: 'global_singleton' })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.updateGlobalContext(contextData);

        expect(result).toMatchObject({ success: true });
        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments).toMatchObject({
          action: 'update',
          level: 'global',
          context_id: 'global_singleton',
          data: contextData,
          propagate_changes: true
        });
      });

      it('should throw error on failure', async () => {
        const mockResponse = {
          result: {
            content: []
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        await expect(api.updateGlobalContext(contextData))
          .rejects.toThrow('Failed to update global context');
      });
    });
  });

  describe('Project Management', () => {
    describe('listProjects', () => {
      it('should use V2 API when authenticated', async () => {
        (apiV2.isAuthenticated as any).mockReturnValue(true);
        const mockProjects = [
          { id: '1', name: 'Project 1', git_branchs: {} },
          { id: '2', name: 'Project 2', git_branchs: {} }
        ];
        (apiV2.projectApiV2.getProjects as any).mockResolvedValue(mockProjects);

        const result = await api.listProjects();

        expect(apiV2.projectApiV2.getProjects).toHaveBeenCalled();
        expect(result).toEqual(mockProjects);
      });

      it('should handle projects with git branches', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  projects: [{
                    id: 'proj1',
                    name: 'Project 1',
                    git_branchs: {
                      'branch1': { id: 'branch1', name: 'main' },
                      'branch2': { id: 'branch2', name: 'feature' }
                    }
                  }]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listProjects();

        expect(result).toHaveLength(1);
        expect(result[0].git_branchs).toHaveProperty('branch1');
        expect(result[0].git_branchs).toHaveProperty('branch2');
      });
    });

    describe('deleteProject', () => {
      const projectId = 'proj-123';

      it('should delete project successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                message: 'Project deleted'
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteProject(projectId);

        expect(result).toEqual({
          success: true,
          message: 'Project deleted',
          error: undefined
        });
      });

      it('should handle deletion failure', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false,
                error: 'Project has active tasks'
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteProject(projectId);

        expect(result).toEqual({
          success: false,
          message: undefined,
          error: 'Project has active tasks'
        });
      });

      it('should handle parse error', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: 'invalid json'
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteProject(projectId);

        expect(result).toEqual({
          success: false,
          error: 'Failed to parse response'
        });
      });
    });
  });

  describe('Branch Management', () => {
    const projectId = 'proj-123';
    const branchName = 'feature-auth';
    const description = 'Authentication feature branch';

    describe('createBranch', () => {
      it('should create branch with git-friendly name', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  git_branch: {
                    id: 'branch-123',
                    name: 'feature-auth',
                    description: description
                  }
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.createBranch(projectId, 'Feature Auth', description);

        const fetchCall = (global.fetch as any).mock.calls[0];
        const body = JSON.parse(fetchCall[1].body);
        expect(body.params.arguments.git_branch_name).toBe('feature-auth');
        expect(result).toMatchObject({
          id: 'branch-123',
          name: 'feature-auth'
        });
      });
    });

    describe('deleteBranch', () => {
      const branchId = 'branch-123';

      it('should delete branch successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: true })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteBranch(projectId, branchId);

        expect(result).toBe(true);
      });

      it('should handle deletion failure', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({ success: false })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.deleteBranch(projectId, branchId);

        expect(result).toBe(false);
      });

      it('should handle network error', async () => {
        (global.fetch as any).mockRejectedValue(new Error('Network error'));

        const result = await api.deleteBranch(projectId, branchId);

        expect(result).toBe(false);
      });
    });
  });

  describe('Agent Management', () => {
    describe('callAgent', () => {
      const agentName = '@test_orchestrator_agent';

      it('should call agent successfully', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                agent_info: { name: agentName }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.callAgent(agentName);

        expect(result).toMatchObject({
          success: true,
          agent_info: { name: agentName }
        });
      });

      it('should handle parse error', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: 'invalid json'
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.callAgent(agentName);

        expect(result).toEqual({
          success: false,
          error: 'Failed to parse response'
        });
      });

      it('should handle no response', async () => {
        const mockResponse = {
          result: {
            content: []
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.callAgent(agentName);

        expect(result).toEqual({
          success: false,
          error: 'No response from server'
        });
      });
    });

    describe('getAvailableAgents', () => {
      it('should return list of available agents', async () => {
        const agents = await api.getAvailableAgents();

        expect(agents).toBeInstanceOf(Array);
        expect(agents.length).toBeGreaterThan(0);
        expect(agents).toContain('@test_orchestrator_agent');
        expect(agents).toContain('@coding_agent');
        expect(agents).toContain('@debugger_agent');
      });
    });
  });

  describe('Rule Management', () => {
    describe('listRules', () => {
      it('should list rules successfully', async () => {
        const mockRules = [
          { id: 'rule1', name: 'Rule 1', type: 'validation' },
          { id: 'rule2', name: 'Rule 2', type: 'security' }
        ];
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                rules: mockRules
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listRules();

        expect(result).toEqual(mockRules);
      });

      it('should return empty array on failure', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.listRules();

        expect(result).toEqual([]);
      });
    });

    describe('validateRule', () => {
      const ruleId = 'rule-123';

      it('should validate rule successfully', async () => {
        const mockValidation = {
          success: true,
          valid: true,
          issues: []
        };
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify(mockValidation)
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.validateRule(ruleId);

        expect(result).toEqual(mockValidation);
      });

      it('should return null on failure', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: false,
                error: 'Rule not found'
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const result = await api.validateRule(ruleId);

        expect(result).toBeNull();
      });
    });
  });

  describe('Helper Functions', () => {
    describe('getTaskCount', () => {
      const branchId = 'branch-123';

      it('should return task count for branch', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: {
                  tasks: [
                    { id: '1', git_branch_id: branchId },
                    { id: '2', git_branch_id: branchId },
                    { id: '3', git_branch_id: branchId }
                  ]
                }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const count = await api.getTaskCount(branchId);

        expect(count).toBe(3);
      });

      it('should return 0 for empty branch', async () => {
        const mockResponse = {
          result: {
            content: [{
              text: JSON.stringify({
                success: true,
                data: { tasks: [] }
              })
            }]
          }
        };
        (global.fetch as any).mockResolvedValue({
          json: jest.fn().mockResolvedValue(mockResponse)
        });

        const count = await api.getTaskCount(branchId);

        expect(count).toBe(0);
      });
    });
  });
});