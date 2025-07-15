import React from "react";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Task } from "../api";

interface TaskContextDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  context: any | null;
  onClose: () => void;
  loading?: boolean;
}

export const TaskContextDialog: React.FC<TaskContextDialogProps> = ({
  open,
  onOpenChange,
  task,
  context,
  onClose,
  loading = false
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl text-left">Task Context</DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto space-y-4">
          {/* Task Information */}
          <div className="bg-gray-50 p-3 rounded">
            <h4 className="font-medium text-sm mb-1">Task: {task?.title}</h4>
            <p className="text-xs text-muted-foreground">ID: {task?.id}</p>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading context...</div>
            </div>
          )}

          {/* Context Content */}
          {!loading && context && (
            <div className="space-y-4">
              {/* Context Summary */}
              {context.metadata && (
                <div>
                  <h4 className="font-semibold text-sm mb-3 text-blue-700">Context Metadata</h4>
                  <div className="bg-blue-50 p-3 rounded">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(context.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Context Data */}
              {context.data && (
                <div>
                  <h4 className="font-semibold text-sm mb-3 text-green-700">Context Data</h4>
                  <div className="bg-green-50 p-3 rounded">
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(context.data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Insights */}
              {context.insights && context.insights.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-3 text-purple-700">Insights</h4>
                  <div className="bg-purple-50 p-3 rounded space-y-2">
                    {context.insights.map((insight: any, index: number) => (
                      <div key={index} className="border-l-4 border-purple-300 pl-3">
                        <p className="text-sm font-medium">{insight.title || `Insight ${index + 1}`}</p>
                        <p className="text-xs text-muted-foreground mt-1">{insight.content}</p>
                        {insight.timestamp && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(insight.timestamp).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Progress History */}
              {context.progress && context.progress.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-3 text-orange-700">Progress History</h4>
                  <div className="bg-orange-50 p-3 rounded space-y-2">
                    {context.progress.map((progress: any, index: number) => (
                      <div key={index} className="border-l-4 border-orange-300 pl-3">
                        <p className="text-sm">{progress.content}</p>
                        {progress.timestamp && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(progress.timestamp).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw Context */}
              <div>
                <h4 className="font-semibold text-sm mb-3 text-gray-700">Complete Context (Raw JSON)</h4>
                <div className="bg-gray-100 p-3 rounded">
                  <pre className="text-xs overflow-x-auto whitespace-pre-wrap max-h-96">
                    {JSON.stringify(context, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* No Context */}
          {!loading && !context && (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">No context data available</div>
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

export default TaskContextDialog;