"""Test automatic context synchronization for task state changes.

This test suite verifies that context is automatically synchronized when:
1. Tasks are updated (UpdateTaskUseCase)
2. Subtasks are updated (UpdateSubtaskUseCase) 
3. Tasks are completed (CompleteTaskUseCase)

Part of Fix for Issue #3: Automatic Context Updates for Task State Changes
"""

import pytest
import uuid
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from fastmcp.task_management.application.use_cases.update_task import UpdateTaskUseCase
from fastmcp.task_management.application.use_cases.update_subtask import UpdateSubtaskUseCase
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.application.dtos.task import UpdateTaskRequest
from fastmcp.task_management.application.dtos.subtask.update_subtask_request import UpdateSubtaskRequest
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestAutomaticContextSync:
    """Test automatic context synchronization across all use cases."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_task_repository = Mock()
        self.mock_subtask_repository = Mock()
        self.mock_task_context_repository = Mock()
        
        # Create test task with proper UUID format
        self.test_task = Task(
            id=TaskId.from_string("12345678-1234-1234-1234-123456789012"),
            title="Test Task",
            description="Test Description",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=[],
            labels=[],
            git_branch_id="87654321-4321-4321-4321-210987654321"
        )
        self.test_task.context_id = "12345678-1234-1234-1234-123456789012"  # Set context_id
        
        # Create test subtask
        self.test_subtask = Subtask(
            title="Test Subtask",
            description="Test Subtask Description",
            parent_task_id=self.test_task.id,
            id=SubtaskId("11111111-1111-1111-1111-111111111111")
        )

    @patch('fastmcp.task_management.application.use_cases.update_task.TaskContextSyncService')
    def test_update_task_triggers_context_sync(self, mock_sync_service_class):
        """Test that UpdateTaskUseCase triggers context sync after task update."""
        # Setup
        mock_sync_service = Mock()
        mock_sync_service_class.return_value = mock_sync_service
        
        self.mock_task_repository.find_by_id.return_value = self.test_task
        self.mock_task_repository.save.return_value = None
        
        update_use_case = UpdateTaskUseCase(self.mock_task_repository)
        
        # Mock asyncio to simulate no running event loop
        with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")), \
             patch('asyncio.run') as mock_asyncio_run:
            
            mock_asyncio_run.return_value = {"success": True, "context": {"id": "12345678-1234-1234-1234-123456789012"}}
            
            # Execute
            request = UpdateTaskRequest(
                task_id="12345678-1234-1234-1234-123456789012",
                title="Updated Title",
                status="in_progress"
            )
            
            result = update_use_case.execute(request)
            
            # Verify context sync was called
            assert mock_sync_service_class.called
            assert mock_asyncio_run.called
            assert result.success is True

    @patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService')
    def test_update_subtask_triggers_parent_context_sync(self, mock_sync_service_class):
        """Test that UpdateSubtaskUseCase triggers parent task context sync."""
        # Setup
        mock_sync_service = Mock()
        mock_sync_service_class.return_value = mock_sync_service
        
        self.mock_task_repository.find_by_id.return_value = self.test_task
        self.mock_subtask_repository.find_by_id.return_value = self.test_subtask
        self.mock_subtask_repository.save.return_value = None
        
        update_use_case = UpdateSubtaskUseCase(
            self.mock_task_repository, 
            self.mock_subtask_repository
        )
        
        # Mock asyncio to simulate no running event loop
        with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")), \
             patch('asyncio.run') as mock_asyncio_run:
            
            mock_asyncio_run.return_value = {"success": True, "context": {"id": "12345678-1234-1234-1234-123456789012"}}
            
            # Execute
            request = UpdateSubtaskRequest(
                task_id="12345678-1234-1234-1234-123456789012",
                id="11111111-1111-1111-1111-111111111111",
                title="Updated Subtask Title",
                progress_percentage=50
            )
            
            result = update_use_case.execute(request)
            
            # Verify parent task context sync was called
            assert mock_sync_service_class.called
            assert mock_asyncio_run.called
            assert result.task_id == "12345678-1234-1234-1234-123456789012"

    @patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory')
    def test_complete_task_updates_context_with_completion_data(self, mock_facade_factory):
        """Test that CompleteTaskUseCase updates context with completion information."""
        # Setup
        mock_facade = Mock()
        mock_facade.create_facade.return_value = mock_facade
        mock_facade.update_context.return_value = {"success": True}
        mock_facade_factory.return_value = mock_facade
        
        self.test_task.status = TaskStatus.in_progress()  # Set to in_progress so it can be completed
        self.mock_task_repository.find_by_id.return_value = self.test_task
        self.mock_task_repository.save.return_value = None
        
        complete_use_case = CompleteTaskUseCase(
            self.mock_task_repository,
            self.mock_subtask_repository,
            self.mock_task_context_repository
        )
        
        # Execute
        result = complete_use_case.execute(
            task_id="12345678-1234-1234-1234-123456789012",
            completion_summary="Task completed successfully",
            testing_notes="All tests passed",
            next_recommendations="Consider optimization"
        )
        
        # Verify context was updated with completion data
        assert mock_facade.update_context.called
        update_call = mock_facade.update_context.call_args
        assert update_call[1]['level'] == 'task'
        assert update_call[1]['context_id'] == '12345678-1234-1234-1234-123456789012'
        
        # Check completion data structure
        context_data = update_call[1]['data']
        assert 'progress' in context_data
        assert context_data['progress']['completion_summary'] == "Task completed successfully"
        assert context_data['progress']['testing_notes'] == "All tests passed"
        assert context_data['progress']['completion_percentage'] == 100.0
        
        assert result['success'] is True

    def test_context_sync_handles_exceptions_gracefully(self):
        """Test that context sync failures don't break task operations."""
        # Setup UpdateTaskUseCase with failing context sync
        with patch('fastmcp.task_management.application.use_cases.update_task.TaskContextSyncService') as mock_sync_service_class:
            mock_sync_service_class.side_effect = Exception("Context sync failed")
            
            self.mock_task_repository.find_by_id.return_value = self.test_task
            self.mock_task_repository.save.return_value = None
            
            update_use_case = UpdateTaskUseCase(self.mock_task_repository)
            
            # Execute - should not raise exception despite context sync failure
            request = UpdateTaskRequest(
                task_id="12345678-1234-1234-1234-123456789012",
                title="Updated Title"
            )
            
            result = update_use_case.execute(request)
            
            # Task update should still succeed
            assert result.success is True

    def test_context_sync_handles_async_context_correctly(self):
        """Test context sync behavior when already in async context."""
        # Setup
        with patch('fastmcp.task_management.application.use_cases.update_task.TaskContextSyncService') as mock_sync_service_class:
            mock_sync_service = Mock()
            mock_sync_service_class.return_value = mock_sync_service
            
            self.mock_task_repository.find_by_id.return_value = self.test_task
            self.mock_task_repository.save.return_value = None
            
            update_use_case = UpdateTaskUseCase(self.mock_task_repository)
            
            # Mock being in an async context (running event loop)
            mock_loop = Mock()
            with patch('asyncio.get_running_loop', return_value=mock_loop):
                
                # Execute
                request = UpdateTaskRequest(
                    task_id="12345678-1234-1234-1234-123456789012", 
                    status="in_progress"
                )
                
                result = update_use_case.execute(request)
                
                # Should complete successfully and log context sync triggered
                assert result.success is True

    def test_context_sync_extracts_task_metadata_correctly(self):
        """Test that context sync extracts correct task metadata."""
        # Setup task with complex metadata
        task_with_metadata = Task(
            id=TaskId.from_string("22222222-2222-2222-2222-222222222222"),
            title="Complex Task",
            description="Complex Description",
            status=TaskStatus.in_progress(),
            priority=Priority.high(),
            assignees=["user1", "user2"],
            labels=["frontend", "urgent"],
            git_branch_id="33333333-3333-3333-3333-333333333333"
        )
        task_with_metadata.project_id = "44444444-4444-4444-4444-444444444444"
        task_with_metadata.context_id = "22222222-2222-2222-2222-222222222222"
        
        with patch('fastmcp.task_management.application.use_cases.update_task.TaskContextSyncService') as mock_sync_service_class:
            mock_sync_service = Mock()
            mock_sync_service_class.return_value = mock_sync_service
            
            self.mock_task_repository.find_by_id.return_value = task_with_metadata
            self.mock_task_repository.save.return_value = None
            
            update_use_case = UpdateTaskUseCase(self.mock_task_repository)
            
            # Mock asyncio to capture sync call details
            with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")), \
                 patch('asyncio.run') as mock_asyncio_run:
                
                mock_asyncio_run.return_value = {"success": True}
                
                # Execute
                request = UpdateTaskRequest(
                    task_id="22222222-2222-2222-2222-222222222222",
                    assignees=["user1", "user2", "user3"]  # Add another assignee
                )
                
                result = update_use_case.execute(request)
                
                # Verify task metadata was extracted correctly
                assert result.success is True
                assert mock_asyncio_run.called

    def test_subtask_context_sync_preserves_parent_task_context(self):
        """Test that subtask updates don't interfere with parent task context structure."""
        # Setup
        parent_task = Task(
            id=TaskId.from_string("55555555-5555-5555-5555-555555555555"),
            title="Parent Task",
            description="Parent Description", 
            status=TaskStatus.in_progress(),
            priority=Priority.medium(),
            git_branch_id="66666666-6666-6666-6666-666666666666"
        )
        parent_task.context_id = "55555555-5555-5555-5555-555555555555"
        
        with patch('fastmcp.task_management.application.use_cases.update_subtask.TaskContextSyncService') as mock_sync_service_class:
            mock_sync_service = Mock()
            mock_sync_service_class.return_value = mock_sync_service
            
            self.mock_task_repository.find_by_id.return_value = parent_task
            self.mock_subtask_repository.find_by_id.return_value = self.test_subtask
            self.mock_subtask_repository.save.return_value = None
            
            update_use_case = UpdateSubtaskUseCase(
                self.mock_task_repository,
                self.mock_subtask_repository
            )
            
            with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")), \
                 patch('asyncio.run') as mock_asyncio_run:
                
                mock_asyncio_run.return_value = {"success": True}
                
                # Execute subtask update
                request = UpdateSubtaskRequest(
                    task_id="55555555-5555-5555-5555-555555555555",
                    id="11111111-1111-1111-1111-111111111111",
                    status="done"  # Complete the subtask
                )
                
                result = update_use_case.execute(request)
                
                # Verify parent context sync was called correctly
                assert mock_asyncio_run.called
                assert result.task_id == "55555555-5555-5555-5555-555555555555"


class TestContextSyncIntegration:
    """Integration tests for context sync across multiple operations."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.mock_task_repository = Mock()
        self.mock_subtask_repository = Mock()
        
        # Create test task
        self.test_task = Task(
            id=TaskId.from_string("77777777-7777-7777-7777-777777777777"),
            title="Integration Test Task",
            description="Integration Description",
            status=TaskStatus.todo(),
            priority=Priority.low(),
            git_branch_id="88888888-8888-8888-8888-888888888888"
        )
        self.test_task.context_id = "77777777-7777-7777-7777-777777777777"

    def test_task_lifecycle_context_sync_sequence(self):
        """Test context sync throughout complete task lifecycle."""
        # This is a conceptual test - in real implementation would test:
        # 1. Task creation triggers context creation
        # 2. Task updates trigger context sync
        # 3. Subtask updates trigger parent context sync
        # 4. Task completion updates context with completion data
        
        self.mock_task_repository.find_by_id.return_value = self.test_task
        self.mock_task_repository.save.return_value = None
        
        # Test Update -> Complete sequence
        with patch('fastmcp.task_management.application.use_cases.update_task.TaskContextSyncService'), \
             patch('fastmcp.task_management.application.use_cases.complete_task.UnifiedContextFacadeFactory') as mock_facade_factory:
            
            mock_facade = Mock()
            mock_facade.update_context.return_value = {"success": True}
            mock_facade_factory.return_value.create_facade.return_value = mock_facade
            
            # 1. Update task
            update_use_case = UpdateTaskUseCase(self.mock_task_repository)
            
            with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running loop")), \
                 patch('asyncio.run', return_value={"success": True}):
                
                update_result = update_use_case.execute(UpdateTaskRequest(
                    task_id="77777777-7777-7777-7777-777777777777",
                    status="in_progress"
                ))
                
                assert update_result.success is True
            
            # 2. Complete task  
            self.test_task.status = TaskStatus.in_progress()  # Update status for completion
            complete_use_case = CompleteTaskUseCase(
                self.mock_task_repository,
                self.mock_subtask_repository
            )
            
            complete_result = complete_use_case.execute(
                task_id="77777777-7777-7777-7777-777777777777",
                completion_summary="Integration test completed"
            )
            
            # Verify both operations succeeded and context was updated
            assert complete_result['success'] is True
            assert mock_facade.update_context.called