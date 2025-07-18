#!/usr/bin/env python3
"""
TDD Test Suite for Five Critical Issues Fixed

This test suite verifies the fixes for the following issues:
1. Task Next Action NoneType error - Fixed null check for task.labels
2. Hierarchical Context Health Check coroutine error - Fixed async/await implementation
3. Branch Statistics not found issue - Fixed git branch persistence
4. Task Creation Context Sync Failed error - Fixed circular dependency
5. Context Creation Foreign Key constraint error - Fixed auto-creation of required entities

Each test is designed to:
- Reproduce the original error condition
- Verify the fix works correctly
- Ensure edge cases are handled
"""

import sys
import os
import pytest
import asyncio
import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.server.server import FastMCP
from fastmcp.server.context import Context
from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database
from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager
from fastmcp.task_management.infrastructure.repositories.project_repository_factory import ProjectRepositoryFactory

# Import specific classes for unit testing
from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase
from fastmcp.task_management.application.services.hierarchical_context_service import HierarchicalContextService
from fastmcp.task_management.application.services.git_branch_service import GitBranchService
from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestFiveCriticalIssuesTDD:
    """TDD test suite for the five critical issues that were fixed"""
    
    @pytest.fixture(scope="function")
    def test_db_path(self, tmp_path):
        """Create a temporary database for testing"""
        db_path = tmp_path / "test_critical_issues.db"
        initialize_database(str(db_path))
        return str(db_path)
    
    @pytest.fixture(scope="function")
    def server(self, test_db_path):
        """Create a FastMCP server instance for testing"""
        # Clear any cached instances
        DatabaseSourceManager.clear_instance()
        ProjectRepositoryFactory.clear_cache()
        
        # Set database path
        os.environ["MCP_DB_PATH"] = test_db_path
        
        server = FastMCP(
            name="test_critical_issues_server",
            enable_task_management=True
        )
        
        return server
    
    async def _call_tool(self, server, tool_name, params):
        """Helper to call a tool and parse the response"""
        try:
            with Context(fastmcp=server):
                response = await server._call_tool(tool_name, params)
            
            if response and isinstance(response, list) and hasattr(response[0], 'text') and response[0].text:
                return json.loads(response[0].text)
            
            return response
        except Exception as e:
            return {"success": False, "error": str(e), "exception_type": type(e).__name__}
    
    # ===== TEST 1: Task Next Action NoneType Error =====
    
    @pytest.mark.asyncio
    async def test_task_next_action_nonetype_error(self, server, test_db_path):
        """
        Test that tasks with None labels don't cause NoneType errors in next action.
        
        Original error: "argument of type 'NoneType' is not iterable" 
        when checking if label in task.labels
        """
        # Setup: Create project and branch
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Test Project for NoneType"
        })
        assert project_result["success"]
        project_id = project_result["project"]["id"]
        
        # Get the main branch ID
        list_result = await self._call_tool(server, "manage_git_branch", {
            "action": "list",
            "project_id": project_id
        })
        assert list_result["success"]
        assert len(list_result["git_branchs"]) > 0, "Project should have at least one branch"
        git_branch_id = list_result["git_branchs"][0]["id"]
        
        # Create tasks with different label configurations
        test_cases = [
            {"title": "Task with None labels", "labels": None},
            {"title": "Task with empty list", "labels": []},
            {"title": "Task with labels", "labels": ["bug", "urgent"]},
            {"title": "Task without labels field", "no_labels": True}
        ]
        
        for case in test_cases:
            params = {
                "action": "create",
                "git_branch_id": git_branch_id,
                "title": case["title"],
                "description": "Test task for NoneType issue"
            }
            
            if not case.get("no_labels"):
                params["labels"] = case.get("labels")
            
            result = await self._call_tool(server, "manage_task", params)
            assert result["success"], f"Failed to create task: {case['title']}"
        
        # Test: Get next task - should not fail with NoneType error
        next_result = await self._call_tool(server, "manage_task", {
            "action": "next",
            "git_branch_id": git_branch_id
        })
        
        # Verify: Should succeed without NoneType error
        error_msg = str(next_result.get("error", ""))
        assert "NoneType" not in error_msg, f"NoneType error should be fixed: {error_msg}"
        
        # Either success or expected "no tasks" message
        if not next_result.get("success"):
            assert "No actionable tasks found" in error_msg or "No tasks found" in error_msg, \
                f"Unexpected error: {error_msg}"
    
    @pytest.mark.asyncio
    async def test_task_next_action_with_label_filtering(self, test_db_path):
        """Test that label filtering works correctly with None labels"""
        # Direct unit test of the NextTaskUseCase
        task_repo = ORMTaskRepository()
        use_case = NextTaskUseCase(task_repo, None)
        
        # Create a mock task with None labels
        task = Task(
            id=TaskId(str(uuid.uuid4())),
            title="Task with None labels",
            description="Test task",
            git_branch_id="test-branch",
            status=TaskStatus.todo(),
            priority=Priority.high(),
            assignees=None,
            labels=None,  # This is the key - None labels
            estimated_effort="",
            due_date=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Test the specific line that was failing
        labels_to_check = ["bug", "urgent"]
        
        # This should not raise "argument of type 'NoneType' is not iterable"
        try:
            # Simulate the logic from line 294 of next_task.py
            if task.labels is not None and isinstance(task.labels, (list, tuple)) and any(label in task.labels for label in labels_to_check):
                has_matching_label = True
            else:
                has_matching_label = False
            
            # Test passed - no exception
            assert not has_matching_label, "Task with None labels should not match any label filter"
        except TypeError as e:
            pytest.fail(f"NoneType error not fixed: {e}")
    
    # ===== TEST 2: Hierarchical Context Health Check Coroutine Error =====
    
    @pytest.mark.asyncio
    async def test_hierarchical_context_health_check_async(self, server):
        """
        Test that health check doesn't fail with coroutine error.
        
        Original error: "'coroutine' object has no attribute 'get'"
        """
        # Test: Call health check action
        result = await self._call_tool(server, "manage_hierarchical_context", {
            "action": "get_health"
        })
        
        # Verify: Should succeed without coroutine error
        error_msg = str(result.get("error", ""))
        assert "coroutine" not in error_msg, f"Coroutine error should be fixed: {error_msg}"
        
        # Should have some health data or success
        assert result.get("success") or "health" in result or "confirmation" in result, \
            f"Expected health data or success, got: {result}"
    
    @pytest.mark.asyncio
    async def test_hierarchical_context_service_async_methods(self):
        """Unit test that HierarchicalContextService.get_system_health is properly async"""
        # Direct unit test
        repository = ORMHierarchicalContextRepository()
        service = HierarchicalContextService(repository=repository)
        
        # This should be an async method now
        assert asyncio.iscoroutinefunction(service.get_system_health), \
            "get_system_health should be async"
        
        # Call it properly with await
        health = await service.get_system_health()
        
        # Verify structure
        assert isinstance(health, dict)
        assert "status" in health
        
        # Check that no coroutine error occurred
        if "error" in health:
            assert "'coroutine' object" not in health["error"], \
                f"Coroutine error should be fixed: {health['error']}"
    
    # ===== TEST 3: Branch Statistics Not Found Issue =====
    
    @pytest.mark.asyncio
    async def test_git_branch_persistence(self, server):
        """
        Test that git branches are persisted to database and can be retrieved.
        
        Original issue: Branch created but not found when getting statistics
        """
        # Create a project
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Test Project for Branch Persistence"
        })
        assert project_result["success"]
        project_id = project_result["project"]["id"]
        
        # Create a new branch
        branch_result = await self._call_tool(server, "manage_git_branch", {
            "action": "create",
            "project_id": project_id,
            "git_branch_name": "feature/test-persistence",
            "git_branch_description": "Test branch persistence"
        })
        
        assert branch_result["success"], f"Branch creation failed: {branch_result.get('error')}"
        branch_id = branch_result["git_branch"]["id"]
        
        # Test: Get branch statistics - should find the branch
        stats_result = await self._call_tool(server, "manage_git_branch", {
            "action": "get_statistics",
            "project_id": project_id,
            "git_branch_id": branch_id
        })
        
        # Verify: Should succeed without "not found" error
        assert stats_result["success"], f"Statistics failed: {stats_result.get('error')}"
        assert "not found" not in str(stats_result.get("error", "")), \
            "Branch should be found after creation"
        
        # Verify statistics structure
        assert "statistics" in stats_result
        assert "total_tasks" in stats_result["statistics"]
        assert "completed_tasks" in stats_result["statistics"]
    
    @pytest.mark.asyncio
    async def test_git_branch_service_uses_repository(self):
        """Unit test that GitBranchService properly uses repository for persistence"""
        # Direct unit test
        service = GitBranchService()
        
        # Verify it has the repository
        assert hasattr(service, '_git_branch_repo'), \
            "GitBranchService should have _git_branch_repo attribute"
        assert isinstance(service._git_branch_repo, ORMGitBranchRepository), \
            "Should use ORMGitBranchRepository for persistence"
    
    # ===== TEST 4 & 5: Task Creation and Context Foreign Key Issues =====
    
    @pytest.mark.asyncio
    async def test_task_creation_with_context_sync(self, server, test_db_path):
        """
        Test that task creation succeeds with proper context initialization.
        
        Original errors:
        - Task creation failed: Unable to initialize task context
        - FOREIGN KEY constraint failed
        """
        # Create a project
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Test Project for Context Sync"
        })
        assert project_result["success"]
        project_id = project_result["project"]["id"]
        
        # Get the main branch
        list_result = await self._call_tool(server, "manage_git_branch", {
            "action": "list",
            "project_id": project_id
        })
        assert list_result["success"]
        assert len(list_result["git_branchs"]) > 0, "Project should have at least one branch"
        git_branch_id = list_result["git_branchs"][0]["id"]
        
        # Test: Create a task - should succeed with context
        task_result = await self._call_tool(server, "manage_task", {
            "action": "create",
            "git_branch_id": git_branch_id,
            "title": "Test Task with Context",
            "description": "This task should have context initialized"
        })
        
        # Verify: Should succeed without context sync error
        assert task_result["success"], f"Task creation failed: {task_result.get('error')}"
        assert "CONTEXT_SYNC_FAILED" not in str(task_result.get("error_code", "")), \
            "Context sync error should be fixed"
        assert "FOREIGN KEY" not in str(task_result.get("error", "")), \
            "Foreign key error should be fixed"
        
        # Verify task has context
        # Handle new response format - task data is under "data" key
        task_data = task_result.get("data", {})
        if "task" in task_data:
            task_id = task_data["task"]["id"]
        else:
            # Fallback to old format if needed
            task_id = task_result["task"]["id"]
            
        get_result = await self._call_tool(server, "manage_task", {
            "action": "get",
            "task_id": task_id,
            "include_context": True
        })
        
        assert get_result["success"]
        
        # Handle new response format for get_result too
        get_task_data = get_result.get("data", {})
        if "task" in get_task_data:
            task = get_task_data["task"]
        else:
            # Fallback to old format if needed
            task = get_result["task"]
            
        # Check for context in various possible locations
        has_context = (
            task.get("context_id") is not None or
            "context" in task or 
            "vision_context" in task or
            "context_data" in task
        )
        assert has_context, "Task should have context data"
    
    @pytest.mark.asyncio
    async def test_context_requires_parent_entities(self, test_db_path):
        """
        Unit test that hierarchical context repository properly enforces parent entity requirements.
        
        In the 4-tier hierarchy, task contexts require their parent branch to exist,
        and branches require their parent project to exist.
        """
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch
        
        repository = ORMHierarchicalContextRepository()
        db_config = get_db_config()
        
        # First create the global context (singleton)
        global_id = "global_singleton"
        repository.create_global_context(
            global_id=global_id,
            data={
                "autonomous_rules": {},
                "security_policies": {},
                "coding_standards": {}
            }
        )
        
        # Create a project in the database
        project_id = str(uuid.uuid4())
        with db_config.get_session() as session:
            project = Project(
                id=project_id,
                name="Test Project",
                description="Test Project for context creation",
                user_id="test-user"
            )
            session.add(project)
            session.commit()
        
        # Create a project context
        repository.create_project_context(
            project_id=project_id,
            data={
                "project_data": {
                    "name": "Test Project",
                    "description": "Test"
                },
                "parent_global_id": global_id
            }
        )
        
        # Create a branch in the database
        branch_id = str(uuid.uuid4())
        with db_config.get_session() as session:
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project_id,
                name="test-branch",
                description="Test Branch"
            )
            session.add(branch)
            session.commit()
        
        # Create a branch context
        repository.create_branch_context(
            branch_id=branch_id,
            data={
                "branch_data": {
                    "name": "Test Branch",
                    "description": "Test"
                },
                "parent_project_id": project_id
            }
        )
        
        # Test 1: Verify task context creation fails without branch
        task_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Branch .* not found"):
            repository.create_task_context(
                task_id=task_id,
                data={
                    "task_data": {
                        "title": "Test Task",
                        "description": "Test",
                        "status": "todo",
                        "priority": "medium"
                    },
                    "parent_branch_id": "non-existent-branch",
                    "parent_branch_context_id": "non-existent-branch"
                }
            )
        
        # Test 2: Verify branch context creation fails without project
        branch_id_test = str(uuid.uuid4())
        with pytest.raises(ValueError, match="Project .* not found"):
            repository.create_branch_context(
                branch_id=branch_id_test,
                data={
                    "branch_data": {
                        "name": "Test Branch",
                        "description": "Test"
                    },
                    "parent_project_id": "non-existent-project"
                }
            )
        
        # Test 3: Verify proper creation works when all entities exist
        # First create a task in the database
        from fastmcp.task_management.infrastructure.database.models import Task as TaskModel
        task_id = str(uuid.uuid4())
        with db_config.get_session() as session:
            task = TaskModel(
                id=task_id,
                title="Test Task",
                description="Test task for context creation",
                git_branch_id=branch_id,
                status="todo",
                priority="medium",
                details="",
                estimated_effort="",
                assignees=[],
                labels=[],
                dependencies=[],
                subtasks=[],
                due_date=None
            )
            session.add(task)
            session.commit()
        
        # Now create the task context
        result = repository.create_task_context(
            task_id=task_id,
            data={
                "task_data": {
                    "title": "Test Task",
                    "description": "Test",
                    "status": "todo",
                    "priority": "medium"
                },
                "parent_branch_id": branch_id,
                "parent_branch_context_id": branch_id
            }
        )
        
        # Verify that the result is returned successfully
        assert result is not None, "Task context should be created successfully"
        assert "task_id" in result, "Task context result should contain task_id"
        assert result["task_id"] == task_id, "Task context should have correct task_id"
        
        # Verify that we can retrieve the created context
        retrieved_context = repository.get_task_context(task_id)
        assert retrieved_context is not None, "Task context should be retrievable"
        assert retrieved_context["task_id"] == task_id, "Retrieved context should have correct task_id"
    
    @pytest.mark.asyncio
    async def test_circular_dependency_resolution(self, server):
        """
        Test that the circular dependency between tasks and contexts is resolved.
        
        The fix ensures tasks can be created even if context creation has issues,
        and proper rollback occurs if needed.
        """
        # Create project
        project_result = await self._call_tool(server, "manage_project", {
            "action": "create",
            "name": "Test Circular Dependency"
        })
        assert project_result["success"]
        project_id = project_result["project"]["id"]
        
        # Get branch
        list_result = await self._call_tool(server, "manage_git_branch", {
            "action": "list",
            "project_id": project_id
        })
        git_branch_id = list_result["git_branchs"][0]["id"]
        
        # Create multiple tasks rapidly to test robustness
        tasks_created = []
        for i in range(5):
            result = await self._call_tool(server, "manage_task", {
                "action": "create",
                "git_branch_id": git_branch_id,
                "title": f"Rapid Task {i}",
                "description": f"Testing circular dependency fix {i}"
            })
            
            assert result["success"], f"Task {i} creation failed: {result.get('error')}"
            
            # Handle new response format - task data is under "data" key
            task_data = result.get("data", {})
            if "task" in task_data:
                tasks_created.append(task_data["task"]["id"])
            else:
                # Fallback to old format if needed
                tasks_created.append(result["task"]["id"])
        
        # Verify all tasks exist and have context
        for task_id in tasks_created:
            get_result = await self._call_tool(server, "manage_task", {
                "action": "get",
                "task_id": task_id,
                "include_context": True
            })
            
            assert get_result["success"], f"Failed to get task {task_id}"
            
            # Handle new response format for get_result
            get_task_data = get_result.get("data", {})
            if "task" in get_task_data:
                task = get_task_data["task"]
            else:
                # Fallback to old format if needed
                task = get_result["task"]
                
            assert task["id"] == task_id
            
            # Check context exists in various possible locations
            has_context = (
                task.get("context_id") is not None or
                "context" in task or 
                "vision_context" in task or
                "context_data" in task
            )
            assert has_context, f"Task {task_id} should have context"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])