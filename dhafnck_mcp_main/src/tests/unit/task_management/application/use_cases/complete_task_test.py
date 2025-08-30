"""
Comprehensive test suite for CompleteTaskUseCase.

Tests the complete task use case including:
- Successful task completion
- Subtask completion validation
- Context creation and validation
- Vision system integration (completion summary requirement)
- Error handling and edge cases
- Repository interaction
- Business rule enforcement
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository
from fastmcp.task_management.domain.repositories.subtask_repository import SubtaskRepository
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.exceptions.task_exceptions import (
    TaskNotFoundError, 
    TaskCompletionError
)
from fastmcp.task_management.domain.exceptions.vision_exceptions import MissingCompletionSummaryError
from fastmcp.task_management.domain.services.task_completion_service import TaskCompletionService
from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository


class TestCompleteTaskUseCaseInitialization:
    """Test cases for CompleteTaskUseCase initialization."""
    
    def test_init_with_task_repository_only(self):
        """Test use case initialization with only task repository."""
        mock_task_repo = Mock(spec=TaskRepository)
        
        use_case = CompleteTaskUseCase(mock_task_repo)
        
        assert use_case._task_repository == mock_task_repo
        assert use_case._subtask_repository is None
        assert use_case._task_context_repository is None
        assert use_case._completion_service is None
    
    def test_init_with_all_repositories(self):
        """Test use case initialization with all repositories."""
        mock_task_repo = Mock(spec=TaskRepository)
        mock_subtask_repo = Mock(spec=SubtaskRepository)
        mock_context_repo = Mock(spec=TaskContextRepository)
        
        with patch('fastmcp.task_management.domain.services.task_completion_service.TaskCompletionService') as mock_service:
            mock_completion_service = Mock()
            mock_service.return_value = mock_completion_service
            
            use_case = CompleteTaskUseCase(mock_task_repo, mock_subtask_repo, mock_context_repo)
            
            assert use_case._task_repository == mock_task_repo
            assert use_case._subtask_repository == mock_subtask_repo
            assert use_case._task_context_repository == mock_context_repo
            assert use_case._completion_service == mock_completion_service
            
            # Verify completion service was created correctly
            mock_service.assert_called_once_with(mock_subtask_repo, mock_context_repo)
    
    def test_init_without_repositories_fails(self):
        """Test initialization without task repository fails."""
        with pytest.raises(TypeError):
            CompleteTaskUseCase()


class TestCompleteTaskUseCaseBasicExecution:
    """Test cases for basic task completion execution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_repo = Mock(spec=TaskRepository)
        self.mock_subtask_repo = Mock(spec=SubtaskRepository)
        self.mock_context_repo = Mock(spec=TaskContextRepository)
        self.use_case = CompleteTaskUseCase(
            self.mock_task_repo, 
            self.mock_subtask_repo, 
            self.mock_context_repo
        )
    
    def test_execute_successful_completion(self):
        """Test successful task completion with all requirements met."""
        # Setup task
        task_id = TaskId("task-123")
        mock_task = Mock(spec=Task)
        mock_task.id = task_id
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        # Setup repository
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        # Setup context repository
        self.mock_context_repo.get.return_value = {"context": "exists"}
        
        # Setup completion service
        self.use_case._completion_service = Mock()
        self.use_case._completion_service.can_complete_task.return_value = True
        self.use_case._completion_service.complete_all_subtasks.return_value = True
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Task completed successfully",
            testing_notes="All tests passed"
        )
        
        # Verify task was found
        self.mock_task_repo.find_by_id.assert_called_once()
        
        # Verify completion validation
        self.use_case._completion_service.can_complete_task.assert_called_once_with(mock_task)
        
        # Verify subtasks were completed
        self.use_case._completion_service.complete_all_subtasks.assert_called_once_with(mock_task)
        
        # Verify task completion was called
        mock_task.complete_task.assert_called_once()
        
        # Verify task was saved
        self.mock_task_repo.save.assert_called_once_with(mock_task)
        
        # Verify success response
        assert result["success"] is True
        assert result["task_id"] == "task-123"
        assert "completed successfully" in result["message"]
    
    def test_execute_task_not_found(self):
        """Test completion fails when task doesn't exist."""
        self.mock_task_repo.find_by_id.return_value = None
        
        with pytest.raises(TaskNotFoundError, match="Task task-nonexistent not found"):
            self.use_case.execute(
                task_id="task-nonexistent",
                completion_summary="Trying to complete non-existent task"
            )
        
        # Verify task lookup was attempted
        self.mock_task_repo.find_by_id.assert_called_once()
    
    def test_execute_task_already_completed(self):
        """Test completion of already completed task."""
        # Setup already completed task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.done()
        mock_task.status.is_done.return_value = True
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Trying to complete already done task"
        )
        
        # Verify failure response
        assert result["success"] is False
        assert result["task_id"] == "task-123"
        assert "already completed" in result["message"]
        
        # Verify no save operation was attempted
        self.mock_task_repo.save.assert_not_called()


class TestCompleteTaskUseCaseVisionSystemIntegration:
    """Test cases for Vision System integration (completion summary requirement)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_repo = Mock(spec=TaskRepository)
        self.use_case = CompleteTaskUseCase(self.mock_task_repo)
    
    def test_execute_missing_completion_summary_raises_error(self):
        """Test that missing completion summary raises Vision System error."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task.side_effect = MissingCompletionSummaryError(task_id="task-123")
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        with pytest.raises(MissingCompletionSummaryError):
            self.use_case.execute(task_id="task-123")  # No completion summary
    
    def test_execute_empty_completion_summary_raises_error(self):
        """Test that empty completion summary raises Vision System error."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task.side_effect = MissingCompletionSummaryError(task_id="task-123")
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        with pytest.raises(MissingCompletionSummaryError):
            self.use_case.execute(
                task_id="task-123",
                completion_summary=""  # Empty summary
            )
    
    def test_execute_whitespace_completion_summary_raises_error(self):
        """Test that whitespace-only completion summary raises Vision System error."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task.side_effect = MissingCompletionSummaryError(task_id="task-123")
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        with pytest.raises(MissingCompletionSummaryError):
            self.use_case.execute(
                task_id="task-123",
                completion_summary="   \t  "  # Whitespace only
            )
    
    def test_execute_valid_completion_summary_passes(self):
        """Test that valid completion summary allows completion."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()  # No exception
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Implemented user authentication with JWT tokens"
        )
        
        # Verify completion was called with summary
        mock_task.complete_task.assert_called_once()
        call_args = mock_task.complete_task.call_args[1]
        assert "completion_summary" in call_args
        assert call_args["completion_summary"] == "Implemented user authentication with JWT tokens"
        
        assert result["success"] is True


class TestCompleteTaskUseCaseSubtaskValidation:
    """Test cases for subtask completion validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_repo = Mock(spec=TaskRepository)
        self.mock_subtask_repo = Mock(spec=SubtaskRepository)
        self.mock_context_repo = Mock(spec=TaskContextRepository)
        self.use_case = CompleteTaskUseCase(
            self.mock_task_repo,
            self.mock_subtask_repo,
            self.mock_context_repo
        )
    
    def test_execute_cannot_complete_with_pending_subtasks(self):
        """Test completion fails when subtasks are not complete."""
        # Setup task with subtasks
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        # Setup completion service to indicate subtasks not complete
        self.use_case._completion_service = Mock()
        self.use_case._completion_service.can_complete_task.return_value = False
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Trying to complete with pending subtasks"
        )
        
        # Verify validation was called
        self.use_case._completion_service.can_complete_task.assert_called_once_with(mock_task)
        
        # Verify failure response
        assert result["success"] is False
        assert "cannot be completed" in result["message"].lower()
        
        # Verify task was not saved
        self.mock_task_repo.save.assert_not_called()
    
    def test_execute_successful_with_all_subtasks_complete(self):
        """Test successful completion when all subtasks are complete."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        # Setup context
        self.mock_context_repo.get.return_value = {"context": "exists"}
        
        # Setup completion service to indicate all requirements met
        self.use_case._completion_service = Mock()
        self.use_case._completion_service.can_complete_task.return_value = True
        self.use_case._completion_service.complete_all_subtasks.return_value = True
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="All subtasks completed successfully"
        )
        
        # Verify subtask completion
        self.use_case._completion_service.complete_all_subtasks.assert_called_once_with(mock_task)
        
        # Verify success
        assert result["success"] is True
    
    def test_execute_subtask_completion_failure(self):
        """Test handling of subtask completion failure."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        # Setup completion service
        self.use_case._completion_service = Mock()
        self.use_case._completion_service.can_complete_task.return_value = True
        self.use_case._completion_service.complete_all_subtasks.return_value = False  # Failure
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Attempting completion with subtask failures"
        )
        
        # Verify failure response
        assert result["success"] is False
        assert "failed to complete subtasks" in result["message"].lower()


class TestCompleteTaskUseCaseContextManagement:
    """Test cases for context creation and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_repo = Mock(spec=TaskRepository)
        self.mock_context_repo = Mock(spec=TaskContextRepository)
        self.use_case = CompleteTaskUseCase(self.mock_task_repo, task_context_repository=self.mock_context_repo)
    
    def test_execute_auto_creates_context_when_missing(self):
        """Test auto-creation of context when it doesn't exist."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.id = TaskId("task-123")
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        # Setup context repository - no existing context
        self.mock_context_repo.get.return_value = None
        self.mock_context_repo.create.return_value = {"context": "created"}
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Creating context automatically"
        )
        
        # Verify context creation was attempted
        self.mock_context_repo.get.assert_called_once_with("task-123")
        self.mock_context_repo.create.assert_called_once()
        
        # Verify success
        assert result["success"] is True
    
    def test_execute_uses_existing_context(self):
        """Test completion with existing context."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        # Setup existing context
        existing_context = {
            "context": "existing",
            "progress": "in_progress",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.mock_context_repo.get.return_value = existing_context
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Using existing context"
        )
        
        # Verify existing context was used (no create call)
        self.mock_context_repo.get.assert_called_once_with("task-123")
        self.mock_context_repo.create.assert_not_called()
        
        # Verify success
        assert result["success"] is True


class TestCompleteTaskUseCaseErrorHandling:
    """Test cases for error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_repo = Mock(spec=TaskRepository)
        self.use_case = CompleteTaskUseCase(self.mock_task_repo)
    
    def test_execute_with_string_task_id(self):
        """Test execution with string task ID."""
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        with patch('fastmcp.task_management.domain.value_objects.task_id.TaskId.from_string') as mock_from_string:
            mock_task_id = Mock()
            mock_from_string.return_value = mock_task_id
            
            result = self.use_case.execute(
                task_id="task-123",  # String ID
                completion_summary="Testing string ID conversion"
            )
            
            # Verify ID conversion
            mock_from_string.assert_called_once_with("task-123")
            self.mock_task_repo.find_by_id.assert_called_once_with(mock_task_id)
            
            assert result["success"] is True
    
    def test_execute_with_integer_task_id(self):
        """Test execution with integer task ID."""
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = True
        
        with patch('fastmcp.task_management.domain.value_objects.task_id.TaskId.from_string') as mock_from_string:
            mock_task_id = Mock()
            mock_from_string.return_value = mock_task_id
            
            result = self.use_case.execute(
                task_id=123,  # Integer ID
                completion_summary="Testing integer ID conversion"
            )
            
            # Verify ID conversion (integer converted to string first)
            mock_from_string.assert_called_once_with("123")
            
            assert result["success"] is True
    
    def test_execute_repository_save_failure(self):
        """Test handling of repository save failure."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task = Mock()
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        self.mock_task_repo.save.return_value = False  # Save fails
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Testing save failure"
        )
        
        # Verify task completion was attempted
        mock_task.complete_task.assert_called_once()
        
        # Verify save failure handling
        assert result["success"] is False
        assert "failed to save" in result["message"].lower()
    
    def test_execute_with_exception_during_completion(self):
        """Test handling of exceptions during task completion."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task.side_effect = Exception("Unexpected error during completion")
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Testing exception handling"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result["message"].lower()
    
    def test_execute_with_completion_error(self):
        """Test handling of TaskCompletionError."""
        # Setup task
        mock_task = Mock(spec=Task)
        mock_task.status = TaskStatus.in_progress()
        mock_task.status.is_done.return_value = False
        mock_task.complete_task.side_effect = TaskCompletionError("Business rule violation")
        
        self.mock_task_repo.find_by_id.return_value = mock_task
        
        result = self.use_case.execute(
            task_id="task-123",
            completion_summary="Testing completion error"
        )
        
        # Verify specific error handling
        assert result["success"] is False
        assert "business rule violation" in result["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__])