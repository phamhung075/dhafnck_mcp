# DhafnckMCP Issues Fix Prompts

This document contains prompts for fixing issues discovered during dhafnck_mcp_http tools testing on 2025-07-16.

## Issue 1: SQLAlchemy Database Connection Error

### Prompt for Claude Session 1
```
I'm working on the dhafnck_mcp_http project and encountering a critical database connection error:

Error: 'SQLAlchemyConnectionWrapper' object has no attribute 'cursor'

This error appears in multiple places:
1. Task creation (partial failure - tasks created but error returned)
2. Subtask creation (complete failure)
3. Context creation (complete failure)

The error suggests that the SQLAlchemyConnectionWrapper is trying to use a cursor attribute that doesn't exist. This might be because:
- The wrapper is expecting a raw database connection instead of SQLAlchemy session
- There's a mismatch between database adapter interfaces
- The code is mixing SQLAlchemy ORM with raw SQL execution

Please help me:
1. Locate all instances where 'cursor' is being accessed on SQLAlchemy objects
2. Fix the database connection wrapper to properly handle SQLAlchemy sessions
3. Ensure consistent database access patterns throughout the codebase
4. Add proper error handling to prevent partial failures

Project structure context:
- Backend: FastAPI with SQLAlchemy
- Database: PostgreSQL
- The issue appears in task management and context management modules
```

## Issue 2: Task Creation API Inconsistency

### Prompt for Claude Session 2
```
I have an API consistency issue in dhafnck_mcp_http where task creation returns errors but still creates tasks in the database.

Current behavior:
- API returns: {"success": false, "error": "The task create operation could not be completed."}
- But the task is actually created in the database
- This causes confusion as the API response doesn't match the actual result

This appears to be a transaction handling issue where:
1. The task is created successfully
2. A subsequent operation fails (possibly context creation)
3. The error is returned but the transaction isn't rolled back

Please help me:
1. Review the task creation endpoint logic
2. Implement proper database transaction handling
3. Ensure all-or-nothing behavior (complete success or complete rollback)
4. Fix the response to accurately reflect what happened
5. Add integration tests to verify transaction behavior

The endpoint should either:
- Complete all operations and return success
- Fail and rollback everything, returning an error
```

## Issue 3: File Permission Error in Next Task Feature

### Prompt for Claude Session 3
```
The "next task" feature in dhafnck_mcp_http is failing with a permission error:

Error: [Errno 13] Permission denied: '/home/daihungpham'

When calling: manage_task(action="next", git_branch_id="...", include_context=true)

This suggests the code is trying to access the user's home directory inappropriately. The feature should:
1. Only access project-specific directories
2. Use configured paths from environment variables
3. Not require access to user home directories

Please help me:
1. Find where the next task action is trying to access the home directory
2. Remove any hardcoded paths or inappropriate directory access
3. Ensure all file operations use proper project paths
4. Add validation to prevent accessing directories outside the project scope
5. Review security implications of file system access

Expected behavior: The next task feature should work entirely with database operations and configured project paths.
```

## Issue 4: Context Creation Failures

### Prompt for Claude Session 4
```
Context creation is completely broken in dhafnck_mcp_http with multiple related issues:

1. Cannot create contexts due to SQLAlchemy cursor error
2. Tasks cannot be completed without contexts
3. Hierarchical context resolution fails because contexts don't exist

The context system appears to be a critical component that:
- Is required for task completion
- Supports hierarchical inheritance (Global → Project → Task)
- Manages task metadata and state

Current errors:
- manage_context(action='create') fails with cursor error
- manage_task(action='complete') fails requiring context
- manage_hierarchical_context resolution fails with "context not found"

Please help me:
1. Fix the context creation to work with SQLAlchemy properly
2. Review why contexts are mandatory for task completion
3. Consider making context creation automatic when creating tasks/projects
4. Ensure hierarchical context inheritance works correctly
5. Add fallback behavior if contexts are missing

The system should either:
- Auto-create contexts when entities are created
- Allow operations to work without contexts (graceful degradation)
- Provide clear context initialization workflows
```

## Issue 5: Subtask System Complete Failure

### Prompt for Claude Session 5
```
The entire subtask management system in dhafnck_mcp_http is non-functional:

Error when creating subtask:
- "Validation failed for field: general"
- "Failed to create subtask: 'SQLAlchemyConnectionWrapper' object has no attribute 'cursor'"

This prevents:
1. Breaking down tasks into smaller units
2. Tracking granular progress
3. Testing the complete task hierarchy

The subtask system should:
- Allow creating multiple subtasks under a parent task
- Track individual subtask progress
- Update parent task progress automatically
- Support subtask dependencies

Please help me:
1. Fix the database connection issue in subtask creation
2. Review the subtask validation logic
3. Ensure subtask-task relationship is properly configured
4. Add cascade operations for parent task updates
5. Implement comprehensive subtask CRUD operations

Expected functionality:
- Create subtasks with proper parent-child relationships
- Update subtask progress
- Automatically calculate parent task progress
- Delete subtasks without affecting other subtasks
```

## Issue 6: API Response Format Inconsistency

### Prompt for Claude Session 6
```
The dhafnck_mcp_http API has inconsistent error response formats across different endpoints:

Examples of different formats:
1. {"success": false, "error": "message"}
2. {"status": "failure", "error": {"message": "...", "code": "..."}}
3. {"success": false, "error": "message", "error_code": "code", "recovery_instructions": [...]}

This inconsistency makes it difficult to:
- Handle errors uniformly in clients
- Provide consistent user experience
- Build reliable error handling

Please help me:
1. Define a standard error response format
2. Create a centralized error handling mechanism
3. Update all endpoints to use the standard format
4. Include consistent fields: success, error_code, message, details, recovery_hints
5. Add API response schemas/models for validation

Suggested standard format:
{
  "success": boolean,
  "data": {} (on success),
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {} (optional technical details),
    "recovery": [] (optional recovery steps)
  },
  "metadata": {} (optional request metadata)
}
```

## Issue 7: Missing Auto-Context Creation

### Prompt for Claude Session 7
```
The dhafnck_mcp_http system requires contexts for operations but doesn't create them automatically:

Current issues:
1. Creating a project doesn't create a project context
2. Creating a task doesn't create a task context
3. Users must manually create contexts before completing tasks
4. This breaks the natural workflow

Expected behavior:
- When a project is created → auto-create project context
- When a task is created → auto-create task context
- Contexts should be transparent to users unless they need customization

Please help me:
1. Add automatic context creation in project creation flow
2. Add automatic context creation in task creation flow
3. Ensure contexts inherit properly (task inherits from project, project from global)
4. Make context creation errors non-blocking (log but continue)
5. Add a system to retroactively create missing contexts

The goal is to make the context system invisible to users while maintaining its benefits for the system.
```

## Issue 8: Transaction and Data Integrity

### Prompt for Claude Session 8
```
The dhafnck_mcp_http system has data integrity issues where operations partially succeed:

Problems:
1. Task creation fails but tasks still appear in database
2. No proper transaction rollback on errors
3. Inconsistent state between API responses and database

This suggests:
- Missing or improperly configured database transactions
- Error handling that doesn't trigger rollbacks
- Multiple database operations not wrapped in single transaction

Please help me:
1. Review all database operations for proper transaction handling
2. Implement unit-of-work pattern for complex operations
3. Ensure ACID compliance for all operations
4. Add transaction decorators/context managers
5. Implement comprehensive rollback on any error

Example fix pattern:
```python
async def create_task_with_context(data):
    async with db.transaction():
        task = await create_task(data)
        context = await create_context(task.id)
        if not context:
            raise RollbackException()
        return task
```

All multi-step operations should succeed completely or fail completely.
```

## Documentation Update Prompt

### Prompt for Documentation Session
```
I need to create a comprehensive testing report and issue resolution tracking document for dhafnck_mcp_http.

Please create a document that includes:

1. Testing Summary
   - Date of testing
   - Tools/features tested
   - Overall success rate

2. Issues Discovered
   - Detailed list of all issues
   - Severity levels (Critical/High/Medium/Low)
   - Impact on functionality

3. Root Cause Analysis
   - Database connection architecture issues
   - Transaction handling problems
   - API design inconsistencies

4. Resolution Status Tracking Table
   | Issue | Severity | Status | Assigned To | Fix PR | Notes |
   |-------|----------|--------|-------------|---------|-------|

5. Lessons Learned
   - Architecture improvements needed
   - Testing gaps identified
   - Development process improvements

6. Recommendations
   - Priority order for fixes
   - Architecture refactoring suggestions
   - Testing strategy improvements

Please format this as a professional technical report that can be shared with the development team.
```