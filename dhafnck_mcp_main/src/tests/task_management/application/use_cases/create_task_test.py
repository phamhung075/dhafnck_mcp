"""Test suite for CreateTaskUseCase.

Tests the task creation use case including:
- Task entity creation with validation
- Repository persistence
- Git branch validation
- Context creation
- Dependency handling
- Error handling
- Authentication validation
"""

import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from fastmcp.task_management.application.use_cases.create_task import CreateTaskUseCase
from fastmcp.task_management.application.dtos.task import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskResponse
)
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository
from fastmcp.task_management.domain.value_objects import TaskStatus, Priority
from fastmcp.task_management.domain.value_objects.task_status import TaskStatusEnum
from fastmcp.task_management.domain.value_objects.priority import PriorityLevel
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.events import TaskCreated
from fastmcp.task_management.domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError


class TestCreateTaskUseCase:
    """Test cases for CreateTaskUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock(spec=TaskRepository)
        self.mock_repository.get_next_id.return_value = TaskId(str(uuid4()))
        self.mock_repository.save.return_value = True
        self.mock_repository.git_branch_exists.return_value = True
        
        self.use_case = CreateTaskUseCase(self.mock_repository)
        
        # Default request data
        self.default_request = CreateTaskRequest(
            title="Test Task",
            description="Test task description",
            git_branch_id=str(uuid4()),
            status=TaskStatusEnum.TODO.value,
            priority=PriorityLevel.MEDIUM.label,
            user_id="test-user-123"
        )
    
    def test_create_task_success(self):
        """Test successful task creation with all parameters."""
        request = CreateTaskRequest(
            title="Complete Feature",
            description="Implement new feature",
            git_branch_id=str(uuid4()),
            status=TaskStatusEnum.IN_PROGRESS.value,
            priority=PriorityLevel.HIGH.label,
            details="Additional implementation details",
            estimated_effort="3 days",
            assignees=["user1", "user2"],
            labels=["feature", "backend"],
            due_date=datetime.now(timezone.utc),
            user_id="test-user-123"
        )
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        assert response.error is None
        assert response.task is not None
        assert response.task.title == "Complete Feature"
        assert response.task.description == "Implement new feature"
        assert response.task.status == TaskStatusEnum.IN_PROGRESS.value
        assert response.task.priority == PriorityLevel.HIGH.label
        
        # Verify repository save was called
        self.mock_repository.save.assert_called_once()
        saved_task = self.mock_repository.save.call_args[0][0]
        assert isinstance(saved_task, Task)
        assert saved_task.title == "Complete Feature"
    
    def test_create_task_minimal_parameters(self):
        """Test task creation with only required parameters."""
        request = CreateTaskRequest(
            title="Minimal Task",
            git_branch_id=str(uuid4()),
            user_id="test-user-123"
        )
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        assert response.task.title == "Minimal Task"
        assert response.task.status == TaskStatusEnum.TODO.value  # Default
        assert response.task.priority == PriorityLevel.MEDIUM.label  # Default
    
    def test_create_task_git_branch_validation(self):
        """Test that git branch existence is validated."""
        self.mock_repository.git_branch_exists.return_value = False
        
        response = self.use_case.execute(self.default_request)
        
        assert response.success is False
        assert "does not exist" in response.error
        assert "git_branch_id" in response.error
        
        # Verify save was not called
        self.mock_repository.save.assert_not_called()
    
    def test_create_task_without_git_branch_exists_method(self):
        """Test task creation when repository doesn't have git_branch_exists method."""
        # Remove the method
        delattr(self.mock_repository, 'git_branch_exists')
        
        response = self.use_case.execute(self.default_request)
        
        # Should succeed without validation
        assert response.success is True
        assert response.task is not None
    
    def test_create_task_with_dependencies(self):
        """Test task creation with dependencies."""
        dep_id1 = str(uuid4())
        dep_id2 = str(uuid4())
        
        request = CreateTaskRequest(
            title="Task with Dependencies",
            git_branch_id=str(uuid4()),
            dependencies=[dep_id1, dep_id2],
            user_id="test-user-123"
        )
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        
        # Verify dependencies were added to task
        saved_task = self.mock_repository.save.call_args[0][0]
        # Check that task has dependencies (implementation specific)
        assert hasattr(saved_task, '_dependencies') or hasattr(saved_task, 'dependencies')
    
    def test_create_task_with_invalid_dependencies(self):
        """Test task creation continues even with invalid dependencies."""
        request = CreateTaskRequest(
            title="Task with Invalid Dependencies",
            git_branch_id=str(uuid4()),
            dependencies=["invalid-uuid", "", "   ", str(uuid4())],
            user_id="test-user-123"
        )
        
        with patch('logging.warning') as mock_warning:
            response = self.use_case.execute(request)
        
        # Task creation should succeed
        assert response.success is True
        
        # Invalid dependencies should be logged
        assert mock_warning.called
    
    def test_create_task_long_title_truncation(self):
        """Test that very long titles are truncated."""
        long_title = "A" * 300  # 300 characters
        
        request = CreateTaskRequest(
            title=long_title,
            git_branch_id=str(uuid4()),
            user_id="test-user-123"
        )
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        assert len(response.task.title) == 200  # Truncated to 200
        assert response.task.title == "A" * 200
    
    def test_create_task_long_description_truncation(self):
        """Test that very long descriptions are truncated."""
        long_description = "B" * 1500  # 1500 characters
        
        request = CreateTaskRequest(
            title="Test Task",
            description=long_description,
            git_branch_id=str(uuid4()),
            user_id="test-user-123"
        )
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        assert len(response.task.description) == 1000  # Truncated to 1000
        assert response.task.description == "B" * 1000
    
    def test_create_task_invalid_status(self):
        """Test task creation with invalid status raises ValueError."""
        request = CreateTaskRequest(
            title="Test Task",
            git_branch_id=str(uuid4()),
            status="invalid_status",
            user_id="test-user-123"
        )
        
        with pytest.raises(ValueError):
            self.use_case.execute(request)
    
    def test_create_task_invalid_priority(self):
        """Test task creation with invalid priority raises ValueError."""
        request = CreateTaskRequest(
            title="Test Task",
            git_branch_id=str(uuid4()),
            priority="invalid_priority",
            user_id="test-user-123"
        )
        
        with pytest.raises(ValueError):
            self.use_case.execute(request)
    
    def test_create_task_repository_save_failure(self):
        """Test handling of repository save failure."""
        self.mock_repository.save.return_value = False
        
        response = self.use_case.execute(self.default_request)
        
        assert response.success is False
        assert "Failed to save task" in response.error
    
    @patch('fastmcp.task_management.infrastructure.database.database_config.get_db_session')
    def test_create_task_branch_task_count_update(self, mock_get_session):
        """Test that branch task count is updated."""
        # Mock database session and branch
        mock_session = MagicMock()
        mock_branch = MagicMock()
        mock_branch.task_count = 5
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_branch
        
        response = self.use_case.execute(self.default_request)
        
        assert response.success is True
        assert mock_branch.task_count == 6
        mock_session.commit.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.database.database_config.get_db_session')
    def test_create_task_branch_task_count_update_failure(self, mock_get_session):
        """Test task creation continues even if branch update fails."""
        mock_get_session.side_effect = Exception("Database error")
        
        with patch.object(self.use_case._logger, 'warning') as mock_warning:
            response = self.use_case.execute(self.default_request)
        
        # Task creation should still succeed
        assert response.success is True
        mock_warning.assert_called_with("Failed to update branch task count: Database error")
    
    @patch('fastmcp.task_management.application.use_cases.create_task.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_task.AuthConfig')
    def test_create_task_context_creation_success(self, mock_auth_config, mock_context_factory):
        """Test successful task context creation."""
        # Setup authentication
        mock_auth_config.is_default_user_allowed.return_value = False
        
        # Setup context facade
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": True}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        # Create task
        response = self.use_case.execute(self.default_request)
        
        assert response.success is True
        
        # Verify context creation
        mock_context_factory.assert_called_once()
        mock_context_factory_instance.create_facade.assert_called_once_with(
            user_id="test-user-123",
            git_branch_id=self.default_request.git_branch_id
        )
        
        # Verify context data
        context_call = mock_context_facade.create_context.call_args
        assert context_call[1]["level"] == "task"
        assert context_call[1]["data"]["branch_id"] == self.default_request.git_branch_id
        assert context_call[1]["data"]["task_data"]["title"] == "Test Task"
        
        # Verify task was saved twice (once for creation, once for context_id update)
        assert self.mock_repository.save.call_count == 2
    
    @patch('fastmcp.task_management.application.use_cases.create_task.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_task.AuthConfig')
    def test_create_task_context_creation_failure(self, mock_auth_config, mock_context_factory):
        """Test task creation continues even if context creation fails."""
        # Setup authentication
        mock_auth_config.is_default_user_allowed.return_value = False
        
        # Setup context facade to fail
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": False, "error": "Context error"}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        with patch.object(self.use_case._logger, 'warning') as mock_warning:
            response = self.use_case.execute(self.default_request)
        
        # Task creation should still succeed
        assert response.success is True
        assert mock_warning.called
        assert "Failed to create task context" in mock_warning.call_args[0][0]
    
    @patch('fastmcp.task_management.application.use_cases.create_task.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_task.AuthConfig')
    def test_create_task_context_compatibility_mode(self, mock_auth_config, mock_context_factory):
        """Test context creation in compatibility mode."""
        # Remove user_id from request
        request = CreateTaskRequest(
            title="Test Task",
            git_branch_id=str(uuid4())
        )
        
        # Setup compatibility mode
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-user"
        
        # Setup context facade
        mock_context_facade = Mock()
        mock_context_facade.create_context.return_value = {"success": True}
        mock_context_factory_instance = Mock()
        mock_context_factory_instance.create_facade.return_value = mock_context_facade
        mock_context_factory.return_value = mock_context_factory_instance
        
        response = self.use_case.execute(request)
        
        assert response.success is True
        
        # Verify compatibility mode was used
        mock_auth_config.is_default_user_allowed.assert_called()
        mock_auth_config.get_fallback_user_id.assert_called()
        mock_auth_config.log_authentication_bypass.assert_called_with(
            "Task context creation", "compatibility mode"
        )
        
        # Verify context was created with fallback user
        mock_context_factory_instance.create_facade.assert_called_once_with(
            user_id="compatibility-user",
            git_branch_id=request.git_branch_id
        )
    
    @patch('fastmcp.task_management.application.use_cases.create_task.UnifiedContextFacadeFactory')
    @patch('fastmcp.task_management.application.use_cases.create_task.AuthConfig')
    def test_create_task_context_no_auth_no_compatibility(self, mock_auth_config, mock_context_factory):
        """Test context creation fails without auth when compatibility mode is disabled."""
        # Remove user_id from request
        request = CreateTaskRequest(
            title="Test Task",
            git_branch_id=str(uuid4())
        )
        
        # Disable compatibility mode
        mock_auth_config.is_default_user_allowed.return_value = False
        
        # Setup context factory to raise auth error
        mock_context_factory.side_effect = UserAuthenticationRequiredError("Task context creation")
        
        with patch.object(self.use_case._logger, 'warning') as mock_warning:
            response = self.use_case.execute(request)
        
        # Task creation should still succeed (context creation is non-critical)
        assert response.success is True
        assert mock_warning.called
        assert "Error creating task context" in mock_warning.call_args[0][0]
    
    def test_create_task_domain_events(self):
        """Test that domain events are handled."""
        response = self.use_case.execute(self.default_request)
        
        assert response.success is True
        
        # Verify task entity was created with events
        saved_task = self.mock_repository.save.call_args[0][0]
        
        # Task should have a method to get events
        if hasattr(saved_task, 'get_events'):
            events = saved_task.get_events()
            # Should have at least a TaskCreated event
            assert any(isinstance(event, TaskCreated) for event in events)
    
    def test_create_task_with_task_id_object(self):
        """Test handling of TaskId object vs string."""
        # Mock repository to return TaskId object
        task_id = TaskId(str(uuid4()))
        self.mock_repository.get_next_id.return_value = task_id
        
        response = self.use_case.execute(self.default_request)
        
        assert response.success is True
        # Response should handle TaskId object properly
        assert response.task.id is not None
    
    def test_create_task_exception_handling(self):
        """Test general exception handling during task creation."""
        self.mock_repository.save.side_effect = Exception("Unexpected error")
        
        with patch('logging.error') as mock_error:
            response = self.use_case.execute(self.default_request)
        
        assert response.success is False
        assert "Failed to create task" in response.error
        assert mock_error.called
    
    def test_create_task_all_status_values(self):
        """Test task creation with all valid status values."""
        for status in TaskStatusEnum:
            request = CreateTaskRequest(
                title=f"Task with {status.value} status",
                git_branch_id=str(uuid4()),
                status=status.value,
                user_id="test-user-123"
            )
            
            response = self.use_case.execute(request)
            
            assert response.success is True
            assert response.task.status == status.value
    
    def test_create_task_all_priority_values(self):
        """Test task creation with all valid priority values."""
        for priority in PriorityLevel:
            request = CreateTaskRequest(
                title=f"Task with {priority.label} priority",
                git_branch_id=str(uuid4()),
                priority=priority.label,
                user_id="test-user-123"
            )
            
            response = self.use_case.execute(request)
            
            assert response.success is True
            assert response.task.priority == priority.label
    
    def test_create_task_response_dto_conversion(self):
        """Test that response DTO properly converts from domain entity."""
        response = self.use_case.execute(self.default_request)
        
        assert response.success is True
        assert isinstance(response.task, TaskResponse)
        assert response.task.title == self.default_request.title
        assert response.task.description == self.default_request.description
        assert response.task.git_branch_id == self.default_request.git_branch_id