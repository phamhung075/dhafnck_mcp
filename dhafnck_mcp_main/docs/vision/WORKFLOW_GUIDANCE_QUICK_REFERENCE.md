# Workflow Guidance Quick Reference

## 🎯 What AI Sees in Every Response

```json
{
    "success": true/false,
    "workflow_guidance": {
        "current_state": { /* where you are */ },
        "rules": [ /* what you must follow */ ],
        "next_actions": [ /* what to do next */ ],
        "hints": [ /* helpful tips */ ],
        "warnings": [ /* what to watch out for */ ],
        "examples": { /* exact commands */ }
    }
}
```

---

## 📋 Common Scenarios & Guidance

### 1️⃣ Starting a New Task

**You see**:
```json
{
    "current_state": {
        "phase": "not_started",
        "status": "todo"
    },
    "next_actions": [{
        "action": "Start working on the task",
        "params": {
            "action": "update",
            "status": "in_progress",
            "work_notes": "Starting work"
        }
    }]
}
```

**You do**: Update status to start working

---

### 2️⃣ Task Needs Progress Update (Stale)

**You see**:
```json
{
    "warnings": ["⚠️ Task hasn't been updated in 40 minutes"],
    "next_actions": [{
        "priority": "CRITICAL",
        "action": "Update progress now",
        "params": {
            "what_i_did": "Describe recent work",
            "progress_percentage": 70
        }
    }]
}
```

**You do**: Use quick_task_update immediately

---

### 3️⃣ Ready to Complete Task

**You see**:
```json
{
    "current_state": {
        "phase": "finalizing",
        "progress": 90,
        "can_complete": true
    },
    "next_actions": [{
        "action": "Complete the task",
        "params": {
            "completion_summary": "What was accomplished"
        }
    }]
}
```

**You do**: Complete with summary

---

### 4️⃣ Blocked by Incomplete Subtasks

**You see**:
```json
{
    "error": "Cannot complete task with incomplete subtasks",
    "current_state": {
        "subtasks_complete": 2,
        "subtasks_total": 3
    },
    "next_actions": [{
        "priority": "CRITICAL",
        "action": "Complete the remaining subtask",
        "params": {
            "subtask_id": "sub_789"
        }
    }]
}
```

**You do**: Complete blocking subtask first

---

### 5️⃣ Missing Required Parameter

**You see**:
```json
{
    "error": "Cannot complete without completion_summary",
    "examples": {
        "minimal_complete": {
            "command": "manage_task(action='complete', task_id='123', completion_summary='Fixed caching bug')"
        }
    }
}
```

**You do**: Copy example and modify

---

## 🚦 Priority Indicators

- **CRITICAL** 🔴 - Do this immediately
- **HIGH** 🟡 - Do this next
- **MEDIUM** 🟢 - Do when convenient  
- **LOW** ⚪ - Optional

---

## 📊 Task Phases & What They Mean

| Phase | Progress | What to Focus On |
|-------|----------|------------------|
| `not_started` | 0% | Update status to begin |
| `analysis` | 0-25% | Understanding the problem |
| `implementation` | 25-75% | Building the solution |
| `finalizing` | 75-99% | Testing and cleanup |
| `completed` | 100% | Get next task |

---

## 🎯 Quick Decision Tree

```
Task Status?
├─ TODO → Update status to "in_progress"
├─ IN_PROGRESS
│  ├─ Last update > 30min → Update progress NOW
│  ├─ Progress < 90% → Continue working
│  └─ Progress >= 90% → Check subtasks
│      ├─ All complete → Complete task
│      └─ Some incomplete → Complete subtasks
└─ BLOCKED → Document blocker & switch tasks
```

---

## 💡 Key Rules to Remember

1. **Can't complete without `completion_summary`**
2. **Must update every 30 minutes**
3. **All subtasks must be done before parent**
4. **Parent progress updates automatically from subtasks**
5. **Always check `next_actions` - it has exact params**

---

## 🔧 Most Used Tools

### Quick Progress Update
```python
quick_task_update(
    task_id="123",
    what_i_did="Built the API endpoint",
    progress_percentage=60
)
```

### Complete Task
```python
manage_task(
    action="complete",
    task_id="123",
    completion_summary="Implemented user authentication"
)
```

### Complete Subtask (Auto-updates Parent)
```python
complete_subtask_with_update(
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="Added unit tests"
)
```

---

## 🚨 Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "Cannot complete without completion_summary" | Add `completion_summary` parameter |
| "Cannot complete with incomplete subtasks" | Complete all subtasks first |
| "Context must be updated" | Use `quick_task_update` before completing |
| "Task not found" | Check task_id is correct |

---

## 📝 Remember

**Every response tells you**:
- WHERE you are (`current_state`)
- WHAT rules apply (`rules`)
- WHAT to do next (`next_actions`)
- Ready-to-use examples (`examples`)

**Just follow the `next_actions` - they have everything you need!**