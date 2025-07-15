import React, { useState, useEffect } from 'react';
import type { Project } from '../types/application';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface ProjectSearchFilterProps {
  projects: Project[];
  onFilterChange: (filteredProjects: Project[]) => void;
}

interface FilterState {
  searchTerm: string;
  status: string;
  priority: string;
  health: string;
  hasIssues: boolean;
  tags: string[];
  dateRange: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export function ProjectSearchFilter({ projects, onFilterChange }: ProjectSearchFilterProps) {
  const [filters, setFilters] = useState<FilterState>({
    searchTerm: '',
    status: 'all',
    priority: 'all',
    health: 'all',
    hasIssues: false,
    tags: [],
    dateRange: 'all',
    sortBy: 'name',
    sortOrder: 'asc'
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [savedFilters, setSavedFilters] = useState<Array<{ name: string; filters: FilterState }>>([]);

  // Extract all unique tags from projects (placeholder - no tags in current Project type)
  const allTags: string[] = [];

  // Extract all unique statuses (placeholder - no status in current Project type)
  const allStatuses = ['active', 'inactive', 'archived'];

  // Filter and sort projects
  useEffect(() => {
    let filtered = projects.filter(project => {
      // Search term filter
      const matchesSearch = !filters.searchTerm || 
        project.name.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
        project.description?.toLowerCase().includes(filters.searchTerm.toLowerCase());
      
      // Status filter (placeholder - always match since no status in Project type)
      const matchesStatus = filters.status === 'all' || true;
      
      // Priority filter (placeholder - always match since no priority in Project type)
      const matchesPriority = filters.priority === 'all' || true;
      
      // Tags filter (placeholder - always match since no tags in Project type)
      const matchesTags = filters.tags.length === 0 || true;
      
      // Health filter (would need health data - mock for now)
      const matchesHealth = filters.health === 'all' || (() => {
        // Mock health calculation based on project ID (deterministic)
        const mockHealth = Math.abs(project.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 100;
        switch (filters.health) {
          case 'excellent': return mockHealth >= 80;
          case 'good': return mockHealth >= 60 && mockHealth < 80;
          case 'poor': return mockHealth < 60;
          default: return true;
        }
      })();
      
      // Issues filter (mock)
      const hasIssues = (Math.abs(project.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 10) > 7; // Mock 30% chance of having issues based on project ID
      const matchesIssues = !filters.hasIssues || hasIssues;
      
      // Date range filter
      const matchesDateRange = filters.dateRange === 'all' || (() => {
        const now = new Date();
        const projectDate = new Date(project.created_at);
        const daysDiff = Math.floor((now.getTime() - projectDate.getTime()) / (1000 * 60 * 60 * 24));
        
        switch (filters.dateRange) {
          case 'week': return daysDiff <= 7;
          case 'month': return daysDiff <= 30;
          case 'quarter': return daysDiff <= 90;
          case 'year': return daysDiff <= 365;
          default: return true;
        }
      })();

      return matchesSearch && matchesStatus && matchesPriority && 
             matchesTags && matchesHealth && matchesIssues && matchesDateRange;
    });

    // Sort projects
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (filters.sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'status':
          comparison = 0; // No status field in Project type
          break;
        case 'priority':
          comparison = 0; // No priority field in Project type
          break;
        case 'created':
          const dateA = new Date(a.created_at).getTime();
          const dateB = new Date(b.created_at).getTime();
          comparison = dateA - dateB;
          break;
        case 'health':
          // Mock health comparison (deterministic)
          const healthA = Math.abs(a.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 100;
          const healthB = Math.abs(b.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 100;
          comparison = healthA - healthB;
          break;
        default:
          comparison = 0;
      }
      
      return filters.sortOrder === 'desc' ? -comparison : comparison;
    });

    onFilterChange(filtered);
  }, [projects, filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateFilter = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const toggleTag = (tag: string) => {
    setFilters(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }));
  };

  const resetFilters = () => {
    setFilters({
      searchTerm: '',
      status: 'all',
      priority: 'all',
      health: 'all',
      hasIssues: false,
      tags: [],
      dateRange: 'all',
      sortBy: 'name',
      sortOrder: 'asc'
    });
  };

  const saveCurrentFilter = () => {
    const name = prompt('Enter a name for this filter:');
    if (name) {
      setSavedFilters(prev => [...prev, { name, filters: { ...filters } }]);
    }
  };

  const loadSavedFilter = (savedFilter: { name: string; filters: FilterState }) => {
    setFilters(savedFilter.filters);
  };

  const deleteSavedFilter = (index: number) => {
    setSavedFilters(prev => prev.filter((_, i) => i !== index));
  };

  const hasActiveFilters = 
    filters.searchTerm !== '' ||
    filters.status !== 'all' ||
    filters.priority !== 'all' ||
    filters.health !== 'all' ||
    filters.hasIssues ||
    filters.tags.length > 0 ||
    filters.dateRange !== 'all';

  return (
    <Card className="p-4 mb-6">
      <div className="space-y-4">
        {/* Quick Search */}
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Search projects by name or description..."
              value={filters.searchTerm}
              onChange={(e) => updateFilter('searchTerm', e.target.value)}
              className="w-full"
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={showAdvanced ? 'bg-blue-50 border-blue-200' : ''}
          >
            🔧 Advanced
          </Button>
          {hasActiveFilters && (
            <Button variant="outline" onClick={resetFilters}>
              🗑️ Clear
            </Button>
          )}
        </div>

        {/* Basic Filters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Status</option>
              {allStatuses.map(status => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="on_hold">On Hold</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Priority</label>
            <select
              value={filters.priority}
              onChange={(e) => updateFilter('priority', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Health</label>
            <select
              value={filters.health}
              onChange={(e) => updateFilter('health', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Health Levels</option>
              <option value="excellent">Excellent (80-100%)</option>
              <option value="good">Good (60-79%)</option>
              <option value="poor">Poor (0-59%)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Sort By</label>
            <div className="flex gap-1">
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter('sortBy', e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
              >
                <option value="name">Name</option>
                <option value="status">Status</option>
                <option value="priority">Priority</option>
                <option value="health">Health</option>
                <option value="created">Created</option>
              </select>
              <Button
                size="sm"
                variant="outline"
                onClick={() => updateFilter('sortOrder', filters.sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-2"
              >
                {filters.sortOrder === 'asc' ? '↑' : '↓'}
              </Button>
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t">
            {/* Tags Filter */}
            {allTags.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">Tags:</label>
                <div className="flex flex-wrap gap-2">
                  {allTags.map(tag => (
                    <Badge
                      key={tag}
                      variant={filters.tags.includes(tag) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleTag(tag)}
                    >
                      {tag}
                      {filters.tags.includes(tag) && ' ✓'}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => updateFilter('dateRange', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                >
                  <option value="all">All Time</option>
                  <option value="week">Last Week</option>
                  <option value="month">Last Month</option>
                  <option value="quarter">Last Quarter</option>
                  <option value="year">Last Year</option>
                </select>
              </div>

              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.hasIssues}
                    onChange={(e) => updateFilter('hasIssues', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm">Has Issues</span>
                </label>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={saveCurrentFilter}
                  className="text-sm"
                >
                  💾 Save Filter
                </Button>
              </div>
            </div>

            {/* Saved Filters */}
            {savedFilters.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">Saved Filters:</label>
                <div className="flex flex-wrap gap-2">
                  {savedFilters.map((savedFilter, index) => (
                    <div key={index} className="flex items-center gap-1">
                      <Badge
                        variant="outline"
                        className="cursor-pointer"
                        onClick={() => loadSavedFilter(savedFilter)}
                      >
                        {savedFilter.name}
                      </Badge>
                      <button
                        onClick={() => deleteSavedFilter(index)}
                        className="text-red-500 hover:text-red-700 text-xs"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-4 border-t">
            <div className="text-xs text-gray-600 mb-2">Active Filters:</div>
            <div className="flex flex-wrap gap-2">
              {filters.searchTerm && (
                <Badge variant="secondary" className="text-xs">
                  Search: "{filters.searchTerm}"
                </Badge>
              )}
              {filters.status !== 'all' && (
                <Badge variant="secondary" className="text-xs">
                  Status: {filters.status}
                </Badge>
              )}
              {filters.priority !== 'all' && (
                <Badge variant="secondary" className="text-xs">
                  Priority: {filters.priority}
                </Badge>
              )}
              {filters.health !== 'all' && (
                <Badge variant="secondary" className="text-xs">
                  Health: {filters.health}
                </Badge>
              )}
              {filters.hasIssues && (
                <Badge variant="secondary" className="text-xs">
                  Has Issues
                </Badge>
              )}
              {filters.tags.map(tag => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  Tag: {tag}
                </Badge>
              ))}
              {filters.dateRange !== 'all' && (
                <Badge variant="secondary" className="text-xs">
                  Date: {filters.dateRange}
                </Badge>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}