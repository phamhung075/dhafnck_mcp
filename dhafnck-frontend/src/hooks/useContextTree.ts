/**
 * Context Tree State Management Hook
 * Provides state management and actions for the hierarchical context tree
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { mcpApi } from '../api/enhanced';
import {
  ContextAnalytics,
  ContextHealthStatus,
  ContextSearchFilters,
  ContextTreeActions,
  ContextTreeError,
  ContextTreeState,
  DelegationRequest,
  TreePerformanceMetrics
} from '../types/context-tree';
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

interface UseContextTreeOptions {
  projectId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableHealthChecks?: boolean;
  enableAnalytics?: boolean;
}

interface UseContextTreeReturn {
  state: ContextTreeState;
  actions: ContextTreeActions;
  analytics: ContextAnalytics | null;
  performance: TreePerformanceMetrics | null;
  errors: ContextTreeError[];
}

export function useContextTree(options: UseContextTreeOptions = {}): UseContextTreeReturn {
  const {
    projectId,
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    enableHealthChecks = true,
    enableAnalytics = false
  } = options;

  // Main state
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

  // Analytics and performance state
  const [analytics, setAnalytics] = useState<ContextAnalytics | null>(null);
  const [performance, setPerformance] = useState<TreePerformanceMetrics | null>(null);
  const [errors, setErrors] = useState<ContextTreeError[]>([]);

  // Computed values
  const filteredContexts = useMemo(() => {
    return ContextTreeUtils.filterContexts(state.contexts, state.searchFilters);
  }, [state.contexts, state.searchFilters]);

  const treeStructure = useMemo(() => {
    const startTime = window.performance?.now() || Date.now();
    const tree = ContextTreeUtils.buildTreeStructure(filteredContexts);
    const endTime = window.performance?.now() || Date.now();

    const metrics: TreePerformanceMetrics = {
      render_time_ms: endTime - startTime,
      node_count: filteredContexts.length,
      depth: ContextTreeUtils.calculateMaxDepth(tree),
      expanded_nodes: state.expandedNodes.size,
      health_checks_pending: Object.values(state.healthStatuses).filter(h => h.status === 'stale').length
    };

    setPerformance(metrics);
    return tree;
  }, [filteredContexts, state.expandedNodes, state.healthStatuses]);

  // Update derived state
  useEffect(() => {
    setState(prev => ({
      ...prev,
      filteredContexts,
      treeStructure
    }));
  }, [filteredContexts, treeStructure]);

  // Calculate analytics when enabled
  useEffect(() => {
    if (enableAnalytics && state.contexts.length > 0) {
      const analyticsData = ContextTreeUtils.calculateAnalytics(state.contexts);
      setAnalytics(analyticsData);
    }
  }, [state.contexts, enableAnalytics]);

  // Error handler
  const handleError = useCallback((error: Error, operation: string, contextId?: string, level?: string) => {
    const contextError: ContextTreeError = {
      code: 'OPERATION_FAILED',
      message: error.message,
      context_id: contextId,
      level: level,
      operation,
      details: error,
      timestamp: Date.now()
    };

    setErrors(prev => [...prev.slice(-9), contextError]); // Keep last 10 errors
    setState(prev => ({ ...prev, error: error.message }));
  }, []);

  // Clear errors
  const clearErrors = useCallback(() => {
    setErrors([]);
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Load contexts from API
  const loadContexts = useCallback(async (forceRefresh = false) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Note: This is a placeholder - the actual API endpoint for getting contexts 
      // would need to be implemented in the backend
      const response = await mcpApi.manageHierarchicalContext('get_health');
      
      if (response.success) {
        // For now, return empty array as this endpoint doesn't exist yet
        // In real implementation, this would fetch all contexts for the project
        setState(prev => ({
          ...prev,
          contexts: [],
          loading: false
        }));
      }
    } catch (error) {
      handleError(error as Error, 'load_contexts');
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [handleError]);

  // Resolve context with full inheritance
  const resolveContext = useCallback(async (contextId: string, level: string) => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      const response = await mcpApi.manageHierarchicalContext('resolve', {
        level,
        context_id: contextId,
        force_refresh: false
      });

      if (response.success) {
        // Update the specific context with resolved data
        setState(prev => ({
          ...prev,
          contexts: prev.contexts.map(context =>
            context.context_id === contextId
              ? { ...context, resolved_data: response.data.resolved_data }
              : context
          ),
          loading: false
        }));

        // Update health status if health checks are enabled
        if (enableHealthChecks) {
          await validateInheritance(contextId, level);
        }
      }
    } catch (error) {
      handleError(error as Error, 'resolve_context', contextId, level);
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [enableHealthChecks, handleError]);

  // Validate context inheritance
  const validateInheritance = useCallback(async (contextId: string, level: string) => {
    try {
      const response = await mcpApi.validateContextInheritance(level, contextId);

      if (response.success) {
        const validation = response.data;
        if (validation) {
          const healthStatus: ContextHealthStatus = {
            status: validation.valid ? 'healthy' : 'error',
            issues: [
              ...validation.errors.map((error: string) => ({
                type: 'error' as const,
                message: error,
                severity: 'high' as const
              })),
              ...validation.warnings.map((warning: string) => ({
                type: 'warning' as const,
                message: warning,
                severity: 'medium' as const
              }))
            ],
            score: validation.valid ? 100 : Math.max(0, 100 - (validation.errors.length * 25)),
            last_validated: new Date().toISOString(),
            validation_details: {
              inheritance_chain_valid: validation.valid,
              cache_consistency: validation.cache_metrics?.hit_ratio > 0.8,
              resolution_timing: validation.resolution_timing || { total_ms: 0, cache_lookup_ms: 0, inheritance_resolution_ms: 0 },
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
      } else {
        // Set error health status
        const errorStatus: ContextHealthStatus = {
          status: 'error',
          issues: [{
            type: 'error',
            message: `Validation failed: ${response.error || 'Unknown error'}`,
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
    } catch (error) {
      handleError(error as Error, 'validate_inheritance', contextId, level);
      
      // Set error health status
      const errorStatus: ContextHealthStatus = {
        status: 'error',
        issues: [{
          type: 'error',
          message: 'Validation failed: Unknown error',
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
  }, [handleError]);

  // Delegate context to higher level
  const delegate = useCallback(async (delegation: DelegationRequest) => {
    setState(prev => ({ ...prev, loading: true }));

    try {
      const response = await mcpApi.manageHierarchicalContext('delegate', {
        level: delegation.source_level,
        context_id: delegation.source_context_id,
        delegate_to: delegation.target_level,
        delegate_data: delegation.delegation_data,
        delegation_reason: delegation.delegation_reason
      });

      if (response.success) {
        // Refresh contexts after successful delegation
        await loadContexts(true);
        setState(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      handleError(error as Error, 'delegate_context', delegation.source_context_id);
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [loadContexts, handleError]);

  // Select context
  const selectContext = useCallback((contextId: string) => {
    setState(prev => ({ ...prev, selectedContext: contextId }));
  }, []);

  // Toggle node expansion
  const toggleExpanded = useCallback((contextId: string) => {
    setState(prev => ({
      ...prev,
      expandedNodes: prev.expandedNodes.has(contextId)
        ? new Set(Array.from(prev.expandedNodes).filter(id => id !== contextId))
        : new Set(Array.from(prev.expandedNodes).concat(contextId))
    }));
  }, []);

  // Update search filters
  const updateSearchFilters = useCallback((filters: Partial<ContextSearchFilters>) => {
    setState(prev => ({
      ...prev,
      searchFilters: { ...prev.searchFilters, ...filters }
    }));
  }, []);

  // Refresh health statuses for all contexts
  const refreshHealth = useCallback(async (contextId?: string) => {
    const contextsToCheck = contextId 
      ? state.contexts.filter(c => c.context_id === contextId)
      : state.contexts;

    const healthPromises = contextsToCheck.map(context => 
      validateInheritance(context.context_id, context.level)
    );

    await Promise.allSettled(healthPromises);
  }, [state.contexts, validateInheritance]);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    await loadContexts(true);
    if (enableHealthChecks) {
      await refreshHealth();
    }
  }, [loadContexts, enableHealthChecks, refreshHealth]);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(refreshAll, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refreshAll]);

  // Initial load effect
  useEffect(() => {
    loadContexts();
  }, [loadContexts, projectId]);

  // Validate tree structure when contexts change
  useEffect(() => {
    if (state.contexts.length > 0) {
      const structureErrors = ContextTreeUtils.validateTreeStructure(state.contexts);
      if (structureErrors.length > 0) {
        setErrors(prev => [...prev, ...structureErrors]);
      }
    }
  }, [state.contexts]);

  // Actions object
  const actions: ContextTreeActions = useMemo(() => ({
    resolveContext,
    validateInheritance,
    selectContext,
    toggleExpanded,
    updateSearchFilters,
    delegate,
    refreshHealth,
    refreshAll
  }), [
    resolveContext,
    validateInheritance,
    selectContext,
    toggleExpanded,
    updateSearchFilters,
    delegate,
    refreshHealth,
    refreshAll
  ]);

  return {
    state,
    actions,
    analytics,
    performance,
    errors
  };
}