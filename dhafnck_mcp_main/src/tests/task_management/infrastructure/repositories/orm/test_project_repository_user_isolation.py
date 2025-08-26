"""
Test ProjectRepository with user isolation.
Following TDD - these tests define expected behavior for user-scoped projects.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ProjectRepository
from fastmcp.task_management.infrastructure.database.models import Project as ProjectORM
from fastmcp.task_management.domain.entities.project import Project as ProjectEntity


class TestProjectRepositoryUserIsolation:
    """Test suite for ProjectRepository with user isolation."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return str(uuid4())
    
    @pytest.fixture
    def other_user_id(self):
        """Generate another user ID for cross-user testing."""
        return str(uuid4())
    
    @pytest.fixture
    def repository(self, mock_session, user_id):
        """Create a ProjectRepository instance with user_id."""
        return ProjectRepository(session=mock_session, user_id=user_id)
    
    # ==================== Constructor Tests ====================
    
    def test_repository_requires_user_id(self, mock_session):
        """Test that ProjectRepository requires user_id."""
        with pytest.raises(TypeError):
            ProjectRepository(session=mock_session)
    
    def test_repository_stores_user_id(self, repository, user_id):
        """Test that repository stores the provided user_id."""
        assert repository.user_id == user_id
    
    # ==================== Create Tests ====================
    
    def test_create_project_adds_user_id(self, repository, mock_session, user_id):
        """Test that creating a project automatically adds user_id."""
        project_data = {
            "name": "Test Project",
            "description": "Test Description",
            "status": "active"
        }
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existing project
        
        # Create project
        project = repository.create(project_data)
        
        # Verify session.add was called
        mock_session.add.assert_called_once()
        added_project = mock_session.add.call_args[0][0]
        
        # Verify user_id was set
        assert hasattr(added_project, 'user_id')
        assert added_project.user_id == user_id
    
    def test_create_prevents_user_id_override(self, repository, mock_session, user_id, other_user_id):
        """Test that users cannot override user_id when creating projects."""
        project_data = {
            "name": "Test Project",
            "description": "Test Description",
            "user_id": other_user_id  # Try to override
        }
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Create project
        project = repository.create(project_data)
        
        # Verify the correct user_id was used
        added_project = mock_session.add.call_args[0][0]
        assert added_project.user_id == user_id
        assert added_project.user_id != other_user_id
    
    # ==================== Read Tests ====================
    
    def test_get_by_id_filters_by_user(self, repository, mock_session, user_id):
        """Test that get_by_id includes user_id in filter."""
        project_id = str(uuid4())
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Get project by ID
        repository.get_by_id(project_id)
        
        # Verify filter was called with both id and user_id
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert project_id in filter_args
        assert user_id in filter_args
    
    def test_get_all_returns_only_user_projects(self, repository, mock_session, user_id):
        """Test that get_all only returns projects for the user."""
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Get all projects
        projects = repository.get_all()
        
        # Verify filter was called with user_id
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert user_id in filter_args
        assert "user_id" in filter_args
    
    def test_search_filters_by_user(self, repository, mock_session, user_id):
        """Test that search operations include user_id filter."""
        search_params = {"name": "Test", "status": "active"}
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Search projects
        repository.search(search_params)
        
        # Verify user_id was included in filters
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert user_id in filter_args
        assert "user_id" in filter_args
    
    # ==================== Update Tests ====================
    
    def test_update_only_affects_user_projects(self, repository, mock_session, user_id):
        """Test that updates only affect user's projects."""
        project_id = str(uuid4())
        update_data = {"description": "Updated description"}
        
        # Create a mock project that belongs to the user
        mock_project = Mock(spec=ProjectORM)
        mock_project.id = project_id
        mock_project.user_id = user_id
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        
        # Update project
        repository.update(project_id, update_data)
        
        # Verify filter included user_id
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert project_id in filter_args
        assert user_id in filter_args
    
    def test_update_prevents_changing_user_id(self, repository, mock_session, user_id, other_user_id):
        """Test that updates cannot change the user_id."""
        project_id = str(uuid4())
        update_data = {
            "description": "Updated",
            "user_id": other_user_id  # Try to change user_id
        }
        
        # Create a mock project
        mock_project = Mock(spec=ProjectORM)
        mock_project.id = project_id
        mock_project.user_id = user_id
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        
        # Update project
        repository.update(project_id, update_data)
        
        # Verify user_id wasn't changed
        assert mock_project.user_id == user_id
        assert mock_project.user_id != other_user_id
    
    # ==================== Delete Tests ====================
    
    def test_delete_only_affects_user_projects(self, repository, mock_session, user_id):
        """Test that delete only affects user's projects."""
        project_id = str(uuid4())
        
        # Create a mock project
        mock_project = Mock(spec=ProjectORM)
        mock_project.id = project_id
        mock_project.user_id = user_id
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        
        # Delete project
        repository.delete(project_id)
        
        # Verify filter included user_id
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert project_id in filter_args
        assert user_id in filter_args
    
    # ==================== Cross-User Isolation Tests ====================
    
    def test_user_cannot_access_other_user_projects(self, mock_session, user_id, other_user_id):
        """Test that users cannot access each other's projects."""
        # Create two repositories for different users
        user1_repo = ProjectRepository(session=mock_session, user_id=user_id)
        user2_repo = ProjectRepository(session=mock_session, user_id=other_user_id)
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # User 1 gets all projects
        user1_repo.get_all()
        user1_filter_args = str(mock_query.filter.call_args_list)
        
        # Reset mock
        mock_query.filter.reset_mock()
        
        # User 2 gets all projects
        user2_repo.get_all()
        user2_filter_args = str(mock_query.filter.call_args_list)
        
        # Verify different user_ids were used
        assert user_id in user1_filter_args
        assert other_user_id not in user1_filter_args
        
        assert other_user_id in user2_filter_args
        assert user_id not in user2_filter_args
    
    def test_get_by_id_returns_none_for_other_user_project(self, repository, mock_session, user_id):
        """Test that get_by_id returns None for another user's project."""
        project_id = str(uuid4())
        
        # Mock the query chain to return None (not found for this user)
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # Try to get project
        result = repository.get_by_id(project_id)
        
        # Should return None
        assert result is None
        
        # Verify user_id was in the filter
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        assert user_id in filter_args
    
    # ==================== Relationship Tests ====================
    
    def test_project_with_git_branches_filters_by_user(self, repository, mock_session, user_id):
        """Test that project with git branches respects user boundaries."""
        # Mock the query chain with joins
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = []
        
        # Get projects with git branches
        repository.get_projects_with_branches()
        
        # Verify user_id filter was applied
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert user_id in filter_args
        assert "user_id" in filter_args
    
    def test_project_task_count_only_counts_user_tasks(self, repository, mock_session, user_id):
        """Test that task counts only include user's tasks."""
        project_id = str(uuid4())
        
        # Mock the query chain for count
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        # Get task count
        count = repository.get_project_task_count(project_id)
        
        # Verify both project_id and user_id were in filter
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert project_id in filter_args
        assert user_id in filter_args
        assert count == 5
    
    # ==================== Special Cases ====================
    
    def test_system_user_can_access_system_projects(self, mock_session):
        """Test that system user can access system projects."""
        system_user_id = "00000000-0000-0000-0000-000000000000"
        repository = ProjectRepository(session=mock_session, user_id=system_user_id)
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Get all projects as system user
        repository.get_all()
        
        # Verify system user_id was used
        filter_calls = mock_query.filter.call_args_list
        filter_args = str(filter_calls)
        
        assert system_user_id in filter_args
    
    def test_handles_null_user_id_in_legacy_data(self, repository, mock_session, user_id):
        """Test handling of legacy data without user_id."""
        # This test documents how to handle migration scenarios
        # where existing data might not have user_id yet
        
        # Mock a project without user_id (legacy data)
        mock_project = Mock(spec=ProjectORM)
        mock_project.id = str(uuid4())
        mock_project.user_id = None  # Legacy data
        
        # Mock the query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        
        # Try to get the project
        result = repository.get_by_id(mock_project.id)
        
        # Should return None since it doesn't belong to the user
        assert result is None or mock_project.user_id == user_id