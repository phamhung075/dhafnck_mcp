# Consolidated MCP Vision Implementation Guide

> **📌 IMPORTANT**: For conflict resolution and authoritative guidance, see [SYSTEM_INTEGRATION_GUIDE.md](SYSTEM_INTEGRATION_GUIDE.md)

## Overview

This guide consolidates all vision system approaches that work within MCP server constraints:
- Server only knows about MCP tool calls
- No persistent AI sessions
- No client-side tracking
- All context through explicit MCP parameters

## Core Architecture

### 1. Vision Hierarchy (Server-Side)

The vision hierarchy exists entirely on the server and is included in task responses:

```
Organization Vision
    ↓
Project Vision  
    ↓
Branch Vision (Git Branch/Task Tree)
    ↓
Task Vision
    ↓
Subtask Vision
```

### 2. Server-Side Enrichment

When AI requests tasks, the server automatically includes:

```python
{
    "task": {
        "id": "task_123",
        "title": "Implement caching",
        # Always included context
        "context_data": { ... },
        # Vision hierarchy
        "vision": {
            "current_objectives": [...],
            "alignment_score": 0.85,
            "kpi_progress": { ... },
            "success_criteria": [...]
        },
        # AI guidance
        "ai_guidance": {
            "focus_areas": [...],
            "recommended_approach": "..."
        }
    }
}
```

### 3. Context Through MCP Parameters

All context updates happen through MCP tool parameters:

```python
# Option 1: Update with task operations
await mcp.manage_task(
    action="update",
    task_id="123",
    status="in_progress",
    work_notes="Implementing Redis cache",  # Context parameter
    progress_made="Added cache configuration"  # Context parameter
)

# Option 2: Dedicated progress reporting
await mcp.report_progress(
    task_id="123",
    progress_type="implementation",
    description="Added Redis cache layer",
    percentage_complete=75
)

# Option 3: Required at completion
await mcp.manage_task(
    action="complete",
    task_id="123",
    completion_summary="Implemented caching with Redis",  # REQUIRED
    testing_notes="All tests pass",
    next_recommendations=["Monitor cache performance"]
)
```

## Implementation Steps

### Step 1: Modify Task MCP Controller

Update the existing task controller to:
1. Default `include_context=True`
2. Add context parameters to manage_task
3. Block completion without summary

```python
# In task_mcp_controller.py

@mcp.tool()
async def manage_task(
    action: str,
    task_id: Optional[str] = None,
    # Standard parameters...
    # NEW context parameters
    work_notes: Optional[str] = None,
    progress_made: Optional[str] = None,
    completion_summary: Optional[str] = None,  # Required for complete
    **kwargs
):
    # Auto-update context if notes provided
    if work_notes or progress_made:
        await auto_update_context(task_id, work_notes, progress_made)
    
    # Block completion without summary
    if action == "complete" and not completion_summary:
        return {
            "error": "Cannot complete without completion_summary",
            "hint": "Describe what was accomplished"
        }
```

### Step 2: Add Progress Reporting Tools

Simple tools for context updates:

```python
@mcp.tool()
async def report_progress(
    task_id: str,
    progress_type: str,  # "analysis", "implementation", "testing", etc.
    description: str,
    percentage_complete: Optional[int] = None
):
    # Maps to context sections automatically
    # No AI needs to understand context structure
```

### Step 3: Enhance Context Factory

Update `ContextResponseFactory` to merge vision data:

```python
def create_unified_context(context_data, vision_data=None):
    # Existing context creation...
    
    if vision_data:
        unified_context["vision"] = {
            "current_objectives": vision_data["objectives"],
            "kpi_progress": vision_data["metrics"],
            "alignment_score": vision_data["alignment"]
        }
```

### Step 4: Configure Auto-Enrichment

```yaml
# mcp_server_config.yaml

task_management:
  default_include_context: true
  default_include_vision: true
  
  # Require summary at completion
  completion_requires_summary: true
  
  # Auto-extract context from parameters
  context_extraction:
    enabled: true
    parameter_mapping:
      work_notes: "progress.current_session_summary"
      progress_made: "progress.completed_actions"
      issues_found: "notes.challenges_encountered"
```

## Workflow Hints System

Every tool response includes guidance to ensure AI follows the correct workflow:

```json
{
    "success": true,
    "task": { ... },
    "workflow_guidance": {
        "current_state": {
            "phase": "implementation",
            "progress": 50,
            "can_complete": false
        },
        "rules": [
            "📝 Update context every 30 minutes",
            "✅ All subtasks must complete first"
        ],
        "next_actions": [
            {
                "action": "Update progress",
                "tool": "report_progress",
                "params": { /* ready to use */ }
            }
        ],
        "hints": [
            "💡 You're halfway done - keep updating progress",
            "📋 2 subtasks remaining"
        ],
        "examples": {
            "quick_update": "report_progress(task_id='123', ...)"
        }
    }
}
```

## AI Workflow

### Getting and Working on Tasks

```python
# 1. Get next task (includes vision/context)
task = await mcp.manage_task(action="next", git_branch_id="main")

# 2. Update progress while working
await mcp.report_progress(
    task_id=task["id"],
    progress_type="implementation",
    description="Added caching layer to API endpoints",
    percentage_complete=50
)

# 3. Complete with required summary
await mcp.manage_task(
    action="complete",
    task_id=task["id"],
    completion_summary="Implemented Redis caching for all endpoints",
    testing_notes="Unit tests pass, 50% performance improvement",
    next_recommendations=["Add cache warming", "Monitor hit rates"]
)
```

### Working with Subtasks

```python
# 1. Work on subtask - parent automatically updated
await mcp.manage_subtask(
    action="update",
    task_id="parent_123",  # Parent task ID
    subtask_id="sub_456",
    status="in_progress",
    work_notes="Implementing authentication"
)

# 2. Complete subtask - parent progress recalculated
await mcp.complete_subtask_with_update(
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="Authentication module complete",
    impact_on_parent="Core security feature implemented"
)
# Parent automatically updated to 33% (1 of 3 subtasks done)

# 3. Quick subtask update
await mcp.quick_subtask_update(
    task_id="parent_123",
    subtask_id="sub_789",
    what_i_did="Fixed validation bug",
    subtask_progress=75
)
# Parent context includes subtask work automatically
```

### Quick Updates

```python
# Simple progress update
await mcp.quick_update(
    task_id="123",
    what_i_did="Fixed the performance bug",
    progress=75
)

# Checkpoint for later
await mcp.checkpoint_work(
    task_id="123",
    current_state="Cache implemented, testing in progress",
    next_steps=["Run load tests", "Update docs"]
)
```

## Key Principles

1. **No State Between Calls**: Each MCP call is independent
2. **Context in Parameters**: All updates through tool parameters
3. **Progressive Building**: Context builds through multiple calls
4. **Completion Enforcement**: Can't complete without summary
5. **Server Enrichment**: Vision/context included automatically
6. **Workflow Hints**: Every response includes next actions and rules

## Benefits

- Works with any AI client (Cursor, Claude, ChatGPT)
- No client modifications needed
- Context tracked without client cooperation
- Vision alignment maintained automatically
- Simple for AI to use

## What NOT to Do

❌ Don't assume AI remembers previous conversations
❌ Don't track client-side actions
❌ Don't use event buses or subscriptions
❌ Don't require persistent AI sessions
❌ Don't use work session tokens across conversations

## Summary

This approach ensures vision/context updates by:
1. Making updates part of normal MCP calls
2. Blocking completion without context
3. Providing simple progress tools
4. Auto-enriching all responses

The AI can't forget to update context because it's required for task completion.