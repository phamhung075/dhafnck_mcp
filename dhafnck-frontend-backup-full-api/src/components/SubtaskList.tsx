import { Check, Eye, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { deleteSubtask, listSubtasks, createSubtask as newSubtask, updateSubtask as saveSubtask, Subtask } from "../api";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

interface SubtaskListProps {
  projectId: string;
  taskTreeId: string;
  parentTaskId: string;
}

const statusColor: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  done: "default",
  in_progress: "secondary",
  review: "secondary",
  testing: "secondary",
  todo: "outline",
  blocked: "destructive",
  cancelled: "destructive",
  archived: "outline"
};

const priorityColor: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  low: "outline",
  medium: "secondary",
  high: "default",
  urgent: "destructive"
};

export function SubtaskList({ projectId, taskTreeId, parentTaskId }: SubtaskListProps) {
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<Subtask | null>(null);
  const [showDelete, setShowDelete] = useState<Subtask | null>(null);
  const [showDetails, setShowDetails] = useState<Subtask | null>(null);
  const [form, setForm] = useState<Partial<Subtask>>({ title: "", description: "", priority: "medium", status: "todo" });
  const [saving, setSaving] = useState(false);

  const fetchSubtasks = () => {
    setLoading(true);
    listSubtasks(parentTaskId)
      .then(setSubtasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchSubtasks();
  }, [projectId, taskTreeId, parentTaskId]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await newSubtask(parentTaskId, { ...form });
      setShowCreate(false);
      setForm({ title: "", description: "", priority: "medium", status: "todo" });
      fetchSubtasks();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (subtask: Subtask) => {
    setShowEdit(subtask);
    setForm({
      title: subtask.title,
      description: subtask.description || "",
      priority: subtask.priority || "medium",
      status: subtask.status || "todo"
    });
  };

  const handleDelete = async (subtaskId: string) => {
    if (!subtaskId) return;
    setSaving(true);
    try {
      await deleteSubtask(parentTaskId, subtaskId);
      setShowDelete(null);
      fetchSubtasks();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-xs text-muted-foreground px-2 py-1">Loading subtasks...</div>;
  if (error) return <div className="text-xs text-destructive px-2 py-1">Error: {error}</div>;

  return (
    <div className="overflow-x-auto">
      <div className="flex justify-end mb-2 gap-2">
        <Button size="sm" variant="default" className="flex items-center gap-1" onClick={() => { setShowCreate(true); setForm({ title: "", description: "", priority: "medium", status: "pending" }); }}>
          <Plus className="w-4 h-4" /> New Subtask
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Priority</TableHead>
            <TableHead>Assignees</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead className="w-24">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {subtasks.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-xs text-muted-foreground">No subtasks found.</TableCell>
            </TableRow>
          ) : (
            subtasks.map((subtask) => (
              <TableRow key={subtask.id} className="hover:bg-accent/30 transition-all">
                <TableCell className="font-medium max-w-xs truncate" title={subtask.title}>{subtask.title}</TableCell>
                <TableCell>
                  <Badge variant={statusColor[subtask.status || "pending"] || "outline"} className="capitalize">
                    {subtask.status?.replace("_", " ") || "pending"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={priorityColor[subtask.priority || "medium"] || "outline"} className="capitalize">
                    {subtask.priority || "medium"}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  {subtask.assignees?.length ? subtask.assignees.join(", ") : <span className="text-muted-foreground text-xs">—</span>}
                </TableCell>
                <TableCell>
                  {subtask.due_date ? (
                    <span className="text-xs">{subtask.due_date}</span>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" className="hover:bg-primary/10" onClick={() => setShowDetails(subtask)} title="View details">
                      <Eye className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <Button size="icon" variant="ghost" className="hover:bg-primary/10" onClick={() => handleEdit(subtask)} title="Edit subtask">
                      <Pencil className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <Button size="icon" variant="ghost" className="hover:text-destructive" onClick={() => setShowDelete(subtask)} title="Delete subtask">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      {/* Create Subtask Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Subtask</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-sm font-medium mb-2 block">Title</label>
              <Input
                placeholder="Subtask title"
                value={form.title || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, title: e.target.value }))}
                disabled={saving}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Description</label>
              <Input
                placeholder="Subtask description"
                value={form.description || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
                disabled={saving}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={form.status || "todo"}
                onChange={(e) => setForm(f => ({ ...f, status: e.target.value }))}
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
                value={form.priority || "medium"}
                onChange={(e) => setForm(f => ({ ...f, priority: e.target.value }))}
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
            <Button variant="secondary" onClick={() => setShowCreate(false)} disabled={saving}>Cancel</Button>
            <Button variant="default" onClick={handleCreate} disabled={saving || !form.title?.trim()}>
              {saving ? <Check className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Edit Subtask Dialog */}
      <Dialog open={!!showEdit} onOpenChange={v => { if (!v) setShowEdit(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Subtask</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div>
              <label className="text-sm font-medium mb-2 block">Title</label>
              <Input
                placeholder="Subtask title"
                value={form.title || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, title: e.target.value }))}
                disabled={saving}
                autoFocus
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Description</label>
              <Input
                placeholder="Subtask description"
                value={form.description || ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
                disabled={saving}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={form.status || "todo"}
                onChange={(e) => setForm(f => ({ ...f, status: e.target.value }))}
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
                value={form.priority || "medium"}
                onChange={(e) => setForm(f => ({ ...f, priority: e.target.value }))}
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
            <Button variant="secondary" onClick={() => setShowEdit(null)} disabled={saving}>Cancel</Button>
            <Button variant="default" onClick={() => {
              setSaving(true);
              const updateData = {
                title: form.title,
                description: form.description,
                priority: form.priority,
                status: form.status
              };
              saveSubtask(parentTaskId, showEdit!.id, updateData)
                .then(() => {
                  setShowEdit(null);
                  setForm({ title: "", description: "", priority: "medium", status: "todo" });
                  fetchSubtasks();
                })
                .catch((e) => {
                  setError(e.message);
                })
                .finally(() => setSaving(false));
            }} disabled={saving || !form.title?.trim()}>
              {saving ? <Check className="w-4 h-4 animate-spin" /> : <Pencil className="w-4 h-4" />} Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Delete Subtask Dialog */}
      <Dialog open={!!showDelete} onOpenChange={v => { if (!v) setShowDelete(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Subtask</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete this subtask: <strong>{showDelete?.title}</strong>?</p>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowDelete(null)} disabled={saving}>Cancel</Button>
            <Button variant="default" className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={() => handleDelete(showDelete!.id)} disabled={saving}>
              {saving ? <Check className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />} Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Subtask Details Dialog */}
      <Dialog open={!!showDetails} onOpenChange={v => { if (!v) setShowDetails(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Subtask Details - Complete Information</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Subtask Information Header */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold">{showDetails?.title}</h3>
              {showDetails?.description && (
                <p className="text-sm text-muted-foreground mt-2">{showDetails.description}</p>
              )}
              <div className="flex gap-2 mt-3 flex-wrap">
                <Badge variant={statusColor[showDetails?.status || "pending"] || "outline"} className="capitalize px-3 py-1">
                  Status: {showDetails?.status?.replace("_", " ") || "pending"}
                </Badge>
                <Badge variant={priorityColor[showDetails?.priority || "medium"] || "outline"} className="capitalize px-3 py-1">
                  Priority: {showDetails?.priority || "medium"}
                </Badge>
                {showDetails?.completed !== undefined && (
                  <Badge variant={showDetails.completed ? "default" : "secondary"} className="px-3 py-1">
                    {showDetails.completed ? "Completed" : "Not Completed"}
                  </Badge>
                )}
              </div>
            </div>

            <Separator />

            {/* IDs and References */}
            <div>
              <h4 className="font-semibold text-sm mb-3 text-blue-700">IDs and References</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-blue-50 p-3 rounded">
                <div className="space-y-1">
                  <span className="text-muted-foreground font-medium">Subtask ID:</span>
                  <p className="font-mono text-xs break-all">{showDetails?.id}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-muted-foreground font-medium">Parent Task ID:</span>
                  <p className="font-mono text-xs break-all">{showDetails?.parent_task_id || parentTaskId}</p>
                </div>
              </div>
            </div>

            <Separator />

            {/* Time Information */}
            <div>
              <h4 className="font-semibold text-sm mb-3 text-green-700">Time Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-green-50 p-3 rounded">
                {showDetails?.estimated_effort && (
                  <div>
                    <span className="text-muted-foreground font-medium">Estimated Effort:</span>
                    <p className="font-semibold">{showDetails.estimated_effort}</p>
                  </div>
                )}
                {showDetails?.due_date && (
                  <div>
                    <span className="text-muted-foreground font-medium">Due Date:</span>
                    <p>{new Date(showDetails.due_date).toLocaleDateString()} ({new Date(showDetails.due_date).toLocaleTimeString()})</p>
                  </div>
                )}
                {showDetails?.created_at && (
                  <div>
                    <span className="text-muted-foreground font-medium">Created:</span>
                    <p>{new Date(showDetails.created_at).toLocaleDateString()} at {new Date(showDetails.created_at).toLocaleTimeString()}</p>
                  </div>
                )}
                {showDetails?.updated_at && (
                  <div>
                    <span className="text-muted-foreground font-medium">Last Updated:</span>
                    <p>{new Date(showDetails.updated_at).toLocaleDateString()} at {new Date(showDetails.updated_at).toLocaleTimeString()}</p>
                  </div>
                )}
              </div>
            </div>

            <Separator />

            {/* Progress and Assignment */}
            <div>
              <h4 className="font-semibold text-sm mb-3 text-purple-700">Progress & Assignment</h4>
              <div className="space-y-3 bg-purple-50 p-3 rounded">
                {/* Progress */}
                {(showDetails?.progress !== undefined || showDetails?.progress_percentage !== undefined) && (
                  <div>
                    <span className="text-muted-foreground font-medium">Progress:</span>
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${showDetails?.progress || showDetails?.progress_percentage || 0}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{showDetails?.progress || showDetails?.progress_percentage || 0}%</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Assignees */}
                {showDetails?.assignees && showDetails.assignees.length > 0 && (
                  <div>
                    <span className="text-muted-foreground font-medium">Assignees:</span>
                    <div className="mt-1">
                      {Array.isArray(showDetails.assignees) ? (
                        <div className="flex flex-wrap gap-1">
                          {showDetails.assignees.map((assignee: string, index: number) => (
                            <Badge key={index} variant="secondary" className="px-2">
                              {assignee}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <Badge variant="secondary" className="px-2">
                          {showDetails.assignees}
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Additional Properties */}
            <Separator />
            <div>
              <h4 className="font-semibold text-sm mb-3 text-orange-700">Additional Properties</h4>
              <div className="bg-orange-50 p-3 rounded">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {/* Check for any additional fields */}
                  {Object.entries(showDetails || {}).map(([key, value]) => {
                    // Skip already displayed fields
                    const skipFields = ['id', 'title', 'description', 'status', 'priority', 'assignees', 
                                      'due_date', 'created_at', 'updated_at', 'estimated_effort', 
                                      'progress', 'progress_percentage', 'parent_task_id', 'completed'];
                    if (skipFields.includes(key) || value === null || value === undefined) return null;
                    
                    return (
                      <div key={key} className="space-y-1">
                        <span className="text-muted-foreground font-medium capitalize">
                          {key.replace(/_/g, ' ')}:
                        </span>
                        <p className="text-sm break-all">
                          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        </p>
                      </div>
                    );
                  }).filter(Boolean)}
                </div>
              </div>
            </div>

            {/* Raw Data */}
            <Separator />
            <details className="cursor-pointer">
              <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                View Complete Raw Subtask Data (JSON)
              </summary>
              <div className="mt-3 bg-gray-100 p-3 rounded">
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(showDetails, null, 2)}
                </pre>
              </div>
            </details>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetails(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 