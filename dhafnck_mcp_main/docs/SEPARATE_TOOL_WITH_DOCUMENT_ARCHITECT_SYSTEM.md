# Separate Tool with Document Architect System

## Overview
This document describes the architecture and best practices for separating tool logic from documentation in the FastMCP subtask management system. The approach ensures maintainability, clarity, and scalability by keeping business logic and documentation in distinct modules.

## Rationale for Separation
- **Maintainability:** Update documentation without touching controller logic.
- **Reusability:** Share documentation across multiple tools/controllers.
- **Organization:** Clear boundaries between code and docs.
- **Version Control:** Track documentation changes independently.
- **Collaboration:** Enable technical writers and developers to work in parallel.

## Directory Structure
```
dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/desc/
├── README.md
├── description_loader.py
├── task/
│   └── tool/
│       └── manage_task_description.py
├── subtask/
│   └── manage_subtask_description.py
└── agent/
    └── call_agent_description.py
```
- **desc/**: All tool documentation lives here, separate from controller logic.
- **description_loader.py**: Aggregates and provides access to all tool descriptions.
- **task/**, **subtask/**, **agent/**: Subdirectories for task, subtask, and agent tool docs.

## Description Loader: Nested & Recursive Support

### New Loader Features
- **Recursive Scanning:** The loader now automatically scans all subdirectories for files ending with `_description.py`.
- **Dynamic Import:** Each file is dynamically imported, and all `*_DESCRIPTION` and `*_PARAMETERS` variables are extracted.
- **Nested Output:** The loader builds a nested dictionary reflecting the directory structure, making it easy to manage large or complex toolsets.

### Usage Example
```python
from .desc import description_loader

descriptions = description_loader.get_all_descriptions()
# Example output structure:
# {
#   'task': {
#       'manage_task': {
#           'description': ...,
#           'parameters': ...
#       }
#   },
#   'subtask': {
#       'manage_subtask': {
#           'description': ...,
#           'parameters': ...
#       }
#   },
#   'agent': {
#       'call_agent': {
#           'description': ...,
#           'parameters': ...
#       }
#   }
# }

# Accessing a specific tool's description:
manage_subtask_desc = descriptions['subtask']['manage_subtask']
call_agent_desc = descriptions['agent']['call_agent']
```

### Integration Pattern
Controllers import documentation via the loader, keeping business logic clean:
```python
from .desc import description_loader

descriptions = description_loader.get_all_descriptions()
manage_subtask_desc = descriptions["subtask"]["manage_subtask"]
call_agent_desc = descriptions["agent"]["call_agent"]

@mcp.tool()
def manage_subtask(
    action: Annotated[str, Field(description=manage_subtask_desc["parameters"]["action"])]
) -> Dict[str, Any]:
    f"""{manage_subtask_desc["description"]}"""
    # Tool implementation here

@mcp.tool()
def call_agent(
    name_agent: str = mcp.Field(description=call_agent_desc["parameters"]["name_agent"])
) -> Dict[str, Any]:
    f"""{call_agent_desc["description"]}"""
    # Tool implementation here
```

## Subtask & Agent Management Tool: Case Studies
- **Subtask Documentation File:** `desc/subtask/manage_subtask_description.py`
- **Agent Documentation File:** `desc/agent/call_agent_description.py`
- **Contents:**
  - High-level overview
  - Action types (e.g., create, update, call_agent)
  - Data structure for each action
  - Usage guidelines and best practices
  - Parameter descriptions

## Best Practices
- Use `TOOL_NAME_DESCRIPTION` and `TOOL_NAME_PARAMETERS` constants in each doc file.
- Follow the emoji and section format for clarity and consistency.
- Update `README.md` in `desc/` to reflect new or changed documentation patterns.
- Keep documentation and logic in sync via the loader.
- For new tools, simply add a new `*_description.py` file in the appropriate subdirectory (e.g., `agent/` for agent tools); the loader will pick it up automatically.

## Migration Benefits

- **Maintainability:** Tool descriptions can be updated without modifying controller code
- **Reusability:** Descriptions can be shared across multiple controllers or tools
- **Organization:** Clear separation between documentation and logic
- **Version Control:** Changes to descriptions can be tracked independently
- **Collaboration:** Documentation can be edited by different team members
- **Testing:** Descriptions can be validated and tested separately

## Benefits
- **Focused Code:** Controllers only handle business logic and protocol.
- **Easy Updates:** Change docs without code changes.
- **Quality:** Dedicated attention to documentation standards.
- **Scalability:** Effortlessly supports large and deeply nested toolsets.

## References
- [desc/README.md](../src/fastmcp/task_management/interface/controllers/desc/README.md)
- [desc/subtask/manage_subtask_description.py](../src/fastmcp/task_management/interface/controllers/desc/subtask/manage_subtask_description.py)
- [desc/agent/call_agent_description.py](../src/fastmcp/task_management/interface/controllers/desc/agent/call_agent_description.py)
- [desc/description_loader.py](../src/fastmcp/task_management/interface/controllers/desc/description_loader.py) 