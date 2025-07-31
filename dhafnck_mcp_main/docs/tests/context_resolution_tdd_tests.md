# Context Resolution TDD Tests Documentation

## Overview

This document describes the Test-Driven Development (TDD) tests created to ensure the context resolution issue doesn't recur. The issue involved branch IDs being incorrectly resolved as task contexts, causing "Context not found" errors.

## Issue Summary

**Problem**: Branch ID `d4f91ee3-1f97-4768-b4ff-1e734180f874` was being resolved as a task context instead of a branch context, causing frontend errors.

**Root Cause**: Frontend was calling `getTaskContext()` with a branch ID instead of `getBranchContext()`.

**Fix**: 
1. Created `getBranchContext()` function in `api.ts`
2. Updated `ProjectList.tsx` to use `getBranchContext()` for branches

## TDD Test Files Created

### 1. Integration Tests

#### `/src/tests/integration/test_context_resolution_differentiation.py`
- **Purpose**: Comprehensive integration tests for context resolution
- **Key Tests**:
  - `test_resolve_branch_context_with_branch_level`: Verifies branch IDs resolve correctly with level='branch'
  - `test_resolve_task_context_with_task_level`: Verifies task IDs resolve correctly with level='task'
  - `test_branch_id_fails_with_task_level`: Ensures branch IDs fail when resolved as tasks
  - `test_task_id_fails_with_branch_level`: Ensures task IDs fail when resolved as branches
  - `test_auto_level_detection_for_branch`: Tests automatic level detection
  - `test_context_inheritance_from_branch_to_task`: Verifies inheritance chain
  - `test_frontend_api_pattern_branch_context`: Tests exact frontend API pattern

#### `/src/tests/integration/test_context_resolution_simple.py`
- **Purpose**: Simplified integration tests without complex fixtures
- **Key Tests**:
  - `test_branch_context_resolution`: Basic branch context resolution
  - `test_task_context_resolution`: Basic task context resolution
  - `test_frontend_api_pattern_for_branches`: Exact frontend pattern testing

### 2. Unit Tests

#### `/src/tests/unit/test_frontend_context_api_patterns.py`
- **Purpose**: Unit tests for frontend API patterns
- **Key Tests**:
  - `test_get_branch_context_api_pattern`: Verifies getBranchContext API calls
  - `test_get_task_context_api_pattern`: Verifies getTaskContext API calls
  - `test_wrong_level_returns_error`: Error handling for wrong levels
  - `test_manage_context_action_mapping`: Action parameter mapping
  - `test_inheritance_data_structure`: Inheritance structure validation

#### `/src/tests/unit/test_context_level_differentiation.py`
- **Purpose**: Focused unit tests documenting the fix
- **Key Tests**:
  - `test_branch_id_resolved_as_branch_not_task`: Documents the core issue and fix
  - `test_frontend_api_patterns`: Documents correct API patterns
  - `test_context_hierarchy_levels`: Documents 4-tier hierarchy

### 3. End-to-End Tests

#### `/src/tests/e2e/test_branch_context_resolution_e2e.py`
- **Purpose**: E2E tests simulating production scenario
- **Key Tests**:
  - `test_frontend_branch_context_resolution_pattern`: Tests exact frontend pattern
  - `test_old_pattern_that_was_failing`: Documents what was failing
  - `test_correct_task_context_resolution`: Ensures tasks still work
  - `test_list_contexts_at_different_levels`: Level-specific listing
  - `test_error_message_improvement`: Clear error messages

### 4. Frontend Tests

#### `/dhafnck-frontend/src/__tests__/api.context.test.ts`
- **Purpose**: TypeScript tests for frontend API functions
- **Key Tests**:
  - `getBranchContext` tests: Correct branch level usage
  - `getTaskContext` tests: Correct task context usage
  - Context level differentiation tests
  - Inheritance data handling tests

## Test Patterns

### 1. Correct Pattern for Branches
```typescript
getBranchContext(branchId) // Uses level='branch'
```

### 2. Correct Pattern for Tasks
```typescript
getTaskContext(taskId) // Uses action='get' with task_id
```

### 3. Error Pattern (What Was Fixed)
```typescript
// WRONG - This was causing the error
getTaskContext(branchId) // Branch ID used as task context
```

## Key Assertions

1. **Level Matching**: Context ID must match the specified level
2. **Error Handling**: Wrong level returns clear error message
3. **Inheritance**: Branch contexts inherit from project/global
4. **API Consistency**: Frontend API calls use correct parameters

## Running the Tests

```bash
# All context resolution tests
python -m pytest src/tests -k "context_resolution" -v

# Unit tests only
python -m pytest src/tests/unit/test_context_level_differentiation.py -v

# Frontend tests
cd dhafnck-frontend && npm test -- api.context.test.ts
```

## Test Coverage

The tests cover:
- ✅ Branch context resolution with correct level
- ✅ Task context resolution with correct level
- ✅ Error handling for mismatched levels
- ✅ Frontend API function correctness
- ✅ Inheritance chain validation
- ✅ Production scenario simulation

## Maintenance

These tests ensure:
1. Branch IDs are always resolved as branch contexts
2. Task IDs are always resolved as task contexts
3. Frontend uses the correct API functions
4. Error messages are clear when levels mismatch
5. The 4-tier hierarchy is properly maintained