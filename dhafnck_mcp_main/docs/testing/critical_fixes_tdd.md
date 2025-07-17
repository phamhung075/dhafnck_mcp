# Critical Fixes TDD Test Suite

This document describes the Test-Driven Development (TDD) test suite created for the five critical issues that were fixed in the MCP task management system.

## Overview

The test suite verifies fixes for the following critical issues:

1. **Task Next Action NoneType Error**
   - Error: `"argument of type 'NoneType' is not iterable"`
   - Fix: Added null check for `task.labels` and `task.assignees`
   - File: `next_task.py` line 294

2. **Hierarchical Context Health Check Coroutine Error**
   - Error: `"'coroutine' object has no attribute 'get'"`
   - Fix: Made `get_system_health` async and added proper await
   - Files: `hierarchical_context_service.py`, `context_mcp_controller.py`

3. **Branch Statistics Not Found Issue**
   - Error: `"Branch {id} not found"`
   - Fix: Ensured branches are persisted using `ORMGitBranchRepository`
   - File: `git_branch_service.py`

4. **Task Creation Context Sync Failed Error**
   - Error: `"Task creation failed: Unable to initialize task context"`
   - Fix: Proper entity creation order and rollback mechanism
   - File: `task_application_facade.py`

5. **Context Creation Foreign Key Constraint Error**
   - Error: `"sqlite3.IntegrityError) FOREIGN KEY constraint failed"`
   - Fix: Auto-create missing project and project_context records
   - File: `hierarchical_context_repository.py`

## Test Structure

### Unit Tests

Located in `src/tests/unit/`:

1. **`use_cases/test_next_task_null_safety.py`**
   - Tests NextTaskUseCase handles None values correctly
   - Verifies label and assignee filtering with null safety
   - Tests edge cases and mixed null/valid scenarios

2. **`services/test_hierarchical_context_async.py`**
   - Tests HierarchicalContextService async methods
   - Verifies get_system_health is properly async
   - Tests concurrent health checks

3. **`services/test_git_branch_persistence.py`**
   - Tests GitBranchService uses repository for persistence
   - Verifies branches are saved to database
   - Tests full create->get cycle

4. **`repositories/test_hierarchical_context_auto_creation.py`**
   - Tests auto-creation of missing entities
   - Verifies foreign key constraints are prevented
   - Tests creation order and default data

### Integration Tests

Located in `src/tests/integration/`:

1. **`test_five_critical_issues_tdd.py`**
   - Comprehensive test for each individual fix
   - Reproduces original error conditions
   - Verifies fixes work in isolation

2. **`test_all_fixes_integration.py`**
   - Tests all fixes working together
   - Complete workflow testing
   - Stress testing with rapid entity creation

## Running the Tests

### Run All Critical Fixes Tests
```bash
cd dhafnck_mcp_main/src
python tests/run_critical_fixes_tests.py
```

### Run with Verbose Output
```bash
python tests/run_critical_fixes_tests.py --verbose
```

### Run Only Unit Tests
```bash
python tests/run_critical_fixes_tests.py --unit-only
```

### Run Only Integration Tests
```bash
python tests/run_critical_fixes_tests.py --integration-only
```

### Include Related Existing Tests
```bash
python tests/run_critical_fixes_tests.py --include-related
```

### Run Individual Test Files
```bash
# Unit test example
pytest tests/unit/use_cases/test_next_task_null_safety.py -v

# Integration test example
pytest tests/integration/test_five_critical_issues_tdd.py -v
```

## Test Scenarios

### 1. NoneType Error Test Scenarios
- Tasks with `labels=None`
- Tasks with `assignees=None`
- Tasks with both `None`
- Tasks with empty lists
- Mixed valid and null values

### 2. Coroutine Error Test Scenarios
- Direct health check calls
- Concurrent health checks
- Controller integration
- Error handling in async context

### 3. Branch Persistence Test Scenarios
- Create branch and get statistics
- Multiple branch operations
- Branch not found prevention
- Repository usage verification

### 4. Context Sync Test Scenarios
- Task creation with context
- Rollback on context failure
- Circular dependency resolution
- Multiple rapid task creation

### 5. Foreign Key Test Scenarios
- Missing project auto-creation
- Missing project context auto-creation
- Proper entity creation order
- Default data for auto-created entities

## Expected Results

All tests should pass, indicating:

- ✅ No NoneType errors when filtering tasks
- ✅ No coroutine errors in health checks
- ✅ Branches persist and can be retrieved
- ✅ Tasks create successfully with context
- ✅ No foreign key constraint violations

## Debugging Failed Tests

If tests fail:

1. Check database initialization
2. Verify all fixes are applied to source code
3. Check for environment-specific issues
4. Review test output for specific error messages
5. Run individual tests with `-v` for detailed output

## Future Improvements

1. Add performance benchmarks
2. Add mutation testing
3. Add property-based testing for edge cases
4. Add load testing for concurrent operations
5. Add regression test automation