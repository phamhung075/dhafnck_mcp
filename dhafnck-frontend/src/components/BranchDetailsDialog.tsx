import React, { useEffect, useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Separator } from "./ui/separator";
import { getBranchContext, Project } from "../api";
import { FileText, Info, ChevronDown, ChevronRight, Hash, Calendar, Tag, Layers, Copy, Check as CheckIcon, GitBranch, Users } from "lucide-react";

interface BranchDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: Project | null;
  branch: any | null;
  onClose: () => void;
}

export const BranchDetailsDialog: React.FC<BranchDetailsDialogProps> = ({
  open,
  onOpenChange,
  project,
  branch,
  onClose
}) => {
  const [branchContext, setBranchContext] = useState<any>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'details' | 'context'>('details');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['data', 'resolved_context', 'branch_data', 'metadata']));
  const [jsonCopied, setJsonCopied] = useState(false);

  // Fetch branch context when dialog opens
  useEffect(() => {
    if (open && branch?.id) {
      setContextLoading(true);
      
      // Fetch branch context
      getBranchContext(branch.id)
        .then(context => {
          console.log('Raw branch context response:', context);
          
          // Extract the actual context data from the response
          if (context) {
            if (context.data && context.data.resolved_context) {
              // New format: data.resolved_context contains the actual context
              console.log('Using resolved_context from data:', context.data.resolved_context);
              setBranchContext(context.data.resolved_context);
            } else if (context.resolved_context) {
              // Alternative format: resolved_context at root level
              console.log('Using resolved_context from root:', context.resolved_context);
              setBranchContext(context.resolved_context);
            } else if (context.data) {
              // Fallback: use data object if it exists
              console.log('Using data object:', context.data);
              setBranchContext(context.data);
            } else {
              // Last resort: use the whole response
              console.log('Using full response:', context);
              setBranchContext(context);
            }
          } else {
            console.log('No context data received');
            setBranchContext(null);
          }
        })
        .catch(error => {
          console.error('Error fetching branch context:', error);
          setBranchContext(null);
        })
        .finally(() => {
          setContextLoading(false);
        });
    } else if (!open) {
      // Clear data when dialog closes
      setBranchContext(null);
      setActiveTab('details');
    }
  }, [open, branch?.id]);

  // Toggle section expansion
  const toggleSection = (path: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  // Copy JSON to clipboard
  const copyJsonToClipboard = () => {
    if (branchContext) {
      const jsonString = JSON.stringify(branchContext, null, 2);
      navigator.clipboard.writeText(jsonString).then(() => {
        setJsonCopied(true);
        setTimeout(() => setJsonCopied(false), 2000);
      }).catch(err => {
        console.error('Failed to copy JSON:', err);
      });
    }
  };

  // Render nested JSON beautifully (same as TaskDetailsDialog)
  const renderNestedJson = (data: any, path: string = '', depth: number = 0): React.ReactElement => {
    if (data === null || data === undefined) {
      return <span className="text-gray-400 italic">null</span>;
    }

    if (typeof data === 'boolean') {
      return <span className={`font-medium ${data ? 'text-green-600' : 'text-red-600'}`}>{String(data)}</span>;
    }

    if (typeof data === 'string') {
      // Check if it's a date string
      if (data.match(/^\d{4}-\d{2}-\d{2}/) || data.includes('T')) {
        try {
          const date = new Date(data);
          if (!isNaN(date.getTime())) {
            return (
              <span className="text-blue-600">
                <Calendar className="inline w-3 h-3 mr-1" />
                {date.toLocaleString()}
              </span>
            );
          }
        } catch {}
      }
      // Check if it's a UUID
      if (data.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
        return (
          <span className="font-mono text-xs text-purple-600">
            <Hash className="inline w-3 h-3 mr-1" />
            {data}
          </span>
        );
      }
      return <span className="text-gray-700 dark:text-gray-300">"{data}"</span>;
    }

    if (typeof data === 'number') {
      return <span className="text-blue-600 font-medium">{data}</span>;
    }

    if (Array.isArray(data)) {
      if (data.length === 0) {
        return <span className="text-gray-400 italic">[]</span>;
      }
      
      const isExpanded = expandedSections.has(path);
      
      return (
        <div className="inline-block">
          <button
            onClick={() => toggleSection(path)}
            className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium">[{data.length} items]</span>
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1">
              {data.map((item, index) => (
                <div key={index} className="flex items-start">
                  <span className="text-gray-400 text-xs mr-2">{index}:</span>
                  {renderNestedJson(item, `${path}[${index}]`, depth + 1)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (typeof data === 'object') {
      const keys = Object.keys(data);
      if (keys.length === 0) {
        return <span className="text-gray-400 italic">{'{}'}</span>;
      }

      const isExpanded = expandedSections.has(path);
      const isMainSection = depth === 0 || depth === 1;
      
      return (
        <div className={depth === 0 ? '' : 'inline-block'}>
          {path && (
            <button
              onClick={() => toggleSection(path)}
              className={`text-xs hover:text-gray-700 flex items-center gap-1 mb-1 ${
                isMainSection ? 'text-gray-700 font-semibold' : 'text-gray-500'
              }`}
            >
              {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              <Layers className="w-3 h-3" />
              <span>{keys.length} properties</span>
            </button>
          )}
          {(!path || isExpanded) && (
            <div className={`${path ? 'ml-4 mt-1' : ''} space-y-1`}>
              {keys.map(key => {
                const value = data[key];
                const currentPath = path ? `${path}.${key}` : key;
                const isEmpty = value === null || value === undefined || 
                               (typeof value === 'object' && Object.keys(value).length === 0) ||
                               (Array.isArray(value) && value.length === 0);
                
                // Get appropriate icon and color for known keys
                let keyIcon = null;
                let keyColor = 'text-gray-600';
                
                if (key.includes('id') || key.includes('uuid')) {
                  keyIcon = <Hash className="inline w-3 h-3 mr-1" />;
                  keyColor = 'text-purple-600';
                } else if (key.includes('date') || key.includes('time') || key.includes('_at')) {
                  keyIcon = <Calendar className="inline w-3 h-3 mr-1" />;
                  keyColor = 'text-blue-600';
                } else if (key.includes('status') || key.includes('state')) {
                  keyIcon = <Tag className="inline w-3 h-3 mr-1" />;
                  keyColor = 'text-green-600';
                } else if (key.includes('agent')) {
                  keyIcon = <Users className="inline w-3 h-3 mr-1" />;
                  keyColor = 'text-orange-600';
                }
                
                return (
                  <div 
                    key={key} 
                    className={`flex items-start ${
                      isEmpty ? 'opacity-50' : ''
                    } ${
                      isMainSection && typeof value === 'object' && !Array.isArray(value) 
                        ? 'p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700' 
                        : ''
                    }`}
                  >
                    <span className={`${keyColor} text-sm font-medium mr-2 min-w-[120px]`}>
                      {keyIcon}
                      {key}:
                    </span>
                    <div className="flex-1">
                      {renderNestedJson(value, currentPath, depth + 1)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      );
    }

    return <span className="text-gray-500">{String(data)}</span>;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-left flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            {branch?.name || 'Branch Details'}
          </DialogTitle>
          
          {/* Tab Navigation */}
          <div className="flex gap-1 mt-4 border-b">
            <button
              onClick={() => setActiveTab('details')}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'details' 
                  ? 'text-blue-600 border-blue-600' 
                  : 'text-gray-500 border-transparent hover:text-gray-700'
              }`}
            >
              <Info className="w-4 h-4" />
              Details
            </button>
            
            <button
              onClick={() => setActiveTab('context')}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'context' 
                  ? 'text-blue-600 border-blue-600' 
                  : 'text-gray-500 border-transparent hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4" />
              Context
              {contextLoading && <span className="text-xs">(Loading...)</span>}
              {!contextLoading && branchContext && Object.keys(branchContext).length > 0 && (
                <Badge variant="secondary" className="text-xs">Available</Badge>
              )}
            </button>
          </div>
        </DialogHeader>
        
        <div className="mt-4">
          {/* Details Tab Content */}
          {activeTab === 'details' && (
            <div className="space-y-4">
              {/* Basic Information */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-3">Basic Information</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Name:</span>
                    <span className="ml-2 font-medium">{branch?.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">ID:</span>
                    <span className="ml-2 font-mono text-xs">{branch?.id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Description:</span>
                    <span className="ml-2">{branch?.description || "No description"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Project:</span>
                    <span className="ml-2">{project?.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Project ID:</span>
                    <span className="ml-2 font-mono text-xs">{project?.id}</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Branch Status */}
              {branch && branch['status'] && (
                <>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-blue-700">Branch Status</h3>
                    <div className="bg-white p-3 rounded border border-blue-200">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {typeof branch['status'] === 'object' 
                          ? JSON.stringify(branch['status'], null, 2)
                          : branch['status']}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Task Statistics */}
              {branch && (branch['task_statistics'] || branch['task_count'] !== undefined) && (
                <>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-green-700">Task Statistics</h3>
                    <div className="bg-white p-3 rounded border border-green-200">
                      {branch['task_count'] !== undefined && (
                        <div className="mb-2">
                          <span className="font-medium">Total Tasks:</span> {branch['task_count']}
                        </div>
                      )}
                      {branch['task_statistics'] && (
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {typeof branch['task_statistics'] === 'object' 
                            ? JSON.stringify(branch['task_statistics'], null, 2)
                            : branch['task_statistics']}
                        </pre>
                      )}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Assigned Agents */}
              {branch && branch['assigned_agents'] && (
                <>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-purple-700">Assigned Agents</h3>
                    <div className="bg-white p-3 rounded border border-purple-200">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {typeof branch['assigned_agents'] === 'object' 
                          ? JSON.stringify(branch['assigned_agents'], null, 2)
                          : branch['assigned_agents']}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Branch Metadata */}
              {branch && branch['metadata'] && (
                <>
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3 text-orange-700">Branch Metadata</h3>
                    <div className="bg-white p-3 rounded border border-orange-200">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {typeof branch['metadata'] === 'object' 
                          ? JSON.stringify(branch['metadata'], null, 2)
                          : branch['metadata']}
                      </pre>
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Additional Fields - Display any other fields */}
              {branch && (
                <>
                  {Object.entries(branch).filter(([key]) => 
                    !['id', 'name', 'description', 'status', 'task_statistics', 'task_count', 'assigned_agents', 'metadata'].includes(key)
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
                    {JSON.stringify({ branch: branch, project: project }, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
          
          {/* Context Tab Content */}
          {activeTab === 'context' && (
            <div className="space-y-4">
              {contextLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <p className="mt-2 text-sm text-gray-500">Loading context...</p>
                </div>
              ) : branchContext ? (
                <>
                  {/* Context Header */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                    <h3 className="text-lg font-semibold text-blue-700 dark:text-blue-300 flex items-center gap-2">
                      <Layers className="w-5 h-5" />
                      Branch Context - Hierarchical View
                    </h3>
                    <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                      Interactive nested view of context data - click to expand/collapse sections
                    </p>
                  </div>
                  
                  {/* Beautiful Nested JSON Display */}
                  <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                    {renderNestedJson(branchContext)}
                  </div>
                  
                  {/* Expand/Collapse All Controls */}
                  <div className="flex gap-2 justify-end mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyJsonToClipboard}
                      className="flex items-center gap-2"
                    >
                      {jsonCopied ? (
                        <>
                          <CheckIcon className="w-4 h-4" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          Copy JSON
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Expand all sections
                        const allPaths = new Set<string>();
                        const traverse = (obj: any, path: string = '') => {
                          if (obj && typeof obj === 'object') {
                            allPaths.add(path);
                            Object.keys(obj).forEach(key => {
                              const newPath = path ? `${path}.${key}` : key;
                              traverse(obj[key], newPath);
                            });
                          }
                        };
                        traverse(branchContext);
                        setExpandedSections(allPaths);
                      }}
                    >
                      Expand All
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setExpandedSections(new Set(['data', 'resolved_context', 'branch_data', 'metadata']))}
                    >
                      Collapse All
                    </Button>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-gray-900">No Context Available</h3>
                  <p className="text-sm text-gray-500 mt-2">
                    This branch doesn't have any context data yet.
                  </p>
                  <p className="text-xs text-gray-400 mt-4">
                    Context is created when branches are updated or when tasks are created within the branch.
                  </p>
                </div>
              )}
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

export default BranchDetailsDialog;