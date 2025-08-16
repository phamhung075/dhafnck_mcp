import { Check, Eye, Pencil, Plus, Trash2, Users } from "lucide-react";
import { useEffect, useState, useCallback, useMemo } from "react";
import { deleteSubtask, listSubtasks, createSubtask as newSubtask, updateSubtask as saveSubtask, Subtask, completeSubtask } from "../api";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

interface LazySubtaskListProps {
  projectId: string;
  taskTreeId: string;
  parentTaskId: string;
}

// Lightweight subtask summary for performance
interface SubtaskSummary {
  id: string;
  title: string;
  status: string;
  priority: string;
  assignees_count: number;
  progress_percentage?: number;
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

export default function LazySubtaskList({ projectId, taskTreeId, parentTaskId }: LazySubtaskListProps) {
  // Lightweight state for performance
  const [subtaskSummaries, setSubtaskSummaries] = useState<SubtaskSummary[]>([]);
  const [fullSubtasks, setFullSubtasks] = useState<Map<string, Subtask>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingSubtasks, setLoadingSubtasks] = useState<Set<string>>(new Set());
  
  // Only load when component is actually rendered (lazy)
  const [hasLoaded, setHasLoaded] = useState(false);

  // Load subtask summaries (lightweight)
  const loadSubtaskSummaries = useCallback(async () => {
    if (hasLoaded) return; // Only load once
    
    setLoading(true);
    setError(null);
    
    try {
      // Try lightweight endpoint first
      const response = await fetch(`/api/subtasks/summaries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parent_task_id: parentTaskId,
          include_counts: true
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubtaskSummaries(data.subtasks);
      } else {
        // Fallback to full subtask loading
        await loadFullSubtasksFallback();
      }
      
    } catch (e) {
      console.warn('Lightweight subtask endpoint not available, falling back');
      await loadFullSubtasksFallback();
    } finally {
      setLoading(false);
      setHasLoaded(true);
    }
  }, [parentTaskId, hasLoaded]);

  // Fallback to current implementation
  const loadFullSubtasksFallback = useCallback(async () => {
    try {
      const subtasks = await listSubtasks(parentTaskId);
      
      // Convert to summaries
      const summaries: SubtaskSummary[] = subtasks.map(subtask => ({
        id: subtask.id,
        title: subtask.title,
        status: subtask.status,
        priority: subtask.priority,
        assignees_count: subtask.assignees?.length || 0,
        progress_percentage: subtask.progress_percentage
      }));
      
      setSubtaskSummaries(summaries);
      
      // Store full subtasks for immediate access
      const subtaskMap = new Map();
      subtasks.forEach(subtask => subtaskMap.set(subtask.id, subtask));
      setFullSubtasks(subtaskMap);
      
    } catch (e: any) {
      setError(e.message);
    }
  }, [parentTaskId]);

  // Load full subtask data on demand
  const loadFullSubtask = useCallback(async (subtaskId: string): Promise<Subtask | null> => {
    if (fullSubtasks.has(subtaskId)) {
      return fullSubtasks.get(subtaskId) || null;
    }
    
    if (loadingSubtasks.has(subtaskId)) {
      return null; // Already loading
    }
    
    setLoadingSubtasks(prev => {
      const newSet = new Set(prev);
      newSet.add(subtaskId);
      return newSet;
    });
    
    try {
      // For now, load all subtasks since we don't have individual endpoint
      if (fullSubtasks.size === 0) {
        await loadFullSubtasksFallback();
      }
      
      const subtask = fullSubtasks.get(subtaskId) || null;
      
      setLoadingSubtasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(subtaskId);
        return newSet;
      });
      
      return subtask;
      
    } catch (e) {
      console.error(`Failed to load subtask ${subtaskId}:`, e);
      setLoadingSubtasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(subtaskId);
        return newSet;
      });
      return null;
    }
  }, [fullSubtasks, loadingSubtasks, loadFullSubtasksFallback]);

  // Load subtasks when component mounts
  useEffect(() => {
    loadSubtaskSummaries();
  }, [loadSubtaskSummaries]);

  // Memoized progress calculation
  const progressSummary = useMemo(() => {
    if (subtaskSummaries.length === 0) return null;
    
    const total = subtaskSummaries.length;
    const completed = subtaskSummaries.filter(s => s.status === 'done').length;
    const inProgress = subtaskSummaries.filter(s => s.status === 'in_progress').length;
    
    return {
      total,
      completed,
      inProgress,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }, [subtaskSummaries]);

  // Render subtask row
  const renderSubtaskRow = useCallback((summary: SubtaskSummary) => {
    const isLoadingFull = loadingSubtasks.has(summary.id);
    
    return (
      <TableRow key={summary.id} className="text-sm">
        <TableCell className="pl-8">
          <div className="flex items-center gap-2">
            <span>{summary.title}</span>
            {summary.progress_percentage !== undefined && (
              <Badge variant="outline" className="text-xs">
                {summary.progress_percentage}%
              </Badge>
            )}
          </div>
        </TableCell>
        
        <TableCell>
          <Badge className={`text-xs`} variant={statusColor[summary.status] || "outline"}>
            {summary.status}
          </Badge>
        </TableCell>
        
        <TableCell>
          <Badge className="text-xs" variant={priorityColor[summary.priority] || "secondary"}>
            {summary.priority}
          </Badge>
        </TableCell>
        
        <TableCell>
          {summary.assignees_count > 0 ? (
            <Badge variant="secondary" className="text-xs">
              {summary.assignees_count} assigned
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">Unassigned</span>
          )}
        </TableCell>
        
        <TableCell>
          <div className="flex gap-1">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => loadFullSubtask(summary.id)}
              disabled={isLoadingFull}
              title="View details"
            >
              {isLoadingFull ? (
                <div className="w-3 h-3 border border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              ) : (
                <Eye className="w-3 h-3" />
              )}
            </Button>
            
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => loadFullSubtask(summary.id)}
              disabled={isLoadingFull}
              title="Edit"
            >
              <Pencil className="w-3 h-3" />
            </Button>
            
            {summary.status !== 'done' && (
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => loadFullSubtask(summary.id)}
                disabled={isLoadingFull}
                title="Complete"
              >
                <Check className="w-3 h-3" />
              </Button>
            )}
          </div>
        </TableCell>
      </TableRow>
    );
  }, [loadingSubtasks, loadFullSubtask]);

  if (loading) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        Loading subtasks...
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 text-center text-sm text-red-500">
        Error loading subtasks: {error}
      </div>
    );
  }
  
  if (subtaskSummaries.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        No subtasks found.
        <Button 
          variant="ghost" 
          size="sm" 
          className="ml-2"
          onClick={() => {/* TODO: Open create subtask dialog */}}
        >
          <Plus className="w-3 h-3 mr-1" />
          Add Subtask
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Progress Summary */}
      {progressSummary && (
        <div className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm">
            <strong>Progress:</strong> {progressSummary.completed}/{progressSummary.total} completed ({progressSummary.percentage}%)
          </div>
          {progressSummary.inProgress > 0 && (
            <Badge variant="secondary" className="text-xs">
              {progressSummary.inProgress} in progress
            </Badge>
          )}
          <div className="flex-1">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressSummary.percentage}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Subtasks Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="text-xs">Subtask</TableHead>
            <TableHead className="text-xs">Status</TableHead>
            <TableHead className="text-xs">Priority</TableHead>
            <TableHead className="text-xs">Assignees</TableHead>
            <TableHead className="text-xs">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {subtaskSummaries.map(renderSubtaskRow)}
        </TableBody>
      </Table>
      
      {/* Add Subtask Button */}
      <div className="flex justify-end pt-2">
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => {/* TODO: Open create subtask dialog */}}
        >
          <Plus className="w-3 h-3 mr-1" />
          Add Subtask
        </Button>
      </div>
    </div>
  );
}