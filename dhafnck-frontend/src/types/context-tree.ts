/**
 * TypeScript interfaces for the hierarchical context tree component
 * Supports Global → Project → Task hierarchy with inheritance and delegation
 */

// Core Context Types
export interface HierarchicalContext {
  context_id: string;
  level: 'global' | 'project' | 'task';
  data: ContextData;
  metadata: ContextMetadata;
  resolved_data?: ResolvedContextData;
  parent_context_id?: string;
  children?: HierarchicalContext[];
}

export interface ContextData {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  assignees?: string[];
  labels?: string[];
  estimated_effort?: string;
  due_date?: string;
  [key: string]: any;
}

export interface ContextMetadata {
  created_at: string;
  updated_at: string;
  user_id: string;
  project_id?: string;
  git_branch_name?: string;
  version?: number;
}

export interface ResolvedContextData {
  resolved_at: string;
  inheritance_chain: string[];
  final_properties: Record<string, any>;
  conflicts?: ContextConflict[];
  dependency_hash: string;
  cache_status: 'hit' | 'miss' | 'stale';
}

// Health and Status Types
export interface ContextHealthStatus {
  status: 'healthy' | 'warning' | 'error' | 'stale';
  issues: ContextIssue[];
  score: number;
  last_validated: string;
  validation_details?: ValidationDetails;
}

export interface ContextIssue {
  type: 'error' | 'warning' | 'info';
  message: string;
  field?: string;
  code?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface ValidationDetails {
  inheritance_chain_valid: boolean;
  cache_consistency: boolean;
  resolution_timing: {
    total_ms: number;
    cache_lookup_ms: number;
    inheritance_resolution_ms: number;
  };
  dependency_hash_match: boolean;
}

// Tree Structure Types
export interface TreeNode {
  id: string;
  context: HierarchicalContext;
  level: 'global' | 'project' | 'task';
  children: TreeNode[];
  parent?: TreeNode;
  depth: number;
  path: string[];
}

export interface InheritancePath {
  path: HierarchicalContext[];
  resolved: boolean;
  conflicts: ContextConflict[];
  total_resolution_time?: number;
}

export interface ContextConflict {
  field: string;
  task_value: any;
  project_value?: any;
  global_value?: any;
  resolution_strategy: 'task_wins' | 'project_wins' | 'global_wins' | 'merge';
  conflict_type: 'value_mismatch' | 'type_mismatch' | 'missing_parent';
}

// Component Props
export interface ContextTreeProps {
  contexts: HierarchicalContext[];
  selectedContext: string | null;
  onContextSelect: (contextId: string, level: string) => void;
  onResolveContext: (contextId: string, level: string) => Promise<void>;
  onDelegate: (fromContext: string, toLevel: 'project' | 'global', data: any) => Promise<void>;
  onValidateInheritance: (contextId: string, level: string) => Promise<void>;
  className?: string;
  showHealthIndicators?: boolean;
  enableDragDrop?: boolean;
  enableSearch?: boolean;
}

export interface ContextNodeProps {
  context: HierarchicalContext;
  level: 'global' | 'project' | 'task';
  isSelected: boolean;
  isExpanded: boolean;
  children?: HierarchicalContext[];
  healthStatus: ContextHealthStatus;
  onSelect: () => void;
  onToggleExpand: () => void;
  onDelegate: (data: any) => Promise<void>;
  onValidate: () => Promise<void>;
  onResolve: () => Promise<void>;
  dragHandle?: React.RefObject<HTMLDivElement>;
  className?: string;
}

// Search and Filter Types
export interface ContextSearchFilters {
  searchTerm: string;
  level: 'all' | 'global' | 'project' | 'task';
  health: 'all' | 'healthy' | 'warning' | 'error' | 'stale';
  hasIssues: boolean;
  status: string[];
  priority: string[];
  assignees: string[];
  labels: string[];
}

export interface SearchResult {
  context: HierarchicalContext;
  matches: SearchMatch[];
  score: number;
}

export interface SearchMatch {
  field: string;
  value: string;
  highlight: string;
  path: string[];
}

// Delegation Types
export interface DelegationRequest {
  source_context_id: string;
  source_level: 'task' | 'project';
  target_level: 'project' | 'global';
  delegation_data: {
    pattern_name: string;
    pattern_type: string;
    implementation: any;
    usage_guide: string;
  };
  delegation_reason: string;
}

export interface DelegationQueueItem {
  delegation_id: string;
  source_context: string;
  target_level: 'project' | 'global';
  data: any;
  created_at: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
}

// State Management Types
export interface ContextTreeState {
  contexts: HierarchicalContext[];
  selectedContext: string | null;
  expandedNodes: Set<string>;
  healthStatuses: Record<string, ContextHealthStatus>;
  searchFilters: ContextSearchFilters;
  filteredContexts: HierarchicalContext[];
  loading: boolean;
  error: string | null;
  treeStructure: TreeNode[];
  delegationQueue: DelegationQueueItem[];
}

export interface ContextTreeActions {
  resolveContext: (contextId: string, level: string) => Promise<void>;
  validateInheritance: (contextId: string, level: string) => Promise<void>;
  selectContext: (contextId: string) => void;
  toggleExpanded: (contextId: string) => void;
  updateSearchFilters: (filters: Partial<ContextSearchFilters>) => void;
  delegate: (delegation: DelegationRequest) => Promise<void>;
  refreshHealth: (contextId?: string) => Promise<void>;
  refreshAll: () => Promise<void>;
}

// Style Configuration Types
export interface TreeStyleConfig {
  container: string;
  globalNode: string;
  projectNode: string;
  taskNode: string;
  healthStatus: {
    healthy: string;
    warning: string;
    error: string;
    stale: string;
  };
  connectionLine: string;
  inheritanceLine: string;
  dragHandle: string;
  expandButton: string;
  actionButton: string;
  searchContainer: string;
  filterControls: string;
}

// Performance and Analytics Types
export interface TreePerformanceMetrics {
  render_time_ms: number;
  node_count: number;
  depth: number;
  expanded_nodes: number;
  health_checks_pending: number;
  memory_usage_mb?: number;
}

export interface ContextAnalytics {
  total_contexts: number;
  contexts_by_level: Record<string, number>;
  health_distribution: Record<string, number>;
  inheritance_depth_avg: number;
  resolution_time_avg: number;
  conflicts_count: number;
  delegation_requests: number;
}

// Event Types
export interface ContextTreeEvent {
  type: 'context_selected' | 'context_expanded' | 'context_resolved' | 'delegation_initiated' | 'health_updated';
  contextId: string;
  level?: string;
  data?: any;
  timestamp: number;
}

// Error Types
export interface ContextTreeError {
  code: string;
  message: string;
  context_id?: string;
  level?: string;
  operation: string;
  details?: any;
  timestamp: number;
}

// Utility Types
export type ContextLevel = 'global' | 'project' | 'task';
export type HealthStatusType = 'healthy' | 'warning' | 'error' | 'stale';
export type ConflictResolutionStrategy = 'task_wins' | 'project_wins' | 'global_wins' | 'merge';
export type DragDropOperation = 'delegate_to_project' | 'delegate_to_global' | 'reorder_children';

// API Response Types
export interface ContextTreeApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: {
    requestId: string;
    responseTime: number;
    operation: string;
  };
}

export interface ResolveContextResponse {
  resolved_context: HierarchicalContext;
  inheritance_chain: HierarchicalContext[];
  resolution_metadata: {
    resolved_at: string;
    dependency_hash: string;
    cache_status: 'hit' | 'miss';
    resolution_timing: ValidationDetails['resolution_timing'];
  };
}

export interface ValidateInheritanceResponse {
  validation: {
    valid: boolean;
    errors: string[];
    warnings: string[];
    inheritance_chain: string[];
    resolution_path: HierarchicalContext[];
    cache_metrics: {
      hit_ratio: number;
      miss_ratio: number;
      entries: number;
    };
    resolution_timing: ValidationDetails['resolution_timing'];
  };
  resolution_metadata: {
    resolved_at: string;
    dependency_hash: string;
    cache_status: 'hit' | 'miss';
  };
}