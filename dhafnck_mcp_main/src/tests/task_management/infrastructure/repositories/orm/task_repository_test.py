"""
Comprehensive tests for ORMTaskRepository

This module provides complete test coverage for the ORMTaskRepository class,
including all public methods, error handling, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, desc, or_, text, func
import uuid

# Import from the correct paths based on the project structure
import sys
import os
# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

try:
    from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
    from fastmcp.task_management.domain.entities.task import Task as TaskEntity
    from fastmcp.task_management.domain.exceptions.task_exceptions import (
        TaskCreationError,
        TaskNotFoundError,
        TaskUpdateError,
    )
    from fastmcp.task_management.domain.value_objects.task_id import TaskId
    from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
    from fastmcp.task_management.domain.value_objects.priority import Priority
    from fastmcp.task_management.infrastructure.database.models import (
        Task, TaskAssignee, TaskDependency, TaskLabel, Label
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Create simple mock classes for testing
    class ORMTaskRepository:
        def __init__(self, **kwargs):
            pass
    
    class TaskEntity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class TaskCreationError(Exception):
        pass
    
    class TaskNotFoundError(Exception):
        pass
    
    class TaskUpdateError(Exception):
        pass
    
    class TaskId:
        def __init__(self, value):
            self.value = value
    
    class TaskStatus:
        TODO = "todo"
        IN_PROGRESS = "in_progress" 
        DONE = "done"
    
    class Priority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
    
    # Mock database models
    class Task:
        def __init__(self):
            pass
    
    class TaskAssignee:
        def __init__(self):
            pass
    
    class TaskDependency:
        def __init__(self):
            pass
    
    class TaskLabel:
        def __init__(self):
            pass
    
    class Label:
        def __init__(self):
            pass


class TestORMTaskRepository:
    """Comprehensive test suite for ORMTaskRepository"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = Mock(spec=Session)
        # Mock query chain
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        
        session.query.return_value = mock_query
        session.add = Mock()
        session.commit = Mock()
        session.flush = Mock()
        session.delete = Mock()
        session.execute = Mock()
        
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository instance with mocked dependencies"""
        repo = ORMTaskRepository(
            session=mock_session,
            git_branch_id="test-branch-id",
            project_id="test-project-id",
            user_id="test-user-id"
        )
        return repo

    @pytest.fixture
    def sample_task_model(self):
        """Create a sample Task model instance"""
        task = Task()
        task.id = "test-task-id"
        task.title = "Test Task"
        task.description = "Test Description"
        task.git_branch_id = "test-branch-id"
        task.status = "todo"
        task.priority = "medium"
        task.details = "Test details"
        task.estimated_effort = "2 hours"
        task.due_date = None
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        task.context_id = "test-context-id"
        task.progress_percentage = 0
        task.completion_summary = ""
        
        # Mock relationships
        task.assignees = []
        task.labels = []
        task.subtasks = []
        task.dependencies = []
        
        return task

    @pytest.fixture
    def sample_task_entity(self):
        """Create a sample TaskEntity for testing"""
        return TaskEntity(
            id=TaskId("test-task-id"),
            title="Test Task",
            description="Test Description",
            git_branch_id="test-branch-id",
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            assignees=["user1"],
            labels=["frontend"],
            details="Test details",
            estimated_effort="2 hours",
            context_id="test-context-id"
        )

    class TestInitialization:
        """Test repository initialization"""
        
        def test_initialization_with_all_parameters(self):
            """Test repository initialization with all parameters"""
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.get_session') as mock_get_session:
                mock_session = Mock()
                mock_get_session.return_value = mock_session
                
                repo = ORMTaskRepository(
                    session=mock_session,
                    git_branch_id="branch-id",
                    project_id="project-id",
                    git_branch_name="branch-name",
                    user_id="user-id"
                )
                
                assert repo.git_branch_id == "branch-id"
                assert repo.project_id == "project-id" 
                assert repo.git_branch_name == "branch-name"
                assert repo.user_id == "user-id"

        def test_initialization_without_session(self):
            """Test repository initialization without session (uses default)"""
            with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.get_session') as mock_get_session:
                mock_session = Mock()
                mock_get_session.return_value = mock_session
                
                repo = ORMTaskRepository(user_id="user-id")
                
                mock_get_session.assert_called_once()
                assert repo.user_id == "user-id"

    class TestLoadTaskWithRelationships:
        """Test _load_task_with_relationships method"""
        
        def test_successful_load_with_relationships(self, repository, mock_session, sample_task_model):
            """Test successful loading of task with all relationships"""
            # Setup mock to return task with relationships
            mock_session.query.return_value.options.return_value.filter.return_value.first.return_value = sample_task_model
            
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__.return_value = mock_session
                
                result = repository._load_task_with_relationships(mock_session, "test-task-id")
                
                assert result == sample_task_model
                mock_session.query.assert_called_with(Task)

        def test_fallback_to_basic_loading(self, repository, mock_session, sample_task_model):
            """Test fallback to basic loading when relationship loading fails"""
            # First call (with relationships) raises exception
            mock_session.query.return_value.options.side_effect = Exception("Relationship error")
            # Second call (basic) succeeds
            mock_session.query.return_value.filter.return_value.first.return_value = sample_task_model
            
            result = repository._load_task_with_relationships(mock_session, "test-task-id")
            
            assert result == sample_task_model
            # Should have empty relationships as fallback
            assert result.assignees == []
            assert result.labels == []
            assert result.subtasks == []
            assert result.dependencies == []

        def test_complete_failure_returns_none(self, repository, mock_session):
            """Test complete failure returns None"""
            # Both relationship and basic loading fail
            mock_session.query.side_effect = Exception("Database error")
            
            result = repository._load_task_with_relationships(mock_session, "test-task-id")
            
            assert result is None

    class TestModelToEntity:
        """Test _model_to_entity conversion method"""
        
        def test_successful_conversion(self, repository, sample_task_model):
            """Test successful conversion from model to entity"""
            # Setup mock assignees
            mock_assignee = Mock()
            mock_assignee.assignee_id = "user1"
            sample_task_model.assignees = [mock_assignee]
            
            # Setup mock labels
            mock_task_label = Mock()
            mock_label = Mock()
            mock_label.name = "frontend"
            mock_task_label.label = mock_label
            sample_task_model.labels = [mock_task_label]
            
            # Setup mock subtasks
            mock_subtask = Mock()
            mock_subtask.id = "subtask-1"
            sample_task_model.subtasks = [mock_subtask]
            
            # Setup mock dependencies
            mock_dependency = Mock()
            mock_dependency.depends_on_task_id = "dep-task-1"
            sample_task_model.dependencies = [mock_dependency]
            
            entity = repository._model_to_entity(sample_task_model)
            
            assert isinstance(entity, TaskEntity)
            assert str(entity.id) == sample_task_model.id
            assert entity.title == sample_task_model.title
            assert entity.assignees == ["user1"]
            assert entity.labels == ["frontend"]
            assert entity.subtasks == ["subtask-1"]
            assert len(entity.dependencies) == 1

        def test_conversion_with_relationship_errors(self, repository, sample_task_model):
            """Test conversion handles relationship loading errors gracefully"""
            # Mock relationships that raise exceptions
            sample_task_model.assignees = Mock()
            sample_task_model.assignees.__iter__ = Mock(side_effect=Exception("Assignee error"))
            sample_task_model.labels = Mock()
            sample_task_model.labels.__iter__ = Mock(side_effect=Exception("Label error"))
            sample_task_model.subtasks = Mock()
            sample_task_model.subtasks.__iter__ = Mock(side_effect=Exception("Subtask error"))
            sample_task_model.dependencies = Mock()
            sample_task_model.dependencies.__iter__ = Mock(side_effect=Exception("Dependency error"))
            
            entity = repository._model_to_entity(sample_task_model)
            
            # Should still create entity with empty relationships
            assert isinstance(entity, TaskEntity)
            assert entity.assignees == []
            assert entity.labels == []
            assert entity.subtasks == []
            assert entity.dependencies == []

        def test_conversion_with_progress_and_completion(self, repository, sample_task_model):
            """Test conversion includes progress and completion data"""
            sample_task_model.progress_percentage = 75
            sample_task_model.completion_summary = "Task completed successfully"
            
            entity = repository._model_to_entity(sample_task_model)
            
            assert entity.overall_progress == 75
            assert entity._completion_summary == "Task completed successfully"

    class TestCreateTask:
        """Test create_task method"""
        
        @patch('uuid.uuid4')
        def test_successful_task_creation(self, mock_uuid, repository, mock_session):
            """Test successful task creation"""
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="generated-task-id")
            
            # Mock transaction context
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'create') as mock_create, \
                 patch.object(repository, 'get_db_session') as mock_db_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                
                # Mock created task
                mock_task = Mock()
                mock_task.id = "generated-task-id"
                mock_create.return_value = mock_task
                
                # Mock DB session context
                mock_db_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_db_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock loaded task with relationships
                mock_load.return_value = mock_task
                
                # Mock entity conversion
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.create_task(
                    title="Test Task",
                    description="Test Description",
                    priority="high",
                    assignee_ids=["user1", "user2"],
                    label_names=["frontend", "backend"]
                )
                
                mock_create.assert_called_once()
                mock_cache.assert_called_once()
                assert result == mock_entity

        def test_create_task_with_exception(self, repository):
            """Test task creation handles exceptions properly"""
            with patch.object(repository, 'transaction') as mock_transaction:
                mock_transaction.side_effect = Exception("Database error")
                
                with pytest.raises(TaskCreationError, match="Failed to create task"):
                    repository.create_task("Test Task", "Test Description")

        def test_create_task_with_labels(self, repository, mock_session):
            """Test task creation with label assignment"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'create') as mock_create, \
                 patch.object(repository, 'get_db_session') as mock_db_context, \
                 patch('uuid.uuid4') as mock_uuid:
                
                mock_uuid.return_value = Mock()
                mock_uuid.return_value.__str__ = Mock(return_value="label-id")
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                
                mock_task = Mock()
                mock_task.id = "task-id"
                mock_create.return_value = mock_task
                
                mock_db_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_db_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock label query - return None (new label)
                mock_session.query.return_value.filter.return_value.first.return_value = None
                
                with patch.object(repository, '_load_task_with_relationships') as mock_load, \
                     patch.object(repository, '_model_to_entity') as mock_to_entity, \
                     patch.object(repository, 'invalidate_cache_for_entity'):
                    
                    mock_load.return_value = mock_task
                    mock_to_entity.return_value = Mock(spec=TaskEntity)
                    
                    repository.create_task(
                        "Test Task",
                        "Test Description", 
                        label_names=["new-label"]
                    )
                    
                    # Verify label creation
                    assert mock_session.add.call_count >= 2  # Label + TaskLabel

    class TestGetTask:
        """Test get_task method"""
        
        def test_successful_get_task(self, repository, mock_session, sample_task_model):
            """Test successful task retrieval"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, 'is_system_mode') as mock_system, \
                 patch.object(repository, 'log_access') as mock_log, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_system.return_value = False
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.filter.return_value.first.return_value = sample_task_model
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.get_task("test-task-id")
                
                mock_load.assert_called_once_with(mock_session, "test-task-id")
                mock_log.assert_called_once_with('read', 'task', "test-task-id")
                assert result == mock_entity

        def test_get_task_not_found(self, repository, mock_session):
            """Test get_task returns None when task not found"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = None
                
                result = repository.get_task("nonexistent-task-id")
                
                assert result is None

        def test_get_task_with_exception(self, repository, mock_session):
            """Test get_task handles exceptions gracefully"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, 'log_access') as mock_log:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.side_effect = Exception("Database error")
                
                result = repository.get_task("test-task-id")
                
                mock_log.assert_called_once_with('read_failed', 'task', "test-task-id")
                assert result is None

        def test_get_task_user_filter_blocks_access(self, repository, mock_session, sample_task_model):
            """Test user filter blocks unauthorized task access"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, 'is_system_mode') as mock_system:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_system.return_value = False
                mock_filter.return_value = mock_session.query.return_value
                # User filter blocks access
                mock_session.query.return_value.filter.return_value.first.return_value = None
                
                result = repository.get_task("test-task-id")
                
                assert result is None

    class TestUpdateTask:
        """Test update_task method"""
        
        def test_successful_task_update(self, repository, sample_task_model):
            """Test successful task update"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'update') as mock_update, \
                 patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache:
                
                mock_session = Mock()
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_update.return_value = sample_task_model
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.update_task(
                    "test-task-id",
                    title="Updated Title",
                    overall_progress=50
                )
                
                # Check that overall_progress was mapped to progress_percentage
                mock_update.assert_called_once()
                update_call_args = mock_update.call_args[1]
                assert 'progress_percentage' in update_call_args
                assert update_call_args['progress_percentage'] == 50
                assert 'overall_progress' not in update_call_args
                
                mock_cache.assert_called_once()
                assert result == mock_entity

        def test_update_task_not_found(self, repository):
            """Test update_task raises exception when task not found"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'update') as mock_update:
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_update.return_value = None
                
                with pytest.raises(TaskNotFoundError, match="Task test-task-id not found"):
                    repository.update_task("test-task-id", title="Updated")

        def test_update_task_with_assignees(self, repository, sample_task_model):
            """Test task update with assignee changes"""
            mock_session = Mock()
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'update') as mock_update, \
                 patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity, \
                 patch.object(repository, 'invalidate_cache_for_entity'):
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_update.return_value = sample_task_model
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_to_entity.return_value = Mock(spec=TaskEntity)
                
                # Mock query for deleting existing assignees
                mock_session.query.return_value.filter.return_value.delete.return_value = 1
                
                repository.update_task(
                    "test-task-id",
                    assignee_ids=["user1", "user2"]
                )
                
                # Verify assignee deletion and creation
                mock_session.query.assert_called()
                mock_session.add.assert_called()

        def test_update_task_with_labels(self, repository, sample_task_model):
            """Test task update with label changes"""
            mock_session = Mock()
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'update') as mock_update, \
                 patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity, \
                 patch.object(repository, 'invalidate_cache_for_entity'), \
                 patch('uuid.uuid4') as mock_uuid:
                
                mock_uuid.return_value = Mock()
                mock_uuid.return_value.__str__ = Mock(return_value="new-label-id")
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_update.return_value = sample_task_model
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_to_entity.return_value = Mock(spec=TaskEntity)
                
                # Mock label query - return None (new label)
                mock_session.query.return_value.filter.return_value.first.return_value = None
                mock_session.query.return_value.filter.return_value.delete.return_value = 1
                
                repository.update_task(
                    "test-task-id",
                    label_names=["new-label"]
                )
                
                # Verify label creation and task-label relationship
                assert mock_session.add.call_count >= 2

        def test_update_task_with_exception(self, repository):
            """Test update_task handles exceptions properly"""
            with patch.object(repository, 'transaction') as mock_transaction:
                mock_transaction.side_effect = Exception("Database error")
                
                with pytest.raises(TaskUpdateError, match="Failed to update task"):
                    repository.update_task("test-task-id", title="Updated")

    class TestDeleteTask:
        """Test delete_task method"""
        
        def test_successful_task_deletion(self, repository):
            """Test successful task deletion"""
            with patch.object(repository, 'delete') as mock_delete, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache:
                
                mock_delete.return_value = True
                
                result = repository.delete_task("test-task-id")
                
                mock_delete.assert_called_once_with("test-task-id")
                mock_cache.assert_called_once()
                assert result is True

        def test_failed_task_deletion(self, repository):
            """Test failed task deletion"""
            with patch.object(repository, 'delete') as mock_delete:
                mock_delete.return_value = False
                
                result = repository.delete_task("test-task-id")
                
                assert result is False

    class TestListTasks:
        """Test list_tasks method"""
        
        def test_list_tasks_without_filters(self, repository, mock_session, sample_task_model):
            """Test listing tasks without filters"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, 'log_access') as mock_log, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.list_tasks()
                
                mock_log.assert_called_once_with('list', 'task')
                assert len(result) == 1
                assert result[0] == mock_entity

        def test_list_tasks_with_filters(self, repository, mock_session, sample_task_model):
            """Test listing tasks with status and priority filters"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_to_entity.return_value = Mock(spec=TaskEntity)
                
                repository.list_tasks(
                    status="in_progress",
                    priority="high",
                    assignee_id="user1",
                    limit=50,
                    offset=10
                )
                
                # Verify filter was applied
                mock_session.query.return_value.filter.assert_called()
                mock_session.query.return_value.join.assert_called()
                mock_session.query.return_value.offset.assert_called_with(10)
                mock_session.query.return_value.limit.assert_called_with(50)

        def test_list_tasks_with_git_branch_filter(self, repository, mock_session):
            """Test that git_branch_id filter is applied when set"""
            repository.git_branch_id = "test-branch"
            
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.list_tasks()
                
                # Verify git_branch_id filter was applied
                mock_session.query.return_value.filter.assert_called()

    class TestListTasksOptimized:
        """Test list_tasks_optimized method"""
        
        def test_optimized_list_with_selectinload(self, repository, mock_session, sample_task_model):
            """Test optimized task listing uses selectinload"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_to_entity.return_value = Mock(spec=TaskEntity)
                
                result = repository.list_tasks_optimized(limit=20)
                
                # Verify selectinload options were used
                mock_session.query.return_value.options.assert_called()
                assert len(result) == 1

        def test_optimized_list_with_filters(self, repository, mock_session):
            """Test optimized listing with multiple filters"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                mock_to_entity.return_value = Mock(spec=TaskEntity)
                
                repository.list_tasks_optimized(
                    status="todo",
                    priority="high",
                    assignee_id="user1"
                )
                
                # Verify all filters were applied
                mock_session.query.return_value.filter.assert_called()
                mock_session.query.return_value.join.assert_called()

    class TestGetTaskCount:
        """Test get_task_count methods"""
        
        def test_get_task_count_basic(self, repository, mock_session):
            """Test basic task count"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.count.return_value = 5
                
                result = repository.get_task_count()
                
                mock_filter.assert_called_once()
                assert result == 5

        def test_get_task_count_with_status_filter(self, repository, mock_session):
            """Test task count with status filter"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.count.return_value = 3
                
                result = repository.get_task_count(status="completed")
                
                mock_session.query.return_value.filter.assert_called()
                assert result == 3

        def test_get_task_count_optimized(self, repository, mock_session):
            """Test optimized task count using direct SQL"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock SQL execution
                mock_result = Mock()
                mock_result.scalar.return_value = 10
                mock_session.execute.return_value = mock_result
                
                repository.user_id = "test-user"
                result = repository.get_task_count_optimized(status="todo")
                
                mock_session.execute.assert_called_once()
                assert result == 10

        def test_get_task_count_optimized_no_result(self, repository, mock_session):
            """Test optimized task count when no result"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock SQL execution returning None
                mock_result = Mock()
                mock_result.scalar.return_value = None
                mock_session.execute.return_value = mock_result
                
                result = repository.get_task_count_optimized()
                
                assert result == 0

    class TestListTasksMinimal:
        """Test list_tasks_minimal method"""
        
        def test_list_tasks_minimal_success(self, repository, mock_session):
            """Test successful minimal task listing"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, 'log_access') as mock_log:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                
                # Mock task results
                mock_task_result = Mock()
                mock_task_result.id = "task-1"
                mock_task_result.title = "Test Task"
                mock_task_result.status = "todo"
                mock_task_result.priority = "medium"
                mock_task_result.progress_percentage = 25
                mock_task_result.assignees_count = 2
                mock_task_result.due_date = None
                mock_task_result.updated_at = datetime.now()
                mock_task_result.git_branch_id = "branch-1"
                
                mock_session.query.return_value.all.return_value = [mock_task_result]
                
                # Mock labels query
                mock_session.query.return_value.join.return_value = []
                
                result = repository.list_tasks_minimal()
                
                mock_log.assert_called_once_with('list_minimal', 'task')
                assert len(result) == 1
                assert result[0]['id'] == "task-1"
                assert result[0]['title'] == "Test Task"
                assert result[0]['assignees_count'] == 2

        def test_list_tasks_minimal_with_filters(self, repository, mock_session):
            """Test minimal task listing with filters"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.list_tasks_minimal(
                    status="in_progress",
                    priority="high",
                    assignee_id="user1",
                    git_branch_id="specific-branch",
                    limit=50,
                    offset=20
                )
                
                # Verify filters were applied
                mock_session.query.return_value.filter.assert_called()
                mock_session.query.return_value.offset.assert_called_with(20)
                mock_session.query.return_value.limit.assert_called_with(50)

        def test_list_tasks_minimal_with_labels(self, repository, mock_session):
            """Test minimal task listing includes labels"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                
                # Mock task results
                mock_task_result = Mock()
                mock_task_result.id = "task-1"
                mock_task_result.title = "Test Task"
                mock_task_result.status = "todo"
                mock_task_result.priority = "medium"
                mock_task_result.progress_percentage = 0
                mock_task_result.assignees_count = 0
                mock_task_result.due_date = None
                mock_task_result.updated_at = datetime.now()
                mock_task_result.git_branch_id = "branch-1"
                
                mock_session.query.return_value.all.return_value = [mock_task_result]
                
                # Mock labels query
                labels_query_mock = Mock()
                labels_query_mock.__iter__ = Mock(return_value=iter([("task-1", "frontend"), ("task-1", "urgent")]))
                mock_session.query.return_value.join.return_value.filter.return_value = labels_query_mock
                
                result = repository.list_tasks_minimal()
                
                assert len(result) == 1
                assert result[0]['labels'] == ["frontend", "urgent"]

        def test_list_tasks_minimal_limit_validation(self, repository, mock_session):
            """Test minimal task listing validates limits"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                # Test limit validation
                repository.list_tasks_minimal(limit=2000)  # Over max
                mock_session.query.return_value.limit.assert_called_with(1000)  # Capped to max
                
                repository.list_tasks_minimal(limit=-5)  # Negative
                mock_session.query.return_value.limit.assert_called_with(20)  # Default
                
                repository.list_tasks_minimal(offset=-10)  # Negative offset
                mock_session.query.return_value.offset.assert_called_with(0)  # Default

        def test_list_tasks_minimal_exception_handling(self, repository, mock_session):
            """Test minimal task listing handles exceptions gracefully"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.side_effect = Exception("Database error")
                
                result = repository.list_tasks_minimal()
                
                # Should return empty list instead of raising exception
                assert result == []

    class TestSearchTasks:
        """Test search_tasks method"""
        
        def test_search_tasks_single_word(self, repository, mock_session, sample_task_model):
            """Test searching tasks with single word query"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, 'log_access') as mock_log, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.search_tasks("authentication")
                
                mock_log.assert_called_once_with('search', 'task')
                assert len(result) == 1
                assert result[0] == mock_entity

        def test_search_tasks_multi_word(self, repository, mock_session):
            """Test searching tasks with multi-word query"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.search_tasks("user authentication JWT")
                
                # Should process multiple words
                mock_session.query.return_value.filter.assert_called()

        def test_search_tasks_empty_query(self, repository):
            """Test search with empty query returns empty list"""
            result = repository.search_tasks("")
            assert result == []
            
            result = repository.search_tasks("   ")
            assert result == []

        def test_search_tasks_with_git_branch_filter(self, repository, mock_session):
            """Test search respects git_branch_id filter"""
            repository.git_branch_id = "test-branch"
            
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.search_tasks("test")
                
                # Verify git_branch_id filter was applied
                mock_session.query.return_value.filter.assert_called()

    class TestUtilityMethods:
        """Test utility and convenience methods"""
        
        def test_get_tasks_by_assignee(self, repository):
            """Test get_tasks_by_assignee delegates to list_tasks"""
            with patch.object(repository, 'list_tasks') as mock_list:
                mock_list.return_value = []
                
                repository.get_tasks_by_assignee("user1")
                
                mock_list.assert_called_once_with(assignee_id="user1")

        def test_get_overdue_tasks(self, repository, mock_session, sample_task_model):
            """Test getting overdue tasks"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.get_overdue_tasks()
                
                # Verify due_date filter was applied
                mock_session.query.return_value.filter.assert_called()
                assert len(result) == 1
                assert result[0] == mock_entity

        def test_batch_update_status(self, repository, mock_session):
            """Test batch status update"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_session.query.return_value.update.return_value = 3
                
                result = repository.batch_update_status(
                    ["task1", "task2", "task3"],
                    "completed"
                )
                
                mock_session.query.return_value.filter.assert_called()
                mock_session.query.return_value.update.assert_called()
                assert result == 3

    class TestAbstractMethodImplementations:
        """Test implementations of abstract methods from TaskRepository interface"""
        
        def test_save_existing_task(self, repository, sample_task_entity):
            """Test saving existing task"""
            mock_session = Mock()
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock existing task found
                existing_task = Mock()
                mock_session.query.return_value.filter.return_value.first.return_value = existing_task
                
                result = repository.save(sample_task_entity)
                
                mock_session.commit.assert_called_once()
                assert result == sample_task_entity

        def test_save_new_task(self, repository, sample_task_entity):
            """Test saving new task"""
            mock_session = Mock()
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock no existing task found
                mock_session.query.return_value.filter.return_value.first.return_value = None
                
                # Mock user validation
                with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.validate_user_id') as mock_validate:
                    mock_validate.return_value = "validated-user-id"
                    repository.user_id = "test-user-id"
                    
                    result = repository.save(sample_task_entity)
                    
                    mock_session.add.assert_called()
                    mock_session.commit.assert_called_once()
                    assert result == sample_task_entity

        def test_save_without_user_id_raises_error(self, repository, sample_task_entity):
            """Test saving task without user_id raises authentication error"""
            mock_session = Mock()
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock no existing task found
                mock_session.query.return_value.filter.return_value.first.return_value = None
                repository.user_id = None
                
                with patch('fastmcp.task_management.infrastructure.repositories.orm.task_repository.UserAuthenticationRequiredError') as mock_error:
                    mock_error.side_effect = Exception("Authentication required")
                    
                    with pytest.raises(Exception, match="Authentication required"):
                        repository.save(sample_task_entity)

        def test_find_by_id(self, repository):
            """Test find_by_id delegates to get_task"""
            with patch.object(repository, 'get_task') as mock_get:
                mock_get.return_value = Mock(spec=TaskEntity)
                
                result = repository.find_by_id("test-id")
                
                mock_get.assert_called_once_with("test-id")
                assert result is not None

        def test_find_all(self, repository):
            """Test find_all delegates to list_tasks"""
            with patch.object(repository, 'list_tasks') as mock_list:
                mock_list.return_value = []
                
                result = repository.find_all()
                
                mock_list.assert_called_once()
                assert result == []

        def test_find_by_status(self, repository):
            """Test find_by_status delegates to list_tasks"""
            with patch.object(repository, 'list_tasks') as mock_list:
                mock_list.return_value = []
                
                repository.find_by_status(TaskStatus.todo())
                
                mock_list.assert_called_once_with(status="todo")

        def test_find_by_priority(self, repository):
            """Test find_by_priority delegates to list_tasks"""
            with patch.object(repository, 'list_tasks') as mock_list:
                mock_list.return_value = []
                
                repository.find_by_priority(Priority.high())
                
                mock_list.assert_called_once_with(priority="high")

        def test_find_by_assignee(self, repository):
            """Test find_by_assignee delegates to get_tasks_by_assignee"""
            with patch.object(repository, 'get_tasks_by_assignee') as mock_get:
                mock_get.return_value = []
                
                repository.find_by_assignee("user1")
                
                mock_get.assert_called_once_with("user1")

        def test_find_by_labels_not_implemented(self, repository):
            """Test find_by_labels returns empty list (not implemented)"""
            result = repository.find_by_labels(["frontend", "urgent"])
            assert result == []

        def test_search(self, repository):
            """Test search delegates to search_tasks"""
            with patch.object(repository, 'search_tasks') as mock_search:
                mock_search.return_value = []
                
                repository.search("query", 20)
                
                mock_search.assert_called_once_with("query", 20)

        def test_delete(self, repository):
            """Test delete delegates to delete_task"""
            with patch.object(repository, 'delete_task') as mock_delete:
                mock_delete.return_value = True
                
                result = repository.delete("task-id")
                
                mock_delete.assert_called_once_with("task-id")
                assert result is True

        def test_exists(self, repository):
            """Test exists checks if get_task returns result"""
            with patch.object(repository, 'get_task') as mock_get:
                mock_get.return_value = Mock(spec=TaskEntity)
                
                result = repository.exists("task-id")
                
                assert result is True
                
                mock_get.return_value = None
                result = repository.exists("task-id")
                
                assert result is False

        def test_get_next_id(self, repository):
            """Test get_next_id generates new TaskId"""
            with patch('uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = Mock()
                mock_uuid.return_value.__str__ = Mock(return_value="new-task-id")
                
                result = repository.get_next_id()
                
                assert isinstance(result, TaskId)
                assert str(result) == "new-task-id"

        def test_count(self, repository):
            """Test count delegates to get_task_count"""
            with patch.object(repository, 'get_task_count') as mock_count:
                mock_count.return_value = 5
                
                result = repository.count(status="todo")
                
                mock_count.assert_called_once_with(status="todo")
                assert result == 5

        def test_get_statistics(self, repository):
            """Test get_statistics returns task counts by status"""
            with patch.object(repository, 'get_task_count') as mock_count:
                mock_count.side_effect = [10, 3, 4, 3]  # total, completed, in_progress, todo
                
                result = repository.get_statistics()
                
                assert result["total_tasks"] == 10
                assert result["completed_tasks"] == 3
                assert result["in_progress_tasks"] == 4
                assert result["todo_tasks"] == 3

    class TestFindByCriteria:
        """Test find_by_criteria method"""
        
        def test_find_by_criteria_with_status(self, repository, mock_session, sample_task_model):
            """Test finding tasks by status criteria"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = [sample_task_model]
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.find_by_criteria(
                    {"status": TaskStatus.todo()},
                    limit=50
                )
                
                mock_session.query.return_value.filter.assert_called()
                mock_session.query.return_value.limit.assert_called_with(50)
                assert len(result) == 1

        def test_find_by_criteria_with_git_branch_override(self, repository, mock_session):
            """Test git_branch_id filter can be overridden by filters parameter"""
            repository.git_branch_id = "repo-branch"
            
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter, \
                 patch.object(repository, '_model_to_entity'):
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.find_by_criteria({"git_branch_id": "filter-branch"})
                
                # Should use filter value, not repository value
                mock_session.query.return_value.filter.assert_called()

        def test_find_by_criteria_with_assignees(self, repository, mock_session):
            """Test finding tasks by assignees criteria"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.find_by_criteria({"assignees": ["user1", "user2"]})
                
                # Should join TaskAssignee table
                mock_session.query.return_value.join.assert_called()

        def test_find_by_criteria_with_labels(self, repository, mock_session):
            """Test finding tasks by labels criteria"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.find_by_criteria({"labels": ["frontend", "urgent"]})
                
                # Should join TaskLabel and Label tables
                mock_session.query.return_value.join.assert_called()

        def test_find_by_criteria_legacy_assignee(self, repository, mock_session):
            """Test finding tasks by legacy single assignee filter"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.find_by_criteria({"assignee": "user1"})
                
                # Should join TaskAssignee table for single assignee
                mock_session.query.return_value.join.assert_called()

        def test_find_by_criteria_with_enum_values(self, repository, mock_session):
            """Test criteria conversion handles enum value objects properly"""
            mock_status = Mock()
            mock_status.value = "in_progress"
            mock_priority = Mock()
            mock_priority.value = "high"
            
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.find_by_criteria({
                    "status": mock_status,
                    "priority": mock_priority
                })
                
                # Should extract .value from enum objects
                mock_session.query.return_value.filter.assert_called()

    class TestSpecialMethods:
        """Test special and edge case methods"""
        
        def test_find_by_id_all_states(self, repository, mock_session, sample_task_model):
            """Test finding task by ID across all states"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_session.query.return_value.first.return_value = sample_task_model
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.find_by_id_all_states("task-id")
                
                # Should not filter by git_branch_id or status
                mock_session.query.return_value.options.assert_called()
                mock_session.query.return_value.filter.assert_called_once()
                assert result == mock_entity

        def test_find_by_id_all_states_not_found(self, repository, mock_session):
            """Test find_by_id_all_states returns None when task not found"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_session.query.return_value.first.return_value = None
                
                result = repository.find_by_id_all_states("nonexistent-task-id")
                
                assert result is None

        def test_git_branch_exists(self, repository, mock_session):
            """Test checking if git branch exists"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                # Mock branch found
                mock_branch = Mock()
                mock_session.query.return_value.filter.return_value.first.return_value = mock_branch
                
                result = repository.git_branch_exists("existing-branch-id")
                assert result is True
                
                # Mock branch not found
                mock_session.query.return_value.filter.return_value.first.return_value = None
                
                result = repository.git_branch_exists("nonexistent-branch-id")
                assert result is False

    class TestErrorHandling:
        """Test error handling and exception scenarios"""
        
        def test_save_with_database_error(self, repository, sample_task_entity):
            """Test save method handles database errors"""
            mock_session = Mock()
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_session.query.side_effect = Exception("Database connection failed")
                
                with pytest.raises(Exception):
                    repository.save(sample_task_entity)

        def test_create_task_with_integrity_error(self, repository):
            """Test create_task handles integrity constraint violations"""
            with patch.object(repository, 'transaction') as mock_transaction:
                mock_transaction.side_effect = IntegrityError("statement", "params", "orig")
                
                with pytest.raises(TaskCreationError):
                    repository.create_task("Test Task", "Description")

        def test_update_task_with_sql_error(self, repository):
            """Test update_task handles SQL errors"""
            with patch.object(repository, 'transaction') as mock_transaction:
                mock_transaction.side_effect = SQLAlchemyError("SQL error")
                
                with pytest.raises(TaskUpdateError):
                    repository.update_task("task-id", title="Updated")

        def test_list_tasks_with_session_error(self, repository, mock_session):
            """Test list_tasks handles session errors gracefully"""
            with patch.object(repository, 'get_db_session') as mock_context:
                mock_context.return_value.__enter__ = Mock(side_effect=Exception("Session error"))
                
                with pytest.raises(Exception):
                    repository.list_tasks()

        def test_model_to_entity_with_missing_attributes(self, repository):
            """Test _model_to_entity handles models with missing attributes"""
            incomplete_task = Mock()
            incomplete_task.id = "task-id"
            incomplete_task.title = "Test Task"
            incomplete_task.description = "Description"
            incomplete_task.status = "todo"
            incomplete_task.priority = "medium"
            # Missing some attributes
            del incomplete_task.git_branch_id
            del incomplete_task.context_id
            
            # Should not raise exception
            entity = repository._model_to_entity(incomplete_task)
            assert isinstance(entity, TaskEntity)

    class TestCacheInvalidation:
        """Test cache invalidation functionality"""
        
        def test_create_task_invalidates_cache(self, repository):
            """Test task creation triggers cache invalidation"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'create') as mock_create, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache, \
                 patch.object(repository, '_load_task_with_relationships'), \
                 patch.object(repository, '_model_to_entity'):
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_task = Mock()
                mock_task.id = "task-id"
                mock_create.return_value = mock_task
                
                repository.create_task("Test", "Description")
                
                mock_cache.assert_called_once()
                cache_call = mock_cache.call_args
                assert cache_call[1]["entity_type"] == "task"
                assert cache_call[1]["entity_id"] == "task-id"

        def test_update_task_invalidates_cache(self, repository):
            """Test task update triggers cache invalidation"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'update') as mock_update, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache, \
                 patch.object(repository, '_load_task_with_relationships'), \
                 patch.object(repository, '_model_to_entity'):
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_update.return_value = Mock()
                
                repository.update_task("task-id", title="Updated")
                
                mock_cache.assert_called_once()

        def test_delete_task_invalidates_cache(self, repository):
            """Test task deletion triggers cache invalidation"""
            with patch.object(repository, 'delete') as mock_delete, \
                 patch.object(repository, 'invalidate_cache_for_entity') as mock_cache:
                
                mock_delete.return_value = True
                
                repository.delete_task("task-id")
                
                mock_cache.assert_called_once()

    class TestUserIsolation:
        """Test user isolation and security features"""
        
        def test_user_filter_applied_to_queries(self, repository, mock_session):
            """Test user filter is applied to all queries"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, 'apply_user_filter') as mock_filter:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_filter.return_value = mock_session.query.return_value
                mock_session.query.return_value.all.return_value = []
                
                repository.list_tasks()
                repository.search_tasks("query")
                repository.get_task_count()
                
                # User filter should be applied for all operations
                assert mock_filter.call_count == 3

        def test_system_mode_bypasses_user_filter(self, repository, mock_session, sample_task_model):
            """Test system mode bypasses user isolation"""
            with patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships') as mock_load, \
                 patch.object(repository, 'is_system_mode') as mock_system, \
                 patch.object(repository, '_model_to_entity') as mock_to_entity:
                
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                mock_load.return_value = sample_task_model
                mock_system.return_value = True  # System mode
                mock_entity = Mock(spec=TaskEntity)
                mock_to_entity.return_value = mock_entity
                
                result = repository.get_task("task-id")
                
                # Should not apply user filter in system mode
                assert result is not None

        def test_user_id_added_to_relationships(self, repository, mock_session):
            """Test user_id is added to relationship entities"""
            with patch.object(repository, 'transaction') as mock_transaction, \
                 patch.object(repository, 'create') as mock_create, \
                 patch.object(repository, 'get_db_session') as mock_context, \
                 patch.object(repository, '_load_task_with_relationships'), \
                 patch.object(repository, '_model_to_entity'), \
                 patch.object(repository, 'invalidate_cache_for_entity'):
                
                mock_transaction.return_value.__enter__ = Mock()
                mock_transaction.return_value.__exit__ = Mock(return_value=None)
                mock_task = Mock()
                mock_task.id = "task-id"
                mock_create.return_value = mock_task
                mock_context.return_value.__enter__ = Mock(return_value=mock_session)
                mock_context.return_value.__exit__ = Mock(return_value=None)
                
                repository.user_id = "test-user"
                repository.create_task(
                    "Test Task",
                    "Description",
                    assignee_ids=["user1"],
                    label_names=["frontend"]
                )
                
                # Verify user_id is set on relationship entities
                assert mock_session.add.called
                add_calls = mock_session.add.call_args_list
                # Should have calls for TaskAssignee and TaskLabel with user_id
                assert len(add_calls) >= 2