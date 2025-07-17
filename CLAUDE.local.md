
### Test & code Structure


dhafnck-frontend/
├── docker/
├── docs/
├── src/
└── tests/

dhafnck_mcp_main/
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
    │       └── ... (source code)
    └── utils/

          