"""Unit tests for Vision System context enforcement."""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.context import TaskContext, ContextMetadata, ContextObjective
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.exceptions.vision_exceptions import (
    MissingCompletionSummaryError,
    InvalidContextUpdateError
)
from fastmcp.task_management.application.services.context_validation_service import ContextValidationService
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase



pytestmark = pytest.mark.unit  # Mark all tests in this file as unit tests

class TestTaskCompletionWithContext:
    """Test task completion with mandatory context updates."""
    
    def test_task_completion_requires_completion_summary(self):
        """Test that task completion fails without completion_summary."""
        # Create a task with valid UUID
        task_id = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_id),
            title="Test Task",
            description="Test task for context enforcement",
            git_branch_id="branch-123"
        )
        
        # Try to complete without completion_summary
        with pytest.raises(MissingCompletionSummaryError) as exc_info:
            task.complete_task(completion_summary=None)
        
        assert task.id.value in str(exc_info.value)
        assert "completion_summary" in str(exc_info.value)
    
    def test_task_completion_with_empty_summary_fails(self):
        """Test that empty completion_summary is rejected."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="Test task for context enforcement",
            git_branch_id="branch-123"
        )
        
        # Try with empty string
        with pytest.raises(MissingCompletionSummaryError):
            task.complete_task(completion_summary="")
        
        # Try with whitespace only
        with pytest.raises(MissingCompletionSummaryError):
            task.complete_task(completion_summary="   ")
    
    def test_task_completion_with_valid_summary_succeeds(self):
        """Test successful task completion with completion_summary."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="Test task for context enforcement",
            git_branch_id="branch-123"
        )
        
        # Set context_id to simulate context update
        task.set_context_id("context-123")
        
        # Complete with valid summary
        completion_summary = "Implemented user authentication with JWT tokens"
        task.complete_task(completion_summary=completion_summary)
        
        # Verify task is completed
        assert task.is_completed
        assert task.status.is_done()
        
        # Verify completion summary is stored
        assert task.get_completion_summary() == completion_summary
    
    def test_task_completion_stores_summary_in_event(self):
        """Test that completion_summary is included in domain event."""
        task = Task.create(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="Test task for context enforcement",
            git_branch_id="branch-123"
        )
        
        task.set_context_id("context-123")
        completion_summary = "Completed database migration"
        
        task.complete_task(completion_summary=completion_summary)
        
        # Check domain events
        events = task.get_events()
        completion_event = None
        
        for event in events:
            if hasattr(event, 'field_name') and event.field_name == 'status':
                completion_event = event
                break
        
        assert completion_event is not None
        assert hasattr(completion_event, 'metadata')
        assert completion_event.metadata.get('completion_summary') == completion_summary


class TestContextValidationService:
    """Test the context validation service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validation_service = ContextValidationService()
        self.task_id = str(uuid.uuid4())
        self.task = Task.create(
            id=TaskId(self.task_id),
            title="Test Task",
            description="Test description",
            git_branch_id="branch-123"
        )
        self.context = self._create_test_context(self.task.id.value)
    
    def _create_test_context(self, task_id: str) -> TaskContext:
        """Create a test context."""
        metadata = ContextMetadata(task_id=task_id)
        objective = ContextObjective(title="Test objective")
        return TaskContext(metadata=metadata, objective=objective)
    
    def test_validate_completion_context_success(self):
        """Test successful validation of completion context."""
        self.task.set_context_id("context-123")
        
        is_valid, errors = self.validation_service.validate_completion_context(
            task=self.task,
            context=self.context,
            completion_summary="Task completed successfully"
        )
        
        # Debug output
        if not is_valid:
            print(f"Validation errors: {errors}")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_completion_context_no_summary(self):
        """Test validation fails without completion_summary."""
        self.task.set_context_id("context-123")
        
        is_valid, errors = self.validation_service.validate_completion_context(
            task=self.task,
            context=self.context,
            completion_summary=""
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("completion_summary" in error for error in errors)
    
    def test_validate_completion_context_wrong_task(self):
        """Test validation fails when context doesn't match task."""
        self.task.set_context_id("context-123")
        wrong_context = self._create_test_context("WRONG-TASK")
        
        is_valid, errors = self.validation_service.validate_completion_context(
            task=self.task,
            context=wrong_context,
            completion_summary="Completed"
        )
        
        assert is_valid is False
        assert any("does not match task" in error for error in errors)
    
    def test_validate_progress_update_valid_types(self):
        """Test validation of progress updates with valid types."""
        valid_types = ['analysis', 'design', 'implementation', 'testing', 
                      'documentation', 'review', 'deployment', 'general']
        
        for progress_type in valid_types:
            is_valid, errors = self.validation_service.validate_progress_update(
                progress_type=progress_type,
                details="Making progress",
                percentage=50
            )
            assert is_valid is True
            assert len(errors) == 0
    
    def test_validate_progress_update_invalid_type(self):
        """Test validation fails with invalid progress type."""
        is_valid, errors = self.validation_service.validate_progress_update(
            progress_type="invalid_type",
            details="Making progress",
            percentage=50
        )
        
        assert is_valid is False
        assert any("Invalid progress_type" in error for error in errors)
    
    def test_validate_progress_update_empty_details(self):
        """Test validation fails with empty details."""
        is_valid, errors = self.validation_service.validate_progress_update(
            progress_type="implementation",
            details="",
            percentage=50
        )
        
        assert is_valid is False
        assert any("details cannot be empty" in error for error in errors)
    
    def test_validate_progress_percentage_bounds(self):
        """Test validation of progress percentage bounds."""
        # Valid percentages
        for percentage in [0, 50, 100]:
            is_valid, _ = self.validation_service.validate_progress_update(
                progress_type="implementation",
                details="Progress",
                percentage=percentage
            )
            assert is_valid is True
        
        # Invalid percentages
        for percentage in [-1, 101, 200]:
            is_valid, errors = self.validation_service.validate_progress_update(
                progress_type="implementation",
                details="Progress",
                percentage=percentage
            )
            assert is_valid is False
            assert any("between 0 and 100" in error for error in errors)


class TestContextEntityEnhancements:
    """Test enhanced context entity with Vision System fields."""
    
    def test_context_update_completion_summary(self):
        """Test updating context with completion summary."""
        metadata = ContextMetadata(task_id=str(uuid.uuid4()))
        objective = ContextObjective(title="Test task")
        context = TaskContext(metadata=metadata, objective=objective)
        
        # Update with completion summary
        completion_summary = "Successfully implemented feature X"
        testing_notes = "All unit tests passing"
        next_recommendations = "Add integration tests"
        
        context.update_completion_summary(
            completion_summary=completion_summary,
            testing_notes=testing_notes,
            next_recommendations=next_recommendations
        )
        
        # Verify updates
        assert context.progress.completion_summary == completion_summary
        assert context.progress.testing_notes == testing_notes
        assert context.progress.next_recommendations == next_recommendations
        assert context.has_completion_summary() is True
    
    def test_context_update_empty_summary_fails(self):
        """Test that empty completion summary is rejected."""
        metadata = ContextMetadata(task_id=str(uuid.uuid4()))
        objective = ContextObjective(title="Test task")
        context = TaskContext(metadata=metadata, objective=objective)
        
        with pytest.raises(ValueError) as exc_info:
            context.update_completion_summary("")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_context_validate_for_completion(self):
        """Test context validation for task completion."""
        metadata = ContextMetadata(task_id=str(uuid.uuid4()))
        objective = ContextObjective(title="Test task")
        context = TaskContext(metadata=metadata, objective=objective)
        
        # Should fail without completion_summary
        is_valid, errors = context.validate_for_task_completion()
        assert is_valid is False
        assert any("completion_summary" in error for error in errors)
        
        # Add completion_summary
        context.update_completion_summary("Task completed")
        
        # Should pass with completion_summary
        is_valid, errors = context.validate_for_task_completion()
        assert is_valid is True
        assert len(errors) == 0
    
    def test_context_serialization_with_vision_fields(self):
        """Test that Vision System fields are properly serialized."""
        metadata = ContextMetadata(task_id=str(uuid.uuid4()))
        objective = ContextObjective(title="Test task")
        context = TaskContext(metadata=metadata, objective=objective)
        
        # Add Vision System data
        context.update_completion_summary(
            completion_summary="Completed successfully",
            testing_notes="Tests passed",
            next_recommendations="Deploy to staging"
        )
        context.progress.vision_alignment_score = 0.85
        
        # Serialize to dict
        context_dict = context.to_dict()
        
        # Verify Vision fields are present
        assert "progress" in context_dict
        progress = context_dict["progress"]
        assert progress["completion_summary"] == "Completed successfully"
        assert progress["testing_notes"] == "Tests passed"
        assert progress["next_recommendations"] == "Deploy to staging"
        assert progress["vision_alignment_score"] == 0.85
    
    def test_context_deserialization_with_vision_fields(self):
        """Test that Vision System fields are properly deserialized."""
        context_data = {
            "metadata": {
                "task_id": str(uuid.uuid4()),
                "status": "in_progress",
                "priority": "high"
            },
            "objective": {
                "title": "Test task"
            },
            "progress": {
                "completion_summary": "Task completed",
                "testing_notes": "All tests green",
                "next_recommendations": "Monitor performance",
                "vision_alignment_score": 0.92,
                "completion_percentage": 100.0
            }
        }
        
        # Deserialize from dict
        context = TaskContext.from_dict(context_data)
        
        # Verify Vision fields
        assert context.progress.completion_summary == "Task completed"
        assert context.progress.testing_notes == "All tests green"
        assert context.progress.next_recommendations == "Monitor performance"
        assert context.progress.vision_alignment_score == 0.92
        assert context.has_completion_summary() is True


class TestCompleteTaskUseCase:
    """Test the enhanced CompleteTaskUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.task_repo_mock = Mock()
        self.subtask_repo_mock = Mock()
        self.hierarchical_context_service_mock = Mock()
        
        # Configure subtask repository mock to return empty list
        self.subtask_repo_mock.find_by_parent_task_id.return_value = []
        
        self.use_case = CompleteTaskUseCase(
            task_repository=self.task_repo_mock,
            subtask_repository=self.subtask_repo_mock
        )
    
    def test_execute_without_completion_summary_fails(self):
        """Test that execute fails without completion_summary."""
        task_id = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_id),
            title="Test Task",
            description="Test description"
        )
        task.set_context_id("context-300")
        
        self.task_repo_mock.find_by_id.return_value = task
        
        # Execute without completion_summary
        result = self.use_case.execute(task_id=task_id)
        
        assert result["success"] is False
        assert "completion_summary" in result["message"]
        assert "hint" in result
    
    def test_execute_with_completion_summary_succeeds(self):
        """Test successful execution with completion_summary."""
        task_id = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_id),
            title="Test Task",
            description="Test description"
        )
        task.set_context_id("context-301")
        
        self.task_repo_mock.find_by_id.return_value = task
        self.task_repo_mock.save.return_value = None
        
        # Mock hierarchical context service with async methods
        self.hierarchical_context_service_mock.get_context = AsyncMock(return_value={
            "success": True,
            "task_context": {"metadata": {"task_id": task_id}}
        })
        self.hierarchical_context_service_mock.update_context = AsyncMock(return_value={
            "success": True
        })
        
        # Execute with completion_summary
        result = self.use_case.execute(
            task_id=task_id,
            completion_summary="Implemented feature successfully",
            testing_notes="All tests passing",
            next_recommendations="Deploy to production"
        )
        
        assert result["success"] is True
        assert result["task_id"] == task_id
        assert "done" in result["message"]
        
        # Verify task was saved
        self.task_repo_mock.save.assert_called_once()
    
    def test_execute_updates_context_with_completion_data(self):
        """Test that context is updated with completion data."""
        task_id = str(uuid.uuid4())
        task = Task.create(
            id=TaskId(task_id),
            title="Test Task",
            description="Test description"
        )
        task.set_context_id("context-302")
        
        self.task_repo_mock.find_by_id.return_value = task
        self.task_repo_mock.save.return_value = None
        
        # Mock the facade that will be created by the factory
        mock_facade = Mock()
        # Use a future timestamp to ensure context is newer than task
        from datetime import datetime, timezone, timedelta
        future_time = (datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        mock_facade.get_context = Mock(return_value={
            "success": True,
            "context": {"updated_at": future_time}
        })
        mock_facade.update_context = Mock(return_value={
            "success": True
        })
        mock_facade.merge_context = Mock(return_value={
            "success": True
        })
        
        # Create a mock factory class and instance
        mock_factory_class = Mock()
        mock_factory_instance = Mock()
        mock_factory_instance.create_facade = Mock(return_value=mock_facade)
        mock_factory_class.return_value = mock_factory_instance
        
        # Mock the factory module import
        with patch.dict('sys.modules', {'fastmcp.task_management.application.factories.hierarchical_context_facade_factory': Mock(HierarchicalContextFacadeFactory=mock_factory_class)}):
            
            completion_summary = "Feature completed"
            testing_notes = "Tests passed"
            
            # Execute
            result = self.use_case.execute(
                task_id=task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            # Verify the result first
            assert result["success"] is True
            
            # Verify context merge was called
            mock_facade.merge_context.assert_called()
            
            # Check the merge data
            merge_call_args = mock_facade.merge_context.call_args[0]
            assert merge_call_args[0] == "task"  # level
            assert merge_call_args[1] == task_id  # task_id
            
            merge_data = merge_call_args[2]
            assert "progress" in merge_data
            assert merge_data["progress"]["completion_summary"] == completion_summary
            assert merge_data["progress"]["testing_notes"] == testing_notes
            assert merge_data["progress"]["completion_percentage"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])