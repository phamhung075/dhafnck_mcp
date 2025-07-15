import { Eye, FileText, Link, Minus, Pencil, Play, Plus, Trash2, Users } from "lucide-react";
import React, { useEffect, useState } from "react";
import { listTasks, Task, updateTask, getTaskContext, listAgents, getAvailableAgents, callAgent, getTask } from "../api";
import { SubtaskList } from "./SubtaskList";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Checkbox } from "./ui/checkbox";

interface TaskListProps {
  projectId: string;
  taskTreeId: string;
}

const TaskList: React.FC<TaskListProps> = ({ projectId, taskTreeId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [showTaskDetailsDialog, setShowTaskDetailsDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showTaskContext, setShowTaskContext] = useState<{ task: Task; context: any } | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    priority: "medium",
    status: "todo"
  });
  const [saving, setSaving] = useState(false);
  const [agents, setAgents] = useState<any[]>([]);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [assigningTask, setAssigningTask] = useState<Task | null>(null);
  const [callingAgent, setCallingAgent] = useState(false);
  const [agentResponses, setAgentResponses] = useState<Record<string, any>>({});
  const [dependencyTitles, setDependencyTitles] = useState<Record<string, string>>({});
  const [hoveredDependency, setHoveredDependency] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    listTasks({ git_branch_id: taskTreeId })
      .then(async (taskList) => {
        setTasks(taskList);
        
        // Fetch titles for all dependencies
        const depTitles: Record<string, string> = {};
        const uniqueDeps = new Set<string>();
        
        taskList.forEach(task => {
          if (task.dependencies && task.dependencies.length > 0) {
            task.dependencies.forEach((dep: string) => uniqueDeps.add(dep));
          }
        });
        
        // Fetch dependency task details in parallel
        const depPromises = Array.from(uniqueDeps).map(async (depId) => {
          try {
            const depTask = await getTask(depId);
            if (depTask) {
              depTitles[depId] = depTask.title;
            }
          } catch (e) {
            console.error(`Error fetching dependency ${depId}:`, e);
            depTitles[depId] = depId.substring(0, 8) + '...';
          }
        });
        
        await Promise.all(depPromises);
        setDependencyTitles(depTitles);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId, taskTreeId]);

  useEffect(() => {
    // Fetch registered agents from project
    listAgents(projectId)
      .then(setAgents)
      .catch((e) => console.error('Error fetching agents:', e));
    
    // Fetch available agents from agent library
    getAvailableAgents()
      .then(setAvailableAgents)
      .catch((e) => console.error('Error fetching agents:', e));
  }, [projectId]);

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  const openTaskDetailsDialog = (task: Task) => {
    setSelectedTask(task);
    setShowTaskDetailsDialog(true);
  };

  const closeTaskDetailsDialog = () => {
    setShowTaskDetailsDialog(false);
    setSelectedTask(null);
  };

  const openEditDialog = (task: Task) => {
    setSelectedTask(task);
    setEditForm({
      title: task.title,
      description: task.description || "",
      priority: task.priority || "medium",
      status: task.status || "todo"
    });
    setShowEditDialog(true);
  };

  const closeEditDialog = () => {
    setShowEditDialog(false);
    setSelectedTask(null);
    setEditForm({
      title: "",
      description: "",
      priority: "medium",
      status: "todo"
    });
  };

  const handleEdit = async () => {
    if (!selectedTask || !editForm.title.trim()) return;
    
    setSaving(true);
    setError(null);
    try {
      const updateData = {
        title: editForm.title,
        description: editForm.description,
        priority: editForm.priority,
        status: editForm.status
      };
      const result = await updateTask(selectedTask.id, updateData);
      
      if (result) {
        closeEditDialog();
        // Refresh tasks list
        const updatedTasks = await listTasks({ git_branch_id: taskTreeId });
        setTasks(updatedTasks);
      } else {
        setError("Failed to update task - no response from server");
      }
    } catch (e: any) {
      setError(e.message || "Failed to update task");
    } finally {
      setSaving(false);
    }
  };

  const openAssignDialog = (task: Task) => {
    setAssigningTask(task);
    setSelectedAgents(task.assignees || []);
    setShowAssignDialog(true);
  };

  const handleAssignAgents = async () => {
    if (!assigningTask) return;
    
    setSaving(true);
    console.log('Assigning agents to task:', assigningTask.id, 'Agents:', selectedAgents);
    
    try {
      const updated = await updateTask(assigningTask.id, { assignees: selectedAgents });
      console.log('Assignment result:', updated);
      
      if (updated) {
        setTasks(prevTasks => 
          prevTasks.map(t => t.id === assigningTask.id ? { ...t, assignees: selectedAgents } : t)
        );
        setShowAssignDialog(false);
        setAssigningTask(null);
        setSelectedAgents([]);
        setAgentResponses({});
      }
    } catch (e) {
      console.error('Error assigning agents:', e);
      alert(`Failed to assign agents: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const toggleAgentSelection = (agentId: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'default';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return 'default';
      case 'in_progress': return 'secondary';
      case 'review': return 'secondary';
      case 'testing': return 'secondary';
      case 'todo': return 'outline';
      case 'blocked': return 'destructive';
      case 'cancelled': return 'destructive';
      case 'archived': return 'outline';
      default: return 'outline';
    }
  };

  if (loading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <>
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
        {tasks.map(task => (
          <React.Fragment key={task.id}>
            <TableRow className={hoveredDependency === task.id ? "bg-yellow-100 transition-colors" : ""}>
              <TableCell>
                <Button variant="ghost" size="icon" onClick={() => toggleTaskExpansion(task.id)}>
                  {expandedTasks[task.id] ? <Minus /> : <Plus />}
                </Button>
              </TableCell>
              <TableCell>
                {task.title}
                {hoveredDependency === task.id && (
                  <span className="ml-2 text-xs text-yellow-700">(dependency)</span>
                )}
              </TableCell>
              <TableCell>
                <Badge>{task.status}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{task.priority}</Badge>
              </TableCell>
              <TableCell>
                {task.dependencies && task.dependencies.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {task.dependencies.map((dep: string, index: number) => (
                      <Badge 
                        key={index} 
                        variant="outline" 
                        className="text-xs flex items-center gap-1 cursor-pointer hover:bg-yellow-200"
                        title={`Depends on: ${dependencyTitles[dep] || dep}`}
                        onMouseEnter={() => setHoveredDependency(dep)}
                        onMouseLeave={() => setHoveredDependency(null)}
                      >
                        <Link className="w-3 h-3" />
                        {dependencyTitles[dep] ? 
                          (dependencyTitles[dep].length > 20 ? 
                            dependencyTitles[dep].substring(0, 20) + '...' : 
                            dependencyTitles[dep]
                          ) : 
                          dep.substring(0, 8) + '...'
                        }
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">None</span>
                )}
              </TableCell>
              <TableCell>
                {task.assignees && task.assignees.length > 0 ? (
                  <span className="text-sm">{task.assignees.join(', ')}</span>
                ) : (
                  <span className="text-sm text-muted-foreground">Unassigned</span>
                )}
              </TableCell>
              <TableCell>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => openTaskDetailsDialog(task)}
                  title="View task details"
                >
                  <Eye />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={async () => {
                    setLoadingContext(true);
                    try {
                      const context = await getTaskContext(task.id);
                      setShowTaskContext({ task, context });
                    } catch (e) {
                      console.error('Error fetching task context:', e);
                    } finally {
                      setLoadingContext(false);
                    }
                  }}
                  title="View task context"
                >
                  <FileText />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => openAssignDialog(task)}
                  title="Assign agents"
                >
                  <Users />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  title="Edit task"
                  onClick={() => openEditDialog(task)}
                >
                  <Pencil />
                </Button>
                <Button variant="ghost" size="icon" title="Delete task">
                  <Trash2 />
                </Button>
              </TableCell>
            </TableRow>
            {expandedTasks[task.id] && (
              <TableRow>
                <TableCell colSpan={7}>
                  <SubtaskList
                    key={task.id} // Ensures re-mount on task change
                    projectId={projectId}
                    taskTreeId={taskTreeId}
                    parentTaskId={task.id}
                  />
                </TableCell>
              </TableRow>
            )}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>

    {/* Task Details Dialog (Task info only) */}
    <Dialog open={showTaskDetailsDialog} onOpenChange={closeTaskDetailsDialog}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-left">Task Details - Complete Information</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {/* Task Information Header */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold">{selectedTask?.title}</h3>
            {selectedTask?.description && (
              <p className="text-sm text-muted-foreground mt-2">{selectedTask.description}</p>
            )}
            <div className="flex gap-2 mt-3 flex-wrap">
              <Badge variant={getStatusColor(selectedTask?.status || 'pending')} className="px-3 py-1">
                Status: {selectedTask?.status?.replace('_', ' ') || 'pending'}
              </Badge>
              <Badge variant={getPriorityColor(selectedTask?.priority || 'medium')} className="px-3 py-1">
                Priority: {selectedTask?.priority || 'medium'}
              </Badge>
            </div>
            {selectedTask?.assignees && selectedTask.assignees.length > 0 && (
              <div className="mt-3">
                <span className="text-sm text-muted-foreground">Assigned to: </span>
                <span className="text-sm font-medium">{selectedTask.assignees.join(', ')}</span>
              </div>
            )}
          </div>

          {/* All Task Details */}
          {selectedTask && (
            <div className="space-y-4">
              {/* IDs and References */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-blue-700">IDs and References</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-blue-50 p-3 rounded">
                  <div className="space-y-1">
                    <span className="text-muted-foreground font-medium">Task ID:</span>
                    <p className="font-mono text-xs break-all">{selectedTask.id}</p>
                  </div>
                  {selectedTask.git_branch_id && (
                    <div className="space-y-1">
                      <span className="text-muted-foreground font-medium">Git Branch ID:</span>
                      <p className="font-mono text-xs break-all">{selectedTask.git_branch_id}</p>
                    </div>
                  )}
                  {selectedTask.context_id && (
                    <div className="space-y-1">
                      <span className="text-muted-foreground font-medium">Context ID:</span>
                      <p className="font-mono text-xs break-all">{selectedTask.context_id}</p>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Time Information */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-green-700">Time Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-green-50 p-3 rounded">
                  {selectedTask.estimated_effort && (
                    <div>
                      <span className="text-muted-foreground font-medium">Estimated Effort:</span>
                      <p className="font-semibold">{selectedTask.estimated_effort}</p>
                    </div>
                  )}
                  {selectedTask.due_date && (
                    <div>
                      <span className="text-muted-foreground font-medium">Due Date:</span>
                      <p>{new Date(selectedTask.due_date).toLocaleDateString()} ({new Date(selectedTask.due_date).toLocaleTimeString()})</p>
                    </div>
                  )}
                  {selectedTask.created_at && (
                    <div>
                      <span className="text-muted-foreground font-medium">Created:</span>
                      <p>{new Date(selectedTask.created_at).toLocaleDateString()} at {new Date(selectedTask.created_at).toLocaleTimeString()}</p>
                    </div>
                  )}
                  {selectedTask.updated_at && (
                    <div>
                      <span className="text-muted-foreground font-medium">Last Updated:</span>
                      <p>{new Date(selectedTask.updated_at).toLocaleDateString()} at {new Date(selectedTask.updated_at).toLocaleTimeString()}</p>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Assignment & Organization */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-purple-700">Assignment & Organization</h4>
                <div className="space-y-3 bg-purple-50 p-3 rounded">
                  {/* Details field */}
                  {selectedTask.details && (
                    <div>
                      <span className="text-muted-foreground font-medium">Additional Details:</span>
                      <p className="mt-1 whitespace-pre-wrap">{selectedTask.details}</p>
                    </div>
                  )}
                  
                  {/* Assignees */}
                  {selectedTask.assignees && selectedTask.assignees.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">Assignees:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {selectedTask.assignees.map((assignee: string, index: number) => (
                          <Badge key={index} variant="secondary" className="px-2">
                            {assignee}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Labels */}
                  {selectedTask.labels && selectedTask.labels.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">Labels:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {selectedTask.labels.map((label: string, index: number) => (
                          <Badge key={index} variant="outline" className="px-2">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Dependencies */}
              {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-orange-700">Dependencies ({selectedTask.dependencies.length})</h4>
                    <div className="space-y-2 bg-orange-50 p-3 rounded">
                      {selectedTask.dependencies.map((dep: string, index: number) => (
                        <div key={index} className="text-sm flex items-start">
                          <span className="text-muted-foreground font-medium mr-2">#{index + 1}:</span>
                          <span className="font-mono text-xs break-all">{dep}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Subtasks Summary */}
              {selectedTask.subtasks && selectedTask.subtasks.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-indigo-700">Subtasks Summary</h4>
                    <div className="bg-indigo-50 p-3 rounded">
                      <p className="text-sm font-medium">Total subtasks: {selectedTask.subtasks.length}</p>
                      <div className="mt-2 space-y-1">
                        {selectedTask.subtasks.map((subtask: any, index: number) => (
                          <div key={index} className="text-sm">
                            <span className="text-muted-foreground">#{index + 1}:</span> {subtask.title || 'Untitled'}
                            {subtask.status && (
                              <Badge variant="outline" className="ml-2 text-xs">
                                {subtask.status}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Context Data */}
              {selectedTask.context_data && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-teal-700">Context Data</h4>
                    <div className="bg-teal-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(selectedTask.context_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                </>
              )}

              {/* Raw Data */}
              <Separator />
              <details className="cursor-pointer">
                <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                  View Complete Raw Task Data (JSON)
                </summary>
                <div className="mt-3 bg-gray-100 p-3 rounded">
                  <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(selectedTask, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={closeTaskDetailsDialog}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Edit Task Dialog */}
    <Dialog open={showEditDialog} onOpenChange={closeEditDialog}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-left">Edit Task</DialogTitle>
        </DialogHeader>
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm mb-4">
            {error}
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Title</label>
            <Input
              placeholder="Task title"
              value={editForm.title}
              onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
              disabled={saving}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Description</label>
            <Input
              placeholder="Task description"
              value={editForm.description}
              onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
              disabled={saving}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Status</label>
            <select
              className="w-full p-2 border border-gray-300 rounded-md"
              value={editForm.status}
              onChange={(e) => setEditForm(prev => ({ ...prev, status: e.target.value }))}
              disabled={saving}
            >
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="review">Review</option>
              <option value="testing">Testing</option>
              <option value="done">Done</option>
              <option value="blocked">Blocked</option>
              <option value="cancelled">Cancelled</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Priority</label>
            <select
              className="w-full p-2 border border-gray-300 rounded-md"
              value={editForm.priority}
              onChange={(e) => setEditForm(prev => ({ ...prev, priority: e.target.value }))}
              disabled={saving}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={closeEditDialog} disabled={saving}>
            Cancel
          </Button>
          <Button 
            onClick={handleEdit} 
            disabled={saving || !editForm.title.trim()}
          >
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Task Context Dialog */}
    <Dialog open={!!showTaskContext} onOpenChange={(v) => { if (!v) setShowTaskContext(null); }}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-left">Task Context - {showTaskContext?.task?.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {loadingContext ? (
            <div className="text-center py-8">
              <div className="text-sm text-muted-foreground">Loading context...</div>
            </div>
          ) : showTaskContext?.context ? (
            <>
              {/* Context Resolution Info */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Context Resolution</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Level:</span>
                    <Badge className="ml-2" variant="secondary">Task</Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Context ID:</span>
                    <span className="ml-2 font-mono text-xs">{showTaskContext.context.context_id || showTaskContext.task.id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Task Title:</span>
                    <span className="ml-2">{showTaskContext.task.title}</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Inheritance Chain */}
              {showTaskContext.context.inheritance_chain && (
                <>
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-blue-700">Inheritance Chain</h4>
                    <div className="bg-blue-50 p-3 rounded">
                      <div className="flex items-center gap-2">
                        {showTaskContext.context.inheritance_chain.map((level: string, index: number) => (
                          <React.Fragment key={level}>
                            <Badge variant={level === 'task' ? 'default' : 'outline'}>
                              {level.toUpperCase()}
                            </Badge>
                            {index < showTaskContext.context.inheritance_chain.length - 1 && (
                              <span className="text-muted-foreground">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Context Data */}
              {showTaskContext.context.data && (
                <>
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-green-700">Context Data</h4>
                    <div className="bg-green-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(showTaskContext.context.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Metadata */}
              {showTaskContext.context.metadata && (
                <>
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-purple-700">Metadata</h4>
                    <div className="bg-purple-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(showTaskContext.context.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Insights */}
              {showTaskContext.context.insights && (
                <>
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-orange-700">Insights</h4>
                    <div className="bg-orange-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(showTaskContext.context.insights, null, 2)}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Progress */}
              {showTaskContext.context.progress && (
                <>
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-indigo-700">Progress</h4>
                    <div className="bg-indigo-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(showTaskContext.context.progress, null, 2)}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Raw Context Data */}
              <details className="cursor-pointer">
                <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                  View Complete Raw Context Data (JSON)
                </summary>
                <div className="mt-3 bg-gray-100 p-3 rounded">
                  <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(showTaskContext.context, null, 2)}
                  </pre>
                </div>
              </details>
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">No context data available</p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setShowTaskContext(null)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Assign Agents Dialog */}
    <Dialog open={showAssignDialog} onOpenChange={(v) => { 
      if (!v) { 
        setShowAssignDialog(false); 
        setAssigningTask(null);
        setSelectedAgents([]);
        setAgentResponses({});
      }
    }}>
      <DialogContent className="max-w-5xl w-[90vw]">
        <DialogHeader>
          <DialogTitle className="text-xl text-left">Assign Agents to Task</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-gray-50 p-3 rounded">
            <h4 className="font-medium text-sm mb-1">Task: {assigningTask?.title}</h4>
            {assigningTask?.assignees && assigningTask.assignees.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Currently assigned: {assigningTask.assignees.join(', ')}
              </p>
            )}
          </div>
          
          <Separator />
          
          <div>
            <h4 className="font-medium text-sm mb-3">Project Registered Agents</h4>
            {agents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No agents registered in this project</p>
            ) : (
              <div className="space-y-2 max-h-[350px] overflow-y-auto border rounded p-2">
                {agents.map((agent) => (
                  <div key={agent.id || agent.name} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded">
                    <Checkbox
                      id={agent.id || agent.name}
                      checked={selectedAgents.includes(agent.id || agent.name)}
                      onCheckedChange={() => toggleAgentSelection(agent.id || agent.name)}
                    />
                    <label
                      htmlFor={agent.id || agent.name}
                      className="flex-1 cursor-pointer"
                    >
                      <div>
                        <p className="font-medium text-sm">{agent.name}</p>
                        {agent.id && (
                          <p className="text-xs text-muted-foreground">ID: {agent.id}</p>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <Separator />
          
          <div>
            <h4 className="font-medium text-sm mb-3">Available Agents from Library</h4>
            <div className="space-y-2 max-h-[500px] overflow-y-auto border rounded p-2">
              {availableAgents.map((agentName) => (
                <div key={agentName} className="border rounded p-2 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`lib-${agentName}`}
                        checked={selectedAgents.includes(agentName)}
                        onCheckedChange={() => toggleAgentSelection(agentName)}
                      />
                      <label
                        htmlFor={`lib-${agentName}`}
                        className="cursor-pointer"
                      >
                        <p className="font-medium text-sm">{agentName}</p>
                        <p className="text-xs text-muted-foreground">From agent library</p>
                      </label>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={async () => {
                        setCallingAgent(true);
                        try {
                          const result = await callAgent(agentName);
                          setAgentResponses(prev => ({
                            ...prev,
                            [agentName]: result
                          }));
                        } catch (e) {
                          console.error('Error calling agent:', e);
                          setAgentResponses(prev => ({
                            ...prev,
                            [agentName]: { error: 'Failed to activate agent', details: e }
                          }));
                        } finally {
                          setCallingAgent(false);
                        }
                      }}
                      disabled={callingAgent}
                      title="Activate this agent"
                    >
                      <Play className="w-4 h-4" />
                    </Button>
                  </div>
                  {agentResponses[agentName] && (
                    <div className="mt-2 p-2 bg-gray-100 rounded">
                      <p className="text-xs font-medium mb-1">Call Agent Response:</p>
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap bg-white p-2 rounded border">
                        {JSON.stringify(agentResponses[agentName], null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { setShowAssignDialog(false); setAssigningTask(null); }}>
            Cancel
          </Button>
          <Button 
            variant="default" 
            onClick={handleAssignAgents}
            disabled={saving}
          >
            {saving ? "Saving..." : "Assign Agents"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
};

export default TaskList; 