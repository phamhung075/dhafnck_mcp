# DhafnckMCP Issues Fix Prompts
Date: 2025-01-31
Purpose: Detailed prompts for fixing issues identified during testing

## Issue #1: Branch Context Creation Requires project_id

### Prompt for New Chat:
```
I need help fixing an issue in the DhafnckMCP system where creating a branch context requires a project_id parameter even though the branch already knows its project.

**Current Behavior:**
When calling manage_context with action="create", level="branch", the system returns error "Missing required field: project_id"

**Expected Behavior:**
The system should auto-detect project_id from the branch_id since branches belong to projects

**Test Case:**
```python
# This fails:
manage_context(
    action="create",
    level="branch", 
    context_id="e9e05e24-d51d-4e51-b3d1-94989cac7622",
    data={...}
)

# This works but shouldn't be necessary:
manage_context(
    action="create",
    level="branch",
    context_id="e9e05e24-d51d-4e51-b3d1-94989cac7622", 
    project_id="47d1f318-5a2e-43fb-a22e-2438ea17ab3a",
    data={...}
)
```

**Files to Check:**
- unified_context_controller.py
- unified_context_service.py
- branch context creation logic

Please implement auto-detection of project_id from branch_id for branch context operations.
```

---

## Issue #2: Task Labels Not Being Persisted

### Prompt for New Chat:
```
I need help fixing an issue where task labels are not being saved when creating tasks in DhafnckMCP.

**Current Behavior:**
When creating a task with labels parameter, the labels are not saved or returned in the response

**Test Case:**
```python
# Creating task with labels:
manage_task(
    action="create",
    git_branch_id="...",
    title="Task 4: Write unit tests",
    labels=["testing", "auth"]
)

# Response shows empty labels:
{
    "task": {
        "labels": [],  # Should contain ["testing", "auth"]
        ...
    }
}
```

**Expected Behavior:**
Labels should be saved and returned in task responses

**Files to Check:**
- create_task.py (CreateTaskUseCase)
- task.py (Task entity)
- task_repository.py
- Database schema for tasks table

Please investigate why labels are not being persisted and fix the issue.
```

---

## Issue #3: Context Insights Not Being Persisted

### Prompt for New Chat:
```
I need help fixing an issue where the insights array in context updates is not being persisted in DhafnckMCP.

**Current Behavior:**
When updating a task context with insights, the insights are not saved

**Test Case:**
```python
# Update context with insights:
manage_context(
    action="update",
    level="task",
    context_id="53fb56ae-527c-4f57-a8b1-ea42ccb6fb7a",
    data={
        "insights": [
            "Using UUID for primary keys provides better scalability",
            "Email validation should be done at application layer",
            "Consider adding soft delete functionality"
        ],
        "next_steps": [...]
    }
)

# Later GET returns empty insights:
manage_context(
    action="get",
    level="task", 
    context_id="53fb56ae-527c-4f57-a8b1-ea42ccb6fb7a"
)
# Response shows: "insights": []
```

**Expected Behavior:**
Insights should be persisted and returned in subsequent GET requests

**Context Storage Structure:**
The context system appears to store data in a JSON field but insights may not be properly merged

**Files to Check:**
- unified_context_service.py (update method)
- Context entity/model
- Database schema for context storage
- JSON merging logic in context updates

Please fix the insights persistence issue ensuring arrays are properly stored and retrieved.
```

---

## Enhancement Suggestions

### Enhancement #1: Batch Operations
```
Consider adding batch operations for creating multiple tasks/subtasks at once:

manage_task(
    action="create_batch",
    git_branch_id="...",
    tasks=[
        {"title": "Task 1", "priority": "high"},
        {"title": "Task 2", "priority": "medium"},
        {"title": "Task 3", "priority": "low"}
    ]
)
```

### Enhancement #2: Advanced Search Filters
```
Enhance search to support multiple filters:

manage_task(
    action="search",
    query="authentication",
    filters={
        "status": ["todo", "in_progress"],
        "priority": "high",
        "assignee": "@coding_agent",
        "has_dependencies": true
    }
)
```

### Enhancement #3: Task Templates
```
Add support for task templates:

manage_task(
    action="create_from_template",
    template="bug_report",
    git_branch_id="...",
    variables={
        "bug_title": "Login fails with special characters",
        "severity": "high"
    }
)
```

---

## Testing Recommendations

1. **Add Integration Tests**: Create tests that verify label persistence end-to-end
2. **Add Context Tests**: Verify all context fields are properly saved and retrieved
3. **Add Validation Tests**: Ensure required fields are validated at API level
4. **Performance Tests**: Test system with 1000+ tasks to verify scalability

---

End of Issues Fix Prompts Document