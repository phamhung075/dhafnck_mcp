// Application-wide types for system integration

export type ViewType = 
  | 'dashboard'
  | 'projects'
  | 'agents'
  | 'contexts'
  | 'monitoring'
  | 'health'
  | 'compliance'
  | 'connections'
  | 'tasks'
  | 'rules';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  notifications: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  sidebarCollapsed: boolean;
  defaultView: ViewType;
}

export interface Agent {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'error';
  project_id: string;
  description?: string;
  capabilities?: string[];
  last_activity?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'archived';
  created_at: string;
  updated_at: string;
  health_score?: number;
  task_count?: number;
  branch_count?: number;
}

export interface GitBranch {
  id: string;
  git_branch_name: string;
  git_branch_description?: string;
  project_id: string;
  status: 'active' | 'archived';
  created_at: string;
  task_count?: number;
  assigned_agents?: Agent[];
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'blocked' | 'review' | 'testing' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent' | 'critical';
  assignees?: string[];
  labels?: string[];
  git_branch_id: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
  estimated_effort?: string;
  completion_summary?: string;
  testing_notes?: string;
}

export interface HierarchicalContext {
  id: string;
  level: 'global' | 'project' | 'task';
  context_id: string;
  data: Record<string, any>;
  metadata: {
    created_at: string;
    updated_at: string;
    dependency_hash: string;
  };
  inheritance_chain?: string[];
}

export interface Rule {
  id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SystemHealthStatus {
  overall_score: number;
  components: {
    database: { status: 'healthy' | 'degraded' | 'critical'; score: number };
    mcp_server: { status: 'healthy' | 'degraded' | 'critical'; score: number };
    authentication: { status: 'healthy' | 'degraded' | 'critical'; score: number };
    context_system: { status: 'healthy' | 'degraded' | 'critical'; score: number };
  };
  last_check: string;
  uptime: string;
}

export interface ComplianceStatus {
  overall_score: number;
  compliance_rate: number;
  total_operations: number;
  violations: number;
  policies: {
    security: { score: number; violations: number };
    data_protection: { score: number; violations: number };
    access_control: { score: number; violations: number };
  };
  last_audit: string;
}

export interface ConnectionStatus {
  status: 'healthy' | 'degraded' | 'critical' | 'unknown';
  latency: number;
  uptime_percentage: number;
  active_connections: number;
  last_check: string;
  error_rate: number;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

export interface UINotification extends Notification {
  autoClose?: boolean;
  duration?: number;
}

export interface Modal {
  id: string;
  type: 'dialog' | 'drawer' | 'fullscreen';
  title: string;
  content: React.ReactNode;
  actions?: Array<{
    label: string;
    variant: 'primary' | 'secondary' | 'danger';
    action: () => void;
  }>;
  onClose?: () => void;
}

export interface ActivityItem {
  id: string;
  type: 'agent_switch' | 'project_select' | 'branch_select' | 'task_update' | 'system_action';
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string;
}

export interface TaskUpdate {
  taskId: string;
  branchId: string;
  updates: Partial<Task>;
}

export interface AgentStatusUpdate {
  agentId: string;
  status: Agent['status'];
  project_id: string;
  last_activity: string;
}

export interface WebSocketMessage {
  type: 'system_health_update' | 'compliance_update' | 'task_update' | 'agent_status_update' | 'notification';
  data: any;
  timestamp: string;
}

export interface CreateProjectData {
  name: string;
  description?: string;
  initial_agents?: string[];
}

export interface ApiRequest {
  toolName: string;
  arguments: Record<string, any>;
  options?: RequestOptions;
}

export interface RequestOptions {
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

export interface PerformanceMetrics {
  requestCount: number;
  successCount: number;
  errorCount: number;
  averageResponseTime: number;
  queueLength: number;
  memoryUsage?: number;
}