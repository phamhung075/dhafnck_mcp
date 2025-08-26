"""
Tests for Project Application Service

This module tests the ProjectApplicationService functionality including:
- Project creation, retrieval, listing, and updates
- Git branch (task tree) creation
- Agent registration and assignment
- Agent unregistration
- Project health checks
- Cleanup operations
- User context handling
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from fastmcp.task_management.application.services.project_application_service import ProjectApplicationService
from fastmcp.task_management.domain.entities.agent import Agent
from fastmcp.task_management.domain.enums.agent_roles import AgentRole


class TestProjectApplicationService:
    """Test suite for ProjectApplicationService"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        repo = Mock()
        repo.find_by_id = AsyncMock()
        repo.update = AsyncMock()
        repo.find_all = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_use_cases(self):
        """Create mock use cases"""
        return {
            'create': Mock(execute=AsyncMock()),
            'get': Mock(execute=AsyncMock()),
            'list': Mock(execute=AsyncMock()),
            'update': Mock(execute=AsyncMock()),
            'create_branch': Mock(execute=AsyncMock()),
            'health_check': Mock(execute=AsyncMock())
        }
    
    @pytest.fixture
    def service(self, mock_project_repository, mock_use_cases):
        """Create service instance with mocked dependencies"""
        service = ProjectApplicationService(mock_project_repository, user_id="test-user-123")
        
        # Replace use cases with mocks
        service._create_project_use_case = mock_use_cases['create']
        service._get_project_use_case = mock_use_cases['get']
        service._list_projects_use_case = mock_use_cases['list']
        service._update_project_use_case = mock_use_cases['update']
        service._create_git_branch_use_case = mock_use_cases['create_branch']
        service._project_health_check_use_case = mock_use_cases['health_check']
        
        return service
    
    @pytest.fixture
    def mock_project(self):
        """Create a mock project"""
        project = Mock()
        project.id = str(uuid4())
        project.name = "Test Project"
        project.registered_agents = {}
        project.agent_assignments = {}
        project.active_work_sessions = {}
        project.resource_locks = {}
        project.git_branchs = {}
        project.register_agent = Mock()
        project.assign_agent_to_tree = Mock()
        return project
    
    @pytest.mark.asyncio
    async def test_create_project(self, service, mock_use_cases):
        """Test project creation"""
        project_id = str(uuid4())
        name = "New Project"
        description = "Test Description"
        
        expected_result = {"success": True, "project": {"id": project_id, "name": name}}
        mock_use_cases['create'].execute.return_value = expected_result
        
        result = await service.create_project(project_id, name, description)
        
        mock_use_cases['create'].execute.assert_called_once_with(project_id, name, description)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_project(self, service, mock_use_cases):
        """Test getting project details"""
        project_id = str(uuid4())
        expected_result = {"success": True, "project": {"id": project_id}}
        mock_use_cases['get'].execute.return_value = expected_result
        
        result = await service.get_project(project_id)
        
        mock_use_cases['get'].execute.assert_called_once_with(project_id)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_list_projects(self, service, mock_use_cases):
        """Test listing projects"""
        expected_result = {"success": True, "projects": [{"id": "1"}, {"id": "2"}]}
        mock_use_cases['list'].execute.return_value = expected_result
        
        result = await service.list_projects()
        
        mock_use_cases['list'].execute.assert_called_once()
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_update_project(self, service, mock_use_cases):
        """Test updating project"""
        project_id = str(uuid4())
        name = "Updated Name"
        description = "Updated Description"
        
        expected_result = {"success": True, "project": {"id": project_id, "name": name}}
        mock_use_cases['update'].execute.return_value = expected_result
        
        result = await service.update_project(project_id, name, description)
        
        mock_use_cases['update'].execute.assert_called_once_with(project_id, name, description)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_create_git_branch(self, service, mock_use_cases):
        """Test creating git branch"""
        project_id = str(uuid4())
        branch_name = "feature/test"
        tree_name = "Test Feature"
        tree_description = "Test Description"
        
        expected_result = {"success": True, "branch": {"name": branch_name}}
        mock_use_cases['create_branch'].execute.return_value = expected_result
        
        result = await service.create_git_branch(project_id, branch_name, tree_name, tree_description)
        
        mock_use_cases['create_branch'].execute.assert_called_once_with(
            project_id, branch_name, tree_name, tree_description
        )
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_project_health_check(self, service, mock_use_cases):
        """Test project health check"""
        project_id = str(uuid4())
        expected_result = {"success": True, "health_score": 95}
        mock_use_cases['health_check'].execute.return_value = expected_result
        
        result = await service.project_health_check(project_id)
        
        mock_use_cases['health_check'].execute.assert_called_once_with(project_id)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, service, mock_project_repository, mock_project):
        """Test successful agent registration"""
        project_id = mock_project.id
        agent_id = "agent-123"
        agent_name = "Test Agent"
        capabilities = ["DEVELOPER", "TESTER"]
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.register_agent(project_id, agent_id, agent_name, capabilities)
        
        # Verify project was fetched
        mock_project_repository.find_by_id.assert_called_once_with(project_id)
        
        # Verify agent was registered
        mock_project.register_agent.assert_called_once()
        registered_agent = mock_project.register_agent.call_args[0][0]
        assert isinstance(registered_agent, Agent)
        assert registered_agent.id == agent_id
        assert registered_agent.name == agent_name
        
        # Verify project was updated
        mock_project_repository.update.assert_called_once_with(mock_project)
        
        # Verify result
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["agent"]["name"] == agent_name
    
    @pytest.mark.asyncio
    async def test_register_agent_project_not_found(self, service, mock_project_repository):
        """Test agent registration when project not found"""
        project_id = str(uuid4())
        mock_project_repository.find_by_id.return_value = None
        
        result = await service.register_agent(project_id, "agent-123", "Test Agent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_success(self, service, mock_project_repository, mock_project):
        """Test successful agent assignment to tree"""
        project_id = mock_project.id
        agent_id = "agent-123"
        branch_name = "feature/test"
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.assign_agent_to_tree(project_id, agent_id, branch_name)
        
        # Verify assignment
        mock_project.assign_agent_to_tree.assert_called_once_with(agent_id, branch_name)
        mock_project_repository.update.assert_called_once_with(mock_project)
        
        assert result["success"] is True
        assert agent_id in result["message"]
        assert branch_name in result["message"]
    
    @pytest.mark.asyncio
    async def test_unregister_agent_success(self, service, mock_project_repository, mock_project):
        """Test successful agent unregistration"""
        project_id = mock_project.id
        agent_id = "agent-123"
        
        # Setup mock agent
        mock_agent = Mock(id=agent_id, name="Test Agent", capabilities={AgentRole.DEVELOPER})
        mock_project.registered_agents = {agent_id: mock_agent}
        mock_project.agent_assignments = {"branch1": agent_id}
        mock_project.active_work_sessions = {"session1": Mock(agent_id=agent_id)}
        mock_project.resource_locks = {"resource1": agent_id}
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.unregister_agent(project_id, agent_id)
        
        # Verify agent was removed from all structures
        assert agent_id not in mock_project.registered_agents
        assert "branch1" not in mock_project.agent_assignments
        assert "session1" not in mock_project.active_work_sessions
        assert "resource1" not in mock_project.resource_locks
        
        # Verify update was called
        mock_project_repository.update.assert_called_once_with(mock_project)
        
        # Verify result
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["removed_sessions"] == 1
        assert result["unlocked_resources"] == 1
    
    @pytest.mark.asyncio
    async def test_unregister_agent_not_found(self, service, mock_project_repository, mock_project):
        """Test unregistering non-existent agent"""
        project_id = mock_project.id
        mock_project.registered_agents = {}
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.unregister_agent(project_id, "non-existent-agent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_single_project(self, service, mock_project_repository, mock_project):
        """Test cleanup for single project"""
        project_id = mock_project.id
        
        # Setup obsolete data
        mock_project.agent_assignments = {
            "valid-branch": "agent-123",
            "invalid-branch": "agent-456"  # Branch doesn't exist
        }
        mock_project.git_branchs = {"valid-branch": Mock()}
        mock_project.registered_agents = {"agent-123": Mock()}
        
        mock_project_repository.find_by_id.return_value = mock_project
        
        result = await service.cleanup_obsolete(project_id)
        
        # Verify cleanup
        assert "invalid-branch" not in mock_project.agent_assignments
        assert "valid-branch" in mock_project.agent_assignments
        
        # Verify result
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert len(result["cleaned_items"]) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_all_projects(self, service, mock_project_repository):
        """Test cleanup for all projects"""
        # Setup multiple projects
        project1 = Mock(id="proj-1", agent_assignments={}, git_branchs={}, 
                       registered_agents={}, active_work_sessions={}, resource_locks={})
        project2 = Mock(id="proj-2", agent_assignments={"invalid": "agent-999"}, 
                       git_branchs={}, registered_agents={}, active_work_sessions={}, resource_locks={})
        
        mock_project_repository.find_all.return_value = [project1, project2]
        
        result = await service.cleanup_obsolete()
        
        # Verify result
        assert result["success"] is True
        assert result["total_cleaned"] >= 1
        assert "proj-1" in result["cleanup_results"]
        assert "proj-2" in result["cleanup_results"]
    
    def test_cleanup_project_data(self, service, mock_project):
        """Test internal cleanup logic"""
        # Setup project with various obsolete data
        mock_project.agent_assignments = {
            "branch1": "agent-1",  # Valid
            "branch2": "agent-999",  # Agent doesn't exist
            "branch999": "agent-1"  # Branch doesn't exist
        }
        mock_project.git_branchs = {"branch1": Mock()}
        mock_project.registered_agents = {"agent-1": Mock()}
        mock_project.active_work_sessions = {
            "session1": Mock(agent_id="agent-999")  # Orphaned session
        }
        mock_project.resource_locks = {
            "resource1": "agent-999"  # Orphaned lock
        }
        
        cleaned_items = service._cleanup_project_data(mock_project)
        
        # Verify cleanup
        assert len(mock_project.agent_assignments) == 1
        assert "branch1" in mock_project.agent_assignments
        assert len(mock_project.active_work_sessions) == 0
        assert len(mock_project.resource_locks) == 0
        assert len(cleaned_items) >= 4
    
    def test_with_user_creates_scoped_service(self, service):
        """Test creating user-scoped service"""
        new_user_id = "different-user-456"
        scoped_service = service.with_user(new_user_id)
        
        assert isinstance(scoped_service, ProjectApplicationService)
        assert scoped_service._user_id == new_user_id
        assert scoped_service._user_id != service._user_id
    
    def test_get_user_scoped_repository(self, service, mock_project_repository):
        """Test getting user-scoped repository"""
        # Test repository with with_user method
        mock_project_repository.with_user = Mock(return_value=Mock())
        scoped_repo = service._get_user_scoped_repository()
        
        mock_project_repository.with_user.assert_called_once_with("test-user-123")
        assert scoped_repo == mock_project_repository.with_user.return_value