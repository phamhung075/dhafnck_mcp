import React from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Separator } from "./ui/separator";
import { Task, Subtask } from "../api";
import ClickableAssignees from "./ClickableAssignees";
import { formatContextDisplay } from "../utils/contextHelpers";

interface TaskDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onClose: () => void;
  onAgentClick: (agentName: string, task: Task | Subtask) => void;
}

export const TaskDetailsDialog: React.FC<TaskDetailsDialogProps> = ({
  open,
  onOpenChange,
  task,
  onClose,
  onAgentClick
}) => {
  // Format context data using helper functions
  const contextDisplay = formatContextDisplay(task?.context_data);
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-left">Task Details - Complete Information</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {/* Task Information Header */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold">{task?.title}</h3>
            {task?.description && (
              <p className="text-sm text-muted-foreground mt-2">{task.description}</p>
            )}
            <div className="flex gap-2 mt-3 flex-wrap">
              <Badge variant={getStatusColor(task?.status || 'pending')} className="px-3 py-1">
                Status: {task?.status?.replace('_', ' ') || 'pending'}
              </Badge>
              <Badge variant={getPriorityColor(task?.priority || 'medium')} className="px-3 py-1">
                Priority: {task?.priority || 'medium'}
              </Badge>
            </div>
            {task?.assignees && task.assignees.length > 0 && (
              <div className="mt-3">
                <span className="text-sm text-muted-foreground">Assigned to: </span>
                <span className="text-sm font-medium">{task.assignees.join(', ')}</span>
              </div>
            )}
          </div>

          {/* All Task Details */}
          {task && (
            <div className="space-y-4">
              {/* IDs and References */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-blue-700">IDs and References</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-blue-50 p-3 rounded">
                  <div className="space-y-1">
                    <span className="text-muted-foreground font-medium">Task ID:</span>
                    <p className="font-mono text-xs break-all">{task.id}</p>
                  </div>
                  {task.git_branch_id && (
                    <div className="space-y-1">
                      <span className="text-muted-foreground font-medium">Git Branch ID:</span>
                      <p className="font-mono text-xs break-all">{task.git_branch_id}</p>
                    </div>
                  )}
                  {task.context_id && (
                    <div className="space-y-1">
                      <span className="text-muted-foreground font-medium">Context ID:</span>
                      <p className="font-mono text-xs break-all">{task.context_id}</p>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Time Information */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-green-700">Time Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm bg-green-50 p-3 rounded">
                  {task.estimated_effort && (
                    <div>
                      <span className="text-muted-foreground font-medium">Estimated Effort:</span>
                      <p className="font-semibold">{task.estimated_effort}</p>
                    </div>
                  )}
                  {task.due_date && (
                    <div>
                      <span className="text-muted-foreground font-medium">Due Date:</span>
                      <p>{new Date(task.due_date).toLocaleDateString()} ({new Date(task.due_date).toLocaleTimeString()})</p>
                    </div>
                  )}
                  {task.created_at && (
                    <div>
                      <span className="text-muted-foreground font-medium">Created:</span>
                      <p>{new Date(task.created_at).toLocaleDateString()} at {new Date(task.created_at).toLocaleTimeString()}</p>
                    </div>
                  )}
                  {task.updated_at && (
                    <div>
                      <span className="text-muted-foreground font-medium">Last Updated:</span>
                      <p>{new Date(task.updated_at).toLocaleDateString()} at {new Date(task.updated_at).toLocaleTimeString()}</p>
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
                  {task.details && (
                    <div>
                      <span className="text-muted-foreground font-medium">Additional Details:</span>
                      <p className="mt-1 whitespace-pre-wrap">{task.details}</p>
                    </div>
                  )}
                  
                  {/* Assignees */}
                  {task.assignees && task.assignees.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">Assignees:</span>
                      <div className="mt-1">
                        <ClickableAssignees
                          assignees={task.assignees}
                          task={task}
                          onAgentClick={onAgentClick}
                          variant="secondary"
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* Labels */}
                  {task.labels && task.labels.length > 0 && (
                    <div>
                      <span className="text-muted-foreground font-medium">Labels:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {task.labels.map((label: string, index: number) => (
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
              {task.dependencies && task.dependencies.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-orange-700">Dependencies ({task.dependencies.length})</h4>
                    <div className="space-y-2 bg-orange-50 p-3 rounded">
                      {task.dependencies.map((dep: string, index: number) => (
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
              {task.subtasks && Array.isArray(task.subtasks) && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-indigo-700">Subtasks Summary</h4>
                    <div className="bg-indigo-50 p-3 rounded">
                      {task.subtasks.length > 0 ? (
                        <>
                          <p className="text-sm font-medium">Total subtasks: {task.subtasks.length}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            View full subtask details in the Subtasks tab
                          </p>
                          {/* Only show subtask IDs if they are valid strings */}
                          {task.subtasks.filter((id: any) => typeof id === 'string' && id.length > 0).length > 0 ? (
                            <div className="mt-2 space-y-1">
                              {task.subtasks
                                .filter((id: any) => typeof id === 'string' && id.length > 0)
                                .map((subtaskId: string, index: number) => (
                                  <div key={index} className="text-sm">
                                    <span className="text-muted-foreground">#{index + 1}:</span> 
                                    <span className="font-mono text-xs ml-1">{subtaskId}</span>
                                  </div>
                                ))}
                            </div>
                          ) : (
                            <p className="text-xs text-muted-foreground mt-2 italic">
                              Subtask IDs not available. View Subtasks tab for details.
                            </p>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No subtasks associated with this task.
                        </p>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* Context Data */}
              {task.context_data && (
                <>
                  <Separator />
                  
                  {/* Enhanced Context Display */}
                  {contextDisplay.hasInfo && (
                    <div>
                      <h4 className="font-semibold text-sm mb-3 text-teal-700">Task Completion Details</h4>
                      <div className="bg-teal-50 p-3 rounded space-y-3">
                        
                        {/* Completion Summary */}
                        {contextDisplay.completionSummary && (
                          <div>
                            <h5 className="font-medium text-xs text-teal-800 mb-1">
                              Completion Summary{contextDisplay.isLegacy ? ' (Legacy)' : ''}:
                            </h5>
                            <p className={`text-sm whitespace-pre-wrap p-2 rounded border ${contextDisplay.isLegacy ? 'bg-yellow-50' : 'bg-white'}`}>
                              {contextDisplay.completionSummary}
                            </p>
                            {contextDisplay.completionPercentage && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Completion: {contextDisplay.completionPercentage}%
                              </p>
                            )}
                            {contextDisplay.isLegacy && (
                              <p className="text-xs text-muted-foreground mt-1 italic">
                                Note: Using legacy completion_summary format
                              </p>
                            )}
                          </div>
                        )}

                        {/* Task Status */}
                        {contextDisplay.taskStatus && (
                          <div>
                            <h5 className="font-medium text-xs text-teal-800 mb-1">Context Status:</h5>
                            <span className="inline-block px-2 py-1 bg-teal-200 text-teal-800 text-xs font-medium rounded">
                              {contextDisplay.taskStatus}
                            </span>
                          </div>
                        )}

                        {/* Testing Notes */}
                        {contextDisplay.testingNotes.length > 0 && (
                          <div>
                            <h5 className="font-medium text-xs text-teal-800 mb-1">Testing Notes & Next Steps:</h5>
                            <ul className="text-sm space-y-1">
                              {contextDisplay.testingNotes.map((step: string, index: number) => (
                                <li key={index} className="bg-white p-2 rounded border border-l-4 border-l-teal-300">
                                  {step}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Raw Context Data */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3 text-teal-700">Raw Context Data</h4>
                    <div className="bg-teal-50 p-3 rounded">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(task.context_data, null, 2)}
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
                    {JSON.stringify(task, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TaskDetailsDialog;