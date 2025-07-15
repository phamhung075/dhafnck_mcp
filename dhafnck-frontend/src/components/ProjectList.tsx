import { ChevronDown, ChevronRight, Folder, GitBranchPlus, Pencil, Plus, Trash2, Code2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { mcpApi, Project } from "../api/enhanced";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { JsonViewDialog } from "./JsonViewDialog";

interface ProjectListProps {
  onSelect?: (projectId: string, branchId: string) => void;
}

const ProjectList: React.FC<ProjectListProps> = ({ onSelect }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<Project | null>(null);
  const [showDelete, setShowDelete] = useState<Project | null>(null);
  const [showCreateBranch, setShowCreateBranch] = useState<Project | null>(null);
  const [form, setForm] = useState<{ name: string; description: string }>({ name: "", description: "" });
  const [saving, setSaving] = useState(false);
  const [openProjects, setOpenProjects] = useState<Record<string, boolean>>({});
  const [jsonViewData, setJsonViewData] = useState<{ title: string; data: any } | null>(null);

  const toggleProject = (projectId: string) => {
    setOpenProjects(prev => ({ ...prev, [projectId]: !prev[projectId] }));
  };

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await mcpApi.manageProject('list');
      if (response.success) {
        setProjects(response.data || []);
      } else {
        setError(response.error || 'Failed to fetch projects');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async () => {
    setSaving(true);
    try {
      const response = await mcpApi.manageProject('create', { name: form.name, description: form.description });
      if (response.success) {
        setShowCreate(false);
        setForm({ name: "", description: "" });
        fetchProjects();
      } else {
        setError(response.error || 'Failed to create project');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateBranch = async () => {
    if (!showCreateBranch) return;
    setSaving(true);
    try {
      const response = await mcpApi.manageGitBranch('create', { 
        project_id: showCreateBranch.id, 
        git_branch_name: form.name, 
        git_branch_description: form.description 
      });
      if (response.success) {
        setShowCreateBranch(null);
        setForm({ name: "", description: "" });
        fetchProjects();
      } else {
        setError(response.error || 'Failed to create branch');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = async () => {
    if (!showEdit) return;
    setSaving(true);
    try {
      const response = await mcpApi.manageProject('update', { 
        project_id: showEdit.id, 
        name: form.name, 
        description: form.description 
      });
      if (response.success) {
        setShowEdit(null);
        setForm({ name: "", description: "" });
        fetchProjects();
      } else {
        setError(response.error || 'Failed to update project');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!showDelete) return;
    setSaving(true);
    try {
      const response = await mcpApi.manageProject('delete', { project_id: showDelete.id });
      if (response.success) {
        setShowDelete(null);
        fetchProjects();
      } else {
        setError(response.error || 'Failed to delete project');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-xs text-muted-foreground px-2 py-1">Loading projects...</div>;
  if (error) return <div className="text-xs text-destructive px-2 py-1">Error: {error}</div>;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-base">Projects</span>
        <Button size="sm" variant="default" onClick={() => { setShowCreate(true); setForm({ name: "", description: "" }); }}>
          <Plus className="w-4 h-4 mr-1" /> New
        </Button>
      </div>
      {projects.length === 0 ? (
        <div className="text-xs text-muted-foreground">No projects found.</div>
      ) : (
        <ul className="flex flex-col gap-1">
          {projects.map((project) => (
            <li key={project.id}>
              <div
                className="group flex items-center justify-between p-2 rounded-md hover:bg-muted/80 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2" onClick={() => toggleProject(project.id)}>
                  {openProjects[project.id] ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  <Folder className="w-4 h-4" />
                  <span className="font-semibold text-sm truncate" title={project.name}>{project.name}</span>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button size="icon" variant="ghost" aria-label="View JSON" onClick={() => setJsonViewData({ title: `Project: ${project.name}`, data: project })}>
                    <Code2 className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" aria-label="Create Branch" onClick={() => { setShowCreateBranch(project); setForm({ name: "", description: "" }); }}>
                    <GitBranchPlus className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" aria-label="Edit" onClick={() => { setShowEdit(project); setForm({ name: project.name, description: project.description || "" }); }}>
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" aria-label="Delete" onClick={() => setShowDelete(project)}>
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                </div>
              </div>
              {openProjects[project.id] && project.task_trees && (
                <ul className="flex flex-col gap-1 ml-6 mt-1 pl-4 border-l border-dashed">
                  {Object.values(project.task_trees).map((tree) => (
                    <li key={tree.id}>
                      <div className="group flex items-center gap-1">
                        <Button
                          size="sm"
                          variant={selected === `${project.id}:${tree.id}` ? "secondary" : "ghost"}
                          className="flex-1 justify-start text-xs"
                          onClick={() => {
                            setSelected(`${project.id}:${tree.id}`);
                            onSelect && onSelect(project.id, tree.id);
                          }}
                        >
                          <span className="truncate">{tree.name}</span>
                        </Button>
                        <Button 
                          size="icon" 
                          variant="ghost" 
                          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                          aria-label="View JSON"
                          onClick={() => setJsonViewData({ title: `Branch: ${tree.name}`, data: tree })}
                        >
                          <Code2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
      {/* Dialogs */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Project</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <Input
              placeholder="Project name"
              value={form.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, name: e.target.value }))}
              autoFocus
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button variant="default" onClick={handleCreate} disabled={!form.name.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showCreateBranch} onOpenChange={(v) => !v && setShowCreateBranch(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Branch in {showCreateBranch?.name}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <Input
              placeholder="Branch name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              autoFocus
              disabled={saving}
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              disabled={saving}
            />
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowCreateBranch(null)} disabled={saving}>Cancel</Button>
            <Button onClick={handleCreateBranch} disabled={saving || !form.name.trim()}>
              {saving ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showEdit} onOpenChange={(v: boolean) => { if (!v) setShowEdit(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <Input
              placeholder="Project name"
              value={form.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, name: e.target.value }))}
              autoFocus
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowEdit(null)}>Cancel</Button>
            <Button variant="default" onClick={handleEdit} disabled={!form.name.trim()}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDelete} onOpenChange={(v: boolean) => { if (!v) setShowDelete(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete this project? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowDelete(null)}>Cancel</Button>
            <Button variant="default" className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
};

export default ProjectList; 