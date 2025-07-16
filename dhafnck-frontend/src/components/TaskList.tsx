import { Eye, FileText, Link, Minus, Pencil, Plus, Trash2, Users } from "lucide-react";
import React, { useEffect, useState } from "react";
import { listTasks, Task, Subtask, updateTask, getTaskContext, listAgents, getAvailableAgents, getTask, callAgent } from "../api";
import { SubtaskList } from "./SubtaskList";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

// Import all the new modular components
import ClickableAssignees from "./ClickableAssignees";
import AgentResponseDialog from "./AgentResponseDialog";
import TaskDetailsDialog from "./TaskDetailsDialog";
import TaskEditDialog from "./TaskEditDialog";
import AgentAssignmentDialog from "./AgentAssignmentDialog";
import TaskContextDialog from "./TaskContextDialog";

interface TaskListProps {
  projectId: string;
  taskTreeId: string;
}

const TaskList: React.FC<TaskListProps> = ({ projectId, taskTreeId }) => {
  // Core state
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);

  // Agent data
  const [agents, setAgents] = useState<any[]>([]);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);

  // Dependencies
  const [dependencyTitles, setDependencyTitles] = useState<Record<string, string>>({});
  const [hoveredDependency, setHoveredDependency] = useState<string | null>(null);

  // Dialog states
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showTaskDetailsDialog, setShowTaskDetailsDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showAgentResponse, setShowAgentResponse] = useState(false);
  const [showTaskContext, setShowTaskContext] = useState(false);

  // Dialog-specific state
  const [currentAgentResponse, setCurrentAgentResponse] = useState<{
    agent: string;
    task: string;
    response?: any;
    error?: string;
    timestamp: string;
  } | null>(null);
  const [taskContext, setTaskContext] = useState<any>(null);
  const [loadingContext, setLoadingContext] = useState(false);

  // Load tasks and dependencies
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

  // Load agents
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

  // Task expansion
  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  // Task Details Dialog
  const openTaskDetailsDialog = (task: Task) => {
    setSelectedTask(task);
    setShowTaskDetailsDialog(true);
  };

  const closeTaskDetailsDialog = () => {
    setShowTaskDetailsDialog(false);
    setSelectedTask(null);
  };

  // Task Edit Dialog
  const openEditDialog = (task: Task) => {
    setSelectedTask(task);
    setShowEditDialog(true);
  };

  const closeEditDialog = () => {
    setShowEditDialog(false);
    setSelectedTask(null);
  };

  const handleTaskEdit = async (updates: Partial<Task>) => {
    if (!selectedTask) return;
    
    setSaving(true);
    setError(null);
    try {
      const result = await updateTask(selectedTask.id, updates);
      
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

  // Agent Assignment Dialog
  const openAssignDialog = (task: Task) => {
    setSelectedTask(task);
    setShowAssignDialog(true);
  };

  const closeAssignDialog = () => {
    setShowAssignDialog(false);
    setSelectedTask(null);
  };

  const handleAgentAssignment = async (selectedAgents: string[]) => {
    if (!selectedTask) return;
    
    setSaving(true);
    console.log('Assigning agents to task:', selectedTask.id, 'Agents:', selectedAgents);
    
    try {
      const updated = await updateTask(selectedTask.id, { assignees: selectedAgents });
      console.log('Assignment result:', updated);
      
      if (updated) {
        setTasks(prevTasks => 
          prevTasks.map(t => t.id === selectedTask.id ? { ...t, assignees: selectedAgents } : t)
        );
        closeAssignDialog();
      }
    } catch (e) {
      console.error('Error assigning agents:', e);
      alert(`Failed to assign agents: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  // Agent Response Dialog
  const handleCallAgent = async (agentName: string, task: Task | Subtask) => {
    try {
      console.log('Calling agent:', agentName, 'for task:', task.title);
      const result = await callAgent(agentName);
      
      // Set response data and show dialog
      setCurrentAgentResponse({
        agent: agentName,
        task: task.title,
        response: result,
        timestamp: new Date().toISOString()
      });
      setShowAgentResponse(true);
      
    } catch (e) {
      console.error('Error calling agent:', e);
      
      // Set error data and show dialog
      setCurrentAgentResponse({
        agent: agentName,
        task: task.title,
        error: e instanceof Error ? e.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
      setShowAgentResponse(true);
    }
  };

  const closeAgentResponseDialog = () => {
    setShowAgentResponse(false);
    setCurrentAgentResponse(null);
  };

  // Task Context Dialog
  const handleViewContext = async (task: Task) => {
    setSelectedTask(task);
    setLoadingContext(true);
    setShowTaskContext(true);
    
    try {
      const context = await getTaskContext(task.id);
      setTaskContext(context);
    } catch (e) {
      console.error('Error fetching task context:', e);
      setTaskContext(null);
    } finally {
      setLoadingContext(false);
    }
  };

  const closeTaskContextDialog = () => {
    setShowTaskContext(false);
    setSelectedTask(null);
    setTaskContext(null);
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
                  <div className="flex items-center gap-2">
                    <span>{task.title}</span>
                    {task.subtasks && task.subtasks.length > 0 && (
                      <Badge variant="outline" className="text-xs ml-1">
                        {task.subtasks.length}
                      </Badge>
                    )}
                  </div>
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
                  <ClickableAssignees
                    assignees={task.assignees || []}
                    task={task}
                    onAgentClick={handleCallAgent}
                    variant="secondary"
                  />
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
                    onClick={() => handleViewContext(task)}
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
                    <SubtaskList projectId={projectId} taskTreeId={taskTreeId} parentTaskId={task.id} />
                  </TableCell>
                </TableRow>
              )}
            </React.Fragment>
          ))}
        </TableBody>
      </Table>

      {/* All Dialog Components */}
      <TaskDetailsDialog
        open={showTaskDetailsDialog}
        onOpenChange={setShowTaskDetailsDialog}
        task={selectedTask}
        onClose={closeTaskDetailsDialog}
        onAgentClick={handleCallAgent}
      />

      <TaskEditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        task={selectedTask}
        onClose={closeEditDialog}
        onSave={handleTaskEdit}
        saving={saving}
      />

      <AgentAssignmentDialog
        open={showAssignDialog}
        onOpenChange={setShowAssignDialog}
        task={selectedTask}
        onClose={closeAssignDialog}
        onAssign={handleAgentAssignment}
        agents={agents}
        availableAgents={availableAgents}
        saving={saving}
      />

      <AgentResponseDialog
        open={showAgentResponse}
        onOpenChange={setShowAgentResponse}
        agentResponse={currentAgentResponse}
        onClose={closeAgentResponseDialog}
      />

      <TaskContextDialog
        open={showTaskContext}
        onOpenChange={setShowTaskContext}
        task={selectedTask}
        context={taskContext}
        onClose={closeTaskContextDialog}
        loading={loadingContext}
      />
    </>
  );
};

export default TaskList;