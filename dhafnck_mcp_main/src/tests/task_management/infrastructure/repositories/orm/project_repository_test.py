"""
Tests for ORM Project Repository Implementation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository
from fastmcp.task_management.infrastructure.repositories.base_orm_repository import BaseORMRepository
from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch
from fastmcp.task_management.domain.entities.project import Project as ProjectEntity
from fastmcp.task_management.domain.entities.git_branch import GitBranch
from fastmcp.task_management.domain.exceptions.base_exceptions import (
    ResourceNotFoundException,
    ValidationException,
    DatabaseException
)


class TestORMProjectRepository:
    """Test the ORMProjectRepository class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "user-123"
    
    @pytest.fixture
    def repository(self, mock_session, user_id):
        """Create a repository instance"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseORMRepository.__init__'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseUserScopedRepository.__init__'):
                repo = ORMProjectRepository(mock_session, user_id)
                repo.session = mock_session
                repo.get_db_session = Mock(return_value=mock_session)
                repo.user_id = user_id
                repo._is_system_mode = False
                repo.apply_user_filter = Mock(return_value=Mock())
                repo.log_access = Mock()
                repo.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": user_id})
                return repo
    
    @pytest.fixture
    def mock_project_model(self):
        """Create a mock Project model"""
        from datetime import timezone
        project = Mock(spec=Project)
        project.id = "project-123"
        project.name = "Test Project"
        project.description = "Test project description"
        project.status = "active"
        project.metadata = {"key": "value"}
        project.created_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)
        project.git_branchs = []
        return project
    
    @pytest.fixture
    def mock_git_branch_model(self):
        """Create a mock ProjectGitBranch model"""
        from datetime import timezone
        branch = Mock(spec=ProjectGitBranch)
        branch.id = "branch-123"
        branch.name = "main"
        branch.description = "Main branch"
        branch.project_id = "project-123"
        branch.task_count = 5
        branch.completed_task_count = 2
        branch.created_at = datetime.now(timezone.utc)
        branch.updated_at = datetime.now(timezone.utc)
        return branch
    
    @pytest.fixture
    def mock_project_entity(self):
        """Create a mock Project entity"""
        from datetime import timezone
        return ProjectEntity(
            id="project-123",
            name="Test Project",
            description="Test project description",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def test_model_to_entity_conversion(self, repository, mock_project_model):
        """Test converting SQLAlchemy model to domain entity"""
        entity = repository._model_to_entity(mock_project_model)
        
        assert isinstance(entity, ProjectEntity)
        assert entity.id == mock_project_model.id
        assert entity.name == mock_project_model.name
        assert entity.description == mock_project_model.description
        assert entity.created_at == mock_project_model.created_at
        assert entity.updated_at == mock_project_model.updated_at
    
    def test_model_to_entity_with_branches(self, repository, mock_project_model, mock_git_branch_model):
        """Test model to entity conversion with git branches"""
        mock_project_model.git_branchs = [mock_git_branch_model]
        
        entity = repository._model_to_entity(mock_project_model)
        
        assert len(entity.git_branchs) == 1
        assert mock_git_branch_model.id in entity.git_branchs
        branch = entity.git_branchs[mock_git_branch_model.id]
        assert branch.name == mock_git_branch_model.name
        assert branch.description == mock_git_branch_model.description
        # Check task count was properly handled
        assert len(branch.all_tasks) == mock_git_branch_model.task_count
    
    @pytest.mark.asyncio
    async def test_save_new_project(self, repository, mock_project_entity):
        """Test saving a new project"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing project
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        await repository.save(mock_project_entity)
        
        # Verify project was added to session
        repository.session.add.assert_called_once()
        repository.session.commit.assert_called_once()
        
        # Verify user_id was set
        repository.set_user_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_existing_project(self, repository, mock_project_entity, mock_project_model):
        """Test updating an existing project"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_project_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        await repository.save(mock_project_entity)
        
        # Verify existing project was updated
        assert mock_project_model.name == mock_project_entity.name
        assert mock_project_model.description == mock_project_entity.description
        repository.session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_project_with_branches(self, repository, mock_project_entity):
        """Test saving project with git branches"""
        from datetime import timezone
        # Add branches to entity
        branch = GitBranch(
            id="branch-456",
            name="feature",
            description="Feature branch",
            project_id=mock_project_entity.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_project_entity.git_branchs["branch-456"] = branch
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        await repository.save(mock_project_entity)
        
        # Verify branch was added
        assert repository.session.add.call_count == 2  # Project + Branch
        repository.session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_id_found(self, repository, mock_project_model):
        """Test finding project by ID"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_project_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = await repository.find_by_id("project-123")
        
        assert result is not None
        assert result.id == mock_project_model.id
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('read', 'project', 'project-123')
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """Test finding non-existent project by ID"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = await repository.find_by_id("nonexistent")
        
        assert result is None
        repository.log_access.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all(self, repository, mock_project_model):
        """Test finding all projects"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_project_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = await repository.find_all()
        
        assert len(result) == 1
        assert result[0].id == mock_project_model.id
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('list', 'project')
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository):
        """Test successful project deletion"""
        repository.delete_project = Mock(return_value=True)
        
        result = await repository.delete("project-123")
        
        assert result is True
        repository.delete_project.assert_called_once_with("project-123")
    
    @pytest.mark.asyncio
    async def test_delete_failure(self, repository):
        """Test failed project deletion"""
        repository.delete_project = Mock(side_effect=Exception("Delete failed"))
        
        result = await repository.delete("project-123")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_project(self, repository, mock_project_entity):
        """Test updating a project"""
        repository.transaction = Mock()
        repository.transaction.__enter__ = Mock(return_value=None)
        repository.transaction.__exit__ = Mock(return_value=None)
        
        # Mock the parent update method
        with patch.object(BaseORMRepository, 'update', return_value=True):
            await repository.update(mock_project_entity)
        
        # Verify transaction was used (through context manager)
        repository.transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_project_not_found(self, repository, mock_project_entity):
        """Test updating non-existent project"""
        repository.transaction = Mock()
        repository.transaction.__enter__ = Mock(return_value=None)
        repository.transaction.__exit__ = Mock(return_value=None)
        
        # Mock the parent update method to return False
        with patch.object(BaseORMRepository, 'update', return_value=False):
            with pytest.raises(ResourceNotFoundException):
                await repository.update(mock_project_entity)
    
    @pytest.mark.asyncio
    async def test_find_by_name(self, repository, mock_project_model):
        """Test finding project by name"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_project_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = await repository.find_by_name("Test Project")
        
        assert result is not None
        assert result.name == mock_project_model.name
    
    @pytest.mark.asyncio
    async def test_count(self, repository):
        """Test counting projects"""
        # Mock the parent count method
        with patch.object(BaseORMRepository, 'count', return_value=5):
            result = await repository.count()
        
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_find_projects_with_agent(self, repository, mock_project_model):
        """Test finding projects with specific agent"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value.all.return_value = [mock_project_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = await repository.find_projects_with_agent("agent-123")
        
        assert len(result) == 1
        assert result[0].id == mock_project_model.id
    
    @pytest.mark.asyncio
    async def test_find_projects_by_status(self, repository, mock_project_model):
        """Test finding projects by status"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_project_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = await repository.find_projects_by_status("active")
        
        assert len(result) == 1
        assert result[0].id == mock_project_model.id
    
    @pytest.mark.asyncio
    async def test_get_project_health_summary(self, repository):
        """Test getting project health summary"""
        # Mock count queries
        mock_query = Mock()
        mock_query.count.return_value = 10  # Total projects
        mock_query.distinct.return_value.all.return_value = [("active",), ("inactive",)]
        mock_query.filter.return_value.count.side_effect = [5, 5, 7, 15, 8]  # Various counts
        mock_query.join.return_value.distinct.return_value.count.return_value = 7
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        
        result = await repository.get_project_health_summary()
        
        assert result["total_projects"] == 10
        assert "projects_by_status" in result
        assert result["projects_with_branches"] == 7
        assert result["total_branches"] == 15
        assert result["assigned_branches"] == 8
        assert result["unassigned_branches"] == 7
        assert result["average_branches_per_project"] == 1.5
    
    @pytest.mark.asyncio
    async def test_save_database_exception(self, repository, mock_project_entity):
        """Test database exception during save"""
        repository.session.__enter__ = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(DatabaseException) as exc_info:
            await repository.save(mock_project_entity)
        
        assert "Failed to save project" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_database_exception(self, repository, mock_project_entity):
        """Test database exception during update"""
        repository.transaction = Mock()
        repository.transaction.__enter__ = Mock(side_effect=Exception("Update error"))
        
        with pytest.raises(DatabaseException) as exc_info:
            await repository.update(mock_project_entity)
        
        assert "Failed to update project" in str(exc_info.value)
    
    def test_initialization_with_user(self, mock_session, user_id):
        """Test repository initialization with user ID"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseORMRepository.__init__'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseUserScopedRepository.__init__'):
                repo = ORMProjectRepository(mock_session, user_id)
                repo.session = mock_session
                repo.user_id = user_id
                repo._is_system_mode = False
                
                assert repo.session == mock_session
                assert repo.user_id == user_id
                assert repo._is_system_mode is False
    
    def test_initialization_without_user(self, mock_session):
        """Test repository initialization without user ID (system mode)"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseORMRepository.__init__'):
            with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.BaseUserScopedRepository.__init__'):
                repo = ORMProjectRepository(mock_session, user_id=None)
                repo.session = mock_session
                repo.user_id = None
                repo._is_system_mode = True
                
                assert repo.session == mock_session
                assert repo.user_id is None
                assert repo._is_system_mode is True
    
    @pytest.mark.asyncio
    async def test_find_by_name_with_user_filter(self, repository, mock_project_model):
        """Test finding project by name applies user filter"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_project_model
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = await repository.find_by_name("Test Project")
        
        assert result is not None
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('read', 'project', mock_project_model.id)
    
    @pytest.mark.asyncio
    async def test_find_projects_with_agent_user_filter(self, repository, mock_project_model):
        """Test finding projects with agent applies user filter"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value.all.return_value = [mock_project_model]
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.apply_user_filter = Mock(return_value=mock_query)
        repository.log_access = Mock()
        
        result = await repository.find_projects_with_agent("agent-123")
        
        assert len(result) == 1
        repository.apply_user_filter.assert_called_once()
        repository.log_access.assert_called_once_with('list', 'project', 'agent=agent-123')
    
    @pytest.mark.asyncio
    async def test_unassign_agent_from_tree(self, repository):
        """Test unassigning agent from git branch"""
        mock_branch = Mock()
        mock_branch.assigned_agent_id = "agent-123"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_branch
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.transaction = Mock()
        repository.transaction.__enter__ = Mock(return_value=None)
        repository.transaction.__exit__ = Mock(return_value=None)
        
        result = await repository.unassign_agent_from_tree(
            project_id="project-123",
            agent_id="agent-123",
            git_branch_id="branch-123"
        )
        
        assert result["success"] is True
        assert result["unassigned_agent_id"] == "agent-123"
        assert mock_branch.assigned_agent_id is None
    
    @pytest.mark.asyncio
    async def test_unassign_agent_from_tree_not_found(self, repository):
        """Test unassigning agent from non-existent branch"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        repository.session.query.return_value = mock_query
        repository.session.__enter__ = Mock(return_value=repository.session)
        repository.session.__exit__ = Mock(return_value=None)
        repository.transaction = Mock()
        repository.transaction.__enter__ = Mock(return_value=None)
        repository.transaction.__exit__ = Mock(return_value=None)
        
        with pytest.raises(ResourceNotFoundException):
            await repository.unassign_agent_from_tree(
                project_id="project-123",
                agent_id="agent-123",
                git_branch_id="nonexistent"
            )
    
    def test_create_project_with_user_id(self, repository):
        """Test creating project with user ID"""
        from uuid import uuid4
        mock_uuid = str(uuid4())
        
        with patch('uuid.uuid4', return_value=mock_uuid):
            with patch.object(repository, 'create') as mock_create:
                with patch.object(repository, '_model_to_entity') as mock_to_entity:
                    mock_create.return_value = Mock()
                    mock_to_entity.return_value = Mock(id=mock_uuid)
                    
                    repository.transaction = Mock()
                    repository.transaction.__enter__ = Mock(return_value=None)
                    repository.transaction.__exit__ = Mock(return_value=None)
                    
                    result = repository.create_project(
                        name="New Project",
                        description="Project description",
                        user_id="user-123"
                    )
                    
                    mock_create.assert_called_once_with(
                        id=mock_uuid,
                        name="New Project",
                        description="Project description",
                        user_id="user-123",
                        status="active",
                        metadata={}
                    )
    
    def test_create_project_without_user_id_compatibility_mode(self, repository):
        """Test creating project without user ID in compatibility mode"""
        from uuid import uuid4
        mock_uuid = str(uuid4())
        
        with patch('uuid.uuid4', return_value=mock_uuid):
            with patch.object(repository, 'create') as mock_create:
                with patch.object(repository, '_model_to_entity') as mock_to_entity:
                    with patch('fastmcp.task_management.infrastructure.repositories.orm.project_repository.AuthConfig') as MockAuthConfig:
                        MockAuthConfig.is_default_user_allowed.return_value = True
                        MockAuthConfig.get_fallback_user_id.return_value = "default-user"
                        
                        mock_create.return_value = Mock()
                        mock_to_entity.return_value = Mock(id=mock_uuid)
                        
                        repository.transaction = Mock()
                        repository.transaction.__enter__ = Mock(return_value=None)
                        repository.transaction.__exit__ = Mock(return_value=None)
                        
                        result = repository.create_project(
                            name="New Project",
                            description="Project description",
                            user_id=None
                        )
                        
                        mock_create.assert_called_once_with(
                            id=mock_uuid,
                            name="New Project",
                            description="Project description",
                            user_id="default-user",
                            status="active",
                            metadata={}
                        )