
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
  server fails if not accessible. Need rebuild docker for view code change
  2. Local Development Mode: MUST use Docker database (/data/dhafnck_mcp.db) -
  server fails if not accessible. Need rebuild docker for view code change
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
- **Context Management System Update**: Enhanced hierarchical context management with delegation and inheritance
  - Implemented four-tier context hierarchy: Global → Project → Branch → Task
  - Added context resolution with full inheritance chain support
  - Context updates now propagate changes to dependent contexts
  - Implemented delegation system for sharing patterns from task to branch/project/global levels
  - Added delegation queue with manual approval workflow
  - Context operations: resolve, update, create, delegate, propagate
  - Delegation queue operations: list, approve, reject, get_status
  - Added context inheritance validation for debugging and troubleshooting
  - Performance optimizations: caching with dependency tracking, automatic cache invalidation
  - Branch-level context enables: branch-specific configurations, isolated experiments, feature-specific standards
  - **Impact**: Enables knowledge sharing across tasks/branches/projects, maintains organizational standards, supports autonomous AI decision-making with proper context
- **4-Tier Context Hierarchy SQLAlchemy Fixes**: Fixed ORM relationship issues for complete 4-tier implementation
  - Fixed SQLAlchemy relationship errors in models.py:
    - Added ForeignKey to BranchContext.branch_id → project_git_branchs.id
    - Added ForeignKey to TaskContext.task_id → tasks.id  
    - Added back_populates="branch_context" to ProjectGitBranch model
    - Added back_populates="task_context" to Task model
  - Updated test_hierarchical_context_orm.py for 4-tier support:
    - Added helper methods: _create_project_entity, _create_git_branch_entity, _create_task_entity
    - Fixed all 28 tests to create required entities before contexts (foreign key constraints)
    - Updated inheritance tests to verify 4-level resolution (global → project → branch → task)
  - Updated ORMHierarchicalContextRepository:
    - Added branch level handling in resolve_context method
    - Updated get_context_hierarchy to return 4-level hierarchy
    - Added branch to search_contexts supported levels
  - Created new test files for 4-layer validation:
    - test_context_inheritance_service_4_layer.py (13 tests passing)
    - test_hierarchical_context_4_layer_integration.py
  - **Impact**: Complete 4-tier hierarchy now works with proper SQLAlchemy relationships and foreign key integrity