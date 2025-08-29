# MCP Tools Test Issues Report
**Date**: 2025-08-29
**Test Environment**: dhafnck_mcp_http MCP Server

## Summary
Comprehensive testing of dhafnck_mcp_http tools revealed several critical issues with various management modules. While project and context management work partially, task management, git branch management, and agent registration have significant problems.

## Issues Found

### 1. Git Branch Management Module Import Error
**Severity**: Critical
**Affected Actions**: All git branch management operations
**Error**: `No module named 'fastmcp.task_management.application.services'`

**Details**:
- Cannot create new branches
- Cannot list existing branches
- Cannot assign agents to branches
- Module import path is broken

**Test Case**:
```python
mcp__dhafnck_mcp_http__manage_git_branch(
    action="create",
    project_id="b380857d-fd6c-45ae-8171-b3237d324fa3",
    git_branch_name="feature/authentication",
    git_branch_description="Authentication feature implementation branch"
)
```

### 2. Task Management Database Query Error
**Severity**: Critical
**Affected Actions**: create, list, search
**Error**: `'str' object has no attribute 'query'` and `'ORMTaskRepository' object has no attribute 'list_tasks_minimal'`

**Details**:
- Task creation fails with database query error
- Task listing fails with missing method error
- Task search fails with query attribute error
- Repository implementation appears incomplete

**Test Cases**:
```python
# Create task fails
mcp__dhafnck_mcp_http__manage_task(
    action="create",
    git_branch_id="0f45e3b0-64f2-4994-be43-b8fd9c19e81a",
    title="Implement user login feature",
    description="Create login functionality with JWT authentication"
)

# List tasks fails
mcp__dhafnck_mcp_http__manage_task(
    action="list",
    git_branch_id="0f45e3b0-64f2-4994-be43-b8fd9c19e81a"
)
```

### 3. Agent Registration Parameter Mismatch
**Severity**: High
**Affected Actions**: register
**Error**: `CachedAgentRepository.register_agent() takes 2 positional arguments but 5 were given`

**Details**:
- Method signature mismatch between interface and implementation
- Cannot register new agents to projects

**Test Case**:
```python
mcp__dhafnck_mcp_http__manage_agent(
    action="register",
    project_id="b380857d-fd6c-45ae-8171-b3237d324fa3",
    name="test-agent-1",
    call_agent="@coding_agent"
)
```

### 4. Global Context UUID Validation
**Severity**: Medium
**Affected Actions**: get global context
**Error**: `invalid input syntax for type uuid: "global"`

**Details**:
- Cannot use "global" as context_id for global level
- Must use actual UUID instead
- Inconsistent with documentation

**Test Case**:
```python
# Fails
mcp__dhafnck_mcp_http__manage_context(
    action="get",
    level="global",
    context_id="global"
)

# Works
mcp__dhafnck_mcp_http__manage_context(
    action="create",
    level="global",
    context_id="65d733e9-04d6-4dda-9536-688c3a59448e"
)
```

### 5. Branch Context Missing project_id
**Severity**: Low
**Affected Actions**: create branch context
**Error**: `Missing required field: project_id`

**Details**:
- Branch context creation requires explicit project_id parameter
- Not automatically inferred from git_branch_id

## Working Features

### ✅ Project Management
- Create projects
- Get project details
- List projects
- Update project
- Health check
- Set project context (with proper field mapping)

### ✅ Context Management (Partial)
- Create/update project context
- Create/update branch context (with project_id)
- Create global context (with UUID)

### ✅ Compliance Management
- Get compliance dashboard (with user_id)
- System health monitoring

## Fix Prompts

### Fix 1: Git Branch Management Module
**Prompt for new chat**:
```
The git branch management module has a critical import error. When calling any action on mcp__dhafnck_mcp_http__manage_git_branch, it fails with:
"No module named 'fastmcp.task_management.application.services'"

Please fix the import path in the git branch management module. The error occurs immediately when trying to execute any action (create, list, etc.). 

Test case that should work after fix:
mcp__dhafnck_mcp_http__manage_git_branch(
    action="create",
    project_id="[valid-project-id]",
    git_branch_name="feature/test",
    git_branch_description="Test branch"
)
```

### Fix 2: Task Management Repository
**Prompt for new chat**:
```
Task management has multiple critical errors:
1. Task creation fails with "'str' object has no attribute 'query'" 
2. Task listing fails with "'ORMTaskRepository' object has no attribute 'list_tasks_minimal'"
3. Task search fails with database query errors

The ORMTaskRepository implementation appears to have missing methods and incorrect database session handling.

Test cases that should work after fix:
- Create task with git_branch_id, title, description
- List tasks by git_branch_id
- Search tasks with query string
```

### Fix 3: Agent Registration
**Prompt for new chat**:
```
Agent registration fails with parameter mismatch:
"CachedAgentRepository.register_agent() takes 2 positional arguments but 5 were given"

The interface is passing more parameters than the repository method accepts. Please fix the parameter passing in manage_agent action="register".

Test case:
mcp__dhafnck_mcp_http__manage_agent(
    action="register",
    project_id="[valid-project-id]",
    name="test-agent",
    call_agent="@coding_agent"
)
```

### Fix 4: Global Context Handling
**Prompt for new chat**:
```
Global context retrieval fails when using "global" as context_id. The system expects a UUID but documentation suggests "global" should work.

Please either:
1. Allow "global" as a special context_id for global level
2. Or auto-generate/retrieve the user's global context UUID

Current error: "invalid input syntax for type uuid: 'global'"
```

## Recommendations

1. **Immediate Priority**: Fix git branch and task management modules as they're core functionality
2. **Testing**: Add integration tests for all MCP tool actions
3. **Documentation**: Update docs to clarify UUID requirements for global context
4. **Repository Pattern**: Review all repository implementations for consistency
5. **Error Handling**: Improve error messages to be more descriptive

## Test Coverage Summary
- **Project Management**: 100% working
- **Git Branch Management**: 0% working (module error)
- **Task Management**: 0% working (repository errors)
- **Subtask Management**: Not tested (depends on tasks)
- **Context Management**: 70% working (UUID issues)
- **Agent Management**: 0% working (parameter mismatch)
- **Compliance Management**: 100% working (with user_id)

## Next Steps
1. Fix critical issues in order of priority
2. Re-run full test suite after fixes
3. Add automated tests to prevent regression
4. Update documentation with correct usage patterns