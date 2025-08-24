"""Comprehensive test suite for Update Subtask Use Case"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timezone
import asyncio

from fastmcp.task_management.application.use_cases.update_subtask import UpdateSubtaskUseCase
from fastmcp.task_management.application.dtos.subtask import UpdateSubtaskRequest, SubtaskResponse
from fastmcp.task_management.domain import TaskRepository, TaskId, TaskNotFoundError
from fastmcp.task_management.domain.repositories.subtask_repository import SubtaskRepository
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId


class TestUpdateSubtaskUseCase:
    """Test suite for UpdateSubtaskUseCase"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        return Mock(spec=TaskRepository)
    
    @pytest.fixture
    def mock_subtask_repository(self):
        """Create a mock subtask repository"""
        return Mock(spec=SubtaskRepository)
    
    @pytest.fixture
    def use_case(self, mock_task_repository, mock_subtask_repository):
        """Create an UpdateSubtaskUseCase instance"""
        return UpdateSubtaskUseCase(mock_task_repository, mock_subtask_repository)
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing"""
        task = Task(
            id=TaskId.from_string("task-123"),
            title="Parent Task",
            description="Parent task description",
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            git_branch_id="branch-456",
            project_id="project-789"
        )
        # Add subtasks to task
        task._subtasks = {
            "subtask-001": {
                "id": "subtask-001",
                "title": "Subtask 1",
                "description": "First subtask",
                "status": "todo",
                "priority": "medium",
                "assignees": ["user1"]
            }
        }
        return task
    
    @pytest.fixture
    def sample_subtask(self):
        """Create a sample subtask for testing"""
        return Subtask(
            id=SubtaskId("subtask-001"),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=TaskId.from_string("task-123"),
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["user1"],
            progress_percentage=0
        )
    
    def test_init(self, mock_task_repository, mock_subtask_repository):
        """Test use case initialization"""
        use_case = UpdateSubtaskUseCase(mock_task_repository, mock_subtask_repository)
        assert use_case._task_repository == mock_task_repository
        assert use_case._subtask_repository == mock_subtask_repository
        assert use_case._context_sync_service is None
    
    def test_execute_with_subtask_repository_update_all_fields(self, use_case, mock_task_repository, mock_subtask_repository, sample_task, sample_subtask):
        """Test updating all subtask fields using subtask repository"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = sample_subtask
        
        # Mock update parent task progress
        with patch.object(use_case, '_update_parent_task_progress'):
            with patch.object(use_case, '_sync_parent_task_context_after_subtask_update'):
                # Create request with all fields
                request = UpdateSubtaskRequest(
                    task_id="task-123",
                    id="subtask-001",
                    title="Updated Subtask",
                    description="Updated description",
                    status="in_progress",
                    priority="high",
                    assignees=["user2", "user3"],
                    progress_percentage=50
                )
                
                # Execute use case
                response = use_case.execute(request)
        
        # Verify subtask methods were called
        assert sample_subtask.title == "Updated Subtask"
        assert sample_subtask.description == "Updated description"
        assert sample_subtask.status == TaskStatus.in_progress()
        assert sample_subtask.priority == Priority.high()
        assert sample_subtask.assignees == ["user2", "user3"]
        assert sample_subtask.progress_percentage == 50
        
        # Verify repository save was called
        mock_subtask_repository.save.assert_called_once_with(sample_subtask)
        
        # Verify response
        assert isinstance(response, SubtaskResponse)
        assert response.task_id == "task-123"
        assert response.subtask["title"] == "Updated Subtask"
    
    def test_execute_with_subtask_repository_status_done(self, use_case, mock_task_repository, mock_subtask_repository, sample_task, sample_subtask):
        """Test marking subtask as done using subtask repository"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = sample_subtask
        
        # Mock update parent task progress
        with patch.object(use_case, '_update_parent_task_progress'):
            with patch.object(use_case, '_sync_parent_task_context_after_subtask_update'):
                # Create request to mark as done
                request = UpdateSubtaskRequest(
                    task_id="task-123",
                    id="subtask-001",
                    status="done"
                )
                
                # Execute use case
                response = use_case.execute(request)
        
        # Verify subtask complete method was called
        assert sample_subtask.status == TaskStatus.done()
        
        # Verify repository save was called
        mock_subtask_repository.save.assert_called_once_with(sample_subtask)
    
    def test_execute_with_subtask_repository_status_todo(self, use_case, mock_task_repository, mock_subtask_repository, sample_task):
        """Test reopening subtask using subtask repository"""
        # Create a completed subtask
        completed_subtask = Subtask(
            id=SubtaskId("subtask-001"),
            title="Completed Subtask",
            description="Was completed",
            parent_task_id=TaskId.from_string("task-123"),
            status=TaskStatus.done(),
            priority=Priority.medium(),
            assignees=["user1"]
        )
        
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = completed_subtask
        
        # Mock update parent task progress
        with patch.object(use_case, '_update_parent_task_progress'):
            with patch.object(use_case, '_sync_parent_task_context_after_subtask_update'):
                # Create request to reopen
                request = UpdateSubtaskRequest(
                    task_id="task-123",
                    id="subtask-001",
                    status="todo"
                )
                
                # Execute use case
                response = use_case.execute(request)
        
        # Verify subtask reopen method was called
        assert completed_subtask.status == TaskStatus.todo()
        
        # Verify repository save was called
        mock_subtask_repository.save.assert_called_once_with(completed_subtask)
    
    def test_execute_with_subtask_repository_progress_percentage(self, use_case, mock_task_repository, mock_subtask_repository, sample_task, sample_subtask):
        """Test updating progress percentage using subtask repository"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = sample_subtask
        
        # Mock update parent task progress
        with patch.object(use_case, '_update_parent_task_progress'):
            with patch.object(use_case, '_sync_parent_task_context_after_subtask_update'):
                # Create request with progress percentage
                request = UpdateSubtaskRequest(
                    task_id="task-123",
                    id="subtask-001",
                    progress_percentage=75
                )
                
                # Execute use case
                response = use_case.execute(request)
        
        # Verify progress was updated
        assert sample_subtask.progress_percentage == 75
        assert sample_subtask.status == TaskStatus.in_progress()  # Auto-updated based on progress
        
        # Verify repository save was called
        mock_subtask_repository.save.assert_called_once_with(sample_subtask)
    
    def test_execute_fallback_to_task_entity(self, use_case, mock_task_repository, sample_task):
        """Test fallback to task entity method when no subtask repository"""
        # Create use case without subtask repository
        use_case_no_subtask_repo = UpdateSubtaskUseCase(mock_task_repository, None)
        
        # Mock task repository
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Mock task methods
        sample_task.update_subtask = Mock(return_value=True)
        sample_task.get_subtask = Mock(return_value={
            "id": "subtask-001",
            "title": "Updated via Task",
            "description": "Updated description",
            "status": "in_progress",
            "priority": "high",
            "assignees": ["user2"]
        })
        sample_task.get_subtask_progress = Mock(return_value={"completed": 0, "total": 1})
        
        # Mock context sync
        with patch.object(use_case_no_subtask_repo, '_sync_parent_task_context_after_subtask_update'):
            # Create request
            request = UpdateSubtaskRequest(
                task_id="task-123",
                id="subtask-001",
                title="Updated via Task",
                description="Updated description",
                status="in_progress",
                priority="high",
                assignees=["user2"]
            )
            
            # Execute use case
            response = use_case_no_subtask_repo.execute(request)
        
        # Verify task methods were called
        sample_task.update_subtask.assert_called_once_with(
            "subtask-001",
            {
                "title": "Updated via Task",
                "description": "Updated description",
                "status": "in_progress",
                "priority": "high",
                "assignees": ["user2"]
            }
        )
        mock_task_repository.save.assert_called_once_with(sample_task)
        
        # Verify response
        assert isinstance(response, SubtaskResponse)
        assert response.subtask["title"] == "Updated via Task"
    
    def test_execute_task_not_found(self, use_case, mock_task_repository):
        """Test updating subtask when parent task not found"""
        # Mock task repository to return None
        mock_task_repository.find_by_id.return_value = None
        
        # Create request
        request = UpdateSubtaskRequest(
            task_id="nonexistent-task",
            id="subtask-001",
            title="Updated"
        )
        
        # Execute and expect exception
        with pytest.raises(TaskNotFoundError) as exc_info:
            use_case.execute(request)
        
        assert "Task nonexistent-task not found" in str(exc_info.value)
    
    def test_execute_subtask_not_found_with_repository(self, use_case, mock_task_repository, mock_subtask_repository, sample_task):
        """Test updating subtask when subtask not found in repository"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = None
        
        # Create request
        request = UpdateSubtaskRequest(
            task_id="task-123",
            id="nonexistent-subtask",
            title="Updated"
        )
        
        # Execute and expect exception
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(request)
        
        assert "Subtask nonexistent-subtask not found" in str(exc_info.value)
    
    def test_execute_subtask_not_found_fallback(self, use_case, mock_task_repository, sample_task):
        """Test updating subtask when subtask not found in task entity"""
        # Create use case without subtask repository
        use_case_no_subtask_repo = UpdateSubtaskUseCase(mock_task_repository, None)
        
        # Mock task repository
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Mock task method to return False
        sample_task.update_subtask = Mock(return_value=False)
        
        # Create request
        request = UpdateSubtaskRequest(
            task_id="task-123",
            id="nonexistent-subtask",
            title="Updated"
        )
        
        # Execute and expect exception
        with pytest.raises(ValueError) as exc_info:
            use_case_no_subtask_repo.execute(request)
        
        assert "Subtask nonexistent-subtask not found" in str(exc_info.value)
    
    def test_convert_to_task_id_from_string(self, use_case):
        """Test converting string to TaskId"""
        result = use_case._convert_to_task_id("task-123")
        assert isinstance(result, TaskId)
        assert str(result.value) == "task-123"
    
    def test_convert_to_task_id_from_int(self, use_case):
        """Test converting int to TaskId"""
        result = use_case._convert_to_task_id(123)
        assert isinstance(result, TaskId)
        assert result.value == 123
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskProgressService')
    def test_update_parent_task_progress(self, mock_progress_service_class, use_case, mock_task_repository, mock_subtask_repository):
        """Test updating parent task progress"""
        # Mock progress service
        mock_progress_service = Mock()
        mock_progress_service_class.return_value = mock_progress_service
        
        # Call method
        use_case._update_parent_task_progress("task-123")
        
        # Verify progress service was called
        mock_progress_service_class.assert_called_once_with(
            mock_task_repository,
            mock_subtask_repository
        )
        mock_progress_service.update_task_progress_from_subtasks.assert_called_once_with("task-123")
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskProgressService')
    def test_update_parent_task_progress_error_handling(self, mock_progress_service_class, use_case, caplog):
        """Test error handling in parent task progress update"""
        import logging
        
        # Set log level
        caplog.set_level(logging.WARNING)
        
        # Mock progress service to raise exception
        mock_progress_service = Mock()
        mock_progress_service.update_task_progress_from_subtasks.side_effect = Exception("Progress error")
        mock_progress_service_class.return_value = mock_progress_service
        
        # Call method
        use_case._update_parent_task_progress("task-123")
        
        # Verify error was logged but not raised
        assert "Failed to update parent task progress" in caplog.text
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService')
    @patch('fastmcp.task_management.application.use_cases.update_subtask.asyncio')
    def test_sync_parent_task_context_after_subtask_update_no_event_loop(self, mock_asyncio, mock_sync_service_class, use_case, sample_task, caplog):
        """Test syncing parent task context when no event loop is running"""
        import logging
        
        # Set log level
        caplog.set_level(logging.INFO)
        
        # Mock no running event loop
        mock_asyncio.get_running_loop.side_effect = RuntimeError("No event loop")
        
        # Mock async run
        mock_async_result = AsyncMock()
        mock_asyncio.run.return_value = {"success": True}
        
        # Mock sync service
        mock_sync_service = Mock()
        mock_sync_service.sync_context_and_get_task = mock_async_result
        mock_sync_service_class.return_value = mock_sync_service
        
        # Call method
        use_case._sync_parent_task_context_after_subtask_update(sample_task)
        
        # Verify async context was created and run
        mock_asyncio.run.assert_called_once()
        assert "No async context, creating new event loop" in caplog.text
        assert "Successfully synced parent task context" in caplog.text
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService')
    @patch('fastmcp.task_management.application.use_cases.update_subtask.asyncio')
    def test_sync_parent_task_context_after_subtask_update_with_event_loop(self, mock_asyncio, mock_sync_service_class, use_case, sample_task, caplog):
        """Test syncing parent task context when event loop is running"""
        import logging
        
        # Set log level
        caplog.set_level(logging.INFO)
        
        # Mock running event loop
        mock_loop = Mock()
        mock_asyncio.get_running_loop.return_value = mock_loop
        
        # Call method
        use_case._sync_parent_task_context_after_subtask_update(sample_task)
        
        # Verify only logged that sync was triggered
        assert "Running in async context, context sync triggered" in caplog.text
        assert "Parent task context sync triggered" in caplog.text
        # Verify asyncio.run was NOT called
        mock_asyncio.run.assert_not_called()
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService')
    @patch('fastmcp.task_management.application.use_cases.update_subtask.asyncio')
    def test_sync_parent_task_context_after_subtask_update_returns_none(self, mock_asyncio, mock_sync_service_class, use_case, sample_task, caplog):
        """Test handling when context sync returns None"""
        import logging
        
        # Set log level
        caplog.set_level(logging.WARNING)
        
        # Mock no running event loop
        mock_asyncio.get_running_loop.side_effect = RuntimeError("No event loop")
        
        # Mock async run to return None
        mock_asyncio.run.return_value = None
        
        # Mock sync service
        mock_sync_service = Mock()
        mock_sync_service_class.return_value = mock_sync_service
        
        # Call method
        use_case._sync_parent_task_context_after_subtask_update(sample_task)
        
        # Verify warning was logged
        assert "Parent task context sync returned None" in caplog.text
    
    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService')
    def test_sync_parent_task_context_after_subtask_update_error_handling(self, mock_sync_service_class, use_case, sample_task, caplog):
        """Test error handling in parent task context sync"""
        import logging
        
        # Set log level
        caplog.set_level(logging.WARNING)
        
        # Mock sync service to raise exception
        mock_sync_service_class.side_effect = Exception("Sync service error")
        
        # Call method - should not raise exception
        use_case._sync_parent_task_context_after_subtask_update(sample_task)
        
        # Verify error was logged but not raised
        assert "Failed to sync parent task context" in caplog.text
        assert "after subtask update: Sync service error" in caplog.text
    
    def test_execute_complete_workflow_with_all_updates(self, use_case, mock_task_repository, mock_subtask_repository, sample_task, sample_subtask):
        """Test complete workflow with all components working together"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = sample_subtask
        
        # Mock progress service
        with patch('fastmcp.task_management.application.use_cases.update_subtask.TaskProgressService') as mock_progress_service_class:
            mock_progress_service = Mock()
            mock_progress_service_class.return_value = mock_progress_service
            
            # Mock context sync service
            with patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService') as mock_sync_service_class:
                mock_sync_service = Mock()
                mock_sync_service_class.return_value = mock_sync_service
                
                # Mock asyncio
                with patch('fastmcp.task_management.application.use_cases.update_subtask.asyncio') as mock_asyncio:
                    mock_asyncio.get_running_loop.side_effect = RuntimeError("No event loop")
                    mock_asyncio.run.return_value = {"success": True}
                    
                    # Create request
                    request = UpdateSubtaskRequest(
                        task_id="task-123",
                        id="subtask-001",
                        title="Complete Update",
                        status="done",
                        progress_percentage=100
                    )
                    
                    # Execute use case
                    response = use_case.execute(request)
        
        # Verify all components were called
        mock_subtask_repository.save.assert_called_once()
        mock_progress_service.update_task_progress_from_subtasks.assert_called_once_with("task-123")
        mock_sync_service_class.assert_called_once()
        mock_asyncio.run.assert_called_once()
        
        # Verify response
        assert response.task_id == "task-123"
        assert response.subtask["title"] == "Complete Update"
        assert response.progress == {"completed": 0, "total": 1}
    
    def test_execute_partial_update_fields(self, use_case, mock_task_repository, mock_subtask_repository, sample_task, sample_subtask):
        """Test updating only some fields of subtask"""
        # Mock repositories
        mock_task_repository.find_by_id.return_value = sample_task
        mock_subtask_repository.find_by_id.return_value = sample_subtask
        
        # Store original values
        original_description = sample_subtask.description
        original_status = sample_subtask.status
        original_priority = sample_subtask.priority
        
        # Mock update parent task progress
        with patch.object(use_case, '_update_parent_task_progress'):
            with patch.object(use_case, '_sync_parent_task_context_after_subtask_update'):
                # Create request with only title update
                request = UpdateSubtaskRequest(
                    task_id="task-123",
                    id="subtask-001",
                    title="Only Title Updated"
                )
                
                # Execute use case
                response = use_case.execute(request)
        
        # Verify only title was updated
        assert sample_subtask.title == "Only Title Updated"
        assert sample_subtask.description == original_description
        assert sample_subtask.status == original_status
        assert sample_subtask.priority == original_priority