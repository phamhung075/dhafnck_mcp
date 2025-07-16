# SQLite to ORM Migration Status Report

## Overview
This report identifies all files in the dhafnck_mcp_main/src directory that still use direct SQLite imports or old SQLite repositories, indicating which parts haven't been migrated to ORM yet.

## Files Still Using Direct SQLite (`import sqlite3`)

### Infrastructure Layer - Database
1. **database/init_database.py** - Database initialization
2. **database/connection_pool.py** - SQLite connection pooling

### Infrastructure Layer - SQLite Repositories (20 files)
All files in `infrastructure/repositories/sqlite/`:
- **base_repository.py** - Base SQLite repository class
- **agent_repository.py** - Agent management
- **git_branch_repository.py** - Git branch management
- **hierarchical_context_repository.py** - Context hierarchy
- **hint_repository.py** - Hint storage
- **label_repository.py** - Label management
- **progress_event_store.py** - Progress event tracking
- **project_repository.py** - Project management
- **subtask_repository.py** - Subtask management
- **task_repository.py** - Task management
- **task_repository_optimized.py** - Optimized task operations
- **template_repository.py** - Template management

### Interface Layer Controllers (5 files)
- **controllers/context_id_detector.py**
- **controllers/git_branch_mcp_controller.py**
- **controllers/task_mcp_controller.py**
- **interface/ddd_compliant_mcp_tools.py**
- **utils/error_handler.py**

### Application Layer (4 files)
- **facades/git_branch_application_facade.py**
- **facades/subtask_application_facade.py**
- **use_cases/assign_agent.py**
- **use_cases/unassign_agent.py**

### Other Components
- **infrastructure/services/template_registry_service.py**
- **vision_orchestration/vision_integration.py**

## Repository Factories Status

### Partially Migrated (Support Both SQLite and ORM)
1. **task_repository_factory.py** - Checks DATABASE_TYPE env variable and supports both SQLite and ORM

### Not Yet Migrated (SQLite Only)
1. **project_repository_factory.py** - Only creates SQLiteProjectRepository
2. **subtask_repository_factory.py** - Only creates SQLiteSubtaskRepository
3. **git_branch_repository_factory.py** - Only creates SQLiteGitBranchRepository
4. **agent_repository_factory.py** - Only creates SQLiteAgentRepository
5. **hierarchical_context_repository_factory.py** - Only creates SQLiteHierarchicalContextRepository

## ORM Implementation Status

### Completed
- **orm/task_repository.py** - ORM implementation for tasks exists

### Missing ORM Implementations
The following repositories need ORM implementations:
- Project Repository
- Subtask Repository
- Git Branch Repository
- Agent Repository
- Hierarchical Context Repository
- Hint Repository
- Label Repository
- Progress Event Store
- Template Repository

## Migration Priority

### High Priority (Core Functionality)
1. **Project Repository** - Central to all operations
2. **Git Branch Repository** - Required for branch management
3. **Hierarchical Context Repository** - Critical for context management
4. **Agent Repository** - Required for agent management

### Medium Priority (Task Management)
1. **Subtask Repository** - Task breakdown functionality
2. **Progress Event Store** - Progress tracking
3. **Template Repository** - Template management

### Low Priority (Supporting Features)
1. **Hint Repository** - Hint storage
2. **Label Repository** - Label management

## Next Steps

1. **Create ORM Models** - Define SQLAlchemy models for all entities in `database/models.py`
2. **Implement ORM Repositories** - Create ORM versions of each repository in `repositories/orm/`
3. **Update Repository Factories** - Modify factories to support DATABASE_TYPE environment variable
4. **Update Controllers/Services** - Remove direct SQLite dependencies
5. **Migration Scripts** - Ensure data migration scripts handle all entities
6. **Testing** - Comprehensive testing of ORM implementations

## Technical Debt

### Issues to Address
1. Direct sqlite3 imports in controllers violate clean architecture
2. Repository factories have inconsistent patterns
3. Some files use both repository factory and direct SQLite repository instantiation
4. Connection pool management needs to be abstracted for multiple database types
5. Database initialization is tightly coupled to SQLite

### Recommendations
1. Create a unified database adapter interface
2. Implement dependency injection for all repository creation
3. Remove all direct sqlite3 imports from non-infrastructure layers
4. Create integration tests for both SQLite and PostgreSQL
5. Document the migration process for other developers