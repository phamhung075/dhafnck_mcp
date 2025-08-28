# 💻 CODE AGENT SCRIPT - Task Workflow Schema

## Schema Logic Flow

### 1. Initialize Agent
```yaml
agent:
  load: "@coding_agent"
  verify: capabilities.permissions.mcp_tools
```

### 2. Get Next Task
```yaml
task_retrieval:
  action: "next"
  filters:
    git_branch_id: "${branch_id}"
    assigned_agent: "@coding_agent"
    include_context: true
  retry:
    if_empty: wait_300_seconds
    max_attempts: 3
```

### 3. Process Task
```yaml
task_processing:
  mark_in_progress:
    action: "update"
    status: "in_progress"
  
  execute_work:
    based_on: task.type
    operations:
      - read_files
      - apply_fixes
      - validate_changes
  
  update_context:
    level: "branch"
    data:
      files_modified: []
      changes_applied: []
      status: "complete"
```

### 4. Complete Task
```yaml
task_completion:
  action: "complete"
  required_fields:
    completion_summary: string
    testing_notes: string
    files_modified: integer
  update_context: true
```

### 5. Loop Control
```yaml
workflow_loop:
  condition: tasks_available
  sequence:
    - get_next_task
    - process_task  
    - complete_task
    - check_for_more
  exit_when: no_tasks_found
```

## Implementation Schema

### Task States
```yaml
states:
  pending: waiting_for_agent
  in_progress: agent_working
  blocked: waiting_dependencies
  completed: work_finished
  failed: needs_retry
```

### Error Handling
```yaml
error_recovery:
  on_failure:
    - log_error
    - update_task_status: "blocked"
    - notify_planner_agent
    - retry_after: 60_seconds
  max_retries: 3
```

### Context Updates
```yaml
context_schema:
  branch_context:
    progress: percentage
    files_modified: list
    violations_fixed: count
    blockers: list
    next_steps: list
  
  task_context:
    start_time: timestamp
    end_time: timestamp
    duration: seconds
    success: boolean
```

### Validation Rules
```yaml
validation:
  before_completion:
    - all_files_exist
    - no_syntax_errors
    - tests_pass
    - lint_clean
  
  required_for_success:
    - completion_summary: not_empty
    - files_modified: greater_than_0
    - context_updated: true
```

## Workflow Dependencies

### Input Requirements
```yaml
required_inputs:
  branch_id: uuid
  project_id: uuid
  agent_permissions: object
  task_filters: object
```

### Output Schema
```yaml
task_output:
  task_id: uuid
  status: string
  completion_summary: string
  files_modified: integer
  context_updated: boolean
  errors: list
```

### Integration Points
```yaml
integrations:
  planner_agent:
    receive: task_assignments
    send: completion_status
  
  test_agent:
    trigger_on: task_complete
    provide: modified_files
  
  context_system:
    update_on: each_operation
    read_before: task_start
```