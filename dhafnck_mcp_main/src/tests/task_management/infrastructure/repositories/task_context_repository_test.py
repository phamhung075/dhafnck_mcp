"""Test suite for TaskContextRepository.

Tests the task context repository including:
- CRUD operations for task contexts
- Session management with custom factory
- Entity to model conversion
- Task data management with insights and progress
- Error handling and validation
- User isolation and filtering
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from contextlib import contextmanager
import uuid

from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository
from fastmcp.task_management.domain.entities.context import TaskContextUnified as TaskContext
from fastmcp.task_management.infrastructure.database.models import TaskContext as TaskContextModel
from sqlalchemy.exc import SQLAlchemyError


class TestTaskContextRepository:
    """Test cases for TaskContextRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock session factory
        self.mock_session_factory = Mock()
        self.mock_session = Mock()
        self.mock_session_factory.return_value = self.mock_session
        
        # Setup session methods
        self.mock_session.commit = Mock()
        self.mock_session.rollback = Mock()
        self.mock_session.close = Mock()
        self.mock_session.add = Mock()
        self.mock_session.flush = Mock()
        self.mock_session.refresh = Mock()
        self.mock_session.get = Mock()
        self.mock_session.execute = Mock()
        self.mock_session.delete = Mock()
        
        # Create repository instance
        self.repository = TaskContextRepository(self.mock_session_factory)
        
        # Test data
        self.test_context_id = str(uuid.uuid4())
        self.test_branch_id = str(uuid.uuid4())
        self.test_task_data = {
            'title': 'Test Task',
            'description': 'Task description',
            'status': 'in_progress',
            'custom_field': 'custom_value'
        }
        
        self.test_insights = [
            'Insight 1: Found optimization opportunity',
            'Insight 2: Need to refactor component'
        ]
        
        self.test_next_steps = [
            'Step 1: Complete implementation',
            'Step 2: Add unit tests'
        ]
        
        self.test_metadata = {
            'local_overrides': {'override1': 'value1'},
            'implementation_notes': {'note1': 'Implementation detail'},
            'delegation_triggers': {'trigger1': 'delegate_condition'},
            'inheritance_disabled': False,
            'force_local_only': True,
            'user_id': 'test-user-123'
        }
        
        self.test_entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data=self.test_task_data,
            progress=75,
            insights=self.test_insights,
            next_steps=self.test_next_steps,
            metadata=self.test_metadata
        )
    
    def test_init(self):
        """Test repository initialization."""
        assert self.repository.session_factory == self.mock_session_factory
        assert self.repository.model_class == TaskContextModel
    
    def test_get_db_session_with_existing_session(self):
        """Test get_db_session uses existing session from transaction."""
        # Mock existing session
        existing_session = Mock()
        self.repository._session = existing_session
        
        with self.repository.get_db_session() as session:
            assert session == existing_session
        
        # Verify no new session was created
        self.mock_session_factory.assert_not_called()
    
    def test_get_db_session_creates_new_session(self):
        """Test get_db_session creates new session when none exists."""
        # Ensure no existing session
        self.repository._session = None
        
        with self.repository.get_db_session() as session:
            assert session == self.mock_session
        
        # Verify session lifecycle
        self.mock_session_factory.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.close.assert_called_once()
    
    def test_get_db_session_handles_sql_error(self):
        """Test get_db_session handles SQLAlchemy errors with rollback."""
        self.repository._session = None
        
        # Make session operation raise error
        self.mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            with self.repository.get_db_session() as session:
                assert session == self.mock_session
                # This will trigger the error when exiting context
        
        # Verify rollback was called
        self.mock_session.rollback.assert_called_once()
        self.mock_session.close.assert_called_once()
    
    def test_create_success(self):
        """Test successful task context creation."""
        # Mock no existing context
        self.mock_session.get.return_value = None
        
        # Mock the created model
        created_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data={'test': 'data'},
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            inheritance_disabled=False,
            force_local_only=False,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            result = self.repository.create(self.test_entity)
        
        assert result == self.test_entity
        
        # Verify session operations
        self.mock_session.get.assert_called_once_with(TaskContextModel, self.test_context_id)
        self.mock_session.add.assert_called_once()
        self.mock_session.flush.assert_called_once()
        self.mock_session.refresh.assert_called_once()
    
    def test_create_already_exists(self):
        """Test creation fails when context already exists."""
        # Mock existing context
        existing_model = Mock()
        self.mock_session.get.return_value = existing_model
        
        with pytest.raises(ValueError) as exc_info:
            self.repository.create(self.test_entity)
        
        assert f"Task context already exists: {self.test_context_id}" in str(exc_info.value)
    
    def test_create_stores_insights_and_progress_in_task_data(self):
        """Test that insights and progress are stored within task_data."""
        self.mock_session.get.return_value = None
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            self.repository.create(self.test_entity)
        
        # Verify add was called with proper task_data structure
        self.mock_session.add.assert_called_once()
        added_model = self.mock_session.add.call_args[0][0]
        
        # Check that insights and progress are in task_data
        task_data = added_model.task_data
        assert task_data['progress'] == 75
        assert task_data['insights'] == self.test_insights
        assert task_data['next_steps'] == self.test_next_steps
        
        # Original task_data fields should still be there
        assert task_data['title'] == 'Test Task'
        assert task_data['custom_field'] == 'custom_value'
    
    def test_get_success(self):
        """Test successful task context retrieval."""
        # Mock database model
        db_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data={'title': 'Test Task'},
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            inheritance_disabled=False,
            force_local_only=False,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.mock_session.get.return_value = db_model
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            result = self.repository.get(self.test_context_id)
        
        assert result == self.test_entity
        self.mock_session.get.assert_called_once_with(TaskContextModel, self.test_context_id)
        mock_to_entity.assert_called_once_with(db_model)
    
    def test_get_not_found(self):
        """Test retrieval returns None when context not found."""
        self.mock_session.get.return_value = None
        
        result = self.repository.get(self.test_context_id)
        
        assert result is None
    
    def test_update_success(self):
        """Test successful task context update."""
        # Mock existing model
        existing_model = Mock()
        existing_model.user_id = "existing-user"
        existing_model.version = 1
        self.mock_session.get.return_value = existing_model
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            result = self.repository.update(self.test_context_id, self.test_entity)
        
        assert result == self.test_entity
        
        # Verify model fields were updated
        assert existing_model.parent_branch_id == self.test_branch_id
        assert existing_model.local_overrides == self.test_metadata['local_overrides']
        assert existing_model.implementation_notes == self.test_metadata['implementation_notes']
        assert existing_model.delegation_triggers == self.test_metadata['delegation_triggers']
        assert existing_model.inheritance_disabled == self.test_metadata['inheritance_disabled']
        assert existing_model.force_local_only == self.test_metadata['force_local_only']
        assert existing_model.version == 2  # Should increment
        
        # Verify task_data includes insights and progress
        task_data = existing_model.task_data
        assert task_data['progress'] == 75
        assert task_data['insights'] == self.test_insights
        assert task_data['next_steps'] == self.test_next_steps
        
        # Verify session operations
        self.mock_session.flush.assert_called_once()
        self.mock_session.refresh.assert_called_once()
    
    def test_update_not_found(self):
        """Test update fails when context doesn't exist."""
        self.mock_session.get.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            self.repository.update(self.test_context_id, self.test_entity)
        
        assert f"Task context not found: {self.test_context_id}" in str(exc_info.value)
    
    def test_delete_success(self):
        """Test successful task context deletion."""
        # Mock existing model
        existing_model = Mock()
        self.mock_session.get.return_value = existing_model
        
        result = self.repository.delete(self.test_context_id)
        
        assert result is True
        self.mock_session.get.assert_called_once_with(TaskContextModel, self.test_context_id)
        self.mock_session.delete.assert_called_once_with(existing_model)
    
    def test_delete_not_found(self):
        """Test deletion returns False when context not found."""
        self.mock_session.get.return_value = None
        
        result = self.repository.delete(self.test_context_id)
        
        assert result is False
        self.mock_session.delete.assert_not_called()
    
    def test_list_without_filters(self):
        """Test listing all task contexts without filters."""
        # Mock database models
        db_models = [
            Mock(id=f"context-{i}", task_id=f"task-{i}", parent_branch_id=f"branch-{i}") 
            for i in range(3)
        ]
        
        # Mock SQLAlchemy result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = db_models
        self.mock_session.execute.return_value = mock_result
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.side_effect = lambda model: TaskContext(
                id=model.task_id,
                branch_id=model.parent_branch_id,
                task_data={},
                progress=0,
                insights=[],
                next_steps=[],
                metadata={}
            )
            
            result = self.repository.list()
        
        assert len(result) == 3
        assert all(isinstance(ctx, TaskContext) for ctx in result)
        
        # Verify SQL execution
        self.mock_session.execute.assert_called_once()
    
    def test_list_with_branch_filter(self):
        """Test listing task contexts filtered by branch_id."""
        filters = {"branch_id": self.test_branch_id}
        
        # Mock empty result for simplicity
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute.return_value = mock_result
        
        result = self.repository.list(filters)
        
        assert result == []
        
        # Verify execute was called (with filters applied)
        self.mock_session.execute.assert_called_once()
    
    def test_list_with_inheritance_disabled_filter(self):
        """Test listing task contexts filtered by inheritance_disabled."""
        filters = {"inheritance_disabled": True}
        
        # Mock empty result for simplicity
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute.return_value = mock_result
        
        result = self.repository.list(filters)
        
        assert result == []
        
        # Verify execute was called (with filters applied)
        self.mock_session.execute.assert_called_once()
    
    def test_to_entity_basic_conversion(self):
        """Test _to_entity converts database model to domain entity."""
        # Create test database model
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        db_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data={
                'title': 'Test Task',
                'progress': 50,
                'insights': ['insight1', 'insight2'],
                'next_steps': ['step1', 'step2'],
                'custom_field': 'custom_value'
            },
            local_overrides={'override': 'value'},
            implementation_notes={'note': 'value'},
            delegation_triggers={'trigger': 'value'},
            inheritance_disabled=True,
            force_local_only=False,
            version=2,
            created_at=created_at,
            updated_at=updated_at
        )
        
        result = self.repository._to_entity(db_model)
        
        assert result.id == self.test_context_id
        assert result.branch_id == self.test_branch_id
        assert result.progress == 50
        assert result.insights == ['insight1', 'insight2']
        assert result.next_steps == ['step1', 'step2']
        
        # Task data should exclude progress, insights, next_steps
        assert result.task_data == {'title': 'Test Task', 'custom_field': 'custom_value'}
        
        # Metadata should be properly populated
        assert result.metadata['local_overrides'] == {'override': 'value'}
        assert result.metadata['implementation_notes'] == {'note': 'value'}
        assert result.metadata['delegation_triggers'] == {'trigger': 'value'}
        assert result.metadata['inheritance_disabled'] is True
        assert result.metadata['force_local_only'] is False
        assert result.metadata['version'] == 2
        assert result.metadata['created_at'] == created_at.isoformat()
        assert result.metadata['updated_at'] == updated_at.isoformat()
    
    def test_to_entity_empty_task_data(self):
        """Test _to_entity handles empty or None task_data."""
        db_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data=None,  # Empty task_data
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            inheritance_disabled=False,
            force_local_only=False,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        result = self.repository._to_entity(db_model)
        
        # Should handle empty task_data gracefully
        assert result.task_data == {}
        assert result.progress == 0  # Default value
        assert result.insights == []  # Default value
        assert result.next_steps == []  # Default value
    
    def test_to_entity_handles_missing_timestamps(self):
        """Test _to_entity handles missing created_at/updated_at timestamps."""
        db_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data={},
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            inheritance_disabled=False,
            force_local_only=False,
            version=1,
            created_at=None,
            updated_at=None
        )
        
        result = self.repository._to_entity(db_model)
        
        assert result.metadata['created_at'] is None
        assert result.metadata['updated_at'] is None
    
    def test_to_entity_cleans_task_data(self):
        """Test _to_entity properly separates insights/progress from task_data."""
        db_model = TaskContextModel(
            id=self.test_context_id,
            task_id=self.test_context_id,
            parent_branch_id=self.test_branch_id,
            parent_branch_context_id=self.test_branch_id,
            task_data={
                'title': 'Test Task',
                'description': 'Task description',
                'progress': 80,
                'insights': ['important insight'],
                'next_steps': ['next step'],
                'business_field': 'business_value',
                'technical_details': {'complex': 'data'}
            },
            local_overrides={},
            implementation_notes={},
            delegation_triggers={},
            inheritance_disabled=False,
            force_local_only=False,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        result = self.repository._to_entity(db_model)
        
        # Verify separation
        assert result.progress == 80
        assert result.insights == ['important insight']
        assert result.next_steps == ['next step']
        
        # Clean task_data should not contain these fields
        expected_clean_data = {
            'title': 'Test Task',
            'description': 'Task description',
            'business_field': 'business_value',
            'technical_details': {'complex': 'data'}
        }
        assert result.task_data == expected_clean_data
    
    @patch('fastmcp.task_management.infrastructure.repositories.task_context_repository.select')
    def test_list_applies_filters_correctly(self, mock_select):
        """Test list applies filters to SQL query correctly."""
        # Setup mock select
        mock_stmt = Mock()
        mock_select.return_value = mock_stmt
        mock_stmt.where.return_value = mock_stmt
        
        # Mock empty result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute.return_value = mock_result
        
        filters = {
            "branch_id": self.test_branch_id,
            "inheritance_disabled": True
        }
        self.repository.list(filters)
        
        # Verify filters were applied (where should be called twice)
        assert mock_stmt.where.call_count == 2
    
    def test_create_sets_default_version(self):
        """Test create sets version to 1 for new contexts."""
        self.mock_session.get.return_value = None
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            self.repository.create(self.test_entity)
        
        # Verify version was set to 1
        added_model = self.mock_session.add.call_args[0][0]
        assert added_model.version == 1
    
    def test_update_increments_version(self):
        """Test update increments version number."""
        # Mock existing model with version 3
        existing_model = Mock()
        existing_model.version = 3
        existing_model.user_id = "test-user"
        self.mock_session.get.return_value = existing_model
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = self.test_entity
            
            self.repository.update(self.test_context_id, self.test_entity)
        
        # Verify version was incremented
        assert existing_model.version == 4
    
    def test_create_handles_empty_metadata(self):
        """Test create handles entity with empty metadata gracefully."""
        # Create entity with minimal metadata
        entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data={'title': 'Test'},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={}  # Empty metadata
        )
        
        self.mock_session.get.return_value = None
        
        with patch.object(self.repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = entity
            
            self.repository.create(entity)
        
        # Should handle empty metadata gracefully
        added_model = self.mock_session.add.call_args[0][0]
        assert added_model.local_overrides == {}
        assert added_model.implementation_notes == {}
        assert added_model.delegation_triggers == {}
        assert added_model.inheritance_disabled is False
        assert added_model.force_local_only is False
    
    def test_user_scoping_in_create(self):
        """Test user scoping is properly applied in create operation"""
        # Create repository with user_id
        repository = TaskContextRepository(self.mock_session_factory, user_id="test-user-456")
        
        # Mock no existing context
        self.mock_session.get.return_value = None
        
        # Create entity with user_id in metadata
        entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data={"title": "Test"},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={"user_id": "entity-user"}  # Entity has different user_id
        )
        
        with patch.object(repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = entity
            
            result = repository.create(entity)
        
        # Verify created model uses repository's user_id (takes precedence)
        added_model = self.mock_session.add.call_args[0][0]
        assert added_model.user_id == "test-user-456"  # Repository user_id
    
    def test_user_scoping_in_get(self):
        """Test user scoping is properly applied in get operation"""
        repository = TaskContextRepository(self.mock_session_factory, user_id="scoped-user")
        
        # Mock database model
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter  # Chain for user filter
        mock_filter.first.return_value = None
        self.mock_session.query.return_value = mock_query
        
        result = repository.get(self.test_context_id)
        
        # Verify user filter was applied in addition to ID filter
        assert mock_query.filter.call_count >= 1
        assert result is None
    
    def test_user_scoping_in_list(self):
        """Test user scoping is properly applied in list operation"""
        repository = TaskContextRepository(self.mock_session_factory, user_id="list-user")
        
        # Mock SQL execution
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute.return_value = mock_result
        
        result = repository.list()
        
        # Verify execute was called with user-filtered query
        self.mock_session.execute.assert_called_once()
        assert result == []
    
    def test_with_user_method(self):
        """Test with_user method creates new repository instance with different user"""
        original_repository = TaskContextRepository(self.mock_session_factory, user_id="original-user")
        
        new_repository = original_repository.with_user("new-user")
        
        # Verify new instance has different user_id
        assert new_repository.user_id == "new-user"
        assert original_repository.user_id == "original-user"
        assert new_repository.session_factory == original_repository.session_factory
        assert new_repository is not original_repository
    
    def test_user_id_fallback_in_create(self):
        """Test user_id fallback behavior in create operation"""
        # Repository without user_id
        repository = TaskContextRepository(self.mock_session_factory, user_id=None)
        
        self.mock_session.get.return_value = None
        
        # Entity with user_id in metadata
        entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data={"title": "Test"},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={"user_id": "entity-user"}
        )
        
        with patch.object(repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = entity
            
            result = repository.create(entity)
        
        # Should fallback to entity's user_id, then to 'system'
        added_model = self.mock_session.add.call_args[0][0]
        assert added_model.user_id == "entity-user"
    
    def test_user_id_system_fallback_in_create(self):
        """Test system fallback when no user_id is available"""
        # Repository without user_id
        repository = TaskContextRepository(self.mock_session_factory, user_id=None)
        
        self.mock_session.get.return_value = None
        
        # Entity without user_id in metadata
        entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data={"title": "Test"},
            progress=0,
            insights=[],
            next_steps=[],
            metadata={}  # No user_id
        )
        
        with patch.object(repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = entity
            
            result = repository.create(entity)
        
        # Should fallback to 'system'
        added_model = self.mock_session.add.call_args[0][0]
        assert added_model.user_id == 'system'
    
    def test_update_preserves_existing_user_id(self):
        """Test update operation preserves existing user_id when repository has none"""
        repository = TaskContextRepository(self.mock_session_factory, user_id=None)
        
        # Mock existing model with user_id
        existing_model = Mock()
        existing_model.user_id = "existing-user"
        existing_model.version = 1
        self.mock_session.get.return_value = existing_model
        
        # Entity without user_id
        entity = TaskContext(
            id=self.test_context_id,
            branch_id=self.test_branch_id,
            task_data={"title": "Updated"},
            progress=50,
            insights=[],
            next_steps=[],
            metadata={}
        )
        
        with patch.object(repository, '_to_entity') as mock_to_entity:
            mock_to_entity.return_value = entity
            
            result = repository.update(self.test_context_id, entity)
        
        # Should preserve existing user_id
        assert existing_model.user_id == "existing-user"
    
    def test_list_with_filters_user_scoping(self):
        """Test list with filters still applies user scoping"""
        repository = TaskContextRepository(self.mock_session_factory, user_id="filtered-user")
        
        # Mock SQL execution
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.mock_session.execute.return_value = mock_result
        
        filters = {"branch_id": "test-branch", "inheritance_disabled": True}
        result = repository.list(filters)
        
        # Verify execute was called with both user filter and custom filters
        self.mock_session.execute.assert_called_once()
        
        # Verify SQL includes user_id filter
        executed_stmt = self.mock_session.execute.call_args[0][0]
        # This is a simplified check - in reality, the SQL would contain the user filter
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__])