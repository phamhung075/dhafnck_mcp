# Architecture Compliance Report V7
Generated: 2025-08-28T20:32:22.127662

## Executive Summary
- **Compliance Score**: 32/100 (Grade: F)
- **Total Code Paths**: 32
- **Compliant Paths**: 21
- **Total Violations**: 11

## Violation Breakdown
- 🔴 **High Severity**: 11
- 🟡 **Medium Severity**: 0
- 🟢 **Low Severity**: 0

## Repository Factory Analysis
- **Total Factories**: 29
- **Working Factories**: 6
- **Broken Factories**: 23

### Factory Details
| Factory | Env Check | DB Check | Redis Check | Status |
|---------|-----------|----------|-------------|--------|
| repository_factory | ✅ | ✅ | ✅ | ✅ Working |
| test_git_branch_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| test_unified_context_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| test_mock_repository_factory | ❌ | ❌ | ❌ | ❌ Broken |
| test_http_server_factory | ❌ | ❌ | ❌ | ❌ Broken |
| mock_repository_factory | ❌ | ❌ | ❌ | ❌ Broken |
| project_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| rule_service_factory | ❌ | ❌ | ❌ | ❌ Broken |
| git_branch_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| project_service_factory | ❌ | ❌ | ❌ | ❌ Broken |
| task_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| subtask_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| agent_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| context_response_factory | ❌ | ❌ | ❌ | ❌ Broken |
| unified_context_facade_factory | ❌ | ❌ | ❌ | ❌ Broken |
| subtask_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| task_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| context_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| git_branch_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| agent_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| rule_workflow_factory | ❌ | ❌ | ❌ | ❌ Broken |
| template_repository_factory | ✅ | ✅ | ✅ | ✅ Working |
| mock_repository_factory | ❌ | ❌ | ❌ | ❌ Broken |
| agent_repository_factory | ✅ | ✅ | ❌ | ✅ Working |
| subtask_repository_factory | ❌ | ❌ | ❌ | ❌ Broken |
| project_repository_factory | ✅ | ✅ | ❌ | ✅ Working |
| repository_factory | ✅ | ✅ | ✅ | ✅ Working |
| task_repository_factory | ❌ | ❌ | ❌ | ❌ Broken |
| git_branch_repository_factory | ✅ | ✅ | ❌ | ✅ Working |

## Code Path Analysis

### ✅ dependency_mcp_controller.manage_dependency
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/dependency_mcp_controller.py:manage_dependency
- **Flow**: Controller(dependency_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ dependency_mcp_controller.handle_dependency_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/dependency_mcp_controller.py:handle_dependency_operations
- **Flow**: Controller(dependency_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ agent_mcp_controller.manage_agent
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/agent_mcp_controller.py:manage_agent
- **Flow**: Controller(agent_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ agent_mcp_controller.manage_agent
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/agent_mcp_controller.py:manage_agent
- **Flow**: Controller(agent_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ agent_mcp_controller.handle_crud_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/agent_mcp_controller.py:handle_crud_operations
- **Flow**: Controller(agent_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ agent_mcp_controller.handle_assignment_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/agent_mcp_controller.py:handle_assignment_operations
- **Flow**: Controller(agent_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ agent_mcp_controller.handle_rebalance_operation
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/agent_mcp_controller.py:handle_rebalance_operation
- **Flow**: Controller(agent_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ project_mcp_controller.manage_project
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/project_mcp_controller.py:manage_project
- **Flow**: Controller(project_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ project_mcp_controller.manage_project
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/project_mcp_controller.py:manage_project
- **Flow**: Controller(project_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ project_mcp_controller.handle_crud_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/project_mcp_controller.py:handle_crud_operations
- **Flow**: Controller(project_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ project_mcp_controller.handle_maintenance_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/project_mcp_controller.py:handle_maintenance_operations
- **Flow**: Controller(project_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ git_branch_mcp_controller.manage_git_branch
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/git_branch_mcp_controller.py:manage_git_branch
- **Flow**: Controller(git_branch_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ git_branch_mcp_controller.manage_git_branch
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/git_branch_mcp_controller.py:manage_git_branch
- **Flow**: Controller(git_branch_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ git_branch_mcp_controller.handle_crud_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/git_branch_mcp_controller.py:handle_crud_operations
- **Flow**: Controller(git_branch_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ git_branch_mcp_controller.handle_agent_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/git_branch_mcp_controller.py:handle_agent_operations
- **Flow**: Controller(git_branch_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ✅ git_branch_mcp_controller.handle_advanced_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/git_branch_mcp_controller.py:handle_advanced_operations
- **Flow**: Controller(git_branch_mcp_controller) → Repository(?)
- **Violations**: 0
- **Cache Invalidation**: ❌

### ❌ task_mcp_controller.manage_task
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/task_mcp_controller.py:manage_task
- **Flow**: Controller(task_mcp_controller) → Repository(?)
- **Violations**: 1
- **Cache Invalidation**: ❌

### ❌ task_mcp_controller.manage_task
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/task_mcp_controller.py:manage_task
- **Flow**: Controller(task_mcp_controller) → Repository(?)
- **Violations**: 1
- **Cache Invalidation**: ❌

### ❌ task_mcp_controller.handle_crud_operations
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/task_mcp_controller.py:handle_crud_operations
- **Flow**: Controller(task_mcp_controller) → Repository(?)
- **Violations**: 1
- **Cache Invalidation**: ❌

### ❌ task_mcp_controller.handle_list_search_next
- **Entry Point**: /home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/src/fastmcp/task_management/interface/controllers/task_mcp_controller.py:handle_list_search_next
- **Flow**: Controller(task_mcp_controller) → Repository(?)
- **Violations**: 1
- **Cache Invalidation**: ❌

## Detailed Violations
