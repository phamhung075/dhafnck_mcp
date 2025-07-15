import { Check, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { mcpApi, Task } from "../api/enhanced";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";

interface SimpleTaskManagerProps {
  projectId?: string;
  taskTreeId?: string;
}

const SimpleTaskManager: React.FC<SimpleTaskManagerProps> = ({ 
  projectId = "demo_project", 
  taskTreeId = "main" 
}) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState<'create' | 'edit' | 'delete' | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    priority: "medium"
  });
  const [saving, setSaving] = useState(false);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const taskList = await mcpApi.getTasks(taskTreeId);
      setTasks(taskList);
    } catch (err: any) {
      setError(err.message || "Failed to fetch tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [projectId, taskTreeId]);

  const handleCreate = async () => {
    if (!form.title.trim()) return;
    
    setSaving(true);
    try {
      await mcpApi.createTask(taskTreeId, form.title, form.description, form.priority);
      setShowDialog(null);
      setForm({ title: "", description: "", priority: "medium" });
      fetchTasks();
    } catch (err: any) {
      setError(err.message || "Failed to create task");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = async () => {
    if (!selectedTask || !form.title.trim()) return;
    
    setSaving(true);
    try {
      await mcpApi.manageTask('update', {
        task_id: selectedTask.id,
        title: form.title,
        description: form.description,
        priority: form.priority
      });
      setShowDialog(null);
      setSelectedTask(null);
      setForm({ title: "", description: "", priority: "medium" });
      fetchTasks();
    } catch (err: any) {
      setError(err.message || "Failed to update task");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedTask) return;
    
    setSaving(true);
    try {
      await mcpApi.manageTask('delete', { task_id: selectedTask.id });
      setShowDialog(null);
      setSelectedTask(null);
      fetchTasks();
    } catch (err: any) {
      setError(err.message || "Failed to delete task");
    } finally {
      setSaving(false);
    }
  };

  const openCreateDialog = () => {
    setForm({ title: "", description: "", priority: "medium" });
    setShowDialog('create');
  };

  const openEditDialog = (task: Task) => {
    setSelectedTask(task);
    setForm({
      title: task.title,
      description: task.description || "",
      priority: task.priority || "medium"
    });
    setShowDialog('edit');
  };

  const openDeleteDialog = (task: Task) => {
    setSelectedTask(task);
    setShowDialog('delete');
  };

  const closeDialog = () => {
    setShowDialog(null);
    setSelectedTask(null);
    setForm({ title: "", description: "", priority: "medium" });
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
      case 'completed': return 'default';
      case 'in_progress': return 'secondary';
      case 'pending': return 'outline';
      case 'cancelled': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Task Manager</h2>
        <Button onClick={openCreateDialog} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Task
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="text-muted-foreground">Loading tasks...</div>
        </div>
      )}

      {/* Tasks List */}
      {!loading && (
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <div className="text-muted-foreground">No tasks found</div>
                <Button onClick={openCreateDialog} className="mt-4">
                  Create your first task
                </Button>
              </CardContent>
            </Card>
          ) : (
            tasks.map((task) => (
              <Card key={task.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{task.title}</CardTitle>
                      {task.description && (
                        <p className="text-sm text-muted-foreground">{task.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => openEditDialog(task)}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => openDeleteDialog(task)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex gap-2">
                    <Badge variant={getStatusColor(task.status)}>
                      {task.status?.replace('_', ' ') || 'pending'}
                    </Badge>
                    <Badge variant={getPriorityColor(task.priority)}>
                      {task.priority || 'medium'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog === 'create' || showDialog === 'edit'} onOpenChange={closeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {showDialog === 'create' ? 'Create New Task' : 'Edit Task'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Title</label>
              <Input
                placeholder="Enter task title"
                value={form.title}
                onChange={(e) => setForm(prev => ({ ...prev, title: e.target.value }))}
                disabled={saving}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Description</label>
              <Input
                placeholder="Enter task description"
                value={form.description}
                onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
                disabled={saving}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={form.priority}
                onChange={(e) => setForm(prev => ({ ...prev, priority: e.target.value }))}
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
            <Button variant="outline" onClick={closeDialog} disabled={saving}>
              Cancel
            </Button>
            <Button 
              onClick={showDialog === 'create' ? handleCreate : handleEdit} 
              disabled={saving || !form.title.trim()}
            >
              {saving ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  {showDialog === 'create' ? 'Creating...' : 'Updating...'}
                </div>
              ) : (
                <>
                  {showDialog === 'create' ? <Plus className="w-4 h-4 mr-2" /> : <Check className="w-4 h-4 mr-2" />}
                  {showDialog === 'create' ? 'Create' : 'Update'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDialog === 'delete'} onOpenChange={closeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Task</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p>Are you sure you want to delete this task?</p>
            <p className="font-medium mt-2">"{selectedTask?.title}"</p>
            <p className="text-sm text-muted-foreground mt-1">This action cannot be undone.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeDialog} disabled={saving}>
              Cancel
            </Button>
            <Button 
              variant="default" 
              onClick={handleDelete} 
              disabled={saving}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {saving ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Deleting...
                </div>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SimpleTaskManager;