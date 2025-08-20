"""
Tests for Project Management Service

This module tests the ProjectManagementService functionality including:
- Project CRUD operations (create, get, list, update, delete)
- User-scoped service creation
- Project health checks and maintenance operations
- Error handling and validation scenarios
- Integration with use cases and repository layer
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastmcp.task_management.application.services.project_management_service import ProjectManagementService
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.repositories.project_repository import ProjectRepository


class TestProjectManagementService:
    """Test suite for ProjectManagementService"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        repo = Mock(spec=ProjectRepository)
        repo.find_by_id = AsyncMock()
        repo.find_by_name = AsyncMock()
        repo.save = AsyncMock()
        repo.delete = AsyncMock()
        return repo
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @pytest.fixture
    def service_with_user(self, mock_project_repository):
        """Create service instance with user context"""
        return ProjectManagementService(project_repo=mock_project_repository, user_id="user-123")
    
    @pytest.fixture
    def mock_project_entity(self):
        """Create a mock project entity"""
        project = Mock(spec=Project)
        project.id = "project-123"
        project.name = "Test Project"
        project.description = "Test Description"
        project.created_at = datetime.now()
        project.updated_at = datetime.now()
        project.to_dict.return_value = {
            "id": "project-123",
            "name": "Test Project",
            "description": "Test Description"
        }
        return project
    
    def test_service_initialization_with_repository(self, mock_project_repository):
        """Test service initialization with provided repository"""
        service = ProjectManagementService(project_repo=mock_project_repository)
        
        assert service._project_repo == mock_project_repository
        assert service._user_id is None
    
    def test_service_initialization_with_user(self, mock_project_repository):
        """Test service initialization with user context"""
        service = ProjectManagementService(project_repo=mock_project_repository, user_id="user-123")
        
        assert service._project_repo == mock_project_repository
        assert service._user_id == "user-123"
    
    @patch('fastmcp.task_management.application.services.project_management_service.GlobalRepositoryManager')
    def test_service_initialization_without_repository(self, mock_repo_manager):
        """Test service initialization without provided repository"""
        mock_default_repo = Mock()
        mock_repo_manager.get_default.return_value = mock_default_repo
        
        service = ProjectManagementService()
        
        assert service._project_repo == mock_default_repo
        mock_repo_manager.get_default.assert_called_once()
    
    def test_with_user_creates_new_instance(self, service, mock_project_repository):
        """Test that with_user creates a new service instance with user context"""
        user_service = service.with_user("user-456")
        
        assert user_service != service
        assert user_service._user_id == "user-456"
        assert user_service._project_repo == mock_project_repository


class TestProjectManagementServiceCreateProject:
    """Test suite for project creation"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.CreateProjectUseCase')
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_use_case_class, service):
        """Test successful project creation"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "Test Project"},
            "message": "Project created successfully"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.create_project("Test Project", "Test Description")
        
        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with(None, "Test Project", "Test Description")
    
    @patch('fastmcp.task_management.application.services.project_management_service.CreateProjectUseCase')
    @pytest.mark.asyncio
    async def test_create_project_with_user_id_parameter(self, mock_use_case_class, service):
        """Test project creation with user_id parameter (though not used in implementation)"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "User Project"}
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.create_project("User Project", "Description", user_id="user-456")
        
        assert result["success"] is True
        mock_use_case.execute.assert_called_once_with(None, "User Project", "Description")
    
    @patch('fastmcp.task_management.application.services.project_management_service.CreateProjectUseCase')
    @pytest.mark.asyncio
    async def test_create_project_error_handling(self, mock_use_case_class, service):
        """Test project creation error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Database connection failed"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.create_project("Test Project")
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]
    
    @patch('fastmcp.task_management.application.services.project_management_service.CreateProjectUseCase')
    @pytest.mark.asyncio
    async def test_create_project_empty_name(self, mock_use_case_class, service):
        """Test project creation with empty name"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": False,
            "error": "Project name is required"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.create_project("")
        
        assert result["success"] is False
        assert "Project name is required" in result["error"]


class TestProjectManagementServiceGetProject:
    """Test suite for project retrieval"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.GetProjectUseCase')
    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_use_case_class, service):
        """Test successful project retrieval by ID"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "Test Project"}
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.get_project("project-123")
        
        assert result["success"] is True
        assert result["project"]["id"] == "project-123"
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @patch('fastmcp.task_management.application.services.project_management_service.GetProjectUseCase')
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_use_case_class, service):
        """Test project retrieval when project not found"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": False,
            "error": "Project not found"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.get_project("nonexistent-project")
        
        assert result["success"] is False
        assert "Project not found" in result["error"]
    
    @patch('fastmcp.task_management.application.services.project_management_service.GetProjectUseCase')
    @pytest.mark.asyncio
    async def test_get_project_error_handling(self, mock_use_case_class, service):
        """Test project retrieval error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Database error"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.get_project("project-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @patch('fastmcp.task_management.application.services.project_management_service.GetProjectUseCase')
    @pytest.mark.asyncio
    async def test_get_project_by_name_success(self, mock_use_case_class, service, mock_project_repository):
        """Test successful project retrieval by name"""
        # Mock project entity found by name
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_project.name = "Test Project"
        mock_project_repository.find_by_name.return_value = mock_project
        
        # Mock use case execution
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "Test Project"}
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.get_project_by_name("Test Project")
        
        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"
        mock_project_repository.find_by_name.assert_called_once_with("Test Project")
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @pytest.mark.asyncio
    async def test_get_project_by_name_not_found(self, service, mock_project_repository):
        """Test project retrieval by name when project not found"""
        mock_project_repository.find_by_name.return_value = None
        
        result = await service.get_project_by_name("Nonexistent Project")
        
        assert result["success"] is False
        assert "Project with name 'Nonexistent Project' not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_project_by_name_error_handling(self, service, mock_project_repository):
        """Test project retrieval by name error handling"""
        mock_project_repository.find_by_name.side_effect = Exception("Database connection failed")
        
        result = await service.get_project_by_name("Test Project")
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]


class TestProjectManagementServiceListProjects:
    """Test suite for project listing"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.ListProjectsUseCase')
    @pytest.mark.asyncio
    async def test_list_projects_success(self, mock_use_case_class, service):
        """Test successful project listing"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "projects": [
                {"id": "project-1", "name": "Project 1"},
                {"id": "project-2", "name": "Project 2"}
            ],
            "count": 2
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.list_projects()
        
        assert result["success"] is True
        assert len(result["projects"]) == 2
        assert result["count"] == 2
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with(include_branches=True)
    
    @patch('fastmcp.task_management.application.services.project_management_service.ListProjectsUseCase')
    @pytest.mark.asyncio
    async def test_list_projects_without_branches(self, mock_use_case_class, service):
        """Test project listing without branch data"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "projects": [{"id": "project-1", "name": "Project 1"}],
            "count": 1
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.list_projects(include_branches=False)
        
        assert result["success"] is True
        mock_use_case.execute.assert_called_once_with(include_branches=False)
    
    @patch('fastmcp.task_management.application.services.project_management_service.ListProjectsUseCase')
    @pytest.mark.asyncio
    async def test_list_projects_error_handling(self, mock_use_case_class, service):
        """Test project listing error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Database query failed"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.list_projects()
        
        assert result["success"] is False
        assert "Database query failed" in result["error"]


class TestProjectManagementServiceUpdateProject:
    """Test suite for project updates"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.UpdateProjectUseCase')
    @pytest.mark.asyncio
    async def test_update_project_success(self, mock_use_case_class, service):
        """Test successful project update"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "Updated Project"},
            "message": "Project updated successfully"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.update_project("project-123", name="Updated Project", description="Updated Description")
        
        assert result["success"] is True
        assert result["project"]["name"] == "Updated Project"
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123", "Updated Project", "Updated Description")
    
    @patch('fastmcp.task_management.application.services.project_management_service.UpdateProjectUseCase')
    @pytest.mark.asyncio
    async def test_update_project_partial_update(self, mock_use_case_class, service):
        """Test project update with partial data"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "project": {"id": "project-123", "name": "Updated Name"}
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.update_project("project-123", name="Updated Name")
        
        assert result["success"] is True
        mock_use_case.execute.assert_called_once_with("project-123", "Updated Name", None)
    
    @patch('fastmcp.task_management.application.services.project_management_service.UpdateProjectUseCase')
    @pytest.mark.asyncio
    async def test_update_project_not_found(self, mock_use_case_class, service):
        """Test project update when project not found"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": False,
            "error": "Project not found"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.update_project("nonexistent-project", name="New Name")
        
        assert result["success"] is False
        assert "Project not found" in result["error"]
    
    @patch('fastmcp.task_management.application.services.project_management_service.UpdateProjectUseCase')
    @pytest.mark.asyncio
    async def test_update_project_error_handling(self, mock_use_case_class, service):
        """Test project update error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Update operation failed"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.update_project("project-123", name="Updated Name")
        
        assert result["success"] is False
        assert "Update operation failed" in result["error"]


class TestProjectManagementServiceHealthCheck:
    """Test suite for project health checks"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.ProjectHealthCheckUseCase')
    @pytest.mark.asyncio
    async def test_project_health_check_success(self, mock_use_case_class, service):
        """Test successful project health check"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "health_score": 85,
            "issues": [],
            "recommendations": ["Consider adding more test coverage"]
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.project_health_check("project-123")
        
        assert result["success"] is True
        assert result["health_score"] == 85
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @patch('fastmcp.task_management.application.services.project_management_service.ProjectHealthCheckUseCase')
    @pytest.mark.asyncio
    async def test_project_health_check_all_projects(self, mock_use_case_class, service):
        """Test health check for all projects"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "overall_health": 75,
            "project_health": {
                "project-1": {"health_score": 80},
                "project-2": {"health_score": 70}
            }
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.project_health_check()
        
        assert result["success"] is True
        assert result["overall_health"] == 75
        mock_use_case.execute.assert_called_once_with(None)
    
    @patch('fastmcp.task_management.application.services.project_management_service.ProjectHealthCheckUseCase')
    @pytest.mark.asyncio
    async def test_project_health_check_error_handling(self, mock_use_case_class, service):
        """Test project health check error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Health check failed"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.project_health_check("project-123")
        
        assert result["success"] is False
        assert "Health check failed" in result["error"]


class TestProjectManagementServiceMaintenanceOperations:
    """Test suite for maintenance operations (cleanup, validate, rebalance)"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock(spec=ProjectRepository)
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @patch('fastmcp.task_management.application.services.project_management_service.CleanupObsoleteUseCase')
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_success(self, mock_use_case_class, service):
        """Test successful cleanup obsolete operation"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "cleaned_items": 5,
            "message": "Cleanup completed successfully"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.cleanup_obsolete("project-123")
        
        assert result["success"] is True
        assert result["cleaned_items"] == 5
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @patch('fastmcp.task_management.application.services.project_management_service.ValidateIntegrityUseCase')
    @pytest.mark.asyncio
    async def test_validate_integrity_success(self, mock_use_case_class, service):
        """Test successful validate integrity operation"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "integrity_score": 95,
            "violations": []
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.validate_integrity("project-123")
        
        assert result["success"] is True
        assert result["integrity_score"] == 95
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @patch('fastmcp.task_management.application.services.project_management_service.RebalanceAgentsUseCase')
    @pytest.mark.asyncio
    async def test_rebalance_agents_success(self, mock_use_case_class, service):
        """Test successful rebalance agents operation"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(return_value={
            "success": True,
            "rebalanced_agents": 3,
            "message": "Agent rebalancing completed"
        })
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.rebalance_agents("project-123")
        
        assert result["success"] is True
        assert result["rebalanced_agents"] == 3
        mock_use_case_class.assert_called_once_with(service._project_repo)
        mock_use_case.execute.assert_called_once_with("project-123")
    
    @patch('fastmcp.task_management.application.services.project_management_service.CleanupObsoleteUseCase')
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_error_handling(self, mock_use_case_class, service):
        """Test cleanup obsolete error handling"""
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("Cleanup operation failed"))
        mock_use_case_class.return_value = mock_use_case
        
        result = await service.cleanup_obsolete("project-123")
        
        assert result["success"] is False
        assert "Cleanup operation failed" in result["error"]


class TestProjectManagementServiceDeleteProject:
    """Test suite for project deletion"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        repo = Mock(spec=ProjectRepository)
        repo.find_by_id = AsyncMock()
        repo.delete = AsyncMock()
        return repo
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @pytest.fixture
    def mock_project_entity(self):
        """Create a mock project entity"""
        project = Mock()
        project.id = "project-123"
        project.name = "Test Project"
        return project
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self, service, mock_project_repository, mock_project_entity):
        """Test successful project deletion with valid conditions"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        mock_project_repository.delete.return_value = True
        
        # Mock git branch facade
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-123", "name": "main", "task_count": 0}
                ]
            }
            mock_facade.delete_git_branch.return_value = {"success": True}
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123", force=False)
            
            assert result["success"] is True
            assert "Test Project" in result["message"]
            assert result["project_id"] == "project-123"
            mock_project_repository.delete.assert_called_once_with("project-123")
    
    @pytest.mark.asyncio
    async def test_delete_project_force_deletion(self, service, mock_project_repository, mock_project_entity):
        """Test forced project deletion bypassing safety checks"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        mock_project_repository.delete.return_value = True
        
        # Mock git branch facade with multiple branches and tasks
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-1", "name": "main", "task_count": 5},
                    {"id": "branch-2", "name": "feature", "task_count": 3}
                ]
            }
            mock_facade.delete_git_branch.return_value = {"success": True}
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123", force=True)
            
            assert result["success"] is True
            # Should delete all branches
            assert mock_facade.delete_git_branch.call_count == 2
    
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, service, mock_project_repository):
        """Test project deletion when project not found"""
        mock_project_repository.find_by_id.return_value = None
        
        result = await service.delete_project("nonexistent-project")
        
        assert result["success"] is False
        assert "Project nonexistent-project not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_project_multiple_branches_validation_fails(self, service, mock_project_repository, mock_project_entity):
        """Test project deletion validation fails with multiple branches"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-1", "name": "main", "task_count": 0},
                    {"id": "branch-2", "name": "feature", "task_count": 0}
                ]
            }
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123", force=False)
            
            assert result["success"] is False
            assert "multiple branches" in result["error"]
            assert "2 branches" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_project_non_main_branch_validation_fails(self, service, mock_project_repository, mock_project_entity):
        """Test project deletion validation fails with non-main branch"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-1", "name": "feature", "task_count": 0}
                ]
            }
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123", force=False)
            
            assert result["success"] is False
            assert "non-main branch" in result["error"]
            assert "feature" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_project_main_branch_with_tasks_validation_fails(self, service, mock_project_repository, mock_project_entity):
        """Test project deletion validation fails with tasks in main branch"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-1", "name": "main", "task_count": 3}
                ]
            }
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123", force=False)
            
            assert result["success"] is False
            assert "3 tasks in main branch" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_project_repository_delete_fails(self, service, mock_project_repository, mock_project_entity):
        """Test project deletion when repository delete operation fails"""
        mock_project_repository.find_by_id.return_value = mock_project_entity
        mock_project_repository.delete.return_value = False  # Repository delete returns False
        
        with patch('fastmcp.task_management.application.services.project_management_service.GitBranchApplicationFacade') as mock_facade_class:
            mock_facade = Mock()
            mock_facade.list_git_branchs.return_value = {
                "success": True,
                "git_branchs": [
                    {"id": "branch-123", "name": "main", "task_count": 0}
                ]
            }
            mock_facade_class.return_value = mock_facade
            
            result = await service.delete_project("project-123")
            
            assert result["success"] is False
            assert "repository returned False" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_project_error_handling(self, service, mock_project_repository):
        """Test project deletion error handling"""
        mock_project_repository.find_by_id.side_effect = Exception("Database connection failed")
        
        result = await service.delete_project("project-123")
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]


class TestProjectManagementServiceIntegration:
    """Test suite for integration scenarios"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        repo = Mock(spec=ProjectRepository)
        repo.find_by_id = AsyncMock()
        repo.find_by_name = AsyncMock()
        repo.save = AsyncMock()
        repo.delete = AsyncMock()
        return repo
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create service instance with mocked dependencies"""
        return ProjectManagementService(project_repo=mock_project_repository)
    
    @pytest.mark.asyncio
    async def test_service_user_scoping_workflow(self, service):
        """Test complete workflow with user scoping"""
        user_service = service.with_user("user-123")
        
        # User service should have different user context but same repository
        assert user_service._user_id == "user-123"
        assert user_service._project_repo == service._project_repo
        
        # User service should be able to perform operations
        with patch('fastmcp.task_management.application.services.project_management_service.CreateProjectUseCase') as mock_use_case_class:
            mock_use_case = Mock()
            mock_use_case.execute = AsyncMock(return_value={"success": True, "project": {"id": "project-123"}})
            mock_use_case_class.return_value = mock_use_case
            
            result = await user_service.create_project("User Project")
            assert result["success"] is True
    
    @patch('fastmcp.task_management.application.services.project_management_service.GlobalRepositoryManager')
    def test_service_dependency_injection_priority(self, mock_repo_manager):
        """Test dependency injection priority (provided repo vs default)"""
        mock_provided_repo = Mock()
        mock_default_repo = Mock()
        mock_repo_manager.get_default.return_value = mock_default_repo
        
        # Service with provided repository
        service_with_repo = ProjectManagementService(project_repo=mock_provided_repo)
        assert service_with_repo._project_repo == mock_provided_repo
        
        # Service without provided repository (should use default)
        service_without_repo = ProjectManagementService()
        assert service_without_repo._project_repo == mock_default_repo
        mock_repo_manager.get_default.assert_called_once()