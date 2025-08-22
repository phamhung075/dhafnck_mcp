# MCP Tools Testing Issues Report
**Date**: 2025-08-22
**Test Environment**: dhafnck_mcp_http MCP server

## Summary
This document outlines issues discovered during comprehensive testing of the MCP tools functionality.

## Issues Found

### 1. Git Branch Creation Failure - Missing user_id
**Severity**: High
**Component**: manage_git_branch
**Action**: create
**Error**: 
```
null value in column "user_id" of relation "project_git_branchs" violates not-null constraint
```
**Details**: Cannot create new git branches due to missing user_id field that is required in database but not exposed in API parameters.

### 2. Branch Context Creation Failure - Missing user_id
**Severity**: High
**Component**: manage_context
**Action**: create (branch level)
**Error**:
```
null value in column "user_id" of relation "branch_contexts" violates not-null constraint
```
**Details**: Cannot create branch-level contexts due to missing user_id field requirement.

### 3. Agent Assignment Failure - Missing user_id
**Severity**: Medium
**Component**: manage_git_branch
**Action**: assign_agent
**Error**:
```
AgentFacadeFactory.create_agent_facade() missing 1 required positional argument: 'user_id'
```
**Details**: Cannot assign agents to branches due to missing user_id parameter in facade factory.

### 4. Label Creation Failure - Missing user_id
**Severity**: Medium
**Component**: manage_task
**Action**: create (with labels)
**Error**:
```
null value in column "user_id" of relation "labels" violates not-null constraint
```
**Details**: Cannot create tasks with labels due to missing user_id field when creating new labels.

### 5. Task List Returns All Tasks Across Projects
**Severity**: Low
**Component**: manage_task
**Action**: list
**Details**: When listing tasks for a specific git_branch_id, the API returns tasks from all projects/branches, not just the specified branch.

### 6. Progress Percentage Not Reflected in Subtask Response
**Severity**: Low
**Component**: manage_subtask
**Action**: update, complete
**Details**: The progress field in subtask responses always shows 0% even after updates with progress_percentage parameter.

### 7. Branch Context Does Not Auto-Create
**Severity**: Medium
**Component**: manage_context
**Action**: resolve (branch level)
**Details**: Branch contexts are not automatically created when branches are created, leading to "Context not found" errors.

## System-Wide Pattern
Most issues revolve around missing `user_id` field that is:
- Required in database schema
- Not exposed in MCP tool parameters
- Not automatically populated from authentication context

## Impact Assessment
- **High Impact**: Cannot create new branches or use multi-branch workflows
- **Medium Impact**: Cannot use agent assignment or labels features
- **Low Impact**: Minor UI/UX issues with task listing and progress tracking

## Recommendations
1. Add user_id as optional parameter to all affected tools
2. Auto-populate user_id from authentication context if not provided
3. Make user_id nullable in database schema for anonymous operations
4. Fix task list filtering to respect git_branch_id parameter
5. Ensure progress calculations are properly reflected in responses
6. Auto-create contexts when creating branches

## Fix Prompts for Each Issue

### Issue 1: Fix Git Branch Creation - Missing user_id
```
Fix the git branch creation failure in dhafnck_mcp_main. The error is:
"null value in column 'user_id' of relation 'project_git_branchs' violates not-null constraint"

The issue occurs when calling manage_git_branch with action="create". 

Fix requirements:
1. Check the database schema at dhafnck_mcp_main/database/schema/project_git_branchs.sql
2. Modify the GitBranchApplicationFacade to handle missing user_id
3. Either make user_id nullable in schema OR auto-populate from auth context
4. Update the MCP tool interface if user_id should be an optional parameter
5. Test the fix by creating a new branch successfully
```

### Issue 2: Fix Branch Context Creation - Missing user_id  
```
Fix the branch context creation failure. The error is:
"null value in column 'user_id' of relation 'branch_contexts' violates not-null constraint"

This happens when calling manage_context with action="create" and level="branch".

Fix requirements:
1. Check branch_contexts table schema
2. Update ContextApplicationFacade to handle missing user_id
3. Consider inheriting user_id from parent project context
4. Ensure branch context auto-creates when branch is created
5. Test by creating a branch and verifying its context exists
```

### Issue 3: Fix Agent Assignment - Missing user_id
```
Fix agent assignment to branches. The error is:
"AgentFacadeFactory.create_agent_facade() missing 1 required positional argument: 'user_id'"

This occurs in manage_git_branch with action="assign_agent".

Fix requirements:
1. Update AgentFacadeFactory.create_agent_facade() signature
2. Make user_id optional with default value
3. Or extract user_id from request context/auth
4. Test by assigning an agent to a branch successfully
```

### Issue 4: Fix Label Creation - Missing user_id
```
Fix task label creation failure. The error is:
"null value in column 'user_id' of relation 'labels' violates not-null constraint"

This happens when creating tasks with labels parameter.

Fix requirements:
1. Check labels table schema
2. Update label creation logic in TaskApplicationFacade
3. Make user_id nullable or auto-populate
4. Consider sharing labels across users if user_id is null
5. Test by creating a task with labels successfully
```

### Issue 5: Fix Task List Filtering
```
Fix task list returning all tasks instead of filtered by branch.

When calling manage_task with action="list" and git_branch_id parameter,
it returns tasks from all branches/projects.

Fix requirements:
1. Check TaskApplicationFacade.list_tasks() method
2. Ensure git_branch_id filter is properly applied in query
3. Verify the SQL query includes WHERE clause for git_branch_id
4. Test that list returns only tasks from specified branch
```

### Issue 6: Fix Subtask Progress Tracking
```
Fix subtask progress percentage not updating in responses.

When updating subtasks with progress_percentage, the response always shows 0%.

Fix requirements:
1. Check SubtaskApplicationFacade update logic
2. Ensure progress_percentage is stored and retrieved correctly
3. Verify parent task progress aggregation works
4. Test that progress updates are reflected in responses
```

### Issue 7: Auto-Create Branch Contexts
```
Implement automatic branch context creation when branches are created.

Currently, branch contexts must be manually created, causing "Context not found" errors.

Fix requirements:
1. Update GitBranchApplicationFacade.create_branch()
2. After branch creation, automatically create its context
3. Initialize with default branch context data
4. Inherit from parent project context
5. Test that new branches have contexts immediately available
```