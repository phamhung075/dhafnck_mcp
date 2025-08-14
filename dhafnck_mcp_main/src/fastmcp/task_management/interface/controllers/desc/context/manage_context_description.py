"""
Context Management Tool Description

This module contains the comprehensive documentation for the manage_context MCP tool.
Separated from the controller logic for better maintainability and organization.
"""

MANAGE_CONTEXT_DESCRIPTION = """
🧩 CONTEXT MANAGEMENT SYSTEM - Task Context and AI Insights

⭐ WHAT IT DOES: Manages task context, properties, insights, and progress tracking for AI-driven workflow orchestration.
📋 WHEN TO USE: Context operations, property management, insight tracking, and progress updates.
🎯 CRITICAL FOR: AI context management and task workflow orchestration.

> **Note**: `manage_context` internally uses the hierarchical context system for backward compatibility. For advanced features like context delegation and inheritance debugging, use `manage_context`.

| Action             | Required Parameters         | Optional Parameters                | Description                                      |
|--------------------|----------------------------|------------------------------------|--------------------------------------------------|
| create             | task_id                    | user_id (default: 'default_id'), project_id, git_branch_id (auto-detected from task if not provided), data_title, data_description, data_status, data_priority, data_assignees, data_labels, data_estimated_effort, data_due_date | Create a new context for a task                  |
| update             | task_id                    | user_id, project_id, git_branch_id (auto-detected), data_title, data_description, data_status, data_priority, data_assignees, data_labels, data_estimated_effort, data_due_date | Update an existing context                       |
| get                | task_id                    | user_id, project_id, git_branch_id (auto-detected)            | Get a context by task ID                         |
| delete             | task_id                    | user_id, project_id, git_branch_id (auto-detected)            | Delete a context by task ID                      |
| list               | user_id, project_id        |                                          | List contexts for a user/project                 |
| get_property       | task_id, property_path     | user_id, project_id, git_branch_id (auto-detected)            | Get a property from a context                    |
| update_property    | task_id, property_path, value | user_id, project_id, git_branch_id (auto-detected)         | Update a property in a context                   |
| merge              | task_id                    | user_id, project_id, git_branch_id (auto-detected), data_title, data_description, data_status, data_priority, data_assignees, data_labels, data_estimated_effort, data_due_date | Merge data into an existing context              |
| add_insight        | task_id, content           | user_id, project_id, git_branch_id (auto-detected), agent, category, importance | Add an insight to a context                      |
| add_progress       | task_id, content           | user_id, project_id, git_branch_id (auto-detected), agent     | Add progress to a context                        |
| update_next_steps  | task_id, next_steps        | user_id, project_id, git_branch_id (auto-detected)            | Update next steps for a context                  |

💡 USAGE GUIDELINES:
• Provide all required identifiers for each action (see table above).
• Optional parameters can be omitted unless overriding defaults.
• git_branch_id is required for most operations but will be auto-detected from task_id when possible.
• The tool returns detailed error messages for missing or invalid parameters, unknown actions, and internal errors.
• All business logic is delegated to the context manager.
• Data parameters are flattened for MCP compatibility (data_title, data_description, etc. instead of complex data dictionary).
• Parameters are reconstructed internally to maintain business logic compatibility.

🔄 PARAMETER FLATTENING PATTERN (MCP COMPATIBILITY):
WHY: MCP protocol requires flat parameter structure - no nested objects allowed
HOW: Prefix nested fields with parent name using underscore

MAPPING EXAMPLES:
• Logical: data.title → Flattened: data_title
• Logical: data.description → Flattened: data_description
• Logical: data.assignees → Flattened: data_assignees
• Logical: data.labels → Flattened: data_labels

RECONSTRUCTION EXAMPLE:
Input (flattened):
  data_title="Task Title"
  data_description="Task Description"
  data_assignees=["user1", "user2"]
  
Internal (reconstructed):
  data = {
    "title": "Task Title",
    "description": "Task Description", 
    "assignees": ["user1", "user2"]
  }

🤖 AI USAGE RULES:

1. ACTION SELECTION DECISION TREE:
   • New task without context → action="create"
   • Existing context needs changes → action="update"
   • Partial updates only → action="merge"
   • Need specific property → action="get_property"
   • Tracking work progress → action="add_progress"
   • Recording discoveries → action="add_insight"
   • Planning next work → action="update_next_steps"

2. PARAMETER CONSTRUCTION RULES:
   • Always use flattened data_* parameters for task data
   • Accept both string and array for assignees/labels
   • Use ISO format for dates (YYYY-MM-DD)
   • Priority values: 'low', 'medium', 'high', 'urgent', 'critical'
   • Status values: 'todo', 'in_progress', 'blocked', 'review', 'testing', 'done'

3. PROPERTY PATH SYNTAX:
   • Dot notation: "metadata.created_at"
   • Array access: "assignees[0]"
   • Nested paths: "insights.latest.content"

4. INSIGHT CATEGORIZATION:
   • 'technical': Code patterns, architecture decisions
   • 'business': Requirements, user feedback
   • 'risk': Potential issues, blockers
   • 'optimization': Performance improvements
   • 'discovery': New findings, alternatives

5. PROGRESS TRACKING PATTERNS:
   • Use add_progress every 25% completion
   • Include specific accomplishments
   • Mention any blockers encountered
   • Reference completed subtasks

📊 FLEXIBLE TYPE HANDLING:
• data_assignees: Union[List[str], str, None]
  - Single string: "user1"
  - List: ["user1", "user2"]
  - None: Use existing/default

• data_labels: Union[List[str], str, None]
  - Single string: "frontend"
  - List: ["frontend", "urgent", "bug"]
  - None: Use existing/default

• next_steps: Union[List[str], str]
  - Single string: "Complete implementation"
  - List: ["Design API", "Implement logic", "Add tests"]

🎯 VALIDATION RULES:
• task_id: Must be valid UUID format
• priority: Must be one of ['low', 'medium', 'high', 'urgent', 'critical']
• status: Must be valid task status
• importance: Must be one of ['low', 'medium', 'high']
• dates: Must be ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
• property_path: Must be valid dot notation path
• content: Required for insights/progress, should be descriptive

💡 PRACTICAL EXAMPLES:

1. Creating context for new task:
   action="create", task_id="uuid", data_title="Implement auth", data_description="Add JWT authentication", data_priority="high", data_assignees=["dev1", "dev2"]

2. Updating progress with discovery:
   action="add_progress", task_id="uuid", content="Completed login UI, discovered existing validation utility"
   Then: action="add_insight", task_id="uuid", content="Found reusable validation in utils/validators.js", category="discovery"

3. Setting next steps after analysis:
   action="update_next_steps", task_id="uuid", next_steps=["Create auth service", "Add JWT middleware", "Update user model", "Write integration tests"]

4. Merging partial updates:
   action="merge", task_id="uuid", data_status="in_progress", data_assignees="additional_dev"

🛑 ERROR HANDLING:
• If required fields are missing, a clear error message is returned specifying which fields are needed.
• Unknown actions return an error listing valid actions.
• Internal errors are logged and returned with a generic error message.
• Type mismatches provide guidance on correct format.
"""

MANAGE_CONTEXT_PARAMETERS = {
    "action": "Context management action. Required. Valid: 'create', 'get', 'update', 'delete', 'list', 'get_property', 'update_property', 'merge', 'add_insight', 'add_progress', 'update_next_steps'",
    "task_id": "Task identifier (UUID). Required for most actions",
    "user_id": "User identifier. Default: 'default_id'",
    "project_id": "Project identifier. Default: ''",
    "git_branch_id": "Git branch identifier (UUID). Auto-detected from task_id if not provided. Required for most operations",
    "property_path": "Property path for property operations (dot notation, e.g., 'metadata.created_at')",
    "value": "Value for property updates (any JSON-serializable type)",
    # Flattened data parameters with comprehensive descriptions
    "data_title": "Context title for create/update/merge operations. String. The main title/name of the task",
    "data_description": "Context description for create/update/merge operations. String. Detailed description including requirements and acceptance criteria",
    "data_status": "Context status for create/update/merge operations. String. Valid: 'todo', 'in_progress', 'blocked', 'review', 'testing', 'done', 'cancelled'",
    "data_priority": "Context priority for create/update/merge operations. String. Valid: 'low', 'medium', 'high', 'urgent', 'critical'",
    "data_assignees": "Context assignees for create/update/merge operations. Union[List[str], str]. Can be single user ID or list of user IDs",
    "data_labels": "Context labels for create/update/merge operations. Union[List[str], str]. Tags for categorization (e.g., 'frontend', 'bug', 'feature')",
    "data_estimated_effort": "Context estimated effort for create/update/merge operations. String. Human-readable format (e.g., '2 hours', '3 days', '1 week')",
    "data_due_date": "Context due date for create/update/merge operations. String. ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    "agent": "Agent name for insights/progress. String. Identifies which agent is adding the insight/progress",
    "category": "Category for insights. String. Valid: 'technical', 'business', 'risk', 'optimization', 'discovery'",
    "content": "Content for insights/progress. String. Detailed description of the insight or progress update",
    "importance": "Importance level for insights. String. Valid: 'low', 'medium', 'high'. Default: 'medium'",
    "next_steps": "List of next steps. Union[List[str], str]. Array of actionable next steps or single step string"
}