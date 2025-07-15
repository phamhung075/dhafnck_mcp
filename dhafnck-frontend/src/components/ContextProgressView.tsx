/**
 * ContextProgressView Component
 * Display and manage context progress entries
 */

import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { ContextProgress } from '../types/context-delegation';

interface ContextProgressViewProps {
  contextId: string;
  progress: ContextProgress[];
  onAddProgress: (progress: ContextProgress) => void;
  readOnly?: boolean;
}

export function ContextProgressView({
  contextId,
  progress,
  onAddProgress,
  readOnly = false
}: ContextProgressViewProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newProgress, setNewProgress] = useState<Partial<ContextProgress>>({
    content: '',
    progress_percentage: 0,
    milestone: ''
  });

  const handleAddProgress = async () => {
    if (!newProgress.content) return;

    const progressEntry: ContextProgress = {
      id: `progress_${Date.now()}`,
      content: newProgress.content,
      progress_percentage: newProgress.progress_percentage,
      milestone: newProgress.milestone,
      created_at: new Date().toISOString(),
      created_by: 'current_user', // This should come from auth context
      related_tasks: []
    };

    onAddProgress(progressEntry);
    setNewProgress({
      content: '',
      progress_percentage: 0,
      milestone: ''
    });
    setShowAddForm(false);
  };

  // Sort progress by date (newest first)
  const sortedProgress = [...progress].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Progress Tracking</h2>
          <p className="text-sm text-gray-600">
            {progress.length} progress entries
          </p>
        </div>
        {!readOnly && (
          <Button
            onClick={() => setShowAddForm(!showAddForm)}
            size="sm"
          >
            {showAddForm ? 'Cancel' : '+ Add Progress'}
          </Button>
        )}
      </div>

      {/* Add Progress Form */}
      {showAddForm && !readOnly && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Add Progress Entry</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Progress Description</label>
              <textarea
                value={newProgress.content}
                onChange={(e) => setNewProgress(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Describe what was accomplished..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Progress Percentage ({newProgress.progress_percentage}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={newProgress.progress_percentage || 0}
                  onChange={(e) => setNewProgress(prev => ({ 
                    ...prev, 
                    progress_percentage: parseInt(e.target.value) 
                  }))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Milestone (Optional)</label>
                <Input
                  value={newProgress.milestone || ''}
                  onChange={(e) => setNewProgress(prev => ({ ...prev, milestone: e.target.value }))}
                  placeholder="e.g., MVP Complete, Testing Phase"
                />
              </div>
            </div>

            <div className="flex space-x-2">
              <Button onClick={handleAddProgress} disabled={!newProgress.content}>
                Add Progress
              </Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Progress Timeline */}
      <div className="space-y-3">
        {sortedProgress.length === 0 ? (
          <Alert>
            <span>No progress entries yet. Add one to start tracking progress.</span>
          </Alert>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-200"></div>
            
            {sortedProgress.map((entry, index) => (
              <div key={entry.id} className="relative flex items-start space-x-4">
                {/* Timeline dot */}
                <div className={`
                  relative z-10 flex items-center justify-center w-12 h-12 rounded-full
                  ${entry.progress_percentage === 100 
                    ? 'bg-green-500 text-white' 
                    : (entry.progress_percentage || 0) >= 75
                    ? 'bg-blue-500 text-white'
                    : (entry.progress_percentage || 0) >= 50
                    ? 'bg-yellow-500 text-white'
                    : 'bg-gray-400 text-white'
                  }
                `}>
                  <span className="text-xs font-bold">
                    {entry.progress_percentage || 0}%
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 min-h-12">
                  <Card className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-gray-800">{entry.content}</p>
                          {entry.milestone && (
                            <div className="mt-2">
                              <Badge variant="outline">
                                🎯 {entry.milestone}
                              </Badge>
                            </div>
                          )}
                        </div>
                        
                        <div className="ml-4 text-right">
                          <div className="text-xs text-gray-500">
                            {entry.created_by}
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(entry.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>

                      {/* Related Tasks */}
                      {entry.related_tasks && entry.related_tasks.length > 0 && (
                        <div className="pt-2 border-t">
                          <span className="text-xs text-gray-500 mr-2">Related tasks:</span>
                          <div className="inline-flex flex-wrap gap-1">
                            {entry.related_tasks.map(taskId => (
                              <Badge key={taskId} variant="outline" className="text-xs">
                                {taskId.slice(0, 8)}...
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Progress Summary */}
      {progress.length > 0 && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Progress Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-gray-500">Latest Progress</span>
              <p className="font-medium">
                {Math.max(...progress.map(p => p.progress_percentage || 0))}%
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Total Entries</span>
              <p className="font-medium">{progress.length}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Last Updated</span>
              <p className="font-medium">
                {new Date(sortedProgress[0]?.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          {/* Progress Chart */}
          <div className="mt-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm text-gray-500">Progress over time:</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${Math.max(...progress.map(p => p.progress_percentage || 0))}%` 
                }}
              ></div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}