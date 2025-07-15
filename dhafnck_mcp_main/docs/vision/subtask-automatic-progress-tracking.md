# Automatic Progress Tracking with Subtasks

## Overview

This document describes how to automatically update parent task progress and context when working with subtasks, ensuring the vision system tracks progress at all levels.

## The Problem

When AI works on subtasks:
- Parent task progress isn't automatically updated
- Context updates on subtasks don't propagate to parent
- Vision metrics aren't aggregated from subtask completion
- AI has to manually update both subtask and parent task

## Solution: Automatic Progress Propagation

### 1. Enhanced Subtask Management

```python
@mcp.tool()
async def manage_subtask(
    action: str,
    task_id: str,  # Parent task ID
    subtask_id: Optional[str] = None,
    title: Optional[str] = None,
    # NEW: Progress tracking parameters
    work_notes: Optional[str] = None,
    progress_made: Optional[str] = None,
    completion_summary: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Enhanced subtask management with automatic parent updates"""
    
    # Execute subtask action
    result = original_manage_subtask(action, task_id, subtask_id, **kwargs)
    
    # Auto-update parent task progress
    if result.get("success"):
        if action == "complete" and subtask_id:
            # Calculate parent progress from subtasks
            await update_parent_progress_from_subtasks(task_id)
            
            # Propagate completion context to parent
            if completion_summary:
                await add_to_parent_context(
                    task_id,
                    f"Subtask completed: {completion_summary}"
                )
        
        elif action in ["create", "update", "delete"]:
            # Recalculate parent progress
            await recalculate_parent_progress(task_id)
    
    return result
```

### 2. Automatic Progress Calculation

```python
class SubtaskProgressCalculator:
    """Calculates parent task progress from subtasks"""
    
    async def calculate_parent_progress(self, task_id: str) -> Dict[str, Any]:
        # Get all subtasks
        subtasks = await get_subtasks(task_id)
        
        if not subtasks:
            return {"percentage": 0, "method": "no_subtasks"}
        
        # Calculate progress
        completed = sum(1 for s in subtasks if s["status"] == "done")
        total = len(subtasks)
        percentage = (completed / total) * 100 if total > 0 else 0
        
        # Get parent task context
        parent_context = await get_task_context(task_id)
        
        # Update parent progress
        return {
            "percentage": percentage,
            "completed_subtasks": completed,
            "total_subtasks": total,
            "method": "subtask_aggregation",
            "details": {
                "completed": [s["title"] for s in subtasks if s["status"] == "done"],
                "in_progress": [s["title"] for s in subtasks if s["status"] == "in_progress"],
                "pending": [s["title"] for s in subtasks if s["status"] == "todo"]
            }
        }
```

### 3. Context Propagation System

```python
class ContextPropagator:
    """Propagates context updates from subtasks to parent"""
    
    async def propagate_subtask_context(
        self,
        parent_task_id: str,
        subtask_id: str,
        subtask_context: Dict[str, Any]
    ):
        # Extract relevant updates from subtask
        insights = subtask_context.get("notes", {}).get("agent_insights", [])
        completed_actions = subtask_context.get("progress", {}).get("completed_actions", [])
        challenges = subtask_context.get("notes", {}).get("challenges_encountered", [])
        
        # Build parent context update
        parent_update = {
            "progress": {
                "subtask_updates": [
                    {
                        "subtask_id": subtask_id,
                        "completed_actions": completed_actions,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            },
            "notes": {
                "subtask_insights": insights,
                "subtask_challenges": challenges
            }
        }
        
        # Update parent context
        await update_task_context(parent_task_id, parent_update)
        
        # Update vision metrics if affected
        if "metrics" in subtask_context:
            await aggregate_vision_metrics(parent_task_id, subtask_context["metrics"])
```

### 4. Enhanced MCP Tools for Subtasks

```python
@mcp.tool()
async def complete_subtask_with_update(
    task_id: str,  # Parent task ID
    subtask_id: str,
    completion_summary: str,
    impact_on_parent: Optional[str] = None,
    metrics_updated: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Complete subtask and automatically update parent"""
    
    # Update subtask context
    subtask_update = {
        "progress": {
            "completion_percentage": 100,
            "completed_actions": [completion_summary]
        }
    }
    
    # Complete the subtask
    result = await manage_subtask(
        action="complete",
        task_id=task_id,
        subtask_id=subtask_id
    )
    
    if result.get("success"):
        # Auto-update parent task
        parent_update = {
            "progress": {
                "subtask_completions": [
                    f"{subtask_id}: {completion_summary}"
                ],
                "impact": impact_on_parent or f"Completed subtask: {completion_summary}"
            }
        }
        
        if metrics_updated:
            parent_update["metrics"] = metrics_updated
        
        # Update parent context
        await update_task_context(task_id, parent_update)
        
        # Recalculate parent progress
        progress = await calculate_parent_progress(task_id)
        
        result["parent_updated"] = True
        result["parent_progress"] = progress["percentage"]
        
        # Check if all subtasks complete
        if progress["percentage"] == 100:
            result["hint"] = "All subtasks complete! Parent task ready for completion."
    
    return result

@mcp.tool()
async def quick_subtask_update(
    task_id: str,  # Parent task ID
    subtask_id: str,
    what_i_did: str,
    subtask_progress: int
) -> Dict[str, Any]:
    """Quick progress update for subtask with parent tracking"""
    
    # Update subtask
    await update_subtask_progress(subtask_id, what_i_did, subtask_progress)
    
    # Calculate weighted parent progress
    parent_progress = await calculate_weighted_parent_progress(task_id)
    
    # Add summary to parent context
    await append_to_parent_context(
        task_id,
        f"Subtask progress: {what_i_did} ({subtask_progress}%)"
    )
    
    return {
        "success": True,
        "subtask_progress": subtask_progress,
        "parent_progress": parent_progress,
        "message": f"Updated subtask and parent task automatically"
    }
```

### 5. Implementation Integration

```python
# In the existing task completion logic
async def complete_task(task_id: str, completion_summary: str):
    # Check subtasks first
    subtasks = await get_subtasks(task_id)
    incomplete_subtasks = [s for s in subtasks if s["status"] != "done"]
    
    if incomplete_subtasks:
        return {
            "success": False,
            "error": "Cannot complete task with incomplete subtasks",
            "incomplete_subtasks": [
                {"id": s["id"], "title": s["title"]} 
                for s in incomplete_subtasks
            ],
            "hint": "Complete all subtasks first or remove incomplete ones"
        }
    
    # Aggregate subtask metrics for vision
    vision_metrics = await aggregate_subtask_vision_metrics(task_id)
    
    # Complete with aggregated data
    return await complete_task_with_vision(
        task_id,
        completion_summary,
        aggregated_metrics=vision_metrics
    )
```

### 6. Configuration

```yaml
# subtask_progress_config.yaml

subtask_management:
  # Automatic parent updates
  auto_update_parent: true
  
  # Progress calculation method
  progress_calculation:
    method: "weighted"  # or "simple_percentage"
    include_in_progress: true  # Count in-progress as partial
    
  # Context propagation
  context_propagation:
    enabled: true
    propagate_insights: true
    propagate_challenges: true
    aggregate_metrics: true
    
  # Vision alignment
  vision_updates:
    cascade_from_subtasks: true
    aggregate_kpis: true
    
  # Completion rules
  completion_rules:
    require_all_subtasks_complete: true
    auto_complete_parent_when_ready: false
```

## Usage Examples

### AI Working on Subtasks

```python
# 1. Get parent task with subtasks
task = await mcp.manage_task(action="get", task_id="parent_123")
# Shows subtasks and overall progress

# 2. Work on a subtask
await mcp.quick_subtask_update(
    task_id="parent_123",
    subtask_id="sub_456",
    what_i_did="Implemented authentication module",
    subtask_progress=100
)
# Parent automatically updated to 33% (1 of 3 subtasks done)

# 3. Complete subtask with impact
await mcp.complete_subtask_with_update(
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="Authentication fully implemented",
    impact_on_parent="Core security feature complete",
    metrics_updated={"security_score": 95}
)
# Parent context and vision metrics updated

# 4. Parent task shows aggregated progress
parent = await mcp.manage_task(action="get", task_id="parent_123")
# Progress: 33%, Context includes all subtask work
```

### Automatic Progress Tracking

```python
# Creating subtasks automatically affects parent
await mcp.manage_subtask(
    action="create",
    task_id="parent_123",
    title="New subtask"
)
# Parent progress recalculated (was 100%, now 75%)

# Deleting subtask
await mcp.manage_subtask(
    action="delete",
    task_id="parent_123",
    subtask_id="sub_789"
)
# Parent progress recalculated again
```

## Benefits

1. **No Manual Updates**: Parent progress tracked automatically
2. **Context Flows Up**: Subtask insights propagate to parent
3. **Vision Alignment**: Metrics aggregate from subtasks
4. **AI-Friendly**: Simple tools that handle complexity
5. **Progress Accuracy**: Real-time progress based on actual subtask state

## Summary

This system ensures that:
- Every subtask action updates parent progress
- Context from subtasks enriches parent task
- Vision metrics aggregate automatically
- AI can focus on work, not progress tracking
- Parent task completion enforces subtask completion