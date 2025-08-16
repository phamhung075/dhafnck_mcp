"""Unit tests for Task Application Service"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Optional
import uuid

from fastmcp.task_management.application.services.task_application_service import (
    TaskApplicationService
)
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskId, TaskStatus, Priority


class TestTaskApplicationService:
    """Test suite for TaskApplicationService"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create mock task repository"""
        return Mock()
    
    @pytest.fixture
    def mock_context_service(self):
        """Create mock context service"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_task_repository, mock_context_service):
        """Create service instance with mocks"""
        with patch('fastmcp.task_management.application.services.task_application_service.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.services.task_application_service.TaskContextRepository'):
                with patch('fastmcp.task_management.application.services.task_application_service.get_db_config'):
                    return TaskApplicationService(
                        task_repository=mock_task_repository,
                        context_service=mock_context_service
                    )
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing"""
        task = Mock(spec=Task)
        task.id = TaskId.generate_new()
        task.title = "Test Task"
        task.description = "Test Description"
        task.status = TaskStatus.todo()
        task.priority = Priority.medium()
        task.git_branch_id = str(uuid.uuid4())
        task.assignees = []
        task.dependencies = []
        task.subtasks = []
        task.get_events = Mock(return_value=[])
        task.to_dict = Mock(return_value={
            'id': str(task.id),
            'title': task.title,
            'description': task.description,
            'status': str(task.status),
            'priority': str(task.priority)
        })
        return task
    
    def test_create_task_success(self, service, mock_task_repository, sample_task):
        """Test successful task creation"""
        # Arrange
        mock_task_repository.save.return_value = sample_task
        
        # Act
        result = service.create_task(
            title=sample_task.title,
            description=sample_task.description,
            git_branch_id=sample_task.git_branch_id
        )
        
        # Assert
        assert result is not None
        mock_task_repository.save.assert_called_once()
        assert result.title == sample_task.title
    
    def test_create_task_with_priority(self, service, mock_task_repository):
        """Test creating task with specific priority"""
        # Arrange
        task = Mock(spec=Task)
        task.priority = Priority.high()
        task.get_events = Mock(return_value=[])
        mock_task_repository.save.return_value = task
        
        # Act
        result = service.create_task(
            title="High Priority Task",
            description="Urgent task",
            git_branch_id=str(uuid.uuid4()),
            priority="high"
        )
        
        # Assert
        assert result is not None
        assert result.priority == Priority.high()
    
    def test_update_task_success(self, service, mock_task_repository, sample_task):
        """Test successful task update"""
        # Arrange
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        sample_task.update_title = Mock()
        
        # Act
        result = service.update_task(
            task_id=sample_task.id,
            title="Updated Title"
        )
        
        # Assert
        assert result is not None
        sample_task.update_title.assert_called_with("Updated Title")
        mock_task_repository.save.assert_called_once()
    
    def test_update_task_not_found(self, service, mock_task_repository):
        """Test updating non-existent task"""
        # Arrange
        task_id = TaskId.generate_new()
        mock_task_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task not found"):
            service.update_task(task_id=task_id, title="New Title")
    
    def test_complete_task_success(self, service, mock_task_repository, sample_task):
        """Test successful task completion"""
        # Arrange
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        sample_task.complete = Mock()
        sample_task.is_completed = False
        
        # Act
        result = service.complete_task(task_id=sample_task.id)
        
        # Assert
        assert result is not None
        sample_task.complete.assert_called_once()
        mock_task_repository.save.assert_called_once()
    
    def test_complete_already_completed_task(self, service, mock_task_repository, sample_task):
        """Test completing an already completed task"""
        # Arrange
        sample_task.is_completed = True
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Act
        result = service.complete_task(task_id=sample_task.id)
        
        # Assert
        assert result == sample_task
        mock_task_repository.save.assert_not_called()
    
    def test_add_dependency_success(self, service, mock_task_repository, mock_dependency_validator):
        """Test adding dependency to task"""
        # Arrange
        task = Mock(spec=Task)
        dependency = Mock(spec=Task)
        task.id = TaskId.generate_new()
        dependency.id = TaskId.generate_new()
        task.add_dependency = Mock()
        task.get_events = Mock(return_value=[])
        
        mock_task_repository.find_by_id.side_effect = [task, dependency]
        mock_task_repository.save.return_value = task
        mock_dependency_validator.validate_dependency_chain.return_value = {
            "valid": True,
            "issues": []
        }
        
        # Act
        result = service.add_dependency(
            task_id=task.id,
            dependency_id=dependency.id
        )
        
        # Assert
        assert result is not None
        task.add_dependency.assert_called_once_with(dependency.id)
        mock_dependency_validator.validate_dependency_chain.assert_called()
    
    def test_add_dependency_circular(self, service, mock_task_repository, mock_dependency_validator):
        """Test adding circular dependency"""
        # Arrange
        task_id = TaskId.generate_new()
        dependency_id = TaskId.generate_new()
        
        mock_dependency_validator.validate_dependency_chain.return_value = {
            "valid": False,
            "errors": ["Circular dependency detected"]
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid dependency"):
            service.add_dependency(task_id=task_id, dependency_id=dependency_id)
    
    def test_remove_dependency_success(self, service, mock_task_repository, sample_task):
        """Test removing dependency from task"""
        # Arrange
        dependency_id = TaskId.generate_new()
        sample_task.remove_dependency = Mock()
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        
        # Act
        result = service.remove_dependency(
            task_id=sample_task.id,
            dependency_id=dependency_id
        )
        
        # Assert
        assert result is not None
        sample_task.remove_dependency.assert_called_once_with(dependency_id)
        mock_task_repository.save.assert_called_once()
    
    def test_get_task_by_id(self, service, mock_task_repository, sample_task):
        """Test retrieving task by ID"""
        # Arrange
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Act
        result = service.get_task(task_id=sample_task.id)
        
        # Assert
        assert result == sample_task
        mock_task_repository.find_by_id.assert_called_once_with(sample_task.id)
    
    def test_get_task_not_found(self, service, mock_task_repository):
        """Test retrieving non-existent task"""
        # Arrange
        task_id = TaskId.generate_new()
        mock_task_repository.find_by_id.return_value = None
        
        # Act
        result = service.get_task(task_id=task_id)
        
        # Assert
        assert result is None
    
    def test_list_tasks_by_branch(self, service, mock_task_repository):
        """Test listing tasks by git branch"""
        # Arrange
        branch_id = str(uuid.uuid4())
        tasks = [Mock(spec=Task) for _ in range(3)]
        mock_task_repository.find_by_git_branch.return_value = tasks
        
        # Act
        result = service.list_tasks_by_branch(git_branch_id=branch_id)
        
        # Assert
        assert len(result) == 3
        mock_task_repository.find_by_git_branch.assert_called_once_with(branch_id)
    
    def test_list_tasks_with_filters(self, service, mock_task_repository):
        """Test listing tasks with status and priority filters"""
        # Arrange
        tasks = [Mock(spec=Task) for _ in range(2)]
        mock_task_repository.find_by_filters.return_value = tasks
        
        # Act
        result = service.list_tasks(
            status="in_progress",
            priority="high"
        )
        
        # Assert
        assert len(result) == 2
        mock_task_repository.find_by_filters.assert_called_once()
    
    def test_assign_task_to_user(self, service, mock_task_repository, sample_task):
        """Test assigning task to user"""
        # Arrange
        user_id = "user123"
        sample_task.assign_to = Mock()
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        
        # Act
        result = service.assign_task(
            task_id=sample_task.id,
            assignee=user_id
        )
        
        # Assert
        assert result is not None
        sample_task.assign_to.assert_called_once_with(user_id)
        mock_task_repository.save.assert_called_once()
    
    def test_unassign_task_from_user(self, service, mock_task_repository, sample_task):
        """Test unassigning task from user"""
        # Arrange
        user_id = "user123"
        sample_task.unassign_from = Mock()
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        
        # Act
        result = service.unassign_task(
            task_id=sample_task.id,
            assignee=user_id
        )
        
        # Assert
        assert result is not None
        sample_task.unassign_from.assert_called_once_with(user_id)
        mock_task_repository.save.assert_called_once()
    
    def test_update_task_status(self, service, mock_task_repository, sample_task):
        """Test updating task status"""
        # Arrange
        new_status = TaskStatus.in_progress()
        sample_task.update_status = Mock()
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        
        # Act
        result = service.update_task_status(
            task_id=sample_task.id,
            status="in_progress"
        )
        
        # Assert
        assert result is not None
        sample_task.update_status.assert_called_once()
        mock_task_repository.save.assert_called_once()
    
    def test_bulk_update_tasks(self, service, mock_task_repository):
        """Test bulk updating multiple tasks"""
        # Arrange
        task_ids = [TaskId.generate_new() for _ in range(3)]
        tasks = []
        for task_id in task_ids:
            task = Mock(spec=Task)
            task.id = task_id
            task.update_status = Mock()
            task.get_events = Mock(return_value=[])
            tasks.append(task)
        
        mock_task_repository.find_by_ids.return_value = tasks
        mock_task_repository.save_batch.return_value = tasks
        
        # Act
        result = service.bulk_update_status(
            task_ids=task_ids,
            status="done"
        )
        
        # Assert
        assert len(result) == 3
        for task in tasks:
            task.update_status.assert_called_once()
        mock_task_repository.save_batch.assert_called_once()
    
    def test_delete_task_success(self, service, mock_task_repository, sample_task):
        """Test deleting a task"""
        # Arrange
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.delete.return_value = True
        
        # Act
        result = service.delete_task(task_id=sample_task.id)
        
        # Assert
        assert result is True
        mock_task_repository.delete.assert_called_once_with(sample_task.id)
    
    def test_delete_task_with_dependencies(self, service, mock_task_repository, sample_task):
        """Test deleting task that has dependencies"""
        # Arrange
        sample_task.dependencies = [TaskId.generate_new()]
        mock_task_repository.find_by_id.return_value = sample_task
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete task with dependencies"):
            service.delete_task(task_id=sample_task.id)
    
    def test_event_publishing(self, service, mock_task_repository, mock_event_publisher, sample_task):
        """Test that events are published after operations"""
        # Arrange
        event = Mock()
        sample_task.get_events.return_value = [event]
        mock_task_repository.find_by_id.return_value = sample_task
        mock_task_repository.save.return_value = sample_task
        
        # Act
        service.update_task(task_id=sample_task.id, title="New Title")
        
        # Assert
        mock_event_publisher.publish.assert_called_once_with(event)
    
    def test_search_tasks(self, service, mock_task_repository):
        """Test searching tasks by query"""
        # Arrange
        query = "authentication"
        tasks = [Mock(spec=Task) for _ in range(2)]
        mock_task_repository.search.return_value = tasks
        
        # Act
        result = service.search_tasks(query=query)
        
        # Assert
        assert len(result) == 2
        mock_task_repository.search.assert_called_once_with(query)