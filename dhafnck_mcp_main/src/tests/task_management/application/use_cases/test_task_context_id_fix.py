"""
Test that verifies tasks have context_id properly set after creation.
This addresses Issue #2 where tasks were created without context_id being populated.
"""

import unittest
import uuid
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.create_task import CreateTaskUseCase
from fastmcp.task_management.application.dtos.task import CreateTaskRequest
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskContextIdFix(unittest.TestCase):
    """Test that context_id is properly set on tasks after creation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = Mock()
        self.use_case = CreateTaskUseCase(self.mock_repository)
        
        # Use proper UUID format
        self.task_id_str = str(uuid.uuid4())
        
        # Mock repository methods
        self.mock_repository.get_next_id.return_value = TaskId(self.task_id_str)
        self.mock_repository.git_branch_exists.return_value = True
        
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    def test_task_creation_sets_context_id_on_success(self, mock_factory_class):
        """Test that context_id is set on task entity when context creation succeeds"""
        
        # Arrange
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        mock_context_facade = Mock()
        mock_factory.create_facade.return_value = mock_context_facade
        
        # Mock successful context creation
        mock_context_facade.create_context.return_value = {
            "success": True,
            "data": {"id": self.task_id_str}
        }
        
        # Track saved tasks
        saved_tasks = []
        def save_task(task):
            saved_tasks.append(task)
            return True
        self.mock_repository.save.side_effect = save_task
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123",
            priority="high"
        )
        
        # Act
        response = self.use_case.execute(request)
        
        # Assert
        self.assertTrue(response.success)
        self.assertIsNotNone(response.task)
        
        # Check that save was called twice: once for initial save, once after context creation
        self.assertEqual(self.mock_repository.save.call_count, 2)
        
        # Get the second saved task (after context creation)
        if len(saved_tasks) >= 2:
            task_with_context = saved_tasks[1]
            # Verify context_id was set
            self.assertEqual(task_with_context.context_id, self.task_id_str)
        
        # Verify context creation was called with correct parameters
        mock_context_facade.create_context.assert_called_once_with(
            level="task",
            context_id=self.task_id_str,
            data={
                "branch_id": "branch-123",
                "task_data": {
                    "title": "Test Task",
                    "status": str(TaskStatus.todo()),
                    "description": "Test Description",
                    "priority": str(Priority("high"))
                }
            }
        )
    
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    def test_task_creation_continues_when_context_fails(self, mock_factory_class):
        """Test that task creation succeeds even if context creation fails"""
        
        # Arrange
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        mock_context_facade = Mock()
        mock_factory.create_facade.return_value = mock_context_facade
        
        # Mock failed context creation
        mock_context_facade.create_context.return_value = {
            "success": False,
            "error": "Context creation failed"
        }
        
        # Track saved tasks
        saved_tasks = []
        def save_task(task):
            saved_tasks.append(task)
            return True
        self.mock_repository.save.side_effect = save_task
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        # Act
        response = self.use_case.execute(request)
        
        # Assert
        self.assertTrue(response.success)
        self.assertIsNotNone(response.task)
        
        # Check that save was called only once (no second save after failed context)
        self.assertEqual(self.mock_repository.save.call_count, 1)
        
        # Get the saved task
        saved_task = saved_tasks[0]
        # Verify context_id was NOT set (remains None)
        self.assertIsNone(saved_task.context_id)
    
    @patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory')
    def test_task_creation_handles_context_exception_gracefully(self, mock_factory_class):
        """Test that task creation succeeds even if context creation throws exception"""
        
        # Arrange
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        
        mock_context_facade = Mock()
        mock_factory.create_facade.return_value = mock_context_facade
        
        # Mock context creation throwing exception
        mock_context_facade.create_context.side_effect = Exception("Unexpected error")
        
        self.mock_repository.save.return_value = True
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        # Act
        response = self.use_case.execute(request)
        
        # Assert
        self.assertTrue(response.success)
        self.assertIsNotNone(response.task)
        
        # Check that save was called only once (no second save after exception)
        self.assertEqual(self.mock_repository.save.call_count, 1)
    
    def test_task_entity_has_context_id_methods(self):
        """Test that Task entity has the required context_id methods"""
        
        # Create a task with proper UUID
        task_id = str(uuid.uuid4())
        task = Task(
            id=TaskId(task_id),
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        # Verify context_id starts as None
        self.assertIsNone(task.context_id)
        self.assertFalse(task.has_updated_context())
        
        # Test set_context_id method
        task.set_context_id("context-456")
        self.assertEqual(task.context_id, "context-456")
        self.assertTrue(task.has_updated_context())
        
        # Test clear_context_id method
        task.clear_context_id()
        self.assertIsNone(task.context_id)
        self.assertFalse(task.has_updated_context())


if __name__ == '__main__':
    unittest.main()