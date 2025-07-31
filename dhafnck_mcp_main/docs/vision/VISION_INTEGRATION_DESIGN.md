# Vision System Integration Design

## Executive Summary

This document provides a comprehensive design for integrating the Vision System into the existing dhafnck_mcp_main task management system. The integration leverages the current DDD architecture while adding new capabilities for mandatory context updates, workflow guidance, automatic progress tracking, and vision hierarchy enrichment.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Integration Points](#integration-points)
3. [Schema Design](#schema-design)
4. [Implementation Strategy](#implementation-strategy)
5. [Code Structure](#code-structure)
6. [Migration Strategy](#migration-strategy)
7. [Key Design Decisions](#key-design-decisions)

---

## Architecture Overview

### Current System + Vision Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP CLIENT                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ MCP Protocol
┌─────────────────────────────────┴───────────────────────────────┐
│                    INTERFACE LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Vision-Enhanced MCP Controllers                  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • TaskMCPController → EnhancedTaskMCPController         │   │
│  │ • NEW: ContextEnforcingController                       │   │
│  │ • NEW: SubtaskProgressController                        │   │
│  │ • WorkflowHintEnhancer (Middleware)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────┐
│                    APPLICATION LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Application Facades + Services              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • TaskApplicationFacade (Enhanced)                       │   │
│  │ • ContextApplicationFacade (Enhanced)                    │   │
│  │ • NEW: VisionEnrichmentService                          │   │
│  │ • NEW: ProgressTrackingService                          │   │
│  │ • NEW: WorkflowGuidanceService                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────┐
│                      DOMAIN LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Domain Entities                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Task (Enhanced with vision fields)                     │   │
│  │ • Context (Enhanced with mandatory fields)               │   │
│  │ • NEW: Vision (Value Object)                            │   │
│  │ • NEW: WorkflowState (Value Object)                     │   │
│  │ • NEW: ProgressSnapshot (Event)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────┐
│                  INFRASTRUCTURE LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Enhanced Repositories                       │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • TaskRepository (with vision data)                      │   │
│  │ • NEW: VisionRepository                                  │   │
│  │ • NEW: ProgressEventStore                               │   │
│  │ • Enhanced SQLite Schema                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow for Vision-Enhanced Operations

```
1. MCP Request → WorkflowHintEnhancer (adds guidance)
2. Controller validates and enforces context rules
3. Application service orchestrates business logic
4. Domain entities enforce business rules
5. Infrastructure persists changes
6. Response enriched with workflow guidance
```

---

## Integration Points

### 1. Workflow Guidance Injection

**Approach**: Middleware Pattern

```python
# src/fastmcp/task_management/interface/middleware/workflow_hint_enhancer.py
class WorkflowHintEnhancer:
    """Wraps all MCP responses with workflow guidance"""
    
    def enhance_response(self, response: dict, context: RequestContext) -> dict:
        guidance = self.workflow_guidance_service.generate_guidance(context)
        response['workflow_guidance'] = guidance
        return response
```

**Integration Point**: MCP server response pipeline

### 2. Context Enforcement

**Approach**: Domain Rule + Controller Validation

```python
# Domain layer enforcement
class Task:
    def complete(self, completion_summary: str) -> None:
        if not completion_summary:
            raise DomainError("completion_summary is required")
        self.context.update_completion_summary(completion_summary)
        self._status = TaskStatus.DONE

# Interface layer enforcement
class ContextEnforcingController:
    @tool(description="Complete task with mandatory context")
    def complete_task_with_context(
        self,
        task_id: str,
        completion_summary: str,  # REQUIRED
        testing_notes: Optional[str] = None,
        next_recommendations: Optional[str] = None
    ) -> dict:
        # Validation and processing
```

**Integration Point**: Task completion flow at domain and interface layers

### 3. Automatic Progress Updates

**Approach**: Domain Events + Event Handler

```python
# Domain event
class SubtaskCompleted(DomainEvent):
    parent_task_id: str
    subtask_id: str
    progress_percentage: float

# Application layer handler
class ProgressTrackingService:
    def handle_subtask_completed(self, event: SubtaskCompleted):
        parent = self.task_repo.get(event.parent_task_id)
        parent.update_progress_from_subtasks()
        self.task_repo.save(parent)
```

**Integration Point**: Domain event system

### 4. Vision Hierarchy Enrichment

**Approach**: Repository Decorator Pattern

```python
class VisionEnrichedTaskRepository:
    def __init__(self, base_repo: TaskRepository, vision_service: VisionEnrichmentService):
        self.base_repo = base_repo
        self.vision_service = vision_service
    
    def get(self, task_id: str, include_context: bool = False) -> Task:
        task = self.base_repo.get(task_id)
        if include_context:
            task = self.vision_service.enrich_with_vision(task)
        return task
```

**Integration Point**: Repository layer with caching

---

## Schema Design

### New Tables

```sql
-- Vision hierarchy and alignment
CREATE TABLE vision_data (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL, -- 'organization', 'project', 'task'
    entity_id TEXT NOT NULL,
    vision_statement TEXT,
    mission TEXT,
    strategic_goals TEXT, -- JSON array
    kpis TEXT, -- JSON object
    alignment_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_id)
);

-- Progress tracking events
CREATE TABLE progress_events (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- 'analysis_complete', 'implementation_progress', etc.
    progress_percentage REAL,
    details TEXT, -- JSON
    agent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Workflow state tracking
CREATE TABLE workflow_states (
    task_id TEXT PRIMARY KEY,
    current_phase TEXT NOT NULL, -- 'planning', 'implementation', 'testing', etc.
    phase_progress REAL,
    last_action TEXT,
    next_recommended_actions TEXT, -- JSON array
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### Modified Tables

```sql
-- Enhanced contexts table
ALTER TABLE contexts ADD COLUMN completion_summary TEXT;
ALTER TABLE contexts ADD COLUMN testing_notes TEXT;
ALTER TABLE contexts ADD COLUMN next_recommendations TEXT;
ALTER TABLE contexts ADD COLUMN vision_alignment_score REAL;

-- Enhanced tasks table
ALTER TABLE tasks ADD COLUMN overall_progress REAL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN is_strategic_priority BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN vision_data TEXT; -- JSON cache
```

---

## Implementation Strategy

### Phase 1: Context Enforcement (Week 1)

**Priority**: CRITICAL

**Files to Create/Modify**:

1. **Domain Layer**:
   - Modify: `domain/entities/task.py` - Add completion validation
   - Modify: `domain/entities/context.py` - Add mandatory fields
   - Create: `domain/exceptions/vision_exceptions.py`

2. **Application Layer**:
   - Modify: `application/facades/task_application_facade.py` - Enhance completion logic
   - Create: `application/services/context_validation_service.py`

3. **Interface Layer**:
   - Create: `interface/controllers/context_enforcing_controller.py`
   - Modify: `interface/controllers/task_mcp_controller.py` - Deprecate old completion

### Phase 2: Progress Tools (Week 1-2)

**Priority**: HIGH

**Files to Create/Modify**:

1. **Domain Layer**:
   - Create: `domain/events/progress_events.py`
   - Modify: `domain/entities/task.py` - Add progress tracking

2. **Application Layer**:
   - Create: `application/services/progress_tracking_service.py`
   - Create: `application/handlers/progress_event_handler.py`

3. **Interface Layer**:
   - Create: `interface/controllers/progress_tracking_controller.py`

### Phase 3: Workflow Hints (Week 2)

**Priority**: HIGH

**Files to Create/Modify**:

1. **Application Layer**:
   - Create: `application/services/workflow_guidance_service.py`
   - Create: `application/services/workflow_state_analyzer.py`

2. **Interface Layer**:
   - Create: `interface/middleware/workflow_hint_enhancer.py`
   - Modify: `mcp_entry_point.py` - Register middleware

### Phase 4: Subtask Auto-Updates (Week 2-3)

**Priority**: MEDIUM

**Files to Create/Modify**:

1. **Domain Layer**:
   - Modify: `domain/entities/task.py` - Add progress calculation
   - Create: `domain/services/progress_calculator.py`

2. **Application Layer**:
   - Modify: `application/facades/task_application_facade.py` - Auto-update logic

3. **Interface Layer**:
   - Create: `interface/controllers/subtask_progress_controller.py`

### Phase 5: Vision Enrichment (Week 3)

**Priority**: MEDIUM

**Files to Create/Modify**:

1. **Domain Layer**:
   - Create: `domain/value_objects/vision.py`
   - Create: `domain/value_objects/kpi.py`

2. **Application Layer**:
   - Create: `application/services/vision_enrichment_service.py`
   - Create: `application/services/kpi_tracking_service.py`

3. **Infrastructure Layer**:
   - Create: `infrastructure/repositories/vision_repository.py`
   - Create: `infrastructure/cache/vision_cache.py`

---

## Code Structure

### Proposed Module Organization

```
src/fastmcp/
├── task_management/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── task.py (enhanced)
│   │   │   └── context.py (enhanced)
│   │   ├── value_objects/
│   │   │   ├── vision.py (new)
│   │   │   ├── workflow_state.py (new)
│   │   │   └── kpi.py (new)
│   │   ├── events/
│   │   │   ├── progress_events.py (new)
│   │   │   └── vision_events.py (new)
│   │   └── services/
│   │       └── progress_calculator.py (new)
│   │
│   ├── application/
│   │   ├── facades/
│   │   │   ├── task_application_facade.py (enhanced)
│   │   │   └── vision_application_facade.py (new)
│   │   ├── services/
│   │   │   ├── context_validation_service.py (new)
│   │   │   ├── progress_tracking_service.py (new)
│   │   │   ├── workflow_guidance_service.py (new)
│   │   │   └── vision_enrichment_service.py (new)
│   │   └── handlers/
│   │       └── progress_event_handler.py (new)
│   │
│   ├── infrastructure/
│   │   ├── repositories/
│   │   │   ├── task_repository.py (enhanced)
│   │   │   └── vision_repository.py (new)
│   │   ├── cache/
│   │   │   └── vision_cache.py (new)
│   │   └── migrations/
│   │       └── add_vision_tables.sql (new)
│   │
│   └── interface/
│       ├── controllers/
│       │   ├── enhanced_task_mcp_controller.py (new)
│       │   ├── context_enforcing_controller.py (new)
│       │   ├── subtask_progress_controller.py (new)
│       │   └── progress_tracking_controller.py (new)
│       └── middleware/
│           └── workflow_hint_enhancer.py (new)
│
└── vision_orchestration/ (new module)
    ├── __init__.py
    ├── config/
    │   └── mcp_vision_config.yaml
    ├── templates/
    │   └── workflow_templates.yaml
    └── rules/
        └── workflow_rules.yaml
```

---

## Migration Strategy

### Database Migration

1. **Backup Current Data**:
   ```bash
   cp task_management.db task_management_backup_$(date +%Y%m%d).db
   ```

2. **Create Migration Script**:
   ```sql
   -- migrations/001_add_vision_system.sql
   BEGIN TRANSACTION;
   
   -- Add new columns to existing tables
   ALTER TABLE contexts ADD COLUMN completion_summary TEXT;
   ALTER TABLE tasks ADD COLUMN overall_progress REAL DEFAULT 0;
   
   -- Create new tables
   CREATE TABLE vision_data (...);
   CREATE TABLE progress_events (...);
   
   -- Migrate existing data
   UPDATE tasks SET overall_progress = 0 WHERE overall_progress IS NULL;
   
   COMMIT;
   ```

3. **Apply Migration**:
   ```python
   # infrastructure/migrations/migration_runner.py
   def apply_vision_migration():
       with sqlite3.connect('task_management.db') as conn:
           conn.executescript(migration_sql)
   ```

### Code Migration

1. **Feature Toggle Approach**:
   ```python
   # config.py
   VISION_FEATURES = {
       'context_enforcement': True,
       'workflow_hints': False,  # Enable gradually
       'auto_progress': False,
       'vision_enrichment': False
   }
   ```

2. **Parallel Run Period**:
   - Keep old endpoints active
   - Add new vision-enhanced endpoints
   - Monitor usage and gradually migrate

3. **Deprecation Timeline**:
   - Week 1-2: New features available
   - Week 3-4: Deprecation warnings
   - Week 5: Remove old endpoints

### Testing Strategy

1. **Unit Tests**:
   - Test each new domain rule
   - Validate context enforcement
   - Progress calculation accuracy

2. **Integration Tests**:
   - End-to-end workflow scenarios
   - Vision data enrichment
   - Event propagation

3. **Performance Tests**:
   - Vision cache effectiveness
   - Progress update overhead
   - Response time with hints

---

## Key Design Decisions

### 1. Workflow Guidance Architecture

**Decision**: Middleware Pattern

**Rationale**:
- Consistent application across all endpoints
- Easy to enable/disable
- Minimal changes to existing controllers
- Clear separation of concerns

**Alternative Considered**: Built into each controller
- Pros: More control per endpoint
- Cons: Code duplication, inconsistency risk

### 2. Vision Data Storage

**Decision**: Separate Tables with JSON Cache

**Rationale**:
- Flexible schema for vision data
- Efficient queries for alignment scores
- Cache reduces join overhead
- Easy to extend with new vision fields

**Alternative Considered**: Embedded in task table
- Pros: Simpler queries
- Cons: Table bloat, migration complexity

### 3. Context Enforcement Level

**Decision**: Both Domain and Application Layer

**Rationale**:
- Domain layer ensures business rule integrity
- Application layer provides better error messages
- Double protection against violations
- Clear separation of validation types

**Alternative Considered**: Database constraints only
- Pros: Absolute enforcement
- Cons: Poor error messages, inflexible

### 4. Progress Tracking Method

**Decision**: Event-Based with Incremental Updates

**Rationale**:
- Accurate historical tracking
- Supports complex progress scenarios
- Enables progress analytics
- Decoupled from task updates

**Alternative Considered**: Calculate on demand
- Pros: Always accurate
- Cons: Performance overhead, no history

---

## Implementation Checklist

### Week 1
- [ ] Set up vision_orchestration module structure
- [ ] Implement context enforcement in domain layer
- [ ] Create context_enforcing_controller
- [ ] Add database migration for context fields
- [ ] Write unit tests for context enforcement
- [ ] Update API documentation

### Week 2
- [ ] Implement progress tracking service
- [ ] Create progress event handlers
- [ ] Add workflow hint enhancer middleware
- [ ] Implement workflow guidance service
- [ ] Create progress tracking tools
- [ ] Integration tests for progress updates

### Week 3
- [ ] Implement subtask auto-update logic
- [ ] Create vision enrichment service
- [ ] Add vision data tables
- [ ] Implement vision caching
- [ ] Performance testing
- [ ] Update deployment scripts

### Week 4
- [ ] End-to-end testing
- [ ] Documentation updates
- [ ] Migration guide for users
- [ ] Performance optimization
- [ ] Rollback procedures
- [ ] Production deployment

---

## Risk Mitigation

1. **Performance Impact**:
   - Implement caching early
   - Use async processing for non-critical updates
   - Monitor response times

2. **Data Migration Failures**:
   - Comprehensive backup strategy
   - Incremental migration approach
   - Rollback procedures documented

3. **Breaking Changes**:
   - Feature toggles for gradual rollout
   - Parallel API versions
   - Clear deprecation timeline

4. **Integration Complexity**:
   - Extensive integration tests
   - Staged deployment
   - Monitoring and alerting

---

## Success Metrics

1. **Context Compliance**: 100% of completed tasks have completion_summary
2. **Response Time**: <50ms overhead for workflow hints
3. **Progress Accuracy**: 99%+ accuracy in parent task progress
4. **Vision Cache Hit Rate**: >90% for frequently accessed tasks
5. **Developer Adoption**: 80% using new tools within 2 weeks

---

## Conclusion

This integration design leverages the existing DDD architecture while cleanly adding vision system capabilities. The phased approach minimizes risk while delivering value incrementally. The architecture maintains clean boundaries and follows established patterns, ensuring maintainability and extensibility.

The design prioritizes developer experience through clear APIs, helpful error messages, and comprehensive workflow guidance, making it easier for AI agents to use the system correctly and efficiently.