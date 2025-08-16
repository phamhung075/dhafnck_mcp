import { Check, Eye, FileText, Link, Minus, Pencil, Plus, Trash2, Users, ChevronDown, ChevronRight } from "lucide-react";
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { listTasks, Task, Subtask, updateTask, getTaskContext, listAgents, getAvailableAgents, callAgent, createTask, completeTask, deleteTask } from "../api";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { RefreshButton } from "./ui/refresh-button";
import TaskSearch from "./TaskSearch";

// Lazy-loaded components
import { lazy, Suspense } from "react";

const LazySubtaskList = lazy(() => import("./LazySubtaskList"));
const TaskDetailsDialog = lazy(() => import("./TaskDetailsDialog"));
const TaskEditDialog = lazy(() => import("./TaskEditDialog"));
const AgentAssignmentDialog = lazy(() => import("./AgentAssignmentDialog"));
const TaskContextDialog = lazy(() => import("./TaskContextDialog"));
const TaskCompleteDialog = lazy(() => import("./TaskCompleteDialog"));
const DeleteConfirmDialog = lazy(() => import("./DeleteConfirmDialog"));
const AgentResponseDialog = lazy(() => import("./AgentResponseDialog"));

// Lightweight components
import ClickableAssignees from "./ClickableAssignees";

interface LazyTaskListProps {
  projectId: string;
  taskTreeId: string;
  onTasksChanged?: () => void;
}

// Pagination configuration
const TASKS_PER_PAGE = 20;
const INITIAL_LOAD_COUNT = 10;

// Lightweight task summary for initial load
interface TaskSummary {
  id: string;
  title: string;
  status: string;
  priority: string;
  subtask_count: number;
  assignees_count: number;
  has_dependencies: boolean;
  has_context: boolean;
}

const LazyTaskList: React.FC<LazyTaskListProps> = ({ projectId, taskTreeId, onTasksChanged }) => {
  // Core state - minimal for performance
  const [taskSummaries, setTaskSummaries] = useState<TaskSummary[]>([]);
  const [fullTasks, setFullTasks] = useState<Map<string, Task>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalTasks, setTotalTasks] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  
  // Lazy loading state
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [loadingTasks, setLoadingTasks] = useState<Set<string>>(new Set());
  const [loadedSubtasks, setLoadedSubtasks] = useState<Set<string>>(new Set());
  const [loadedContexts, setLoadedContexts] = useState<Set<string>>(new Set());
  const [loadedAgents, setLoadedAgents] = useState(false);
  
  // Dialog states - simplified
  const [activeDialog, setActiveDialog] = useState<{
    type: 'details' | 'edit' | 'create' | 'assign' | 'context' | 'complete' | 'delete' | 'agent-response' | null;
    taskId?: string;
    data?: any;
  }>({ type: null });

  // Lazy data stores
  const [agents, setAgents] = useState<any[]>([]);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [taskContexts, setTaskContexts] = useState<Map<string, any>>(new Map());

  // Memoized filtered and sorted tasks
  const displayTasks = useMemo(() => {
    const startIndex = (currentPage - 1) * TASKS_PER_PAGE;
    const endIndex = startIndex + TASKS_PER_PAGE;
    return taskSummaries.slice(0, endIndex);
  }, [taskSummaries, currentPage]);

  // Initial lightweight load - only task summaries
  const loadTaskSummaries = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      // Request lightweight task data
      const response = await fetch(`/api/tasks/summaries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          git_branch_id: taskTreeId,
          page,
          limit: TASKS_PER_PAGE,
          include_counts: true
        })
      });
      
      const data = await response.json();
      
      if (page === 1) {
        setTaskSummaries(data.tasks);
      } else {
        setTaskSummaries(prev => [...prev, ...data.tasks]);
      }
      
      setTotalTasks(data.total);
      setHasMore(data.has_more);
      
    } catch (e: any) {
      // Fallback to full task loading if lightweight endpoint doesn't exist
      console.warn('Lightweight endpoint not available, falling back to full load');
      await loadFullTasksFallback();
    } finally {
      setLoading(false);
    }
  }, [taskTreeId]);

  // Fallback to current implementation if lightweight endpoint isn't available
  const loadFullTasksFallback = useCallback(async () => {
    try {
      const taskList = await listTasks({ git_branch_id: taskTreeId });
      
      // Convert to task summaries
      const summaries: TaskSummary[] = taskList.map(task => ({
        id: task.id,
        title: task.title,
        status: task.status,
        priority: task.priority,
        subtask_count: task.subtasks?.length || 0,
        assignees_count: task.assignees?.length || 0,
        has_dependencies: Boolean(task.dependencies?.length),
        has_context: Boolean(task.context_id || task.context_data)
      }));
      
      setTaskSummaries(summaries);
      setTotalTasks(summaries.length);
      
      // Store full tasks for immediate access
      const taskMap = new Map();
      taskList.forEach(task => taskMap.set(task.id, task));
      setFullTasks(taskMap);
      
    } catch (e: any) {
      setError(e.message);
    }
  }, [taskTreeId]);

  // Load full task data on demand
  const loadFullTask = useCallback(async (taskId: string): Promise<Task | null> => {
    if (fullTasks.has(taskId)) {
      return fullTasks.get(taskId) || null;
    }
    
    if (loadingTasks.has(taskId)) {
      return null; // Already loading
    }
    
    setLoadingTasks(prev => {
      const newSet = new Set(prev);
      newSet.add(taskId);
      return newSet;
    });
    
    try {
      // Request single task with full data
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const task = await response.json();
      
      setFullTasks(prev => {
        const newMap = new Map(prev);
        newMap.set(taskId, task);
        return newMap;
      });
      setLoadingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
      
      return task;
      
    } catch (e) {
      console.error(`Failed to load task ${taskId}:`, e);
      setLoadingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
      return null;
    }
  }, [fullTasks, loadingTasks]);

  // Load agents only when needed
  const loadAgentsOnDemand = useCallback(async () => {
    if (loadedAgents) return;
    
    try {
      const [projectAgents, availableAgentsList] = await Promise.all([
        listAgents(projectId),
        getAvailableAgents()
      ]);
      setAgents(projectAgents);
      setAvailableAgents(availableAgentsList);
      setLoadedAgents(true);
    } catch (e) {
      console.error('Error loading agents:', e);
    }
  }, [projectId, loadedAgents]);

  // Load task context on demand
  const loadTaskContext = useCallback(async (taskId: string) => {
    if (taskContexts.has(taskId) || loadedContexts.has(taskId)) {
      return taskContexts.get(taskId) || null;
    }
    
    setLoadedContexts(prev => {
      const newSet = new Set(prev);
      newSet.add(taskId);
      return newSet;
    });
    
    try {
      const context = await getTaskContext(taskId);
      setTaskContexts(prev => {
        const newMap = new Map(prev);
        newMap.set(taskId, context);
        return newMap;
      });
      return context;
    } catch (e) {
      console.error(`Failed to load context for task ${taskId}:`, e);
      return null;
    }
  }, [taskContexts, loadedContexts]);

  // Task expansion with lazy subtask loading
  const toggleTaskExpansion = useCallback(async (taskId: string) => {
    const isExpanded = expandedTasks.has(taskId);
    
    if (isExpanded) {
      // Collapse
      setExpandedTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
    } else {
      // Expand - load full task data if needed
      await loadFullTask(taskId);
      setExpandedTasks(prev => {
        const newSet = new Set(prev);
        newSet.add(taskId);
        return newSet;
      });
    }
  }, [expandedTasks, loadFullTask]);

  // Dialog handlers with lazy loading
  const openDialog = useCallback(async (type: string, taskId?: string, extraData?: any) => {
    if (taskId) {
      await loadFullTask(taskId);
    }
    
    if (type === 'assign') {
      await loadAgentsOnDemand();
    }
    
    setActiveDialog({ type: type as any, taskId, data: extraData });
  }, [loadFullTask, loadAgentsOnDemand]);

  const closeDialog = useCallback(() => {
    setActiveDialog({ type: null });
  }, []);

  // Load more tasks (pagination)
  const loadMoreTasks = useCallback(async () => {
    if (!hasMore || loading) return;
    
    const nextPage = Math.floor(taskSummaries.length / TASKS_PER_PAGE) + 1;
    await loadTaskSummaries(nextPage);
  }, [hasMore, loading, taskSummaries.length, loadTaskSummaries]);

  // Initial load
  useEffect(() => {
    loadTaskSummaries(1);
  }, [projectId, taskTreeId, loadTaskSummaries]);

  // Render task row with lazy loading indicators
  const renderTaskRow = useCallback((summary: TaskSummary) => {
    const isExpanded = expandedTasks.has(summary.id);
    const isLoading = loadingTasks.has(summary.id);
    const fullTask = fullTasks.get(summary.id) || null;
    
    return (
      <React.Fragment key={summary.id}>
        <TableRow>
          <TableCell style={{ width: '50px' }}>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => toggleTaskExpansion(summary.id)}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              ) : isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </Button>
          </TableCell>
          
          <TableCell>
            <div className="flex items-center gap-2">
              <span>{summary.title}</span>
              {summary.subtask_count > 0 && (
                <Badge variant="outline" className="text-xs">
                  {summary.subtask_count}
                </Badge>
              )}
            </div>
          </TableCell>
          
          <TableCell>
            <Badge>{summary.status}</Badge>
          </TableCell>
          
          <TableCell>
            <Badge variant="secondary">{summary.priority}</Badge>
          </TableCell>
          
          <TableCell>
            {summary.has_dependencies ? (
              <Badge variant="outline" className="text-xs">
                Has dependencies
              </Badge>
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </TableCell>
          
          <TableCell>
            {summary.assignees_count > 0 ? (
              <Badge variant="secondary" className="text-xs">
                {summary.assignees_count} assigned
              </Badge>
            ) : (
              <span className="text-xs text-muted-foreground">Unassigned</span>
            )}
          </TableCell>
          
          <TableCell>
            <div className="flex gap-1">
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => openDialog('details', summary.id)}
                title="View details"
              >
                <Eye className="w-4 h-4" />
              </Button>
              
              {summary.has_context && (
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => openDialog('context', summary.id)}
                  title="View context"
                >
                  <FileText className="w-4 h-4" />
                </Button>
              )}
              
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => openDialog('assign', summary.id)}
                title="Assign agents"
              >
                <Users className="w-4 h-4" />
              </Button>
              
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => openDialog('edit', summary.id)}
                title="Edit task"
              >
                <Pencil className="w-4 h-4" />
              </Button>
            </div>
          </TableCell>
        </TableRow>
        
        {isExpanded && fullTask && (
          <TableRow>
            <TableCell colSpan={7}>
              <Suspense fallback={<div className="p-4 text-center">Loading subtasks...</div>}>
                <LazySubtaskList 
                  projectId={projectId} 
                  taskTreeId={taskTreeId} 
                  parentTaskId={summary.id}
                />
              </Suspense>
            </TableCell>
          </TableRow>
        )}
      </React.Fragment>
    );
  }, [expandedTasks, loadingTasks, fullTasks, toggleTaskExpansion, openDialog, projectId, taskTreeId]);

  if (loading && taskSummaries.length === 0) {
    return <div className="p-4 text-center">Loading tasks...</div>;
  }
  
  if (error) {
    return <div className="p-4 text-center text-red-500">Error: {error}</div>;
  }

  return (
    <>
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="w-full">
          <Suspense fallback={<div>Loading search...</div>}>
            <TaskSearch
              projectId={projectId}
              taskTreeId={taskTreeId}
              onTaskSelect={(task) => openDialog('details', task.id)}
              onSubtaskSelect={(subtask, parentTask) => openDialog('details', parentTask.id)}
            />
          </Suspense>
        </div>
        
        {/* Header */}
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">
            Tasks ({totalTasks})
          </h2>
          <div className="flex gap-2">
            <Button
              onClick={() => openDialog('create')}
              size="sm"
              variant="default"
              className="flex items-center gap-1"
            >
              <Plus className="w-4 h-4" />
              New Task
            </Button>
            <RefreshButton 
              onClick={() => loadTaskSummaries(1)} 
              loading={loading}
              size="sm"
            />
          </div>
        </div>
      </div>

      {/* Task Table */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead style={{ width: '50px' }}></TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Dependencies</TableHead>
              <TableHead>Assignees</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayTasks.map(renderTaskRow)}
          </TableBody>
        </Table>
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center p-4">
          <Button
            onClick={loadMoreTasks}
            disabled={loading}
            variant="outline"
          >
            {loading ? 'Loading...' : 'Load More Tasks'}
          </Button>
        </div>
      )}

      {/* Lazy-loaded Dialogs */}
      <Suspense fallback={null}>
        {activeDialog.type === 'details' && activeDialog.taskId && (
          <TaskDetailsDialog
            open={true}
            onOpenChange={closeDialog}
            task={fullTasks.get(activeDialog.taskId) || null}
            onClose={closeDialog}
            onAgentClick={() => {}} // TODO: implement
          />
        )}
        
        {activeDialog.type === 'edit' && (
          <TaskEditDialog
            open={true}
            onOpenChange={closeDialog}
            task={activeDialog.taskId ? fullTasks.get(activeDialog.taskId) || null : null}
            onClose={closeDialog}
            onSave={() => {}} // TODO: implement
            saving={false}
          />
        )}
        
        {activeDialog.type === 'assign' && activeDialog.taskId && (
          <AgentAssignmentDialog
            open={true}
            onOpenChange={closeDialog}
            task={fullTasks.get(activeDialog.taskId) || null}
            onClose={closeDialog}
            onAssign={() => {}} // TODO: implement
            agents={agents}
            availableAgents={availableAgents}
            saving={false}
          />
        )}
        
        {activeDialog.type === 'context' && activeDialog.taskId && (
          <TaskContextDialog
            open={true}
            onOpenChange={closeDialog}
            task={fullTasks.get(activeDialog.taskId) || null}
            context={taskContexts.get(activeDialog.taskId) || null}
            onClose={closeDialog}
            loading={loadedContexts.has(activeDialog.taskId) && !taskContexts.has(activeDialog.taskId)}
          />
        )}
      </Suspense>
    </>
  );
};

export default LazyTaskList;