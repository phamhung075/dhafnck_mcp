# Comprehensive MCP Testing Issues Report
**Date**: 2025-08-29
**Test Protocol**: MCP Tool Comprehensive Testing
**Current Session**: 2025-08-29 (Follow-up Testing)
**Test Agent**: @test_orchestrator_agent

## Executive Summary
Comprehensive testing of MCP tools revealed multiple critical issues across various management operations. The issues primarily affect git branch management, task management, subtask management, and context management operations.

## Current Testing Session (2025-08-29 Follow-up)

### Testing Status
- ✅ **Completed**: Verification of previously identified issues
- 🔄 **Protocol**: Test → Stop on Error → Document → Continue
- 🎯 **Focus**: Verify issue status and test any fixes since previous session

### Current Session Results

#### ✅ Working Features
1. **Project Management**
   - List projects: ✅ Working
   - Get project: ✅ Working
   - All project operations functional

#### ❌ Still Broken Features

1. **Git Branch Management**
   - Get operation: ❌ Still failing with "Project repository creation requires user authentication"
   - Update operation: ❌ Still failing with "unexpected keyword argument 'project_id'"

2. **Task Management**
   - Create: ⚠️ Works but status validation is inconsistent
     - MCP validator accepts: pending, in_progress, completed, blocked, cancelled
     - Domain accepts: cancelled, review, blocked, done, testing, in_progress, archived, todo
     - Must omit status parameter to use default "todo"
   - Search: ❌ Still failing with "Task ID value must be a string, got <class 'uuid.UUID'>"

3. **Subtask Management**
   - Create: ❌ Still failing with "Task {id} not found" even for just-created tasks

4. **Context Management**
   - Create: ❌ Inconsistent - says "already exists" but get returns "not found"
   - Get: ❌ Returns "not found" even after create says it exists

### Summary of Verification
- **No improvements detected** since previous testing session
- All previously identified critical issues remain unresolved
- Status validation inconsistency in tasks is still present
- Context management has same create/get inconsistency

## Issues Found During Testing

### 1. Git Branch Management Issues

#### Issue 1.1: Git Branch Get Operation Failure
- **Action**: `manage_git_branch` with `action="get"`
- **Error**: "Project repository creation requires user authentication. No user ID was provided."
- **Severity**: High
- **Impact**: Cannot retrieve individual git branch details
- **Test Data**: 
  - Project ID: `a710de26-4e2d-42cb-8f54-a20786489c82`
  - Branch ID: `8d3241c5-37e0-430b-b31c-fefb90a2cdca`

#### Issue 1.2: Git Branch Update Operation Failure
- **Action**: `manage_git_branch` with `action="update"`
- **Error**: "GitBranchApplicationFacade.update_git_branch() got an unexpected keyword argument 'project_id'"
- **Severity**: Critical
- **Impact**: Cannot update git branch descriptions or properties
- **Root Cause**: Method signature mismatch - `project_id` parameter not expected

#### Issue 1.3: Agent Assignment Failure
- **Action**: `manage_git_branch` with `action="assign_agent"`
- **Error**: "'GitBranchApplicationFacade' object has no attribute 'assign_agent'"
- **Severity**: Critical
- **Impact**: Cannot assign agents to git branches
- **Root Cause**: Missing method implementation in GitBranchApplicationFacade

### 2. Task Management Issues

#### Issue 2.1: Task Status Validation Inconsistency
- **Action**: `manage_task` with `action="create"`
- **Error**: Conflicting validation messages for status field
- **Severity**: High
- **Details**: 
  - Validator says: "pending, in_progress, completed, blocked, cancelled"
  - Domain says: "cancelled, review, blocked, done, testing, in_progress, archived, todo"
- **Impact**: Confusion about valid task statuses

#### Issue 2.2: Task Update Missing Project ID
- **Action**: `manage_task` with `action="update"`
- **Error**: "project_id is required"
- **Severity**: Medium
- **Impact**: Cannot update tasks without providing project_id
- **Note**: Task should be identifiable by task_id alone

#### Issue 2.3: Task Search UUID Error
- **Action**: `manage_task` with `action="search"`
- **Error**: "Task ID value must be a string, got <class 'uuid.UUID'>"
- **Severity**: High
- **Impact**: Search functionality broken
- **Root Cause**: Type conversion issue with UUID handling

#### Issue 2.4: Task List Returns All Tasks
- **Action**: `manage_task` with `action="list"`
- **Issue**: Returns all tasks across all branches, not filtered by git_branch_id
- **Severity**: Medium
- **Impact**: Cannot get tasks for specific branch only
- **Expected**: Should filter by git_branch_id when provided

#### Issue 2.5: Task Dependency Operations Not Working
- **Action**: `manage_task` with `action="add_dependency"`
- **Error**: Parameter validation errors
- **Severity**: High
- **Impact**: Cannot create task dependencies
- **Issues**:
  - Dependencies parameter during create doesn't accept list or string formats
  - add_dependency action has parameter issues

#### Issue 2.6: Task Completion Requires Project ID
- **Action**: `manage_task` with `action="complete"`
- **Error**: "project_id is required"
- **Severity**: Medium
- **Impact**: Cannot complete tasks without project_id
- **Note**: Should work with just task_id

### 3. Subtask Management Issues

#### Issue 3.1: Subtask Creation Task Not Found
- **Action**: `manage_subtask` with `action="create"`
- **Error**: "Task {task_id} not found"
- **Severity**: Critical
- **Impact**: Cannot create subtasks for any tasks
- **Test Cases**:
  - Task ID: `a3a18503-64c9-46b0-83ee-ef72104bb9c0` (newly created)
  - Task ID: `c0d28762-29bd-43ab-b5f8-af9bbd8ec997` (existing)
- **Root Cause**: Possible project/branch scope issue in task lookup

### 4. Context Management Issues

#### Issue 4.1: Context Creation Success But Get Fails
- **Action**: `manage_context` with `action="create"` then `action="get"`
- **Issue**: Context creation reports success but get returns "not found"
- **Severity**: High
- **Impact**: Context data not accessible after creation
- **Test Cases**:
  - Project context: `a710de26-4e2d-42cb-8f54-a20786489c82`
  - Branch context: `8d3241c5-37e0-430b-b31c-fefb90a2cdca`

#### Issue 4.2: Branch Context Already Exists Error
- **Action**: `manage_context` with `action="create"` for branch
- **Error**: "Branch context already exists"
- **Issue**: Inconsistent - says exists during create but not found during get
- **Severity**: High
- **Impact**: Context state inconsistency

## Summary of Critical Issues

### Broken Features (Cannot Use At All)
1. Git branch update
2. Git branch agent assignment  
3. Subtask creation
4. Task dependency management
5. Task search

### Partially Working Features (Limited Functionality)
1. Git branch get (authentication issue)
2. Task update (requires project_id)
3. Task completion (requires project_id)
4. Task list (no branch filtering)
5. Context management (creation/retrieval mismatch)

### Working Features
1. Project management (create, list, get, update, health check)
2. Git branch creation and list
3. Task creation (without dependencies)
4. Basic task list (all tasks)

## Recommended Fixes Priority

### Priority 1 (Critical - System Unusable)
1. Fix subtask creation - task lookup scope issue
2. Fix git branch update - remove project_id parameter requirement
3. Fix git branch agent assignment - implement missing method

### Priority 2 (High - Major Features Broken)
1. Fix task search - UUID type handling
2. Fix task dependency operations
3. Fix context management consistency
4. Fix task status validation inconsistency

### Priority 3 (Medium - Usability Issues)
1. Fix task update/complete to not require project_id
2. Fix task list to properly filter by git_branch_id
3. Fix git branch get authentication issue

## Fix Prompts for Each Issue

### Fix Prompt 1: Git Branch Update Parameter Issue
```
Fix the git branch update operation in GitBranchApplicationFacade. The update_git_branch method is receiving an unexpected 'project_id' parameter. The method should either:
1. Accept and ignore the project_id parameter, OR
2. The MCP controller should not pass project_id to this method

File: dhafnck_mcp_main/src/fastmcp/task_management/application/facades/git_branch_application_facade.py
Error: GitBranchApplicationFacade.update_git_branch() got an unexpected keyword argument 'project_id'
```

### Fix Prompt 2: Git Branch Agent Assignment Missing Method
```
Implement the assign_agent method in GitBranchApplicationFacade. The method is called but not defined.

File: dhafnck_mcp_main/src/fastmcp/task_management/application/facades/git_branch_application_facade.py
Error: 'GitBranchApplicationFacade' object has no attribute 'assign_agent'
Required: Implement assign_agent(git_branch_id, agent_id) method
```

### Fix Prompt 3: Subtask Creation Task Lookup Issue
```
Fix subtask creation in SubtaskApplicationFacade. The create_subtask method cannot find tasks even though they exist. The issue appears to be with task lookup scope or project/branch context.

Error: "Task {task_id} not found" for valid task IDs
Files to check:
- dhafnck_mcp_main/src/fastmcp/task_management/application/facades/subtask_application_facade.py
- Task repository lookup methods
```

### Fix Prompt 4: Task Search UUID Type Error
```
Fix the task search operation to properly handle UUID types. The search is failing with "Task ID value must be a string, got <class 'uuid.UUID'>".

Error location: Task search operation
Fix: Ensure UUID is converted to string before processing
```

### Fix Prompt 5: Task Status Validation Inconsistency
```
Fix task status validation inconsistency. The MCP validator and domain validator have different valid status lists:
- MCP Validator: pending, in_progress, completed, blocked, cancelled
- Domain: cancelled, review, blocked, done, testing, in_progress, archived, todo

Align these to use consistent status values across the system.
```

### Fix Prompt 6: Context Management Get/Create Inconsistency
```
Fix context management where creation succeeds but retrieval fails. Context creation returns success but subsequent get operations return "Context not found".

Test case:
1. Create context for project/branch - returns success
2. Get same context - returns not found

Check context persistence and retrieval logic.
```

## Testing Validation Requirements

After fixes are implemented:
1. Restart backend
2. Verify in database (Supabase/SQLite)
3. Retest each fixed operation
4. Ensure no regression in working features
5. Update this report with resolution status

## Conclusion

The MCP tool system has significant issues that prevent normal operation. The most critical issues are in subtask management, git branch operations, and task dependencies. These need immediate attention to restore system functionality.

**Total Issues Found**: 15
**Critical Issues**: 5
**High Priority Issues**: 6
**Medium Priority Issues**: 4