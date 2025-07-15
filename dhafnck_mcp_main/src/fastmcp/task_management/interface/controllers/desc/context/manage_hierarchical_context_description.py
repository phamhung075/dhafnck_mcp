"""
Hierarchical Context Management Tool Description

This module contains the comprehensive documentation for the manage_hierarchical_context MCP tool.
Separated from the controller logic for better maintainability and organization.
"""

MANAGE_HIERARCHICAL_CONTEXT_DESCRIPTION = """
🔗 HIERARCHICAL CONTEXT MANAGEMENT SYSTEM - Enhanced context with inheritance and delegation

⭐ WHAT IT DOES: Manages contexts across Global → Project → Task hierarchy with full inheritance, delegation, and autonomous AI workflow integration.
📋 WHEN TO USE: Advanced context operations requiring inheritance, delegation, or hierarchical resolution.
🎯 CRITICAL FOR: Multi-level context management, inheritance chains, and delegation workflows.

📊 VISUAL HIERARCHY:
```
GLOBAL (Singleton: 'global_singleton')
   ↓ inherits to
PROJECT (ID: project_id)  
   ↓ inherits to
TASK (ID: task_id)
```

| Action              | Required Parameters         | Optional Parameters                | Description                                      |
|---------------------|----------------------------|------------------------------------|--------------------------------------------------|
| resolve             | level, context_id          | force_refresh                      | Get fully resolved context with inheritance chain |
| update              | level, context_id, data    | propagate_changes                  | Update context and optionally propagate changes  |
| create              | level, context_id, data    |                                    | Create new context at specified level           |
| delegate            | level, context_id, delegate_to, delegate_data | delegation_reason    | Delegate context data to higher level           |
| propagate           | level, context_id, data    |                                    | Force propagation of changes                     |
| get_health          | (none)                     |                                    | Get system health status                         |
| cleanup_cache       | (none)                     |                                    | Clean up expired cache entries                  |

🏗️ HIERARCHY LEVELS:
• global: Singleton global context (context_id: 'global_singleton')
• project: Project-level context (context_id: project_id)
• task: Task-level context (context_id: task_id)

🔄 INHERITANCE FLOW:
Task → Project → Global (contexts inherit from higher levels)

🤖 AI DECISION MATRIX FOR DELEGATION:
```python
DELEGATION_RULES = {
    "reusable_pattern": "delegate_to_project",      # Patterns useful across tasks
    "organization_standard": "delegate_to_global",   # Company-wide best practices
    "task_specific": "no_delegation",                # Keep at task level
    "cross_project_insight": "delegate_to_global",   # Insights spanning projects
    "team_convention": "delegate_to_project"         # Team-specific patterns
}

# Example usage in your workflow:
if discovered_pattern.type == "reusable_authentication_flow":
    action = "delegate"
    delegate_to = "project"  # Share with all tasks in project
elif discovered_pattern.type == "company_coding_standard":
    action = "delegate"
    delegate_to = "global"   # Share across entire organization
```

🔍 CONTEXT RESOLUTION WORKFLOW:
1. **ALWAYS resolve before making changes** - Get current state first
   ```
   # BEFORE any update/delegate action:
   current_context = resolve(level="task", context_id=task_id)
   ```

2. **Use force_refresh sparingly** - Only when you suspect stale cache
   ```
   # Normal resolution (uses cache if valid):
   context = resolve(level="task", context_id=task_id)
   
   # Force refresh (bypasses cache):
   context = resolve(level="task", context_id=task_id, force_refresh=true)
   ```

3. **Understand inheritance chain** - Lower levels inherit from higher
   ```
   Task Context = Task Data + Project Data + Global Data
   (Most specific)                          (Most general)
   ```

📈 PROPAGATION RULES & IMPACT ANALYSIS:
1. **When to set propagate_changes=true** (default):
   • Updating shared configurations
   • Modifying inherited properties
   • Changes affecting dependent contexts
   
2. **When to set propagate_changes=false**:
   • Task-specific temporary changes
   • Experimental modifications
   • Performance-sensitive bulk updates

3. **Impact Analysis Considerations**:
   ```python
   # High Impact (propagate_changes=true):
   - Authentication methods
   - API endpoints
   - Security policies
   - Workflow standards
   
   # Low Impact (propagate_changes=false):  
   - Task progress updates
   - Local debugging flags
   - Temporary overrides
   ```

4. **Cache Considerations**:
   • Propagation invalidates dependent caches
   • Force refresh bypasses optimization
   • Monitor cache hit rates via get_health
   • Regular cleanup_cache maintains performance

💡 USAGE EXAMPLES:
• Resolve task context: action="resolve", level="task", context_id="task-123"
• Update project: action="update", level="project", context_id="proj-456", data={...}
• Delegate to global: action="delegate", level="task", context_id="task-123", delegate_to="global", delegate_data={...}

🔧 ADVANCED FEATURES:
• Context caching with dependency tracking
• Automatic propagation of changes to dependent contexts
• Delegation queue for manual review and approval
• Inheritance validation and debugging
• Performance monitoring and metrics

🛑 ERROR HANDLING:
• If required fields are missing, a clear error message is returned specifying which fields are needed.
• Unknown actions return an error listing valid actions.
• Internal errors are logged and returned with a generic error message.
• Validation errors provide detailed context about what went wrong.
"""

MANAGE_HIERARCHICAL_CONTEXT_PARAMETERS = {
    "action": "Context management action. Required. Valid: 'resolve', 'update', 'create', 'delegate', 'propagate', 'get_health', 'cleanup_cache'",
    "level": "Context level in hierarchy. Valid: 'global', 'project', 'task'. Default: 'task'",
    "context_id": "Context identifier (task_id, project_id, or 'global_singleton'). Required for most actions",
    "data": "Context data to create/update. Dictionary format. Optional",
    "delegate_to": "Target level for delegation. Valid: 'project', 'global'. Required for delegate action",
    "delegate_data": "Data to delegate to higher level. Dictionary format. Optional",
    "delegation_reason": "Reason for delegation. String. Default: 'Manual delegation via MCP'",
    "force_refresh": "Force cache refresh for resolve action. Boolean. Default: false",
    "propagate_changes": "Propagate changes to dependent contexts. Boolean. Default: true"
}