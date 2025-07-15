/**
 * Context Search and Filter Component
 * Provides search and filtering capabilities for the context tree
 */
import React, { useState, useEffect, useMemo } from 'react';
import { 
  HierarchicalContext, 
  ContextSearchFilters, 
  SearchResult 
} from '../types/context-tree';
import { ContextTreeUtils } from '../utils/context-tree-utils';

interface ContextSearchProps {
  contexts: HierarchicalContext[];
  filters: ContextSearchFilters;
  onFilterChange: (filters: Partial<ContextSearchFilters>) => void;
  className?: string;
}

// Individual filter components
function SearchInput({ 
  value, 
  onChange, 
  placeholder = "Search contexts..."
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const [localValue, setLocalValue] = useState(value);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [localValue, onChange]);

  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  return (
    <div className="relative">
      <input
        type="text"
        placeholder={placeholder}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        className="w-full px-3 py-2 pr-8 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>
  );
}

function LevelFilter({ 
  value, 
  onChange 
}: {
  value: string;
  onChange: (value: 'all' | 'global' | 'project' | 'task') => void;
}) {
  return (
    <select 
      value={value} 
      onChange={(e) => onChange(e.target.value as 'all' | 'global' | 'project' | 'task')}
      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="all">All Levels</option>
      <option value="global">Global</option>
      <option value="project">Project</option>
      <option value="task">Task</option>
    </select>
  );
}

function HealthFilter({ 
  value, 
  onChange 
}: {
  value: string;
  onChange: (value: 'all' | 'healthy' | 'warning' | 'error' | 'stale') => void;
}) {
  return (
    <select 
      value={value} 
      onChange={(e) => onChange(e.target.value as 'all' | 'healthy' | 'warning' | 'error' | 'stale')}
      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="all">All Health</option>
      <option value="healthy">Healthy</option>
      <option value="warning">Warning</option>
      <option value="error">Error</option>
      <option value="stale">Stale</option>
    </select>
  );
}

function MultiSelectFilter({
  title,
  options,
  selected,
  onChange,
  placeholder = "Select..."
}: {
  title: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = (option: string) => {
    const newSelected = selected.includes(option)
      ? selected.filter(item => item !== option)
      : [...selected, option];
    onChange(newSelected);
  };

  const handleClear = () => {
    onChange([]);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between"
      >
        <span className="truncate">
          {selected.length === 0 
            ? placeholder 
            : selected.length === 1 
              ? selected[0] 
              : `${selected.length} selected`
          }
        </span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          <div className="sticky top-0 bg-gray-50 px-3 py-2 border-b">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">{title}</span>
              {selected.length > 0 && (
                <button
                  onClick={handleClear}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          
          <div className="py-1">
            {options.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">No options available</div>
            ) : (
              options.map(option => (
                <label key={option} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selected.includes(option)}
                    onChange={() => handleToggle(option)}
                    className="mr-2 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 truncate">{option}</span>
                </label>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function FilterSummary({ 
  filters, 
  resultCount, 
  totalCount,
  onClearAll 
}: {
  filters: ContextSearchFilters;
  resultCount: number;
  totalCount: number;
  onClearAll: () => void;
}) {
  const activeFilters = [];
  
  if (filters.searchTerm) activeFilters.push(`search: "${filters.searchTerm}"`);
  if (filters.level !== 'all') activeFilters.push(`level: ${filters.level}`);
  if (filters.health !== 'all') activeFilters.push(`health: ${filters.health}`);
  if (filters.status.length > 0) activeFilters.push(`status: ${filters.status.length} selected`);
  if (filters.priority.length > 0) activeFilters.push(`priority: ${filters.priority.length} selected`);
  if (filters.assignees.length > 0) activeFilters.push(`assignees: ${filters.assignees.length} selected`);
  if (filters.labels.length > 0) activeFilters.push(`labels: ${filters.labels.length} selected`);
  if (filters.hasIssues) activeFilters.push('has issues');

  if (activeFilters.length === 0) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="text-sm text-blue-800">
            Showing {resultCount} of {totalCount} contexts
          </div>
          <div className="text-xs text-blue-600 mt-1">
            Active filters: {activeFilters.join(', ')}
          </div>
        </div>
        <button
          onClick={onClearAll}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          Clear All
        </button>
      </div>
    </div>
  );
}

export function ContextSearch({ 
  contexts, 
  filters, 
  onFilterChange, 
  className = '' 
}: ContextSearchProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Extract unique values from contexts for filter options
  const filterOptions = useMemo(() => {
    const statuses = new Set<string>();
    const priorities = new Set<string>();
    const assignees = new Set<string>();
    const labels = new Set<string>();

    contexts.forEach(context => {
      if (context.data.status) statuses.add(context.data.status);
      if (context.data.priority) priorities.add(context.data.priority);
      if (context.data.assignees) {
        context.data.assignees.forEach((assignee: string) => assignees.add(assignee));
      }
      if (context.data.labels) {
        context.data.labels.forEach((label: string) => labels.add(label));
      }
    });

    return {
      statuses: Array.from(statuses).sort(),
      priorities: Array.from(priorities).sort(),
      assignees: Array.from(assignees).sort(),
      labels: Array.from(labels).sort()
    };
  }, [contexts]);

  // Calculate filtered results count
  const filteredContexts = useMemo(() => {
    return ContextTreeUtils.filterContexts(contexts, filters);
  }, [contexts, filters]);

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<ContextSearchFilters>) => {
    onFilterChange(newFilters);
  };

  // Clear all filters
  const handleClearAll = () => {
    onFilterChange({
      searchTerm: '',
      level: 'all',
      health: 'all',
      hasIssues: false,
      status: [],
      priority: [],
      assignees: [],
      labels: []
    });
  };

  // Check if any filters are active
  const hasActiveFilters = 
    filters.searchTerm || 
    filters.level !== 'all' || 
    filters.health !== 'all' ||
    filters.status.length > 0 ||
    filters.priority.length > 0 ||
    filters.assignees.length > 0 ||
    filters.labels.length > 0 ||
    filters.hasIssues;

  return (
    <div className={`context-search ${className}`}>
      {/* Search Input */}
      <div className="mb-3">
        <SearchInput
          value={filters.searchTerm}
          onChange={(value) => handleFilterChange({ searchTerm: value })}
          placeholder="Search contexts by title, description, or ID..."
        />
      </div>

      {/* Quick Filters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <LevelFilter
          value={filters.level}
          onChange={(value) => handleFilterChange({ level: value })}
        />
        <HealthFilter
          value={filters.health}
          onChange={(value) => handleFilterChange({ health: value })}
        />
        <label className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md">
          <input
            type="checkbox"
            checked={filters.hasIssues}
            onChange={(e) => handleFilterChange({ hasIssues: e.target.checked })}
            className="text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Has Issues</span>
        </label>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md flex items-center justify-center"
        >
          <span>More Filters</span>
          <svg 
            className={`w-4 h-4 ml-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Advanced Filters */}
      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 mb-3 p-3 bg-gray-50 rounded-md">
          <MultiSelectFilter
            title="Status"
            options={filterOptions.statuses}
            selected={filters.status}
            onChange={(selected) => handleFilterChange({ status: selected })}
            placeholder="Filter by status"
          />
          <MultiSelectFilter
            title="Priority"
            options={filterOptions.priorities}
            selected={filters.priority}
            onChange={(selected) => handleFilterChange({ priority: selected })}
            placeholder="Filter by priority"
          />
          <MultiSelectFilter
            title="Assignees"
            options={filterOptions.assignees}
            selected={filters.assignees}
            onChange={(selected) => handleFilterChange({ assignees: selected })}
            placeholder="Filter by assignees"
          />
          <MultiSelectFilter
            title="Labels"
            options={filterOptions.labels}
            selected={filters.labels}
            onChange={(selected) => handleFilterChange({ labels: selected })}
            placeholder="Filter by labels"
          />
        </div>
      )}

      {/* Filter Summary */}
      {hasActiveFilters && (
        <FilterSummary
          filters={filters}
          resultCount={filteredContexts.length}
          totalCount={contexts.length}
          onClearAll={handleClearAll}
        />
      )}
    </div>
  );
}