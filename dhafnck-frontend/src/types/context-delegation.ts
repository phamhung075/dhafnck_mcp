/**
 * TypeScript interfaces for Context Delegation & Management components
 * Extends the context-tree.ts types for Prompt 3B implementation
 */

import { HierarchicalContext, ContextData, ContextMetadata } from './context-tree';

// Re-export for convenience
export type { ContextData, ContextMetadata, HierarchicalContext } from './context-tree';

// Additional Context Types for Delegation
export interface ResolvedContext {
  context: HierarchicalContext;
  inheritance_chain: InheritanceChainItem[];
  resolved_data: Record<string, any>;
  conflicts: ContextConflict[];
  resolution_metadata: {
    resolved_at: string;
    dependency_hash: string;
    cache_status: 'hit' | 'miss' | 'stale';
    resolution_timing: {
      total_ms: number;
      cache_lookup_ms: number;
      inheritance_resolution_ms: number;
    };
  };
}

export interface InheritanceChainItem {
  level: 'global' | 'project' | 'task';
  context_id: string;
  data: ContextData;
  effective_properties: string[];
  overridden_properties: string[];
}

export interface ContextConflict {
  field: string;
  task_value: any;
  project_value?: any;
  global_value?: any;
  resolution_strategy: 'task_wins' | 'project_wins' | 'global_wins' | 'merge';
  conflict_type: 'value_mismatch' | 'type_mismatch' | 'missing_parent';
}

// Context Insights
export interface ContextInsight {
  id: string;
  content: string;
  category: 'technical' | 'business' | 'risk' | 'optimization' | 'discovery';
  importance: 'low' | 'medium' | 'high';
  created_at: string;
  created_by: string;
  tags: string[];
  metadata?: Record<string, any>;
}

// Context Progress
export interface ContextProgress {
  id: string;
  content: string;
  progress_percentage?: number;
  milestone?: string;
  created_at: string;
  created_by: string;
  related_tasks?: string[];
}

// Delegation Types
export interface DelegationRequest {
  source_context_id: string;
  source_level: 'task' | 'project';
  target_level: 'project' | 'global';
  delegation_data: {
    pattern_name: string;
    pattern_type: 'reusable_component' | 'best_practice' | 'configuration' | 'workflow';
    implementation: any;
    usage_guide: string;
    tags: string[];
    category?: string;
  };
  delegation_reason: string;
}

export interface DelegationPreview {
  estimated_impact: 'low' | 'medium' | 'high';
  affected_contexts: string[];
  potential_conflicts: string[];
  recommendations: string[];
  approval_likelihood: number; // 0-1
}

export interface PendingDelegation {
  delegation_id: string;
  source_context: string;
  source_level: 'task' | 'project';
  target_level: 'project' | 'global';
  delegation_data: any;
  delegation_reason: string;
  created_at: string;
  created_by: string;
  status: 'pending' | 'approved' | 'rejected';
  priority?: 'low' | 'medium' | 'high';
  review_notes?: string;
}

export interface DelegationHistoryItem {
  delegation_id: string;
  action: 'created' | 'approved' | 'rejected' | 'modified';
  timestamp: string;
  user_id: string;
  details: string;
  metadata?: Record<string, any>;
}

export interface DelegationTarget {
  level: 'project' | 'global';
  context_id: string;
  display_name: string;
  description?: string;
  permissions: string[];
}

// Pattern Management
export interface DelegationPattern {
  type: 'reusable_component' | 'best_practice' | 'configuration' | 'workflow';
  name: string;
  description: string;
  template?: any;
  required_fields: string[];
  optional_fields: string[];
  validation_rules?: ValidationRule[];
}

export interface ValidationRule {
  field: string;
  rule: 'required' | 'min_length' | 'max_length' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

// Context Inheritance Validation
export interface ContextInheritanceValidation {
  valid: boolean;
  errors: ValidationError[];
  warnings: string[];
  inheritance_chain: string[];
  resolution_path: HierarchicalContext[];
  cache_metrics: {
    hit_ratio: number;
    miss_ratio: number;
    entries: number;
    total_size_mb?: number;
  };
  resolution_timing: {
    total_ms: number;
    cache_lookup_ms: number;
    inheritance_resolution_ms: number;
  };
  performance_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  optimization_suggestions: string[];
}

export interface ValidationError {
  code: string;
  message: string;
  field?: string;
  severity: 'error' | 'warning' | 'info';
  suggestion?: string;
}

// Component Props Interfaces

export interface ContextDetailsPanelProps {
  context: HierarchicalContext | null;
  resolvedContext: ResolvedContext | null;
  inheritanceChain: InheritanceChainItem[];
  onUpdateContext: (contextId: string, updates: Partial<ContextData>) => Promise<void>;
  onAddInsight: (contextId: string, insight: ContextInsight) => Promise<void>;
  onAddProgress: (contextId: string, progress: ContextProgress) => Promise<void>;
  onUpdateNextSteps: (contextId: string, steps: string[]) => Promise<void>;
  onForceRefresh: () => Promise<void>;
  className?: string;
}

export interface ContextDataEditorProps {
  contextData: ContextData;
  onChange: (updates: Partial<ContextData>) => void;
  onSave: () => Promise<void>;
  readOnly?: boolean;
  showHistory?: boolean;
  validationErrors?: ValidationError[];
}

export interface ContextDelegationWorkflowProps {
  sourceContext: HierarchicalContext;
  availableTargets: DelegationTarget[];
  onDelegate: (delegation: DelegationRequest) => Promise<void>;
  onPreviewDelegation: (delegation: DelegationRequest) => Promise<DelegationPreview>;
  delegationHistory: DelegationHistoryItem[];
  availablePatterns: DelegationPattern[];
}

export interface DelegationQueueViewerProps {
  pendingDelegations: PendingDelegation[];
  onApproveDelegation: (delegationId: string) => Promise<void>;
  onRejectDelegation: (delegationId: string, reason: string) => Promise<void>;
  onViewDelegationDetails: (delegationId: string) => void;
  userRole: 'admin' | 'reviewer' | 'contributor';
  queueStats?: {
    total_pending: number;
    average_approval_time: number;
    rejection_rate: number;
  };
}

export interface ContextInheritanceDebuggerProps {
  contextId: string;
  level: 'project' | 'task';
  validationResult: ContextInheritanceValidation | null;
  onValidate: (contextId: string, level: string) => Promise<void>;
  onRepairInheritance: (contextId: string, level: string) => Promise<void>;
  onOptimizePerformance: (contextId: string) => Promise<void>;
  onClearCache: (contextId: string) => Promise<void>;
}

export interface ContextInsightsManagerProps {
  insights: ContextInsight[];
  onAddInsight: (insight: Omit<ContextInsight, 'id' | 'created_at'>) => Promise<void>;
  onUpdateInsight: (insightId: string, updates: Partial<ContextInsight>) => Promise<void>;
  onDeleteInsight: (insightId: string) => Promise<void>;
  onFilterInsights: (filters: InsightFilters) => void;
  contextId: string;
  readOnly?: boolean;
}

export interface InsightFilters {
  category?: 'technical' | 'business' | 'risk' | 'optimization' | 'discovery';
  importance?: 'low' | 'medium' | 'high';
  tags?: string[];
  searchTerm?: string;
  dateRange?: {
    from: string;
    to: string;
  };
}

// State Management
export interface ContextManagementState {
  selectedContext: HierarchicalContext | null;
  resolvedContext: ResolvedContext | null;
  inheritanceChain: InheritanceChainItem[];
  validationResults: Record<string, ContextInheritanceValidation>;
  delegationQueue: PendingDelegation[];
  delegationHistory: DelegationHistoryItem[];
  insights: Record<string, ContextInsight[]>;
  progress: Record<string, ContextProgress[]>;
  availablePatterns: DelegationPattern[];
  availableTargets: DelegationTarget[];
  editMode: boolean;
  unsavedChanges: boolean;
  loading: {
    context: boolean;
    delegation: boolean;
    validation: boolean;
    insights: boolean;
  };
  errors: {
    context?: string;
    delegation?: string;
    validation?: string;
    insights?: string;
  };
}

// Hook Interface
export interface UseContextManagementReturn {
  state: ContextManagementState;
  actions: {
    // Context operations
    updateContext: (contextId: string, updates: Partial<ContextData>) => Promise<void>;
    resolveContext: (contextId: string, level: string, forceRefresh?: boolean) => Promise<void>;
    refreshContext: (contextId: string) => Promise<void>;
    
    // Delegation operations
    delegateContext: (delegation: DelegationRequest) => Promise<void>;
    previewDelegation: (delegation: DelegationRequest) => Promise<DelegationPreview>;
    approveDelegation: (delegationId: string) => Promise<void>;
    rejectDelegation: (delegationId: string, reason: string) => Promise<void>;
    refreshDelegationQueue: () => Promise<void>;
    
    // Insight operations
    addInsight: (contextId: string, insight: ContextInsight) => Promise<void>;
    updateInsight: (contextId: string, insightId: string, updates: Partial<ContextInsight>) => Promise<void>;
    deleteInsight: (contextId: string, insightId: string) => Promise<void>;
    refreshInsights: (contextId: string) => Promise<void>;
    
    // Progress operations
    addProgress: (contextId: string, progress: ContextProgress) => Promise<void>;
    updateNextSteps: (contextId: string, steps: string[]) => Promise<void>;
    
    // Validation operations
    validateInheritance: (contextId: string, level: string) => Promise<void>;
    repairInheritance: (contextId: string, level: string) => Promise<void>;
    optimizePerformance: (contextId: string) => Promise<void>;
    clearCache: (contextId: string) => Promise<void>;
  };
}

// API Response Types
export interface ContextManagementApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: {
    requestId: string;
    responseTime: number;
    operation: string;
  };
}

// Tab Types for ContextDetailsPanel
export type ContextDetailTab = 'overview' | 'data' | 'inheritance' | 'insights' | 'progress' | 'next-steps';

// Delegation Workflow Steps
export type DelegationStep = 'pattern-selection' | 'target-selection' | 'configuration' | 'preview' | 'submission';

// Theme Support
export interface ContextManagementTheme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
}