/**
 * Modern MCP API - All 23 Tools with Enhanced Features
 * 
 * Production-ready API wrapper with circuit breaker, retry logic,
 * performance monitoring, and comprehensive error handling.
 */

// Core API Wrapper
export { 
  McpApiWrapper, 
  McpApiError
} from './enhanced';

export { mcpApi } from './enhanced';

// Type Definitions
export type {
  McpResponse,
  RequestOptions,
  PerformanceMetrics,
  Agent,
  AgentCallResponse,
  HierarchicalContext,
  ContextInheritanceValidation,
  ConnectionStatus,
  ComplianceStatus,
  ComplianceViolation,
  Task,
  Subtask,
  Project,
  Branch,
  Rule,
  // Parameter types
  AgentParams,
  ContextParams,
  HierarchicalParams,
  DelegationParams,
  ComplianceParams,
  ConnectionParams,
  RuleParams,
  ProjectParams,
  BranchParams,
  TaskParams,
  SubtaskParams
} from './enhanced';

// Usage Examples
export * as examples from './examples';

// Import for default export
import { mcpApi } from './enhanced';

// Default export - Ready-to-use API instance
export default mcpApi;