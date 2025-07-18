
### Test & code Structure

only source of trust of path is:
root/
├──___root___
├── dhafnck-frontend/
│   ├── docker/
│   ├── docs/
│   ├── src/
│   └── tests/
│
└── dhafnck_mcp_main/
    ├── docker/
    ├── docs/
    └── src/
        ├── tests/
        │   ├── unit/
        │   ├── integration/
        │   ├── e2e/
        │   ├── performance/
        │   └── fixtures/
        ├── fastmcp/
        │   └── task_management/
        │       └── ... (DDD source code)
        └── utils/

ignore 
00_RESOURCES/*
00_RULES/*


## HIERARCHICAL CONTEXT SYSTEM

### 4-Tier Architecture
The system now uses a 4-tier hierarchical context system:
```
GLOBAL (singleton) → PROJECT → BRANCH → TASK
```

### Key Points:
1. **Backward Compatibility**: The `manage_context` tool still works but internally uses the hierarchical system
2. **Context Inheritance**: Lower levels automatically inherit from higher levels
3. **UUID-Based Branches**: Use `git_branch_id` (UUID) instead of branch names
4. **Auto-Detection**: Branch ID is auto-detected from task when not provided

### When to Use Each Tool:
- **manage_context**: For simple task operations (backward compatible)
- **manage_hierarchical_context**: For advanced operations like delegation, inheritance debugging, branch contexts

### Common Operations:
```python
# Resolve context with inheritance
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="resolve",
    level="task",
    context_id=task_id
)

# Delegate pattern to project level
mcp__dhafnck_mcp_http__manage_hierarchical_context(
    action="delegate",
    level="task",
    context_id=task_id,
    delegate_to="project",
    delegate_data={...}
)
```

## ISSUE KNOW:
1. Task Completion Validation Issue ⚠️
  - Problem: Task completion fails with "Task completion requires context to be created first" even
  when context exists
  - Explanation: This is not actually a problem — it's a strict requirement. The context must be updated before completing the task. To avoid forgetting this step: always make sure to update the context before attempting to complete the task.


## CHANGELOG: AI must update this when make change on project
  Strict Requirements:
  1. Docker Container Mode: MUST use Docker database (/data/dhafnck_mcp.db) -
  server fails if not accessible. Need rebuild docker for view code change
  2. Local Development Mode: MUST use Docker database (/data/dhafnck_mcp.db) -
  server fails if not accessible. Need rebuild docker for view code change
  3. MCP STDIN Mode: Uses local database (technical limitation - cannot access
  Docker database)
  4. Test Mode: Always uses isolated test database (dhafnck_mcp_test.db)

### 2025-01-18
- **Subtask Architecture Fix**: Task entity stores subtask IDs only, validation in TaskCompletionService. Frontend updated for new structure. Fixed 3 tests.
- **Database Mode Config**: Strict Docker DB enforcement (/data/dhafnck_mcp.db) for local/container modes. MCP STDIN uses local DB. Tests use isolated DB. Docs: DATABASE_MODE_CONFIGURATION.md
- **4-Tier Context System**: Global→Project→Branch→Task hierarchy with inheritance, delegation, caching. Added delegation queue with approval workflow. Fixed SQLAlchemy relationships (ForeignKeys, back_populates). 28 tests fixed, 2 new test files added.
- **Context Branch Mapping**: Replaced git_branch_name with git_branch_id. Auto-detection from task_id. Updated: context_mcp_controller.py, hierarchical_context_facade*.py, descriptions. Created test_context_git_branch_id_fix.py (7 tests). Fixes "Branch default_branch not found" error.
- **Hierarchical Context Migration**: Updated TaskCompletionService to validate hierarchical context instead of basic context. All error messages now use manage_hierarchical_context commands. Created test_task_completion_hierarchical_context.py (7 tests). Replaced manage_context calls in: error_handler.py, task_workflow_guidance.py, workflow_hint_enhancer.py, next_task.py, complete_task_optimized.py. Progress on Issue #2.
- **Task Status Update Fix**: Fixed error where updating task status to 'in_progress' incorrectly triggered completion validation. Added context-aware routing in error_handler.py for ValueError exceptions. Created test_task_status_update_error_fix.py with 3 TDD tests. Now properly routes "context must be updated" errors based on action parameter.
- **Documentation Updates**: Updated all project documentation to reflect hierarchical context system:
  - CLAUDE.md: Added 4-tier hierarchy diagram, context tool selection guide, and v9.1 key updates
  - CLAUDE.local.md: Added hierarchical context system section with usage examples
  - docs/HIERARCHICAL_CONTEXT_MIGRATION.md: Created comprehensive migration guide with architecture diagram
  - docs/index.md: Updated with migration guide reference