import { ChevronDown, ChevronRight, Eye, FileText, Folder, GitBranchPlus, Globe, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createBranch, createProject, deleteProject, getGlobalContext, getProjectContext, getTaskContext, getTaskCount, listProjects, Project, updateProject } from "../api";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";

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
  const [showProjectDetails, setShowProjectDetails] = useState<Project | null>(null);
  const [showBranchDetails, setShowBranchDetails] = useState<{ project: Project; branch: any } | null>(null);
  const [showProjectContext, setShowProjectContext] = useState<{ project: Project; context: any } | null>(null);
  const [showBranchContext, setShowBranchContext] = useState<{ project: Project; branch: any; context: any } | null>(null);
  const [showGlobalContext, setShowGlobalContext] = useState<{ context: any } | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);
  const [form, setForm] = useState<{ name: string; description: string }>({ name: "", description: "" });
  const [saving, setSaving] = useState(false);
  const [openProjects, setOpenProjects] = useState<Record<string, boolean>>({});
  const [taskCounts, setTaskCounts] = useState<Record<string, number>>({});

  const toggleProject = (projectId: string) => {
    setOpenProjects(prev => ({ ...prev, [projectId]: !prev[projectId] }));
  };

  const refreshTaskCounts = async () => {
    const countPromises: Promise<{ id: string; count: number }>[] = [];
    
    for (const project of projects) {
      if (project.git_branchs) {
        for (const tree of Object.values(project.git_branchs)) {
          countPromises.push(
            getTaskCount(tree.id)
              .then(count => ({ id: tree.id, count }))
              .catch(e => {
                console.error(`Error fetching task count for branch ${tree.id}:`, e);
                return { id: tree.id, count: 0 };
              })
          );
        }
      }
    }
    
    const results = await Promise.all(countPromises);
    const counts: Record<string, number> = {};
    results.forEach(({ id, count }) => {
      counts[id] = count;
    });
    setTaskCounts(counts);
  };

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const projectsData = await listProjects();
      setProjects(projectsData);
      
      // Fetch task counts for all branches in parallel
      const countPromises: Promise<{ id: string; count: number }>[] = [];
      
      for (const project of projectsData) {
        if (project.git_branchs) {
          for (const tree of Object.values(project.git_branchs)) {
            countPromises.push(
              getTaskCount(tree.id)
                .then(count => ({ id: tree.id, count }))
                .catch(e => {
                  console.error(`Error fetching task count for branch ${tree.id}:`, e);
                  return { id: tree.id, count: 0 };
                })
            );
          }
        }
      }
      
      const results = await Promise.all(countPromises);
      const counts: Record<string, number> = {};
      results.forEach(({ id, count }) => {
        counts[id] = count;
      });
      setTaskCounts(counts);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Refresh task counts when projects change
  useEffect(() => {
    if (projects.length > 0) {
      refreshTaskCounts();
    }
  }, [projects]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      await createProject({ name: form.name, description: form.description });
      setShowCreate(false);
      setForm({ name: "", description: "" });
      fetchProjects();
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
      await createBranch(showCreateBranch.id, form.name, form.description);
      setShowCreateBranch(null);
      setForm({ name: "", description: "" });
      fetchProjects();
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
      await updateProject(showEdit.id, { name: form.name, description: form.description });
      setShowEdit(null);
      setForm({ name: "", description: "" });
      fetchProjects();
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
      await deleteProject(showDelete.id);
      setShowDelete(null);
      fetchProjects();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-xs text-muted-foreground px-2 py-1">Loading projects...</div>;
  if (error) return <div className="text-xs text-destructive px-2 py-1">Error: {error}</div>;

  return (
    <div className="flex flex-col gap-2 overflow-visible">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-base">Projects</span>
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline" 
            onClick={async () => {
              setLoadingContext(true);
              try {
                const context = await getGlobalContext();
                setShowGlobalContext({ context });
              } catch (e) {
                console.error('Error fetching global context:', e);
              } finally {
                setLoadingContext(false);
              }
            }}
            aria-label="View Global Context"
          >
            <Globe className="w-4 h-4 mr-1" /> Global
          </Button>
          <Button size="sm" variant="default" onClick={() => { setShowCreate(true); setForm({ name: "", description: "" }); }}>
            <Plus className="w-4 h-4 mr-1" /> New
          </Button>
        </div>
      </div>
      {projects.length === 0 ? (
        <div className="text-xs text-muted-foreground">No projects found.</div>
      ) : (
        <ul className="flex flex-col gap-1">
          {projects.map((project) => (
            <li key={project.id}>
              <div
                className="group relative flex items-center justify-between p-2 rounded-md hover:bg-muted/80 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2 flex-1" onClick={() => toggleProject(project.id)}>
                  {openProjects[project.id] ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  <Folder className="w-4 h-4" />
                  <span className="font-semibold text-sm truncate text-left" title={project.name}>{project.name}</span>
                  {!openProjects[project.id] && project.git_branchs && Object.keys(project.git_branchs).length > 0 && (
                    <Badge variant="outline" className="text-xs ml-2">
                      {Object.keys(project.git_branchs).length}
                    </Badge>
                  )}
                </div>
                <div className="absolute right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white shadow-lg rounded-md p-1 z-50">
                  <Button size="icon" variant="ghost" aria-label="View Details" onClick={() => setShowProjectDetails(project)}>
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" aria-label="View Context" onClick={async () => {
                    setLoadingContext(true);
                    try {
                      const context = await getProjectContext(project.id);
                      setShowProjectContext({ project, context });
                    } catch (e) {
                      console.error('Error fetching project context:', e);
                    } finally {
                      setLoadingContext(false);
                    }
                  }}>
                    <FileText className="w-4 h-4" />
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
              {openProjects[project.id] && project.git_branchs && (
                <ul className="flex flex-col gap-1 ml-8 mt-1">
                  {Object.values(project.git_branchs).map((tree) => (
                    <li key={tree.id}>
                      <div className="group relative flex items-center gap-1">
                        <span className="text-muted-foreground">—</span>
                        <Button
                          size="sm"
                          variant={selected === `${project.id}:${tree.id}` ? "secondary" : "ghost"}
                          className="flex-1 justify-start text-xs text-left"
                          onClick={() => {
                            setSelected(`${project.id}:${tree.id}`);
                            onSelect && onSelect(project.id, tree.id);
                          }}
                        >
                          <span className="truncate text-left flex-1">{tree.name}</span>
                          <Badge variant="secondary" className="text-xs ml-2">
                            {taskCounts[tree.id] ?? '...'}
                          </Badge>
                        </Button>
                        <div className="absolute right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white shadow-lg rounded-md p-1 z-50">
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-6 w-6"
                            onClick={() => setShowBranchDetails({ project, branch: tree })}
                            aria-label="View Branch Details"
                          >
                            <Eye className="w-3 h-3" />
                          </Button>
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-6 w-6"
                            onClick={async () => {
                              setLoadingContext(true);
                              try {
                                const context = await getTaskContext(tree.id);
                                setShowBranchContext({ project, branch: tree, context });
                              } catch (e) {
                                console.error('Error fetching branch context:', e);
                              } finally {
                                setLoadingContext(false);
                              }
                            }}
                            aria-label="View Branch Context"
                          >
                            <FileText className="w-3 h-3" />
                          </Button>
                        </div>
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
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-base">New Project</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Input
              placeholder="Project name"
              value={form.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, name: e.target.value }))}
              autoFocus
              className="h-8 text-sm"
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
              className="h-8 text-sm"
            />
          </div>
          <DialogFooter className="mt-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)} size="sm">Cancel</Button>
            <Button variant="default" onClick={handleCreate} disabled={!form.name.trim()} size="sm">
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showCreateBranch} onOpenChange={(v) => !v && setShowCreateBranch(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-base">New Branch in {showCreateBranch?.name}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Input
              placeholder="Branch name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              autoFocus
              disabled={saving}
              className="h-8 text-sm"
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              disabled={saving}
              className="h-8 text-sm"
            />
          </div>
          <DialogFooter className="mt-3">
            <Button variant="secondary" onClick={() => setShowCreateBranch(null)} disabled={saving} size="sm">Cancel</Button>
            <Button onClick={handleCreateBranch} disabled={saving || !form.name.trim()} size="sm">
              {saving ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showEdit} onOpenChange={(v: boolean) => { if (!v) setShowEdit(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-base">Edit Project</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Input
              placeholder="Project name"
              value={form.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, name: e.target.value }))}
              autoFocus
              className="h-8 text-sm"
            />
            <Input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, description: e.target.value }))}
              className="h-8 text-sm"
            />
          </div>
          <DialogFooter className="mt-3">
            <Button variant="secondary" onClick={() => setShowEdit(null)} size="sm">Cancel</Button>
            <Button variant="default" onClick={handleEdit} disabled={!form.name.trim()} size="sm">
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!showDelete} onOpenChange={(v: boolean) => { if (!v) setShowDelete(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-base">Delete Project</DialogTitle>
          </DialogHeader>
          <p className="text-sm">Are you sure you want to delete this project? This action cannot be undone.</p>
          <DialogFooter className="mt-3">
            <Button variant="secondary" onClick={() => setShowDelete(null)} size="sm">Cancel</Button>
            <Button variant="default" className="bg-destructive text-destructive-foreground hover:bg-destructive/90" onClick={handleDelete} size="sm">Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Project Details Dialog */}
      <Dialog open={!!showProjectDetails} onOpenChange={(v) => { if (!v) setShowProjectDetails(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Project Details - {showProjectDetails?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Basic Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">Basic Information</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Name:</span>
                  <span className="ml-2 font-medium">{showProjectDetails?.name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">ID:</span>
                  <span className="ml-2 font-mono text-xs">{showProjectDetails?.id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Description:</span>
                  <span className="ml-2">{showProjectDetails?.description || "No description"}</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Orchestration Status */}
            {showProjectDetails && (showProjectDetails as any)['orchestration_status'] && (
              <>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-green-700">Orchestration Status</h3>
                  <div className="bg-white p-3 rounded border border-green-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showProjectDetails as any)['orchestration_status'] === 'object' 
                        ? JSON.stringify((showProjectDetails as any)['orchestration_status'], null, 2)
                        : (showProjectDetails as any)['orchestration_status']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Registered Agents */}
            {showProjectDetails && (showProjectDetails as any)['registered_agents'] && (
              <>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-purple-700">Registered Agents</h3>
                  <div className="bg-white p-3 rounded border border-purple-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showProjectDetails as any)['registered_agents'] === 'object' 
                        ? JSON.stringify((showProjectDetails as any)['registered_agents'], null, 2)
                        : (showProjectDetails as any)['registered_agents']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Agent Assignments */}
            {showProjectDetails && (showProjectDetails as any)['agent_assignments'] && (
              <>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-orange-700">Agent Assignments</h3>
                  <div className="bg-white p-3 rounded border border-orange-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showProjectDetails as any)['agent_assignments'] === 'object' 
                        ? JSON.stringify((showProjectDetails as any)['agent_assignments'], null, 2)
                        : (showProjectDetails as any)['agent_assignments']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Task Trees / Branches */}
            {showProjectDetails?.git_branchs && Object.keys(showProjectDetails.git_branchs).length > 0 && (
              <>
                <div className="bg-indigo-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-indigo-700">Task Trees / Branches ({Object.keys(showProjectDetails.git_branchs).length})</h3>
                  <div className="bg-white p-3 rounded border border-indigo-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(showProjectDetails.git_branchs, null, 2)}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Additional Fields - Display any other fields */}
            {showProjectDetails && (
              <>
                {Object.entries(showProjectDetails).filter(([key]) => 
                  !['id', 'name', 'description', 'git_branchs', 'orchestration_status', 'registered_agents', 'agent_assignments'].includes(key)
                ).map(([key, value]) => {
                  if (value === null || value === undefined) return null;
                  
                  return (
                    <React.Fragment key={key}>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-lg font-semibold mb-3 capitalize">{key.replace(/_/g, ' ')}</h3>
                        <div className="bg-white p-3 rounded border border-gray-200">
                          {typeof value === 'object' ? (
                            <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <span className="text-sm">{String(value)}</span>
                          )}
                        </div>
                      </div>
                      <Separator />
                    </React.Fragment>
                  );
                })}
              </>
            )}

            {/* Raw Data */}
            <details className="cursor-pointer">
              <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                View Complete Raw Project Data (JSON)
              </summary>
              <div className="mt-3 bg-gray-100 p-3 rounded">
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(showProjectDetails, null, 2)}
                </pre>
              </div>
            </details>
          </div>
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowProjectDetails(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Branch Details Dialog */}
      <Dialog open={!!showBranchDetails} onOpenChange={(v) => { if (!v) setShowBranchDetails(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Branch Details - {showBranchDetails?.branch?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Basic Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">Basic Information</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Name:</span>
                  <span className="ml-2 font-medium">{showBranchDetails?.branch?.name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">ID:</span>
                  <span className="ml-2 font-mono text-xs">{showBranchDetails?.branch?.id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Description:</span>
                  <span className="ml-2">{showBranchDetails?.branch?.description || "No description"}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Project:</span>
                  <span className="ml-2">{showBranchDetails?.project?.name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Project ID:</span>
                  <span className="ml-2 font-mono text-xs">{showBranchDetails?.project?.id}</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Branch Status */}
            {showBranchDetails?.branch && (showBranchDetails.branch as any)['status'] && (
              <>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-blue-700">Branch Status</h3>
                  <div className="bg-white p-3 rounded border border-blue-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showBranchDetails.branch as any)['status'] === 'object' 
                        ? JSON.stringify((showBranchDetails.branch as any)['status'], null, 2)
                        : (showBranchDetails.branch as any)['status']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Task Statistics */}
            {showBranchDetails?.branch && (showBranchDetails.branch as any)['task_statistics'] && (
              <>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-green-700">Task Statistics</h3>
                  <div className="bg-white p-3 rounded border border-green-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showBranchDetails.branch as any)['task_statistics'] === 'object' 
                        ? JSON.stringify((showBranchDetails.branch as any)['task_statistics'], null, 2)
                        : (showBranchDetails.branch as any)['task_statistics']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Assigned Agents */}
            {showBranchDetails?.branch && (showBranchDetails.branch as any)['assigned_agents'] && (
              <>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-purple-700">Assigned Agents</h3>
                  <div className="bg-white p-3 rounded border border-purple-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showBranchDetails.branch as any)['assigned_agents'] === 'object' 
                        ? JSON.stringify((showBranchDetails.branch as any)['assigned_agents'], null, 2)
                        : (showBranchDetails.branch as any)['assigned_agents']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Branch Metadata */}
            {showBranchDetails?.branch && (showBranchDetails.branch as any)['metadata'] && (
              <>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3 text-orange-700">Branch Metadata</h3>
                  <div className="bg-white p-3 rounded border border-orange-200">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {typeof (showBranchDetails.branch as any)['metadata'] === 'object' 
                        ? JSON.stringify((showBranchDetails.branch as any)['metadata'], null, 2)
                        : (showBranchDetails.branch as any)['metadata']}
                    </pre>
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Additional Fields - Display any other fields */}
            {showBranchDetails?.branch && (
              <>
                {Object.entries(showBranchDetails.branch).filter(([key]) => 
                  !['id', 'name', 'description', 'status', 'task_statistics', 'assigned_agents', 'metadata'].includes(key)
                ).map(([key, value]) => {
                  if (value === null || value === undefined) return null;
                  
                  return (
                    <React.Fragment key={key}>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-lg font-semibold mb-3 capitalize">{key.replace(/_/g, ' ')}</h3>
                        <div className="bg-white p-3 rounded border border-gray-200">
                          {typeof value === 'object' ? (
                            <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <span className="text-sm">{String(value)}</span>
                          )}
                        </div>
                      </div>
                      <Separator />
                    </React.Fragment>
                  );
                })}
              </>
            )}

            {/* Raw Data */}
            <details className="cursor-pointer">
              <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                View Complete Raw Branch Data (JSON)
              </summary>
              <div className="mt-3 bg-gray-100 p-3 rounded">
                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify({ branch: showBranchDetails?.branch, project: showBranchDetails?.project }, null, 2)}
                </pre>
              </div>
            </details>
          </div>
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowBranchDetails(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Project Context Dialog */}
      <Dialog open={!!showProjectContext} onOpenChange={(v) => { if (!v) setShowProjectContext(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Project Context - {showProjectContext?.project?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {loadingContext ? (
              <div className="text-center py-8">
                <div className="text-sm text-muted-foreground">Loading context...</div>
              </div>
            ) : showProjectContext?.context ? (
              <>
                {/* Context Resolution Info */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Context Resolution</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Level:</span>
                      <Badge className="ml-2" variant="secondary">Project</Badge>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Context ID:</span>
                      <span className="ml-2 font-mono text-xs">{showProjectContext.context.context_id || showProjectContext.project.id}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Inheritance Chain */}
                {showProjectContext.context.inheritance_chain && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-blue-700">Inheritance Chain</h4>
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="flex items-center gap-2">
                          {showProjectContext.context.inheritance_chain.map((level: string, index: number) => (
                            <React.Fragment key={level}>
                              <Badge variant={level === 'project' ? 'default' : 'outline'}>
                                {level.toUpperCase()}
                              </Badge>
                              {index < showProjectContext.context.inheritance_chain.length - 1 && (
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
                {showProjectContext.context.data && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-green-700">Context Data</h4>
                      <div className="bg-green-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showProjectContext.context.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Metadata */}
                {showProjectContext.context.metadata && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-purple-700">Metadata</h4>
                      <div className="bg-purple-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showProjectContext.context.metadata, null, 2)}
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
                      {JSON.stringify(showProjectContext.context, null, 2)}
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
            <Button variant="outline" onClick={() => setShowProjectContext(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Branch Context Dialog */}
      <Dialog open={!!showBranchContext} onOpenChange={(v) => { if (!v) setShowBranchContext(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Branch/Task Tree Context - {showBranchContext?.branch?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {loadingContext ? (
              <div className="text-center py-8">
                <div className="text-sm text-muted-foreground">Loading context...</div>
              </div>
            ) : showBranchContext?.context ? (
              <>
                {/* Context Resolution Info */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Context Resolution</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Level:</span>
                      <Badge className="ml-2" variant="secondary">Task (Branch)</Badge>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Context ID:</span>
                      <span className="ml-2 font-mono text-xs">{showBranchContext.context.context_id || showBranchContext.branch.id}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Project:</span>
                      <span className="ml-2">{showBranchContext.project.name}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Inheritance Chain */}
                {showBranchContext.context.inheritance_chain && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-blue-700">Inheritance Chain</h4>
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="flex items-center gap-2">
                          {showBranchContext.context.inheritance_chain.map((level: string, index: number) => (
                            <React.Fragment key={level}>
                              <Badge variant={level === 'task' ? 'default' : 'outline'}>
                                {level.toUpperCase()}
                              </Badge>
                              {index < showBranchContext.context.inheritance_chain.length - 1 && (
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
                {showBranchContext.context.data && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-green-700">Context Data</h4>
                      <div className="bg-green-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showBranchContext.context.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Metadata */}
                {showBranchContext.context.metadata && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-purple-700">Metadata</h4>
                      <div className="bg-purple-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showBranchContext.context.metadata, null, 2)}
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
                      {JSON.stringify(showBranchContext.context, null, 2)}
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
            <Button variant="outline" onClick={() => setShowBranchContext(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Global Context Dialog */}
      <Dialog open={!!showGlobalContext} onOpenChange={(v) => { if (!v) setShowGlobalContext(null); }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl text-left">Global Context</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {loadingContext ? (
              <div className="text-center py-8">
                <div className="text-sm text-muted-foreground">Loading global context...</div>
              </div>
            ) : showGlobalContext?.context ? (
              <>
                {/* Context Resolution Info */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">Context Resolution</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Level:</span>
                      <Badge className="ml-2" variant="default">Global</Badge>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Context ID:</span>
                      <span className="ml-2 font-mono text-xs">global_singleton</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Scope:</span>
                      <span className="ml-2">Organization-wide settings and capabilities</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Inheritance Chain */}
                {showGlobalContext.context.inheritance_chain && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-blue-700">Inheritance Chain</h4>
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="flex items-center gap-2">
                          {showGlobalContext.context.inheritance_chain.map((level: string, index: number) => (
                            <React.Fragment key={level}>
                              <Badge variant={level === 'global' ? 'default' : 'outline'}>
                                {level.toUpperCase()}
                              </Badge>
                              {index < showGlobalContext.context.inheritance_chain.length - 1 && (
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
                {showGlobalContext.context.data && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-green-700">Global Context Data</h4>
                      <div className="bg-green-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showGlobalContext.context.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Metadata */}
                {showGlobalContext.context.metadata && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-purple-700">Metadata</h4>
                      <div className="bg-purple-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showGlobalContext.context.metadata, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Platform Capabilities */}
                {showGlobalContext.context.platform_capabilities && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-orange-700">Platform Capabilities</h4>
                      <div className="bg-orange-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showGlobalContext.context.platform_capabilities, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Organizational Standards */}
                {showGlobalContext.context.organizational_standards && (
                  <>
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-indigo-700">Organizational Standards</h4>
                      <div className="bg-indigo-50 p-3 rounded">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(showGlobalContext.context.organizational_standards, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* Additional Fields - Display any other fields */}
                {showGlobalContext.context && (
                  <>
                    {Object.entries(showGlobalContext.context).filter(([key]) => 
                      !['inheritance_chain', 'data', 'metadata', 'platform_capabilities', 'organizational_standards', 'context_id'].includes(key)
                    ).map(([key, value]) => {
                      if (value === null || value === undefined) return null;
                      
                      return (
                        <React.Fragment key={key}>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <h3 className="text-lg font-semibold mb-3 capitalize">{key.replace(/_/g, ' ')}</h3>
                            <div className="bg-white p-3 rounded border border-gray-200">
                              {typeof value === 'object' ? (
                                <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                              ) : (
                                <span className="text-sm">{String(value)}</span>
                              )}
                            </div>
                          </div>
                          <Separator />
                        </React.Fragment>
                      );
                    })}
                  </>
                )}

                {/* Raw Context Data */}
                <details className="cursor-pointer">
                  <summary className="font-semibold text-sm text-gray-700 hover:text-gray-900">
                    View Complete Raw Global Context Data (JSON)
                  </summary>
                  <div className="mt-3 bg-gray-100 p-3 rounded">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(showGlobalContext.context, null, 2)}
                    </pre>
                  </div>
                </details>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground">No global context data available</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGlobalContext(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProjectList; 