# Manual Progress Tracking with Subtasks

## Overview

This document describes how AI agents must manually update parent task progress and context when working with subtasks. The system cannot automatically track progress - AI must remember to update both subtask and parent task progress.

## The Reality

When AI works on subtasks:
- Parent task progress is NOT automatically updated
- Context updates on subtasks do NOT propagate automatically
- Vision metrics must be manually aggregated
- AI MUST manually update both subtask and parent task

## Solution: Manual Progress Updates with Enriched Responses

### 1. Enhanced Subtask Management Tools

```python
@mcp.tool()
async def manage_subtask(
    action: str,
    task_id: str,  # Parent task ID
    subtask_id: Optional[str] = None,
    title: Optional[str] = None,
    # REQUIRED for progress tracking
    progress_percentage: Optional[int] = None,  # AI must provide
    progress_notes: Optional[str] = None,       # AI must describe work
    completion_summary: Optional[str] = None,   # Required for completion
    **kwargs
) -> Dict[str, Any]:
    """Subtask management requiring manual progress updates"""
    
    # Validate required fields based on action
    if action == "update" and not progress_notes:
        return {
            "success": False,
            "error": "progress_notes required to track what you did",
            "hint": "Describe what work you completed on this subtask"
        }
    
    if action == "complete" and not completion_summary:
        return {
            "success": False,
            "error": "completion_summary required to complete subtask",
            "example": "Implemented authentication with JWT tokens"
        }
    
    # Execute subtask action
    result = execute_subtask_action(action, task_id, subtask_id, **kwargs)
    
    # Calculate parent progress from all subtasks
    if result.get("success"):
        parent_progress = calculate_parent_progress_from_subtasks(task_id)
        
        # Enrich response to remind AI about parent update
        result["parent_task_reminder"] = {
            "parent_progress": f"{parent_progress}%",
            "message": "Remember to update parent task context too!",
            "suggested_update": {
                "action": "update",
                "context_id": task_id,
                "data": {
                    "subtask_progress": [
                        f"Completed: {progress_notes or completion_summary}"
                    ]
                }
            }
        }
    
    return result
```

### 2. Manual Progress Tracking Pattern

```python
# WHAT AI MUST DO:

# 1. Before starting work on subtask
subtask = manage_subtask(
    action="get",
    task_id="parent_123",
    subtask_id="sub_456"
)

# 2. Do the work with built-in tools
# ... edit files, run tests, etc ...

# 3. MANUALLY update subtask progress
manage_subtask(
    action="update",
    task_id="parent_123",
    subtask_id="sub_456",
    progress_percentage=50,
    progress_notes="Implemented login flow, tests pending"
)

# 4. MANUALLY update parent task context
manage_context(
    action="update",
    level="task",
    context_id="parent_123",
    data={
        "subtask_updates": {
            "sub_456": "Login flow implemented (50%)"
        }
    }
)
```

### 3. Required Parameters for Progress

```python
class SubtaskProgressRequirements:
    """Enforces manual progress tracking through required parameters"""
    
    UPDATE_ACTION_REQUIRES = [
        "progress_percentage",  # 0-100
        "progress_notes"       # What was done
    ]
    
    COMPLETE_ACTION_REQUIRES = [
        "completion_summary",   # Detailed summary
        "impact_on_parent"     # How this affects parent task
    ]
    
    def validate(self, action: str, params: dict) -> dict:
        if action == "update":
            missing = [p for p in self.UPDATE_ACTION_REQUIRES if not params.get(p)]
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required: {missing}",
                    "hint": "AI must manually provide progress updates"
                }
        
        return {"success": True}
```

### 4. Response Enrichment to Guide AI

```python
def enrich_subtask_response(response: dict, context: dict) -> dict:
    """Add reminders and guidance to subtask responses"""
    
    # Calculate time since last update
    last_update = context.get("last_progress_update")
    if last_update:
        time_elapsed = datetime.utcnow() - last_update
        if time_elapsed > timedelta(minutes=30):
            response["progress_reminder"] = {
                "⚠️ status": "Progress update overdue",
                "last_update": f"{time_elapsed.minutes} minutes ago",
                "action_needed": "Update subtask progress"
            }
    
    # Add parent task status
    parent = get_parent_task(context["parent_id"])
    response["parent_task_info"] = {
        "overall_progress": f"{parent.calculated_progress}%",
        "total_subtasks": parent.subtask_count,
        "completed_subtasks": parent.completed_subtask_count,
        "next_step": "Remember to update parent context after subtask work"
    }
    
    return response
```

### 5. Complete Subtask Pattern

```python
# REQUIRED PATTERN FOR COMPLETING SUBTASKS:

# 1. Complete the subtask with summary
result = manage_subtask(
    action="complete",
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="""
    Implemented complete authentication flow:
    - Created login endpoint
    - Added JWT token generation
    - Implemented refresh tokens
    - All tests passing (15/15)
    """,
    impact_on_parent="Core authentication feature complete"
)

# 2. Update parent task context (MANUAL)
manage_context(
    action="update",
    level="task",
    context_id="parent_123",
    data={
        "completed_subtasks": {
            "sub_456": "Authentication flow complete"
        },
        "overall_progress": "1 of 3 major features complete"
    }
)

# 3. Check if all subtasks complete
if result.get("all_subtasks_complete"):
    # Parent task ready for completion
    manage_task(
        action="complete",
        task_id="parent_123",
        completion_summary="All features implemented..."
    )
```

### 6. Why Manual Updates?

```yaml
# The constraints we face:

ai_limitations:
  - cannot_modify_ai_tools: true  # Can't change Claude/Cursor tools
  - no_automatic_capture: true    # Can't see what AI does
  - no_persistent_sessions: true  # Each call is independent
  
system_capabilities:
  - can_require_parameters: true  # Force completion_summary
  - can_enrich_responses: true    # Add reminders
  - can_calculate_progress: true  # From manual updates
  - can_validate_inputs: true     # Ensure progress provided
```

## Usage Examples

### AI Working on Subtasks (Manual Pattern)

```python
# 1. Start work on subtask
subtask = manage_subtask(
    action="get", 
    task_id="parent_123",
    subtask_id="sub_456"
)
# Response includes reminder about manual updates

# 2. Do some work...
# ... edit files, write code, run tests ...

# 3. MUST manually update progress
manage_subtask(
    action="update",
    task_id="parent_123", 
    subtask_id="sub_456",
    progress_percentage=75,
    progress_notes="API endpoints complete, working on tests"
)

# 4. Complete subtask when done
manage_subtask(
    action="complete",
    task_id="parent_123",
    subtask_id="sub_456", 
    completion_summary="API fully implemented with tests",
    impact_on_parent="Backend API ready for frontend integration"
)

# 5. Don't forget parent context!
manage_context(
    action="update",
    level="task",
    context_id="parent_123",
    data={
        "progress": ["Backend API complete (subtask 1/3)"],
        "next_steps": ["Start frontend integration"]
    }
)
```

### What Happens Without Manual Updates

```python
# BAD: AI forgets to update progress
# Result: Parent task shows 0% even though work is done

# BAD: AI completes subtask without summary
manage_subtask(action="complete", task_id="p1", subtask_id="s1")
# ERROR: completion_summary is required

# BAD: AI doesn't update parent context
# Result: Parent task has no record of subtask work
```

## Best Practices

1. **Update After Each Work Session**
   - Set a timer to remind yourself
   - Update before switching tasks
   - Include specific details

2. **Use Templates for Consistency**
   ```python
   progress_template = {
       "files_modified": [],
       "tests_added": [],
       "features_completed": [],
       "blockers": []
   }
   ```

3. **Complete Parent Task Properly**
   - Ensure all subtasks are complete
   - Aggregate findings in parent summary
   - Include learnings from all subtasks

## Summary

The subtask progress system requires:
- **Manual progress updates** from AI at each step
- **Required parameters** for completion (can't skip)
- **Response enrichment** to remind about updates
- **Parent context updates** must be done separately
- **AI discipline** to remember the manual process

This is NOT automatic - it requires AI to actively track and update progress!