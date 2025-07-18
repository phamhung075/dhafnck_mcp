"""TDD Tests for Task Status Update Error Fix

This test file demonstrates the issue where updating a task status to 'in_progress'
incorrectly triggers task completion validation errors.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from fastmcp.task_management.interface.utils.error_handler import UserFriendlyErrorHandler
from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.use_cases.update_task import UpdateTaskUseCase
from fastmcp.task_management.application.dtos.task import UpdateTaskRequest
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskStatusUpdateErrorFix:
    """Test cases to ensure task status updates work correctly without triggering completion validation."""
    
    def test_error_handler_should_not_treat_update_errors_as_completion_errors(self):
        """Test that the error handler doesn't misinterpret update errors as completion errors."""
        # Arrange
        # This error might come from task entity validation during update
        update_error = ValueError("Context must be updated for some reason")
        context = {"action": "update", "task_id": "test-task-123"}
        
        # Act
        result = UserFriendlyErrorHandler.handle_error(
            update_error, 
            "task update operation",
            context
        )
        
        # Assert
        # The error should NOT be treated as a task completion error
        assert "Task completion requires" not in result.get("error", "")
        assert result.get("error_code") != "CONTEXT_REQUIRED"
        # It should be treated as a validation error instead
        assert result.get("error_code") == "VALIDATION_ERROR"
        assert "Invalid parameter format" in result.get("error", "")
    
    def test_task_update_to_in_progress_should_not_trigger_completion_validation(self):
        """Test that updating task status to 'in_progress' doesn't trigger completion validation."""
        # Arrange
        task_id = "f3b9c852-4eb8-4e71-a0ed-f0d3e8c143eb"
        mock_repository = Mock()
        
        # Create a task that exists
        existing_task = Task(
            id=TaskId(task_id),
            git_branch_id="branch-123",
            title="Test Task",
            description="Test task description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.find_by_id.return_value = existing_task
        mock_repository.save.return_value = None
        
        # Create update use case
        update_use_case = UpdateTaskUseCase(task_repository=mock_repository)
        
        # Create update request
        request = UpdateTaskRequest(
            task_id=task_id,
            status="in_progress"  # This should NOT trigger completion validation
        )
        
        # Act
        response = update_use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.task.status == "in_progress"
        # Verify the task was saved with the new status
        mock_repository.save.assert_called_once()
        saved_task = mock_repository.save.call_args[0][0]
        assert saved_task.status.value == "in_progress"
    
    
    
    def test_error_handler_context_aware_routing(self):
        """Test that error handler considers the action context when routing errors."""
        # Arrange
        error_message = "Context must be updated before proceeding"
        
        # Test case 1: Update action context
        update_context = {"action": "update", "task_id": "123"}
        update_result = UserFriendlyErrorHandler.handle_error(
            ValueError(error_message),
            "task update operation", 
            update_context
        )
        
        # Test case 2: Complete action context  
        complete_context = {"action": "complete", "task_id": "123"}
        complete_result = UserFriendlyErrorHandler.handle_error(
            ValueError(error_message),
            "task complete operation",
            complete_context
        )
        
        # Assert - different handling based on context
        # Update context should NOT get completion-specific error handling
        assert "Task completion requires" not in update_result.get("error", "")
        assert update_result.get("error_code") != "CONTEXT_REQUIRED"
        
        # Complete context SHOULD get completion-specific error handling
        assert "Task completion requires hierarchical context" in complete_result.get("error", "")
        assert complete_result.get("error_code") == "CONTEXT_REQUIRED"