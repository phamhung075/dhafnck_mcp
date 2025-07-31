# Hierarchical Context System

## Overview

The DhafnckMCP Hierarchical Context System provides a 4-tier inheritance structure that enables intelligent context sharing, pattern delegation, and organizational learning across the platform.

## Architecture

### 4-Tier Hierarchy
```
GLOBAL (Singleton: 'global_singleton')
   ↓ inherits to
PROJECT (ID: project_id)  
   ↓ inherits to
BRANCH (ID: git_branch_id)
   ↓ inherits to
TASK (ID: task_id)
```

### Context Inheritance Flow
Lower levels automatically inherit properties from higher levels, with more specific values taking precedence:
```
Final Context = Task Data + Branch Data + Project Data + Global Data
(Most specific)                                         (Most general)
```

## Core Components

### HierarchicalContextService
**Purpose**: Manages context CRUD operations at all hierarchy levels

```python
class HierarchicalContextService:
    async def create_context(
        self, 
        level: ContextLevel, 
        context_id: str, 
        data: ContextData
    ) -> ContextResponse:
        # Create context at specified level
        # Validate hierarchy constraints
        # Initialize with defaults
```

### ContextInheritanceService
**Purpose**: Resolves context inheritance chains

```python
class ContextInheritanceService:
    async def resolve_context(
        self, 
        level: ContextLevel, 
        context_id: str,
        force_refresh: bool = False
    ) -> ResolvedContext:
        # Build inheritance chain: task → branch → project → global
        # Merge context data with precedence rules
        # Cache resolved context for performance
```

### ContextDelegationService
**Purpose**: Manages pattern sharing between hierarchy levels

```python
class ContextDelegationService:
    async def delegate_context(
        self,
        source_level: ContextLevel,
        source_id: str,
        target_level: ContextLevel,
        delegate_data: Dict[str, Any],
        delegation_reason: str
    ) -> DelegationResponse:
        # Queue delegation for approval (if required)
        # Apply delegation to target level
        # Invalidate dependent caches
```

### ContextCacheService
**Purpose**: Performance optimization with dependency tracking

```python
class ContextCacheService:
    def get_cached_context(
        self, 
        cache_key: str
    ) -> Optional[ResolvedContext]:
        # LRU cache with dependency tracking
        # Automatic invalidation on changes
        # Performance metrics collection
```

## Context Data Structure

### ContextData Schema
```python
@dataclass
class ContextData:
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    estimated_effort: Optional[str] = None
    due_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    insights: Optional[List[Dict[str, Any]]] = None
    progress: Optional[List[Dict[str, Any]]] = None
    next_steps: Optional[List[str]] = None
```

### ResolvedContext Structure
```python
@dataclass
class ResolvedContext:
    context_id: str
    level: ContextLevel
    data: ContextData
    inheritance_chain: List[str]
    dependency_hash: str
    resolved_at: datetime
    cache_status: str
```

## Usage Patterns

### 1. Context Resolution (Read Operations)
```python
# Resolve task context with full inheritance
context = await hierarchical_context_facade.resolve_context(
    level="task",
    context_id="task-uuid-123",
    force_refresh=False
)

# Access inherited data
title = context.data.title  # May come from task, branch, project, or global
assignees = context.data.assignees  # Merged from all levels
```

### 2. Context Updates (Write Operations)
```python
# Update task context
await hierarchical_context_facade.update_context(
    level="task",
    context_id="task-uuid-123",
    data={
        "status": "in_progress",
        "progress": ["Started implementation"],
        "discoveries": ["Found existing utility function"]
    },
    propagate_changes=True
)
```

### 3. Context Delegation (Pattern Sharing)
```python
# Delegate reusable pattern to project level
await hierarchical_context_facade.delegate_context(
    level="task",
    context_id="task-uuid-123",
    delegate_to="project",
    delegate_data={
        "authentication_pattern": {
            "implementation": auth_code_template,
            "usage_guide": "When implementing JWT auth",
            "best_practices": ["Use secure cookies", "Implement refresh tokens"]
        }
    },
    delegation_reason="Reusable authentication implementation"
)
```

## Hierarchy Level Details

### Global Context ('global_singleton')
**Purpose**: Organization-wide patterns and standards
- **Content**: Company coding standards, security policies, architecture patterns
- **Inheritance**: Root level - inherits from no other level
- **Delegation Target**: Receives critical patterns that benefit entire organization

**Example Global Context**:
```json
{
  "coding_standards": {
    "python": {
      "formatter": "black",
      "linter": "ruff",
      "type_checking": "mypy"
    }
  },
  "security_policies": {
    "authentication": "JWT with refresh tokens",
    "authorization": "RBAC with minimum permissions"
  },
  "architecture_patterns": {
    "api_design": "RESTful with OpenAPI",
    "database": "Repository pattern with SQLAlchemy"
  }
}
```

### Project Context (project_id)
**Purpose**: Project-specific configuration and team patterns
- **Content**: Team conventions, project architecture, shared utilities
- **Inheritance**: Inherits from Global context
- **Delegation Target**: Receives patterns useful across project features

**Example Project Context**:
```json
{
  "team_conventions": {
    "git_workflow": "GitFlow with feature branches",
    "code_review": "Minimum 2 approvals for main",
    "testing": "TDD with 90% coverage requirement"
  },
  "project_architecture": {
    "frontend": "Next.js with TypeScript",
    "backend": "FastAPI with async/await",
    "database": "PostgreSQL with SQLAlchemy ORM"
  },
  "shared_utilities": {
    "authentication": "utils/auth.py",
    "database": "utils/db.py",
    "testing": "tests/conftest.py"
  }
}
```

### Branch Context (git_branch_id)
**Purpose**: Feature or work branch specific context
- **Content**: Feature requirements, implementation decisions, branch-specific configurations
- **Inheritance**: Inherits from Project → Global contexts
- **Delegation Target**: Receives patterns specific to feature development

**Example Branch Context**:
```json
{
  "feature_requirements": {
    "user_authentication": {
      "login_methods": ["email", "oauth"],
      "session_management": "JWT with Redis",
      "security_requirements": ["2FA optional", "password complexity"]
    }
  },
  "implementation_decisions": {
    "oauth_provider": "Auth0",
    "session_storage": "Redis with TTL",
    "password_hashing": "bcrypt with salt"
  },
  "branch_config": {
    "testing_database": "test_auth_db",
    "feature_flags": ["auth_v2_enabled"],
    "integration_endpoints": ["auth0_test_env"]
  }
}
```

### Task Context (task_id)
**Purpose**: Specific work unit context and progress
- **Content**: Task progress, discoveries, implementation details, blockers
- **Inheritance**: Inherits from Branch → Project → Global contexts
- **Delegation Source**: Delegates useful patterns to higher levels

**Example Task Context**:
```json
{
  "task_progress": {
    "completed_steps": ["API design", "database schema"],
    "current_step": "Implementation",
    "remaining_steps": ["Testing", "Documentation"]
  },
  "discoveries": [
    "Found existing rate limiting utility",
    "Auth0 SDK has built-in refresh token handling",
    "Redis client pool already configured"
  ],
  "implementation_details": {
    "files_modified": ["auth/routes.py", "auth/models.py"],
    "new_dependencies": ["auth0-python"],
    "configuration_changes": ["redis_config.py"]
  },
  "blockers": [],
  "insights": [
    {
      "category": "performance",
      "content": "Redis connection pooling improves response time by 40%",
      "impact": "Apply to all caching operations"
    }
  ]
}
```

## Context Inheritance Rules

### Precedence Order
1. **Task Level**: Most specific, highest precedence
2. **Branch Level**: Feature-specific overrides
3. **Project Level**: Team and project defaults
4. **Global Level**: Organization-wide standards, lowest precedence

### Merge Strategy
```python
def merge_contexts(task_data, branch_data, project_data, global_data):
    """Merge context data with precedence rules"""
    
    # Start with global defaults
    merged = copy.deepcopy(global_data)
    
    # Apply project overrides
    merged = deep_merge(merged, project_data)
    
    # Apply branch-specific settings
    merged = deep_merge(merged, branch_data)
    
    # Apply task-specific values (highest precedence)
    merged = deep_merge(merged, task_data)
    
    return merged
```

### Special Merge Rules
- **Lists**: Concatenated (global + project + branch + task)
- **Dictionaries**: Deep merged with child precedence
- **Primitive Values**: Child value completely overrides parent
- **Null Values**: Parent value used if child is null

## Delegation Workflow

### Automatic Delegation Triggers
```python
DELEGATION_RULES = {
    "reusable_pattern": "delegate_to_project",      # Patterns useful across tasks
    "organization_standard": "delegate_to_global",   # Company-wide best practices
    "feature_specific": "delegate_to_branch",        # Feature-specific patterns
    "task_specific": "no_delegation",                # Keep at task level
}
```

### Manual Delegation Process
1. **Queue Request**: Delegation request added to review queue
2. **Manual Review**: Administrator reviews delegation appropriateness
3. **Approval/Rejection**: Decision with optional reason
4. **Application**: Approved delegations applied to target level
5. **Cache Invalidation**: Dependent contexts refreshed

### Delegation Best Practices
```python
# Good delegation candidates
DELEGATE_TO_PROJECT = [
    "authentication_patterns",
    "database_connection_utilities", 
    "error_handling_templates",
    "testing_frameworks_setup"
]

DELEGATE_TO_GLOBAL = [
    "security_compliance_patterns",
    "coding_style_guidelines",
    "architecture_decision_templates",
    "deployment_configuration_patterns"
]

# Poor delegation candidates (keep at task level)
KEEP_AT_TASK = [
    "specific_bug_fixes",
    "feature_implementation_details",
    "temporary_debugging_code",
    "task_specific_progress_notes"
]
```

## Performance Optimization

### Caching Strategy
```python
class ContextCacheService:
    def __init__(self):
        self._cache = LRUCache(maxsize=1000)
        self._dependency_tracker = DependencyTracker()
    
    def cache_context(self, context: ResolvedContext):
        """Cache with dependency tracking"""
        cache_key = f"{context.level}:{context.context_id}"
        
        # Track dependencies
        self._dependency_tracker.add_dependency(
            cache_key, 
            context.inheritance_chain
        )
        
        # Store in cache
        self._cache[cache_key] = context
    
    def invalidate_dependents(self, changed_context_id: str):
        """Invalidate all contexts that depend on changed context"""
        dependents = self._dependency_tracker.get_dependents(changed_context_id)
        for dependent_key in dependents:
            self._cache.pop(dependent_key, None)
```

### Cache Invalidation Rules
- **Task Update**: Invalidates only task cache
- **Branch Update**: Invalidates branch + all dependent tasks
- **Project Update**: Invalidates project + all dependent branches and tasks
- **Global Update**: Invalidates entire cache (rare operation)

## Error Handling

### Context Resolution Errors
```python
class ContextResolutionError(Exception):
    """Raised when context resolution fails"""
    
class MissingParentContextError(ContextResolutionError):
    """Raised when required parent context doesn't exist"""
    
class CircularDependencyError(ContextResolutionError):
    """Raised when circular dependency detected in inheritance chain"""
```

### Error Recovery Strategies
1. **Missing Parent**: Create default parent context
2. **Circular Dependency**: Break cycle and log warning
3. **Cache Miss**: Rebuild from source data
4. **Invalid Data**: Use schema defaults with validation warnings

## Monitoring and Diagnostics

### Health Metrics
```python
class ContextSystemMetrics:
    cache_hit_ratio: float
    cache_miss_ratio: float
    average_resolution_time: float
    inheritance_chain_depth: Dict[str, int]
    delegation_queue_size: int
    error_rate: float
```

### Diagnostic Tools
```python
# Validate inheritance chain
await validate_context_inheritance(level="task", context_id="task-123")

# Check cache status
cache_status = await get_cache_status()

# Analyze delegation queue
queue_status = await get_delegation_queue_status()
```

## Best Practices

### 1. Context Design
- **Keep data structures consistent** across hierarchy levels
- **Use meaningful naming** for delegated patterns
- **Document context schemas** for team understanding
- **Validate data types** at each level

### 2. Inheritance Strategy
- **Design for inheritance** - consider how data flows down
- **Use specific overrides** rather than complete replacements
- **Document inheritance behavior** for complex patterns
- **Test inheritance chains** with realistic data

### 3. Delegation Guidelines
- **Delegate reusable patterns** that benefit multiple contexts
- **Avoid over-delegation** of task-specific details
- **Use clear delegation reasons** for review process
- **Monitor delegation effectiveness** through usage metrics

### 4. Performance Optimization
- **Cache frequently accessed** contexts
- **Use force_refresh sparingly** to maintain performance
- **Monitor cache hit ratios** and adjust cache size
- **Profile resolution times** for optimization opportunities

## MCP Tool Usage

### Using manage_context Tool

The `manage_context` tool provides a unified interface for all hierarchical context operations. 

> **Note**: The system previously used `manage_hierarchical_context` which is now deprecated. The current `manage_context` tool internally uses the hierarchical system and provides full backward compatibility while offering a simpler interface.

```python
# Create context at any level
mcp__dhafnck_mcp_http__manage_context(
    action="create",
    level="task",  # or "project", "branch", "global"
    context_id="task-123",
    data={
        "title": "Implement authentication",
        "status": "in_progress",
        "priority": "high"
    }
)

# Get context with inheritance
mcp__dhafnck_mcp_http__manage_context(
    action="get",
    level="task",
    context_id="task-123",
    include_inherited=True  # Include data from parent contexts
)

# Update context
mcp__dhafnck_mcp_http__manage_context(
    action="update",
    level="task",
    context_id="task-123",
    data={
        "status": "completed",
        "progress": 100,
        "completion_summary": "JWT authentication implemented with refresh tokens"
    },
    propagate_changes=True  # Update dependent contexts
)

# Resolve full inheritance chain
mcp__dhafnck_mcp_http__manage_context(
    action="resolve",
    level="task",
    context_id="task-123",
    force_refresh=False  # Use cache if available
)

# Delegate pattern to higher level
mcp__dhafnck_mcp_http__manage_context(
    action="delegate",
    level="task",
    context_id="task-123",
    delegate_to="project",  # Target level: "global", "project", or "branch"
    delegate_data={
        "jwt_auth_pattern": {
            "implementation": "auth_code_template",
            "usage": "Reusable JWT authentication pattern"
        }
    },
    delegation_reason="Reusable authentication pattern for all project features"
)

# Add insight to context
mcp__dhafnck_mcp_http__manage_context(
    action="add_insight",
    level="task",
    context_id="task-123",
    content="Redis session caching improved response time by 40%",
    category="performance",
    importance="high"
)

# Add progress update
mcp__dhafnck_mcp_http__manage_context(
    action="add_progress",
    level="task",
    context_id="task-123",
    content="Completed JWT token generation and validation",
    agent="@coding_agent"
)

# List contexts at a level
mcp__dhafnck_mcp_http__manage_context(
    action="list",
    level="task",
    filters={
        "status": "in_progress",
        "priority": "high"
    }
)

# Delete context
mcp__dhafnck_mcp_http__manage_context(
    action="delete",
    level="task",
    context_id="task-123"
)
```

### Common Usage Patterns

#### 1. Task Work with Context Updates
```python
# Start work on task
mcp__dhafnck_mcp_http__manage_task(
    action="update",
    task_id="task-123",
    status="in_progress"
)

# Update context with progress
mcp__dhafnck_mcp_http__manage_context(
    action="add_progress",
    level="task",
    context_id="task-123",
    content="Implementing JWT token generation logic"
)

# Add discoveries as insights
mcp__dhafnck_mcp_http__manage_context(
    action="add_insight",
    level="task",
    context_id="task-123",
    content="Found existing auth utility that can be reused",
    category="discovery"
)

# Complete task with context update
mcp__dhafnck_mcp_http__manage_task(
    action="complete",
    task_id="task-123",
    completion_summary="JWT authentication fully implemented"
)
```

#### 2. Pattern Delegation Flow
```python
# After implementing reusable pattern
mcp__dhafnck_mcp_http__manage_context(
    action="delegate",
    level="task",
    context_id="task-123",
    delegate_to="project",
    delegate_data={
        "error_handling_pattern": {
            "code": error_handler_template,
            "usage": "Standard error handling for all API endpoints",
            "example": "See auth/errors.py for implementation"
        }
    },
    delegation_reason="Standardized error handling pattern for consistency"
)
```

#### 3. Multi-Level Context Resolution
```python
# Get complete context for decision making
context = mcp__dhafnck_mcp_http__manage_context(
    action="resolve",
    level="task",
    context_id="task-123"
)

# Access inherited coding standards from global level
coding_standards = context["data"]["metadata"]["coding_standards"]

# Access project-specific architecture from project level
architecture = context["data"]["metadata"]["project_architecture"]

# Access branch-specific feature requirements
feature_reqs = context["data"]["metadata"]["feature_requirements"]
```

## Integration Examples

### Task Management Integration
```python
# Task creation with context
task = await task_facade.create_task(
    git_branch_id="branch-uuid",
    title="Implement user authentication",
    description="Add JWT-based authentication with refresh tokens"
)

# Context is automatically created and inherits from branch → project → global
context = await hierarchical_context_facade.resolve_context(
    level="task",
    context_id=task.id
)

# Access inherited patterns
auth_pattern = context.data.metadata.get("authentication_patterns", {})
coding_standards = context.data.metadata.get("coding_standards", {})
```

### Agent Assignment Integration
```python
# Agent selection can use context data
context = await hierarchical_context_facade.resolve_context(
    level="task", 
    context_id=task_id
)

# Select agent based on context
if "security" in context.data.labels:
    agent = "@security_auditor_agent"
elif "frontend" in context.data.labels:
    agent = "@ui_designer_agent"
else:
    agent = "@coding_agent"
```

## Conclusion

The Hierarchical Context System provides a powerful foundation for intelligent context management in DhafnckMCP. By enabling automatic inheritance and pattern delegation, it facilitates organizational learning and maintains consistency across projects while providing the flexibility needed for specific work contexts.

The system's design prioritizes performance through intelligent caching while maintaining data integrity through careful validation and error handling. This enables autonomous AI agents to work with rich, contextual information that improves decision-making and reduces repetitive pattern discovery.