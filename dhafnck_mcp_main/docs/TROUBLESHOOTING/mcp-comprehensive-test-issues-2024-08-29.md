# MCP Tools Comprehensive Test Issues Report
*Test Date: 2025-08-29*  
*Tester: AI Agent*  
*Architecture: Domain-Driven Design (DDD)*

## Executive Summary
During comprehensive MCP tools testing, multiple critical issues were identified preventing proper functionality. All issues stem from improper parameter passing between layers, violating DDD architecture principles.

## 🔴 Critical Issues Requiring Immediate Fix

### Issue #1: Project Creation - User ID Parameter Mismatch
**Status:** ❌ BLOCKING  
**Affected Tool:** `mcp__dhafnck_mcp_http__manage_project`  
**Action:** `create`

#### Problem
```python
Error: ProjectApplicationFacade.create_project() got an unexpected keyword argument 'user_id'
```

#### Root Cause
The CRUD handler in the interface layer is passing `user_id` to the application facade, but the facade doesn't accept this parameter. This violates DDD architecture where:
- Interface layer should adapt external requests to domain needs
- Application layer shouldn't be aware of authentication concerns directly

#### Files Affected
- `/src/fastmcp/task_management/interface/mcp_controllers/project_mcp_controller/handlers/crud_handler.py`
- `/src/fastmcp/task_management/application/facades/project_application_facade.py`

#### DDD-Compliant Fix
```python
# In crud_handler.py - REMOVE user_id from facade call
# Line 27-30: Change from:
result = await facade.create_project(
    name=name,
    description=description,
    user_id=user_id  # REMOVE THIS LINE
)

# To:
result = await facade.create_project(
    name=name,
    description=description
)
```

#### Fix Prompt for New Session
```
Fix project creation user_id parameter issue respecting DDD architecture:

PROBLEM: Project CRUD handler passes user_id to application facade, violating DDD separation.

DDD PRINCIPLES TO FOLLOW:
1. Interface layer adapts external concerns (authentication) 
2. Application layer focuses on business logic
3. User context should be handled by repositories, not facades

FILES TO FIX:
- /src/fastmcp/task_management/interface/mcp_controllers/project_mcp_controller/handlers/crud_handler.py
  Remove user_id from facade.create_project() call (line 27-30)

VALIDATION:
- Facade should only receive business parameters (name, description)
- User context should be injected at repository level
- Interface layer can keep user_id for logging/metadata only
```

---

### Issue #2: Task Creation - User ID Parameter Mismatch
**Status:** ❌ BLOCKING  
**Affected Tool:** `mcp__dhafnck_mcp_http__manage_task`  
**Action:** `create`

#### Problem
```python
Error: CRUDHandler.create_task() got an unexpected keyword argument 'user_id'
```

#### Root Cause
Similar to Issue #1, the task controller is passing `user_id` to the CRUD handler which doesn't accept it. The handler signature doesn't include `user_id` parameter.

#### Files Affected
- `/src/fastmcp/task_management/interface/mcp_controllers/task_mcp_controller/task_mcp_controller.py`
- `/src/fastmcp/task_management/interface/mcp_controllers/task_mcp_controller/handlers/crud_handler.py`

#### DDD-Compliant Fix
The task CRUD handler should not receive user_id directly. User context should be obtained from the authenticated context at the controller level.

#### Fix Prompt for New Session
```
Fix task creation user_id parameter issue respecting DDD architecture:

PROBLEM: Task controller passes user_id to CRUD handler which doesn't accept it.

DDD PRINCIPLES:
1. Handlers should not deal with authentication directly
2. User context should flow through proper authentication middleware
3. Business operations should be user-agnostic at handler level

FILES TO CHECK:
- Task controller: How it calls crud_handler.create_task()
- CRUD handler: Current method signature
- Operation factory: How it instantiates handlers

FIX APPROACH:
1. Remove user_id from handler calls
2. Let authentication middleware handle user context
3. Use facade factory with proper user context injection
```

---

### Issue #3: Git Branch Creation - Project User Scoping Issue
**Status:** ❌ BLOCKING  
**Affected Tool:** `mcp__dhafnck_mcp_http__manage_git_branch`  
**Action:** `create`

#### Problem
```
Error: Project d2181350-0163-464b-a110-8e07dd86625c not found
```
Even though the project exists (confirmed by list operation).

#### Root Cause
User-scoped repository filtering is preventing access to projects. The MVP mode user (`mvp_user_12345`) might not have access to projects created by other users.

#### DDD-Compliant Fix
In MVP mode, repositories should not filter by user_id. This is a domain concern that should be configurable.

#### Fix Prompt for New Session
```
Fix git branch creation project not found issue respecting DDD:

PROBLEM: Projects exist but are "not found" due to user scoping in MVP mode.

DDD PRINCIPLES:
1. Domain layer defines business rules (MVP mode = no user filtering)
2. Infrastructure implements these rules in repositories
3. Configuration should drive behavior, not hardcoded logic

FILES TO CHECK:
- Repository base classes for user scoping logic
- MVP mode configuration and its impact on filtering
- Project repository implementation

FIX APPROACH:
1. In MVP mode, disable user filtering in repositories
2. Make user scoping a configurable domain rule
3. Ensure consistent behavior across all repositories
```

---

### Issue #4: Database Schema - Missing User ID in Git Branches
**Status:** ⚠️ WARNING  
**Affected Tool:** Database layer  
**Table:** `project_git_branchs`

#### Problem
```sql
null value in column "user_id" of relation "project_git_branchs" violates not-null constraint
```

#### Root Cause
The database schema requires `user_id` but the domain entities don't provide it in MVP mode.

#### DDD-Compliant Fix
Either:
1. Make `user_id` nullable in MVP mode
2. Use a default MVP user ID at repository level
3. Remove user_id requirement from git_branchs table

#### Fix Prompt for New Session
```
Fix database user_id constraint issue respecting DDD:

PROBLEM: Git branches table requires user_id but domain doesn't provide it in MVP mode.

DDD PRINCIPLES:
1. Domain model should drive database schema, not vice versa
2. Infrastructure adapts to domain needs
3. MVP mode is a domain concept that infrastructure must support

OPTIONS:
1. Make user_id nullable in database when MVP mode is enabled
2. Set default user_id in repository when saving (mvp_user_12345)
3. Remove user_id constraint from git_branchs table

RECOMMENDED: Option 2 - Repository handles MVP mode transparently
```

---

## 📋 Testing Progress Summary

### ✅ Working Operations
- Project list (with user_id workaround)
- Task list (when git_branch_id exists)
- Project health check

### ❌ Blocked Operations
- Project creation (user_id parameter issue)
- Task creation (user_id parameter issue)  
- Git branch creation (project not found issue)
- Context management (various parameter issues)

### ⚠️ Not Yet Tested
- Subtask management
- Task completion workflow
- Context hierarchy
- Global context updates

---

## 🏗️ DDD Architecture Violations Found

1. **Interface-Application Coupling**: Interface layer passing authentication concerns to application layer
2. **Repository User Scoping**: Hard-coded user filtering preventing MVP mode operation
3. **Database-Driven Design**: Schema constraints driving domain behavior instead of domain driving schema
4. **Parameter Leakage**: Authentication parameters leaking through multiple layers

---

## 🎯 Recommended Fix Order

1. **Fix Project Creation** - Foundation for all other operations
2. **Fix Task Creation** - Core functionality requirement
3. **Fix Repository User Scoping** - Affects all operations
4. **Fix Git Branch Creation** - Needed for task organization
5. **Database Schema Alignment** - Long-term stability

---

## 🔄 Testing Protocol

After each fix:
1. Make code changes respecting DDD principles
2. Restart backend: `cd /home/daihungpham/__projects__/agentic-project && echo "R" | ./docker-system/docker-menu.sh`
3. Wait 3 seconds for startup
4. Test the specific operation
5. If successful, proceed to next fix
6. If failed, analyze and correct

---

## 📝 Validation Checklist

- [ ] Project creation works without user_id errors
- [ ] Task creation works without parameter errors
- [ ] Git branch creation finds existing projects
- [ ] Database accepts entities without user_id errors
- [ ] All operations work in MVP mode
- [ ] DDD architecture principles maintained
- [ ] No authentication parameters in business logic

---

## 💡 Long-term Recommendations

1. **Implement Proper MVP Mode**: Create a domain service that handles MVP mode consistently
2. **Separate Authentication Concerns**: Use middleware/interceptors for auth, not business logic
3. **Repository Pattern Enhancement**: Make user scoping a strategy pattern, not hardcoded
4. **Database Migration**: Align schema with domain model requirements
5. **Integration Tests**: Add tests that validate MVP mode operation

---

## 📊 Impact Assessment

**Severity**: CRITICAL  
**Business Impact**: Complete blockage of MCP tool functionality  
**Technical Debt**: Medium - requires refactoring but not redesign  
**Estimated Fix Time**: 2-3 hours for all issues  
**Risk Level**: Low - fixes are isolated and testable  

---

*Document Generated: 2025-08-29 19:30:00 UTC*  
*Next Review: After fixes are implemented*