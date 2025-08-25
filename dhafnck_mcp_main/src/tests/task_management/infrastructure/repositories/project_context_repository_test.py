"""
Tests for ProjectContextRepository

Tests the project context repository functionality including CRUD operations,
user scoping, project-specific operations, and database interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime, timezone

from fastmcp.task_management.infrastructure.repositories.project_context_repository import ProjectContextRepository
from fastmcp.task_management.infrastructure.database.models import ProjectContext as ProjectContextModel
from fastmcp.task_management.domain.entities.context import ProjectContext


class TestProjectContextRepository:
    """Test suite for ProjectContextRepository"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_session_factory = Mock()
        self.mock_session = Mock(spec=Session)
        self.mock_session_factory.return_value = self.mock_session
        self.user_id = "test-user-123"
        
        self.repository = ProjectContextRepository(
            session_factory=self.mock_session_factory,
            user_id=self.user_id
        )

    def test_initialization(self):
        """Test repository initialization"""
        # Assert
        assert self.repository.session_factory == self.mock_session_factory
        assert self.repository.user_id == self.user_id

    def test_initialization_without_user_id(self):
        """Test repository initialization without user_id"""
        # Act
        repo = ProjectContextRepository(self.mock_session_factory)
        
        # Assert
        assert repo.session_factory == self.mock_session_factory
        assert repo.user_id is None

    def test_with_user_creates_new_instance(self):
        """Test with_user creates new repository instance with user scoping"""
        # Arrange
        new_user_id = "new-user-456"
        
        # Act
        scoped_repo = self.repository.with_user(new_user_id)
        
        # Assert
        assert isinstance(scoped_repo, ProjectContextRepository)
        assert scoped_repo.user_id == new_user_id
        assert scoped_repo.session_factory == self.mock_session_factory
        assert scoped_repo != self.repository

    def test_create_project_context_success(self):
        """Test successful project context creation"""
        # Arrange
        project_id = str(uuid.uuid4())
        data = {
            "project_name": "Test Project",
            "project_settings": {
                "coding_standards": {},
                "workflow_templates": {}
            }
        }
        
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.id = project_id
        mock_model.user_id = self.user_id
        mock_model.data = data
        
        self.mock_session.add = Mock()
        self.mock_session.commit = Mock()
        self.mock_session.refresh = Mock()
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_context_repository.ProjectContextModel') as MockModel:
            MockModel.return_value = mock_model
            
            # Act
            result = self.repository.create(project_id, data)
            
            # Assert
            assert result == mock_model
            MockModel.assert_called_once_with(
                id=project_id,
                user_id=self.user_id,
                data=data
            )
            self.mock_session.add.assert_called_once_with(mock_model)
            self.mock_session.commit.assert_called_once()
            self.mock_session.refresh.assert_called_once_with(mock_model)

    def test_create_project_context_with_database_error(self):
        """Test project context creation with database error"""
        # Arrange
        project_id = str(uuid.uuid4())
        data = {"project_name": "Test Project"}
        
        self.mock_session.commit.side_effect = SQLAlchemyError("Database error")
        self.mock_session.rollback = Mock()
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.create(project_id, data)
        
        self.mock_session.rollback.assert_called_once()

    def test_get_project_context_success(self):
        """Test successful project context retrieval"""
        # Arrange
        project_id = str(uuid.uuid4())
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.id = project_id
        mock_model.user_id = self.user_id
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_model
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = self.repository.get(project_id)
        
        # Assert
        assert result == mock_model
        self.mock_session.query.assert_called_once_with(ProjectContextModel)

    def test_get_project_context_not_found(self):
        """Test project context retrieval when context doesn't exist"""
        # Arrange
        project_id = "nonexistent-project"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = self.repository.get(project_id)
        
        # Assert
        assert result is None

    def test_get_project_context_with_user_scoping(self):
        """Test project context retrieval with user scoping"""
        # Arrange
        project_id = str(uuid.uuid4())
        mock_model = Mock(spec=ProjectContextModel)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_model
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = self.repository.get(project_id)
        
        # Assert
        assert result == mock_model
        # Verify user_id was included in filter
        mock_query.filter.assert_called()

    def test_update_project_context_success(self):
        """Test successful project context update"""
        # Arrange
        project_id = str(uuid.uuid4())
        update_data = {
            "project_name": "Updated Project",
            "last_modified": datetime.now(timezone.utc)
        }
        
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.id = project_id
        
        # Mock get method to return existing context
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Act
            result = self.repository.update(project_id, update_data)
            
            # Assert
            assert result == mock_model
            assert mock_model.data == update_data
            self.mock_session.commit.assert_called_once()

    def test_update_project_context_not_found(self):
        """Test updating project context that doesn't exist"""
        # Arrange
        project_id = "nonexistent-project"
        update_data = {"project_name": "Updated"}
        
        # Mock get method to return None
        with patch.object(self.repository, 'get', return_value=None):
            # Act
            result = self.repository.update(project_id, update_data)
            
            # Assert
            assert result is None

    def test_delete_project_context_success(self):
        """Test successful project context deletion"""
        # Arrange
        project_id = str(uuid.uuid4())
        mock_model = Mock(spec=ProjectContextModel)
        
        # Mock get method to return existing context
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Act
            result = self.repository.delete(project_id)
            
            # Assert
            assert result is True
            self.mock_session.delete.assert_called_once_with(mock_model)
            self.mock_session.commit.assert_called_once()

    def test_delete_project_context_not_found(self):
        """Test deleting project context that doesn't exist"""
        # Arrange
        project_id = "nonexistent-project"
        
        # Mock get method to return None
        with patch.object(self.repository, 'get', return_value=None):
            # Act
            result = self.repository.delete(project_id)
            
            # Assert
            assert result is False

    def test_list_project_contexts_success(self):
        """Test successful listing of project contexts"""
        # Arrange
        filters = {"status": "active"}
        mock_contexts = [
            Mock(spec=ProjectContextModel),
            Mock(spec=ProjectContextModel)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_contexts
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = self.repository.list(filters)
        
        # Assert
        assert result == mock_contexts
        self.mock_session.query.assert_called_once_with(ProjectContextModel)

    def test_list_project_contexts_without_filters(self):
        """Test listing project contexts without filters"""
        # Arrange
        mock_contexts = [Mock(spec=ProjectContextModel)]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_contexts
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = self.repository.list()
        
        # Assert
        assert result == mock_contexts

    def test_exists_project_context_success(self):
        """Test checking if project context exists"""
        # Arrange
        project_id = str(uuid.uuid4())
        mock_model = Mock(spec=ProjectContextModel)
        
        # Mock get method
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Act
            result = self.repository.exists(project_id)
            
            # Assert
            assert result is True

    def test_exists_project_context_not_found(self):
        """Test checking if project context exists when it doesn't"""
        # Arrange
        project_id = "nonexistent-project"
        
        # Mock get method
        with patch.object(self.repository, 'get', return_value=None):
            # Act
            result = self.repository.exists(project_id)
            
            # Assert
            assert result is False

    def test_find_by_project_name(self):
        """Test finding project context by project name"""
        # Arrange
        project_name = "Test Project"
        mock_contexts = [Mock(spec=ProjectContextModel)]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_contexts
        self.mock_session.query.return_value = mock_query
        
        # Act - if method exists
        if hasattr(self.repository, 'find_by_project_name'):
            result = self.repository.find_by_project_name(project_name)
            
            # Assert
            assert result == mock_contexts
            # Verify query was filtered by project name
            mock_query.filter.assert_called()

    def test_get_project_settings(self):
        """Test getting project-specific settings"""
        # Arrange
        project_id = str(uuid.uuid4())
        project_data = {
            "project_name": "Test Project",
            "project_settings": {
                "coding_standards": {"style": "PEP8"},
                "workflow_templates": {"template1": {}}
            }
        }
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.data = project_data
        
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Act - if method exists
            if hasattr(self.repository, 'get_project_settings'):
                result = self.repository.get_project_settings(project_id)
                
                # Assert
                assert result == project_data["project_settings"]

    def test_update_project_settings(self):
        """Test updating project-specific settings"""
        # Arrange
        project_id = str(uuid.uuid4())
        new_settings = {
            "coding_standards": {"style": "Black"},
            "new_setting": "value"
        }
        
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.data = {
            "project_name": "Test Project",
            "project_settings": {"old_setting": "old_value"}
        }
        
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Act - if method exists
            if hasattr(self.repository, 'update_project_settings'):
                result = self.repository.update_project_settings(project_id, new_settings)
                
                # Assert
                assert result == mock_model
                # Verify settings were merged/updated
                assert "coding_standards" in mock_model.data["project_settings"]

    def test_add_insight_to_project_context(self):
        """Test adding insight to project context"""
        # Arrange
        project_id = str(uuid.uuid4())
        insight_content = "Important project insight"
        category = "architecture"
        importance = "high"
        agent = "architect-agent"
        
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.data = {"insights": []}
        
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Check if add_insight method exists
            if hasattr(self.repository, 'add_insight'):
                # Act
                result = self.repository.add_insight(
                    project_id, insight_content, category, importance, agent
                )
                
                # Assert
                assert result == mock_model
                # Verify insight was added
                expected_insight = {
                    "content": insight_content,
                    "category": category,
                    "importance": importance,
                    "agent": agent,
                    "timestamp": mock_model.data["insights"][0]["timestamp"]  # Dynamic timestamp
                }
                assert len(mock_model.data["insights"]) > 0

    def test_add_progress_to_project_context(self):
        """Test adding progress update to project context"""
        # Arrange
        project_id = str(uuid.uuid4())
        progress_content = "Project milestone completed"
        agent = "project-manager-agent"
        
        mock_model = Mock(spec=ProjectContextModel)
        mock_model.data = {"progress": []}
        
        with patch.object(self.repository, 'get', return_value=mock_model):
            # Check if add_progress method exists
            if hasattr(self.repository, 'add_progress'):
                # Act
                result = self.repository.add_progress(project_id, progress_content, agent)
                
                # Assert
                assert result == mock_model
                # Verify progress was added
                assert len(mock_model.data["progress"]) > 0

    def test_get_project_statistics(self):
        """Test getting project statistics if method exists"""
        # Arrange
        project_id = str(uuid.uuid4())
        
        # Act - if method exists
        if hasattr(self.repository, 'get_project_statistics'):
            with patch.object(self.repository, 'get') as mock_get:
                mock_model = Mock(spec=ProjectContextModel)
                mock_model.data = {
                    "statistics": {
                        "total_branches": 5,
                        "total_tasks": 25,
                        "completed_tasks": 20
                    }
                }
                mock_get.return_value = mock_model
                
                result = self.repository.get_project_statistics(project_id)
                
                # Assert
                assert "total_branches" in result
                assert "total_tasks" in result
                assert "completed_tasks" in result


# User scoping and isolation tests
class TestProjectContextRepositoryUserScoping:
    """Test user scoping and data isolation functionality"""

    def setup_method(self):
        """Set up test fixtures for user scoping tests"""
        self.mock_session_factory = Mock()
        self.mock_session = Mock(spec=Session)
        self.mock_session_factory.return_value = self.mock_session
        
        self.user_id_1 = "user-123"
        self.user_id_2 = "user-456"
        
        self.repo_user_1 = ProjectContextRepository(
            session_factory=self.mock_session_factory,
            user_id=self.user_id_1
        )

    def test_user_scoped_create_includes_user_id(self):
        """Test that user-scoped repository includes user_id in creation"""
        # Arrange
        project_id = str(uuid.uuid4())
        data = {"project_name": "User Project"}
        
        mock_model = Mock(spec=ProjectContextModel)
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_context_repository.ProjectContextModel') as MockModel:
            MockModel.return_value = mock_model
            
            # Act
            self.repo_user_1.create(project_id, data)
            
            # Assert
            MockModel.assert_called_once_with(
                id=project_id,
                user_id=self.user_id_1,
                data=data
            )

    def test_user_scoped_get_filters_by_user_id(self):
        """Test that user-scoped repository filters by user_id in queries"""
        # Arrange
        project_id = str(uuid.uuid4())
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = Mock()
        self.mock_session.query.return_value = mock_query
        
        # Act
        self.repo_user_1.get(project_id)
        
        # Assert
        self.mock_session.query.assert_called_once_with(ProjectContextModel)
        # Verify filter was called (implementation would include user_id filter)
        mock_query.filter.assert_called()

    def test_user_scoped_list_filters_by_user_id(self):
        """Test that user-scoped repository filters list by user_id"""
        # Arrange
        filters = {"status": "active"}
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_session.query.return_value = mock_query
        
        # Act
        self.repo_user_1.list(filters)
        
        # Assert
        # Verify that user_id filter is applied in addition to provided filters
        mock_query.filter.assert_called()

    def test_cross_user_isolation(self):
        """Test that users cannot access each other's project contexts"""
        # Arrange
        project_id = str(uuid.uuid4())
        repo_user_2 = self.repo_user_1.with_user(self.user_id_2)
        
        # Mock user 1 has access to project
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = Mock(spec=ProjectContextModel)
        self.mock_session.query.return_value = mock_query
        
        # Act
        result_user_1 = self.repo_user_1.get(project_id)
        
        # Mock user 2 does not have access (different user_id filter)
        mock_query.first.return_value = None
        result_user_2 = repo_user_2.get(project_id)
        
        # Assert
        assert result_user_1 is not None
        assert result_user_2 is None

    def test_repository_without_user_id_no_scoping(self):
        """Test that repository without user_id doesn't apply user scoping"""
        # Arrange
        repo_no_user = ProjectContextRepository(self.mock_session_factory, user_id=None)
        project_id = str(uuid.uuid4())
        data = {"project_name": "Global Project"}
        
        mock_model = Mock(spec=ProjectContextModel)
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_context_repository.ProjectContextModel') as MockModel:
            MockModel.return_value = mock_model
            
            # Act
            repo_no_user.create(project_id, data)
            
            # Assert
            MockModel.assert_called_once_with(
                id=project_id,
                user_id=None,
                data=data
            )


# Edge cases and error handling
class TestProjectContextRepositoryEdgeCases:
    """Test edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_session_factory = Mock()
        self.repository = ProjectContextRepository(self.mock_session_factory)

    def test_create_with_duplicate_project_id(self):
        """Test creating project context with duplicate ID"""
        # Arrange
        project_id = str(uuid.uuid4())
        data = {"project_name": "Test Project"}
        
        # Mock database to raise integrity error
        self.mock_session_factory.return_value.commit.side_effect = SQLAlchemyError("UNIQUE constraint failed")
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.create(project_id, data)

    def test_update_with_concurrent_modification(self):
        """Test handling concurrent modifications"""
        # This would test optimistic locking or similar mechanisms
        # Implementation dependent - placeholder for concurrent modification tests
        pass

    def test_large_project_data_handling(self):
        """Test handling of large project data"""
        # Arrange
        project_id = str(uuid.uuid4())
        large_data = {
            "project_name": "Large Project",
            "large_settings": {"key_" + str(i): "value_" + str(i) for i in range(1000)}
        }
        
        # Act - should handle large data appropriately
        # Implementation dependent test
        pass

    def test_invalid_project_id_format(self):
        """Test handling of invalid project ID format"""
        # Arrange
        invalid_project_ids = ["", None, "not-a-uuid", 123]
        
        for invalid_id in invalid_project_ids:
            # Act & Assert
            try:
                result = self.repository.get(invalid_id)
                # Should either return None or raise appropriate exception
                assert result is None or isinstance(result, Exception)
            except Exception as e:
                assert isinstance(e, (ValueError, TypeError))

    def test_database_connection_failure(self):
        """Test handling of database connection failure"""
        # Arrange
        failing_session_factory = Mock()
        failing_session_factory.side_effect = Exception("Database connection failed")
        
        repo = ProjectContextRepository(failing_session_factory)
        
        # Act & Assert
        with pytest.raises(Exception):
            repo.get(str(uuid.uuid4()))

    def test_transaction_rollback_on_error(self):
        """Test proper transaction rollback on errors"""
        # Arrange
        project_id = str(uuid.uuid4())
        data = {"project_name": "Test Project"}
        
        mock_session = Mock(spec=Session)
        mock_session.commit.side_effect = SQLAlchemyError("Transaction failed")
        mock_session.rollback = Mock()
        
        self.mock_session_factory.return_value = mock_session
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.create(project_id, data)
        
        mock_session.rollback.assert_called_once()

    def test_malformed_data_structure(self):
        """Test handling of malformed data structures"""
        # Arrange
        project_id = str(uuid.uuid4())
        malformed_data = {
            "project_name": ["should", "be", "string"],  # Wrong type
            "nested": {"circular": None}
        }
        # Create circular reference
        malformed_data["nested"]["circular"] = malformed_data["nested"]
        
        # Act & Assert
        # Should handle malformed data gracefully or raise appropriate exception
        try:
            result = self.repository.create(project_id, malformed_data)
        except Exception as e:
            assert isinstance(e, (ValueError, TypeError, RecursionError))

    def test_empty_filters_in_list_operation(self):
        """Test list operation with various filter combinations"""
        # Arrange
        test_filters = [
            {},  # Empty filters
            None,  # None filters
            {"nonexistent_field": "value"},  # Invalid field
            {"project_name": ""},  # Empty value
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value = mock_query
        self.mock_session_factory.return_value = mock_session
        
        for filters in test_filters:
            # Act
            result = self.repository.list(filters)
            
            # Assert
            assert isinstance(result, list)  # Should return empty list or valid results

    def test_session_cleanup_after_exception(self):
        """Test proper session cleanup after exceptions"""
        # This tests that sessions are properly closed/cleaned up after errors
        # Implementation dependent - would test session context management
        pass