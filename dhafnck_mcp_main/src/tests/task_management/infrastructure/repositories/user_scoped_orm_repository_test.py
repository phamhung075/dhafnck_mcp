"""
Tests for User-Scoped ORM Repository

This module tests the UserScopedORMRepository functionality including:
- Combined ORM and user-scoped functionality
- CRUD operations with automatic user isolation
- Bulk operations with user filtering
- Query filtering and user context enforcement
- Repository inheritance behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.user_scoped_orm_repository import (
    UserScopedORMRepository
)


class MockModel:
    """Mock SQLAlchemy model for testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestUserScopedORMRepository:
    """Test suite for UserScopedORMRepository"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = Mock(spec=Session)
        session.query.return_value = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.delete = Mock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create repository instance"""
        return UserScopedORMRepository(MockModel, session=mock_session, user_id="test-user-123")
    
    @pytest.fixture
    def mock_model_instance(self):
        """Create a mock model instance"""
        return MockModel(id="model-123", user_id="test-user-123", name="Test Model")
    
    def test_get_by_id_with_user_filter(self, repository, mock_session, mock_model_instance):
        """Test getting model by ID with user isolation"""
        # Mock query chain
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_model_instance
        mock_session.query.return_value = query_mock
        
        result = repository.get_by_id("model-123")
        
        # Verify user filter was applied
        mock_session.query.assert_called_with(MockModel)
        assert result == mock_model_instance
    
    def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting non-existent model"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        mock_session.query.return_value = query_mock
        
        result = repository.get_by_id("non-existent")
        
        assert result is None
    
    def test_get_all_with_pagination(self, repository, mock_session):
        """Test getting all models with pagination and user filter"""
        models = [
            MockModel(id=f"model-{i}", user_id="test-user-123")
            for i in range(5)
        ]
        
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.offset.return_value = filter_mock
        filter_mock.limit.return_value = filter_mock
        filter_mock.all.return_value = models[1:3]  # Simulate pagination
        mock_session.query.return_value = query_mock
        
        result = repository.get_all(limit=2, offset=1)
        
        # Verify pagination was applied
        filter_mock.offset.assert_called_once_with(1)
        filter_mock.limit.assert_called_once_with(2)
        assert len(result) == 2
    
    def test_create_with_user_id_injection(self, repository, mock_session):
        """Test creating model with automatic user_id injection"""
        # Mock the parent create method
        with patch('fastmcp.task_management.infrastructure.repositories.base_orm_repository.BaseORMRepository.create') as mock_create:
            mock_model = MockModel(id="new-123", user_id="test-user-123", name="New Model")
            mock_create.return_value = mock_model
            
            result = repository.create(name="New Model")
            
            # Verify user_id was added
            create_args = mock_create.call_args[1]
            assert 'user_id' in create_args
            assert create_args['user_id'] == "test-user-123"
    
    def test_update_with_user_ownership(self, repository, mock_session, mock_model_instance):
        """Test updating model with user ownership verification"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_model_instance
        mock_session.query.return_value = query_mock
        
        result = repository.update("model-123", name="Updated Name")
        
        # Verify model was updated
        assert mock_model_instance.name == "Updated Name"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_model_instance)
    
    def test_update_prevents_user_id_change(self, repository, mock_session, mock_model_instance):
        """Test that update prevents changing user_id"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_model_instance
        mock_session.query.return_value = query_mock
        
        # Try to update with different user_id
        result = repository.update("model-123", name="Updated", user_id="different-user")
        
        # Verify user_id wasn't changed
        assert mock_model_instance.user_id == "test-user-123"
    
    def test_delete_with_user_ownership(self, repository, mock_session, mock_model_instance):
        """Test deleting model with user ownership verification"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_model_instance
        mock_session.query.return_value = query_mock
        
        result = repository.delete("model-123")
        
        mock_session.delete.assert_called_once_with(mock_model_instance)
        mock_session.commit.assert_called_once()
        assert result is True
    
    def test_delete_not_found(self, repository, mock_session):
        """Test deleting non-existent model"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        mock_session.query.return_value = query_mock
        
        result = repository.delete("non-existent")
        
        mock_session.delete.assert_not_called()
        assert result is False
    
    def test_find_by_with_user_filter(self, repository, mock_session):
        """Test finding models by criteria with user filter"""
        models = [
            MockModel(id="1", user_id="test-user-123", status="active"),
            MockModel(id="2", user_id="test-user-123", status="active")
        ]
        
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.all.return_value = models
        mock_session.query.return_value = query_mock
        
        result = repository.find_by(status="active")
        
        assert len(result) == 2
    
    def test_find_one_by_with_user_filter(self, repository, mock_session, mock_model_instance):
        """Test finding one model by criteria with user filter"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = mock_model_instance
        mock_session.query.return_value = query_mock
        
        result = repository.find_one_by(name="Test Model")
        
        assert result == mock_model_instance
    
    def test_count_with_filters(self, repository, mock_session):
        """Test counting models with filters and user isolation"""
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 5
        mock_session.query.return_value = query_mock
        
        count = repository.count(status="active")
        
        assert count == 5
    
    def test_exists(self, repository):
        """Test checking if model exists"""
        with patch.object(repository, 'count', return_value=1):
            assert repository.exists(name="Test") is True
        
        with patch.object(repository, 'count', return_value=0):
            assert repository.exists(name="Test") is False
    
    def test_bulk_create_with_user_isolation(self, repository, mock_session):
        """Test bulk creating models with user_id injection"""
        records = [
            {"name": "Model 1"},
            {"name": "Model 2"},
            {"name": "Model 3"}
        ]
        
        # Mock parent bulk_create
        with patch('fastmcp.task_management.infrastructure.repositories.base_orm_repository.BaseORMRepository.bulk_create') as mock_bulk:
            mock_models = [MockModel(id=f"{i}", user_id="test-user-123") for i in range(3)]
            mock_bulk.return_value = mock_models
            
            result = repository.bulk_create(records)
            
            # Verify user_id was added to all records
            processed_records = mock_bulk.call_args[0][0]
            for record in processed_records:
                assert record['user_id'] == "test-user-123"
            
            assert len(result) == 3
    
    def test_bulk_update_with_user_filter(self, repository, mock_session):
        """Test bulk updating models with user filter"""
        ids = ["1", "2", "3"]
        updates = {"status": "inactive", "user_id": "different-user"}  # Try to change user_id
        
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.update.return_value = 2
        mock_session.query.return_value = query_mock
        
        count = repository.bulk_update(ids, updates)
        
        # Verify user_id was removed from updates
        actual_updates = filter_mock.update.call_args[0][0]
        assert 'user_id' not in actual_updates
        assert actual_updates['status'] == "inactive"
        
        assert count == 2
    
    def test_bulk_delete_with_user_filter(self, repository, mock_session):
        """Test bulk deleting models with user filter"""
        ids = ["1", "2", "3"]
        
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.count.return_value = 2
        filter_mock.delete.return_value = None
        mock_session.query.return_value = query_mock
        
        count = repository.bulk_delete(ids)
        
        # Verify delete was called
        filter_mock.delete.assert_called_once_with(synchronize_session=False)
        mock_session.commit.assert_called_once()
        assert count == 2
    
    def test_log_access_tracking(self, repository, mock_session):
        """Test that access is logged for audit"""
        # Create a model with mocked log_access
        with patch.object(repository, 'log_access') as mock_log:
            query_mock = Mock()
            filter_mock = Mock()
            query_mock.filter.return_value = filter_mock
            filter_mock.filter.return_value = filter_mock
            filter_mock.first.return_value = Mock(id="123")
            mock_session.query.return_value = query_mock
            
            repository.get_by_id("123")
            
            mock_log.assert_called_once_with('read', 'MockModel', '123')
    
    def test_inheritance_behavior(self, repository):
        """Test that repository properly inherits from both base classes"""
        # Check it has methods from BaseORMRepository
        assert hasattr(repository, 'get_db_session')
        assert hasattr(repository, 'model_class')
        
        # Check it has methods from BaseUserScopedRepository
        assert hasattr(repository, 'apply_user_filter')
        assert hasattr(repository, 'ensure_user_ownership')
        assert hasattr(repository, 'user_id')
        assert repository.user_id == "test-user-123"
    
    def test_get_db_session_context_manager(self, repository):
        """Test get_db_session context manager"""
        with repository.get_db_session() as session:
            assert session is not None
    
    def test_repository_without_user_id(self, mock_session):
        """Test repository behavior without user_id (system mode)"""
        repo = UserScopedORMRepository(MockModel, session=mock_session, user_id=None)
        
        # In system mode, should still work but without user filtering
        assert repo.user_id is None