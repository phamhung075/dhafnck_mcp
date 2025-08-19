"""
Tests for ORM Task Repository Implementation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.database.models import Task, TaskAssignee, TaskDependency, TaskLabel, Label
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.domain.exceptions.task_exceptions import (
    TaskCreationError,
    TaskNotFoundError,
    TaskUpdateError
)


class TestORMTaskRepository:
    """Test the ORMTaskRepository class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def git_branch_id(self):
        """Test git branch ID"""
        return "branch-123"
    
    @pytest.fixture
    def project_id(self):
        """Test project ID"""
        return "project-123"
    
    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "user-123"
    
    @pytest.fixture
    def repository(self, mock_session, git_branch_id, project_id, user_id):
        """Create a repository instance"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseORMRepository.__init__'):
            repo = ORMTaskRepository(mock_session, git_branch_id, project_id, user_id=user_id)
            repo.session = mock_session
            repo.get_db_session = Mock(return_value=mock_session)
            repo.transaction = Mock()
            repo.transaction.__enter__ = Mock(return_value=None)
            repo.transaction.__exit__ = Mock(return_value=None)
            return repo
    
    @pytest.fixture
    def mock_task_model(self):
        """Create a mock Task model"""
        task = Mock(spec=Task)
        task.id = "task-123"
        task.title = "Test Task"
        task.description = "Test task description"
        task.git_branch_id = "branch-123"
        task.status = "todo"
        task.priority = "high"
        task.details = "Additional details"
        task.estimated_effort = "2 hours"
        task.due_date = None
        task.context_id = "context-123"
        task.progress_percentage = 50
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        
        # Mock relationships
        task.assignees = []
        task.labels = []
        task.subtasks = []
        task.dependencies = []
        
        return task
    
    @pytest.fixture
    def mock_assignee(self):
        """Create a mock TaskAssignee"""
        assignee = Mock(spec=TaskAssignee)
        assignee.assignee_id = "user-456"
        assignee.role = "contributor"
        return assignee
    
    @pytest.fixture
    def mock_label(self):
        """Create a mock Label"""
        label = Mock(spec=Label)
        label.id = "label-123"
        label.name = "bug"
        label.color = "#ff0000"
        label.description = "Bug label"
        return label
    
    @pytest.fixture
    def mock_task_label(self, mock_label):
        """Create a mock TaskLabel"""
        task_label = Mock(spec=TaskLabel)
        task_label.label = mock_label
        return task_label
    
    def test_model_to_entity_conversion(self, repository, mock_task_model, mock_assignee, mock_task_label):
        """Test converting SQLAlchemy model to domain entity"""
        # Add relationships
        mock_task_model.assignees = [mock_assignee]
        mock_task_model.labels = [mock_task_label]
        
        # Add mock subtask
        mock_subtask = Mock()
        mock_subtask.id = "subtask-456"
        mock_task_model.subtasks = [mock_subtask]
        
        # Add mock dependency
        mock_dependency = Mock(spec=TaskDependency)
        mock_dependency.depends_on_task_id = "dep-789"
        mock_task_model.dependencies = [mock_dependency]
        
        entity = repository._model_to_entity(mock_task_model)
        
        assert isinstance(entity, TaskEntity)
        assert entity.id.value == mock_task_model.id
        assert entity.title == mock_task_model.title
        assert entity.description == mock_task_model.description
        assert entity.status == TaskStatus.TODO
        assert entity.priority == Priority.HIGH
        assert entity.overall_progress == 50
        assert "user-456" in entity.assignees
        assert "bug" in entity.labels
        assert "subtask-456" in entity.subtasks
        assert len(entity.dependencies) == 1
        assert entity.dependencies[0].value == "dep-789"
    
    def test_create_task_success(self, repository):
        """Test successful task creation"""
        title = "New Task"
        description = "Task description"
        priority = "high"
        assignee_ids = ["user-456", "user-789"]
        label_names = ["bug", "feature"]
        
        # Mock the create method
        mock_created_task = Mock()
        mock_created_task.id = "new-task-id"
        repository.create = Mock(return_value=mock_created_task)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        # Mock session for assignees and labels
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing labels
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Mock reloading the task
        mock_reloaded_task = Mock(spec=Task)
        mock_reloaded_task.id = "new-task-id"
        mock_reloaded_task.title = title
        mock_reloaded_task.description = description
        mock_reloaded_task.status = "todo"
        mock_reloaded_task.priority = priority
        mock_reloaded_task.assignees = []
        mock_reloaded_task.labels = []
        mock_reloaded_task.subtasks = []
        mock_reloaded_task.dependencies = []
        mock_reloaded_task.created_at = datetime.now()
        mock_reloaded_task.updated_at = datetime.now()
        
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_reloaded_task
        
        with patch('uuid.uuid4', return_value='generated-uuid'):
            result = repository.create_task(
                title=title,
                description=description,
                priority=priority,
                assignee_ids=assignee_ids,
                label_names=label_names
            )
        
        assert result.title == title
        assert result.description == description
        assert result.priority == Priority.HIGH
        repository.create.assert_called_once()
        repository.set_user_id.assert_called_once()
        
        # Verify assignees were added
        assert repository.session.add.call_count >= len(assignee_ids)
    
    def test_create_task_with_existing_label(self, repository):
        """Test creating task with existing label"""
        title = "New Task"
        description = "Task description"
        label_names = ["existing-label"]
        
        # Mock existing label
        mock_existing_label = Mock(spec=Label)
        mock_existing_label.id = "existing-label-id"
        mock_existing_label.name = "existing-label"
        
        mock_created_task = Mock()
        mock_created_task.id = "new-task-id"
        repository.create = Mock(return_value=mock_created_task)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        # Mock query to return existing label
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_existing_label
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Mock reloaded task
        mock_reloaded_task = Mock(spec=Task)
        mock_reloaded_task.id = "new-task-id"
        mock_reloaded_task.assignees = []
        mock_reloaded_task.labels = []
        mock_reloaded_task.subtasks = []
        mock_reloaded_task.dependencies = []
        mock_reloaded_task.created_at = datetime.now()
        mock_reloaded_task.updated_at = datetime.now()
        
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.side_effect = [mock_existing_label, mock_reloaded_task]
        
        result = repository.create_task(
            title=title,
            description=description,
            label_names=label_names
        )
        
        # Verify no new label was created (add called only for TaskLabel)
        add_calls = repository.session.add.call_args_list
        label_creates = [call for call in add_calls if isinstance(call[0][0], Label)]
        assert len(label_creates) == 0
    
    def test_create_task_error(self, repository):
        """Test task creation error handling"""
        repository.create = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(TaskCreationError) as exc_info:
            repository.create_task("Title", "Description")
        
        assert "Failed to create task" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
    
    def test_get_task_found(self, repository, mock_task_model):
        """Test getting existing task"""
        task_id = "task-123"
        
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_task_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = repository.get_task(task_id)
        
        assert result is not None
        assert result.id.value == task_id
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('read', 'task', task_id)
    
    def test_get_task_not_found(self, repository):
        """Test getting non-existent task"""
        task_id = "nonexistent"
        
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = repository.get_task(task_id)
        
        assert result is None
        repository.log_access.assert_called_once()
    
    def test_update_task_success(self, repository, mock_task_model):
        """Test successful task update"""
        task_id = "task-123"
        updates = {
            "title": "Updated Title",
            "status": "in_progress",
            "overall_progress": 75
        }
        
        # Mock the update method
        repository.update = Mock(return_value=mock_task_model)
        
        # Mock reloading the task
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_task_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = repository.update_task(task_id, **updates)
        
        # Verify progress_percentage was mapped correctly
        update_call_args = repository.update.call_args[1]
        assert "progress_percentage" in update_call_args
        assert update_call_args["progress_percentage"] == 75
        assert "overall_progress" not in update_call_args
    
    def test_update_task_with_assignees(self, repository, mock_task_model):
        """Test updating task with new assignees"""
        task_id = "task-123"
        updates = {
            "assignee_ids": ["user-111", "user-222"]
        }
        
        repository.update = Mock(return_value=mock_task_model)
        
        # Mock query for deleting existing assignees
        mock_query = Mock()
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Mock reloading
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_task_model
        
        result = repository.update_task(task_id, **updates)
        
        # Verify assignees were deleted and added
        mock_query.filter.return_value.delete.assert_called()
        assert repository.session.add.call_count == len(updates["assignee_ids"])
    
    def test_update_task_with_labels(self, repository, mock_task_model):
        """Test updating task with new labels"""
        task_id = "task-123"
        updates = {
            "label_names": ["urgent", "high-priority"]
        }
        
        repository.update = Mock(return_value=mock_task_model)
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing labels
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Mock reloading
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.side_effect = [None, None, mock_task_model]
        
        with patch('uuid.uuid4', side_effect=['label-id-1', 'label-id-2']):
            result = repository.update_task(task_id, **updates)
        
        # Verify labels were deleted and added
        mock_query.filter.return_value.delete.assert_called()
        # Should add 2 labels + 2 TaskLabel relationships
        assert repository.session.add.call_count == 4
    
    def test_update_task_not_found(self, repository):
        """Test updating non-existent task"""
        task_id = "nonexistent"
        repository.update = Mock(return_value=None)
        
        with pytest.raises(TaskNotFoundError) as exc_info:
            repository.update_task(task_id, title="New Title")
        
        assert f"Task {task_id} not found" in str(exc_info.value)
    
    def test_update_task_error(self, repository):
        """Test task update error handling"""
        task_id = "task-123"
        repository.update = Mock(side_effect=Exception("Update failed"))
        
        with pytest.raises(TaskUpdateError) as exc_info:
            repository.update_task(task_id, title="New Title")
        
        assert "Failed to update task" in str(exc_info.value)
        assert "Update failed" in str(exc_info.value)
    
    def test_delete_task(self, repository):
        """Test task deletion"""
        task_id = "task-123"
        
        # Mock the parent delete method
        with patch.object(repository, 'delete', return_value=True) as mock_delete:
            result = repository.delete_task(task_id)
        
        assert result is True
        mock_delete.assert_called_once_with(task_id)
    
    def test_initialization_with_user(self, mock_session, git_branch_id, project_id, user_id):
        """Test repository initialization with user ID"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseORMRepository.__init__'):
            repo = ORMTaskRepository(
                mock_session,
                git_branch_id=git_branch_id,
                project_id=project_id,
                user_id=user_id
            )
            
            assert repo.session == mock_session
            assert repo.git_branch_id == git_branch_id
            assert repo.project_id == project_id
            assert repo.user_id == user_id
            assert repo._is_system_mode is False
    
    def test_model_to_entity_with_no_relationships(self, repository):
        """Test model to entity conversion with no relationships"""
        task = Mock(spec=Task)
        task.id = "task-999"
        task.title = "Simple Task"
        task.description = "No relationships"
        task.git_branch_id = "branch-123"
        task.status = "done"
        task.priority = "low"
        task.details = ""
        task.estimated_effort = ""
        task.due_date = None
        task.context_id = None
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        task.assignees = []
        task.labels = []
        task.subtasks = []
        task.dependencies = []
        
        # Test without progress_percentage attribute
        if hasattr(task, 'progress_percentage'):
            delattr(task, 'progress_percentage')
        
        entity = repository._model_to_entity(task)
        
        assert entity.id.value == task.id
        assert entity.status == TaskStatus.DONE
        assert entity.priority == Priority.LOW
        assert len(entity.assignees) == 0
        assert len(entity.labels) == 0
        assert len(entity.subtasks) == 0
        assert len(entity.dependencies) == 0
        assert entity.overall_progress == 0  # Default value