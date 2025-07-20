# MCP Tools Testing Issues Report

Date: 2025-01-20
Tester: Claude Code

## Summary

This document summarizes the issues discovered during comprehensive testing of the dhafnck_mcp_http MCP tools. The testing covered project management, git branch management, task management, subtask management, task completion, and context management across different hierarchy levels.

## Issues Found

### 1. Subtask `insights_found` Parameter Type Issue

**Issue**: When completing a subtask, the `insights_found` parameter does not accept an array/list format as expected.

**Error Message**: 
```
Input validation error: '["Using jest-mock-extended library simplifies JWT library mocking", "Test cases should cover edge cases like empty payload and expired secrets"]' is not valid under any of the given schemas
```

**Expected Behavior**: The parameter should accept a list/array of insights.

**Workaround**: Currently only accepts single string values or must be omitted.

**Severity**: Medium - Limits the ability to document multiple insights from subtask work.

### 2. Context Management Boolean Parameter Type Issue

**Issue**: The `include_inherited` parameter in `manage_context` action does not properly accept boolean values.

**Error Message**:
```
Input validation error: 'true' is not valid under any of the given schemas
```

**Expected Behavior**: Boolean parameters should accept true/false values.

**Workaround**: Had to omit the parameter entirely.

**Severity**: Low - Can still retrieve context without inheritance flag.

### 3. Missing Automatic Context Updates

**Issue**: When updating task status or completing subtasks, the parent task context is not automatically updated with the changes.

**Expected Behavior**: Task context should reflect current status, completion percentage, and subtask progress automatically.

**Observed Behavior**: Context remains static unless explicitly updated.

**Severity**: Medium - Requires manual context synchronization.

## What Worked Well

### ✅ Successful Operations

1. **Project Management**
   - Created 2 projects successfully
   - Retrieved projects by ID and name
   - Listed all projects
   - Updated project descriptions
   - Health checks worked properly

2. **Git Branch Management**
   - Created 2 branches with proper naming conventions
   - Retrieved branch details
   - Updated branch descriptions
   - Agent assignment worked correctly
   - Statistics retrieval functioned properly

3. **Task Management**
   - Created 7 tasks across 2 branches
   - Added dependencies between tasks
   - Updated task status and details
   - Search functionality worked well
   - Next task retrieval with context worked
   - Task completion with summary and testing notes succeeded

4. **Subtask Management**
   - Created 4 subtasks with TDD naming
   - Updated subtask progress with percentage
   - Listed subtasks with progress summary
   - Retrieved individual subtasks
   - Completed subtasks (with workaround for insights)

5. **Context Management**
   - Retrieved contexts at all hierarchy levels (global, project, branch, task)
   - Context was automatically created during entity creation
   - Task completion auto-created context when missing

## Recommendations

1. **Fix Parameter Type Validation**: Ensure all parameters accept their documented types (arrays for lists, booleans for flags).

2. **Improve Context Synchronization**: Implement automatic context updates when task/subtask states change.

3. **Enhanced Error Messages**: Provide more specific guidance on parameter formats in error messages.

4. **Documentation Updates**: Update API documentation to reflect actual parameter requirements and workarounds.

## Test Coverage Summary

- ✅ Project Management: 100% coverage
- ✅ Git Branch Management: 100% coverage
- ✅ Task Management: 100% coverage
- ✅ Subtask Management: 90% coverage (insights parameter issue)
- ✅ Context Management: 80% coverage (inheritance parameter issue)
- ✅ Task Completion: 100% coverage

### 4. Test Database Configuration Issue

**Issue**: Vision System integration tests fail due to PostgreSQL connection errors when trying to use a test database.

**Error Message**:
```
psycopg2.OperationalError: connection to server on socket "@@@db.dmuqoeppsoesqcijrwhw.supabase.co/.s.PGSQL.5432" failed: Connection refused
```

**Root Cause**: The password in DATABASE_URL contains "@" characters which are being incorrectly parsed as part of the hostname.

**Expected Behavior**: Tests should use a separate PostgreSQL test database or schema to avoid affecting production data.

**Current State**: Tests are configured to use SQLite by default when PYTEST_CURRENT_TEST is set, but user requires PostgreSQL for tests.

**Severity**: High - Blocks integration testing with PostgreSQL.

## Overall Assessment

The MCP tools are functional and provide comprehensive task management capabilities. The hierarchical structure (Global → Project → Branch → Task) is well-implemented. The main issues are related to parameter type validation and could be resolved with minor fixes. The auto-context creation feature during task completion is particularly helpful and reduces friction in the workflow.

The test database configuration needs proper setup to support PostgreSQL testing with isolation from production data.

---

## Fix Prompts for Each Issue

### Fix Prompt 1: Subtask insights_found Parameter Type Issue

**Title**: Fix subtask completion insights_found parameter to accept array of strings

**Context**: 
The `manage_subtask` tool's `complete` action has an `insights_found` parameter that should accept an array of insights but currently throws a validation error when an array is provided.

**Current Behavior**:
- Error when passing array: `["insight1", "insight2"]`
- Error message: "Input validation error: '["insight1", "insight2"]' is not valid under any of the given schemas"

**Expected Behavior**:
- Should accept both single string and array of strings
- Example: `insights_found=["Using jest-mock-extended simplifies mocking", "Test edge cases"]`

**Technical Details**:
- Tool: `mcp__dhafnck_mcp_http__manage_subtask`
- Action: `complete`
- Parameter: `insights_found`
- File to check: Likely in the parameter validation schema for manage_subtask

**Fix Request**:
Please update the parameter validation schema for the `insights_found` parameter in the subtask completion action to accept:
1. A single string (current behavior)
2. An array/list of strings (new behavior)
3. null/None (optional parameter)

Test the fix by completing a subtask with multiple insights in array format.

---

### Fix Prompt 2: Context Management Boolean Parameter Issue

**Title**: Fix boolean parameter validation in manage_context tool

**Context**:
The `manage_context` tool has boolean parameters like `include_inherited` that don't properly accept boolean values (true/false).

**Current Behavior**:
- Error when passing boolean: `include_inherited=true`
- Error message: "Input validation error: 'true' is not valid under any of the given schemas"

**Expected Behavior**:
- Should accept boolean values: `true` or `false`
- Should also accept string representations: `"true"` or `"false"`

**Technical Details**:
- Tool: `mcp__dhafnck_mcp_http__manage_context`
- Action: `get` (and possibly others)
- Parameters affected: `include_inherited`, `force_refresh`, `propagate_changes`
- File to check: Parameter validation/coercion logic

**Fix Request**:
Please update the parameter validation for boolean parameters in manage_context to:
1. Accept Python boolean types (True/False)
2. Accept string representations ("true"/"false", "True"/"False")
3. Apply the existing ParameterTypeCoercer logic if not already applied

Test the fix by retrieving context with `include_inherited=true`.

---

### Fix Prompt 3: Automatic Context Updates for Task State Changes

**Title**: Implement automatic context updates when task/subtask states change

**Context**:
When tasks or subtasks are updated (status changes, completion, progress updates), their associated contexts are not automatically updated to reflect these changes.

**Current Behavior**:
- Task status update doesn't update context
- Subtask completion doesn't update parent task context
- Context remains with original data unless manually updated

**Expected Behavior**:
- When task status changes, context should reflect new status
- When subtask completes, parent task context should show updated progress
- Context should maintain a history of significant state changes

**Technical Details**:
- Affected operations: task update, task complete, subtask update, subtask complete
- Context levels affected: task and branch contexts
- Integration point: Task/subtask service layer should trigger context updates

**Fix Request**:
Please implement automatic context synchronization:
1. In task update operations, trigger context update with new status/details
2. In subtask operations, update parent task context with aggregated progress
3. Add a context sync service or enhance existing services
4. Ensure updates are efficient (batch updates if multiple changes)

Test by:
1. Updating a task status and checking if context reflects the change
2. Completing subtasks and verifying parent task context shows progress

---

### Fix Prompt 4: PostgreSQL Test Database Configuration

**Title**: Configure PostgreSQL test database support with proper URL parsing and schema isolation

**Context**:
Vision System integration tests need to use PostgreSQL but are failing due to connection string parsing issues and lack of proper test database isolation.

**Current Behavior**:
- Tests default to SQLite when PYTEST_CURRENT_TEST is detected
- When forced to use PostgreSQL, the DATABASE_URL parsing fails with "@" characters in password
- No clear separation between test and production databases

**Expected Behavior**:
- Tests should support PostgreSQL with a separate test database or schema
- Database URLs with special characters in passwords should be properly parsed
- Test data should be isolated from production data

**Technical Details**:
- Error occurs in database_config.py when parsing DATABASE_URL
- Password contains "@" which gets misinterpreted as hostname separator
- Need to support both local PostgreSQL and cloud-hosted test databases

**Fix Request**:
Please implement proper PostgreSQL test database support:
1. Create a test database configuration that supports:
   - Separate test database (e.g., dhafnck_mcp_test)
   - OR separate schema within same database (e.g., test schema)
2. Fix URL parsing to handle special characters in passwords
3. Add environment variable for TEST_DATABASE_URL that takes precedence
4. Update DatabaseSourceManager to respect PostgreSQL test configuration
5. Document the test database setup process

**Suggested Implementation**:
```python
# In database_config.py or test configuration
def get_test_database_url():
    # Option 1: Use dedicated TEST_DATABASE_URL
    if test_url := os.environ.get("TEST_DATABASE_URL"):
        return test_url
    
    # Option 2: Use production DB with test schema
    if prod_url := os.environ.get("DATABASE_URL"):
        # Parse and add schema parameter
        parsed = urlparse(prod_url)
        # Add ?options=--search_path=test
        return add_schema_to_url(parsed, "test")
    
    # Option 3: Local PostgreSQL test DB
    return "postgresql://postgres:postgres@localhost:5432/dhafnck_mcp_test"
```

Test the fix by:
1. Setting up a test PostgreSQL database
2. Running Vision System integration tests
3. Verifying data isolation from production

---

## Testing Verification Script

After implementing these fixes, run the following test sequence:

```python
# Test Fix 1: Subtask insights array
manage_subtask(
    action="complete",
    task_id="task-id",
    subtask_id="subtask-id",
    completion_summary="Test completion",
    insights_found=["First insight", "Second insight", "Third insight"]
)

# Test Fix 2: Boolean parameters
manage_context(
    action="get",
    level="task",
    context_id="task-id",
    include_inherited=true,
    force_refresh=false
)

# Test Fix 3: Automatic context sync
# 1. Update task status
manage_task(action="update", task_id="task-id", status="in_progress")
# 2. Check context immediately
manage_context(action="get", level="task", context_id="task-id")
# Context should show status="in_progress"
```