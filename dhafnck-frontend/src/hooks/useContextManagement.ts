/**
 * useContextManagement Hook
 * Centralized state management for context details panel and delegation workflow
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { mcpApi } from '../api/enhanced';
import {
    ContextData,
    ContextInheritanceValidation,
    ContextInsight,
    ContextManagementState,
    ContextProgress,
    DelegationHistoryItem,
    DelegationPreview,
    DelegationRequest,
    InheritanceChainItem,
    PendingDelegation,
    ResolvedContext,
    UseContextManagementReturn
} from '../types/context-delegation';

interface UseContextManagementOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableCache?: boolean;
}

export function useContextManagement(
  projectId?: string,
  taskId?: string,
  options: UseContextManagementOptions = {}
): UseContextManagementReturn {
  const {
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    enableCache = true
  } = options;

  // State
  const [state, setState] = useState<ContextManagementState>({
    selectedContext: null,
    resolvedContext: null,
    inheritanceChain: [],
    validationResults: {},
    delegationQueue: [],
    delegationHistory: [],
    insights: {},
    progress: {},
    availablePatterns: [],
    availableTargets: [],
    editMode: false,
    unsavedChanges: false,
    loading: {
      context: false,
      delegation: false,
      validation: false,
      insights: false
    },
    errors: {}
  });

  // Refs
  const cacheRef = useRef<Map<string, any>>(new Map());
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cache helpers
  const getCacheKey = useCallback((operation: string, params: any) => {
    return `${operation}_${JSON.stringify(params)}`;
  }, []);

  const getCachedData = useCallback((key: string) => {
    if (!enableCache) return null;
    const cached = cacheRef.current.get(key);
    if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
      return cached.data;
    }
    return null;
  }, [enableCache]);

  const setCachedData = useCallback((key: string, data: any) => {
    if (enableCache) {
      cacheRef.current.set(key, {
        data,
        timestamp: Date.now()
      });
    }
  }, [enableCache]);

  // Error handling
  const handleError = useCallback((operation: string, error: unknown) => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [operation]: errorMessage
      }
    }));
    console.error(`Context management error (${operation}):`, error);
  }, []);

  // Clear error
  const clearError = useCallback((operation: string) => {
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [operation]: undefined
      }
    }));
  }, []);

  // Set loading state
  const setLoading = useCallback((operation: keyof ContextManagementState['loading'], loading: boolean) => {
    setState(prev => ({
      ...prev,
      loading: {
        ...prev.loading,
        [operation]: loading
      }
    }));
  }, []);

  // Context operations
  const updateContext = useCallback(async (contextId: string, updates: Partial<ContextData>) => {
    setLoading('context', true);
    clearError('context');

    try {
      // Flatten the updates for MCP API
      const flattenedUpdates: Record<string, any> = {};
      Object.entries(updates).forEach(([key, value]) => {
        flattenedUpdates[`data_${key}`] = value;
      });

      const result = await mcpApi.manageContext('update', {
        task_id: contextId,
        ...flattenedUpdates
      });

      if (result.success) {
        // Update local state
        setState(prev => ({
          ...prev,
          selectedContext: prev.selectedContext ? {
            ...prev.selectedContext,
            data: { ...prev.selectedContext.data, ...updates }
          } : null,
          unsavedChanges: false
        }));

        // Invalidate cache
        cacheRef.current.clear();
      } else {
        throw new Error(result.error || 'Failed to update context');
      }
    } catch (error) {
      handleError('context', error);
      throw error;
    } finally {
      setLoading('context', false);
    }
  }, [setLoading, clearError, handleError]);

  const resolveContext = useCallback(async (contextId: string, level: string, forceRefresh = false) => {
    const cacheKey = getCacheKey('resolve', { contextId, level });
    
    if (!forceRefresh) {
      const cached = getCachedData(cacheKey);
      if (cached) {
        setState(prev => ({
          ...prev,
          resolvedContext: cached.resolvedContext,
          inheritanceChain: cached.inheritanceChain
        }));
        return;
      }
    }

    setLoading('context', true);
    clearError('context');

    try {
      const result = await mcpApi.manageHierarchicalContext('resolve', {
        level,
        context_id: contextId,
        force_refresh: forceRefresh
      });

      if (result.success && result.data) {
        const resolvedContext: ResolvedContext = {
          context: result.data.resolved_context,
          inheritance_chain: result.data.inheritance_chain || [],
          resolved_data: result.data.resolved_context?.data || {},
          conflicts: result.data.conflicts || [],
          resolution_metadata: result.data.resolution_metadata || {
            resolved_at: new Date().toISOString(),
            dependency_hash: '',
            cache_status: 'miss' as const,
            resolution_timing: { total_ms: 0, cache_lookup_ms: 0, inheritance_resolution_ms: 0 }
          }
        };

        const inheritanceChain: InheritanceChainItem[] = result.data.inheritance_chain?.map((item: any) => ({
          level: item.level,
          context_id: item.context_id,
          data: item.data || {},
          effective_properties: item.effective_properties || [],
          overridden_properties: item.overridden_properties || []
        })) || [];

        setState(prev => ({
          ...prev,
          resolvedContext,
          inheritanceChain,
          selectedContext: result.data.resolved_context
        }));

        setCachedData(cacheKey, { resolvedContext, inheritanceChain });
      } else {
        throw new Error(result.error || 'Failed to resolve context');
      }
    } catch (error) {
      handleError('context', error);
      throw error;
    } finally {
      setLoading('context', false);
    }
  }, [getCacheKey, getCachedData, setCachedData, setLoading, clearError, handleError]);

  const refreshContext = useCallback(async (contextId: string) => {
    if (state.selectedContext) {
      await resolveContext(contextId, state.selectedContext.level, true);
    }
  }, [state.selectedContext, resolveContext]);

  // Delegation operations
  const delegateContext = useCallback(async (delegation: DelegationRequest) => {
    setLoading('delegation', true);
    clearError('delegation');

    try {
      const result = await mcpApi.manageHierarchicalContext('delegate', {
        level: delegation.source_level,
        context_id: delegation.source_context_id,
        delegate_to: delegation.target_level,
        delegate_data: delegation.delegation_data,
        delegation_reason: delegation.delegation_reason
      });

      if (result.success) {
        // Add to delegation history
        const historyItem: DelegationHistoryItem = {
          delegation_id: `del_${Date.now()}`,
          action: 'created',
          timestamp: new Date().toISOString(),
          user_id: 'current_user',
          details: `Delegated ${delegation.delegation_data.pattern_name} to ${delegation.target_level}`
        };

        setState(prev => ({
          ...prev,
          delegationHistory: [historyItem, ...prev.delegationHistory]
        }));

        // Refresh delegation queue
        await refreshDelegationQueue();
      } else {
        throw new Error(result.error || 'Failed to delegate context');
      }
    } catch (error) {
      handleError('delegation', error);
      throw error;
    } finally {
      setLoading('delegation', false);
    }
  }, [setLoading, clearError, handleError]);

  const previewDelegation = useCallback(async (delegation: DelegationRequest): Promise<DelegationPreview> => {
    // Mock preview for now - in real implementation, this would call an API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          estimated_impact: 'medium',
          affected_contexts: ['project_context_1', 'task_context_2'],
          potential_conflicts: [],
          recommendations: ['Consider adding more documentation', 'Test in staging environment first'],
          approval_likelihood: 0.85
        });
      }, 1000);
    });
  }, []);

  const approveDelegation = useCallback(async (delegationId: string) => {
    setLoading('delegation', true);
    clearError('delegation');

    try {
      const result = await mcpApi.manageDelegationQueue('approve', {
        delegation_id: delegationId
      });

      if (result.success) {
        await refreshDelegationQueue();
      } else {
        throw new Error(result.error || 'Failed to approve delegation');
      }
    } catch (error) {
      handleError('delegation', error);
      throw error;
    } finally {
      setLoading('delegation', false);
    }
  }, [setLoading, clearError, handleError]);

  const rejectDelegation = useCallback(async (delegationId: string, reason: string) => {
    setLoading('delegation', true);
    clearError('delegation');

    try {
      const result = await mcpApi.manageDelegationQueue('reject', {
        delegation_id: delegationId,
        rejection_reason: reason
      });

      if (result.success) {
        await refreshDelegationQueue();
      } else {
        throw new Error(result.error || 'Failed to reject delegation');
      }
    } catch (error) {
      handleError('delegation', error);
      throw error;
    } finally {
      setLoading('delegation', false);
    }
  }, [setLoading, clearError, handleError]);

  const refreshDelegationQueue = useCallback(async () => {
    try {
      const result = await mcpApi.manageDelegationQueue('list');
      
      if (result.success && result.data) {
        const pendingDelegations: PendingDelegation[] = result.data.pending_delegations?.map((item: any) => ({
          delegation_id: item.delegation_id,
          source_context: item.source_context,
          source_level: item.source_level,
          target_level: item.target_level,
          delegation_data: item.data,
          delegation_reason: item.reason,
          created_at: item.created_at,
          created_by: item.created_by || 'unknown',
          status: item.status || 'pending'
        })) || [];

        setState(prev => ({
          ...prev,
          delegationQueue: pendingDelegations
        }));
      }
    } catch (error) {
      handleError('delegation', error);
    }
  }, [handleError]);

  // Insight operations
  const addInsight = useCallback(async (contextId: string, insight: ContextInsight) => {
    setLoading('insights', true);
    clearError('insights');

    try {
      const result = await mcpApi.manageContext('add_insight', {
        task_id: contextId,
        content: insight.content,
        category: insight.category,
        importance: insight.importance
      });

      if (result.success) {
        setState(prev => ({
          ...prev,
          insights: {
            ...prev.insights,
            [contextId]: [...(prev.insights[contextId] || []), insight]
          }
        }));
      } else {
        throw new Error(result.error || 'Failed to add insight');
      }
    } catch (error) {
      handleError('insights', error);
      throw error;
    } finally {
      setLoading('insights', false);
    }
  }, [setLoading, clearError, handleError]);

  const updateInsight = useCallback(async (contextId: string, insightId: string, updates: Partial<ContextInsight>) => {
    setLoading('insights', true);
    clearError('insights');

    try {
      // Update local state - in real implementation, this would call an API
      setState(prev => ({
        ...prev,
        insights: {
          ...prev.insights,
          [contextId]: prev.insights[contextId]?.map(insight =>
            insight.id === insightId ? { ...insight, ...updates } : insight
          ) || []
        }
      }));
    } catch (error) {
      handleError('insights', error);
      throw error;
    } finally {
      setLoading('insights', false);
    }
  }, [setLoading, clearError, handleError]);

  const deleteInsight = useCallback(async (contextId: string, insightId: string) => {
    setLoading('insights', true);
    clearError('insights');

    try {
      // Update local state - in real implementation, this would call an API
      setState(prev => ({
        ...prev,
        insights: {
          ...prev.insights,
          [contextId]: prev.insights[contextId]?.filter(insight => insight.id !== insightId) || []
        }
      }));
    } catch (error) {
      handleError('insights', error);
      throw error;
    } finally {
      setLoading('insights', false);
    }
  }, [setLoading, clearError, handleError]);

  const refreshInsights = useCallback(async (contextId: string) => {
    // In real implementation, this would fetch insights from API
    // For now, we'll keep existing local state
  }, []);

  // Progress operations
  const addProgress = useCallback(async (contextId: string, progress: ContextProgress) => {
    try {
      const result = await mcpApi.manageContext('add_progress', {
        task_id: contextId,
        content: progress.content
      });

      if (result.success) {
        setState(prev => ({
          ...prev,
          progress: {
            ...prev.progress,
            [contextId]: [...(prev.progress[contextId] || []), progress]
          }
        }));
      } else {
        throw new Error(result.error || 'Failed to add progress');
      }
    } catch (error) {
      handleError('context', error);
      throw error;
    }
  }, [handleError]);

  const updateNextSteps = useCallback(async (contextId: string, steps: string[]) => {
    try {
      const result = await mcpApi.manageContext('update_next_steps', {
        task_id: contextId,
        next_steps: steps
      });

      if (result.success) {
        setState(prev => ({
          ...prev,
          selectedContext: prev.selectedContext ? {
            ...prev.selectedContext,
            data: { ...prev.selectedContext.data, next_steps: steps }
          } : null
        }));
      } else {
        throw new Error(result.error || 'Failed to update next steps');
      }
    } catch (error) {
      handleError('context', error);
      throw error;
    }
  }, [handleError]);

  // Validation operations
  const validateInheritance = useCallback(async (contextId: string, level: string) => {
    setLoading('validation', true);
    clearError('validation');

    try {
      const result = await mcpApi.validateContextInheritance(level, contextId);

      if (result.success && result.data) {
        const validation: ContextInheritanceValidation = result.data as any;
        setState(prev => ({
          ...prev,
          validationResults: {
            ...prev.validationResults,
            [contextId]: validation
          }
        }));
      } else {
        throw new Error(result.error || 'Failed to validate inheritance');
      }
    } catch (error) {
      handleError('validation', error);
      throw error;
    } finally {
      setLoading('validation', false);
    }
  }, [setLoading, clearError, handleError]);

  const repairInheritance = useCallback(async (contextId: string, level: string) => {
    // Mock implementation - in real API, this would trigger repair operations
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await validateInheritance(contextId, level);
    } catch (error) {
      handleError('validation', error);
      throw error;
    }
  }, [validateInheritance, handleError]);

  const optimizePerformance = useCallback(async (contextId: string) => {
    // Mock implementation - in real API, this would trigger optimization
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      cacheRef.current.clear(); // Clear cache as part of optimization
    } catch (error) {
      handleError('validation', error);
      throw error;
    }
  }, [handleError]);

  const clearCache = useCallback(async (contextId: string) => {
    cacheRef.current.clear();
    if (state.selectedContext) {
      await refreshContext(contextId);
    }
  }, [state.selectedContext, refreshContext]);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh && state.selectedContext) {
      refreshIntervalRef.current = setInterval(() => {
        refreshContext(state.selectedContext!.context_id);
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, state.selectedContext, refreshContext]);

  // Initialize data on mount
  useEffect(() => {
    if (taskId) {
      resolveContext(taskId, 'task');
    }
    refreshDelegationQueue();
  }, [taskId, resolveContext, refreshDelegationQueue]);

  return {
    state,
    actions: {
      updateContext,
      resolveContext,
      refreshContext,
      delegateContext,
      previewDelegation,
      approveDelegation,
      rejectDelegation,
      refreshDelegationQueue,
      addInsight,
      updateInsight,
      deleteInsight,
      refreshInsights,
      addProgress,
      updateNextSteps,
      validateInheritance,
      repairInheritance,
      optimizePerformance,
      clearCache
    }
  };
}