# Detailed Workflow Guidance System Specification

## Overview

This document provides exact specifications for the `workflow_guidance` object that appears in every MCP tool response, showing AI exactly what to do at each step.

---

## 1. Core Structure

Every response includes this structure:

```json
{
    "success": true/false,
    "task": {...},  // Only on success
    "error": "...",  // Only on failure
    "workflow_guidance": {
        "current_state": {...},
        "rules": [...],
        "next_actions": [...],
        "hints": [...],
        "warnings": [...],
        "examples": {...}
    }
}
```

---

## 2. Task Lifecycle Workflow Guidance

### 2.1 Getting a New Task (Status: TODO)

**Action**: `manage_task(action="next")` or `manage_task(action="get", task_id="123")`

**Success Response**:
```json
{
    "success": true,
    "task": {
        "id": "task_123",
        "title": "Implement caching layer",
        "status": "todo",
        "completion_percentage": 0
    },
    "workflow_guidance": {
        "current_state": {
            "phase": "not_started",
            "status": "todo",
            "progress": 0,
            "has_context": false,
            "has_subtasks": false,
            "can_complete": false,
            "time_since_update": null
        },
        "rules": [
            "🚀 REQUIRED: Update status to 'in_progress' before starting work",
            "📝 REQUIRED: Update context at least every 30 minutes while working",
            "✅ REQUIRED: Provide completion_summary to complete task",
            "📋 OPTIONAL: Break into subtasks if complex (>4 hours work)"
        ],
        "next_actions": [
            {
                "priority": "HIGH",
                "action": "Start working on the task",
                "tool": "manage_task",
                "params": {
                    "action": "update",
                    "task_id": "task_123",
                    "status": "in_progress",
                    "work_notes": "Starting analysis of caching requirements"
                },
                "reason": "Task must be marked as in_progress before work begins"
            },
            {
                "priority": "MEDIUM",
                "action": "Create subtasks if needed",
                "tool": "manage_subtask",
                "params": {
                    "action": "create",
                    "task_id": "task_123",
                    "title": "Example: Research caching solutions"
                },
                "reason": "Complex tasks benefit from breakdown"
            }
        ],
        "hints": [
            "💡 Start by understanding the requirements",
            "📖 Review existing code before implementing",
            "🔍 Check if similar caching exists elsewhere"
        ],
        "warnings": [],
        "examples": {
            "start_task": {
                "description": "Begin working on the task",
                "command": "manage_task(action='update', task_id='task_123', status='in_progress', work_notes='Analyzing caching requirements')"
            },
            "create_subtask": {
                "description": "Break down into smaller tasks",
                "command": "manage_subtask(action='create', task_id='task_123', title='Research Redis vs Memcached')"
            }
        }
    }
}
```

### 2.2 Starting Work (Status: TODO → IN_PROGRESS)

**Action**: `manage_task(action="update", task_id="123", status="in_progress", work_notes="Starting work")`

**Success Response**:
```json
{
    "success": true,
    "workflow_guidance": {
        "current_state": {
            "phase": "analysis",
            "status": "in_progress",
            "progress": 0,
            "has_context": true,
            "time_since_update": 0
        },
        "rules": [
            "📊 Update progress percentage as you complete work",
            "💡 Report insights using report_progress",
            "⏰ Update context within 30 minutes",
            "🚨 Report blockers immediately"
        ],
        "next_actions": [
            {
                "priority": "MEDIUM",
                "action": "Report initial progress",
                "tool": "report_progress",
                "params": {
                    "task_id": "task_123",
                    "progress_type": "analysis",
                    "description": "Completed requirements analysis",
                    "percentage_complete": 20
                },
                "reason": "Track progress through task phases"
            }
        ],
        "hints": [
            "✅ Task now in progress - good start!",
            "🎯 Focus on understanding before implementing",
            "📝 Use quick_task_update for simple progress reports"
        ],
        "warnings": [],
        "examples": {
            "quick_update": {
                "description": "Simple progress update",
                "command": "quick_task_update(task_id='task_123', what_i_did='Analyzed existing code', progress_percentage=20)"
            }
        }
    }
}
```

### 2.3 Mid-Work Progress Update

**Action**: `report_progress(task_id="123", progress_type="implementation", description="Added Redis client", percentage_complete=50)`

**Success Response**:
```json
{
    "success": true,
    "workflow_guidance": {
        "current_state": {
            "phase": "implementation",
            "status": "in_progress",
            "progress": 50,
            "has_context": true,
            "time_since_update": 0
        },
        "rules": [
            "🧪 Test as you implement",
            "📝 Document significant decisions",
            "⚡ Update on major milestones"
        ],
        "next_actions": [
            {
                "priority": "LOW",
                "action": "Continue implementation",
                "tool": "Continue with your work",
                "reason": "You're making good progress"
            },
            {
                "priority": "MEDIUM",
                "action": "If you hit a blocker",
                "tool": "report_progress",
                "params": {
                    "task_id": "task_123",
                    "progress_type": "debugging",
                    "description": "Describe the issue"
                }
            }
        ],
        "hints": [
            "🎯 50% complete - halfway there!",
            "💪 Keep the momentum going",
            "🔄 Remember to commit your changes"
        ],
        "warnings": [],
        "examples": {}
    }
}
```

### 2.4 Near Completion (Progress > 80%)

**Action**: `quick_task_update(task_id="123", what_i_did="Finished implementation, testing now", progress_percentage=90)`

**Success Response**:
```json
{
    "success": true,
    "workflow_guidance": {
        "current_state": {
            "phase": "finalizing",
            "status": "in_progress",
            "progress": 90,
            "has_context": true,
            "has_subtasks": true,
            "subtasks_complete": 2,
            "subtasks_total": 3,
            "can_complete": false
        },
        "rules": [
            "✅ All subtasks must be complete before parent task",
            "📝 Completion requires 'completion_summary'",
            "🧪 Ensure all tests pass",
            "📚 Update documentation if needed"
        ],
        "next_actions": [
            {
                "priority": "HIGH",
                "action": "Complete remaining subtask",
                "tool": "manage_subtask",
                "params": {
                    "action": "list",
                    "task_id": "task_123"
                },
                "reason": "1 subtask still incomplete"
            },
            {
                "priority": "MEDIUM",
                "action": "Prepare for completion",
                "tool": "Think about your completion summary",
                "reason": "You'll need this for task completion"
            }
        ],
        "hints": [
            "🏁 Almost done! Just 1 subtask remaining",
            "📋 Review all work before completing",
            "💭 Think about next recommendations"
        ],
        "warnings": [
            "⚠️ Cannot complete parent task until all subtasks are done",
            "📝 Remember: completion_summary is required"
        ],
        "examples": {
            "check_subtasks": {
                "description": "See remaining subtasks",
                "command": "manage_subtask(action='list', task_id='task_123')"
            }
        }
    }
}
```

### 2.5 Task Completion

**Action**: `manage_task(action="complete", task_id="123", completion_summary="Implemented Redis caching")`

**Success Response**:
```json
{
    "success": true,
    "workflow_guidance": {
        "current_state": {
            "phase": "completed",
            "status": "done",
            "progress": 100
        },
        "rules": [],
        "next_actions": [
            {
                "priority": "HIGH",
                "action": "Get your next task",
                "tool": "manage_task",
                "params": {
                    "action": "next",
                    "git_branch_id": "main"
                },
                "reason": "Continue with next priority task"
            },
            {
                "priority": "LOW",
                "action": "Review completed work",
                "tool": "manage_task",
                "params": {
                    "action": "get",
                    "task_id": "task_123",
                    "include_context": true
                }
            }
        ],
        "hints": [
            "🎉 Great job! Task completed successfully",
            "🚀 Ready for your next challenge?",
            "📊 Your progress updates were helpful"
        ],
        "warnings": [],
        "examples": {
            "next_task": {
                "description": "Get next priority task",
                "command": "manage_task(action='next')"
            }
        }
    }
}
```

---

## 3. Error Scenarios

### 3.1 Attempting to Complete Without Context Update

**Action**: `manage_task(action="complete", task_id="123")`

**Error Response**:
```json
{
    "success": false,
    "error": "Cannot complete task without completion_summary",
    "error_code": "MISSING_REQUIRED_PARAMETER",
    "workflow_guidance": {
        "current_state": {
            "phase": "finalizing",
            "status": "in_progress",
            "progress": 90,
            "has_context": true,
            "missing_requirements": ["completion_summary"]
        },
        "rules": [
            "❌ BLOCKED: completion_summary is REQUIRED",
            "📝 Describe what you accomplished",
            "💡 Optional: Add testing_notes and next_recommendations"
        ],
        "next_actions": [
            {
                "priority": "CRITICAL",
                "action": "Add completion summary and retry",
                "tool": "manage_task",
                "params": {
                    "action": "complete",
                    "task_id": "task_123",
                    "completion_summary": "Describe what you accomplished",
                    "testing_notes": "How you tested (optional)",
                    "next_recommendations": ["Future improvements (optional)"]
                },
                "reason": "Completion summary is required"
            },
            {
                "priority": "HIGH",
                "action": "Or use combined completion",
                "tool": "complete_task_with_update",
                "params": {
                    "task_id": "task_123",
                    "completion_summary": "What was done",
                    "completed_actions": ["List of actions"],
                    "insights": ["Any discoveries"]
                },
                "reason": "Updates context and completes in one call"
            }
        ],
        "hints": [
            "💡 The completion_summary helps track what was accomplished",
            "📝 Be specific about what you implemented",
            "🎯 This creates valuable documentation"
        ],
        "warnings": [
            "⚠️ Task cannot be completed without summary"
        ],
        "examples": {
            "minimal_complete": {
                "description": "Simplest way to complete",
                "command": "manage_task(action='complete', task_id='task_123', completion_summary='Implemented caching with Redis')"
            },
            "detailed_complete": {
                "description": "Complete with full details",
                "command": "complete_task_with_update(task_id='task_123', completion_summary='Added Redis caching layer', completed_actions=['Configured Redis', 'Implemented cache logic', 'Added tests'], testing_notes='All tests pass, 50% performance improvement')"
            }
        }
    }
}
```

### 3.2 Attempting to Complete with Incomplete Subtasks

**Action**: `manage_task(action="complete", task_id="123", completion_summary="Done")`

**Error Response**:
```json
{
    "success": false,
    "error": "Cannot complete task with incomplete subtasks",
    "error_code": "INCOMPLETE_SUBTASKS",
    "incomplete_subtasks": [
        {"id": "sub_789", "title": "Write tests", "status": "in_progress"}
    ],
    "workflow_guidance": {
        "current_state": {
            "phase": "blocked",
            "subtasks_complete": 2,
            "subtasks_total": 3,
            "blocking_subtasks": ["sub_789"]
        },
        "rules": [
            "❌ ALL subtasks must be completed first",
            "📋 Parent task completion requires 100% subtask completion"
        ],
        "next_actions": [
            {
                "priority": "CRITICAL",
                "action": "Complete the remaining subtask",
                "tool": "complete_subtask_with_update",
                "params": {
                    "task_id": "task_123",
                    "subtask_id": "sub_789",
                    "completion_summary": "What was done for this subtask"
                },
                "reason": "Subtask 'Write tests' is still in progress"
            },
            {
                "priority": "HIGH",
                "action": "Check subtask status",
                "tool": "manage_subtask",
                "params": {
                    "action": "get",
                    "task_id": "task_123",
                    "subtask_id": "sub_789"
                }
            }
        ],
        "hints": [
            "🔍 Focus on completing 'Write tests' subtask",
            "📊 Parent will be 100% when all subtasks done",
            "💡 Parent progress updates automatically"
        ],
        "warnings": [
            "⚠️ Parent task blocked by incomplete subtask"
        ],
        "examples": {
            "complete_subtask": {
                "description": "Complete the blocking subtask",
                "command": "complete_subtask_with_update(task_id='task_123', subtask_id='sub_789', completion_summary='Added unit tests for cache logic')"
            }
        }
    }
}
```

### 3.3 Task Not Updated Recently (Stale)

**Action**: `manage_task(action="get", task_id="123")`

**Success Response with Warning**:
```json
{
    "success": true,
    "task": {...},
    "workflow_guidance": {
        "current_state": {
            "phase": "implementation",
            "status": "in_progress",
            "progress": 60,
            "time_since_update": 2400  // 40 minutes
        },
        "rules": [
            "⏰ OVERDUE: Context should be updated every 30 minutes",
            "📝 Provide progress update immediately"
        ],
        "next_actions": [
            {
                "priority": "CRITICAL",
                "action": "Update progress now",
                "tool": "quick_task_update",
                "params": {
                    "task_id": "task_123",
                    "what_i_did": "Describe recent work",
                    "progress_percentage": 60
                },
                "reason": "No updates in 40 minutes (30 min limit)"
            }
        ],
        "hints": [
            "⏰ Task appears stale - update needed",
            "💡 Even small updates are valuable",
            "📝 Helps track work patterns"
        ],
        "warnings": [
            "⚠️ Task hasn't been updated in 40 minutes",
            "⏰ Updates should happen every 30 minutes"
        ],
        "examples": {
            "quick_update": {
                "description": "Quick progress report",
                "command": "quick_task_update(task_id='task_123', what_i_did='Implemented cache invalidation logic', progress_percentage=70)"
            }
        }
    }
}
```

---

## 4. Subtask-Specific Guidance

### 4.1 Working on Subtasks

**Action**: `manage_subtask(action="update", task_id="parent_123", subtask_id="sub_456", status="in_progress")`

**Success Response**:
```json
{
    "success": true,
    "parent_progress": 33,  // Automatically calculated
    "workflow_guidance": {
        "current_state": {
            "subtask_status": "in_progress",
            "parent_task_id": "parent_123",
            "parent_progress": 33,
            "sibling_subtasks": {
                "total": 3,
                "completed": 1,
                "in_progress": 1,
                "todo": 1
            }
        },
        "rules": [
            "🔄 Parent progress updates automatically",
            "📝 Subtask updates appear in parent context",
            "✅ Complete subtasks to advance parent"
        ],
        "next_actions": [
            {
                "priority": "MEDIUM",
                "action": "Work on this subtask",
                "tool": "quick_subtask_update",
                "params": {
                    "task_id": "parent_123",
                    "subtask_id": "sub_456",
                    "what_i_did": "Your progress",
                    "subtask_progress": 50
                }
            }
        ],
        "hints": [
            "📊 Parent is now 33% complete",
            "🎯 Focus on completing this subtask",
            "💡 Parent context includes your updates"
        ]
    }
}
```

---

## 5. Special Scenarios

### 5.1 High Priority/Strategic Task

**Response Enhancement**:
```json
{
    "workflow_guidance": {
        "current_state": {
            "strategic_importance": "HIGH",
            "vision_alignment": 0.95
        },
        "rules": [
            "⭐ HIGH PRIORITY: Align with vision objectives",
            "📊 Track KPI impact carefully",
            "💡 Consider innovation opportunities"
        ],
        "hints": [
            "⭐ This task has high strategic importance",
            "🎯 Focus on KPI: response_time < 200ms",
            "💡 Innovation opportunity: Consider microservices"
        ]
    }
}
```

### 5.2 Blocked Task

**Response Enhancement**:
```json
{
    "workflow_guidance": {
        "current_state": {
            "phase": "blocked",
            "blockers": ["Waiting for API credentials"]
        },
        "next_actions": [
            {
                "priority": "HIGH",
                "action": "Document the blocker",
                "tool": "checkpoint_work",
                "params": {
                    "task_id": "task_123",
                    "current_state": "Implemented client, waiting for credentials",
                    "next_steps": ["Test with credentials", "Deploy"],
                    "blockers": ["Need production API keys"]
                }
            },
            {
                "priority": "HIGH",
                "action": "Work on something else",
                "tool": "manage_task",
                "params": {
                    "action": "next"
                }
            }
        ]
    }
}
```

---

## 6. Adaptive Hint Logic

The system adapts hints based on:

### Context Factors
- **Time of day**: Morning vs afternoon hints
- **Progress rate**: Encouragement vs gentle push
- **Error frequency**: More detailed examples
- **Task complexity**: Breakdown suggestions

### Examples:
```javascript
// Slow progress
hints: ["🐢 Take your time to understand the problem", "💡 Consider breaking this down further"]

// Fast progress  
hints: ["🚀 Great pace!", "🎯 You're flying through this"]

// Many errors
hints: ["📚 Check the documentation", "💡 Try a simpler approach first"]

// First task
hints: ["👋 Welcome! Take time to explore", "📖 Review related code first"]
```

---

## 7. Implementation Notes

### Response Enhancement Pipeline

```python
def enhance_response(base_response, action, context):
    # 1. Analyze current state
    state = analyze_task_state(base_response)
    
    # 2. Apply rules engine
    rules = get_rules_for_state(state, action)
    
    # 3. Generate next actions
    next_actions = suggest_next_actions(state, context)
    
    # 4. Create contextual hints
    hints = generate_hints(state, context, user_history)
    
    # 5. Check for warnings
    warnings = check_warnings(state)
    
    # 6. Build examples
    examples = get_relevant_examples(state, action)
    
    # 7. Assemble guidance
    base_response["workflow_guidance"] = {
        "current_state": state,
        "rules": rules,
        "next_actions": next_actions,
        "hints": hints,
        "warnings": warnings,
        "examples": examples
    }
    
    return base_response
```

---

## Summary

The workflow_guidance system ensures AI always knows:
1. **Where they are** (current_state)
2. **What rules apply** (rules)  
3. **What to do next** (next_actions with exact params)
4. **Helpful context** (hints)
5. **What to avoid** (warnings)
6. **How to do it** (examples)

Every response guides the AI to the next correct action, making it impossible to get lost in the workflow.