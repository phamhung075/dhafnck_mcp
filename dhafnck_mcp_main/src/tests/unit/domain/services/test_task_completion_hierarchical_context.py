"""
Unit tests for task completion service with hierarchical context validation

This test file verifies the migration from basic context to hierarchical context
validation in the task completion service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid

from fastmcp.task_management.domain.services.task_completion_service import TaskCompletionService
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.exceptions.task_exceptions import TaskCompletionError


class TestTaskCompletionHierarchicalContext:
    """Test suite for hierarchical context validation in task completion"""
    
    @pytest.fixture
    def mock_subtask_repository(self):
        """Mock subtask repository"""
        return Mock()
    
    @pytest.fixture
    def mock_hierarchical_context_service(self):
        """Mock hierarchical context service"""
        mock = Mock()
        # Default to returning a valid context
        mock.get_context.return_value = {
            "success": True,
            "context": {
                "level": "task",
                "context_id": "task-123",
                "data": {"status": "in_progress"}
            }
        }
        return mock
    
    @pytest.fixture
    def task_completion_service(self, mock_subtask_repository, mock_hierarchical_context_service):
        """Create task completion service with mocked dependencies"""
        service = TaskCompletionService(mock_subtask_repository, mock_hierarchical_context_service)
        return service
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing"""
        task_id = TaskId(str(uuid.uuid4()))
        task = Task.create(
            id=task_id,
            title="Test Task",
            description="Test task for hierarchical context validation",
            git_branch_id="branch-123"
        )
        # Set status to in_progress
        from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
        task.status = TaskStatus.in_progress()
        return task
    
    def test_task_completion_requires_hierarchical_context(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that task completion checks for hierarchical context instead of basic context"""
        # Setup: Task has no context_id (context not created)
        sample_task._context_id = None
        
        # Mock subtask repository to return empty list
        task_completion_service._subtask_repository.find_by_parent_task_id.return_value = []
        
        # Mock hierarchical context service to return no context
        mock_hierarchical_context_service.get_context.return_value = {
            "success": False,
            "error": "Context not found"
        }
        
        # Act
        can_complete, error_message = task_completion_service.can_complete_task(sample_task)
        
        # Assert
        assert can_complete is False
        assert "hierarchical context" in error_message.lower()
        assert "manage_hierarchical_context" in error_message
        assert "manage_context" not in error_message  # Should not mention old command
        
        # Verify hierarchical context service was called
        mock_hierarchical_context_service.get_context.assert_called_once_with(
            "task", sample_task.id.value
        )
    
    def test_task_completion_with_valid_hierarchical_context(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that task can be completed when hierarchical context exists"""
        # Setup: Task has context_id
        sample_task._context_id = "context-123"
        
        # Mock no subtasks
        task_completion_service._subtask_repository.find_by_parent_task_id.return_value = []
        
        # Act
        can_complete, error_message = task_completion_service.can_complete_task(sample_task)
        
        # Assert
        assert can_complete is True
        assert error_message is None
        
        # Verify hierarchical context was checked
        mock_hierarchical_context_service.get_context.assert_called_once()
    
    def test_error_messages_use_hierarchical_context_commands(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that error messages provide correct hierarchical context commands"""
        # Setup: No context
        sample_task._context_id = None
        mock_hierarchical_context_service.get_context.return_value = {
            "success": False,
            "error": "Context not found"
        }
        
        # Mock subtask repository to return empty list
        task_completion_service._subtask_repository.find_by_parent_task_id.return_value = []
        
        # Act
        can_complete, error_message = task_completion_service.can_complete_task(sample_task)
        
        # Assert error message contains hierarchical context command
        assert "manage_hierarchical_context" in error_message
        assert "action='create'" in error_message or "action=\"create\"" in error_message
        assert "level='task'" in error_message or "level=\"task\"" in error_message
        assert f"context_id='{sample_task.id.value}'" in error_message or f'context_id="{sample_task.id.value}"' in error_message
    
    def test_get_completion_blockers_checks_hierarchical_context(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that get_completion_blockers uses hierarchical context"""
        # Setup: No context
        sample_task._context_id = None
        mock_hierarchical_context_service.get_context.return_value = {
            "success": False,
            "error": "Context not found"
        }
        
        # Act
        blockers = task_completion_service.get_completion_blockers(sample_task)
        
        # Assert
        assert len(blockers) > 0
        blocker_text = blockers[0]
        assert "hierarchical context" in blocker_text.lower()
        assert "manage_hierarchical_context" in blocker_text
    
    def test_context_required_error_uses_hierarchical_commands(self, task_completion_service, sample_task):
        """Test that _create_context_required_error provides hierarchical context commands"""
        # Act
        error_dict = task_completion_service._create_context_required_error(sample_task)
        
        # Assert
        assert "hierarchical context" in error_dict["error"].lower()
        
        # Check step-by-step fix uses hierarchical commands
        steps = error_dict["step_by_step_fix"]
        create_step = next(s for s in steps if s["action"] == "Create context")
        assert "manage_hierarchical_context" in create_step["command"]
        assert "level=" in create_step["command"]
        assert "task" in create_step["command"]
        
        update_step = next(s for s in steps if s["action"] == "Update context status")
        assert "manage_hierarchical_context" in update_step["command"]
        assert "action='update'" in update_step["command"] or 'action="update"' in update_step["command"]
    
    def test_hierarchical_context_validation_with_inheritance(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that hierarchical context validation considers inheritance"""
        # Setup: Task has context with inherited data
        sample_task._context_id = "context-123"
        mock_hierarchical_context_service.get_context.return_value = {
            "success": True,
            "context": {
                "level": "task",
                "context_id": sample_task.id.value,
                "data": {"status": "in_progress"},
                "inherited_data": {
                    "project_settings": {"team": "backend"},
                    "global_settings": {"org": "acme"}
                }
            }
        }
        
        # Mock no subtasks
        task_completion_service._subtask_repository.find_by_parent_task_id.return_value = []
        
        # Act
        can_complete, error_message = task_completion_service.can_complete_task(sample_task)
        
        # Assert
        assert can_complete is True
        assert error_message is None
    
    def test_context_stale_check_uses_hierarchical_context(self, task_completion_service, sample_task, mock_hierarchical_context_service):
        """Test that context staleness check works with hierarchical context"""
        # Setup: Task has context
        sample_task._context_id = "context-123"
        
        # Mock hierarchical context with metadata
        mock_hierarchical_context_service.get_context.return_value = {
            "success": True,
            "context": {
                "level": "task",
                "context_id": sample_task.id.value,
                "data": {"status": "in_progress"},
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }
        
        # Mock no subtasks
        task_completion_service._subtask_repository.find_by_parent_task_id.return_value = []
        
        # Act
        can_complete, error_message = task_completion_service.can_complete_task(sample_task)
        
        # Assert
        assert can_complete is True
        assert error_message is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])