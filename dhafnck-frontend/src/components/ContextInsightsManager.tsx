/**
 * ContextInsightsManager Component
 * Manage insights with creation, editing, and filtering
 */

import React, { useState, useCallback } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import {
  ContextInsightsManagerProps,
  ContextInsight,
  InsightFilters
} from '../types/context-delegation';

export function ContextInsightsManager({
  insights,
  contextId,
  onAddInsight,
  onUpdateInsight,
  onDeleteInsight,
  onFilterInsights,
  readOnly = false
}: ContextInsightsManagerProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingInsight, setEditingInsight] = useState<string | null>(null);
  const [filters, setFilters] = useState<InsightFilters>({});
  const [newInsight, setNewInsight] = useState<Partial<ContextInsight>>({
    content: '',
    category: 'technical',
    importance: 'medium',
    tags: []
  });

  // Filter insights based on current filters
  const filteredInsights = insights.filter(insight => {
    if (filters.category && insight.category !== filters.category) return false;
    if (filters.importance && insight.importance !== filters.importance) return false;
    if (filters.searchTerm && !insight.content.toLowerCase().includes(filters.searchTerm.toLowerCase())) return false;
    if (filters.tags && filters.tags.length > 0 && !filters.tags.some(tag => insight.tags.includes(tag))) return false;
    if (filters.dateRange) {
      const insightDate = new Date(insight.created_at);
      const fromDate = new Date(filters.dateRange.from);
      const toDate = new Date(filters.dateRange.to);
      if (insightDate < fromDate || insightDate > toDate) return false;
    }
    return true;
  });

  // Handle adding new insight
  const handleAddInsight = useCallback(async () => {
    if (!newInsight.content) return;

    try {
      await onAddInsight({
        content: newInsight.content,
        category: newInsight.category || 'technical',
        importance: newInsight.importance || 'medium',
        tags: newInsight.tags || [],
        created_by: 'current_user' // This should come from auth context
      } as Omit<ContextInsight, 'id' | 'created_at'>);

      setNewInsight({
        content: '',
        category: 'technical',
        importance: 'medium',
        tags: []
      });
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to add insight:', error);
    }
  }, [newInsight, onAddInsight]);

  // Handle updating insight
  const handleUpdateInsight = useCallback(async (insightId: string, updates: Partial<ContextInsight>) => {
    try {
      await onUpdateInsight(insightId, updates);
      setEditingInsight(null);
    } catch (error) {
      console.error('Failed to update insight:', error);
    }
  }, [onUpdateInsight]);

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: Partial<InsightFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFilterInsights(updatedFilters);
  }, [filters, onFilterInsights]);

  // Get all unique tags
  const allTags = Array.from(new Set(insights.flatMap(insight => insight.tags)));

  return (
    <div className="space-y-4">
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Insights</h2>
          <p className="text-sm text-gray-600">
            {filteredInsights.length} of {insights.length} insights
          </p>
        </div>
        {!readOnly && (
          <Button
            onClick={() => setShowAddForm(!showAddForm)}
            size="sm"
          >
            {showAddForm ? 'Cancel' : '+ Add Insight'}
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <Input
              placeholder="Search insights..."
              value={filters.searchTerm || ''}
              onChange={(e) => handleFilterChange({ searchTerm: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange({ category: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Categories</option>
              <option value="technical">Technical</option>
              <option value="business">Business</option>
              <option value="risk">Risk</option>
              <option value="optimization">Optimization</option>
              <option value="discovery">Discovery</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Importance</label>
            <select
              value={filters.importance || ''}
              onChange={(e) => handleFilterChange({ importance: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Levels</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Tags</label>
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) {
                  const currentTags = filters.tags || [];
                  handleFilterChange({ 
                    tags: [...currentTags, e.target.value].filter((tag, index, arr) => arr.indexOf(tag) === index)
                  });
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">Add tag filter...</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filters */}
        {(filters.tags && filters.tags.length > 0) && (
          <div className="mt-3">
            <span className="text-sm text-gray-600 mr-2">Tag filters:</span>
            <div className="inline-flex flex-wrap gap-1">
              {filters.tags.map(tag => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                  <button
                    onClick={() => handleFilterChange({ 
                      tags: filters.tags?.filter(t => t !== tag) 
                    })}
                    className="ml-1 text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Add Insight Form */}
      {showAddForm && !readOnly && (
        <Card className="p-4">
          <h3 className="font-medium mb-3">Add New Insight</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Content</label>
              <textarea
                value={newInsight.content}
                onChange={(e) => setNewInsight(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Describe your insight..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Category</label>
                <select
                  value={newInsight.category}
                  onChange={(e) => setNewInsight(prev => ({ ...prev, category: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="technical">Technical</option>
                  <option value="business">Business</option>
                  <option value="risk">Risk</option>
                  <option value="optimization">Optimization</option>
                  <option value="discovery">Discovery</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Importance</label>
                <select
                  value={newInsight.importance}
                  onChange={(e) => setNewInsight(prev => ({ ...prev, importance: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Tags</label>
                <Input
                  placeholder="tag1, tag2, tag3"
                  value={(newInsight.tags || []).join(', ')}
                  onChange={(e) => setNewInsight(prev => ({ 
                    ...prev, 
                    tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
                  }))}
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <Button onClick={handleAddInsight} disabled={!newInsight.content}>
                Add Insight
              </Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Insights List */}
      <div className="space-y-3">
        {filteredInsights.length === 0 ? (
          <Alert>
            <span>No insights match the current filters</span>
          </Alert>
        ) : (
          filteredInsights.map(insight => (
            <InsightCard
              key={insight.id}
              insight={insight}
              isEditing={editingInsight === insight.id}
              onEdit={() => setEditingInsight(insight.id)}
              onSave={(updates) => handleUpdateInsight(insight.id, updates)}
              onCancel={() => setEditingInsight(null)}
              onDelete={() => onDeleteInsight(insight.id)}
              readOnly={readOnly}
            />
          ))
        )}
      </div>
    </div>
  );
}

// Individual Insight Card Component
function InsightCard({
  insight,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onDelete,
  readOnly
}: {
  insight: ContextInsight;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (updates: Partial<ContextInsight>) => void;
  onCancel: () => void;
  onDelete: () => void;
  readOnly: boolean;
}) {
  const [editData, setEditData] = useState(insight);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'technical': return 'bg-blue-100 text-blue-800';
      case 'business': return 'bg-green-100 text-green-800';
      case 'risk': return 'bg-red-100 text-red-800';
      case 'optimization': return 'bg-purple-100 text-purple-800';
      case 'discovery': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  if (isEditing && !readOnly) {
    return (
      <Card className="p-4">
        <div className="space-y-3">
          <textarea
            value={editData.content}
            onChange={(e) => setEditData(prev => ({ ...prev, content: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select
              value={editData.category}
              onChange={(e) => setEditData(prev => ({ ...prev, category: e.target.value as any }))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="technical">Technical</option>
              <option value="business">Business</option>
              <option value="risk">Risk</option>
              <option value="optimization">Optimization</option>
              <option value="discovery">Discovery</option>
            </select>
            <select
              value={editData.importance}
              onChange={(e) => setEditData(prev => ({ ...prev, importance: e.target.value as any }))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <Input
              placeholder="tag1, tag2, tag3"
              value={editData.tags.join(', ')}
              onChange={(e) => setEditData(prev => ({ 
                ...prev, 
                tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
              }))}
            />
          </div>
          <div className="flex space-x-2">
            <Button size="sm" onClick={() => onSave(editData)}>
              Save
            </Button>
            <Button size="sm" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-gray-800">{insight.content}</p>
          </div>
          {!readOnly && (
            <div className="flex space-x-1 ml-4">
              <Button size="sm" variant="outline" onClick={onEdit}>
                Edit
              </Button>
              <Button size="sm" variant="outline" onClick={onDelete}>
                Delete
              </Button>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(insight.category)}`}>
              {insight.category}
            </span>
            <Badge variant={getImportanceColor(insight.importance) as any}>
              {insight.importance}
            </Badge>
            {insight.tags.map(tag => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="text-xs text-gray-500">
            {insight.created_by} • {new Date(insight.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>
    </Card>
  );
}