import { Calendar, Clock, FileText, Flag, Hash, Info, Tag, Users } from "lucide-react";
import React from "react";
import { Task, Subtask } from "../api/enhanced";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Separator } from "./ui/separator";

interface TaskDetailViewProps {
  task: Task | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface SubtaskDetailViewProps {
  subtask: Subtask | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const statusColor: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  completed: "default",
  done: "default",
  in_progress: "secondary",
  todo: "outline",
  pending: "outline",
  cancelled: "destructive",
  blocked: "destructive"
};

const priorityColor: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  low: "outline",
  medium: "secondary",
  high: "default",
  urgent: "destructive",
  critical: "destructive"
};

function formatDate(date: string | null | undefined): string {
  if (!date) return "Not set";
  return new Date(date).toLocaleString();
}

export function TaskDetailView({ task, open, onOpenChange }: TaskDetailViewProps) {
  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" style={{ width: '90vw', maxWidth: '1024px' }}>
        <DialogHeader>
          <DialogTitle className="text-2xl">{task.title}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Status and Priority */}
          <div className="flex gap-4 items-center">
            <div className="flex items-center gap-2">
              <Flag className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Status:</span>
              <Badge variant={statusColor[task.status] || "outline"}>{task.status}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Priority:</span>
              <Badge variant={priorityColor[task.priority] || "outline"}>{task.priority}</Badge>
            </div>
          </div>

          {/* Description */}
          {task.description && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <h3 className="font-semibold">Description</h3>
              </div>
              <p className="text-sm text-muted-foreground ml-6">{task.description}</p>
            </div>
          )}

          {/* Details */}
          {task.details && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <h3 className="font-semibold">Details</h3>
              </div>
              <div className="ml-6 text-sm text-muted-foreground whitespace-pre-wrap">{task.details}</div>
            </div>
          )}

          <Separator />

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            {/* Task ID */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Task ID</span>
              </div>
              <p className="text-sm text-muted-foreground ml-6 font-mono break-all">{task.id}</p>
            </div>

            {/* Estimated Effort */}
            {task.estimated_effort && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Estimated Effort</span>
                </div>
                <p className="text-sm text-muted-foreground ml-6">{task.estimated_effort}</p>
              </div>
            )}

            {/* Created At */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Created</span>
              </div>
              <p className="text-sm text-muted-foreground ml-6">{formatDate(task.created_at)}</p>
            </div>

            {/* Updated At */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Last Updated</span>
              </div>
              <p className="text-sm text-muted-foreground ml-6">{formatDate(task.updated_at)}</p>
            </div>

            {/* Due Date */}
            {task.due_date && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Due Date</span>
                </div>
                <p className="text-sm text-muted-foreground ml-6">{formatDate(task.due_date)}</p>
              </div>
            )}
          </div>

          {/* Assignees */}
          {task.assignees && task.assignees.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-semibold">Assignees</h3>
                </div>
                <div className="flex flex-wrap gap-2 ml-6">
                  {task.assignees.map((assignee: string, idx: number) => (
                    <Badge key={idx} variant="secondary">{assignee}</Badge>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Labels */}
          {task.labels && task.labels.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-semibold">Labels</h3>
                </div>
                <div className="flex flex-wrap gap-2 ml-6">
                  {task.labels.map((label: string, idx: number) => (
                    <Badge key={idx} variant="outline">{label}</Badge>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Subtasks Summary */}
          {task.subtasks && task.subtasks.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <h3 className="font-semibold">Subtasks ({task.subtasks.length})</h3>
                <div className="space-y-2 ml-6">
                  {task.subtasks.map((subtask: any) => (
                    <div key={subtask.id} className="flex items-center gap-2 text-sm">
                      <Badge variant={statusColor[subtask.status] || "outline"} className="text-xs">
                        {subtask.status}
                      </Badge>
                      <span className="text-muted-foreground">{subtask.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Additional Metadata */}
          {(task.git_branch_id || task.context_id) && (
            <>
              <Separator />
              <div className="space-y-2 text-sm">
                {task.git_branch_id && (
                  <div>
                    <span className="font-medium">Branch ID:</span>{" "}
                    <span className="text-muted-foreground font-mono text-xs break-all">{task.git_branch_id}</span>
                  </div>
                )}
                {task.context_id && (
                  <div>
                    <span className="font-medium">Context ID:</span>{" "}
                    <span className="text-muted-foreground font-mono text-xs break-all">{task.context_id}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function SubtaskDetailView({ subtask, open, onOpenChange }: SubtaskDetailViewProps) {
  if (!subtask) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl" style={{ width: '85vw', maxWidth: '768px' }}>
        <DialogHeader>
          <DialogTitle className="text-xl">{subtask.title}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Status and Priority */}
          <div className="flex gap-4 items-center">
            <div className="flex items-center gap-2">
              <Flag className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Status:</span>
              <Badge variant={statusColor[subtask.status] || "outline"}>{subtask.status}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Priority:</span>
              <Badge variant={priorityColor[subtask.priority] || "outline"}>{subtask.priority}</Badge>
            </div>
          </div>

          {/* Description */}
          {subtask.description && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <h3 className="font-semibold">Description</h3>
              </div>
              <p className="text-sm text-muted-foreground ml-6">{subtask.description}</p>
            </div>
          )}

          <Separator />

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            {/* Subtask ID */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Subtask ID</span>
              </div>
              <p className="text-sm text-muted-foreground ml-6 font-mono text-xs break-all">{subtask.id}</p>
            </div>

            {/* Parent Task ID */}
            {(subtask as any).parent_task_id && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Parent Task</span>
                </div>
                <p className="text-sm text-muted-foreground ml-6 font-mono text-xs break-all">{(subtask as any).parent_task_id}</p>
              </div>
            )}

            {/* Created At */}
            {(subtask as any).created_at && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Created</span>
                </div>
                <p className="text-sm text-muted-foreground ml-6">{formatDate((subtask as any).created_at)}</p>
              </div>
            )}

            {/* Updated At */}
            {(subtask as any).updated_at && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Last Updated</span>
                </div>
                <p className="text-sm text-muted-foreground ml-6">{formatDate((subtask as any).updated_at)}</p>
              </div>
            )}
          </div>

          {/* Assignees */}
          {(subtask as any).assignees && (subtask as any).assignees.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <h3 className="font-semibold">Assignees</h3>
                </div>
                <div className="flex flex-wrap gap-2 ml-6">
                  {(subtask as any).assignees.map((assignee: string, idx: number) => (
                    <Badge key={idx} variant="secondary">{assignee}</Badge>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}