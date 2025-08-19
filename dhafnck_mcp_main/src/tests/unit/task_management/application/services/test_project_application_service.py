"""
Unit tests for Project Application Service

Tests project management operations following DDD patterns with user isolation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from fastmcp.task_management.application.services.project_application_service import (
    ProjectApplicationService
)
from fastmcp.task_management.domain.entities.agent import Agent
from fastmcp.task_management.domain.enums.agent_roles import AgentRole


class TestProjectApplicationService:
    """Test cases for ProjectApplicationService"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        repo = Mock()
        repo.find_by_id = AsyncMock()
        repo.update = AsyncMock()
        repo.find_all = AsyncMock()
        repo.with_user = Mock(return_value=repo)
        repo.user_id = None
        repo.session = Mock()
        return repo
    
    @pytest.fixture
    def mock_use_cases(self):
        """Create mock use cases"""
        use_cases = {
            'create': Mock(),
            'get': Mock(),
            'list': Mock(),
            'update': Mock(),
            'create_branch': Mock(),
            'health_check': Mock()
        }
        for use_case in use_cases.values():
            use_case.execute = AsyncMock()
        return use_cases
    
    @pytest.fixture
    def service(self, mock_project_repository, mock_use_cases):
        """Create service instance with mocks"""
        with patch('fastmcp.task_management.application.services.project_application_service.CreateProjectUseCase', return_value=mock_use_cases['create']):
            with patch('fastmcp.task_management.application.services.project_application_service.GetProjectUseCase', return_value=mock_use_cases['get']):
                with patch('fastmcp.task_management.application.services.project_application_service.ListProjectsUseCase', return_value=mock_use_cases['list']):
                    with patch('fastmcp.task_management.application.services.project_application_service.UpdateProjectUseCase', return_value=mock_use_cases['update']):
                        with patch('fastmcp.task_management.application.services.project_application_service.CreateGitBranchUseCase', return_value=mock_use_cases['create_branch']):
                            with patch('fastmcp.task_management.application.services.project_application_service.ProjectHealthCheckUseCase', return_value=mock_use_cases['health_check']):
                                service = ProjectApplicationService(mock_project_repository, "test_user")
                                service._use_cases = mock_use_cases  # Store for easy access in tests
                                return service
    
    @pytest.fixture
    def mock_project(self):
        """Create a mock project entity"""
        project = Mock()
        project.id = "proj123"
        project.name = "Test Project"
        project.description = "Test Description"
        project.registered_agents = {}
        project.agent_assignments = {}
        project.active_work_sessions = {}
        project.resource_locks = {}
        project.git_branchs = {"main": Mock()}
        project.register_agent = Mock()
        project.assign_agent_to_tree = Mock()
        return project
    
    def test_init(self, mock_project_repository):
        """Test service initialization"""
        user_id = "test_user"
        service = ProjectApplicationService(mock_project_repository, user_id)
        
        assert service._project_repository == mock_project_repository
        assert service._user_id == user_id
    
    def test_get_user_scoped_repository_with_with_user(self, service, mock_project_repository):
        """Test getting user-scoped repository with with_user method"""
        scoped_repo = Mock()
        mock_project_repository.with_user.return_value = scoped_repo
        
        result = service._get_user_scoped_repository()
        
        mock_project_repository.with_user.assert_called_once_with("test_user")
        assert result == scoped_repo
    
    def test_get_user_scoped_repository_with_user_id_property(self, service, mock_project_repository):
        """Test getting user-scoped repository with user_id property"""
        # Setup repository with different user_id
        mock_project_repository.with_user = None  # No with_user method
        mock_project_repository.user_id = "different_user"
        
        with patch('fastmcp.task_management.application.services.project_application_service.type') as mock_type:
            mock_class = Mock()
            new_repo = Mock()
            mock_class.return_value = new_repo
            mock_type.return_value = mock_class
            
            result = service._get_user_scoped_repository()
            
            mock_class.assert_called_once_with(mock_project_repository.session, user_id="test_user")
            assert result == new_repo
    
    def test_with_user(self, service, mock_project_repository):
        """Test creating user-scoped service"""
        new_user_id = "new_user"
        new_service = service.with_user(new_user_id)
        
        assert isinstance(new_service, ProjectApplicationService)
        assert new_service._user_id == new_user_id
        assert new_service._project_repository == mock_project_repository
    
    @pytest.mark.asyncio
    async def test_create_project(self, service):
        """Test creating a project"""
        project_id = "proj123"
        name = "Test Project"
        description = "Test Description"
        expected_result = {"success": True, "project": {"id": project_id}}
        
        service._use_cases['create'].execute.return_value = expected_result
        
        result = await service.create_project(project_id, name, description)
        
        assert result == expected_result
        service._use_cases['create'].execute.assert_called_once_with(project_id, name, description)
    
    @pytest.mark.asyncio
    async def test_get_project(self, service):
        """Test getting a project"""
        project_id = "proj123"
        expected_result = {"success": True, "project": {"id": project_id}}
        
        service._use_cases['get'].execute.return_value = expected_result
        
        result = await service.get_project(project_id)
        
        assert result == expected_result
        service._use_cases['get'].execute.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_list_projects(self, service):
        """Test listing projects"""
        expected_result = {"success": True, "projects": []}
        
        service._use_cases['list'].execute.return_value = expected_result
        
        result = await service.list_projects()
        
        assert result == expected_result
        service._use_cases['list'].execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_project(self, service):
        """Test updating a project"""
        project_id = "proj123"
        name = "Updated Name"
        description = "Updated Description"
        expected_result = {"success": True, "project": {"id": project_id}}
        
        service._use_cases['update'].execute.return_value = expected_result
        
        result = await service.update_project(project_id, name, description)
        
        assert result == expected_result
        service._use_cases['update'].execute.assert_called_once_with(project_id, name, description)
    
    @pytest.mark.asyncio
    async def test_create_git_branch(self, service):
        """Test creating a git branch"""
        project_id = "proj123"
        branch_name = "feature/test"
        tree_name = "Feature Tree"
        tree_description = "Feature Description"
        expected_result = {"success": True, "branch": {"name": branch_name}}
        
        service._use_cases['create_branch'].execute.return_value = expected_result
        
        result = await service.create_git_branch(project_id, branch_name, tree_name, tree_description)
        
        assert result == expected_result
        service._use_cases['create_branch'].execute.assert_called_once_with(
            project_id, branch_name, tree_name, tree_description
        )
    
    @pytest.mark.asyncio
    async def test_project_health_check(self, service):
        """Test project health check"""
        project_id = "proj123"
        expected_result = {"success": True, "health_score": 85}
        
        service._use_cases['health_check'].execute.return_value = expected_result
        
        result = await service.project_health_check(project_id)
        
        assert result == expected_result
        service._use_cases['health_check'].execute.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, service, mock_project_repository, mock_project):
        """Test successfully registering an agent"""
        project_id = "proj123"
        agent_id = "agent123"
        agent_name = "Test Agent"
        capabilities = ["developer", "tester"]
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        with patch('fastmcp.task_management.application.services.project_application_service.Agent') as mock_agent_class:
            with patch('fastmcp.task_management.application.services.project_application_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime.now(timezone.utc)
                
                result = await service.register_agent(project_id, agent_id, agent_name, capabilities)
        
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["agent"]["name"] == agent_name
        assert f"Agent '{agent_id}' registered successfully" in result["message"]
        
        # Verify agent was registered to project
        mock_project.register_agent.assert_called_once()
        mock_project_repository.update.assert_called_once_with(mock_project)
    
    @pytest.mark.asyncio
    async def test_register_agent_project_not_found(self, service, mock_project_repository):
        """Test registering agent when project not found"""
        mock_project_repository.find_by_id.return_value = None
        
        result = await service.register_agent("nonexistent", "agent123", "Agent")
        
        assert result["success"] is False
        assert "Project with ID 'nonexistent' not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_register_agent_with_error(self, service, mock_project_repository, mock_project):
        """Test registering agent with validation error"""
        mock_project_repository.find_by_id.return_value = mock_project
        mock_project.register_agent.side_effect = ValueError("Agent already registered")
        
        result = await service.register_agent("proj123", "agent123", "Agent")
        
        assert result["success"] is False
        assert "Agent already registered" in result["error"]
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_success(self, service, mock_project_repository, mock_project):
        """Test successfully assigning agent to tree"""
        project_id = "proj123"
        agent_id = "agent123"
        branch_name = "main"
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.assign_agent_to_tree(project_id, agent_id, branch_name)
        
        assert result["success"] is True
        assert f"Agent '{agent_id}' assigned to tree '{branch_name}' successfully" in result["message"]
        
        mock_project.assign_agent_to_tree.assert_called_once_with(agent_id, branch_name)
        mock_project_repository.update.assert_called_once_with(mock_project)
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_error(self, service, mock_project_repository, mock_project):
        """Test assigning agent with error"""
        mock_project_repository.find_by_id.return_value = mock_project
        mock_project.assign_agent_to_tree.side_effect = ValueError("Agent not registered")
        
        result = await service.assign_agent_to_tree("proj123", "agent123", "main")
        
        assert result["success"] is False
        assert "Agent not registered" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unregister_agent_success(self, service, mock_project_repository, mock_project):
        """Test successfully unregistering an agent"""
        project_id = "proj123"
        agent_id = "agent123"
        
        # Setup mock agent
        mock_agent = Mock()
        mock_agent.id = agent_id
        mock_agent.name = "Test Agent"
        mock_agent.capabilities = [AgentRole.DEVELOPER]
        
        mock_project.registered_agents = {agent_id: mock_agent}
        mock_project.agent_assignments = {"main": agent_id}
        mock_project.active_work_sessions = {"session1": Mock(agent_id=agent_id)}
        mock_project.resource_locks = {"resource1": agent_id}
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.unregister_agent(project_id, agent_id)
        
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["removed_sessions"] == 1
        assert result["unlocked_resources"] == 1
        assert f"Agent '{agent_id}' unregistered successfully" in result["message"]
        
        # Verify agent was removed
        assert agent_id not in mock_project.registered_agents
        assert "main" not in mock_project.agent_assignments
        assert "session1" not in mock_project.active_work_sessions
        assert "resource1" not in mock_project.resource_locks
    
    @pytest.mark.asyncio
    async def test_unregister_agent_not_found(self, service, mock_project_repository, mock_project):
        """Test unregistering non-existent agent"""
        mock_project.registered_agents = {}
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.unregister_agent("proj123", "nonexistent")
        
        assert result["success"] is False
        assert "Agent 'nonexistent' not found in project 'proj123'" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_single_project(self, service, mock_project_repository, mock_project):
        """Test cleaning up obsolete data for a single project"""
        project_id = "proj123"
        
        # Setup obsolete data
        mock_project.agent_assignments = {"deleted_tree": "agent1", "main": "deleted_agent"}
        mock_project.git_branchs = {"main": Mock()}
        mock_project.registered_agents = {"agent1": Mock()}
        mock_project.active_work_sessions = {"session1": Mock(agent_id="deleted_agent")}
        mock_project.resource_locks = {"resource1": "deleted_agent"}
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.cleanup_obsolete(project_id)
        
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert len(result["cleaned_items"]) > 0
        
        # Verify cleanup occurred
        assert "deleted_tree" not in mock_project.agent_assignments
        assert "main" not in mock_project.agent_assignments
        assert "session1" not in mock_project.active_work_sessions
        assert "resource1" not in mock_project.resource_locks
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_all_projects(self, service, mock_project_repository, mock_project):
        """Test cleaning up obsolete data for all projects"""
        # Create two mock projects
        project1 = Mock()
        project1.id = "proj1"
        project1.agent_assignments = {"deleted": "agent"}
        project1.git_branchs = {}
        project1.registered_agents = {}
        project1.active_work_sessions = {}
        project1.resource_locks = {}
        
        project2 = Mock()
        project2.id = "proj2"
        project2.agent_assignments = {}
        project2.git_branchs = {}
        project2.registered_agents = {}
        project2.active_work_sessions = {}
        project2.resource_locks = {}
        
        mock_project_repository.find_all.return_value = [project1, project2]
        
        result = await service.cleanup_obsolete()
        
        assert result["success"] is True
        assert result["total_cleaned"] == 1
        assert "proj1" in result["cleanup_results"]
        assert len(result["cleanup_results"]["proj1"]) == 1
    
    def test_cleanup_project_data_assignments(self, service):
        """Test cleanup of agent assignments"""
        project = Mock()
        project.agent_assignments = {
            "existing_tree": "existing_agent",
            "deleted_tree": "agent1",
            "tree_with_deleted_agent": "deleted_agent"
        }
        project.git_branchs = {"existing_tree": Mock(), "tree_with_deleted_agent": Mock()}
        project.registered_agents = {"existing_agent": Mock()}
        project.active_work_sessions = {}
        project.resource_locks = {}
        
        cleaned = service._cleanup_project_data(project)
        
        assert len(cleaned) == 2
        assert "deleted_tree" not in project.agent_assignments
        assert "tree_with_deleted_agent" not in project.agent_assignments
        assert "existing_tree" in project.agent_assignments
    
    def test_cleanup_project_data_sessions(self, service):
        """Test cleanup of work sessions"""
        project = Mock()
        project.agent_assignments = {}
        project.git_branchs = {}
        project.registered_agents = {"agent1": Mock()}
        project.active_work_sessions = {
            "session1": Mock(agent_id="agent1"),
            "session2": Mock(agent_id="deleted_agent")
        }
        project.resource_locks = {}
        
        cleaned = service._cleanup_project_data(project)
        
        assert len(cleaned) == 1
        assert "session1" in project.active_work_sessions
        assert "session2" not in project.active_work_sessions
    
    def test_cleanup_project_data_locks(self, service):
        """Test cleanup of resource locks"""
        project = Mock()
        project.agent_assignments = {}
        project.git_branchs = {}
        project.registered_agents = {"agent1": Mock()}
        project.active_work_sessions = {}
        project.resource_locks = {
            "resource1": "agent1",
            "resource2": "deleted_agent"
        }
        
        cleaned = service._cleanup_project_data(project)
        
        assert len(cleaned) == 1
        assert "resource1" in project.resource_locks
        assert "resource2" not in project.resource_locks