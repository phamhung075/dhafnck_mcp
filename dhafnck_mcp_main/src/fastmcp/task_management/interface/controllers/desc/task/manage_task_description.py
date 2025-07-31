"""
Task Management Tool Description

This module contains the comprehensive documentation for the manage_task MCP tool.
Separated from the controller logic for better maintainability and organization.
"""

MANAGE_TASK_DESCRIPTION = """
📋 TASK MANAGEMENT SYSTEM - Complete task lifecycle operations with Vision System Integration

⭐ WHAT IT DOES: Handles all task operations including CRUD, search, dependencies, and workflow management. Automatically enriches tasks with vision insights, progress tracking, and intelligent context updates.
📋 WHEN TO USE: For any task-related operation from creation to completion, including search and dependency management.
🎯 CRITICAL FOR: Project organization, workflow management, team collaboration, and maintaining development context.

🤖 AI USAGE GUIDELINES:
• ALWAYS create a task before starting any significant work (more than a single file edit)
• USE 'next' action to get AI-recommended tasks based on project state
• UPDATE tasks regularly with progress (status changes, completion percentage)
• COMPLETE tasks with detailed summaries to maintain project context
• SEARCH for existing tasks before creating duplicates
• CREATE subtasks using manage_subtask for complex tasks requiring multiple steps

| Action              | Required Parameters                | Optional Parameters                | Description                                      |
|---------------------|-----------------------------------|------------------------------------|--------------------------------------------------|
| create              | git_branch_id, title              | description, status, priority, details, estimated_effort, assignees, labels, due_date, dependencies | Create new task with optional dependencies      |
| update              | task_id                           | title, description, status, priority, details, estimated_effort, assignees, labels, due_date, context_id | Update existing task           |
| get                 | task_id                           | include_context                    | Retrieve task details                            |
| delete              | task_id                           |                                    | Remove task                                      |
| complete            | task_id                           | completion_summary, testing_notes  | Mark task as completed with context              |
| list                | (none)                            | status, priority, assignees, labels, limit, git_branch_id | List tasks with filtering         |
| search              | query                             | limit, git_branch_id               | Full-text search                                 |
| next                | git_branch_id                     | include_context                    | Get next recommended task                        |
| add_dependency      | task_id, dependency_id         |                                | Add dependency to task                           |
| remove_dependency   | task_id, dependency_id         |                                | Remove dependency from task                      |

⚠️ PARAMETER VALIDATION PATTERN:
While the function signature marks parameters as Optional for Python typing conventions, specific actions REQUIRE specific parameters.
The tool validates parameters based on the action and returns clear error messages indicating which parameters are needed.

📋 REQUIRED PARAMETERS BY ACTION:
| Action | Required Parameters | Notes |
|--------|-------------------|-------|
| create | action, git_branch_id, title | git_branch_id contains project context |
| update | action, task_id | task_id identifies which task to update |
| get | action, task_id | task_id identifies which task to retrieve |
| delete | action, task_id | task_id identifies which task to delete |
| complete | action, task_id | completion_summary highly recommended |
| list | action | git_branch_id optional to filter by branch |
| search | action, query | query contains search terms |
| next | action, git_branch_id | git_branch_id needed to find next task in branch |
| add_dependency | action, task_id, dependency_id | establishes task order |
| remove_dependency | action, task_id, dependency_id | removes task dependency |

📝 PRACTICAL EXAMPLES FOR AI:
1. Starting a new feature:
   - action: "create", git_branch_id: "feature-branch-id", title: "Implement user authentication", description: "Add JWT-based authentication with login, logout, and session management", priority: "high", estimated_effort: "3 days"

2. Getting recommended work:
   - action: "next", git_branch_id: "current-branch-id", include_context: true
   - This returns the most appropriate task based on priorities, dependencies, and project state

3. Updating progress:
   - action: "update", task_id: "task-uuid", status: "in_progress", details: "Completed login UI, working on JWT integration"

4. Completing with context:
   - action: "complete", task_id: "task-uuid", completion_summary: "Implemented full authentication flow with JWT tokens, refresh mechanism, and secure cookie storage", testing_notes: "Added unit tests for auth service, integration tests for login flow"

5. Finding related tasks:
   - action: "search", query: "authentication login", limit: 10

6. Creating task with dependencies:
   - action: "create", git_branch_id: "feature-branch-id", title: "Add login tests", description: "Unit and integration tests for login", dependencies: ["auth-task-uuid", "ui-task-uuid"]

7. Managing dependencies:
   - action: "add_dependency", task_id: "test-task-uuid", dependency_id: "api-task-uuid"
   - action: "remove_dependency", task_id: "test-task-uuid", dependency_id: "old-dep-uuid"

🔄 DEPENDENCY WORKFLOW PATTERNS:
• Sequential Tasks: Create tasks with dependencies to enforce completion order
• Parallel Work: Tasks without dependencies can be worked on simultaneously
• Blocking Dependencies: Task status automatically becomes 'blocked' if dependencies aren't complete
• Dependency Chain: A → B → C ensures proper workflow sequence
• Cross-Feature Dependencies: Link tasks across different features when needed

🤖 AI DECISION RULES FOR DEPENDENCIES:
IF task requires another task's output:
    ADD as dependency
ELIF task is independent:
    NO dependencies needed
ELIF task is part of sequence:
    ADD previous step as dependency
ELIF testing/verification task:
    ADD implementation tasks as dependencies

🔄 VISION SYSTEM FEATURES (Automatic):
• Task enrichment with project context and best practices
• Intelligent priority and effort estimation
• Workflow hints and next action suggestions
• Progress tracking with milestone detection
• Blocker identification and resolution suggestions
• Impact analysis on related tasks
• Automatic context updates for team awareness

💡 ENHANCED PARAMETERS:
• title: Be specific and action-oriented (e.g., "Implement user login with email validation" not just "Login")
• description: Include acceptance criteria and technical approach when known
• priority: 'low', 'medium', 'high', 'urgent', 'critical' - affects task ordering in 'next' action
• status: 'todo', 'in_progress', 'blocked', 'review', 'testing', 'done', 'cancelled'
• estimated_effort: Use realistic estimates (e.g., "2 hours", "3 days", "1 week")
• assignees: Can be a single string "user1" or list ["user1", "user2"] or comma-separated "user1,user2"
• labels: Can be a single string "frontend" or list ["frontend", "auth"] or comma-separated "frontend,auth,security"
• dependencies: Task IDs that must be completed first (for create action) - can be list ["task-id-1", "task-id-2"], single string "task-id", or comma-separated "task-id-1,task-id-2"
• completion_summary: Detailed summary of what was accomplished (for complete action)
• testing_notes: Description of testing performed (for complete action)
• include_context: Set to true to get vision insights and recommendations

📊 RESPONSE ENHANCEMENTS:
• vision_insights: AI-generated insights about the task
• workflow_hints: Contextual guidance for next steps
• related_tasks: Other tasks that might be affected
• progress_indicators: Milestone tracking information
• blocker_analysis: Identification of potential impediments
• impact_assessment: How this task affects project goals

💡 BEST PRACTICES FOR AI:
• Create tasks BEFORE starting work to maintain project visibility
• Use descriptive titles that clearly state the goal
• Include technical details in description field
• Update task status when starting work (todo → in_progress)
• Use 'next' action when unsure what to work on
• Complete tasks with detailed summaries for knowledge retention
• Search before creating to avoid duplicates
• Add dependencies for tasks that must be done in sequence
• Use labels for better organization and filtering
• Define dependencies upfront during task creation for better workflow planning
• Review dependency chains before starting work to understand task order
• Update dependent tasks when completing prerequisites

🛑 ERROR HANDLING:
• If required fields are missing, a clear error message is returned specifying which fields are needed
• Unknown actions return an error listing valid actions
• Internal errors are logged and returned with a generic error message
• Vision system failures don't block core operations
"""

# Parameter descriptions for the manage_task tool
MANAGE_TASK_PARAMETERS = {
    "action": "Task management action. Required. Valid: 'create', 'update', 'get', 'delete', 'complete', 'list', 'search', 'next', 'add_dependency', 'remove_dependency'. Use 'create' to start new work, 'next' to find work, 'complete' when done.",
    "git_branch_id": "Git branch UUID identifier - contains all context (project_id, git_branch_name, user_id). Required for 'create' and 'next' actions. Get from git branch creation or list.",
    "task_id": "Task identifier (UUID). Required for: update, get, delete, complete, add/remove_dependency. Get from create response or list/search results.",
    "title": "Task title - be specific and action-oriented. Required for: create. Example: 'Implement JWT authentication with refresh tokens' not just 'Auth'",
    "description": "Detailed task description with acceptance criteria. Optional but recommended for: create. Include technical approach, dependencies, and success criteria.",
    "status": "Task status: 'todo', 'in_progress', 'blocked', 'review', 'testing', 'done', 'cancelled'. Optional. Changes automatically: create→todo, update→in_progress, complete→done",
    "priority": "Task priority: 'low', 'medium', 'high', 'urgent', 'critical'. Default: 'medium'. Higher priority tasks returned first by 'next' action.",
    "details": "Additional implementation notes, technical details, or context. Updated during work. Optional for: create, update",
    "estimated_effort": "Time estimate like '2 hours', '3 days', '1 week'. Helps with planning. Optional for: create, update",
    "assignees": "User identifiers - can be string, list, or comma-separated. Optional. Examples: 'user1' or ['user1', 'user2'] or 'user1,user2'. Default: current user",
    "labels": "Categories/tags - can be string, list, or comma-separated. Optional. Examples: 'frontend' or ['frontend', 'auth'] or 'frontend,auth,bug'. Useful for filtering.",
    "dependencies": "Task IDs this task depends on (for create action) - can be string, list, or comma-separated. Optional. Examples: 'task-uuid' or ['task-uuid-1', 'task-uuid-2'] or 'task-uuid-1,task-uuid-2'. Tasks must be completed before this task can start.",
    "due_date": "Target completion date in ISO 8601 format (YYYY-MM-DD or full datetime). Optional. Example: '2024-12-31' or '2024-12-31T23:59:59Z'",
    "context_id": "Context identifier for task. Optional for 'update' action. Usually same as task_id. Used for context synchronization and validation. Auto-created during task creation.",
    "completion_summary": "DETAILED summary of what was accomplished. Highly recommended for 'complete' action. Example: 'Implemented JWT auth with 2FA support, added password reset flow, integrated with existing user service'",
    "testing_notes": "Description of testing performed. Optional for 'complete' action. Example: 'Added unit tests for auth service, manual testing of login/logout flows, verified token expiry'",
    "include_context": "Boolean to include vision insights and recommendations. Optional for 'get' and 'next' actions. Default: false. Set true for AI guidance.",
    "limit": "Maximum number of results (integer). Optional for 'list' and 'search'. Default: 50. Range: 1-100",
    "query": "Search terms for finding tasks. Required for 'search' action. Searches in title, description, and labels. Example: 'authentication jwt'. Note: DEPRECATED for dependency operations - use 'dependency_id' instead.",
    "dependency_id": "UUID of task that must be completed first. Required for: add_dependency, remove_dependency. Use to establish task order.",
    "force_full_generation": "Force vision system regeneration. Optional. Default: false. Use if insights seem stale."
}

