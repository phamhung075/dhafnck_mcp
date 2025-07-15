# Architect Agent Prompt - Vision System Integration

## Prompt for New Chat

```
I need the @code_architect_agent to analyze the current dhafnck_mcp_main codebase and design the integration of the new Vision System.

## Context

We have a complete Vision System design (see /dhafnck_mcp_main/docs/vision/) that needs to be integrated into the existing task management system. The vision system will:

1. Add mandatory context updates for task completion
2. Include workflow guidance in every MCP response
3. Auto-update parent tasks from subtask progress
4. Enrich tasks with vision hierarchy and KPIs
5. Provide AI with next actions and examples

## Current System Overview

- MCP server (FastMCP) with task management
- Domain-driven design with clean architecture
- SQLite database for persistence
- Existing controllers: task_mcp_controller.py, subtask_mcp_controller.py
- Context management already exists but not enforced

## Requirements

1. **No Backward Compatibility Needed** - We can break existing data/APIs
2. **Clean Implementation** - No legacy code preservation
3. **Schema Changes Allowed** - Database can be modified/recreated
4. **Fresh Start OK** - Can delete old data and start clean

## Analysis Needed

Please analyze:

1. **Current Architecture**
   - Task management structure in src/fastmcp/task_management/
   - How MCP tools are registered and responses generated
   - Current context management implementation
   - Database schema and repositories

2. **Integration Points**
   - Where to inject workflow_guidance into responses
   - How to modify task completion flow
   - Where to add progress tracking tools
   - How to implement subtask auto-updates

3. **Schema Design**
   - New tables/columns for vision data
   - Context enforcement at DB level
   - Progress tracking storage
   - Vision hierarchy storage

4. **Implementation Strategy**
   - Which components to modify vs replace
   - Order of implementation for minimal disruption
   - How to structure the new vision modules
   - Testing strategy for new requirements

## Deliverables

1. **Architecture Diagram** showing:
   - Current system structure
   - Integration points for vision system
   - New components to add
   - Data flow for workflow guidance

2. **Implementation Plan** with:
   - Specific files to modify/create
   - Database schema changes
   - New domain models needed
   - API changes required

3. **Code Structure** proposal:
   - Where vision components should live
   - How to organize workflow guidance
   - Module dependencies
   - Clean boundaries between systems

4. **Migration Strategy**:
   - How to transition from current to new system
   - Database migration approach
   - Testing phases
   - Rollout plan

## Key Design Decisions Needed

1. Should workflow_guidance be:
   - A middleware that wraps all responses?
   - Built into each controller?
   - A separate service called by controllers?

2. Should vision data be:
   - Stored in separate tables?
   - Embedded in task table?
   - Cached in Redis?

3. Should context enforcement be:
   - At application layer only?
   - Also enforced at database level?
   - Through domain entity validation?

4. Should progress tracking be:
   - Event-based?
   - Calculated on demand?
   - Stored and updated incrementally?

## Resources

- Vision system docs: /dhafnck_mcp_main/docs/vision/
- Start with: SYSTEM_INTEGRATION_GUIDE.md (authoritative specs)
- Implementation roadmap: IMPLEMENTATION_ROADMAP.md
- Workflow details: WORKFLOW_GUIDANCE_DETAILED_SPEC.md

Please provide a comprehensive analysis and integration design that leverages the existing DDD architecture while cleanly integrating the new vision capabilities.
```

## Additional Context for Architect

### What Can Be Changed

1. **Database Schema** - Add/modify tables as needed
2. **API Contracts** - No existing clients to support
3. **Domain Models** - Can be enhanced or replaced
4. **Business Logic** - Can enforce new rules strictly

### What Should Be Preserved

1. **DDD Architecture** - Keep clean boundaries
2. **FastMCP Framework** - Work within MCP patterns
3. **Core Concepts** - Tasks, subtasks, context
4. **Repository Pattern** - For data access

### Priority Focus

1. **Context Enforcement** - Block completion without summary
2. **Workflow Guidance** - Every response helps AI
3. **Progress Automation** - Subtasks update parents
4. **Vision Integration** - But start with core features

The architect should focus on a clean, maintainable integration that makes the system better, not just bigger.