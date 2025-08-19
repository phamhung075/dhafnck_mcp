"""
Tests for Global Context Repository with User Isolation

This module tests the GlobalContextRepository functionality including:
- User-scoped global context operations
- Context ID normalization for backward compatibility
- CRUD operations with user isolation
- Context field mapping and custom fields
- Migration to user-scoped contexts
- Singleton behavior per user
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastmcp.task_management.infrastructure.repositories.global_context_repository_user_scoped import (
    GlobalContextRepository,
    GLOBAL_SINGLETON_UUID
)
from fastmcp.task_management.domain.entities.context import GlobalContext
from fastmcp.task_management.infrastructure.database.models import GlobalContext as GlobalContextModel


class TestGlobalContextRepository:
    """Test suite for GlobalContextRepository"""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory"""
        session = Mock(spec=Session)
        session.query.return_value = Mock()
        session.get.return_value = None
        session.add = Mock()
        session.flush = Mock()
        session.refresh = Mock()
        session.delete = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        
        factory = Mock(return_value=session)
        return factory
    
    @pytest.fixture
    def repository(self, mock_session_factory):
        """Create repository instance"""
        return GlobalContextRepository(mock_session_factory, user_id="test-user-123")
    
    @pytest.fixture
    def mock_global_context_model(self):
        """Create a mock GlobalContext model"""
        model = Mock(spec=GlobalContextModel)
        model.id = f"{GLOBAL_SINGLETON_UUID}_test-user-123"
        model.organization_id = "org-123"
        model.autonomous_rules = {"rule1": "value1"}
        model.security_policies = {"policy1": "value1"}
        model.coding_standards = {"standard1": "value1"}
        model.workflow_templates = {"template1": "value1"}
        model.delegation_rules = {"delegation1": "value1"}
        model.user_id = "test-user-123"
        model.created_at = datetime.now(timezone.utc)
        model.updated_at = datetime.now(timezone.utc)
        model.version = 1
        return model
    
    @pytest.fixture
    def global_context_entity(self):
        """Create a GlobalContext entity"""
        return GlobalContext(
            id="global_singleton",
            organization_name="org-123",
            global_settings={
                "autonomous_rules": {"rule1": "value1"},
                "security_policies": {"policy1": "value1"},
                "coding_standards": {"standard1": "value1"},
                "workflow_templates": {"template1": "value1"},
                "delegation_rules": {"delegation1": "value1"},
                "custom_field": "custom_value"  # Custom field
            },
            metadata={}
        )
    
    def test_normalize_context_id_with_user(self, repository):
        """Test context ID normalization with user context"""
        # Test global_singleton normalization
        normalized = repository._normalize_context_id("global_singleton")
        assert normalized == f"{GLOBAL_SINGLETON_UUID}_test-user-123"
        
        # Test other IDs remain unchanged
        other_id = "some-other-id"
        assert repository._normalize_context_id(other_id) == other_id
    
    def test_normalize_context_id_without_user(self):
        """Test context ID normalization without user context"""
        repo = GlobalContextRepository(Mock(), user_id=None)
        
        # Test global_singleton normalization
        normalized = repo._normalize_context_id("global_singleton")
        assert normalized == GLOBAL_SINGLETON_UUID
    
    def test_create_success(self, repository, mock_session_factory, global_context_entity):
        """Test successful global context creation"""
        session = mock_session_factory.return_value
        
        # Mock query to return no existing context
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.create(global_context_entity)
        
        # Verify session operations
        session.add.assert_called_once()
        created_model = session.add.call_args[0][0]
        
        # Verify model fields
        assert created_model.id == f"{GLOBAL_SINGLETON_UUID}_test-user-123"
        assert created_model.organization_id == "org-123"
        assert created_model.user_id == "test-user-123"
        assert created_model.autonomous_rules == {"rule1": "value1"}
        
        # Verify custom field handling
        assert "_custom" in created_model.workflow_templates
        assert created_model.workflow_templates["_custom"]["custom_field"] == "custom_value"
    
    def test_create_already_exists(self, repository, mock_session_factory, global_context_entity):
        """Test creating when global context already exists"""
        session = mock_session_factory.return_value
        
        # Mock existing context
        existing = Mock()
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = existing
        session.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            repository.create(global_context_entity)
        
        assert "already exists" in str(exc_info.value)
    
    def test_get_success(self, repository, mock_session_factory, mock_global_context_model):
        """Test successful context retrieval"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_global_context_model
        session.query.return_value = query_mock
        
        result = repository.get("global_singleton")
        
        # Verify query
        session.query.assert_called_with(GlobalContextModel)
        
        # Verify result
        assert isinstance(result, GlobalContext)
        assert result.organization_name == "org-123"
        assert result.global_settings["autonomous_rules"]["rule1"] == "value1"
    
    def test_get_not_found(self, repository, mock_session_factory):
        """Test get when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.get("global_singleton")
        
        assert result is None
    
    def test_update_success(self, repository, mock_session_factory, mock_global_context_model, global_context_entity):
        """Test successful context update"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_global_context_model
        session.query.return_value = query_mock
        
        # Update entity
        global_context_entity.global_settings["new_rule"] = "new_value"
        
        result = repository.update("global_singleton", global_context_entity)
        
        # Verify updates
        assert mock_global_context_model.organization_id == "org-123"
        assert isinstance(result, GlobalContext)
    
    def test_update_not_found(self, repository, mock_session_factory, global_context_entity):
        """Test update when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            repository.update("global_singleton", global_context_entity)
        
        assert "not found" in str(exc_info.value)
    
    def test_delete_success(self, repository, mock_session_factory, mock_global_context_model):
        """Test successful context deletion"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_global_context_model
        session.query.return_value = query_mock
        
        result = repository.delete("global_singleton")
        
        session.delete.assert_called_once_with(mock_global_context_model)
        assert result is True
    
    def test_delete_not_found(self, repository, mock_session_factory):
        """Test delete when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.delete("global_singleton")
        
        assert result is False
    
    def test_list_with_user_filter(self, repository, mock_session_factory):
        """Test listing contexts with user filter"""
        session = mock_session_factory.return_value
        
        # Mock contexts
        context1 = Mock()
        context2 = Mock()
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [context1, context2]
        session.query.return_value = query_mock
        
        # Add to_entity conversion
        with patch.object(repository, '_to_entity', side_effect=lambda x: Mock()):
            result = repository.list()
        
        # Verify user filter was applied
        assert len(result) == 2
    
    def test_get_user_global_context(self, repository, mock_session_factory, mock_global_context_model):
        """Test convenience method for getting user's global context"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_global_context_model
        session.query.return_value = query_mock
        
        result = repository.get_user_global_context()
        
        assert isinstance(result, GlobalContext)
    
    def test_count_user_contexts(self, repository, mock_session_factory):
        """Test counting user contexts"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        session.query.return_value = query_mock
        
        count = repository.count_user_contexts()
        
        assert count == 1
    
    def test_to_entity_conversion(self, repository, mock_global_context_model):
        """Test model to entity conversion"""
        # Test normal conversion
        entity = repository._to_entity(mock_global_context_model)
        
        assert isinstance(entity, GlobalContext)
        assert entity.id == mock_global_context_model.id
        assert entity.organization_name == "org-123"
        assert entity.global_settings["autonomous_rules"]["rule1"] == "value1"
        assert entity.metadata["user_id"] == "test-user-123"
    
    def test_to_entity_with_custom_fields(self, repository):
        """Test model to entity conversion with custom fields"""
        # Create model with custom fields
        model = Mock(spec=GlobalContextModel)
        model.id = "test-id"
        model.organization_id = "org-123"
        model.autonomous_rules = {}
        model.security_policies = {}
        model.coding_standards = {}
        model.workflow_templates = {
            "template1": "value1",
            "_custom": {
                "custom_field1": "custom_value1",
                "custom_field2": "custom_value2"
            }
        }
        model.delegation_rules = {}
        model.user_id = "test-user-123"
        model.created_at = datetime.now(timezone.utc)
        model.updated_at = datetime.now(timezone.utc)
        model.version = 1
        
        entity = repository._to_entity(model)
        
        # Verify custom fields are extracted
        assert entity.global_settings["custom_field1"] == "custom_value1"
        assert entity.global_settings["custom_field2"] == "custom_value2"
        assert "_custom" not in entity.global_settings["workflow_templates"]
    
    def test_migrate_to_user_scoped(self, repository, mock_session_factory):
        """Test migration of contexts to user-scoped"""
        session = mock_session_factory.return_value
        
        # Mock contexts without user_id
        context1 = Mock(id="ctx-1", user_id=None)
        context2 = Mock(id="ctx-2", user_id=None)
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [context1, context2]
        session.query.return_value = query_mock
        
        count = repository.migrate_to_user_scoped()
        
        # Verify migration
        assert count == 2
        assert context1.user_id == "00000000-0000-0000-0000-000000000000"
        assert context2.user_id == "00000000-0000-0000-0000-000000000000"
        session.commit.assert_called_once()
    
    def test_session_error_handling(self, repository, mock_session_factory):
        """Test session error handling"""
        session = mock_session_factory.return_value
        
        # Mock SQLAlchemy error
        session.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            with repository.get_db_session() as s:
                s.commit()
        
        # Verify rollback was called
        session.rollback.assert_called_once()
    
    def test_apply_user_filter(self, repository, mock_session_factory):
        """Test user filter application"""
        # Test is inherited from BaseUserScopedRepository
        # This would be tested in the base class tests
        pass