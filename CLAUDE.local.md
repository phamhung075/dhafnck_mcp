
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