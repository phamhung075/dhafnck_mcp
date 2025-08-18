# DhafnckMCP Usage Guide for AI Agents

## 🚀 Quick Start - Your First Actions

```python
# 1. Switch to appropriate agent role
mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")

# 2. Check system health
mcp__dhafnck_mcp_http__manage_connection(action="health_check")

# 3. List available projects
mcp__dhafnck_mcp_http__manage_project(action="list")

# 4. Get or create a task to work on
mcp__dhafnck_mcp_http__manage_task(
    action="next",
    git_branch_id=branch_id,
    include_context=True
)
```

## 📊 Context Management - Share Information Between Sessions

### The Context Hierarchy
```
GLOBAL → PROJECT → BRANCH → TASK
```
Each level inherits from above. Update context to share information between:
- Different AI sessions
- Different agents  
- Different time periods

### ⚠️ CRITICAL: Context Creation for Frontend Visibility
**Tasks DO NOT automatically create context**. You must explicitly create context for tasks to be viewable in the frontend "Actions context" feature.

```python
# After creating a task, ALWAYS create its context:
task = mcp__dhafnck_mcp_http__manage_task(
    action="create",
    git_branch_id=branch_id,
    title="My new task"
)

# REQUIRED: Create context for frontend visibility
mcp__dhafnck_mcp_http__manage_context(
    action="create",
    level="task",
    context_id=task["task"]["id"],
    git_branch_id=branch_id,
    data={
        "branch_id": branch_id,
        "task_data": {
            "title": task["task"]["title"],
            "status": task["task"]["status"],
            "description": task["task"]["description"]
        }
    }
)
```

### Always Update Context With Your Work
```python
# After making discoveries or decisions, UPDATE the context:
mcp__dhafnck_mcp_http__manage_context(
    action="update",
    level="branch",  # or "project" for broader sharing
    context_id=branch_id,
    data={
        "discoveries": ["Found the API uses port 3800", "Database is PostgreSQL"],
        "decisions": ["Using React hooks for state management"],
        "current_work": "Implementing user authentication",
        "blockers": ["Missing Supabase credentials"],
        "next_steps": ["Add JWT token validation", "Test login flow"]
    },
    propagate_changes=True
)
```

### Read Context From Previous Sessions
```python
# Get all inherited context to understand previous work:
context = mcp__dhafnck_mcp_http__manage_context(
    action="resolve",
    level="branch",
    context_id=branch_id,
    force_refresh=False
)
# Context will contain all updates from this branch, project, and global levels
```

## 🤖 Agent Switching - Use The Right Specialist

### Quick Agent Selection
```python
# Based on work type, switch to appropriate agent:
if "debug" in user_request or "fix" in user_request:
    agent = "@debugger_agent"
elif "implement" in user_request or "code" in user_request:
    agent = "@coding_agent"
elif "test" in user_request:
    agent = "@test_orchestrator_agent"
elif "design" in user_request or "ui" in user_request:
    agent = "@ui_designer_agent"
else:
    agent = "@uber_orchestrator_agent"  # Default

mcp__dhafnck_mcp_http__call_agent(name_agent=agent)
```

### Available Specialist Agents
- `@coding_agent` - Writing implementation code
- `@debugger_agent` - Fixing bugs and errors
- `@test_orchestrator_agent` - Creating and running tests
- `@ui_designer_agent` - Frontend and UI work
- `@documentation_agent` - Writing docs and guides
- `@task_planning_agent` - Breaking down complex tasks
- `@security_auditor_agent` - Security reviews
- `@uber_orchestrator_agent` - General coordination

## 📝 Task Management - Track Your Work

### Create Task Before Starting Work
```python
task = mcp__dhafnck_mcp_http__manage_task(
    action="create",
    git_branch_id=branch_id,
    title="Implement user authentication",
    description="Add JWT-based auth with login/logout",
    priority="high"
)
```

### Update Task Progress
```python
mcp__dhafnck_mcp_http__manage_task(
    action="update",
    task_id=task_id,
    status="in_progress",
    details="Completed login UI, working on JWT validation"
)
```

### Complete Task With Summary
```python
mcp__dhafnck_mcp_http__manage_task(
    action="complete",
    task_id=task_id,
    completion_summary="Implemented full JWT authentication with refresh tokens",
    testing_notes="Added unit tests for auth service, tested login/logout flow"
)
```

## 🔄 Practical Workflows

### Starting New Work
```python
# 1. Switch to orchestrator
mcp__dhafnck_mcp_http__call_agent(name_agent="@uber_orchestrator_agent")

# 2. Get branch context to understand current state
context = mcp__dhafnck_mcp_http__manage_context(
    action="resolve",
    level="branch",
    context_id=branch_id
)

# 3. Create or get task
task = mcp__dhafnck_mcp_http__manage_task(
    action="next",  # or "create" for new task
    git_branch_id=branch_id
)

# 4. Switch to appropriate specialist
mcp__dhafnck_mcp_http__call_agent(name_agent="@coding_agent")

# 5. Update status
mcp__dhafnck_mcp_http__manage_task(
    action="update",
    task_id=task.task_id,
    status="in_progress"
)

# 6. Do the work...

# 7. Update context with findings
mcp__dhafnck_mcp_http__manage_context(
    action="update",
    level="branch",
    context_id=branch_id,
    data={
        "completed_work": "Added user authentication",
        "technical_decisions": ["Using JWT with 24h expiry"],
        "files_modified": ["auth.service.ts", "login.component.tsx"]
    }
)

# 8. Complete task
mcp__dhafnck_mcp_http__manage_task(
    action="complete",
    task_id=task.task_id,
    completion_summary="Full authentication implementation complete"
)
```

### Debugging Existing Code
```python
# 1. Switch to debugger
mcp__dhafnck_mcp_http__call_agent(name_agent="@debugger_agent")

# 2. Get context to understand the issue
context = mcp__dhafnck_mcp_http__manage_context(
    action="resolve",
    level="branch",
    context_id=branch_id
)

# 3. Investigate and fix...

# 4. Update context with solution
mcp__dhafnck_mcp_http__manage_context(
    action="update",
    level="branch",
    context_id=branch_id,
    data={
        "bug_fixed": "Login redirect loop",
        "root_cause": "Missing token refresh logic",
        "solution": "Added token refresh interceptor"
    }
)
```

## 🔍 Finding Information From Previous Sessions

### Check Project Context
```python
# See what's been done in this project
project_context = mcp__dhafnck_mcp_http__manage_context(
    action="get",
    level="project",
    context_id=project_id,
    include_inherited=True
)
```

### Check Branch Context
```python
# See current branch work and decisions
branch_context = mcp__dhafnck_mcp_http__manage_context(
    action="get",
    level="branch", 
    context_id=branch_id,
    include_inherited=True
)
```

### Search Tasks
```python
# Find related work
tasks = mcp__dhafnck_mcp_http__manage_task(
    action="search",
    query="authentication login",
    git_branch_id=branch_id
)
```

## 💡 Key Principles

### 1. Always Update Context
After any significant work, discovery, or decision, update the branch or project context so future sessions can access this information.

### 2. Use The Right Agent
Switch to the appropriate specialist agent for the work type. Don't try to do everything with one agent.

### 3. Track Work With Tasks
Create tasks before starting work. Update progress. Complete with detailed summaries.

### 4. Read Context First
Before starting work, always resolve context to understand what's been done before.

### 5. Share Reusable Patterns
If you discover something reusable, delegate it to project or global level:
```python
mcp__dhafnck_mcp_http__manage_context(
    action="delegate",
    level="branch",
    context_id=branch_id,
    delegate_to="project",
    delegate_data={
        "pattern": "JWT refresh token implementation",
        "code": refresh_token_code,
        "usage": "How to implement token refresh"
    },
    delegation_reason="Reusable authentication pattern"
)
```

## 🚨 Important Rules

1. **No work without agent role** - Always call `mcp__dhafnck_mcp_http__call_agent` first
2. **No work without task** - Create or get a task before starting work
3. **Update CHANGELOG.md** - Document all project changes
4. **Update context regularly** - Share information for other sessions
5. **Complete tasks properly** - Include detailed summaries and testing notes
6. **Create context for visibility** - Tasks need explicit context creation to be viewable in frontend

## 📋 Common Tool Patterns

### Project Management
```python
# Create project
mcp__dhafnck_mcp_http__manage_project(action="create", name="new-feature")

# List projects
mcp__dhafnck_mcp_http__manage_project(action="list")

# Get project health
mcp__dhafnck_mcp_http__manage_project(action="project_health_check", project_id=id)
```

### Branch Management
```python
# Create branch
mcp__dhafnck_mcp_http__manage_git_branch(
    action="create",
    project_id=project_id,
    git_branch_name="feature/auth"
)

# Assign agent to branch
mcp__dhafnck_mcp_http__manage_git_branch(
    action="assign_agent",
    project_id=project_id,
    git_branch_id=branch_id,
    agent_id="@coding_agent"
)
```

### Subtask Management
```python
# Create subtask
mcp__dhafnck_mcp_http__manage_subtask(
    action="create",
    task_id=parent_task_id,
    title="Create login component"
)

# Update subtask progress
mcp__dhafnck_mcp_http__manage_subtask(
    action="update",
    task_id=parent_task_id,
    subtask_id=subtask_id,
    progress_percentage=75,
    progress_notes="Login UI complete"
)
```

## 🔧 Troubleshooting Context Issues

### Context Not Showing in Frontend?

If you see "No context available for this task" in the frontend:

1. **Check if context exists**:
```python
mcp__dhafnck_mcp_http__manage_context(
    action="get",
    level="task",
    context_id=task_id,
    include_inherited=True
)
```

2. **If context doesn't exist, create it**:
```python
# First ensure branch context exists
mcp__dhafnck_mcp_http__manage_context(
    action="create",
    level="branch",
    context_id=branch_id,
    project_id=project_id,
    data={"project_id": project_id, "git_branch_id": branch_id}
)

# Then create task context
mcp__dhafnck_mcp_http__manage_context(
    action="create",
    level="task",
    context_id=task_id,
    git_branch_id=branch_id,
    data={
        "branch_id": branch_id,
        "task_data": {"title": "Task title", "status": "in_progress"}
    }
)
```

3. **Update task to link context**:
```python
mcp__dhafnck_mcp_http__manage_task(
    action="update",
    task_id=task_id,
    context_id=task_id  # Link task to its context
)
```

### Known Issue: Auto-Context Creation
Currently, contexts are NOT automatically created when:
- Tasks are created
- Tasks are completed
- Tasks are updated

**You MUST manually create contexts for frontend visibility.**

## 🔗 System Information

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3800
- **Database**: `/data/dhafnck_mcp.db` (Docker)
- **Docs**: `dhafnck_mcp_main/docs/`
- **Tests**: `dhafnck_mcp_main/src/tests/`

---

**Remember**: The key to multi-session collaboration is updating context. Every AI agent and session can access shared context, making your work persistent and discoverable.
    - Do not EXPOSED PASSWORD: All password need store in .env file on root (single file)