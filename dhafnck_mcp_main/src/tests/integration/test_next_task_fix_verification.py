"""Integration test to verify the next task TypeError fix"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase, NextTaskResponse
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.entities.task import Task

class TestNextTaskFix:
    """Test that the next task operation works without TypeError"""
    
    def test_next_task_with_no_tasks(self):
        """Test next task when there are no tasks"""
        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = []
        
        # Create mock facade factory
        mock_facade_factory = MagicMock()
        
        # Create facade with mock repository
        mock_use_cases = {
            "_do_next_use_case": NextTaskUseCase(task_repository=mock_repo)
        }
        
        # Create facade
        facade = TaskApplicationFacade(
            task_repository=mock_repo,
            project_repository=MagicMock(),
            agent_repository=MagicMock(),
            create_task_use_case=MagicMock(),
            update_task_use_case=MagicMock(),
            complete_task_use_case=MagicMock(),
            do_next_use_case=mock_use_cases["_do_next_use_case"]
        )
        
        # Mock the facade factory to return our facade
        mock_facade_factory.create.return_value = facade
        
        # Create controller
        controller = TaskMCPController(task_facade_factory=mock_facade_factory)
        
        # Execute manage_task with "next" action
        result = controller.manage_task(
            action="next",
            git_branch_id="test-branch-uuid"
        )
        
        # Verify no TypeError and correct response
        assert result["success"] == False  # No tasks found
        assert "error" in result or "message" in result
        assert "TypeError" not in str(result)
    
    def test_next_task_with_available_task(self):
        """Test next task when there is an available task"""
        # Create a mock task
        mock_task = MagicMock(spec=Task)
        mock_task.id = TaskId("test-task-123")
        mock_task.title = "Test Task"
        mock_task.description = "Test Description"
        mock_task.status = TaskStatus.todo()
        mock_task.priority = Priority.high()
        mock_task.assignees = []
        mock_task.labels = []
        mock_task.dependencies = []
        mock_task.subtasks = []
        mock_task.context_id = None
        mock_task.to_dict.return_value = {
            "id": "test-task-123",
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo",
            "priority": "high"
        }
        mock_task.get_subtask_progress.return_value = {"completed": 0, "total": 0, "percentage": 0}
        
        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = [mock_task]
        
        # Create mock facade factory
        mock_facade_factory = MagicMock()
        
        # Create NextTaskUseCase with mock repository
        next_use_case = NextTaskUseCase(task_repository=mock_repo)
        
        # Create facade
        facade = TaskApplicationFacade(
            task_repository=mock_repo,
            project_repository=MagicMock(),
            agent_repository=MagicMock(),
            create_task_use_case=MagicMock(),
            update_task_use_case=MagicMock(),
            complete_task_use_case=MagicMock(),
            do_next_use_case=next_use_case
        )
        
        # Mock the facade factory to return our facade
        mock_facade_factory.create.return_value = facade
        
        # Create controller
        controller = TaskMCPController(task_facade_factory=mock_facade_factory)
        
        # Execute manage_task with "next" action
        result = controller.manage_task(
            action="next",
            git_branch_id="test-branch-uuid",
            include_context=True
        )
        
        # Verify no TypeError and correct response
        assert "TypeError" not in str(result)
        assert "error" not in result or "TypeError" not in result["error"]
        
        # The response structure should be valid
        assert "success" in result
        if result["success"]:
            assert "task" in result
        
    @pytest.mark.asyncio
    async def test_async_execution_no_type_error(self):
        """Test that async execution doesn't cause TypeError"""
        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = []
        
        # Create NextTaskUseCase
        next_use_case = NextTaskUseCase(task_repository=mock_repo)
        
        # Execute with correct parameter name
        response = await next_use_case.execute(
            git_branch_id="test-branch-uuid",  # Correct parameter name
            include_context=True
        )
        
        # Verify response is valid
        assert response is not None
        assert hasattr(response, 'has_next')
        assert response.has_next == False  # No tasks
        assert response.message == "No tasks found. Create a task to get started!"

if __name__ == "__main__":
    # Run the tests
    test = TestNextTaskFix()
    
    print("Testing next task with no tasks...")
    test.test_next_task_with_no_tasks()
    print("✓ Passed: No TypeError with empty task list")
    
    print("\nTesting next task with available task...")
    test.test_next_task_with_available_task()
    print("✓ Passed: No TypeError with available task")
    
    print("\nTesting async execution...")
    asyncio.run(test.test_async_execution_no_type_error())
    print("✓ Passed: Async execution works correctly")
    
    print("\n✅ All tests passed! The TypeError issue is fixed.")