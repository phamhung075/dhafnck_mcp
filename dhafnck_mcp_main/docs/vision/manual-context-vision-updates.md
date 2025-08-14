# Manual Context and Vision Updates - Working with AI Limitations

## The Reality

AI clients (Claude Code, Cursor, etc.) have their own built-in tools that we CANNOT modify:
- ✅ They can read/write files
- ✅ They can run commands
- ✅ They can complete tasks
- ❌ **We CANNOT track what they do automatically**
- ❌ **We CANNOT modify their tools**

The AI must manually update context - this is not automatic.

## Solution: Enforcement Through Required Parameters

### 1. Block Task Completion Without Summary

Since we can't track automatically, we REQUIRE manual summaries:

```python
# Modified complete_task action
@mcp.tool()
async def manage_task(
    action: str,
    task_id: str,
    completion_summary: str = None,  # REQUIRED for complete action
    # ... other params ...
) -> Dict[str, Any]:
    
    if action == "complete":
        # ENFORCE: completion_summary is required
        if not completion_summary:
            return {
                "success": False,
                "error": "completion_summary is required to complete task",
                "hint": "Please provide a detailed summary of what you accomplished",
                "example": {
                    "action": "complete",
                    "task_id": task_id,
                    "completion_summary": "Implemented JWT refresh tokens: Modified auth/jwt.py, added Redis storage, created tests. All tests passing."
                }
            }
        
        # Save the summary as context
        await update_task_context(
            task_id=task_id,
            updates={
                "completion": {
                    "summary": completion_summary,
                    "timestamp": datetime.utcnow(),
                    "completed_by": current_agent
                }
            }
        )
```

### 2. Encourage Updates Through Response Enrichment

Since we can't track automatically, we remind AI through enriched responses:

```python
# Enhanced task response with update reminders
def enhance_task_response(task: Dict[str, Any]) -> Dict[str, Any]:
    """Add update reminders to task responses"""
    
    # Calculate time since last update
    last_update = get_last_context_update(task["id"])
    time_since = datetime.utcnow() - last_update
    
    if time_since > timedelta(minutes=30):
        task["context_reminder"] = {
            "status": "⚠️ Context update needed",
            "last_update": f"{time_since.total_seconds() // 60} minutes ago",
            "suggested_update": {
                "action": "update",
                "task_id": task["id"],
                "context_id": task["id"],
                "data": {
                    "progress": ["What you've done so far"],
                    "files_modified": ["List files you've changed"],
                    "decisions": ["Key decisions made"],
                    "blockers": ["Any issues encountered"]
                }
            }
        }
    
    return task
```

### 3. Progress Tracking Through Parameters

Since we can't see AI's work, we ask for progress explicitly:

```python
# Add progress parameter to update action
@mcp.tool()
async def manage_task(
    action: str,
    task_id: str,
    progress_notes: str = None,  # Optional progress update
    # ... other params ...
) -> Dict[str, Any]:
    
    if action == "update" and progress_notes:
        # AI voluntarily provided progress
        await add_progress_note(
            task_id=task_id,
            note=progress_notes,
            timestamp=datetime.utcnow()
        )
        
        return {
            "success": True,
            "message": "Progress noted. Thank you for the update!",
            "next_reminder": "in 30 minutes"
        }
```

### 4. Templates in Task Descriptions

Help AI remember what to track by including templates:

```python
def create_task_with_context_template(title: str, description: str) -> Task:
    """Create task with built-in context tracking template"""
    
    enhanced_description = f"""
{description}

REMEMBER TO UPDATE CONTEXT:
After completing work, update context with:
- Files you read: []
- Files you modified: []
- Key decisions: []
- Discoveries: []
- Test results: []
- Next steps: []

Use: manage_context(action="update", level="task", context_id=task_id, data={{...}})
"""
    
    return create_task(
        title=title,
        description=enhanced_description
    )
```

## What We Can and Cannot Do

### We CAN:
- **Require** completion_summary parameter
- **Remind** through enriched responses
- **Provide** templates and examples
- **Track** when context was last updated
- **Block** completion without summary

### We CANNOT:
- **Automatically track** file modifications
- **Intercept** AI tool calls
- **Modify** Claude Code or Cursor tools
- **See** what AI does between MCP calls
- **Force** updates during work

## Best Practices for Manual Updates

### 1. Start Task Pattern
```python
# AI should check context first
context = manage_context(
    action="get",
    level="task",
    context_id=task_id
)

# Plan work based on context
# ... do work ...
```

### 2. During Work Pattern
```python
# After significant progress
manage_task(
    action="update",
    task_id=task_id,
    progress_notes="Implemented authentication flow, all tests passing"
)

# Or update context directly
manage_context(
    action="update",
    level="task",
    context_id=task_id,
    data={
        "progress": ["Implemented auth flow"],
        "files_modified": ["auth/login.py", "auth/jwt.py"],
        "test_results": "15/15 passing"
    }
)
```

### 3. Complete Task Pattern
```python
# REQUIRED: Detailed completion summary
manage_task(
    action="complete",
    task_id=task_id,
    completion_summary="""
    Implemented complete authentication system:
    - Modified auth/login.py for new flow
    - Added JWT refresh tokens in auth/jwt.py
    - Created comprehensive test suite
    - All 15 tests passing with 95% coverage
    - Ready for code review
    """
)
```

## Why This Approach?

### Constraints We Face:
1. **Cannot modify AI tools** - Built-in tools are unchangeable
2. **Cannot track automatically** - No access to AI's actions
3. **AI forgets to update** - Natural behavior without enforcement
4. **No persistent sessions** - Each interaction is independent

### Our Solutions:
1. **Required parameters** - Can't complete without summary
2. **Response enrichment** - Remind about updates
3. **Templates** - Make it easy to remember what to track
4. **Time-based reminders** - Alert when updates are stale

## Summary

The vision system works by:
- **Requiring** manual summaries at task completion
- **Reminding** AI to update context through enriched responses
- **Providing** templates to make updates easier
- **Tracking** update freshness to identify stale context

This is a **manual process** that requires AI discipline, not automatic tracking!