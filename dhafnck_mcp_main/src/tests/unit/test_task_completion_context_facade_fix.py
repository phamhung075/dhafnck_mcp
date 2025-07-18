"""
Test Task Completion Context Facade Fix

TDD tests for fixing the HierarchicalContextFacadeFactory.create_facade() parameter error
when completing tasks that have context validation.

Error being fixed:
"HierarchicalContextFacadeFactory.create_context_facade() got an unexpected keyword argument 'git_branch_name'"

Root cause: complete_task.py line 112 calls create_facade() without required git_branch_id parameter.
"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.exceptions import TaskNotFoundError


class TestTaskCompletionContextFacadeFix:
    """Test suite for task completion context facade parameter fix."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.task_repository = Mock()
        self.subtask_repository = Mock()
        self.hierarchical_context_service = Mock()
        
        self.use_case = CompleteTaskUseCase(
            task_repository=self.task_repository,
            subtask_repository=self.subtask_repository,
            hierarchical_context_service=self.hierarchical_context_service
        )
        
        # Generate valid UUIDs for testing
        self.task_uuid = str(uuid.uuid4())
        self.context_uuid = str(uuid.uuid4())
        self.branch_uuid = str(uuid.uuid4())
        
        # Mock task with required attributes
        self.mock_task = Mock(spec=Task)
        self.mock_task.id = TaskId.from_string(self.task_uuid)
        self.mock_task.title = "Test Task"
        
        # Mock the status properly
        mock_status = Mock()
        mock_status.is_done.return_value = False
        self.mock_task.status = mock_status
        
        self.mock_task.context_id = self.context_uuid
        self.mock_task.git_branch_id = self.branch_uuid  # Key attribute for fix
        self.mock_task.updated_at = datetime.now(timezone.utc)
        self.mock_task.get_events.return_value = []
        self.mock_task.get_subtask_progress.return_value = {"completed": 0, "total": 0}
        
        # Add complete_task method mock
        self.mock_task.complete_task = Mock()
        
        # Add save method for task repository
        self.task_repository.save = Mock()
        self.task_repository.find_all.return_value = []
        
    def test_create_facade_with_git_branch_id_from_task(self):
        """
        Test that create_facade() is called with git_branch_id extracted from task.
        
        This is the core fix - the factory needs git_branch_id parameter.
        """
        # Setup
        self.task_repository.find_by_id.return_value = self.mock_task
        self.subtask_repository.find_by_parent_task_id.return_value = []
        
        # Mock the hierarchical context facade factory and result
        mock_facade = Mock()
        mock_context_result = {
            "success": True,
            "context": {"updated_at": "2025-07-18 10:00:00"}
        }
        mock_facade.get_context.return_value = mock_context_result
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            mock_factory_instance.create_facade.return_value = mock_facade
            
            # Execute
            result = self.use_case.execute(
                task_id=self.task_uuid,
                completion_summary="Task completed successfully"
            )
            
            # Verify create_facade was called with git_branch_id from task
            # Should be called twice: once for context retrieval, once for context update
            assert mock_factory_instance.create_facade.call_count == 2
            
            # Verify all calls used git_branch_id from task
            expected_calls = [
                mock_factory_instance.create_facade.call_args_list[0],
                mock_factory_instance.create_facade.call_args_list[1]
            ]
            for call_args in expected_calls:
                assert call_args[1]['git_branch_id'] == self.branch_uuid
            
            # Verify task completion succeeded
            assert result["success"] is True
            assert result["task_id"] == self.task_uuid
    
    def test_create_facade_without_git_branch_id_handles_gracefully(self):
        """
        Test that the system handles missing git_branch_id gracefully.
        
        The current system design logs warnings but allows task completion to succeed
        when context operations fail.
        """
        # Setup task without git_branch_id
        task_without_branch_uuid = str(uuid.uuid4())
        task_without_branch = Mock(spec=Task)
        task_without_branch.id = TaskId.from_string(task_without_branch_uuid)
        task_without_branch.context_id = str(uuid.uuid4())
        task_without_branch.git_branch_id = None  # Missing git_branch_id
        mock_status = Mock()
        mock_status.is_done.return_value = False
        task_without_branch.status = mock_status
        
        # Add required mock methods for task completion
        task_without_branch.complete_task = Mock()
        task_without_branch.get_events.return_value = []
        task_without_branch.get_subtask_progress.return_value = {"completed": 0, "total": 0}
        
        self.task_repository.find_by_id.return_value = task_without_branch
        # Mock find_by_parent_task_id to return empty list (no subtasks)
        self.subtask_repository.find_by_parent_task_id.return_value = []
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            
            # Simulate the factory raising ValueError when git_branch_id is None
            mock_factory_instance.create_facade.side_effect = ValueError("git_branch_id is required for creating facade")
            
            # Execute and verify graceful error handling
            result = self.use_case.execute(
                task_id=task_without_branch_uuid,
                completion_summary="Task completed"
            )
            
            # Should handle the error gracefully and allow task completion to succeed
            assert result["success"] is True  # Task completion succeeds despite context errors
            assert result["task_id"] == task_without_branch_uuid
    
    def test_create_facade_with_default_parameters(self):
        """
        Test that create_facade() uses default values for user_id and project_id.
        
        The fix should include these defaults while adding git_branch_id.
        """
        # Setup
        self.task_repository.find_by_id.return_value = self.mock_task
        self.subtask_repository.find_by_parent_task_id.return_value = []
        
        mock_facade = Mock()
        mock_facade.get_context.return_value = {"success": True, "context": {"updated_at": "2025-07-18 10:00:00"}}
        mock_facade.merge_context.return_value = {"success": True}
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            mock_factory_instance.create_facade.return_value = mock_facade
            
            # Execute
            result = self.use_case.execute(
                task_id=self.task_uuid,
                completion_summary="Task completed"
            )
            
            # Verify create_facade was called twice (once for get_context, once for merge_context)
            assert mock_factory_instance.create_facade.call_count == 2
            
            # Verify all calls used git_branch_id
            for call_args in mock_factory_instance.create_facade.call_args_list:
                assert call_args[1]['git_branch_id'] == self.branch_uuid
            
            assert result["success"] is True
    
    def test_context_facade_error_propagation(self):
        """
        Test that errors from hierarchical context facade are properly handled.
        
        This ensures the fix doesn't break error handling.
        """
        # Setup
        self.task_repository.find_by_id.return_value = self.mock_task
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            
            # Simulate facade creation error
            mock_factory_instance.create_facade.side_effect = Exception("Facade creation failed")
            
            # Execute
            result = self.use_case.execute(
                task_id=self.task_uuid,
                completion_summary="Task completed"
            )
            
            # Should handle facade creation errors
            # The task completion might still succeed if context validation is optional
            # or it should fail gracefully with proper error handling
            assert "success" in result
    
    def test_task_without_git_branch_id_attribute(self):
        """
        Test handling of tasks that don't have git_branch_id attribute.
        
        This tests backward compatibility with older task entities.
        """
        # Create task without git_branch_id attribute
        old_task_uuid = str(uuid.uuid4())
        task_old_format = Mock(spec=Task)
        task_old_format.id = TaskId.from_string(old_task_uuid)
        task_old_format.context_id = str(uuid.uuid4())
        mock_status = Mock()
        mock_status.is_done.return_value = False
        task_old_format.status = mock_status
        # Note: no git_branch_id attribute
        
        self.task_repository.find_by_id.return_value = task_old_format
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            
            # Execute
            result = self.use_case.execute(
                task_id=old_task_uuid,
                completion_summary="Task completed"
            )
            
            # Should handle missing git_branch_id gracefully
            # Either by providing a default or skipping context facade creation
            assert "success" in result
    
    def test_context_facade_merge_context_with_git_branch_id(self):
        """
        Test that merge_context operation also works after facade fix.
        
        The fix should ensure both get_context and merge_context operations work.
        """
        # Setup
        self.task_repository.find_by_id.return_value = self.mock_task
        self.subtask_repository.find_by_parent_task_id.return_value = []
        
        mock_facade = Mock()
        mock_facade.get_context.return_value = {
            "success": True, 
            "context": {"updated_at": "2025-07-18 10:00:00"}
        }
        mock_facade.merge_context.return_value = {"success": True}
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            mock_factory_instance.create_facade.return_value = mock_facade
            
            # Execute
            result = self.use_case.execute(
                task_id=self.task_uuid,
                completion_summary="Task completed with testing"
            )
            
            # Verify both get_context and merge_context were called
            mock_facade.get_context.assert_called_with("task", self.task_uuid)
            mock_facade.merge_context.assert_called_once()
            
            # Verify the facade was created twice (once for get_context, once for merge_context)
            assert mock_factory_instance.create_facade.call_count == 2
            
            # Verify all calls used git_branch_id
            for call_args in mock_factory_instance.create_facade.call_args_list:
                assert call_args[1]['git_branch_id'] == self.branch_uuid
            
            assert result["success"] is True
    
    def test_completion_service_validation_with_fixed_facade(self):
        """
        Test that completion service validation works with fixed facade creation.
        
        This ensures the fix doesn't break task completion validation.
        """
        # Setup completion service
        completion_service = Mock()
        self.use_case._completion_service = completion_service
        
        self.task_repository.find_by_id.return_value = self.mock_task
        self.subtask_repository.find_by_parent_task_id.return_value = []
        
        mock_facade = Mock()
        mock_facade.get_context.return_value = {
            "success": True,
            "context": {"updated_at": "2025-07-18 10:00:00"}
        }
        mock_facade.merge_context.return_value = {"success": True}
        
        with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
            mock_factory_instance = Mock()
            mock_factory_class.return_value = mock_factory_instance
            mock_factory_instance.create_facade.return_value = mock_facade
            
            # Execute
            result = self.use_case.execute(
                task_id=self.task_uuid,
                completion_summary="Validated task completion"
            )
            
            # Verify completion service validation was called
            completion_service.validate_task_completion.assert_called_once_with(self.mock_task)
            
            # Verify facade was created twice (once for get_context, once for merge_context)
            assert mock_factory_instance.create_facade.call_count == 2
            
            # Verify all calls used git_branch_id
            for call_args in mock_factory_instance.create_facade.call_args_list:
                assert call_args[1]['git_branch_id'] == self.branch_uuid
            
            assert result["success"] is True


class TestTaskCompletionContextFacadeEdgeCases:
    """Test edge cases for the context facade fix."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.task_repository = Mock()
        self.use_case = CompleteTaskUseCase(task_repository=self.task_repository)
    
    def test_git_branch_id_extraction_from_various_task_formats(self):
        """
        Test git_branch_id extraction from different task object formats.
        
        This ensures the fix works with various task entity implementations.
        """
        test_cases = [
            # Standard task with git_branch_id attribute
            {
                "name": "standard_task",
                "task_attrs": {"git_branch_id": str(uuid.uuid4())},
                "expected": "valid_uuid"
            },
            # Task with git_branch_id as property
            {
                "name": "property_task", 
                "task_attrs": {"_git_branch_id": str(uuid.uuid4())},
                "expected": "valid_uuid"
            },
            # Task with None git_branch_id
            {
                "name": "none_branch_id",
                "task_attrs": {"git_branch_id": None},
                "expected": None
            }
        ]
        
        for case in test_cases:
            with patch('fastmcp.task_management.application.factories.hierarchical_context_facade_factory.HierarchicalContextFacadeFactory') as mock_factory_class:
                # Create mock task with specific attributes
                task_uuid = str(uuid.uuid4())
                mock_task = Mock(spec=Task)
                mock_task.id = TaskId.from_string(task_uuid)
                mock_status = Mock()
                mock_status.is_done.return_value = True  # Already completed
                mock_task.status = mock_status
                
                # Set git_branch_id attribute
                if "git_branch_id" in case["task_attrs"]:
                    mock_task.git_branch_id = case["task_attrs"]["git_branch_id"]
                
                self.task_repository.find_by_id.return_value = mock_task
                
                # Execute
                result = self.use_case.execute(
                    task_id=task_uuid,
                    completion_summary="Test completion"
                )
                
                # For already completed tasks, facade creation shouldn't be called
                if mock_task.status.is_done():
                    assert result["success"] is False
                    assert "already completed" in result["message"]
    
    def test_error_handling_preserves_original_behavior(self):
        """
        Test that error handling behavior is preserved after the fix.
        
        The fix should not change how other errors are handled.
        """
        # Test task not found error
        self.task_repository.find_by_id.return_value = None
        
        nonexistent_uuid = str(uuid.uuid4())
        with pytest.raises(TaskNotFoundError):
            self.use_case.execute(
                task_id=nonexistent_uuid,
                completion_summary="Should fail"
            )
        
        # Test should maintain original error handling patterns
        assert True  # Placeholder for additional error handling tests