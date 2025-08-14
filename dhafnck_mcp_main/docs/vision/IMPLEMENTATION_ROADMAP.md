# Vision System Implementation Roadmap

## Overview

This document provides a complete phased implementation plan for the MCP Vision System. Each phase includes specific documents to read, sections to focus on, and files to create/edit.

---

## 📋 Phase Init: Preparation & Understanding 

### Objective
Understand the vision system architecture and MCP constraints. before working on each phase

### Documents to Read

1. **[consolidated-mcp-vision-implementation.md](consolidated-mcp-vision-implementation.md)**
   - Read sections: Overview, Core Architecture, Key Principles
   - Focus on: MCP constraints and server-side approach

2. **[01-vision-hierarchy.md](01-vision-hierarchy.md)**
   - Read sections: Hierarchical Structure, Vision Levels
   - Focus on: How vision cascades from Organization → Task

3. **[server-side-context-tracking.md](server-side-context-tracking.md)**
   - Read sections: The Constraint, Solution Overview
   - Focus on: How to track context through MCP parameters only

### Success Criteria
- [ ] Understand MCP server constraints
- [ ] Understand vision hierarchy concept
- [ ] Know how context tracking works without client-side state

### No files to create in this phase

---

## 🔧 Phase 1: Enforce Context Updates (1-2 days)

### Objective
Modify task completion to require context updates, blocking completion without them.

### Documents to Read

1. **[manual-context-vision-updates.md](manual-context-vision-updates.md)**
   - Read sections: "Block Task Completion Without Updates", "New Combined Actions"
   - Focus on: How to enforce manual context requirements through required parameters

2. **[server-side-context-tracking.md](server-side-context-tracking.md)**
   - Read sections: "Require Context with Each Significant Action", "Completion Checklist"
   - Focus on: Required parameters for completion

### Files to Edit

```python
# 1. Modify existing task controller
src/fastmcp/task_management/interface/controllers/task_mcp_controller.py
  - Add context parameters to manage_task() method
  - Add work_notes, progress_made, completion_summary parameters
  - Block completion if completion_summary is missing
  - Reference: manual-context-vision-updates.md - "Modified manage_task Tool"

# 2. Update context factory (if needed)
src/fastmcp/task_management/application/factories/context_response_factory.py
  - Ensure it handles new context update fields
  - Reference: implementation-guide-server-enrichment.md - "Enhanced Context Response Factory"
```

### Files to Create

```python
# 1. Context enforcing controller (OPTIONAL - can modify existing controller instead)
src/fastmcp/task_management/interface/controllers/context_enforcing_controller.py
  - Reference implementation in manual-context-vision-updates.md
  - Implements: manage_task with context enforcement
  - Key methods: enforce completion_summary requirement
  - Alternative: Modify existing task_mcp_controller.py directly
```

### Testing
```bash
# Test that completion fails without summary
mcp.manage_task(action="complete", task_id="123")
# Should return error with guidance

# Test successful completion
mcp.manage_task(
    action="complete", 
    task_id="123",
    completion_summary="Implemented feature X"
)
# Should succeed
```

### Success Criteria
- [ ] Task completion blocked without completion_summary
- [ ] Error messages include helpful examples
- [ ] Context parameters accepted in manage_task

---

## 🚀 Phase 2: Add Progress Reporting Tools (1-2 days)

### Objective
Create simple tools for AI to report progress without understanding context structure.

### Documents to Read

1. **[server-side-context-tracking.md](server-side-context-tracking.md)**
   - Read sections: "Progressive Context Building", "Expected AI Workflow"
   - Focus on: report_progress tool design

2. **[consolidated-mcp-vision-implementation.md](consolidated-mcp-vision-implementation.md)**
   - Read sections: "Context Through MCP Parameters"
   - Focus on: Tool parameter design

### Files to Create

```python
# 1. Add progress reporting tools to existing controller
# Either modify task_mcp_controller.py OR create new file:
src/fastmcp/task_management/interface/controllers/progress_tools_controller.py

Key tools to implement:
- report_progress(task_id, progress_type, description, percentage)
- quick_task_update(task_id, what_i_did, progress_percentage)  
- checkpoint_work(task_id, current_state, next_steps)

Reference: context_enforcing_controller.py example in docs
```

### Configuration to Add

```yaml
# In config file (location depends on your setup)
mcp_server_config.yaml:
  task_management:
    progress_tracking:
      enabled: true
      types: ["analysis", "implementation", "testing", "debugging"]
      auto_map_to_context: true
```

### Testing
```bash
# Test progress reporting
mcp.report_progress(
    task_id="123",
    progress_type="implementation",
    description="Added caching layer",
    percentage_complete=50
)
# Should update context automatically
```

### Success Criteria
- [ ] report_progress tool available and working
- [ ] quick_task_update provides simple interface
- [ ] Progress maps to correct context sections

---

## 🎯 Phase 3: Implement Workflow Hints (2-3 days)

### Objective
Add workflow guidance to every tool response to guide AI behavior.

### Documents to Read

1. **[workflow-hints-and-rules.md](workflow-hints-and-rules.md)** - **PRIMARY DOCUMENT**
   - Read: Entire document
   - Focus on: Response structure, hint generation logic

2. **[consolidated-mcp-vision-implementation.md](consolidated-mcp-vision-implementation.md)**
   - Read sections: "Workflow Hints System"
   - Focus on: How hints integrate with responses

### Files to Create

```python
# 1. Workflow hint enhancer
src/fastmcp/task_management/interface/controllers/workflow_hint_enhancer.py
  - Reference implementation in workflow-hints-and-rules.md
  - Key classes: WorkflowHintEnhancer
  - Key methods: enhance_task_response(), _generate_workflow_guidance()
  - See code examples in the document

# 2. Integrate with task controller
src/fastmcp/task_management/interface/controllers/task_mcp_controller.py
  - Import WorkflowHintEnhancer
  - Wrap all responses with enhancer.enhance_task_response()
  - Ensure errors also get enhancement
```

### Configuration

```yaml
# workflow_hints_config.yaml
workflow_hints:
  enabled: true
  always_include_hints: true
  update_interval_minutes: 30
  phases:
    not_started:
      rules: ["Must update status to in_progress"]
      hints: ["Begin by analyzing requirements"]
```

### Testing
```bash
# Get task - should include workflow guidance
response = mcp.manage_task(action="get", task_id="123")
assert "workflow_guidance" in response
assert "next_actions" in response["workflow_guidance"]

# Error should include resolution guidance
response = mcp.manage_task(action="complete", task_id="123")
assert "resolution_guidance" in response
```

### Success Criteria
- [ ] All task responses include workflow_guidance
- [ ] Errors include resolution steps and examples
- [ ] Next actions are contextually relevant
- [ ] Hints adapt based on task state

---

## 🔄 Phase 4: Subtask Progress Integration (2 days)

### Objective
Enforce manual progress tracking for subtasks through required parameters and response enrichment.

### Documents to Read

1. **[subtask-manual-progress-tracking.md](subtask-manual-progress-tracking.md)** - **PRIMARY DOCUMENT**
   - Read: Entire document
   - Focus on: Required parameters, manual update patterns

2. **[consolidated-mcp-vision-implementation.md](consolidated-mcp-vision-implementation.md)**
   - Read sections: "Working with Subtasks"
   - Focus on: Enhanced subtask tools

### Files to Create/Edit

```python
# 1. Subtask progress controller
src/fastmcp/task_management/interface/controllers/subtask_progress_controller.py
  - Reference implementation in subtask-manual-progress-tracking.md
  - Key class: SubtaskProgressController
  - Key tools: complete_subtask_with_update, quick_subtask_update
  - See complete code structure in the document

# 2. Modify subtask management
src/fastmcp/task_management/interface/controllers/subtask_mcp_controller.py (if exists)
  - Add required parameters for progress tracking
  - Calculate parent progress from manual updates
  - Return reminders for parent context updates
  - Reference: subtask_progress_controller.py example
```

### Testing
```bash
# Complete subtask - parent should update
mcp.complete_subtask_with_update(
    task_id="parent_123",
    subtask_id="sub_456",
    completion_summary="Auth module done"
)
# Check parent progress increased

# Quick subtask update
mcp.quick_subtask_update(
    task_id="parent_123",
    subtask_id="sub_789",
    what_i_did="Fixed validation",
    subtask_progress=50
)
# Parent context should include update
```

### Success Criteria
- [ ] Subtask completion updates parent progress
- [ ] Parent can't complete with incomplete subtasks
- [ ] Subtask context propagates to parent
- [ ] Progress calculation is accurate

---

## 🌟 Phase 5: Vision Enrichment (3-4 days)

### Objective
Automatically include vision hierarchy and alignment in task responses.

### Documents to Read

1. **[implementation-guide-server-enrichment.md](implementation-guide-server-enrichment.md)** - **PRIMARY DOCUMENT**
   - Read: Entire document
   - Focus on: VisionEnrichmentService design

2. **[02-vision-components.md](02-vision-components.md)**
   - Read: Vision component structures
   - Focus on: What data to include in enrichment

3. **[04-domain-models.md](04-domain-models.md)**
   - Read: Vision domain models
   - Focus on: Vision entity structures

### Files to Create

```python
# 1. Vision enrichment service
src/fastmcp/vision_orchestration/vision_enrichment_service.py
  - Key class: VisionEnrichmentService
  - Key method: enrich_task_with_vision()
  - Returns: Vision hierarchy, alignment scores, KPIs

# 2. Vision domain models (if not exist)
src/fastmcp/task_management/domain/value_objects/vision_objects.py
  - VisionObjective, VisionMetric, VisionAlignment classes
  - Reference: 04-domain-models.md

# 3. Update application facade
src/fastmcp/task_management/application/facades/task_application_facade.py
  - Inject VisionEnrichmentService
  - Call enrichment in get_next_task()
  - Merge vision into context_data
```

### Configuration

```yaml
# vision_enrichment_config.yaml
vision_enrichment:
  enabled: true
  default_include_vision: true
  cache_ttl_seconds: 300
  alignment_thresholds:
    high: 0.8
    medium: 0.5
```

### Testing
```bash
# Get task with vision
task = mcp.manage_task(action="next", include_vision=True)
assert "vision" in task
assert "alignment_score" in task["vision"]
assert "kpi_progress" in task["vision"]
```

### Success Criteria
- [ ] Tasks include vision hierarchy
- [ ] Alignment scores calculated correctly
- [ ] KPIs and metrics included
- [ ] AI guidance based on vision

---

## 🔒 Phase 6: Integration & Testing (2-3 days)

### Objective
Ensure all components work together seamlessly.

### Documents to Review

1. **[consolidated-mcp-vision-implementation.md](consolidated-mcp-vision-implementation.md)**
   - Review: Complete workflow examples
   - Verify: All features documented are implemented

### Integration Points to Test

```python
# 1. Complete workflow test
- Get task (with vision + hints)
- Update progress (manual context)
- Work on subtasks (manual progress updates)
- Complete with summary (enforced)
- Verify vision metrics updated

# 2. Error handling test
- Try invalid actions
- Verify helpful error guidance
- Check resolution examples work

# 3. Subtask workflow test
- Create subtasks
- Update subtask progress
- Complete subtasks
- Verify parent ready for completion
```

### Files to Update

```python
# 1. Main MCP server initialization
src/fastmcp/server.py (or equivalent)
  - Register all new controllers
  - Enable hint enhancement
  - Configure vision enrichment

# 2. Configuration loading
  - Ensure all config files loaded
  - Set proper defaults
```

### Success Criteria
- [ ] End-to-end workflow works smoothly
- [ ] All error cases handled gracefully
- [ ] Performance acceptable (<100ms overhead)
- [ ] AI receives comprehensive guidance

---

## 📊 Phase 7: Monitoring & Optimization (Optional)

### Objective
Add monitoring and optimize performance.

### Areas to Monitor
- Context update frequency
- Vision calculation performance  
- Hint generation time
- Progress tracking accuracy

### Optimizations
- Cache vision calculations
- Batch context updates
- Optimize database queries

---

## 🎯 Quick Reference: What to Build

### Controllers (Phase 1-4)
1. `context_enforcing_controller.py` - Enforce context updates
2. `progress_tools_controller.py` - Simple progress reporting
3. `workflow_hint_enhancer.py` - Add guidance to responses
4. `subtask_progress_controller.py` - Manual progress tracking with required parameters

### Services (Phase 5)
1. `vision_enrichment_service.py` - Include vision in tasks
2. Vision domain models - Define vision structures

### Key Features by Phase
- Phase 1: Can't complete without context ✓
- Phase 2: Easy progress reporting ✓
- Phase 3: AI gets hints on what to do next ✓
- Phase 4: Subtasks update parents automatically ✓
- Phase 5: Vision included in every task ✓

---

## 🚀 Getting Started

1. **Start with Phase 0** - Read the core documents
2. **Implement Phase 1** - This blocks the main issue (forgetting context)
3. **Add phases incrementally** - Each phase adds value independently
4. **Test as you go** - Use the testing examples provided

The system is designed so each phase provides value even without the later phases!