
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


## CHANGELOG

### 2025-01-18
- Fixed AttributeError when completing tasks with subtasks
- Task entity now only stores subtask IDs, not full objects
- Subtask validation moved to TaskCompletionService
- Fixed failing tests to align with new architecture:
  - test_task_completion_requires_all_subtasks_completed
  - test_all_subtasks_completed_check
  - test_task_entity_subtasks_as_dict_vs_objects