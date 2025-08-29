"""Test for Complete Task Use Case"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch, AsyncMock, call
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.task_priority import TaskPriority
from fastmcp.task_management.domain.exceptions import TaskNotFoundError
from fastmcp.task_management.domain.exceptions.task_exceptions import TaskCompletionError
from fastmcp.task_management.domain.exceptions.vision_exceptions import MissingCompletionSummaryError
from fastmcp.task_management.domain.events import TaskUpdated


class TestCompleteTaskUseCase:
    """Test suite for CompleteTaskUseCase"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        return Mock()
    
    @pytest.fixture
    def mock_subtask_repository(self):
        """Create a mock subtask repository"""
        return Mock()
    
    @pytest.fixture
    def mock_task_context_repository(self):
        """Create a mock task context repository"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_task_repository, mock_subtask_repository, mock_task_context_repository):
        """Create a complete task use case instance"""
        return CompleteTaskUseCase(
            mock_task_repository,
            mock_subtask_repository,
            mock_task_context_repository
        )
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task"""
        task = Mock(spec=Task)
        task.id = TaskId.from_string("123")
        task.title = "Test Task"
        task.description = "Test Description"
        task.status = TaskStatus.in_progress()
        task.priority = TaskPriority.medium()
        task.assignees = []
        task.labels = []
        task.estimated_effort = None
        task.due_date = None
        task.updated_at = datetime.now(timezone.utc)
        task.git_branch_id = "branch-123"
        task.project_id = None
        task.context_id = None
        task.dependencies = []
        
        # Mock methods
        task.complete_task = Mock()
        task.get_subtask_progress = Mock(return_value={
            "total": 0,
            "completed": 0,
            "percentage": 100
        })
        task.get_events = Mock(return_value=[])
        task.get_dependency_ids = Mock(return_value=[])
        
        return task
    
    @pytest.fixture
    def sample_subtask(self):
        """Create a sample subtask"""
        subtask = Mock(spec=Subtask)
        subtask.id = "subtask-1"
        subtask.title = "Test Subtask"
        subtask.is_completed = False
        return subtask
    
    def test_init(self, mock_task_repository, mock_subtask_repository, mock_task_context_repository):
        """Test use case initialization"""
        use_case = CompleteTaskUseCase(
            mock_task_repository,
            mock_subtask_repository,
            mock_task_context_repository
        )
        assert use_case._task_repository == mock_task_repository
        assert use_case._subtask_repository == mock_subtask_repository
        assert use_case._task_context_repository == mock_task_context_repository
        assert hasattr(use_case, '_completion_service')
        assert hasattr(use_case, '_validation_service')
    
    def test_init_without_subtask_repository(self, mock_task_repository):
        """Test use case initialization without subtask repository"""
        use_case = CompleteTaskUseCase(mock_task_repository)
        assert use_case._subtask_repository is None
        assert use_case._completion_service is None
    
    def test_execute_task_not_found(self, use_case, mock_task_repository):
        """Test execute when task is not found"""
        task_id = "missing-task"
        mock_task_repository.find_by_id.return_value = None
        
        with pytest.raises(TaskNotFoundError) as exc_info:
            use_case.execute(task_id)
        
        assert f"Task {task_id} not found" in str(exc_info.value)
    
    def test_execute_task_already_completed(self, use_case, mock_task_repository, sample_task):
        """Test execute when task is already completed"""
        task_id = "123"
        sample_task.status = TaskStatus.done()
        sample_task.status.is_done = Mock(return_value=True)
        mock_task_repository.find_by_id.return_value = sample_task
        
        result = use_case.execute(task_id)
        
        assert result["success"] is False
        assert result["task_id"] == str(task_id)
        assert "already completed" in result["message"]
        assert result["status"] == str(sample_task.status)
    
    def test_execute_missing_completion_summary(self, use_case, mock_task_repository, sample_task):
        """Test execute with missing completion summary (Vision System requirement)"""
        task_id = "123"
        mock_task_repository.find_by_id.return_value = sample_task
        sample_task.complete_task.side_effect = MissingCompletionSummaryError("Summary required")
        
        result = use_case.execute(task_id)
        
        assert result["success"] is False
        assert result["task_id"] == str(task_id)
        assert "Summary required" in result["message"]
        assert "hint" in result
    
    def test_execute_task_completion_error(self, use_case, mock_task_repository, sample_task):
        """Test execute with task completion error"""
        task_id = "123"
        mock_task_repository.find_by_id.return_value = sample_task
        sample_task.complete_task.side_effect = TaskCompletionError("Cannot complete")
        
        result = use_case.execute(task_id)
        
        assert result["success"] is False
        assert result["task_id"] == str(task_id)
        assert "Cannot complete" in result["message"]
    
    def test_execute_success_with_completion_summary(self, use_case, mock_task_repository, sample_task):
        """Test successful task completion with summary"""
        task_id = "123"
        completion_summary = "Task completed successfully"
        testing_notes = "All tests passed"
        next_recommendations = "Deploy to production"
        
        mock_task_repository.find_by_id.return_value = sample_task
        
        result = use_case.execute(
            task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes,
            next_recommendations=next_recommendations
        )
        
        assert result["success"] is True
        assert result["task_id"] == str(task_id)
        assert result["status"] == str(sample_task.status)
        assert "done, can next_task" in result["message"]
        
        # Verify task was completed with summary
        sample_task.complete_task.assert_called_once()
        call_kwargs = sample_task.complete_task.call_args.kwargs
        assert call_kwargs["completion_summary"] == completion_summary
        
        # Verify task was saved
        mock_task_repository.save.assert_called_once_with(sample_task)
    
    def test_execute_with_subtasks_all_completed(self, use_case, mock_task_repository, 
                                                 mock_subtask_repository, sample_task):
        """Test task completion when all subtasks are completed"""
        task_id = "123"
        
        # Create completed subtasks
        subtasks = [
            Mock(is_completed=True, title="Subtask 1"),
            Mock(is_completed=True, title="Subtask 2")
        ]
        
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_parent_task_id.return_value = subtasks
        
        result = use_case.execute(task_id, completion_summary="All done")
        
        assert result["success"] is True
        assert "subtask_summary" in result
        assert result["subtask_summary"]["total"] == 2
        assert result["subtask_summary"]["completed"] == 2
        assert result["subtask_summary"]["incomplete"] == 0
        assert result["subtask_summary"]["completion_percentage"] == 100
        assert result["subtask_summary"]["can_complete_parent"] is True
    
    def test_execute_with_subtasks_incomplete(self, use_case, mock_task_repository,
                                              mock_subtask_repository, sample_task):
        """Test task completion blocked by incomplete subtasks"""
        task_id = "123"
        
        # Create mix of completed and incomplete subtasks
        subtasks = [
            Mock(is_completed=True, title="Completed 1"),
            Mock(is_completed=False, title="Incomplete 1"),
            Mock(is_completed=False, title="Incomplete 2"),
            Mock(is_completed=True, title="Completed 2"),
            Mock(is_completed=False, title="Incomplete 3")
        ]
        
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_parent_task_id.return_value = subtasks
        
        # Use case without completion service should do fallback validation
        use_case._completion_service = None
        
        result = use_case.execute(task_id, completion_summary="Try to complete")
        
        assert result["success"] is False
        assert "3 of 5 subtasks are incomplete" in result["message"]
        assert "Incomplete 1" in result["message"]
        assert "Incomplete 2" in result["message"]
        assert "and 1 more" in result["message"]
        assert "Complete all subtasks first" in result["message"]
    
    @patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory')
    def test_execute_auto_create_context(self, mock_factory, use_case, mock_task_repository,
                                        mock_task_context_repository, sample_task):
        """Test auto-creation of context during completion"""
        task_id = "123"
        
        # Setup task without context
        sample_task.context_id = None
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_context_repository.get.return_value = None  # No legacy context
        
        # Mock unified context facade
        mock_facade = Mock()
        mock_facade.get_context.return_value = {"success": False}  # No existing context
        mock_facade.create_context.return_value = {"success": True}
        mock_factory.return_value.create_facade.return_value = mock_facade
        
        result = use_case.execute(task_id, completion_summary="Complete with auto-context")
        
        assert result["success"] is True
        
        # Verify context was created
        assert mock_facade.create_context.call_count >= 1  # May create hierarchy
        
        # Verify task context_id was updated
        assert sample_task.context_id == str(task_id)
        assert mock_task_repository.save.call_count >= 2  # Once for context_id, once for completion
    
    @patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory')
    def test_execute_with_existing_legacy_context(self, mock_factory, use_case, mock_task_repository,
                                                 mock_task_context_repository, sample_task):
        """Test completion with existing legacy context"""
        task_id = "123"
        
        # Setup task without context_id
        sample_task.context_id = None
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Mock existing legacy context
        legacy_context = {"id": task_id, "data": "legacy"}
        mock_task_context_repository.get.return_value = legacy_context
        
        result = use_case.execute(task_id, completion_summary="Complete with legacy context")
        
        assert result["success"] is True
        
        # Verify task context_id was updated to link to legacy context
        assert sample_task.context_id == str(task_id)
        assert mock_task_repository.save.call_count >= 2
    
    @patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory')
    def test_execute_with_existing_unified_context(self, mock_factory, use_case, mock_task_repository,
                                                  mock_task_context_repository, sample_task):
        """Test completion with existing unified context"""
        task_id = "123"
        
        # Setup task without context_id
        sample_task.context_id = None
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_context_repository.get.return_value = None  # No legacy context
        
        # Mock existing unified context
        mock_facade = Mock()
        mock_facade.get_context.return_value = {
            "success": True,
            "context": {"id": task_id, "data": "unified"}
        }
        mock_factory.return_value.create_facade.return_value = mock_facade
        
        result = use_case.execute(task_id, completion_summary="Complete with unified context")
        
        assert result["success"] is True
        
        # Verify task context_id was updated
        assert sample_task.context_id == str(task_id)
    
    def test_execute_context_validation_bypass(self, use_case, mock_task_repository, sample_task):
        """Test bypassing context validation when it fails"""
        task_id = "123"
        
        # Setup task with context_id  
        sample_task.context_id = "context-123"
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Make complete_task raise context validation error
        sample_task.complete_task.side_effect = [
            ValueError("Context must be updated after task update"),
            None  # Second call succeeds
        ]
        
        result = use_case.execute(task_id, completion_summary="Complete anyway")
        
        assert result["success"] is True
        
        # Verify task status was manually set
        assert sample_task.status == TaskStatus.done()
        assert sample_task._completion_summary == "Complete anyway"
    
    @patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory')
    def test_execute_update_context_after_completion(self, mock_factory, use_case, mock_task_repository, sample_task):
        """Test updating context with completion information"""
        task_id = "123"
        completion_summary = "Task completed"
        testing_notes = "Tests passed"
        next_recommendations = "Deploy next"
        
        sample_task.context_id = "context-123"
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Mock unified facade
        mock_facade = Mock()
        mock_facade.update_context = Mock()
        mock_factory.return_value.create_facade.return_value = mock_facade
        
        result = use_case.execute(
            task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes,
            next_recommendations=next_recommendations
        )
        
        assert result["success"] is True
        
        # Verify context was updated with completion info
        mock_facade.update_context.assert_called_once()
        update_call = mock_facade.update_context.call_args
        assert update_call.kwargs["level"] == "task"
        assert update_call.kwargs["context_id"] == str(task_id)
        
        context_data = update_call.kwargs["data"]
        assert context_data["progress"]["current_session_summary"] == completion_summary
        assert context_data["progress"]["completion_percentage"] == 100.0
        assert next_recommendations in context_data["progress"]["next_steps"]
        assert any("Testing completed" in step for step in context_data["progress"]["next_steps"])
    
    def test_update_dependent_tasks(self, use_case, mock_task_repository, sample_task):
        """Test updating tasks that depend on completed task"""
        completed_task = sample_task
        
        # Create dependent tasks
        dependent_task1 = Mock()
        dependent_task1.id = TaskId.from_string("456")
        dependent_task1.dependencies = [completed_task.id]
        dependent_task1.status = Mock(value="blocked")
        
        dependent_task2 = Mock()
        dependent_task2.id = TaskId.from_string("789")
        dependent_task2.dependencies = []
        dependent_task2.get_dependency_ids = Mock(return_value=[str(completed_task.id)])
        dependent_task2.status = Mock(value="blocked")
        
        unrelated_task = Mock()
        unrelated_task.id = TaskId.from_string("999")
        unrelated_task.dependencies = []
        unrelated_task.get_dependency_ids = Mock(return_value=[])
        
        all_tasks = [dependent_task1, dependent_task2, unrelated_task]
        mock_task_repository.find_all.return_value = all_tasks
        
        # Mock checking all dependencies complete
        use_case._check_all_dependencies_complete = Mock(return_value=True)
        
        use_case._update_dependent_tasks(completed_task)
        
        # Verify dependent tasks were found and updated
        assert dependent_task1.status == TaskStatus.todo()
        assert dependent_task2.status == TaskStatus.todo()
        assert mock_task_repository.save.call_count == 2  # Save both dependent tasks
    
    def test_update_dependent_tasks_with_remaining_dependencies(self, use_case, mock_task_repository, sample_task):
        """Test updating dependent task with remaining incomplete dependencies"""
        completed_task = sample_task
        
        # Create dependent task with multiple dependencies
        dependent_task = Mock()
        dependent_task.id = TaskId.from_string("456")
        dependent_task.dependencies = [completed_task.id, TaskId.from_string("other-dep")]
        dependent_task.status = Mock(value="blocked")
        
        mock_task_repository.find_all.return_value = [dependent_task]
        
        # Mock that not all dependencies are complete
        use_case._check_all_dependencies_complete = Mock(return_value=False)
        
        use_case._update_dependent_tasks(completed_task)
        
        # Verify task remains blocked
        assert dependent_task.status.value == "blocked"
        mock_task_repository.save.assert_not_called()
    
    def test_check_all_dependencies_complete_all_done(self, use_case):
        """Test checking dependencies when all are completed"""
        task = Mock()
        task.id = TaskId.from_string("123")
        task.dependencies = [TaskId.from_string("dep1"), TaskId.from_string("dep2")]
        
        dep1 = Mock()
        dep1.id = TaskId.from_string("dep1")
        dep1.status = Mock()
        dep1.status.is_done.return_value = True
        
        dep2 = Mock()
        dep2.id = TaskId.from_string("dep2")
        dep2.status = Mock()
        dep2.status.is_done.return_value = True
        
        all_tasks = [dep1, dep2, task]
        
        result = use_case._check_all_dependencies_complete(task, all_tasks)
        
        assert result is True
    
    def test_check_all_dependencies_complete_some_incomplete(self, use_case):
        """Test checking dependencies when some are incomplete"""
        task = Mock()
        task.id = TaskId.from_string("123")
        task.get_dependency_ids = Mock(return_value=["dep1", "dep2"])
        task.dependencies = None
        
        dep1 = Mock()
        dep1.id = TaskId.from_string("dep1")
        dep1.status = Mock()
        dep1.status.is_done = Mock(return_value=True)
        
        dep2 = Mock()  
        dep2.id = TaskId.from_string("dep2")
        dep2.status = Mock(value="in_progress")
        
        all_tasks = [dep1, dep2, task]
        
        result = use_case._check_all_dependencies_complete(task, all_tasks)
        
        assert result is False
    
    def test_check_all_dependencies_complete_missing_dependency(self, use_case, caplog):
        """Test checking dependencies when dependency task not found"""
        task = Mock()
        task.id = TaskId.from_string("123")
        task.dependencies = [TaskId.from_string("missing-dep")]
        
        all_tasks = [task]  # Missing dependency not in list
        
        with caplog.at_level(logging.WARNING):
            result = use_case._check_all_dependencies_complete(task, all_tasks)
        
        assert result is False
        assert "Dependency task" in caplog.text
        assert "not found" in caplog.text
    
    def test_execute_with_domain_events(self, use_case, mock_task_repository, sample_task):
        """Test handling of domain events after completion"""
        task_id = "123"
        
        # Create domain events
        event1 = TaskUpdated(
            task_id=sample_task.id,
            field_name="status",
            old_value="in_progress",
            new_value="done",
            updated_at=datetime.now(timezone.utc)
        )
        event2 = Mock()  # Non-TaskUpdated event
        
        sample_task.get_events.return_value = [event1, event2]
        mock_task_repository.find_by_id.return_value = sample_task
        
        result = use_case.execute(task_id, completion_summary="Complete")
        
        assert result["success"] is True
        sample_task.get_events.assert_called_once()
    
    def test_execute_int_task_id(self, use_case, mock_task_repository, sample_task):
        """Test execute with integer task ID"""
        task_id = 123  # Integer ID
        
        mock_task_repository.find_by_id.return_value = sample_task
        
        result = use_case.execute(task_id, completion_summary="Complete")
        
        assert result["success"] is True
        assert result["task_id"] == "123"
        
        # Verify TaskId was created from int
        find_call = mock_task_repository.find_by_id.call_args
        assert isinstance(find_call[0][0], TaskId)
    
    def test_execute_with_completion_service_validation(self, use_case, mock_task_repository, sample_task):
        """Test task completion validation using completion service"""
        task_id = "123"
        
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Mock completion service validation
        use_case._completion_service.validate_task_completion = Mock()
        use_case._completion_service.get_subtask_completion_summary = Mock(return_value={
            "total": 5,
            "completed": 5,
            "incomplete": 0,
            "completion_percentage": 100,
            "can_complete_parent": True
        })
        
        result = use_case.execute(task_id, completion_summary="Complete")
        
        assert result["success"] is True
        use_case._completion_service.validate_task_completion.assert_called_once_with(sample_task)