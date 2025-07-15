import { Check, Code2, Eye, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { mcpApi, Subtask } from "../api/enhanced";
import { JsonViewDialog } from "./JsonViewDialog";
import { SubtaskDetailView } from "./TaskDetailView";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

interface SubtaskListProps {
  projectId: string;
  taskTreeId: string;
  parentTaskId: string;
}

const statusColor: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  completed: "default",
  in_progress: "secondary",
  pending: "outline",
  cancelled: "destructive"
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
  const [form, setForm] = useState<Partial<Subtask>>({ title: "", description: "", priority: "medium" });
  const [saving, setSaving] = useState(false);
  const [selectedSubtask, setSelectedSubtask] = useState<Subtask | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [jsonViewData, setJsonViewData] = useState<{ title: string; data: any } | null>(null);

  const fetchSubtasks = () => {
    setLoading(true);
    console.log("SUBLIST: Fetching for", { projectId, taskTreeId, parentTaskId });
    mcpApi.getSubtasks(parentTaskId)
      .then(data => {
        console.log("SUBLIST: API response", data);
        setSubtasks(data)
      })
      .catch((e) => {
        console.error("SUBLIST: API error", e);
        setError(e.message)
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    console.log("SUBLIST: useEffect triggered for", parentTaskId);
    fetchSubtasks();
  }, [projectId, taskTreeId, parentTaskId]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await mcpApi.createSubtask(parentTaskId, form.title || "", form.description || "");
      setShowCreate(false);
      setForm({ title: "", description: "", priority: "medium" });
      fetchSubtasks();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (subtask: Subtask) => {
    setShowEdit(subtask);
    setForm(subtask);
  };

  const handleDelete = async (subtaskId: string) => {
    if (!subtaskId) return;
    setSaving(true);
    try {
      await mcpApi.manageSubtask('delete', { task_id: parentTaskId, subtask_id: subtaskId });
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
        <Button size="sm" variant="default" className="flex items-center gap-1" onClick={() => { setShowCreate(true); setForm({ title: "", description: "", priority: "medium" }); }}>
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
                    <Button 
                      size="icon" 
                      variant="ghost" 
                      className="hover:bg-primary/10" 
                      onClick={() => {
                        setSelectedSubtask(subtask);
                        setShowDetails(true);
                      }}
                      title="View Details"
                    >
                      <Eye className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <Button 
                      size="icon" 
                      variant="ghost" 
                      className="hover:bg-primary/10" 
                      onClick={() => setJsonViewData({ title: `Subtask: ${subtask.title}`, data: subtask })}
                      title="View JSON"
                    >
                      <Code2 className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <Button size="icon" variant="ghost" className="hover:bg-primary/10" onClick={() => handleEdit(subtask)} title="Edit">
                      <Pencil className="w-4 h-4 text-muted-foreground" />
                    </Button>
                    <Button size="icon" variant="ghost" className="hover:text-destructive" onClick={() => setShowDelete(subtask)} title="Delete">
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
            <Input
              placeholder="Title"
              value={form.title || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, title: e.target.value }))}
              disabled={saving}
              autoFocus
            />
            <Input
              placeholder="Description"
              value={form.description || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
              disabled={saving}
            />
            <Input
              placeholder="Priority (low, medium, high, urgent)"
              value={form.priority || "medium"}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, priority: e.target.value }))}
              disabled={saving}
            />
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
            <Input
              placeholder="Title"
              value={form.title || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, title: e.target.value }))}
              disabled={saving}
              autoFocus
            />
            <Input
              placeholder="Description"
              value={form.description || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
              disabled={saving}
            />
            <Input
              placeholder="Priority (low, medium, high, urgent)"
              value={form.priority || "medium"}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, priority: e.target.value }))}
              disabled={saving}
            />
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowEdit(null)} disabled={saving}>Cancel</Button>
            <Button variant="default" onClick={() => {
              setSaving(true);
              mcpApi.manageSubtask('update', { 
                task_id: parentTaskId, 
                subtask_id: showEdit!.id,
                title: form.title || "",
                description: form.description || "",
                priority: form.priority || "medium"
              })
                .then(() => {
                  setShowEdit(null);
                  setForm({ title: "", description: "", priority: "medium" });
                  fetchSubtasks();
                })
                .catch((e: any) => {
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
      
      <SubtaskDetailView 
        subtask={selectedSubtask}
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
    </div>
  );
} 