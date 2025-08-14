# Workflow Hints and Rules System

## Overview

This system ensures AI follows the correct workflow by including contextual hints, rules, and next action suggestions in every MCP tool response. AI can't forget what to do next because each response tells them explicitly.

## Core Concept

Every tool response includes:
1. **Current State** - Where you are in the workflow
2. **Required Actions** - What must be done before proceeding
3. **Next Steps** - Recommended actions based on state
4. **Rules** - Constraints and requirements
5. **Examples** - Ready-to-use tool calls

## Implementation

### 1. Workflow State Tracking

```python
class WorkflowStateTracker:
    """Tracks workflow state to provide contextual hints"""
    
    def get_workflow_state(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Determine current workflow state and next actions"""
        
        state = {
            "current_phase": self._determine_phase(task),
            "completion_percentage": task.get("completion_percentage", 0),
            "has_context": task.get("context_id") is not None,
            "has_subtasks": len(task.get("subtasks", [])) > 0,
            "subtasks_complete": self._all_subtasks_complete(task),
            "last_update": task.get("last_update_time")
        }
        
        # Generate hints based on state
        state["hints"] = self._generate_hints(state)
        state["rules"] = self._get_applicable_rules(state)
        state["next_actions"] = self._suggest_next_actions(state, task)
        
        return state
    
    def _determine_phase(self, task: Dict[str, Any]) -> str:
        """Determine current workflow phase"""
        
        status = task.get("status", "todo")
        progress = task.get("completion_percentage", 0)
        
        if status == "todo" and progress == 0:
            return "not_started"
        elif status == "in_progress" and progress < 30:
            return "analysis"
        elif status == "in_progress" and progress < 70:
            return "implementation"
        elif status == "in_progress" and progress < 90:
            return "testing"
        elif status == "in_progress" and progress >= 90:
            return "finalizing"
        elif status == "review":
            return "review"
        elif status == "done":
            return "completed"
        else:
            return "unknown"
```

### 2. Enhanced Tool Response Structure

```python
class WorkflowHintEnhancer:
    """Enhances tool responses with workflow hints"""
    
    def enhance_response(self, 
                        base_response: Dict[str, Any], 
                        action: str,
                        task_state: Dict[str, Any]) -> Dict[str, Any]:
        """Add workflow hints to any tool response"""
        
        # Keep original response
        enhanced = base_response.copy()
        
        # Add workflow guidance
        enhanced["workflow_guidance"] = {
            "current_state": {
                "phase": task_state["current_phase"],
                "progress": task_state["completion_percentage"],
                "status": task_state.get("status", "unknown")
            },
            "rules": self._get_rules_for_action(action, task_state),
            "next_steps": self._get_next_steps(action, task_state),
            "warnings": self._get_warnings(action, task_state),
            "examples": self._get_examples(action, task_state)
        }
        
        # Add specific hints based on action
        if action == "get" or action == "next":
            enhanced["workflow_guidance"]["hint"] = self._get_task_start_hint(task_state)
        elif action == "update":
            enhanced["workflow_guidance"]["hint"] = self._get_update_hint(task_state)
        elif action == "complete":
            enhanced["workflow_guidance"]["hint"] = self._get_completion_hint(task_state)
        
        return enhanced
```

### 3. Action-Specific Hints and Rules

```python
# Example responses with workflow guidance

# When getting a task
{
    "success": true,
    "task": { ... },
    "workflow_guidance": {
        "current_state": {
            "phase": "not_started",
            "progress": 0,
            "status": "todo"
        },
        "rules": [
            "📋 Must update status to 'in_progress' before working",
            "📝 Must update context at least every 30 minutes",
            "✅ Must provide completion_summary to complete task"
        ],
        "next_steps": [
            {
                "action": "Start working on task",
                "tool": "manage_task",
                "params": {
                    "action": "update",
                    "task_id": "123",
                    "status": "in_progress",
                    "work_notes": "Starting analysis of requirements"
                }
            }
        ],
        "hint": "👉 This task hasn't been started. Update status to 'in_progress' first!",
        "examples": {
            "start_task": {
                "description": "Mark task as in progress",
                "call": "manage_task(action='update', task_id='123', status='in_progress', work_notes='Starting work')"
            }
        }
    }
}

# When updating progress
{
    "success": true,
    "workflow_guidance": {
        "current_state": {
            "phase": "implementation",
            "progress": 50
        },
        "rules": [
            "📊 Update progress percentage with each significant change",
            "🔍 Report any blockers or issues found",
            "💡 Share insights that might help with vision alignment"
        ],
        "next_steps": [
            {
                "action": "Continue implementation",
                "hint": "Remember to update progress when you complete major parts"
            },
            {
                "action": "If blocked",
                "tool": "report_progress",
                "params": {
                    "progress_type": "debugging",
                    "description": "Describe the blocker"
                }
            }
        ],
        "hint": "✅ Progress saved! You're halfway done. Keep updating as you work.",
        "warnings": []
    }
}

# When trying to complete without context
{
    "success": false,
    "error": "Cannot complete task without context update",
    "workflow_guidance": {
        "current_state": {
            "phase": "finalizing",
            "progress": 90,
            "missing": ["context_update", "completion_summary"]
        },
        "rules": [
            "❌ BLOCKED: Context must be updated before completion",
            "📝 REQUIRED: completion_summary parameter",
            "✅ OPTIONAL: testing_notes, next_recommendations"
        ],
        "next_steps": [
            {
                "action": "Update context first",
                "tool": "quick_task_update",
                "params": {
                    "task_id": "123",
                    "what_i_did": "Describe your work",
                    "progress_percentage": 100
                }
            },
            {
                "action": "Then complete with summary",
                "tool": "complete_task_with_update",
                "params": {
                    "task_id": "123",
                    "completion_summary": "What was accomplished",
                    "testing_notes": "How it was tested"
                }
            }
        ],
        "hint": "⚠️ You need to update context before completing. Use one of the examples above!",
        "examples": {
            "quick_complete": "complete_task_with_update(task_id='123', completion_summary='Fixed caching bug', completed_actions=['Added Redis', 'Fixed timeout'])"
        }
    }
}
```

### 4. Subtask Workflow Hints

```python
# When working with subtasks
{
    "success": true,
    "subtasks": [...],
    "workflow_guidance": {
        "current_state": {
            "parent_progress": 33,
            "subtasks_total": 3,
            "subtasks_complete": 1,
            "subtasks_in_progress": 1
        },
        "rules": [
            "🔄 Parent progress updates automatically from subtasks",
            "📋 All subtasks must complete before parent can complete",
            "💬 Subtask updates propagate to parent context"
        ],
        "next_steps": [
            {
                "action": "Work on next subtask",
                "subtask_id": "sub_456",
                "status": "todo",
                "hint": "This subtask is ready to start"
            }
        ],
        "hint": "📊 Parent task is 33% complete (1/3 subtasks done). Work on remaining subtasks.",
        "warnings": [
            "⚠️ Parent task cannot be completed until all subtasks are done"
        ]
    }
}
```

### 5. Configuration for Workflow Rules

```yaml
# workflow_hints_config.yaml

workflow_hints:
  enabled: true
  
  # Include hints in all responses
  always_include_hints: true
  
  # Workflow phases and their rules
  phases:
    not_started:
      rules:
        - "Must update status to 'in_progress' before working"
        - "Should add initial work notes"
      hints:
        - "Start by analyzing the requirements"
        - "Break down into subtasks if complex"
    
    implementation:
      rules:
        - "Update progress at least every 30 minutes"
        - "Report blockers immediately"
      hints:
        - "Remember to test as you implement"
        - "Update context with significant changes"
    
    finalizing:
      rules:
        - "Must update context before completion"
        - "Completion requires summary"
      hints:
        - "Review your work before completing"
        - "Ensure all subtasks are done"
  
  # Context requirements by progress
  context_rules:
    0-25: "optional"
    26-75: "recommended" 
    76-99: "required"
    100: "mandatory"
  
  # Time-based reminders
  reminders:
    after_minutes: 30
    message: "Remember to update task progress"
    severity: "warning"
```

### 6. Smart Hint Generation

```python
class SmartHintGenerator:
    """Generates contextual hints based on task state and history"""
    
    def generate_hints(self, task: Dict[str, Any], action: str) -> List[str]:
        hints = []
        
        # Time-based hints
        if self._is_stale(task):
            hints.append("⏰ Task hasn't been updated in 30+ minutes")
        
        # Progress-based hints
        progress = task.get("completion_percentage", 0)
        if progress == 0:
            hints.append("💡 Start by updating status to 'in_progress'")
        elif progress > 80 and not task.get("testing_notes"):
            hints.append("🧪 Consider adding testing notes before completion")
        
        # Subtask hints
        if task.get("subtasks"):
            incomplete = self._count_incomplete_subtasks(task)
            if incomplete > 0:
                hints.append(f"📋 {incomplete} subtasks remaining")
        
        # Vision alignment hints
        if task.get("vision", {}).get("strategic_importance") == "high":
            hints.append("⭐ High strategic importance - focus on vision alignment")
        
        # Action-specific hints
        if action == "complete" and not task.get("context_id"):
            hints.append("❌ Update context before completing (required)")
        
        return hints
```

## Usage Examples

### AI Gets Task Response
```python
response = await mcp.manage_task(action="next")
# Response includes:
# - Current workflow phase
# - Required next actions
# - Ready-to-use examples
# - Warnings about blockers
```

### AI Updates Progress
```python
response = await mcp.report_progress(...)
# Response includes:
# - Confirmation of update
# - Reminder of next steps
# - Time until next required update
# - Suggestions based on progress
```

### AI Tries Invalid Action
```python
response = await mcp.manage_task(action="complete", task_id="123")
# Response includes:
# - Clear error explanation
# - Required steps to fix
# - Example commands to run
# - Alternative approaches
```

## Benefits

1. **AI Can't Forget**: Every response includes next steps
2. **Self-Documenting**: Examples in every response
3. **Error Prevention**: Warnings before problems occur
4. **Workflow Enforcement**: Rules clearly stated
5. **Context Aware**: Hints change based on task state

## Summary

This system ensures AI follows the correct workflow by:
- Including explicit next steps in every response
- Providing ready-to-use examples
- Showing warnings before errors occur
- Adapting hints based on current state
- Making rules clear and actionable

The AI literally cannot forget what to do next because every tool response tells them!