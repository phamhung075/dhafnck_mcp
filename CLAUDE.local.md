
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


## CHANGELOG: AI must update this when make change on project
  Strict Requirements:
  1. Docker Container Mode: MUST use Docker database (/data/dhafnck_mcp.db) -
  server fails if not accessible
  2. Local Development Mode: MUST use Docker database (/data/dhafnck_mcp.db) -
  server fails if not accessible
  3. MCP STDIN Mode: Uses local database (technical limitation - cannot access
  Docker database)
  4. Test Mode: Always uses isolated test database (dhafnck_mcp_test.db)

### 2025-01-18
- Fixed AttributeError when completing tasks with subtasks
- Task entity now only stores subtask IDs, not full objects
- Subtask validation moved to TaskCompletionService
- Fixed failing tests to align with new architecture:
  - test_task_completion_requires_all_subtasks_completed
  - test_all_subtasks_completed_check
  - test_task_entity_subtasks_as_dict_vs_objects
- Updated frontend to handle new architecture:
  - Task interface now uses subtask IDs (string[]) instead of Subtask objects
  - TaskList shows subtask count with "subtasks" label
  - TaskDetailsDialog displays subtask IDs with note to view details in Subtasks tab
- **Database Mode Configuration**: Updated database source manager for strict consistency enforcement
  - Local development MUST use Docker database (/data/dhafnck_mcp.db) - server fails if not accessible
  - Docker container mode MUST use Docker database (/data/dhafnck_mcp.db) - server fails if not accessible
  - MCP STDIN mode uses local database (cannot access Docker database due to stdin communication)
  - Test isolation maintained: tests always use local test database (dhafnck_mcp_test.db)
  - Removed fallback mechanisms: fail-fast behavior prevents data inconsistency
  - Created documentation: docs/DATABASE_MODE_CONFIGURATION.md
  - **Impact**: Enforces strict consistency between local development and frontend, prevents silent data isolation issues