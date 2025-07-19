# Task Dependency Management Fix Summary

## Issue Identified
The original question was about task dependencies not showing up in task `get` responses. However, through investigation, I found:

1. **Task `get` responses already include dependencies correctly** - both the basic `dependencies` field and enhanced `dependency_relationships` field are properly populated.

2. **The real issue was in dependency management operations** - specifically the `add_dependency` and `remove_dependency` operations failing when trying to reference completed or archived tasks.

## Root Cause
The dependency management use cases were using `find_by_id()` which only looks for active tasks, but should use `find_by_id_all_states()` to also search completed and archived tasks.

### Files with the Bug
1. `src/fastmcp/task_management/application/use_cases/manage_dependencies.py`
   - Line 48: `dependency_task = self._task_repository.find_by_id(dependency_id)`
   - Line 118: Similar issue in `get_dependencies()` method

2. `src/fastmcp/task_management/application/facades/task_application_facade.py`
   - Line 660: `dependency_task = self._task_repository.find_by_id(TaskId(dependency_id))`

## Fix Applied

### 1. Updated ManageDependenciesUseCase
**File:** `src/fastmcp/task_management/application/use_cases/manage_dependencies.py`

**Before:**
```python
dependency_task = self._task_repository.find_by_id(dependency_id)
if not dependency_task:
    raise TaskNotFoundError(f"Dependency task {request.dependency_id} not found")
```

**After:**
```python
# Try to find dependency task in all states (active, completed, archived)
dependency_task = self._task_repository.find_by_id_all_states(dependency_id)
if not dependency_task:
    raise TaskNotFoundError(f"Dependency task {request.dependency_id} not found")
```

**Also fixed in `get_dependencies()` method:**
```python
# Search in all states for dependency details
dep_task = self._task_repository.find_by_id_all_states(self._convert_to_task_id(str(dep_id)))
```

### 2. Updated TaskApplicationFacade
**File:** `src/fastmcp/task_management/application/facades/task_application_facade.py`

**Before:**
```python
# First try to find dependency in current context
dependency_task = self._task_repository.find_by_id(TaskId(dependency_id))

# If not found and repository supports cross-context search, try that
if not dependency_task and hasattr(self._task_repository, 'find_by_id_across_contexts'):
    dependency_task = self._task_repository.find_by_id_across_contexts(TaskId(dependency_id))
```

**After:**
```python
# First try to find dependency in current context
dependency_task = self._task_repository.find_by_id(TaskId(dependency_id))

# If not found, try to find across all states (active, completed, archived)
if not dependency_task and hasattr(self._task_repository, 'find_by_id_all_states'):
    dependency_task = self._task_repository.find_by_id_all_states(TaskId(dependency_id))

# If still not found and repository supports cross-context search, try that
if not dependency_task and hasattr(self._task_repository, 'find_by_id_across_contexts'):
    dependency_task = self._task_repository.find_by_id_across_contexts(TaskId(dependency_id))
```

## Testing

Created and ran a test (`test_dependency_fix.py`) that:
1. Creates an active task
2. Creates another task and marks it as completed
3. Attempts to add the completed task as a dependency to the active task
4. Verifies the operation succeeds

**Test Result:** ✅ SUCCESS - completed tasks can now be added as dependencies.

## Impact

### Before Fix
- Users received "Dependency task with ID X not found" errors when trying to add completed/archived tasks as dependencies
- Only active tasks could be used as dependencies

### After Fix
- Completed and archived tasks can be added as dependencies
- Dependency operations work across all task states
- Backward compatibility maintained

## Repository Method Used

The fix relies on the existing `find_by_id_all_states()` method in the ORM task repository:

```python
def find_by_id_all_states(self, task_id) -> Optional[TaskEntity]:
    """Find task by ID across all states (active, completed, archived)"""
    with self.get_db_session() as session:
        # Search across all statuses without any git_branch_id filter
        # This ensures we find tasks regardless of their current state
        task = session.query(Task).options(
            joinedload(Task.assignees),
            joinedload(Task.labels).joinedload(TaskLabel.label),
            joinedload(Task.subtasks)
        ).filter(Task.id == str(task_id)).first()
        
        return self._model_to_entity(task) if task else None
```

This method was already implemented but wasn't being used by the dependency management operations.

## Status
✅ **FIXED** - Dependency management now works correctly with completed and archived tasks.