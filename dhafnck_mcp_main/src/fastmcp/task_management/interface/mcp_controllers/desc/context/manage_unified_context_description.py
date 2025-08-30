"""
Unified Context Management Description and Parameters

This module contains the complete description and parameter specifications
for the unified context management tool, supporting the 4-tier hierarchy:
GLOBAL → PROJECT → BRANCH → TASK
"""

MANAGE_UNIFIED_CONTEXT_DESCRIPTION = """
🔗 UNIFIED CONTEXT MANAGEMENT SYSTEM - 4-Tier Context Operations with Hierarchical Inheritance

⭐ WHAT IT DOES: Manages hierarchical contexts across 4 tiers (Global → Project → Branch → Task) with unified API, automatic inheritance, smart caching, and seamless data flow. Each user has their own global context instance for complete isolation.

📋 WHEN TO USE: Context operations, cross-session data persistence, hierarchical data management, agent coordination, and multi-tier information sharing.

🎯 CRITICAL FOR: Session continuity, hierarchical project organization, agent collaboration, cross-session knowledge retention, and distributed team coordination.

🏗️ HIERARCHY STRUCTURE:
```
GLOBAL (per-user) ↓ inherits to
PROJECT          ↓ inherits to
BRANCH           ↓ inherits to
TASK
```

| Action | Required Parameters | Optional Parameters | Description |
|--------|-------------------|-------------------|-------------|
| create | action, level, context_id | data, user_id, project_id, git_branch_id | Create new context at specified level |
| get | action, level, context_id | include_inherited, user_id | Retrieve specific context with optional inheritance |
| update | action, level, context_id | data, propagate_changes, user_id | Update existing context with propagation |
| delete | action, level, context_id | user_id | Remove context from specified level |
| resolve | action, level, context_id | force_refresh, include_inherited, user_id | Resolve complete context with inheritance chain |
| delegate | action, level, context_id, delegate_to | delegate_data, delegation_reason, user_id | Delegate context data to different level |
| add_insight | action, level, context_id, content | category, importance, agent, user_id | Add categorized insight to context |
| add_progress | action, level, context_id, content | agent, user_id | Add progress information to context |
| list | action, level | filters, user_id | List contexts at specified level with filtering |

🎯 LEVEL PARAMETER:
• 'global': User-scoped global context (each user has their own global context instance)
• 'project': Project-specific context inheriting from global
• 'branch': Git branch context inheriting from project and global  
• 'task': Task-specific context inheriting from branch, project, and global

💡 USAGE GUIDELINES:
• Always specify 'level' parameter to determine hierarchy tier
• Use 'context_id' appropriate for the level (user_id for global, project_id for project, etc.)
• Leverage 'include_inherited' to access complete inheritance chain
• Use 'propagate_changes' to cascade updates down the hierarchy

🔄 KEY FEATURES:
• Unified API: Single interface for all context operations across hierarchy levels
• Full Hierarchy Support: Complete 4-tier inheritance with user-scoped global contexts
• Automatic Inheritance: Child contexts automatically access parent context data
• Smart Caching: Intelligent caching with invalidation on updates for optimal performance
• Change Propagation: Automatic cascading of updates through hierarchy levels
• Delegation Queue: Queue-based delegation system for cross-level data movement
• Backward Compatible: Full compatibility with legacy parameter formats

📊 ADVANCED PARAMETERS:
• force_refresh: (boolean, default: false) Bypass cache and force fresh data retrieval
• include_inherited: (boolean, default: false) Include inherited data from parent levels
• propagate_changes: (boolean, default: true) Automatically cascade changes to child levels
• delegate_to: (string) Target level for context delegation ('global'|'project'|'branch'|'task')
• delegate_data: (dict/JSON string) Specific data to delegate to target level
• delegation_reason: (string) Reason for delegation for audit and tracking purposes
• filters: (dict/JSON string) Filter criteria for list operations
• data: (dict/JSON string) Context data - automatically parsed from JSON strings

🚀 EXAMPLE USAGE:

Dictionary format:
action="create", level="task", context_id="task-123", data={
    "status": "in_progress", 
    "insights": ["API uses JWT tokens"], 
    "progress": 75
}

JSON string format:
action="update", level="branch", context_id="branch-456", data='{"decisions": ["Use React hooks"], "blockers": ["Missing credentials"]}'

Legacy parameter format (backward compatible):
action="create", task_id="task-123", data_title="Authentication Task", data_status="in_progress"

⚠️ BACKWARD COMPATIBILITY:
• Legacy 'task_id' parameter automatically mapped to 'context_id'
• Legacy data parameters (data_title, data_description, etc.) automatically converted to structured data object
• All legacy parameter formats continue to work without modification

🛡️ ERROR HANDLING:
• Validates level and context_id parameters for consistency
• Provides clear error messages for invalid operations
• Handles JSON parsing errors gracefully with detailed feedback
• Maintains data integrity across hierarchy operations
"""

MANAGE_UNIFIED_CONTEXT_PARAMETERS = {
    "action": "Context management action to perform. Valid: 'create', 'get', 'update', 'delete', 'resolve', 'delegate', 'add_insight', 'add_progress', 'list'. Each action operates within the specified hierarchy level",
    "level": "Context hierarchy level. Valid: 'global' (user-scoped), 'project' (project-specific), 'branch' (git branch), 'task' (task-specific). Determines inheritance scope and data isolation",
    "context_id": "Context identifier appropriate for the level. Use user_id for global, project_id for project, git_branch_id for branch, task_id for task. Must match the specified level",
    "data": "Context data as dictionary object or JSON string (automatically parsed). Supports nested structures, arrays, and complex data types. Legacy data_* parameters are automatically converted",
    "user_id": "User identifier for authentication and audit trails. Used for user-scoped global contexts and access control across all hierarchy levels",
    "project_id": "Project identifier for project-level context operations. Required for project, branch, and task level operations when not inferrable from context",
    "git_branch_id": "Git branch identifier for branch-level context operations. Required for branch and task level operations when creating branch-specific contexts",
    "force_refresh": "Bypass cache and force fresh data retrieval. Boolean, default: false. Use when cache consistency is critical or after external data changes",
    "include_inherited": "Include inherited data from parent levels in response. Boolean, default: false. Enables complete context resolution with inheritance chain",
    "propagate_changes": "Automatically cascade changes to child levels in hierarchy. Boolean, default: true. Maintains consistency across hierarchy when updating parent contexts",
    "delegate_to": "Target level for context delegation operations. Valid: 'global', 'project', 'branch', 'task'. Used with delegate action to move context data between levels",
    "delegate_data": "Specific data to delegate to target level as dictionary object or JSON string. Can be subset of source context or completely new data structure",
    "delegation_reason": "Reason for context delegation for audit trails and team communication. Helps track why data was moved between hierarchy levels",
    "content": "Content for insight or progress operations. String content that will be categorized and added to the specified context level",
    "category": "Insight category for add_insight operations. Valid: 'technical', 'business', 'performance', 'risk', 'discovery'. Helps organize and filter insights",
    "importance": "Importance level for insights and progress updates. Valid: 'low', 'medium', 'high', 'critical'. Used for prioritization and filtering",
    "agent": "Agent identifier that created the insight or progress update. String identifier for tracking agent contributions and coordination",
    "filters": "Filter criteria for list operations as dictionary object or JSON string. Supports filtering by data fields, creation dates, agents, and other metadata",
    
    # Legacy parameters for backward compatibility
    "task_id": "Legacy: Use 'context_id' instead. Automatically mapped to context_id for task-level operations. Maintained for backward compatibility",
    "data_title": "Legacy: Use data.title instead. Title field within data object structure. Automatically converted to structured data format",
    "data_description": "Legacy: Use data.description instead. Description field within data object. Provides backward compatibility for existing integrations",
    "data_status": "Legacy: Use data.status instead. Status field within data object structure. Supports existing status tracking workflows",
    "data_priority": "Legacy: Use data.priority instead. Priority field within data object. Maintains compatibility with priority-based filtering",
    "data_tags": "Legacy: Use data.tags instead. Tags array within data object structure. Preserves existing tagging and categorization systems",
    "data_metadata": "Legacy: Use data.metadata instead. Metadata object within data structure. Ensures compatibility with existing metadata systems"
}


def get_unified_context_description() -> str:
    """Get the unified context management description.
    
    Returns:
        str: Complete description of the unified context management system
    """
    return MANAGE_UNIFIED_CONTEXT_DESCRIPTION


def get_unified_context_parameters() -> dict:
    """Get the unified context management parameters.
    
    Returns:
        dict: Dictionary of parameter names and their descriptions
    """
    return MANAGE_UNIFIED_CONTEXT_PARAMETERS