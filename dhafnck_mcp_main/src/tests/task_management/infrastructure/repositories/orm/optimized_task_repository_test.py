"""
Tests for Optimized Task Repository
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository import OptimizedTaskRepository
from fastmcp.task_management.infrastructure.database.models import Task, TaskAssignee, TaskLabel, Label
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestOptimizedTaskRepository:
    """Test the OptimizedTaskRepository class"""
    
    @pytest.fixture
    def mock_optimizer(self):
        """Create a mock performance optimizer"""
        optimizer = Mock()
        optimizer.get_cache_key = Mock(side_effect=lambda op, **kwargs: f"{op}_{kwargs}")
        optimizer.get_from_cache = Mock(return_value=None)
        optimizer.set_cache = Mock()
        optimizer.optimize_task_query = Mock(side_effect=lambda session, query, filters: query)
        optimizer._cache = {}
        return optimizer
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = Mock(spec=Session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        return session
    
    @pytest.fixture
    def repository(self, mock_optimizer, mock_session):
        """Create a repository instance"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.get_performance_optimizer', return_value=mock_optimizer):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.ORMTaskRepository.__init__'):
                repo = OptimizedTaskRepository(git_branch_id="branch-123")
                repo.get_db_session = Mock(return_value=mock_session)
                repo._model_to_entity = Mock()
                repo.optimizer = mock_optimizer
                repo.git_branch_id = "branch-123"
                return repo
    
    @pytest.fixture
    def mock_task_model(self):
        """Create a mock Task model"""
        task = Mock(spec=Task)
        task.id = "task-123"
        task.title = "Test Task"
        task.description = "Test description"
        task.git_branch_id = "branch-123"
        task.status = "todo"
        task.priority = "high"
        task.progress_percentage = 50
        task.due_date = None
        task.created_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        task.assignees = []
        task.labels = []
        task.subtasks = []
        task.dependencies = []
        return task
    
    def test_list_tasks_with_cache_hit(self, repository, mock_optimizer):
        """Test list_tasks returns cached result when available"""
        # Arrange
        cached_tasks = [Mock(spec=TaskEntity)]
        mock_optimizer.get_from_cache.return_value = cached_tasks
        
        # Act
        result = repository.list_tasks(status="todo", use_cache=True)
        
        # Assert
        assert result == cached_tasks
        mock_optimizer.get_from_cache.assert_called_once()
        mock_optimizer.set_cache.assert_not_called()
    
    def test_list_tasks_with_cache_miss(self, repository, mock_optimizer, mock_session, mock_task_model):
        """Test list_tasks fetches from database on cache miss"""
        # Arrange
        mock_optimizer.get_from_cache.return_value = None
        
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_task_model]
        
        mock_session.query.return_value = mock_query
        
        task_entity = Mock(spec=TaskEntity)
        repository._model_to_entity.return_value = task_entity
        
        # Act
        result = repository.list_tasks(status="todo", priority="high", limit=10, use_cache=True)
        
        # Assert
        assert result == [task_entity]
        mock_optimizer.get_from_cache.assert_called_once()
        mock_optimizer.set_cache.assert_called_once()
        mock_session.query.assert_called_once_with(Task)
        repository._model_to_entity.assert_called_once_with(mock_task_model)
    
    def test_list_tasks_applies_filters(self, repository, mock_session):
        """Test list_tasks applies all filters correctly"""
        # Arrange
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session.query.return_value = mock_query
        
        # Act
        repository.list_tasks(
            status="todo",
            priority="high",
            assignee_id="user-123",
            limit=20,
            offset=10
        )
        
        # Assert
        # Verify filter was called
        mock_query.filter.assert_called()
        # Verify assignee filter
        mock_query.filter.assert_any_call(Task.assignees.any(TaskAssignee.assignee_id == "user-123"))
        # Verify pagination
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(20)
    
    def test_list_tasks_minimal(self, repository, mock_optimizer, mock_session):
        """Test list_tasks_minimal returns minimal task data"""
        # Arrange
        mock_optimizer.get_from_cache.return_value = None
        
        # Mock query results
        mock_result = Mock()
        mock_result.id = "task-123"
        mock_result.title = "Test Task"
        mock_result.status = "todo"
        mock_result.priority = "high"
        mock_result.progress_percentage = 50
        mock_result.due_date = None
        mock_result.updated_at = datetime.now(timezone.utc)
        mock_result.assignees_count = 2
        
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_result]
        
        mock_session.query.return_value = mock_query
        
        # Mock labels query
        mock_labels_query = Mock()
        mock_labels_query.join.return_value = mock_labels_query
        mock_labels_query.filter.return_value = mock_labels_query
        mock_labels_query.__iter__ = Mock(return_value=iter([("task-123", "bug"), ("task-123", "urgent")]))
        mock_session.query.side_effect = [mock_query, mock_labels_query]
        
        # Act
        result = repository.list_tasks_minimal(status="todo", limit=10)
        
        # Assert
        assert len(result) == 1
        assert result[0]['id'] == "task-123"
        assert result[0]['title'] == "Test Task"
        assert result[0]['status'] == "todo"
        assert result[0]['priority'] == "high"
        assert result[0]['progress_percentage'] == 50
        assert result[0]['assignees_count'] == 2
        assert result[0]['labels'] == ["bug", "urgent"]
        
        mock_optimizer.set_cache.assert_called_once()
    
    def test_list_tasks_minimal_with_filters(self, repository, mock_session):
        """Test list_tasks_minimal applies filters correctly"""
        # Arrange
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session.query.return_value = mock_query
        
        # Act
        repository.list_tasks_minimal(
            status="in_progress",
            priority="low",
            assignee_id="user-456",
            limit=5,
            offset=20
        )
        
        # Assert
        # Verify filter was called
        mock_query.filter.assert_called()
        # Should filter by assignee
        assert any(TaskAssignee.assignee_id == "user-456" in str(call) for call in mock_query.filter.call_args_list)
        # Verify pagination
        mock_query.offset.assert_called_once_with(20)
        mock_query.limit.assert_called_once_with(5)
    
    def test_get_task_count_with_cache(self, repository, mock_optimizer):
        """Test get_task_count returns cached value"""
        # Arrange
        mock_optimizer.get_from_cache.return_value = 42
        
        # Act
        result = repository.get_task_count(status="todo", use_cache=True)
        
        # Assert
        assert result == 42
        mock_optimizer.get_from_cache.assert_called_once()
        mock_optimizer.set_cache.assert_not_called()
    
    def test_get_task_count_without_cache(self, repository, mock_optimizer, mock_session):
        """Test get_task_count fetches from database"""
        # Arrange
        mock_optimizer.get_from_cache.return_value = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 15
        
        mock_session.query.return_value = mock_query
        
        # Act
        result = repository.get_task_count(status="done", use_cache=True)
        
        # Assert
        assert result == 15
        mock_optimizer.set_cache.assert_called_once()
    
    def test_search_tasks_with_caching(self, repository, mock_optimizer):
        """Test search_tasks uses caching"""
        # Arrange
        mock_optimizer.get_from_cache.return_value = None
        
        # Mock parent class search_tasks
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.super') as mock_super:
            mock_tasks = [Mock(spec=TaskEntity)]
            mock_super().search_tasks.return_value = mock_tasks
            
            # Act
            result = repository.search_tasks("test query", limit=10)
            
            # Assert
            assert result == mock_tasks
            mock_optimizer.get_from_cache.assert_called_once()
            mock_optimizer.set_cache.assert_called_once()
    
    def test_invalidate_cache_specific_operation(self, repository, mock_optimizer):
        """Test invalidate_cache for specific operation"""
        # Arrange
        mock_optimizer._cache = {
            "list_tasks_key1": "value1",
            "list_tasks_key2": "value2",
            "search_tasks_key1": "value3",
            "task_count_key1": "value4"
        }
        
        # Act
        repository.invalidate_cache("list_tasks")
        
        # Assert
        assert "list_tasks_key1" not in mock_optimizer._cache
        assert "list_tasks_key2" not in mock_optimizer._cache
        assert "search_tasks_key1" in mock_optimizer._cache
        assert "task_count_key1" in mock_optimizer._cache
    
    def test_invalidate_cache_all(self, repository, mock_optimizer):
        """Test invalidate_cache clears all cache"""
        # Arrange
        mock_optimizer._cache = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        # Act
        repository.invalidate_cache()
        
        # Assert
        assert len(mock_optimizer._cache) == 0
    
    def test_create_task_invalidates_cache(self, repository):
        """Test create_task invalidates relevant caches"""
        # Arrange
        task = Mock(spec=TaskEntity)
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.super') as mock_super:
            mock_super().create_task.return_value = task
            
            with patch.object(repository, 'invalidate_cache') as mock_invalidate:
                # Act
                result = repository.create_task(task)
                
                # Assert
                assert result == task
                mock_invalidate.assert_any_call('list_tasks')
                mock_invalidate.assert_any_call('task_count')
                assert mock_invalidate.call_count == 2
    
    def test_update_task_invalidates_cache(self, repository):
        """Test update_task invalidates relevant caches"""
        # Arrange
        task = Mock(spec=TaskEntity)
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.super') as mock_super:
            mock_super().update_task.return_value = task
            
            with patch.object(repository, 'invalidate_cache') as mock_invalidate:
                # Act
                result = repository.update_task("task-123", status="done")
                
                # Assert
                assert result == task
                mock_invalidate.assert_any_call('list_tasks')
                mock_invalidate.assert_any_call('search_tasks')
                assert mock_invalidate.call_count == 2
    
    def test_delete_task_invalidates_cache(self, repository):
        """Test delete_task invalidates relevant caches"""
        # Arrange
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.super') as mock_super:
            mock_super().delete_task.return_value = True
            
            with patch.object(repository, 'invalidate_cache') as mock_invalidate:
                # Act
                result = repository.delete_task("task-123")
                
                # Assert
                assert result is True
                mock_invalidate.assert_any_call('list_tasks')
                mock_invalidate.assert_any_call('task_count')
                mock_invalidate.assert_any_call('search_tasks')
                assert mock_invalidate.call_count == 3
    
    def test_delete_task_no_invalidation_on_failure(self, repository):
        """Test delete_task doesn't invalidate cache on failure"""
        # Arrange
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.super') as mock_super:
            mock_super().delete_task.return_value = False
            
            with patch.object(repository, 'invalidate_cache') as mock_invalidate:
                # Act
                result = repository.delete_task("task-123")
                
                # Assert
                assert result is False
                mock_invalidate.assert_not_called()
    
    def test_git_branch_filter_applied(self, repository, mock_session):
        """Test that git_branch_id filter is correctly applied"""
        # Arrange
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session.query.return_value = mock_query
        
        # Act
        repository.list_tasks()
        
        # Assert
        # Verify filter was called with git_branch_id
        mock_query.filter.assert_called()
        filter_args = mock_query.filter.call_args[0]
        # The filter should include git_branch_id check
        assert any(hasattr(arg, 'left') and hasattr(arg.left, 'key') and arg.left.key == 'git_branch_id' 
                  for arg in filter_args if hasattr(arg, 'left'))
    
    def test_repository_initialization(self):
        """Test repository initialization with git_branch_id"""
        # Arrange & Act
        with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.get_performance_optimizer'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository.ORMTaskRepository.__init__') as mock_init:
                repo = OptimizedTaskRepository(git_branch_id="test-branch-123")
                
                # Assert
                mock_init.assert_called_once_with(session=None, git_branch_id="test-branch-123")