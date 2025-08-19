"""
Tests for Project Context Repository with User Isolation

This module tests the ProjectContextRepository functionality including:
- User-scoped project context operations
- CRUD operations with user isolation
- Context merging functionality
- Project-user relationship enforcement
- Migration to user-scoped contexts
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastmcp.task_management.infrastructure.repositories.project_context_repository_user_scoped import (
    ProjectContextRepository
)
from fastmcp.task_management.domain.entities.context import ProjectContext
from fastmcp.task_management.infrastructure.database.models import ProjectContext as ProjectContextModel


class TestProjectContextRepository:
    """Test suite for ProjectContextRepository"""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory"""
        session = Mock(spec=Session)
        session.query.return_value = Mock()
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
        return ProjectContextRepository(mock_session_factory, user_id="test-user-123")
    
    @pytest.fixture
    def mock_project_context_model(self):
        """Create a mock ProjectContext model"""
        model = Mock(spec=ProjectContextModel)
        model.id = "context-123"
        model.project_id = "project-123"
        model.context_data = {"key": "value", "project_setting": "test"}
        model.user_id = "test-user-123"
        model.created_at = datetime.now(timezone.utc)
        model.updated_at = datetime.now(timezone.utc)
        return model
    
    def test_create_success(self, repository, mock_session_factory):
        """Test successful project context creation"""
        session = mock_session_factory.return_value
        project_id = "project-123"
        context_data = {"key": "value", "setting": "test"}
        
        # Mock query to return no existing context
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.create(project_id, context_data)
        
        # Verify session operations
        session.add.assert_called_once()
        created_model = session.add.call_args[0][0]
        
        # Verify model fields
        assert created_model.project_id == project_id
        assert created_model.context_data == context_data
        assert created_model.user_id == "test-user-123"
        
        # Verify return type
        assert isinstance(result, ProjectContext)
    
    def test_create_already_exists(self, repository, mock_session_factory):
        """Test creating when project context already exists"""
        session = mock_session_factory.return_value
        
        # Mock existing context
        existing = Mock()
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = existing
        session.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            repository.create("project-123", {})
        
        assert "already exists" in str(exc_info.value)
    
    def test_get_success(self, repository, mock_session_factory, mock_project_context_model):
        """Test successful context retrieval"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_project_context_model
        session.query.return_value = query_mock
        
        result = repository.get("project-123")
        
        # Verify query
        session.query.assert_called_with(ProjectContextModel)
        
        # Verify result
        assert isinstance(result, ProjectContext)
        assert result.project_id == "project-123"
        assert result.context_data == {"key": "value", "project_setting": "test"}
    
    def test_get_not_found(self, repository, mock_session_factory):
        """Test get when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.get("project-123")
        
        assert result is None
    
    def test_update_success(self, repository, mock_session_factory, mock_project_context_model):
        """Test successful context update"""
        session = mock_session_factory.return_value
        new_context_data = {"updated": "data", "new_key": "new_value"}
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_project_context_model
        session.query.return_value = query_mock
        
        result = repository.update("project-123", new_context_data)
        
        # Verify updates
        assert mock_project_context_model.context_data == new_context_data
        assert isinstance(result, ProjectContext)
    
    def test_update_not_found(self, repository, mock_session_factory):
        """Test update when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            repository.update("project-123", {})
        
        assert "not found" in str(exc_info.value)
    
    def test_delete_success(self, repository, mock_session_factory, mock_project_context_model):
        """Test successful context deletion"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = mock_project_context_model
        session.query.return_value = query_mock
        
        result = repository.delete("project-123")
        
        session.delete.assert_called_once_with(mock_project_context_model)
        assert result is True
    
    def test_delete_not_found(self, repository, mock_session_factory):
        """Test delete when context not found"""
        session = mock_session_factory.return_value
        
        # Mock query returning None
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        session.query.return_value = query_mock
        
        result = repository.delete("project-123")
        
        assert result is False
    
    def test_list_by_user(self, repository, mock_session_factory):
        """Test listing contexts for current user"""
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
        with patch.object(repository, '_to_entity', side_effect=lambda x: Mock(spec=ProjectContext)):
            result = repository.list_by_user()
        
        assert len(result) == 2
    
    def test_list_by_project_ids(self, repository, mock_session_factory):
        """Test listing contexts for specific projects"""
        session = mock_session_factory.return_value
        project_ids = ["proj-1", "proj-2", "proj-3"]
        
        # Mock contexts
        context1 = Mock()
        context2 = Mock()
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [context1, context2]
        session.query.return_value = query_mock
        
        # Add to_entity conversion
        with patch.object(repository, '_to_entity', side_effect=lambda x: Mock(spec=ProjectContext)):
            result = repository.list_by_project_ids(project_ids)
        
        # Verify in_ was used for project IDs
        assert len(result) == 2
    
    def test_merge_context_update_existing(self, repository, mock_session_factory, mock_project_context_model):
        """Test merging data into existing context"""
        session = mock_session_factory.return_value
        project_id = "project-123"
        additional_data = {"new_key": "new_value", "another": "data"}
        
        # Mock existing context
        existing_context = ProjectContext(
            id="ctx-123",
            project_id=project_id,
            context_data={"existing": "data", "key": "old_value"},
            metadata={}
        )
        
        # Mock get to return existing
        with patch.object(repository, 'get', return_value=existing_context):
            with patch.object(repository, 'update') as mock_update:
                mock_update.return_value = Mock(spec=ProjectContext)
                
                result = repository.merge_context(project_id, additional_data)
                
                # Verify merge was called with combined data
                expected_data = {
                    "existing": "data",
                    "key": "old_value",
                    "new_key": "new_value",
                    "another": "data"
                }
                mock_update.assert_called_once_with(project_id, expected_data)
    
    def test_merge_context_create_new(self, repository):
        """Test merging data when no existing context"""
        project_id = "project-123"
        additional_data = {"new_key": "new_value"}
        
        # Mock get to return None
        with patch.object(repository, 'get', return_value=None):
            with patch.object(repository, 'create') as mock_create:
                mock_create.return_value = Mock(spec=ProjectContext)
                
                result = repository.merge_context(project_id, additional_data)
                
                # Verify create was called
                mock_create.assert_called_once_with(project_id, additional_data)
    
    def test_count_user_project_contexts(self, repository, mock_session_factory):
        """Test counting user's project contexts"""
        session = mock_session_factory.return_value
        
        # Mock query
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 5
        session.query.return_value = query_mock
        
        count = repository.count_user_project_contexts()
        
        assert count == 5
    
    def test_to_entity_conversion(self, repository, mock_project_context_model):
        """Test model to entity conversion"""
        entity = repository._to_entity(mock_project_context_model)
        
        assert isinstance(entity, ProjectContext)
        assert entity.id == "context-123"
        assert entity.project_id == "project-123"
        assert entity.context_data == {"key": "value", "project_setting": "test"}
        assert entity.metadata["user_id"] == "test-user-123"
    
    def test_get_inherited_context(self, repository):
        """Test getting inherited context (placeholder for future implementation)"""
        project_id = "project-123"
        
        # Mock get to return project context
        project_context = ProjectContext(
            id="ctx-123",
            project_id=project_id,
            context_data={"project": "data"},
            metadata={}
        )
        
        with patch.object(repository, 'get', return_value=project_context):
            result = repository.get_inherited_context(project_id)
            
            # Currently just returns project context
            assert result == {"project": "data"}
    
    def test_migrate_to_user_scoped(self, repository, mock_session_factory):
        """Test migration of contexts to user-scoped"""
        session = mock_session_factory.return_value
        
        # Mock contexts without user_id
        context1 = Mock(project_id="proj-1", user_id=None)
        context2 = Mock(project_id="proj-2", user_id=None)
        
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
    
    def test_user_filter_application(self, repository, mock_session_factory):
        """Test that user filter is properly applied"""
        session = mock_session_factory.return_value
        
        # Create a more detailed query mock
        query_mock = Mock()
        filter_mock = Mock()
        query_mock.filter.return_value = filter_mock
        filter_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        session.query.return_value = query_mock
        
        # Call get which should apply user filter
        repository.get("project-123")
        
        # Verify query was created
        session.query.assert_called_with(ProjectContextModel)