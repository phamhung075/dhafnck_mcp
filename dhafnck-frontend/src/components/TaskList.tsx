import { Code2, Eye, Minus, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { mcpApi, Task } from "../api/enhanced";
import { JsonViewDialog } from "./JsonViewDialog";
import { SubtaskList } from "./SubtaskList";
import { TaskDetailView } from "./TaskDetailView";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

interface TaskListProps {
  projectId: string;
  taskTreeId: string;
  onTaskSelect?: (task: Task) => void;
  selectedTaskId?: string;
}

const TaskList: React.FC<TaskListProps> = ({ projectId, taskTreeId, onTaskSelect, selectedTaskId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [jsonViewData, setJsonViewData] = useState<{ title: string; data: any } | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newTaskForm, setNewTaskForm] = useState({ title: "", description: "", priority: "medium", status: "todo" });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    setLoading(true);
    mcpApi.getTasks(taskTreeId)
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId, taskTreeId]);

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  const handleCreateTask = async () => {
    setCreating(true);
    try {
      await mcpApi.createTask(taskTreeId, newTaskForm.title, newTaskForm.description, newTaskForm.priority);
      setShowCreateDialog(false);
      setNewTaskForm({ title: "", description: "", priority: "medium", status: "todo" });
      // Refresh the task list
      mcpApi.getTasks(taskTreeId)
        .then(setTasks)
        .catch((e) => setError(e.message));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Tasks</h2>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Task
        </Button>
      </div>
      <Table>
        <TableHeader>
        <TableRow>
          <TableHead style={{ width: '50px' }}></TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map(task => (
          <React.Fragment key={task.id}>
            <TableRow 
              className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 ${
                selectedTaskId === task.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
              }`}
              onClick={() => {
                if (onTaskSelect) {
                  onTaskSelect(task);
                }
              }}
            >
              <TableCell>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleTaskExpansion(task.id);
                  }}
                >
                  {expandedTasks[task.id] ? <Minus /> : <Plus />}
                </Button>
              </TableCell>
              <TableCell className="font-medium">{task.title}</TableCell>
              <TableCell>
                <Badge>{task.status}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{task.priority}</Badge>
              </TableCell>
              <TableCell>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedTask(task);
                    setShowDetails(true);
                  }}
                  title="View Details"
                >
                  <Eye className="w-4 h-4" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  title="View JSON"
                  onClick={() => setJsonViewData({ title: `Task: ${task.title}`, data: task })}
                >
                  <Code2 className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon" title="Edit">
                  <Pencil className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon" title="Delete">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </TableCell>
            </TableRow>
            {expandedTasks[task.id] && (
              <TableRow>
                <TableCell colSpan={5}>
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
    
    <TaskDetailView 
      task={selectedTask}
      open={showDetails}
      onOpenChange={setShowDetails}
    />
    
    {jsonViewData && (
      <JsonViewDialog
        title={jsonViewData.title}
        data={jsonViewData.data}
        open={!!jsonViewData}
        onOpenChange={(open) => !open && setJsonViewData(null)}
      />
    )}

    <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Title</label>
            <Input
              value={newTaskForm.title}
              onChange={(e) => setNewTaskForm({ ...newTaskForm, title: e.target.value })}
              placeholder="Enter task title"
              disabled={creating}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <Input
              value={newTaskForm.description}
              onChange={(e) => setNewTaskForm({ ...newTaskForm, description: e.target.value })}
              placeholder="Enter task description"
              disabled={creating}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Priority</label>
            <select
              value={newTaskForm.priority}
              onChange={(e) => setNewTaskForm({ ...newTaskForm, priority: e.target.value })}
              className="w-full border rounded px-3 py-2"
              disabled={creating}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Status</label>
            <select
              value={newTaskForm.status}
              onChange={(e) => setNewTaskForm({ ...newTaskForm, status: e.target.value })}
              className="w-full border rounded px-3 py-2"
              disabled={creating}
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="blocked">Blocked</option>
              <option value="review">Review</option>
              <option value="testing">Testing</option>
              <option value="done">Done</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setShowCreateDialog(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleCreateTask} disabled={creating || !newTaskForm.title.trim()}>
            {creating ? "Creating..." : "Create Task"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
};

export default TaskList; 