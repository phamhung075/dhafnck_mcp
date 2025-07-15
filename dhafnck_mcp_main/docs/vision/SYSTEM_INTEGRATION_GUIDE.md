# Vision System Integration Guide - Resolving Conflicts

## Overview

This document resolves conflicts and inconsistencies between vision documents, providing the authoritative implementation approach.

## Core Principles (Authoritative)

### 1. MCP Server Constraints
- **Stateless Operations**: Each MCP call is independent, no persistent sessions
- **Parameter-Based Context**: All updates through explicit MCP parameters
- **Server-Side Only**: No client tracking, only MCP tool calls are visible

### 2. Context Update Requirements

**AUTHORITATIVE RULE**: Context updates are **MANDATORY** for task completion.

```python
# This is REQUIRED - no exceptions:
await mcp.manage_task(
    action="complete",
    task_id="123",
    completion_summary="What was accomplished"  # MANDATORY
)

# Optional but recommended:
testing_notes="How it was tested"  # Optional
next_recommendations=["Future work"]  # Optional
```

### 3. Progress Tracking Approach

**AUTHORITATIVE APPROACH**: Hybrid automatic + manual

**For Tasks**:
- Manual progress updates through `report_progress` or task parameters
- AI explicitly provides progress percentage

**For Subtasks**:
- Automatic parent progress calculation when subtasks complete
- Formula: `completed_subtasks / total_subtasks * 100`
- In-progress subtasks count as 50% for weighted calculation

```python
# Task progress - manual
await mcp.report_progress(
    task_id="123",
    progress_type="implementation",
    description="Added feature",
    percentage_complete=75  # Manual
)

# Subtask completion - automatic parent update
await mcp.complete_subtask_with_update(
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="Done"
)
# Parent progress automatically recalculated
```

### 4. Vision Enrichment Behavior

**AUTHORITATIVE DEFAULT**: Vision is included by default when `include_context=True`

```python
# Default behavior (context includes vision):
task = await mcp.manage_task(action="next")  # include_context=True by default

# Explicit control:
task = await mcp.manage_task(
    action="get",
    task_id="123",
    include_context=True,   # Default
    include_vision=True     # Default when context included
)

# Minimal response (no vision):
task = await mcp.manage_task(
    action="get",
    task_id="123",
    include_context=False
)
```

## Standardized Naming Conventions

### Python Code (snake_case)
```python
# Functions/Methods
manage_task()
report_progress()
complete_task_with_update()
quick_task_update()

# Parameters
task_id
completion_summary
work_notes
progress_percentage

# Response fields
workflow_guidance
next_actions
vision_hierarchy
```

### Response Structure (Standardized)
```json
{
    "success": true,
    "task": {
        "id": "123",
        "context_data": {},
        "vision": {}
    },
    "workflow_guidance": {
        "current_state": {},
        "rules": [],
        "next_actions": [],
        "hints": [],
        "examples": {}
    }
}
```

## Configuration Structure

**SINGLE CONFIGURATION FILE**: `mcp_vision_config.yaml`

```yaml
# All vision configuration in one place
vision_system:
  # Core settings
  context_updates:
    require_completion_summary: true
    update_interval_minutes: 30
    auto_extract_from_params: true
  
  # Progress tracking
  progress_tracking:
    task_progress: "manual"  # Explicit updates
    subtask_progress: "automatic"  # Calculated
    weighted_calculation: true
  
  # Vision enrichment
  vision_enrichment:
    enabled: true
    include_by_default: true
    cache_ttl_seconds: 300
  
  # Workflow hints
  workflow_hints:
    enabled: true
    always_include: true
    phases:
      not_started:
        rules: ["Must update status"]
        hints: ["Begin with analysis"]
```

## Implementation File Structure

```
src/fastmcp/
├── task_management/
│   ├── interface/
│   │   └── controllers/
│   │       ├── task_mcp_controller.py          # Modified for context params
│   │       ├── subtask_mcp_controller.py       # Modified for auto-updates
│   │       ├── progress_tools_controller.py    # NEW: Progress tools
│   │       └── workflow_hint_enhancer.py       # NEW: Hint system
│   ├── application/
│   │   ├── facades/
│   │   │   └── task_application_facade.py      # Modified for vision
│   │   └── services/
│   │       └── vision_enrichment_service.py    # NEW: Vision enrichment
│   └── domain/
│       └── value_objects/
│           └── vision_objects.py                # NEW: Vision models
└── vision_orchestration/                        # NEW: Vision system
    ├── __init__.py
    └── config.py                               # Config loader
```

## Conflict Resolutions

### 1. Session vs Stateless
**RESOLUTION**: Stateless wins. No persistent sessions between MCP calls.
- Remove references to work session tokens spanning conversations
- Use task_id + timestamp for tracking within single conversation

### 2. Optional vs Required Context
**RESOLUTION**: Context updates are REQUIRED for completion.
- `completion_summary` is mandatory
- Other fields optional but recommended
- Block completion without context

### 3. Multiple Configuration Files
**RESOLUTION**: Single `mcp_vision_config.yaml` file.
- All settings in one place
- Environment-specific overrides supported
- Clear hierarchy of settings

### 4. Vision as Default vs Optional
**RESOLUTION**: Vision included by default when context requested.
- `include_context=True` (default) includes vision
- Can be disabled with `include_vision=False`
- Minimal mode with `include_context=False`

## Tool Naming (Final)

### Core Tools
- `manage_task` - Main task operations
- `manage_subtask` - Subtask operations
- `complete_task_with_update` - Complete with context
- `report_progress` - Progress updates
- `quick_task_update` - Simple updates
- `checkpoint_work` - Save work state

### Subtask-Specific
- `complete_subtask_with_update` - Complete with parent update
- `quick_subtask_update` - Simple subtask progress

## Error Response Format

```json
{
    "success": false,
    "error": "Clear error message",
    "error_code": "MISSING_CONTEXT",
    "resolution_guidance": {
        "likely_cause": "Context not updated",
        "resolution_steps": [
            "Update context first",
            "Then retry completion"
        ],
        "examples": {
            "fix": "quick_task_update(task_id='123', what_i_did='...', progress_percentage=100)"
        }
    },
    "workflow_guidance": {
        "rules": ["Context update required"],
        "next_actions": [{}]
    }
}
```

## Implementation Priority (Clarified)

1. **Phase 1**: Block completion without context (CRITICAL)
2. **Phase 2**: Add progress tools (HIGH)
3. **Phase 3**: Add workflow hints (HIGH)
4. **Phase 4**: Subtask auto-updates (MEDIUM)
5. **Phase 5**: Vision enrichment (MEDIUM)

Each phase builds on previous, but provides value independently.

## Summary

This guide provides the authoritative resolution for all conflicts:
- Context updates are MANDATORY for completion
- Progress is manual for tasks, automatic for subtasks
- Vision included by default with context
- Single configuration file approach
- Stateless MCP operations only
- Consistent snake_case naming throughout

Use this guide as the primary reference when implementing the vision system.