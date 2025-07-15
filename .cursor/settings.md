---
description: Core settings and workflow configuration
globs:
alwaysApply: true
tags: [init, sync, GLOBAL-RULE, TASK-MANAGEMENT, AGENT-MANAGEMENT, continue]
---
## Step 1: ⚙️ Core System Initialization (`load_core`)
#core
### 🪄 What it does:

Loads and activates **Core Mechanic Systems**, **Task Management**, and **Agent Information**.

### 🖥️ Display:

```txt
"Loading Core Content..."
```

### 🧩 Steps:

1. Load the core rule file:

   ```ts
   manage_rule({ action: "load_core", target: "ultimate.md" })
   ```

   Save if not exist the core content exact to :

   ```
   .cursor/rules/ultimate.core.md
   ```

   Add the metadata block below to that file to avoid future reloads:

   ```yaml
   ---
   description: Core Task Management System
   alwaysApply: true
   globs:
   Loading core: saved, no reload needed
   ---
   ```

   2. Parse & apply:

   * Core Mechanic Systems
   * Core Task Management logic
   * Agent information → stored in session memory


2. Update session memory with parsed info

---

## Step 2: 🧑 Default User Behavior Handling

## 🧠 Context Consistency Rule

**Always ensure** the following context parameters are synchronized for reliable session operations:

* ✅ `user_id` is consistent
* ✅ `project_name` is consistent
* ✅ `git_branch_name` is consistent

### 🧪 CASE 1: If user inputs `init` or `sync`

```tags
#init #sync
```

Steps:

0. Ensure core is loaded before continue

1. Clear individual cursor memory

2. Execute in terminal:

   ```bash
   .cursor/env.dhafnck_mcp.sh
   ```

   (updates memory with environment settings)

3. If `.git` doesn't exist, initialize Git:

   ```bash
   git init && git add . && git commit -m "Initial project with dhafnck_mcp"
   ```

---

### 🔁 CASE 2: If user inputs `continue` or `next`

```tags
#continue
```

Steps:

0. Ensure core is loaded before continue

1. Use task manager tool:

   ```ts
   dhafnck_mcp_http.manage_task({ action: "next" })
   ```

2. Assign agent via:

   ```ts
   call_agent()
   ```

3. Agent takes over → continues the task

4. Agent must:

   * ✅ Update context before finishing the task
   * ✅ Create or update documents needed to **resume or document the task**

5. Loop:

   * Go back to step 2 if there's a new task to fetch

### 🔁 CASE 3: If user demande something : research, analyze, debug, correct code, developpe or anything else

0. Ensure core is loaded before continue
1. Call agent with adapte competence and switch role to this agent for do task
2. If task complex or large try to call task agent make task plan complete and assigne to other agent for working
3. Alway call_agent to do task

---

## Step 3 : 📄 Understand Documentation Format

All documents must follow this [template format](document.md).
It ensures clarity, consistency, and automation compatibility.

---

## Step 4: ✅ Understand Task Lifecycle & Status Rules

### Main status flow:

```txt
todo → in_progress → review → testing → done
   ↓         ↓           ↓         ↓
blocked   blocked     blocked   blocked
   ↓         ↓           ↓         ↓
cancelled cancelled   cancelled cancelled
```

### Completion Protocol:

1. **Create task**

   ```ts
   { action: "create", ... }
   ```

2. **Set status**

   ```ts
   { action: "update", task_id: "...", status: "in_progress" }
   ```

3. **Update task context**

   ```ts
   { action: "update_property", ... }
   ```

4. **Complete the task**

   ```ts
   { action: "complete", task_id: "..." }
   ```

✅ To reach `done`, all checklists and subtasks (and their nested checklists) **must** be completed.

---

### ✅ Checklist Example:

Checklist is considered complete when all items are marked:

* ☑ Attach files
* ☑ Write documentation
* ☑ Final review

---

Correct code to follow: Important Changes

  TaskId Migration to UUID Format
  - Updated task_id.py to use UUID-based IDs instead of date-based format
  - Changed from YYYYMMDDXXX to 32-character hex UUID strings
  - Added backward compatibility for legacy formats
  - Updated domain imports to use UUID implementation

  Task Entity Enhancements
  - Added comprehensive context management with context_id field
  - Implemented task completion validation requiring updated context
  - Enhanced subtask management with hierarchical ID support
  - Added assignee validation using AgentRole enum
  - Improved label validation and suggestion system

  Repository Updates
  - Modified SQLiteTaskRepository to use UUID-based TaskId
  - Added hierarchical user/project/branch context filtering
  - Implemented UUID schema with backward compatibility
  - Enhanced task relation management (assignees, labels, dependencies, subtasks)

  Application Layer Improvements
  - Updated CreateTaskUseCase to use UUID TaskId generation
  - Added content length validation and truncation
  - Enhanced error handling and domain event processing

  Key Business Logic Enhancements
  - Tasks now require context updates before completion
  - All subtasks must be completed before parent task completion
  - Improved assignee management with role-based validation
  - Enhanced dependency tracking and circular reference prevention


---

 No Derive context based on available parameters, no legacy code, i need clean code