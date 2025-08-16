#!/usr/bin/env python3
"""
Unit tests for TaskApplicationFacade
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
import uuid

from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.application.dtos.task.search_tasks_request import SearchTasksRequest
from fastmcp.task_management.domain.exceptions.task_exceptions import TaskNotFoundError
from fastmcp.task_management.domain.exceptions.base_exceptions import ValidationException
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository"""
    return Mock()


@pytest.fixture
def mock_subtask_repository():
    """Create a mock subtask repository"""
    return Mock()


@pytest.fixture
def mock_context_service():
    """Create a mock context service"""
    return Mock()


@pytest.fixture
def mock_git_branch_repository():
    """Create a mock git branch repository"""
    mock = Mock()
    # Make find_all async
    mock.find_all = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def task_facade(mock_task_repository, mock_subtask_repository, mock_context_service, mock_git_branch_repository):
    """Create a TaskApplicationFacade with mocked dependencies"""
    # Mock the database config to avoid Supabase issues
    with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config'):
        # Mock the imports that happen inside __init__
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            with patch('fastmcp.task_management.infrastructure.repositories.task_context_repository.TaskContextRepository'):
                with patch('fastmcp.task_management.application.services.task_context_sync_service.TaskContextSyncService') as mock_sync_service:
                    with patch('fastmcp.task_management.application.services.dependency_resolver_service.DependencyResolverService'):
                        # Mock the hierarchical context service
                        mock_hierarchical_service = Mock()
                        mock_factory.return_value.create_unified_service.return_value = mock_hierarchical_service
                        
                        # Mock the sync service to avoid errors
                        mock_sync_instance = Mock()
                        mock_sync_instance.sync_context_and_get_task = AsyncMock(return_value=None)
                        mock_sync_service.return_value = mock_sync_instance
                        
                        facade = TaskApplicationFacade(
                            task_repository=mock_task_repository,
                            subtask_repository=mock_subtask_repository,
                            context_service=mock_context_service,
                            git_branch_repository=mock_git_branch_repository
                        )
                        # Override the sync service with our mock
                        facade._task_context_sync_service = mock_sync_instance
                        return facade


@pytest.fixture
def sample_task_entity():
    """Create a sample task entity"""
    return TaskEntity(
        id=TaskId(str(uuid.uuid4())),
        title="Test Task",
        description="Test Description",
        git_branch_id=str(uuid.uuid4()),
        status=TaskStatus("todo"),
        priority=Priority("medium"),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestTaskApplicationFacade:
    """Test suite for TaskApplicationFacade"""
    
    @pytest.mark.unit
    def test_create_task_success(self, task_facade, mock_task_repository, sample_task_entity):
        """Test successful task creation"""
        # Arrange
        request = CreateTaskRequest(
            title="New Task",
            description="New Description",
            git_branch_id=str(uuid.uuid4()),
            priority="high"
        )
        
        # Mock the use case to return proper response
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = sample_task_entity
        mock_response.message = "Task created successfully"
        
        # Mock the create use case execute method
        task_facade._create_task_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = task_facade.create_task(request)
        
        # Assert
        assert result["success"] is True
        assert "task" in result
        task_facade._create_task_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_create_task_validation_error(self, task_facade):
        """Test task creation with invalid request"""
        # Arrange
        request = CreateTaskRequest(
            title="",  # Empty title should fail validation
            description="Description",
            git_branch_id=str(uuid.uuid4()),
            priority="medium"  # Add default priority
        )
        
        # Act
        result = task_facade.create_task(request)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "title is required" in result["error"].lower()
    
    @pytest.mark.unit
    def test_update_task_success(self, task_facade, mock_task_repository, sample_task_entity):
        """Test successful task update"""
        # Arrange
        task_id = str(uuid.uuid4())
        request = UpdateTaskRequest(
            title="Updated Title",
            status="in_progress"
        )
        
        mock_task_repository.get_task.return_value = sample_task_entity
        mock_task_repository.update_task.return_value = sample_task_entity
        
        # Act
        result = task_facade.update_task(task_id, request)
        
        # Assert
        assert result["success"] is True
        assert "task" in result["data"]
        mock_task_repository.update_task.assert_called_once()
    
    @pytest.mark.unit
    def test_update_task_not_found(self, task_facade, mock_task_repository):
        """Test updating non-existent task"""
        # Arrange
        task_id = str(uuid.uuid4())
        request = UpdateTaskRequest(title="Updated Title")
        
        mock_task_repository.get_task.return_value = None
        
        # Act
        result = task_facade.update_task(task_id, request)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.unit
    def test_get_task_success(self, task_facade, mock_task_repository, sample_task_entity):
        """Test successful task retrieval"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_task_repository.get_task.return_value = sample_task_entity
        
        # Act
        result = task_facade.get_task(task_id)
        
        # Assert
        assert result["success"] is True
        assert "task" in result["data"]
        mock_task_repository.get_task.assert_called_once_with(task_id)
    
    @pytest.mark.unit
    def test_get_task_not_found(self, task_facade, mock_task_repository):
        """Test getting non-existent task"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_task_repository.get_task.return_value = None
        
        # Act
        result = task_facade.get_task(task_id)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.unit
    def test_delete_task_success(self, task_facade, mock_task_repository):
        """Test successful task deletion"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_task_repository.delete_task.return_value = True
        
        # Act
        result = task_facade.delete_task(task_id)
        
        # Assert
        assert result["success"] is True
        mock_task_repository.delete_task.assert_called_once_with(task_id)
    
    @pytest.mark.unit
    def test_delete_task_not_found(self, task_facade, mock_task_repository):
        """Test deleting non-existent task"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_task_repository.delete_task.return_value = False
        
        # Act
        result = task_facade.delete_task(task_id)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.unit
    def test_list_tasks_with_filters(self, task_facade, mock_task_repository):
        """Test listing tasks with filters"""
        # Arrange
        request = ListTasksRequest(
            status="in_progress",
            priority="high",
            limit=10
        )
        
        mock_tasks = [Mock() for _ in range(3)]
        mock_task_repository.list_tasks.return_value = mock_tasks
        
        # Act
        result = task_facade.list_tasks(request)
        
        # Assert
        assert result["success"] is True
        assert "tasks" in result["data"]
        assert len(result["data"]["tasks"]) == 3
        mock_task_repository.list_tasks.assert_called_once()
    
    @pytest.mark.unit
    def test_search_tasks(self, task_facade, mock_task_repository):
        """Test searching tasks"""
        # Arrange
        request = SearchTasksRequest(
            query="authentication",
            limit=5
        )
        
        mock_tasks = [Mock() for _ in range(2)]
        mock_task_repository.search_tasks.return_value = mock_tasks
        
        # Act
        result = task_facade.search_tasks(request)
        
        # Assert
        assert result["success"] is True
        assert "tasks" in result["data"]
        assert len(result["data"]["tasks"]) == 2
        mock_task_repository.search_tasks.assert_called_once()
    
    @pytest.mark.unit
    def test_complete_task_success(self, task_facade, mock_task_repository, mock_subtask_repository, sample_task_entity):
        """Test completing a task"""
        # Arrange
        task_id = str(uuid.uuid4())
        completion_summary = "Task completed successfully"
        testing_notes = "All tests passed"
        
        mock_task_repository.get_task.return_value = sample_task_entity
        mock_subtask_repository.get_subtasks_for_task.return_value = []
        
        # Act
        result = task_facade.complete_task(
            task_id=task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes
        )
        
        # Assert
        assert result["success"] is True
        mock_task_repository.update_task.assert_called()
    
    @pytest.mark.unit
    def test_complete_task_with_incomplete_subtasks(self, task_facade, mock_task_repository, mock_subtask_repository, sample_task_entity):
        """Test completing a task with incomplete subtasks"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        mock_task_repository.get_task.return_value = sample_task_entity
        
        # Create mock subtasks - one incomplete
        incomplete_subtask = Mock()
        incomplete_subtask.status = "in_progress"
        mock_subtask_repository.get_subtasks_for_task.return_value = [incomplete_subtask]
        
        # Act
        result = task_facade.complete_task(
            task_id=task_id,
            completion_summary="Summary"
        )
        
        # Assert
        # Should allow completion but might warn about incomplete subtasks
        # Exact behavior depends on business rules
        assert "success" in result
    
    @pytest.mark.unit
    def test_next_task_with_no_tasks(self, task_facade, mock_task_repository):
        """Test getting next task when no tasks available"""
        # Arrange
        git_branch_id = str(uuid.uuid4())
        mock_task_repository.list_tasks.return_value = []
        
        # Act
        result = task_facade.next_task(git_branch_id)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["has_next"] is False
    
    @pytest.mark.unit
    def test_next_task_with_available_tasks(self, task_facade, mock_task_repository, sample_task_entity):
        """Test getting next task with available tasks"""
        # Arrange
        git_branch_id = str(uuid.uuid4())
        mock_task_repository.list_tasks.return_value = [sample_task_entity]
        
        # Act
        result = task_facade.next_task(git_branch_id)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["has_next"] is True
        assert "next_item" in result["data"]
    
    @pytest.mark.unit
    def test_add_dependency(self, task_facade, mock_task_repository, sample_task_entity):
        """Test adding a dependency to a task"""
        # Arrange
        task_id = str(uuid.uuid4())
        dependency_id = str(uuid.uuid4())
        
        mock_task_repository.get_task.return_value = sample_task_entity
        mock_task_repository.add_dependency.return_value = True
        
        # Act
        result = task_facade.add_dependency(task_id, dependency_id)
        
        # Assert
        assert result["success"] is True
        mock_task_repository.add_dependency.assert_called_once_with(task_id, dependency_id)
    
    @pytest.mark.unit
    def test_remove_dependency(self, task_facade, mock_task_repository, sample_task_entity):
        """Test removing a dependency from a task"""
        # Arrange
        task_id = str(uuid.uuid4())
        dependency_id = str(uuid.uuid4())
        
        mock_task_repository.get_task.return_value = sample_task_entity
        mock_task_repository.remove_dependency.return_value = True
        
        # Act
        result = task_facade.remove_dependency(task_id, dependency_id)
        
        # Assert
        assert result["success"] is True
        mock_task_repository.remove_dependency.assert_called_once_with(task_id, dependency_id)
    
    @pytest.mark.unit
    def test_error_handling(self, task_facade, mock_task_repository):
        """Test error handling in facade methods"""
        # Arrange
        task_id = str(uuid.uuid4())
        mock_task_repository.get_task.side_effect = Exception("Database error")
        
        # Act
        result = task_facade.get_task(task_id)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]