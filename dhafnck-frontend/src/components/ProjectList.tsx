import { ChevronDown, ChevronRight, Eye, FileText, Folder, GitBranchPlus, Globe, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createBranch, createProject, deleteBranch, deleteProject, getGlobalContext, getProjectContext, getBranchContext, getTaskCount, listProjects, Project, updateProject } from "../api";
import { getBranchSummaries, BranchSummary } from "../api-lazy";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";
import { RefreshButton } from "./ui/refresh-button";
import BranchDetailsDialog from "./BranchDetailsDialog";

interface ProjectListProps {
  onSelect?: (projectId: string, branchId: string) => void;
  refreshKey?: number; // Add refresh trigger
}

const ProjectList: React.FC<ProjectListProps> = ({ onSelect, refreshKey }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<Project | null>(null);
  const [showDelete, setShowDelete] = useState<Project | null>(null);
  const [showDeleteBranch, setShowDeleteBranch] = useState<{ project: Project; branch: any } | null>(null);
  const [showCreateBranch, setShowCreateBranch] = useState<Project | null>(null);
  const [showProjectDetails, setShowProjectDetails] = useState<Project | null>(null);
  const [showBranchDetails, setShowBranchDetails] = useState<{ project: Project; branch: any } | null>(null);
  const [showProjectContext, setShowProjectContext] = useState<{ project: Project; context: any } | null>(null);
  const [showGlobalContext, setShowGlobalContext] = useState<{ context: any } | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);
  const [form, setForm] = useState<{ name: string; description: string }>({ name: "", description: "" });
  const [saving, setSaving] = useState(false);
  const [openProjects, setOpenProjects] = useState<Record<string, boolean>>({});
  const [taskCounts, setTaskCounts] = useState<Record<string, number>>({});
  const [branchSummaries, setBranchSummaries] = useState<Record<string, BranchSummary[]>>({});
  const [loadingBranches, setLoadingBranches] = useState<Record<string, boolean>>({});

  const toggleProject = async (projectId: string) => {
    const isOpening = !openProjects[projectId];
    setOpenProjects(prev => ({ ...prev, [projectId]: isOpening }));
    
    // Load branch summaries with optimized endpoint when opening
    if (isOpening && !branchSummaries[projectId]) {
      setLoadingBranches(prev => ({ ...prev, [projectId]: true }));
      try {
        const summaries = await getBranchSummaries(projectId);
        setBranchSummaries(prev => ({ ...prev, [projectId]: summaries.branches }));
        
        // Update task counts from the optimized response
        const counts: Record<string, number> = {};
        for (const branch of summaries.branches) {
          counts[branch.id] = branch.task_counts.total;
        }
        setTaskCounts(prev => ({ ...prev, ...counts }));
      } catch (error) {
        console.error('Error loading branch summaries:', error);
      } finally {
        setLoadingBranches(prev => ({ ...prev, [projectId]: false }));
      }
    }
  };

  const refreshTaskCounts = async () => {
    // Refresh by fetching projects again with updated task counts
    try {
      const projectsData = await listProjects();
      setProjects(projectsData);
      
      // Extract task counts from the refreshed project data
      const counts: Record<string, number> = {};
      for (const project of projectsData) {
        if (project.git_branchs) {
          for (const tree of Object.values(project.git_branchs)) {
            counts[tree.id] = tree.task_count ?? 0;
          }
        }
      }
      setTaskCounts(counts);
    } catch (e) {
      console.error('Error refreshing task counts:', e);
    }
  };

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const projectsData = await listProjects();
      console.log('Fetched projects data:', projectsData);
      setProjects(projectsData);
      
      // Extract task counts from the project data directly (no additional API calls needed)
      const counts: Record<string, number> = {};
      for (const project of projectsData) {
        if (project.git_branchs) {
          for (const tree of Object.values(project.git_branchs)) {
            // Use task_count from API response if available, otherwise fallback to 0
            counts[tree.id] = tree.task_count ?? 0;
            console.log(`Branch ${tree.name} (${tree.id}): task_count = ${tree.task_count}`);
          }
        }
      }
      setTaskCounts(counts);
      console.log('Updated task counts:', counts);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('ProjectList refreshKey changed:', refreshKey);
    fetchProjects();
  }, [refreshKey]); // Refresh when refreshKey changes

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
    setError(null);
    try {
      const result = await deleteProject(showDelete.id);
      if (result.success) {
        setShowDelete(null);
        fetchProjects();
      } else {
        // Show the specific validation error from backend
        const errorMsg = result.error || "Failed to delete project";
        setError(errorMsg);
      }
    } catch (e: any) {
      setError(e.message || "Failed to delete project");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteBranch = async () => {
    if (!showDeleteBranch) return;
    setSaving(true);
    console.log('Deleting branch:', showDeleteBranch.branch.id, 'from project:', showDeleteBranch.project.id);
    try {
      const success = await deleteBranch(showDeleteBranch.project.id, showDeleteBranch.branch.id);
      console.log('Delete result:', success);
      if (success) {
        // Close the project expansion to avoid rendering deleted branches
        const projectId = showDeleteBranch.project.id;
        setOpenProjects(prev => ({ ...prev, [projectId]: false }));
        setShowDeleteBranch(null);
        await fetchProjects(); // Make sure to await the refresh
      } else {
        setError("Failed to delete branch");
      }
    } catch (e: any) {
      console.error('Delete branch error:', e);
      setError(e.message || "Failed to delete branch");
    } finally {
      setSaving(false);
    }
  };

  if (loading && projects.length === 0) return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground px-2 py-1">
      <div className="animate-spin h-3 w-3 border-2 border-primary border-t-transparent rounded-full"></div>
      Loading projects...
    </div>
  );
  if (error) return <div className="text-xs text-destructive px-2 py-1">Error: {error}</div>;

  return (
    <div className="flex flex-col gap-2 overflow-visible">
      <div className="flex justify-between items-center mb-2 gap-2">
        <span className="font-bold text-base shrink-0">DhafnckMCP Projects</span>
        <div className="flex gap-1 flex-wrap justify-end">
          <RefreshButton 
            onClick={fetchProjects} 
            loading={loading}
            size="sm"
            variant="outline"
          />
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
                  <div className="flex gap-1 ml-2">
                    {project.git_branchs && Object.keys(project.git_branchs).length > 0 && (
                      <Badge variant={openProjects[project.id] ? "secondary" : "outline"} className="text-xs">
                        {Object.keys(project.git_branchs).length} {Object.keys(project.git_branchs).length === 1 ? 'branch' : 'branches'}
                      </Badge>
                    )}
                    {(() => {
                      const totalTasks = project.git_branchs ? 
                        Object.values(project.git_branchs).reduce((sum, branch: any) => sum + (branch.task_count || 0), 0) : 0;
                      return totalTasks > 0 ? (
                        <Badge variant="default" className="text-xs">
                          {totalTasks} {totalTasks === 1 ? 'task' : 'tasks'}
                        </Badge>
                      ) : null;
                    })()}
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0">
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label="View Details" onClick={() => setShowProjectDetails(project)}>
                    <Eye className="w-3 h-3" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label="View Context" onClick={async () => {
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
                    <FileText className="w-3 h-3" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label="Create Branch" onClick={() => { setShowCreateBranch(project); setForm({ name: "", description: "" }); }}>
                    <GitBranchPlus className="w-3 h-3" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label="Edit" onClick={() => { setShowEdit(project); setForm({ name: project.name, description: project.description || "" }); }}>
                    <Pencil className="w-3 h-3" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-7 w-7" aria-label="Delete" onClick={() => setShowDelete(project)}>
                    <Trash2 className="w-3 h-3 text-destructive" />
                  </Button>
                </div>
              </div>
              {openProjects[project.id] && (
                <ul className="flex flex-col gap-1 ml-8 mt-1">
                  {loadingBranches[project.id] ? (
                    <li className="text-xs text-muted-foreground pl-4">Loading branches...</li>
                  ) : branchSummaries[project.id] ? (
                    // Use optimized branch summaries if available
                    branchSummaries[project.id].map((branch) => (
                      <li key={branch.id}>
                        <div className="group relative flex items-center gap-1">
                          <span className="text-muted-foreground">—</span>
                          <Button
                            size="sm"
                            variant={selected === `${project.id}:${branch.id}` ? "secondary" : "ghost"}
                            className="flex-1 justify-start text-xs text-left"
                            onClick={() => {
                              setSelected(`${project.id}:${branch.id}`);
                              onSelect && onSelect(project.id, branch.id);
                            }}
                          >
                            <span className="truncate text-left flex-1">{branch.name}</span>
                            <div className="flex items-center gap-1">
                              <Badge variant="secondary" className="text-xs">
                                {branch.task_counts.total}
                              </Badge>
                              {branch.has_urgent_tasks && (
                                <Badge variant="destructive" className="text-xs">!</Badge>
                              )}
                              {branch.is_completed && (
                                <Badge variant="secondary" className="text-xs text-green-600">✓</Badge>
                              )}
                            </div>
                          </Button>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0">
                            <Button 
                              size="icon" 
                              variant="ghost" 
                              className="h-6 w-6"
                              onClick={() => setShowBranchDetails({ project, branch })}
                              aria-label="View Branch Details & Context"
                              title="View Branch Details & Context"
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                            {branch.name !== 'main' && (
                              <Button 
                                size="icon" 
                                variant="ghost" 
                                className="h-6 w-6"
                                onClick={() => setShowDeleteBranch({ project, branch })}
                                aria-label="Delete Branch"
                              >
                                <Trash2 className="w-3 h-3 text-destructive" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </li>
                    ))
                  ) : project.git_branchs ? (
                    // Fallback to original branch data if optimized not loaded
                    Object.values(project.git_branchs).map((tree) => (
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
                              {tree.task_count !== undefined ? tree.task_count : (taskCounts[tree.id] ?? 0)}
                            </Badge>
                          </Button>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0">
                            <Button 
                              size="icon" 
                              variant="ghost" 
                              className="h-6 w-6"
                              onClick={() => setShowBranchDetails({ project, branch: tree })}
                              aria-label="View Branch Details & Context"
                              title="View Branch Details & Context"
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                            {tree.name !== 'main' && (
                              <Button 
                                size="icon" 
                                variant="ghost" 
                                className="h-6 w-6"
                                onClick={() => setShowDeleteBranch({ project, branch: tree })}
                                aria-label="Delete Branch"
                              >
                                <Trash2 className="w-3 h-3 text-destructive" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </li>
                    ))
                  ) : null}
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

      {/* Delete Branch Dialog */}
      <Dialog open={!!showDeleteBranch} onOpenChange={(v: boolean) => { if (!v) setShowDeleteBranch(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-base">Delete Branch</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm">Are you sure you want to delete the branch <strong>{showDeleteBranch?.branch.name}</strong> from project <strong>{showDeleteBranch?.project.name}</strong>?</p>
            {showDeleteBranch && showDeleteBranch.branch.task_count > 0 && (
              <p className="text-sm text-destructive">
                Warning: This branch contains {showDeleteBranch.branch.task_count} task(s) that will also be deleted.
              </p>
            )}
            <p className="text-sm text-muted-foreground">This action cannot be undone.</p>
          </div>
          <DialogFooter className="mt-3">
            <Button variant="secondary" onClick={() => setShowDeleteBranch(null)} size="sm" disabled={saving}>
              Cancel
            </Button>
            <Button 
              variant="default" 
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90" 
              onClick={handleDeleteBranch} 
              size="sm"
              disabled={saving}
            >
              {saving ? "Deleting..." : "Delete Branch"}
            </Button>
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

      {/* Branch Details Dialog with Tabs */}
      <BranchDetailsDialog
        open={!!showBranchDetails}
        onOpenChange={(open) => { if (!open) setShowBranchDetails(null); }}
        project={showBranchDetails?.project || null}
        branch={showBranchDetails?.branch || null}
        onClose={() => setShowBranchDetails(null)}
      />


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