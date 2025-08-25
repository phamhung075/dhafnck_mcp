"""
Tests for ORM Task Repository Implementation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.base_orm_repository import BaseORMRepository
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
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseUserScopedRepository.__init__'):
                repo = ORMTaskRepository(mock_session, git_branch_id, project_id, user_id=user_id)
                repo.session = mock_session
                repo.get_db_session = Mock(return_value=mock_session)
                repo.transaction = Mock()
                repo.transaction.__enter__ = Mock(return_value=None)
                repo.transaction.__exit__ = Mock(return_value=None)
                repo.git_branch_id = git_branch_id
                repo.project_id = project_id
                repo.user_id = user_id
                repo._is_system_mode = False
                repo.apply_user_filter = Mock(return_value=Mock())
                repo.log_access = Mock()
                repo.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": user_id})
                return repo
    
    @pytest.fixture
    def mock_task_model(self):
        """Create a mock Task model"""
        from datetime import timezone
        task = Mock(spec=Task)
        task.id = "12345678-1234-5678-1234-567812345678"  # Valid UUID format
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
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        
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
        mock_subtask.id = "11111111-2222-3333-4444-555555555555"  # Valid UUID
        mock_task_model.subtasks = [mock_subtask]
        
        # Add mock dependency
        mock_dependency = Mock(spec=TaskDependency)
        mock_dependency.depends_on_task_id = "99999999-8888-7777-6666-555555555555"  # Valid UUID
        mock_task_model.dependencies = [mock_dependency]
        
        entity = repository._model_to_entity(mock_task_model)
        
        assert isinstance(entity, TaskEntity)
        assert entity.id.value == mock_task_model.id
        assert entity.title == mock_task_model.title
        assert entity.description == mock_task_model.description
        assert entity.status.value == "todo"
        assert entity.priority.value == "high"
        assert entity.overall_progress == 50
        assert "user-456" in entity.assignees
        assert "bug" in entity.labels
        assert "11111111-2222-3333-4444-555555555555" in entity.subtasks
        assert len(entity.dependencies) == 1
        assert entity.dependencies[0].value == "99999999-8888-7777-6666-555555555555"
    
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
        from datetime import timezone
        mock_reloaded_task.created_at = datetime.now(timezone.utc)
        mock_reloaded_task.updated_at = datetime.now(timezone.utc)
        
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
        assert result.priority.value == "high"
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
        from datetime import timezone
        mock_reloaded_task.created_at = datetime.now(timezone.utc)
        mock_reloaded_task.updated_at = datetime.now(timezone.utc)
        
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
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
        
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
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
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
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
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
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
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
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
        repository.update = Mock(side_effect=Exception("Update failed"))
        
        with pytest.raises(TaskUpdateError) as exc_info:
            repository.update_task(task_id, title="New Title")
        
        assert "Failed to update task" in str(exc_info.value)
        assert "Update failed" in str(exc_info.value)
    
    def test_delete_task(self, repository):
        """Test task deletion"""
        task_id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
        
        # Mock the parent delete method
        with patch.object(repository, 'delete', return_value=True) as mock_delete:
            result = repository.delete_task(task_id)
        
        assert result is True
        mock_delete.assert_called_once_with(task_id)
    
    def test_initialization_with_user(self, mock_session, git_branch_id, project_id, user_id):
        """Test repository initialization with user ID"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseORMRepository.__init__'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseUserScopedRepository.__init__'):
                repo = ORMTaskRepository(
                    mock_session,
                    git_branch_id=git_branch_id,
                    project_id=project_id,
                    user_id=user_id
                )
                repo.session = mock_session
                repo.git_branch_id = git_branch_id
                repo.project_id = project_id
                repo.user_id = user_id
                repo._is_system_mode = False
                
                assert repo.session == mock_session
                assert repo.git_branch_id == git_branch_id
                assert repo.project_id == project_id
                assert repo.user_id == user_id
                assert repo._is_system_mode is False
    
    def test_model_to_entity_with_no_relationships(self, repository):
        """Test model to entity conversion with no relationships"""
        task = Mock(spec=Task)
        task.id = "99999999-9999-9999-9999-999999999999"  # Valid UUID
        task.title = "Simple Task"
        task.description = "No relationships"
        task.git_branch_id = "branch-123"
        task.status = "done"
        task.priority = "low"
        task.details = ""
        task.estimated_effort = ""
        task.due_date = None
        task.context_id = None
        from datetime import timezone
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        task.assignees = []
        task.labels = []
        task.subtasks = []
        task.dependencies = []
        
        # Test without progress_percentage attribute
        if hasattr(task, 'progress_percentage'):
            delattr(task, 'progress_percentage')
        
        entity = repository._model_to_entity(task)
        
        assert entity.id.value == task.id
        assert entity.status.value == "done"
        assert entity.priority.value == "low"
        assert len(entity.assignees) == 0
        assert len(entity.labels) == 0
        assert len(entity.subtasks) == 0
        assert len(entity.dependencies) == 0
        assert entity.overall_progress == 0  # Default value
    
    def test_list_tasks_with_user_filter(self, repository, mock_task_model):
        """Test listing tasks applies user filter"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_task_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = repository.list_tasks(status="todo", priority="high")
        
        assert len(result) == 1
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('list', 'task')
    
    def test_search_tasks_with_user_filter(self, repository, mock_task_model):
        """Test searching tasks applies user filter"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_task_model]
        
        # Mock label subquery
        mock_subquery = Mock()
        mock_query.join.return_value.filter.return_value.subquery.return_value = mock_subquery
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = repository.search_tasks("test query")
        
        assert len(result) == 1
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('search', 'task')
    
    def test_list_tasks_optimized(self, repository, mock_task_model):
        """Test optimized task listing with user filter"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_task_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        
        result = repository.list_tasks_optimized(status="in_progress", limit=10)
        
        assert len(result) == 1
        repository.apply_user_filter.assert_called_once()
    
    def test_get_task_count_with_user_filter(self, repository):
        """Test task count applies user filter"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        
        result = repository.get_task_count(status="todo")
        
        assert result == 5
        repository.apply_user_filter.assert_called_once()
    
    def test_get_task_count_optimized(self, repository):
        """Test optimized task count with user filter"""
        mock_result = Mock()
        mock_result.scalar.return_value = 10
        
        repository.session.execute.return_value = mock_result
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = repository.get_task_count_optimized(status="done", priority="high")
        
        assert result == 10
        # Verify SQL includes user_id filter
        execute_call = repository.session.execute.call_args
        sql_query = execute_call[0][0].text
        params = execute_call[0][1]
        assert "user_id = :user_id" in sql_query
        assert params["user_id"] == repository.user_id
    
    def test_save_task_entity(self, repository):
        """Test saving a task entity"""
        from datetime import timezone
        task_entity = TaskEntity(
            id=TaskId("12345678-1234-5678-1234-567812345678"),
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123",
            status=TaskStatus("todo"),
            priority=Priority("high"),
            assignees=["user-111"],
            labels=["urgent"],
            details="Details",
            estimated_effort="3 hours",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        task_entity.overall_progress = 25
        
        # Mock session and query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing task
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = repository.save(task_entity)
        
        assert result == task_entity
        # Verify new task was added
        repository.session.add.assert_called()
        repository.session.commit.assert_called_once()
    
    def test_save_existing_task_entity(self, repository, mock_task_model):
        """Test updating an existing task entity"""
        from datetime import timezone
        task_entity = TaskEntity(
            id=TaskId("12345678-1234-5678-1234-567812345678"),
            title="Updated Task",
            description="Updated Description",
            git_branch_id="branch-123",
            status=TaskStatus("in_progress"),
            priority=Priority("medium"),
            assignees=[],
            labels=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock existing task
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_task_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = repository.save(task_entity)
        
        assert result == task_entity
        # Verify existing task was updated
        assert mock_task_model.title == "Updated Task"
        assert mock_task_model.status == "in_progress"
        repository.session.commit.assert_called_once()
    
    def test_batch_update_status(self, repository):
        """Test batch updating task status"""
        mock_query = Mock()
        mock_query.filter.return_value.update.return_value = 3  # 3 tasks updated
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        task_ids = ["task-1", "task-2", "task-3"]
        result = repository.batch_update_status(task_ids, "completed")
        
        assert result == 3
        # Verify update was called with correct parameters
        update_call = mock_query.filter.return_value.update.call_args
        assert update_call[0][0]['status'] == 'completed'
        assert 'updated_at' in update_call[0][0]
    
    def test_find_by_criteria(self, repository, mock_task_model):
        """Test finding tasks by multiple criteria"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_task_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Test with TaskStatus and Priority enums
        filters = {
            'status': TaskStatus('in_progress'),
            'priority': Priority('high'),
            'assignees': ['user-123', 'user-456']
        }
        
        result = repository.find_by_criteria(filters, limit=10)
        
        assert len(result) == 1
        # Verify filters were applied
        assert mock_query.filter.called
        assert mock_query.join.called
    
    def test_git_branch_exists(self, repository):
        """Test checking if git branch exists"""
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        
        mock_branch = Mock(spec=ProjectGitBranch)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_branch
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = repository.git_branch_exists("branch-123")
        
        assert result is True
        
        # Test non-existent branch
        mock_query.filter.return_value.first.return_value = None
        result = repository.git_branch_exists("nonexistent")
        
        assert result is False
    
    def test_create_task_with_user_id_in_task_label(self, repository):
        """Test that user_id is properly set in TaskLabel during task creation"""
        title = "Task with Labels"
        description = "Testing user_id in labels"
        label_names = ["test-label"]
        
        mock_created_task = Mock()
        mock_created_task.id = "new-task-id"
        repository.create = Mock(return_value=mock_created_task)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": repository.user_id})
        
        # Mock query for labels
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing label
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
        from datetime import timezone
        mock_reloaded_task.created_at = datetime.now(timezone.utc)
        mock_reloaded_task.updated_at = datetime.now(timezone.utc)
        
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_reloaded_task
        
        with patch('uuid.uuid4', return_value='generated-label-id'):
            result = repository.create_task(
                title=title,
                description=description,
                label_names=label_names
            )
        
        # Find TaskLabel creation call
        task_label_calls = [
            call for call in repository.session.add.call_args_list
            if call[0][0].__class__.__name__ == 'TaskLabel'
        ]
        
        # Verify user_id was set in TaskLabel
        assert len(task_label_calls) > 0
        task_label = task_label_calls[0][0][0]
        assert hasattr(task_label, 'user_id')
        assert task_label.user_id == repository.user_id
    
    def test_count(self, repository):
        """Test count method"""
        # Mock get_task_count
        repository.get_task_count = Mock(return_value=10)
        
        # Test count with no filters
        result = repository.count()
        assert result == 10
        repository.get_task_count.assert_called_once_with(status=None)
        
        # Test count with status filter
        repository.get_task_count.reset_mock()
        result = repository.count(status="todo")
        assert result == 10
        repository.get_task_count.assert_called_once_with(status="todo")
    
    def test_count_with_multiple_filters(self, repository):
        """Test count method with multiple filters (only status is used)"""
        repository.get_task_count = Mock(return_value=5)
        
        # Even if other filters are passed, only status is used
        result = repository.count(status="in_progress", priority="high", assignee="user-123")
        assert result == 5
        repository.get_task_count.assert_called_once_with(status="in_progress")
    
    def test_get_statistics(self, repository):
        """Test get_statistics method"""
        # Mock the count methods
        repository.get_task_count = Mock()
        repository.get_task_count.side_effect = [
            10,  # total_tasks
            3,   # todo_tasks
            4,   # in_progress_tasks
            2,   # done_tasks
            1    # cancelled_tasks
        ]
        
        result = repository.get_statistics()
        
        assert result == {
            "total_tasks": 10,
            "todo_tasks": 3,
            "in_progress_tasks": 4,
            "done_tasks": 2,
            "cancelled_tasks": 1
        }
        
        # Verify get_task_count was called with correct parameters
        assert repository.get_task_count.call_count == 5
        repository.get_task_count.assert_any_call()
        repository.get_task_count.assert_any_call(status="todo")
        repository.get_task_count.assert_any_call(status="in_progress")
        repository.get_task_count.assert_any_call(status="done")
        repository.get_task_count.assert_any_call(status="cancelled")
    
    def test_find_by_criteria_with_all_filters(self, repository, mock_task_model):
        """Test find_by_criteria with all possible filters"""
        mock_query = Mock()
        repository.session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_task_model]
        
        # Mock apply_user_filter
        repository.apply_user_filter = Mock(return_value=mock_query)
        
        filters = {
            'git_branch_id': 'branch-123',
            'status': TaskStatus.IN_PROGRESS,
            'priority': Priority.HIGH,
            'assignees': ['user-1', 'user-2'],
            'labels': ['bug', 'feature']
        }
        
        result = repository.find_by_criteria(filters, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], TaskEntity)
        
        # Verify filters were applied
        repository.apply_user_filter.assert_called_once()
        mock_query.limit.assert_called_once_with(10)
    
    def test_find_by_criteria_with_legacy_assignee(self, repository, mock_task_model):
        """Test find_by_criteria with legacy single assignee filter"""
        mock_query = Mock()
        repository.session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_task_model]
        
        repository.apply_user_filter = Mock(return_value=mock_query)
        
        filters = {
            'assignee': 'user-123'  # Legacy single assignee
        }
        
        result = repository.find_by_criteria(filters)
        
        assert len(result) == 1
        # Verify join was called for assignee filter
        mock_query.join.assert_called()
    
    # REGRESSION TESTS FOR GIT BRANCH FILTERING FIX
    # Issue: Logical OR operator in git_branch_filter caused falsy values to be ignored
    
    def test_git_branch_filtering_with_constructor_value(self, mock_session, mock_task_model):
        """Test that constructor git_branch_id is used correctly for filtering"""
        # Test various git_branch_id values that might be falsy
        test_cases = [
            "normal-branch-id",      # Normal string
            "",                      # Empty string (falsy) - should still apply filter
            "0",                     # String zero (falsy in some contexts) - should still apply filter
            "false",                 # String false - should still apply filter
            "null"                   # String null - should still apply filter
        ]
        
        for git_branch_id in test_cases:
            # Create repository with mocked session
            with patch.object(ORMTaskRepository, '__init__', lambda self, session, git_branch_id=None, project_id=None, git_branch_name=None, user_id=None: None):
                repository = ORMTaskRepository(
                    session=mock_session,
                    git_branch_id=git_branch_id,
                    user_id="test-user"
                )
                # Manually set attributes since __init__ is mocked
                repository.git_branch_id = git_branch_id
                repository.user_id = "test-user"
                repository.project_id = "test-project"
                repository.session = mock_session
                
                # Mock the database session context manager
                mock_context_session = Mock()
                mock_context_session.__enter__ = Mock(return_value=mock_session)
                mock_context_session.__exit__ = Mock(return_value=None)
                
                with patch.object(repository, 'get_db_session', return_value=mock_context_session):
                    mock_query = Mock()
                    mock_session.query.return_value = mock_query
                    mock_query.options.return_value = mock_query
                    mock_query.filter.return_value = mock_query
                    mock_query.order_by.return_value = mock_query
                    mock_query.all.return_value = [mock_task_model]
                    
                    repository.apply_user_filter = Mock(return_value=mock_query)
                    
                    # Call find_by_criteria without git_branch_id in filters
                    result = repository.find_by_criteria({})
                    
                    # Verify the constructor git_branch_id was used for filtering
                    # With the fix, filter is now applied for all non-None values (including falsy ones)
                    if git_branch_id is not None:
                        mock_query.filter.assert_called()
                        filter_calls = mock_query.filter.call_args_list
                        
                        # Check that git_branch_id filter was applied
                        git_branch_filter_applied = any(
                            'git_branch_id' in str(call) for call in filter_calls
                        )
                        
                        assert git_branch_filter_applied, f"Git branch filter not applied for value: {git_branch_id}"
                    
                    assert len(result) == 1
    
    def test_git_branch_filtering_precedence(self, mock_session, mock_task_model):
        """Test that constructor git_branch_id takes precedence over filters git_branch_id"""
        constructor_branch_id = "constructor-branch"
        filter_branch_id = "filter-branch"
        
        with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
            repository = ORMTaskRepository(
                session=mock_session,
                git_branch_id=constructor_branch_id,
                user_id="test-user"
            )
            
            mock_query = Mock()
            repository.session.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_task_model]
            
            repository.apply_user_filter = Mock(return_value=mock_query)
            
            # Call with git_branch_id in filters - constructor should take precedence
            filters = {'git_branch_id': filter_branch_id}
            result = repository.find_by_criteria(filters)
            
            # Verify constructor value was used, not filter value
            filter_calls = mock_query.filter.call_args_list
            constructor_used = any(
                constructor_branch_id in str(call) 
                for call in filter_calls
            )
            filter_used = any(
                filter_branch_id in str(call) and constructor_branch_id not in str(call)
                for call in filter_calls
            )
            
            assert constructor_used, "Constructor git_branch_id should take precedence"
            assert not filter_used, "Filter git_branch_id should not be used when constructor is set"
            assert len(result) == 1
    
    def test_git_branch_filtering_fallback_to_filters(self, mock_session, mock_task_model):
        """Test that filters git_branch_id is used when constructor git_branch_id is None"""
        filter_branch_id = "filter-branch"
        
        with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
            repository = ORMTaskRepository(
                session=mock_session,
                git_branch_id=None,  # Constructor has None
                user_id="test-user"
            )
            
            mock_query = Mock()
            repository.session.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_task_model]
            
            repository.apply_user_filter = Mock(return_value=mock_query)
            
            # Call with git_branch_id in filters
            filters = {'git_branch_id': filter_branch_id}
            result = repository.find_by_criteria(filters)
            
            # Verify filter value was used
            filter_calls = mock_query.filter.call_args_list
            filter_used = any(
                filter_branch_id in str(call) 
                for call in filter_calls
            )
            
            assert filter_used, "Filter git_branch_id should be used when constructor is None"
            assert len(result) == 1
    
    def test_git_branch_filtering_no_filter_when_both_none(self, mock_session, mock_task_model):
        """Test that no git_branch_id filter is applied when both constructor and filters are None"""
        with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
            repository = ORMTaskRepository(
                session=mock_session,
                git_branch_id=None,
                user_id="test-user"
            )
            
            mock_query = Mock()
            repository.session.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_task_model]
            
            repository.apply_user_filter = Mock(return_value=mock_query)
            
            # Call without git_branch_id in filters
            filters = {}
            result = repository.find_by_criteria(filters)
            
            # Verify no git_branch_id filter was applied
            filter_calls = mock_query.filter.call_args_list
            git_branch_filter_applied = any(
                'git_branch_id' in str(call) 
                for call in filter_calls
            )
            
            assert not git_branch_filter_applied, "No git_branch_id filter should be applied when both are None"
            assert len(result) == 1
    
    def test_git_branch_filtering_debug_logging(self, mock_session, mock_task_model):
        """Test that proper debug logging is generated for git branch filtering"""
        git_branch_id = "test-branch"
        
        with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
            repository = ORMTaskRepository(
                session=mock_session,
                git_branch_id=git_branch_id,
                user_id="test-user"
            )
            
            mock_query = Mock()
            repository.session.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.all.return_value = [mock_task_model]
            
            repository.apply_user_filter = Mock(return_value=mock_query)
            
            # Mock logger to capture debug messages
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.logger') as mock_logger:
                filters = {}
                result = repository.find_by_criteria(filters)
                
                # Verify debug logging was called with proper messages
                debug_calls = mock_logger.debug.call_args_list
                
                # Check for branch filter resolution log
                resolution_logged = any(
                    'Branch filter resolution:' in str(call) and git_branch_id in str(call)
                    for call in debug_calls
                )
                
                # Check for branch filter application log
                application_logged = any(
                    'Applying git_branch_id filter:' in str(call) and git_branch_id in str(call)
                    for call in debug_calls
                )
                
                assert resolution_logged, "Branch filter resolution should be logged"
                assert application_logged, "Branch filter application should be logged"
                assert len(result) == 1
    
    def test_git_branch_filtering_edge_cases(self, mock_session, mock_task_model):
        """Test git branch filtering with various edge case values"""
        edge_cases = [
            (0, "numeric zero"),
            (False, "boolean false"),
            ([], "empty list"),
            ({}, "empty dict"),
            ("   ", "whitespace string"),
        ]
        
        for edge_value, description in edge_cases:
            with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
                repository = ORMTaskRepository(
                    session=mock_session,
                    git_branch_id=edge_value,
                    user_id="test-user"
                )
                
                mock_query = Mock()
                repository.session.query.return_value = mock_query
                mock_query.options.return_value = mock_query
                mock_query.filter.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_query.all.return_value = [mock_task_model]
                
                repository.apply_user_filter = Mock(return_value=mock_query)
                
                # Should not raise exception and should handle edge case gracefully
                try:
                    result = repository.find_by_criteria({})
                    # If the edge value is truthy and not None, it should be used for filtering
                    if edge_value is not None and edge_value not in (False, 0, [], {}, ""):
                        # Filter should be applied for non-falsy values
                        mock_query.filter.assert_called()
                    assert len(result) == 1
                except Exception as e:
                    pytest.fail(f"Edge case {description} ({edge_value}) caused exception: {e}")
    
    def test_git_branch_constructor_storage(self, mock_session):
        """Test that constructor properly stores git_branch_id"""
        test_branch_id = "stored-branch-id"
        
        with patch.object(ORMTaskRepository, 'get_db_session', return_value=mock_session):
            repository = ORMTaskRepository(
                session=mock_session,
                git_branch_id=test_branch_id,
                user_id="test-user"
            )
            
            # Verify the git_branch_id was stored correctly
            assert repository.git_branch_id == test_branch_id
            
            # Test with None
            repository_none = ORMTaskRepository(
                session=mock_session,
                git_branch_id=None,
                user_id="test-user"
            )
            
            assert repository_none.git_branch_id is None
    
    def test_user_isolation_in_graceful_loading(self, repository, mock_session):
        """Test user isolation is properly applied in graceful task loading"""
        task_id = "test-task-id"
        
        # Mock relationships loading failure to trigger fallback
        mock_session.query.side_effect = [Exception("Relationship loading failed"), Mock()]
        
        # Mock basic task loading
        mock_task = Mock()
        mock_task.assignees = []
        mock_task.labels = []
        mock_task.subtasks = []
        mock_task.dependencies = []
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = mock_query
        
        result = repository._load_task_with_relationships(mock_session, task_id)
        
        # Should fallback to basic loading and return task with empty relationships
        assert result == mock_task
        assert result.assignees == []
        assert result.labels == []
        assert result.subtasks == []
        assert result.dependencies == []
    
    def test_task_assignee_user_id_constraint(self, repository):
        """Test that TaskAssignee creation includes user_id for database constraint"""
        title = "Task with Assignee"
        assignee_ids = ["user-456"]
        
        mock_created_task = Mock()
        mock_created_task.id = "new-task-id"
        repository.create = Mock(return_value=mock_created_task)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": repository.user_id})
        
        # Mock session
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        # Mock reloaded task
        mock_reloaded_task = Mock(spec=Task)
        mock_reloaded_task.id = "new-task-id"
        mock_reloaded_task.assignees = []
        mock_reloaded_task.labels = []
        mock_reloaded_task.subtasks = []
        mock_reloaded_task.dependencies = []
        from datetime import timezone
        mock_reloaded_task.created_at = datetime.now(timezone.utc)
        mock_reloaded_task.updated_at = datetime.now(timezone.utc)
        
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_reloaded_task
        repository.session.query.return_value = mock_query
        
        result = repository.create_task(
            title=title,
            description="Description",
            assignee_ids=assignee_ids
        )
        
        # Verify TaskAssignee was created with user_id
        add_calls = repository.session.add.call_args_list
        assignee_adds = [call for call in add_calls if hasattr(call[0][0], 'assignee_id')]
        
        assert len(assignee_adds) >= 1
        assignee_obj = assignee_adds[0][0][0]
        assert hasattr(assignee_obj, 'user_id')
        assert assignee_obj.user_id == repository.user_id
    
    def test_user_id_in_authentication_context(self, mock_session):
        """Test user authentication context in task creation and saving"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseORMRepository.__init__'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.BaseUserScopedRepository.__init__'):
                repo = ORMTaskRepository(mock_session, git_branch_id="branch-123", user_id="authenticated-user")
                repo.user_id = "authenticated-user"
                repo.session = mock_session
                
                # Test user_id is used in various operations
                assert repo.user_id == "authenticated-user"
                
                # Mock task entity for save method testing
                from fastmcp.task_management.domain.entities.task import Task as TaskEntity
                from fastmcp.task_management.domain.value_objects.task_id import TaskId
                from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
                from fastmcp.task_management.domain.value_objects.priority import Priority
                from datetime import timezone
                
                task_entity = TaskEntity(
                    id=TaskId("12345678-1234-5678-1234-567812345678"),
                    title="Test Task",
                    description="Test Description",
                    git_branch_id="branch-123",
                    status=TaskStatus("todo"),
                    priority=Priority("high"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                # Mock session operations for save
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = None  # No existing task
                repo.session.query.return_value = mock_query
                repo.session.add = Mock()
                repo.session.commit = Mock()
                repo.session.__enter__ = Mock(return_value=repo.session)
                repo.session.__exit__ = Mock(return_value=None)
                
                # Save should use authenticated user_id
                result = repo.save(task_entity)
                
                # Verify user_id was set in created task
                repo.session.add.assert_called()
                created_task = repo.session.add.call_args[0][0]
                assert created_task.user_id == "authenticated-user"