"""Integration tests for NextTaskUseCase NoneType error fix

Tests the complete flow through the MCP controller to ensure NoneType errors
are properly handled at all levels of the application.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestNextTaskNoneTypeIntegration:
    """Integration tests for NoneType error fix in manage_task next action"""

    def create_mock_task_entity(
        self,
        task_id: str = "task-123",
        title: str = "Test Task",
        status: str = "todo",
        priority: str = "medium",
        assignees=None,
        labels=None
    ):
        """Create a mock task entity with proper value objects"""
        task = MagicMock(spec=Task)
        task.id = TaskId(task_id)
        task.title = title
        task.description = "Test description"
        task.status = TaskStatus.from_string(status)
        task.priority = Priority.from_string(priority)
        task.assignees = assignees  # Can be None
        task.labels = labels  # Can be None
        task.dependencies = []
        task.subtasks = []
        task.context_id = f"context-{task_id}"
        
        # Mock the to_dict method
        task.to_dict = MagicMock(return_value={
            "id": task_id,
            "title": title,
            "description": "Test description",
            "status": status,
            "priority": priority,
            "assignees": assignees,
            "labels": labels,
            "dependencies": [],
            "subtasks": []
        })
        
        task.get_subtask_progress = MagicMock(return_value={
            "completed": 0,
            "total": 0,
            "percentage": 0
        })
        
        return task

    @pytest.mark.asyncio
    async def test_manage_task_next_with_none_attributes_through_controller(self):
        """Test the full MCP flow with tasks having None attributes"""
        # Create controller with factory
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Mock the facade and repository
        with patch.object(controller, '_facade') as mock_facade:
            # Setup facade response
            mock_facade.get_next_task = AsyncMock(return_value={
                "success": True,
                "action": "next",
                "task": {
                    "id": "task-123",
                    "title": "Task with None attributes",
                    "status": "todo",
                    "assignees": None,  # This is the key - None value
                    "labels": None,     # This too
                    "priority": "high"
                },
                "message": "Next action: Work on task 'Task with None attributes'"
            })
            
            # Execute manage_task with next action
            result = await controller.manage_task(
                action="next",
                git_branch_id="test-branch"
            )
            
            # Assert no error occurred
            assert result["success"] is True
            assert result["action"] == "next"
            assert "task" in result

    @pytest.mark.asyncio
    async def test_manage_task_next_filters_with_none_values(self):
        """Test filtering functionality when tasks have None assignees/labels"""
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Create mock tasks with various None configurations
        tasks = [
            self.create_mock_task_entity("task-1", "Task 1", assignees=["user1"], labels=["bug"]),
            self.create_mock_task_entity("task-2", "Task 2", assignees=None, labels=["feature"]),
            self.create_mock_task_entity("task-3", "Task 3", assignees=["user2"], labels=None),
            self.create_mock_task_entity("task-4", "Task 4", assignees=None, labels=None),
        ]
        
        # Mock the repository to return our tasks
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = tasks
        mock_repo.git_branch_id = "test-branch"
        mock_repo.user_id = "test-user"
        mock_repo.project_id = "test-project"
        
        # Create a real facade with mocked repository
        with patch('fastmcp.task_management.application.facades.task_application_facade.InMemoryTaskRepository', return_value=mock_repo):
            facade = TaskApplicationFacade()
            controller._facade = facade
            
            # Test 1: Filter by assignee when some tasks have None assignees
            result = await controller.manage_task(
                action="next",
                git_branch_id="test-branch",
                assignees="user1"  # This will be converted to a list internally
            )
            
            # Should not crash and should return appropriate response
            assert "error" not in result or "NoneType" not in result.get("error", "")
            
            # Test 2: Filter by labels when some tasks have None labels  
            result = await controller.manage_task(
                action="next",
                git_branch_id="test-branch",
                labels=["bug"]
            )
            
            # Should not crash
            assert "error" not in result or "NoneType" not in result.get("error", "")

    @pytest.mark.asyncio
    async def test_controller_parameter_validation_for_next_action(self):
        """Test that controller properly validates parameters for next action"""
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Mock facade
        controller._facade = MagicMock()
        controller._facade.get_next_task = AsyncMock(return_value={
            "success": True,
            "action": "next",
            "message": "No tasks found"
        })
        
        # Test various parameter combinations
        test_cases = [
            # Basic next action
            {"action": "next", "git_branch_id": "main"},
            # With assignees filter
            {"action": "next", "git_branch_id": "main", "assignees": "user1"},
            # With labels filter
            {"action": "next", "git_branch_id": "main", "labels": ["bug", "urgent"]},
            # With both filters
            {"action": "next", "git_branch_id": "main", "assignees": ["user1", "user2"], "labels": ["feature"]},
            # With include_context
            {"action": "next", "git_branch_id": "main", "include_context": True}
        ]
        
        for params in test_cases:
            result = await controller.manage_task(**params)
            # Should not have NoneType errors
            if "error" in result:
                assert "NoneType" not in result["error"]

    @pytest.mark.asyncio
    async def test_edge_cases_for_none_handling(self):
        """Test edge cases where None values might cause issues"""
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Create tasks with edge case scenarios
        edge_case_task = self.create_mock_task_entity("edge-1", "Edge Case Task")
        # Simulate completely missing attributes (not just None)
        delattr(edge_case_task, 'assignees')
        delattr(edge_case_task, 'labels')
        
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = [edge_case_task]
        mock_repo.git_branch_id = "test-branch"
        
        with patch('fastmcp.task_management.application.facades.task_application_facade.InMemoryTaskRepository', return_value=mock_repo):
            facade = TaskApplicationFacade()
            controller._facade = facade
            
            # This should not crash even with missing attributes
            result = await controller.manage_task(
                action="next",
                git_branch_id="test-branch",
                assignees="user1"
            )
            
            # Should handle gracefully
            assert "success" in result
            assert "NoneType" not in str(result.get("error", ""))

    @pytest.mark.asyncio
    async def test_real_world_scenario_simulation(self):
        """Simulate a real-world scenario with mixed task states"""
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Create realistic task distribution
        tasks = [
            # Normal tasks
            self.create_mock_task_entity("task-1", "Implement feature", status="in_progress", 
                                       assignees=["dev1", "dev2"], labels=["feature", "frontend"]),
            self.create_mock_task_entity("task-2", "Fix bug", status="todo", priority="urgent",
                                       assignees=["dev1"], labels=["bug", "backend"]),
            # Tasks with None values (common in practice)
            self.create_mock_task_entity("task-3", "Research task", status="todo",
                                       assignees=None, labels=None),  # Unassigned research task
            self.create_mock_task_entity("task-4", "Documentation", status="todo",
                                       assignees=["dev3"], labels=None),  # No labels yet
            # Completed task
            self.create_mock_task_entity("task-5", "Completed feature", status="done",
                                       assignees=["dev1"], labels=["feature"])
        ]
        
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = tasks
        mock_repo.git_branch_id = "main"
        mock_repo.user_id = "current-user"
        mock_repo.project_id = "project-123"
        
        with patch('fastmcp.task_management.application.facades.task_application_facade.InMemoryTaskRepository', return_value=mock_repo):
            facade = TaskApplicationFacade()
            controller._facade = facade
            
            # Scenario 1: Get next task for dev1
            result = await controller.manage_task(
                action="next",
                git_branch_id="main", 
                assignees="dev1"
            )
            assert result["success"] is True
            # Should get task-2 (urgent bug) or task-1 (in progress)
            
            # Scenario 2: Get next bug task
            result = await controller.manage_task(
                action="next",
                git_branch_id="main",
                labels=["bug"]
            )
            assert result["success"] is True
            
            # Scenario 3: Get any unassigned task
            # This specifically tests the None assignees filtering
            unassigned_tasks = [t for t in tasks if t.assignees is None]
            assert len(unassigned_tasks) > 0  # We have unassigned tasks
            
            # This should not crash when checking assignees
            result = await controller.manage_task(
                action="next",
                git_branch_id="main"
            )
            assert "NoneType" not in str(result.get("error", ""))

    @pytest.mark.asyncio
    async def test_error_message_validation(self):
        """Ensure the specific error message is not present after fix"""
        factory = TaskFacadeFactory()
        controller = TaskMCPController(factory)
        
        # Create a task that would previously cause the error
        problematic_task = self.create_mock_task_entity(
            "prob-1", 
            "Problematic Task",
            status="todo",
            assignees=None,  # This would cause "None is not iterable"
            labels=None      # This too
        )
        
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = [problematic_task]
        mock_repo.git_branch_id = "main"
        
        with patch('fastmcp.task_management.application.facades.task_application_facade.InMemoryTaskRepository', return_value=mock_repo):
            facade = TaskApplicationFacade()
            controller._facade = facade
            
            # This exact call would previously fail with "argument of type 'NoneType' is not iterable"
            result = await controller.manage_task(
                action="next",
                git_branch_id="main",
                assignees="any-user",  # Filtering by assignee when task has None assignees
                labels=["any-label"]   # Filtering by label when task has None labels
            )
            
            # Verify the specific error is not present
            if "error" in result:
                assert "argument of type 'NoneType' is not iterable" not in result["error"]
                assert "NoneType" not in result["error"]
            
            # Should get a proper "no matching tasks" response instead
            assert result["success"] is False or (result["success"] is True and not result.get("has_next", True))