# AI Implementation Guide - Quick Reference

## For AI Working on Each Phase

### 🤖 Phase 1: Enforce Context Updates

**Your Task**: Make it impossible to complete tasks without context updates.

**Read First**:
- `automatic-context-vision-updates.md` → Section: "Block Task Completion Without Updates"

**Edit This File**:
```python
src/fastmcp/task_management/interface/controllers/task_mcp_controller.py
```

**Add These Parameters**:
```python
async def manage_task(
    action: str,
    task_id: Optional[str] = None,
    # ADD THESE:
    work_notes: Optional[str] = None,
    progress_made: Optional[str] = None, 
    completion_summary: Optional[str] = None,  # REQUIRED for complete
    **kwargs
):
```

**Key Logic to Add**:
```python
if action == "complete":
    if not completion_summary:
        return {
            "success": False,
            "error": "Cannot complete without completion_summary",
            "example": {
                "action": "complete",
                "task_id": task_id,
                "completion_summary": "Describe what you did"
            }
        }
```

**Test Your Work**:
```python
# This should FAIL:
mcp.manage_task(action="complete", task_id="123")

# This should SUCCEED:
mcp.manage_task(
    action="complete",
    task_id="123", 
    completion_summary="Fixed the bug"
)
```

---

### 🤖 Phase 2: Add Progress Tools

**Your Task**: Create simple tools for progress updates.

**Read First**:
- `server-side-context-tracking.md` → Section: "Progressive Context Building"

**Create This File**:
```python
src/fastmcp/task_management/interface/controllers/progress_tools_controller.py
```

**Implement These Tools**:
```python
@mcp.tool()
async def report_progress(
    task_id: str,
    progress_type: str,  # "analysis", "implementation", "testing"
    description: str,
    percentage_complete: Optional[int] = None
):
    # Map to context automatically
    # No complex context structure needed

@mcp.tool()  
async def quick_task_update(
    task_id: str,
    what_i_did: str,
    progress_percentage: int
):
    # Super simple interface
```

**Register Tools** in main controller setup.

---

### 🤖 Phase 3: Add Workflow Hints

**Your Task**: Make every response tell AI what to do next.

**Read First**:
- `workflow-hints-and-rules.md` → **Read entire document**

**Create This File**:
```python
src/fastmcp/task_management/interface/controllers/workflow_hint_enhancer.py
```

**Key Method**:
```python
def enhance_task_response(self, response, action, task_state):
    response["workflow_guidance"] = {
        "current_state": {...},
        "rules": ["📝 Update every 30 min", ...],
        "next_actions": [
            {
                "action": "Update progress",
                "tool": "report_progress",
                "params": {...}  # Ready to use!
            }
        ],
        "hints": ["💡 You're 50% done"],
        "examples": {...}
    }
    return response
```

**Integrate** by wrapping ALL task responses.

---

### 🤖 Phase 4: Subtask Auto-Updates

**Your Task**: Make subtasks automatically update parent progress.

**Read First**:
- `subtask-automatic-progress-tracking.md` → **Read entire document**

**Create This File**:
```python
src/fastmcp/task_management/interface/controllers/subtask_progress_controller.py
```

**Key Features**:
1. When subtask completes → Calculate parent progress
2. When subtask updates → Add note to parent context
3. Parent can't complete until all subtasks done

**Key Tool**:
```python
@mcp.tool()
async def complete_subtask_with_update(
    task_id: str,  # Parent
    subtask_id: str,
    completion_summary: str
):
    # 1. Complete subtask
    # 2. Update parent progress (automatic!)
    # 3. Add to parent context
```

---

### 🤖 Phase 5: Vision Enrichment

**Your Task**: Include vision hierarchy in every task response.

**Read First**:
- `implementation-guide-server-enrichment.md` → **Read entire document**

**Create This Service**:
```python
src/fastmcp/vision_orchestration/vision_enrichment_service.py
```

**Key Method**:
```python
async def enrich_task_with_vision(self, task):
    task["vision"] = {
        "hierarchy": load_vision_hierarchy(),
        "alignment": calculate_alignment_score(),
        "kpis": get_current_metrics(),
        "guidance": generate_ai_guidance()
    }
    return task
```

**Update** `get_next_task()` to call enrichment.

---

## 📋 Common Patterns

### Pattern 1: Add Parameters to Existing Tools
```python
# Before:
async def manage_task(action, task_id):

# After:
async def manage_task(action, task_id, work_notes=None, completion_summary=None):
    if work_notes:
        auto_update_context(task_id, work_notes)
```

### Pattern 2: Enhance Responses
```python
# Wrap responses:
response = original_method()
response = hint_enhancer.enhance(response)
return response
```

### Pattern 3: Auto-Update Parent from Child
```python
# In subtask operations:
if action == "complete":
    update_parent_progress(parent_task_id)
    propagate_context_to_parent(parent_task_id)
```

---

## 🚨 Remember

1. **Test After Each Change** - Use the test examples
2. **Keep It Simple** - AI shouldn't need to understand complex structures
3. **Always Include Examples** - In error messages and hints
4. **Make Errors Helpful** - Include how to fix them

---

## 🎯 Success Checklist

Phase 1 ✓ = Can't complete without context
Phase 2 ✓ = Simple progress reporting works  
Phase 3 ✓ = Every response has guidance
Phase 4 ✓ = Subtasks update parents
Phase 5 ✓ = Vision in all task responses

Start with Phase 1 - it solves the main problem!