/**
 * Hierarchical Context Tree Component
 * Visualizes Global → Project → Task hierarchy with inheritance and delegation
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { mcpApi } from '../api/enhanced';
import { 
  ContextTreeProps, 
  ContextTreeState, 
  HierarchicalContext, 
  ContextHealthStatus,
  TreeNode,
  ContextSearchFilters,
  DelegationRequest,
  TreePerformanceMetrics
} from '../types/context-tree';
import { ContextNode } from './ContextNode';
import { ContextSearch } from './ContextSearch';
import { ContextTreeUtils } from '../utils/context-tree-utils';

const defaultSearchFilters: ContextSearchFilters = {
  searchTerm: '',
  level: 'all',
  health: 'all',
  hasIssues: false,
  status: [],
  priority: [],
  assignees: [],
  labels: []
};

export function ContextTree({
  contexts,
  selectedContext,
  onContextSelect,
  onResolveContext,
  onDelegate,
  onValidateInheritance,
  className = '',
  showHealthIndicators = true,
  enableDragDrop = true,
  enableSearch = true
}: ContextTreeProps) {
  const [state, setState] = useState<ContextTreeState>({
    contexts: [],
    selectedContext: null,
    expandedNodes: new Set(),
    healthStatuses: {},
    searchFilters: defaultSearchFilters,
    filteredContexts: [],
    loading: false,
    error: null,
    treeStructure: [],
    delegationQueue: []
  });

  const [performanceMetrics, setPerformanceMetrics] = useState<TreePerformanceMetrics>({
    render_time_ms: 0,
    node_count: 0,
    depth: 0,
    expanded_nodes: 0,
    health_checks_pending: 0
  });

  // Update state when contexts prop changes
  useEffect(() => {
    setState(prev => ({
      ...prev,
      contexts: contexts,
      selectedContext: selectedContext
    }));
  }, [contexts, selectedContext]);

  // Build tree structure from flat context list
  const treeStructure = useMemo(() => {
    const startTime = performance.now();
    const tree = ContextTreeUtils.buildTreeStructure(state.contexts);
    const endTime = performance.now();

    const metrics: TreePerformanceMetrics = {
      render_time_ms: endTime - startTime,
      node_count: state.contexts.length,
      depth: ContextTreeUtils.calculateMaxDepth(tree),
      expanded_nodes: state.expandedNodes.size,
      health_checks_pending: Object.values(state.healthStatuses).filter(h => h.status === 'stale').length
    };

    setPerformanceMetrics(metrics);
    return tree;
  }, [state.contexts, state.expandedNodes, state.healthStatuses]);

  // Filter contexts based on search criteria
  const filteredContexts = useMemo(() => {
    if (!enableSearch) return state.contexts;
    
    return ContextTreeUtils.filterContexts(state.contexts, state.searchFilters);
  }, [state.contexts, state.searchFilters, enableSearch]);

  // Health status management
  const updateHealthStatus = useCallback(async (contextId: string, level: string) => {
    try {
      const validation = await mcpApi.executeTool('validate_context_inheritance', {
        level,
        context_id: contextId
      });

      if (validation.success && validation.data) {
        const validationData = validation.data as any;
        const healthStatus: ContextHealthStatus = {
          status: validationData.validation?.valid ? 'healthy' : 'error',
          issues: [
            ...(validationData.validation?.errors || []).map((error: string) => ({
              type: 'error' as const,
              message: error,
              severity: 'high' as const
            })),
            ...(validationData.validation?.warnings || []).map((warning: string) => ({
              type: 'warning' as const,
              message: warning,
              severity: 'medium' as const
            }))
          ],
          score: validationData.validation?.valid ? 100 : 50,
          last_validated: new Date().toISOString(),
          validation_details: {
            inheritance_chain_valid: validationData.validation?.valid || false,
            cache_consistency: (validationData.validation?.cache_metrics?.hit_ratio || 0) > 0.8,
            resolution_timing: validationData.validation?.resolution_timing || { total_ms: 0, cache_lookup_ms: 0, inheritance_resolution_ms: 0 },
            dependency_hash_match: true
          }
        };

        setState(prev => ({
          ...prev,
          healthStatuses: {
            ...prev.healthStatuses,
            [contextId]: healthStatus
          }
        }));
      }
    } catch (error) {
      const errorStatus: ContextHealthStatus = {
        status: 'error',
        issues: [{
          type: 'error',
          message: `Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
          severity: 'critical'
        }],
        score: 0,
        last_validated: new Date().toISOString()
      };

      setState(prev => ({
        ...prev,
        healthStatuses: {
          ...prev.healthStatuses,
          [contextId]: errorStatus
        }
      }));
    }
  }, []);

  // Context resolution handler
  const handleResolveContext = useCallback(async (contextId: string, level: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      await onResolveContext(contextId, level);
      
      // Update health status after resolution
      if (showHealthIndicators) {
        await updateHealthStatus(contextId, level);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to resolve context'
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [onResolveContext, showHealthIndicators, updateHealthStatus]);

  // Context validation handler
  const handleValidateInheritance = useCallback(async (contextId: string, level: string) => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      await onValidateInheritance(contextId, level);
      await updateHealthStatus(contextId, level);
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to validate inheritance'
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [onValidateInheritance, updateHealthStatus]);

  // Delegation handler
  const handleDelegate = useCallback(async (
    fromContext: string, 
    toLevel: 'project' | 'global', 
    data: any
  ) => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      await onDelegate(fromContext, toLevel, data);
      
      // Refresh contexts after delegation
      // Note: This assumes parent component will provide updated contexts
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to delegate context'
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [onDelegate]);

  // Search filter update handler
  const handleSearchFilterChange = useCallback((filters: Partial<ContextSearchFilters>) => {
    setState(prev => ({
      ...prev,
      searchFilters: { ...prev.searchFilters, ...filters }
    }));
  }, []);

  // Node selection handler
  const handleContextSelect = useCallback((contextId: string, level: string) => {
    setState(prev => ({ ...prev, selectedContext: contextId }));
    onContextSelect(contextId, level);
  }, [onContextSelect]);

  // Node expansion handler
  const handleToggleExpanded = useCallback((contextId: string) => {
    setState(prev => ({
      ...prev,
      expandedNodes: prev.expandedNodes.has(contextId)
        ? new Set(Array.from(prev.expandedNodes).filter(id => id !== contextId))
        : new Set(Array.from(prev.expandedNodes).concat(contextId))
    }));
  }, []);

  // Render tree nodes recursively
  const renderTreeNode = useCallback((node: TreeNode, index: number) => {
    const isSelected = state.selectedContext === node.context.context_id;
    const isExpanded = state.expandedNodes.has(node.context.context_id);
    const healthStatus = state.healthStatuses[node.context.context_id] || {
      status: 'stale' as const,
      issues: [],
      score: 0,
      last_validated: ''
    };

    return (
      <div key={node.context.context_id} className="relative">
        <ContextNode
          context={node.context}
          level={node.level}
          isSelected={isSelected}
          isExpanded={isExpanded}
          children={node.children.map(child => child.context)}
          healthStatus={healthStatus}
          onSelect={() => handleContextSelect(node.context.context_id, node.level)}
          onToggleExpand={() => handleToggleExpanded(node.context.context_id)}
          onDelegate={(data) => handleDelegate(node.context.context_id, 'project', data)}
          onValidate={() => handleValidateInheritance(node.context.context_id, node.level)}
          onResolve={() => handleResolveContext(node.context.context_id, node.level)}
          enableDragDrop={enableDragDrop}
          showHealth={showHealthIndicators}
        />
        
        {isExpanded && node.children.length > 0 && (
          <div className="ml-6 mt-2 space-y-2">
            {node.children.map((child, childIndex) => renderTreeNode(child, childIndex))}
          </div>
        )}
      </div>
    );
  }, [
    state.selectedContext,
    state.expandedNodes,
    state.healthStatuses,
    handleContextSelect,
    handleToggleExpanded,
    handleDelegate,
    handleValidateInheritance,
    handleResolveContext,
    enableDragDrop,
    showHealthIndicators
  ]);

  // Auto-load health statuses on mount
  useEffect(() => {
    if (showHealthIndicators && contexts.length > 0) {
      contexts.forEach(context => {
        if (!state.healthStatuses[context.context_id]) {
          updateHealthStatus(context.context_id, context.level);
        }
      });
    }
  }, [contexts, showHealthIndicators, state.healthStatuses, updateHealthStatus]);

  return (
    <div className={`context-tree ${className}`}>
      {/* Search and Filter Controls */}
      {enableSearch && (
        <ContextSearch
          contexts={state.contexts}
          filters={state.searchFilters}
          onFilterChange={handleSearchFilterChange}
          className="mb-4"
        />
      )}

      {/* Performance Metrics (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="text-xs text-gray-500 mb-2 p-2 bg-gray-50 rounded">
          Nodes: {performanceMetrics.node_count} | 
          Depth: {performanceMetrics.depth} | 
          Expanded: {performanceMetrics.expanded_nodes} | 
          Render: {performanceMetrics.render_time_ms.toFixed(2)}ms
        </div>
      )}

      {/* Error Display */}
      {state.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4">
          {state.error}
        </div>
      )}

      {/* Loading Indicator */}
      {state.loading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-3 py-2 rounded mb-4">
          Processing context operation...
        </div>
      )}

      {/* Tree Structure */}
      <div className="tree-container space-y-2">
        {filteredContexts.length === 0 && !state.loading ? (
          <div className="text-gray-500 text-center py-8">
            {state.searchFilters.searchTerm ? 'No contexts match your search criteria' : 'No contexts available'}
          </div>
        ) : (
          <div className="tree-nodes">
            {treeStructure.map((node, index) => renderTreeNode(node, index))}
          </div>
        )}
      </div>

      {/* Context Statistics */}
      {contexts.length > 0 && (
        <div className="mt-4 text-xs text-gray-500 border-t pt-2">
          <div className="flex justify-between">
            <span>Total Contexts: {contexts.length}</span>
            <span>
              Global: {contexts.filter(c => c.level === 'global').length} | 
              Project: {contexts.filter(c => c.level === 'project').length} | 
              Task: {contexts.filter(c => c.level === 'task').length}
            </span>
          </div>
          {showHealthIndicators && (
            <div className="flex justify-between mt-1">
              <span>Health Status:</span>
              <span>
                Healthy: {Object.values(state.healthStatuses).filter(h => h.status === 'healthy').length} | 
                Warning: {Object.values(state.healthStatuses).filter(h => h.status === 'warning').length} | 
                Error: {Object.values(state.healthStatuses).filter(h => h.status === 'error').length}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}