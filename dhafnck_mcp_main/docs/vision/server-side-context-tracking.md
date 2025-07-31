# Server-Side Context Tracking for Stateless AI Clients

## The Constraint

- **Server**: Runs in Docker, only knows about MCP tool calls
- **AI Clients**: Work independently (Cursor, Claude Code), server can't see their actions
- **Challenge**: Need to ensure context/vision updates without tracking client-side activity

## Solution: Context-Aware MCP Tools

### 1. Make Every MCP Tool Context-Aware

Instead of tracking client actions, make each server tool automatically update context:

```python
class ContextAwareMCPTools:
    """Wrap existing tools to auto-update context"""
    
    def __init__(self, original_tool, context_manager):
        self._original_tool = original_tool
        self._context_manager = context_manager
        self._current_task_context = {}
    
    async def enhanced_manage_task(self, action: str, **kwargs):
        """Enhanced task management that tracks context"""
        
        # Store task context for other tools
        if action in ["get", "next"]:
            result = await self._original_tool(action=action, **kwargs)
            if result.get("success") and result.get("task"):
                self._current_task_context[result["task"]["id"]] = {
                    "started_at": datetime.now(),
                    "last_action": action
                }
        
        # Auto-update context on task modifications
        elif action == "update":
            task_id = kwargs.get("task_id")
            if task_id:
                # Record what was updated
                context_update = {
                    "progress": {
                        "completed_actions": [f"Updated task: {kwargs}"],
                        "last_update": datetime.now().isoformat()
                    }
                }
                await self._context_manager.auto_update(task_id, context_update)
        
        return await self._original_tool(action=action, **kwargs)
```

### 2. Require Context with Each Significant Action

Make context updates part of the tool parameters:

```python
@mcp.tool()
async def manage_task(
    action: str,
    task_id: Optional[str] = None,
    # NEW: Context parameters included in task operations
    work_summary: Optional[str] = None,  # What was done
    progress_notes: Optional[str] = None,  # Current progress
    insights_found: Optional[List[str]] = None,  # Discoveries
    **kwargs
) -> Dict[str, Any]:
    """Task management with built-in context tracking"""
    
    # If work_summary provided, auto-update context
    if work_summary and task_id:
        await update_context_from_summary(task_id, work_summary, progress_notes, insights_found)
    
    # Continue with normal task operation
    return await original_manage_task(action, task_id, **kwargs)
```

### 3. Session-Based Progress Tracking

Track progress within MCP session:

```python
class MCPSessionTracker:
    """Track AI work within MCP session"""
    
    def __init__(self):
        self._sessions = {}  # session_id -> work_data
    
    async def track_tool_call(self, session_id: str, tool_name: str, params: Dict):
        """Track each MCP tool call"""
        
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "started": datetime.now(),
                "task_id": None,
                "tool_calls": []
            }
        
        session = self._sessions[session_id]
        
        # Extract task context
        if "task_id" in params:
            session["task_id"] = params["task_id"]
        
        # Record tool usage
        session["tool_calls"].append({
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "params": self._sanitize_params(params)
        })
        
        # Auto-generate context after N calls
        if len(session["tool_calls"]) >= 5 and session["task_id"]:
            await self._generate_context_from_calls(session)
```

### 4. Progressive Context Building

Build context progressively from MCP calls:

```python
@mcp.tool()
async def report_progress(
    task_id: str,
    action_type: str,  # "code_change", "test_run", "analysis", etc.
    description: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Simple progress reporting that builds context"""
    
    # Map action types to context sections
    context_mapping = {
        "code_change": "technical.changes",
        "test_run": "progress.test_results",
        "analysis": "notes.agent_insights",
        "bug_fix": "progress.completed_actions",
        "refactor": "technical.architecture_notes"
    }
    
    # Build context update
    context_section = context_mapping.get(action_type, "notes.general")
    await append_to_context(task_id, context_section, description, details)
    
    return {"success": True, "context_updated": True}
```

### 5. Completion Checklist

Require specific information at completion:

```python
@mcp.tool()
async def complete_task(
    task_id: str,
    # Required completion information
    what_was_accomplished: str,
    how_it_was_tested: Optional[str] = None,
    known_issues: Optional[List[str]] = None,
    recommended_next_steps: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Complete task with required context information"""
    
    # Build final context update
    final_context = {
        "progress": {
            "completion_summary": what_was_accomplished,
            "testing_notes": how_it_was_tested or "Not specified",
            "completion_percentage": 100
        },
        "notes": {
            "known_issues": known_issues or [],
            "recommendations": recommended_next_steps or []
        }
    }
    
    # Update context first
    await update_context(task_id, final_context)
    
    # Then complete
    return await complete_task_internal(task_id)
```

### 6. Context Templates in Responses

Provide pre-filled context templates:

```python
def enhance_task_response(task: Dict[str, Any]) -> Dict[str, Any]:
    """Add context helpers to task response"""
    
    task["context_helpers"] = {
        "report_code_change": {
            "tool": "report_progress",
            "template": {
                "task_id": task["id"],
                "action_type": "code_change",
                "description": "Modified [FILE] to [WHAT YOU DID]"
            }
        },
        "report_test": {
            "tool": "report_progress",
            "template": {
                "task_id": task["id"],
                "action_type": "test_run",
                "description": "Ran tests: [PASS/FAIL] - [DETAILS]"
            }
        },
        "quick_complete": {
            "tool": "complete_task",
            "template": {
                "task_id": task["id"],
                "what_was_accomplished": "[SUMMARY]",
                "how_it_was_tested": "[TEST METHOD]"
            }
        }
    }
    
    return task
```

## Implementation Strategy

### Phase 1: Modify Existing Tools
- Add optional context parameters to all task tools
- Make `complete_task` require summary information
- Auto-update context when parameters provided

### Phase 2: Add Progress Reporting Tools
- `report_progress` - Simple progress updates
- `report_insight` - Capture discoveries
- `checkpoint_work` - Save work state

### Phase 3: Session Tracking
- Track MCP calls within session
- Generate context from call patterns
- Remind about updates based on activity

## Expected AI Workflow

```python
# 1. AI gets task (server tracks this)
task = await mcp.manage_task(action="next")

# 2. AI reports progress (simple!)
await mcp.report_progress(
    task_id=task["id"],
    action_type="code_change",
    description="Added caching to API endpoints"
)

# 3. AI runs tests
await mcp.report_progress(
    task_id=task["id"],
    action_type="test_run",
    description="All tests passing, performance improved by 50%"
)

# 4. AI completes with required info
await mcp.complete_task(
    task_id=task["id"],
    what_was_accomplished="Implemented Redis caching for all API endpoints",
    how_it_was_tested="Unit tests + performance benchmarks",
    recommended_next_steps=["Monitor cache hit rates", "Add cache warming"]
)
```

## Benefits

1. **No Client Tracking Needed**: Everything happens through MCP calls
2. **Progressive Context**: Builds throughout work session
3. **Required at Completion**: Can't complete without summary
4. **Simple for AI**: Just describe what you did
5. **Automatic Vision Updates**: Server calculates impact

This approach works entirely within server boundaries while ensuring context is captured.