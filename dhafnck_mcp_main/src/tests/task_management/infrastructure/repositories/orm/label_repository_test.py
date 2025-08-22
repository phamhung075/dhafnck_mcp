"""
Test cases for ORM Label Repository Implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.label_repository import ORMLabelRepository
from fastmcp.task_management.infrastructure.database.models import Label, TaskLabel, Task
from fastmcp.task_management.infrastructure.database.database_adapter import DatabaseAdapter
from fastmcp.task_management.domain.entities.label import Label as LabelEntity
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.exceptions.base_exceptions import (
    RepositoryError, NotFoundError, ValidationError
)


class TestORMLabelRepository:
    """Test cases for ORMLabelRepository class."""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """Create mock database adapter."""
        adapter = Mock(spec=DatabaseAdapter)
        return adapter
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock(spec=Session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        return session
    
    @pytest.fixture
    def label_repository(self, mock_db_adapter, mock_session):
        """Create label repository with mocked dependencies."""
        mock_db_adapter.get_session.return_value = mock_session
        return ORMLabelRepository(mock_db_adapter)
    
    @pytest.fixture
    def mock_label(self):
        """Create mock label model."""
        label = Mock(spec=Label)
        label.id = 1
        label.name = "bug"
        label.color = "#ff0000"
        label.description = "Bug reports"
        label.created_at = datetime.now()
        return label
    
    @pytest.fixture
    def mock_task(self):
        """Create mock task model."""
        task = Mock(spec=Task)
        task.id = "task-123"
        task.title = "Test Task"
        task.description = "Test description"
        task.git_branch_id = "branch-456"
        task.status = "todo"
        task.priority = "medium"
        task.details = {}
        task.estimated_effort = None
        task.due_date = None
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        task.context_id = None
        return task
    
    def test_create_label_success(self, label_repository, mock_session, mock_label):
        """Test successful label creation."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock(side_effect=lambda l: setattr(l, 'id', 1))
        
        result = label_repository.create_label(
            name="bug",
            color="#ff0000",
            description="Bug reports"
        )
        
        assert isinstance(result, LabelEntity)
        assert result.name == "bug"
        assert result.color == "#ff0000"
        assert result.description == "Bug reports"
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    def test_create_label_default_color(self, label_repository, mock_session):
        """Test label creation with default color."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock(side_effect=lambda l: setattr(l, 'id', 1))
        
        result = label_repository.create_label(name="feature")
        
        assert result.color == "#0066cc"  # Default color
        assert result.description == ""  # Default empty description
    
    def test_create_label_duplicate_name(self, label_repository, mock_session, mock_label):
        """Test label creation with duplicate name."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        with pytest.raises(ValidationError, match="Label with name 'bug' already exists"):
            label_repository.create_label(name="bug")
        
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_create_label_database_error(self, label_repository, mock_session):
        """Test label creation with database error."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.commit.side_effect = Exception("Database error")
        
        with pytest.raises(RepositoryError, match="Failed to create label"):
            label_repository.create_label(name="test")
    
    def test_get_label_success(self, label_repository, mock_session, mock_label):
        """Test successful label retrieval by ID."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_repository.get_label(1)
        
        assert result is not None
        assert isinstance(result, LabelEntity)
        assert result.id == 1
        assert result.name == "bug"
        
        mock_session.query.assert_called_with(Label)
    
    def test_get_label_not_found(self, label_repository, mock_session):
        """Test label retrieval when not found."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_repository.get_label(999)
        
        assert result is None
    
    def test_get_label_database_error(self, label_repository, mock_session):
        """Test label retrieval with database error."""
        mock_session.query.side_effect = Exception("Database error")
        
        with pytest.raises(RepositoryError, match="Failed to get label"):
            label_repository.get_label(1)
    
    def test_get_label_by_name_success(self, label_repository, mock_session, mock_label):
        """Test successful label retrieval by name."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        
        result = label_repository.get_label_by_name("bug")
        
        assert result is not None
        assert result.name == "bug"
    
    def test_get_label_by_name_not_found(self, label_repository, mock_session):
        """Test label by name when not found."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_repository.get_label_by_name("nonexistent")
        
        assert result is None
    
    def test_update_label_success(self, label_repository, mock_session, mock_label):
        """Test successful label update."""
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_label,  # First query for label to update
            None  # Second query to check name uniqueness
        ]
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        result = label_repository.update_label(
            label_id=1,
            name="critical-bug",
            color="#ff00ff",
            description="Critical bugs"
        )
        
        assert mock_label.name == "critical-bug"
        assert mock_label.color == "#ff00ff"
        assert mock_label.description == "Critical bugs"
        
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    def test_update_label_partial_update(self, label_repository, mock_session, mock_label):
        """Test partial label update."""
        original_name = mock_label.name
        original_description = mock_label.description
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        result = label_repository.update_label(label_id=1, color="#00ff00")
        
        assert mock_label.name == original_name
        assert mock_label.color == "#00ff00"
        assert mock_label.description == original_description
    
    def test_update_label_not_found(self, label_repository, mock_session):
        """Test updating non-existent label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError, match="Label"):
            label_repository.update_label(label_id=999, name="new-name")
    
    def test_update_label_duplicate_name(self, label_repository, mock_session, mock_label):
        """Test updating label with duplicate name."""
        existing_label = Mock(spec=Label)
        existing_label.name = "existing"
        
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_label,  # Label to update
            existing_label  # Existing label with new name
        ]
        
        with pytest.raises(ValidationError, match="Label with name 'existing' already exists"):
            label_repository.update_label(label_id=1, name="existing")
    
    def test_delete_label_success(self, label_repository, mock_session, mock_label):
        """Test successful label deletion."""
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = label_repository.delete_label(1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_label)
        mock_session.commit.assert_called_once()
    
    def test_delete_label_not_found(self, label_repository, mock_session):
        """Test deleting non-existent label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_repository.delete_label(999)
        
        assert result is False
        mock_session.delete.assert_not_called()
    
    def test_list_labels_success(self, label_repository, mock_session):
        """Test successful label listing."""
        mock_labels = [
            Mock(id=1, name="bug", color="#ff0000", description="Bugs", created_at=datetime.now()),
            Mock(id=2, name="feature", color="#00ff00", description="Features", created_at=datetime.now())
        ]
        
        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_labels
        
        result = label_repository.list_labels(limit=10, offset=0)
        
        assert len(result) == 2
        assert all(isinstance(label, LabelEntity) for label in result)
        assert result[0].name == "bug"
        assert result[1].name == "feature"
    
    def test_list_labels_with_pagination(self, label_repository, mock_session):
        """Test label listing with pagination."""
        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = label_repository.list_labels(limit=5, offset=10)
        
        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(5)
    
    def test_assign_label_to_task_success(self, label_repository, mock_session, mock_label, mock_task):
        """Test successful label assignment to task."""
        # Fix the user_id issue by mocking it
        label_repository.user_id = "test-user-123"
        
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task,  # Task exists
            mock_label,  # Label exists
            None  # Not already assigned
        ]
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        result = label_repository.assign_label_to_task("task-123", 1)
        
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Check TaskLabel creation
        task_label = mock_session.add.call_args[0][0]
        assert task_label.task_id == "task-123"
        assert task_label.label_id == 1
        assert task_label.user_id == "test-user-123"
    
    def test_assign_label_to_task_already_assigned(self, label_repository, mock_session, mock_label, mock_task):
        """Test assigning already assigned label."""
        mock_task_label = Mock(spec=TaskLabel)
        
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task,  # Task exists
            mock_label,  # Label exists
            mock_task_label  # Already assigned
        ]
        
        result = label_repository.assign_label_to_task("task-123", 1)
        
        assert result is False
        mock_session.add.assert_not_called()
    
    def test_assign_label_to_task_task_not_found(self, label_repository, mock_session):
        """Test assigning label to non-existent task."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError, match="Task"):
            label_repository.assign_label_to_task("nonexistent", 1)
    
    def test_assign_label_to_task_label_not_found(self, label_repository, mock_session, mock_task):
        """Test assigning non-existent label to task."""
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_task,  # Task exists
            None  # Label doesn't exist
        ]
        
        with pytest.raises(NotFoundError, match="Label"):
            label_repository.assign_label_to_task("task-123", 999)
    
    def test_remove_label_from_task_success(self, label_repository, mock_session):
        """Test successful label removal from task."""
        mock_task_label = Mock(spec=TaskLabel)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_task_label
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        
        result = label_repository.remove_label_from_task("task-123", 1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_task_label)
        mock_session.commit.assert_called_once()
    
    def test_remove_label_from_task_not_assigned(self, label_repository, mock_session):
        """Test removing non-assigned label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = label_repository.remove_label_from_task("task-123", 1)
        
        assert result is False
        mock_session.delete.assert_not_called()
    
    def test_get_tasks_by_label_success(self, label_repository, mock_session, mock_label):
        """Test getting tasks by label."""
        mock_tasks = [
            Mock(id="task-1", title="Task 1", description="", git_branch_id="branch-1",
                 status="todo", priority="high", details={}, estimated_effort=None,
                 due_date=None, created_at=datetime.now(), updated_at=datetime.now(), context_id=None),
            Mock(id="task-2", title="Task 2", description="", git_branch_id="branch-1",
                 status="in_progress", priority="medium", details={}, estimated_effort=None,
                 due_date=None, created_at=datetime.now(), updated_at=datetime.now(), context_id=None)
        ]
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_label
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = mock_tasks
        
        result = label_repository.get_tasks_by_label(1)
        
        assert len(result) == 2
        assert all(isinstance(task, TaskEntity) for task in result)
        assert result[0].id == "task-1"
        assert result[1].id == "task-2"
    
    def test_get_tasks_by_label_not_found(self, label_repository, mock_session):
        """Test getting tasks by non-existent label."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError, match="Label"):
            label_repository.get_tasks_by_label(999)
    
    def test_get_labels_by_task_success(self, label_repository, mock_session, mock_task):
        """Test getting labels by task."""
        mock_labels = [
            Mock(id=1, name="bug", color="#ff0000", description="", created_at=datetime.now()),
            Mock(id=2, name="urgent", color="#ff00ff", description="", created_at=datetime.now())
        ]
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = mock_labels
        
        result = label_repository.get_labels_by_task("task-123")
        
        assert len(result) == 2
        assert all(isinstance(label, LabelEntity) for label in result)
        assert result[0].name == "bug"
        assert result[1].name == "urgent"
    
    def test_get_labels_by_task_not_found(self, label_repository, mock_session):
        """Test getting labels by non-existent task."""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError, match="Task"):
            label_repository.get_labels_by_task("nonexistent")
    
    def test_database_error_handling(self, label_repository, mock_session):
        """Test generic database error handling."""
        mock_session.query.side_effect = Exception("Connection lost")
        
        with pytest.raises(RepositoryError, match="Failed to list labels"):
            label_repository.list_labels()


class TestEntityConversion:
    """Test cases for entity conversion methods."""
    
    def test_model_to_entity_conversion(self):
        """Test Label model to entity conversion."""
        repository = ORMLabelRepository(Mock())
        
        model = Mock(spec=Label)
        model.id = 1
        model.name = "test"
        model.color = "#123456"
        model.description = "Test label"
        model.created_at = datetime.now()
        
        entity = repository._model_to_entity(model)
        
        assert isinstance(entity, LabelEntity)
        assert entity.id == model.id
        assert entity.name == model.name
        assert entity.color == model.color
        assert entity.description == model.description
        assert entity.created_at == model.created_at
    
    def test_task_model_to_entity_conversion(self):
        """Test Task model to entity conversion."""
        repository = ORMLabelRepository(Mock())
        
        model = Mock(spec=Task)
        model.id = "task-123"
        model.title = "Test Task"
        model.description = "Description"
        model.git_branch_id = "branch-456"
        model.status = "in_progress"
        model.priority = "high"
        model.details = {"key": "value"}
        model.estimated_effort = 5
        model.due_date = datetime.now()
        model.created_at = datetime.now()
        model.updated_at = datetime.now()
        model.context_id = "context-789"
        
        entity = repository._task_model_to_entity(model)
        
        assert isinstance(entity, TaskEntity)
        assert entity.id == model.id
        assert entity.title == model.title
        assert entity.description == model.description
        assert entity.git_branch_id == model.git_branch_id
        assert entity.status == model.status
        assert entity.priority == model.priority
        assert entity.details == model.details
        assert entity.estimated_effort == model.estimated_effort
        assert entity.due_date == model.due_date
        assert entity.created_at == model.created_at
        assert entity.updated_at == model.updated_at
        assert entity.context_id == model.context_id