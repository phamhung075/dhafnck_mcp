# Automatic Context and Vision Updates - Solving the Forgetting Problem

## The Problem

AI clients (Claude Code, Cursor, etc.) consistently:
- ✅ Get tasks
- ✅ Complete work
- ✅ Move to next task
- ❌ **FORGET to update context/vision**

This breaks the entire vision system because progress isn't tracked and insights are lost.

## Solution: Multi-Layer Automatic Update System

### 1. Block Task Completion Without Updates

```python
# Modified complete_task action
@mcp.tool()
async def manage_task(
    action: str,
    task_id: str,
    # ... other params ...
) -> Dict[str, Any]:
    
    if action == "complete":
        # CHECK: Has context been updated recently?
        context_state = await check_context_update_status(task_id)
        
        if not context_state["recently_updated"]:
            return {
                "success": False,
                "error": "Cannot complete task without context update",
                "required_updates": [
                    "progress.completed_actions",
                    "progress.next_steps",
                    "notes.agent_insights"
                ],
                "hint": "Use update_task_context action first with your progress",
                "example": {
                    "action": "update_task_context",
                    "task_id": task_id,
                    "updates": {
                        "progress": {
                            "completed_actions": ["Implemented feature X", "Fixed bug Y"],
                            "completion_percentage": 100
                        },
                        "notes": {
                            "agent_insights": ["Found performance improvement opportunity"]
                        }
                    }
                }
            }
```

### 2. Automatic Context Extraction from Actions

```python
# New middleware that tracks all AI actions
class ContextExtractionMiddleware:
    """Automatically extracts context from AI tool calls"""
    
    async def track_ai_actions(self, tool_call: ToolCall, result: Any):
        # Extract meaningful updates from tool usage
        context_updates = {}
        
        # Track file modifications
        if tool_call.name in ["Edit", "Write", "MultiEdit"]:
            context_updates["technical.key_files"] = tool_call.params.get("file_path")
            context_updates["progress.completed_actions"] = f"Modified {tool_call.params.get('file_path')}"
        
        # Track code execution
        if tool_call.name == "Bash":
            command = tool_call.params.get("command")
            if "test" in command:
                context_updates["progress.completed_actions"] = "Ran tests"
            if "npm install" in command:
                context_updates["technical.dependencies"] = "Updated dependencies"
        
        # Track searches and analysis
        if tool_call.name in ["Grep", "Task"]:
            context_updates["notes.analysis"] = f"Searched for: {tool_call.params.get('pattern')}"
        
        # Auto-save to task context
        if context_updates:
            await auto_update_context(
                task_id=current_task_id,
                updates=context_updates,
                source="auto_extracted"
            )
```

### 3. Guided Update Prompts in Responses

```python
# Enhanced task response with update reminders
def enhance_task_response(task: Dict[str, Any]) -> Dict[str, Any]:
    """Add update prompts to task responses"""
    
    task["update_reminder"] = {
        "message": "🔔 Remember to update context before completing",
        "required_before_completion": True,
        "quick_update_template": {
            "action": "update_task_context",
            "task_id": task["id"],
            "updates": {
                "progress": {
                    "completed_actions": ["<DESCRIBE WHAT YOU DID>"],
                    "completion_percentage": 0,
                    "current_session_summary": "<SUMMARY OF WORK>"
                },
                "vision_updates": {
                    "metrics_affected": {
                        "<METRIC_NAME>": "<NEW_VALUE>"
                    },
                    "objectives_progress": "<PROGRESS ON OBJECTIVES>"
                }
            }
        },
        "auto_complete_with_update": {
            "action": "complete_with_context",
            "task_id": task["id"],
            "completion_summary": "<WHAT WAS ACCOMPLISHED>",
            "vision_impact": "<HOW THIS AFFECTS VISION>"
        }
    }
    
    return task
```

### 4. New Combined Actions

Create new MCP tools that combine completion with updates:

```python
@mcp.tool()
async def complete_task_with_update(
    task_id: str,
    completion_summary: str,
    completed_actions: List[str],
    insights: Optional[List[str]] = None,
    vision_impact: Optional[Dict[str, Any]] = None,
    metrics_updated: Optional[Dict[str, float]] = None,
    next_steps: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Complete task and update context in one action"""
    
    # First, update context
    context_update = {
        "progress": {
            "completed_actions": completed_actions,
            "completion_percentage": 100,
            "current_session_summary": completion_summary
        },
        "notes": {
            "agent_insights": insights or [],
            "completion_notes": completion_summary
        }
    }
    
    if vision_impact:
        context_update["vision_updates"] = vision_impact
    
    if metrics_updated:
        context_update["metrics"] = metrics_updated
    
    if next_steps:
        context_update["progress"]["next_steps"] = next_steps
    
    # Update context
    await update_task_context(task_id, context_update)
    
    # Update vision metrics if provided
    if metrics_updated:
        await update_vision_metrics(task_id, metrics_updated)
    
    # Now complete the task
    return await complete_task(task_id)

@mcp.tool()
async def quick_task_update(
    task_id: str,
    what_i_did: str,
    progress_percentage: int,
    any_issues: Optional[str] = None
) -> Dict[str, Any]:
    """Simplified update for AI clients"""
    
    updates = {
        "progress": {
            "completed_actions": [what_i_did],
            "completion_percentage": progress_percentage
        }
    }
    
    if any_issues:
        updates["notes"] = {"challenges_encountered": [any_issues]}
    
    return await update_task_context(task_id, updates)
```

### 5. Automatic Reminder System

```python
class TaskReminderSystem:
    """Reminds AI to update context"""
    
    def check_update_needed(self, task: Dict[str, Any]) -> Dict[str, Any]:
        last_update = task.get("context_data", {}).get("last_updated")
        time_since_update = datetime.now() - last_update
        
        if time_since_update > timedelta(minutes=30):
            return {
                "reminder_level": "high",
                "message": "⚠️ Context hasn't been updated in 30+ minutes",
                "suggested_action": "quick_task_update"
            }
        
        # Check if any work was done without updates
        recent_tool_calls = get_recent_tool_calls(task["id"])
        if len(recent_tool_calls) > 10:
            return {
                "reminder_level": "medium",
                "message": "📝 You've made several changes - please update context",
                "detected_changes": summarize_changes(recent_tool_calls)
            }
        
        return {"reminder_level": "none"}
```

### 6. Configuration

```yaml
# automatic_update_config.yaml

context_updates:
  # Enforce updates before completion
  require_update_before_complete: true
  update_timeout_minutes: 30
  
  # Auto-extraction from tool calls
  auto_extraction:
    enabled: true
    track_tools:
      - Edit
      - Write
      - MultiEdit
      - Bash
      - Task
    
  # Reminder system
  reminders:
    enabled: true
    intervals:
      - after_minutes: 15
        level: "gentle"
      - after_minutes: 30
        level: "strong"
      - after_minutes: 45
        level: "blocking"
    
  # Simplified update tools
  quick_update_tools:
    enabled: true
    templates:
      - name: "quick_progress"
        fields: ["what_i_did", "percentage"]
      - name: "quick_complete"
        fields: ["summary", "next_task_recommendation"]

vision_updates:
  # Auto-calculate vision impact
  auto_calculate_impact: true
  
  # Track metrics from tool usage
  metric_extraction:
    performance_tests: ["response_time", "throughput"]
    unit_tests: ["test_coverage", "test_pass_rate"]
```

## Implementation Priority

### Phase 1: Block Completion Without Updates
```python
# Immediate implementation in manage_task
if action == "complete":
    if not has_recent_context_update(task_id):
        return completion_blocked_response()
```

### Phase 2: Add Combined Actions
```python
# New tools that make updating easy
- complete_task_with_update()
- quick_task_update()
```

### Phase 3: Auto-Extraction
```python
# Track all tool calls and extract context
- Implement ContextExtractionMiddleware
- Auto-save meaningful updates
```

## Expected AI Workflow After Implementation

```python
# AI gets task
task = await mcp.manage_task(action="next")
# Response includes update reminder and templates

# AI works on task...

# AI can't complete without update
result = await mcp.manage_task(action="complete", task_id="123")
# ERROR: "Cannot complete without context update"

# AI uses quick update
await mcp.complete_task_with_update(
    task_id="123",
    completion_summary="Implemented caching layer",
    completed_actions=["Added Redis", "Optimized queries"],
    metrics_updated={"response_time_ms": 200}
)
# SUCCESS: Task completed and context updated

# Or AI uses the reminder template
await mcp.quick_task_update(
    task_id="123",
    what_i_did="Fixed the performance issue",
    progress_percentage=100
)
# Then complete
await mcp.manage_task(action="complete", task_id="123")
# SUCCESS
```

## Summary

This solution ensures AI clients CANNOT forget to update context/vision by:
1. **Blocking** task completion without updates
2. **Providing** easy update tools and templates
3. **Auto-extracting** context from AI actions
4. **Reminding** with increasing urgency
5. **Guiding** with examples in every response

The key is making updates mandatory and effortless.