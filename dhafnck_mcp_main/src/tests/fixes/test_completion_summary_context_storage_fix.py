"""
TDD Tests for Completion Summary Context Storage Fix

PROBLEM:
- completion_summary is not being saved to context properly
- Context update fails due to wrong data structure
- Context shows status as "todo" even after task completion
- No completion_summary field appears in context after task completion

ROOT CAUSE:
1. Wrong data structure in complete_task.py: progress nested object vs ContextProgress schema
2. completion_summary stored in wrong location - should be in progress.current_session_summary
3. Status not synchronized between task and context

EXPECTED BEHAVIOR:
1. After task completion, context should contain completion_summary in progress.current_session_summary
2. Context status should be updated to "done" to match task status
3. Progress completion_percentage should be set to 100.0
4. testing_notes should be stored in progress.next_steps or similar field
"""

import pytest
from unittest.mock import Mock, patch
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from datetime import datetime
import uuid


class TestCompletionSummaryContextStorageFix:
    """Test suite for completion summary context storage fix"""

    @pytest.fixture
    def mock_task_repository(self):
        repo = Mock(spec=TaskRepository)
        # Return empty list for find_all to avoid iteration errors during dependency updates
        repo.find_all.return_value = []
        return repo

    @pytest.fixture
    def mock_task(self):
        task = Mock(spec=Task)
        task_id_str = str(uuid.uuid4())
        task.task_id = task_id_str
        task.git_branch_id = str(uuid.uuid4())
        task.title = "Test Task"
        task.status = TaskStatus.todo()
        task.priority = Priority.medium()
        task.created_at = datetime.now()
        task.context_id = None  # Add context_id attribute
        task.project_id = "test-project"  # Add project_id for auto-context creation
        task.get_subtask_progress.return_value = {"total": 0, "completed": 0}
        
        # Mock the subtasks attribute that might be accessed during iteration
        task.subtasks = []  # Empty list to avoid iteration error
        
        # Mock the id property (required by TaskCompletionService) with proper .value attribute
        from fastmcp.task_management.domain.value_objects.task_id import TaskId
        task.id = Mock()
        task.id.value = task_id_str
        
        def mock_complete_task(completion_summary, context_updated_at=None):
            task.status = TaskStatus.done()
            task.completion_summary = completion_summary
            return task
        
        task.complete_task = mock_complete_task
        return task

    @pytest.fixture
    def mock_subtask_repository(self):
        from fastmcp.task_management.domain.repositories.subtask_repository import SubtaskRepository
        repo = Mock(spec=SubtaskRepository)
        # Return empty list for subtask search to avoid iteration errors
        repo.find_by_parent_task_id.return_value = []
        return repo

    @pytest.fixture
    def mock_task_context_repository(self):
        from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository
        repo = Mock(spec=TaskContextRepository)
        # Return None to trigger context auto-creation
        repo.get.return_value = None
        return repo

    @pytest.fixture
    def complete_task_use_case(self, mock_task_repository, mock_subtask_repository, mock_task_context_repository):
        return CompleteTaskUseCase(mock_task_repository, mock_subtask_repository, mock_task_context_repository)

    def test_completion_summary_stored_in_correct_context_location(self, complete_task_use_case, mock_task_repository, mock_task):
        """
        TEST: Completion summary should be stored in progress.current_session_summary
        
        This test should now PASS after the fix
        """
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        # Mock the task.status.is_done() check to return False initially
        mock_task.status.is_done.return_value = False
        
        completion_summary = "Task completed successfully with all features implemented"
        testing_notes = "All unit tests pass, integration tests verified"
        
        # Mock the UnifiedContextFacade to capture the context update
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            # Assert - Check that context update was called with correct structure
            print(f"Result: {result}")
            print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and "success" in result:
                print(f"Success value: {result['success']}, type: {type(result['success'])}")
                if not result["success"]:
                    print(f"Failure message: {result.get('message', 'No message')}")
            assert result["success"] is True
            mock_facade.update_context.assert_called_once()
            
            # Get the actual call arguments
            call_args = mock_facade.update_context.call_args
            context_data = call_args[1]["data"]  # Get the 'data' keyword argument
            
            # FIXED: Now using correct ContextProgress schema structure
            assert "progress" in context_data
            
            progress_data = context_data["progress"]
            assert "current_session_summary" in progress_data
            assert progress_data["current_session_summary"] == completion_summary
            assert progress_data["completion_percentage"] == 100.0

    def test_context_status_synchronized_with_task_status(self, complete_task_use_case, mock_task_repository, mock_task):
        """
        TEST: Context status should be updated to match task status
        
        This test should now PASS after the fix
        """
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        completion_summary = "Task fully completed"
        
        # Mock the UnifiedContextFacade
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary
            )
            
            # Assert
            assert result["success"] is True
            mock_facade.update_context.assert_called_once()
            
            # Get the actual call arguments
            call_args = mock_facade.update_context.call_args
            context_data = call_args[1]["data"]
            
            # FIXED: Status synchronization now implemented
            assert "metadata" in context_data
            assert context_data["metadata"]["status"] == "done"

    def test_testing_notes_stored_in_context(self, complete_task_use_case, mock_task_repository, mock_task):
        """
        TEST: Testing notes should be stored in progress.next_steps
        
        This test should now PASS after the fix
        """
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        completion_summary = "Task completed"
        testing_notes = "Unit tests: 15/15 passed, Integration tests: 8/8 passed, Manual testing completed"
        
        # Mock the UnifiedContextFacade
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            # Assert
            assert result["success"] is True
            mock_facade.update_context.assert_called_once()
            
            # Get the actual call arguments
            call_args = mock_facade.update_context.call_args
            context_data = call_args[1]["data"]
            
            # FIXED: testing_notes now stored in progress.next_steps
            assert "progress" in context_data
            progress_data = context_data["progress"]
            assert "next_steps" in progress_data
            
            # testing_notes should be included in next_steps as "Testing completed: ..."
            testing_step = f"Testing completed: {testing_notes}"
            assert testing_step in progress_data["next_steps"]

    def test_context_update_structure_matches_schema(self, complete_task_use_case, mock_task_repository, mock_task):
        """
        TEST: Context update structure should match ContextProgress schema
        
        This test should now PASS after the fix
        """
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        completion_summary = "Feature implementation completed"
        testing_notes = "All tests pass"
        next_recommendations = ["Deploy to staging", "Update documentation"]
        
        # Mock the UnifiedContextFacade
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes,
                next_recommendations=next_recommendations
            )
            
            # Assert
            assert result["success"] is True
            mock_facade.update_context.assert_called_once()
            
            # Get the actual call arguments
            call_args = mock_facade.update_context.call_args
            context_data = call_args[1]["data"]
            
            # FIXED: Structure now matches ContextProgress schema
            assert "progress" in context_data
            progress_data = context_data["progress"]
            
            # ContextProgress expected fields all present and correct types:
            assert isinstance(progress_data.get("current_session_summary", ""), str)
            assert isinstance(progress_data.get("completion_percentage", 0), (int, float))
            assert isinstance(progress_data.get("next_steps", []), list)
            assert isinstance(progress_data.get("completed_actions", []), list)
            
            # Specific values:
            assert progress_data["current_session_summary"] == completion_summary
            assert progress_data["completion_percentage"] == 100.0
            
            # next_recommendations should be in next_steps
            next_steps = progress_data.get("next_steps", [])
            for recommendation in next_recommendations:
                assert recommendation in next_steps

    def test_context_update_handles_missing_optional_fields(self, complete_task_use_case, mock_task_repository, mock_task):
        """
        TEST: Context update should work with minimal required fields
        
        This should pass - ensuring the fix handles optional fields gracefully
        """
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        completion_summary = "Task done"
        # No testing_notes or next_recommendations provided
        
        # Mock the UnifiedContextFacade
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary
            )
            
            # Assert
            assert result["success"] is True
            mock_facade.update_context.assert_called_once()
            
            # Get the actual call arguments
            call_args = mock_facade.update_context.call_args
            context_data = call_args[1]["data"]
            
            # Should still have proper structure with minimal data
            assert "progress" in context_data
            progress_data = context_data["progress"]
            assert progress_data["current_session_summary"] == completion_summary
            assert progress_data["completion_percentage"] == 100.0
            
            # Status should still be synchronized
            assert "metadata" in context_data
            assert context_data["metadata"]["status"] == "done"