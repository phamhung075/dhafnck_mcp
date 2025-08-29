"""Test for Project Application Service"""

import pytest
from unittest.mock import Mock, MagicMock, patch, ANY
from datetime import datetime, timezone
import uuid

from fastmcp.task_management.application.orchestrators.services.project_application_service import ProjectApplicationService
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.domain.entities.agent import Agent
from fastmcp.task_management.domain.entities.work_session import WorkSession
from fastmcp.task_management.domain.enums.agent_roles import AgentRole
from fastmcp.task_management.domain.exceptions import ProjectNotFoundError


class TestProjectApplicationService:
    """Test suite for ProjectApplicationService"""
    
    @pytest.fixture
    def mock_project_repository(self):
        """Create a mock project repository"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_project_repository):
        """Create a project application service instance"""
        return ProjectApplicationService(mock_project_repository)
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project"""
        project = Mock(spec=Project)
        project.id = "test-project-id"
        project.name = "Test Project"
        project.description = "Test Description"
        project.registered_agents = {}
        project.git_branchs = {}
        project.agent_assignments = {}
        project.active_work_sessions = {}
        project.resource_locks = {}
        return project
    
    @pytest.fixture
    def sample_agent(self):
        """Create a sample agent"""
        agent = Mock(spec=Agent)
        agent.id = "test-agent-id"
        agent.name = "Test Agent"
        agent.capabilities = {AgentRole.CODING}
        agent.created_at = datetime.now(timezone.utc)
        return agent
    
    def test_init(self, mock_project_repository):
        """Test service initialization"""
        service = ProjectApplicationService(mock_project_repository)
        assert service._project_repository == mock_project_repository
        assert service._user_id is None
        assert hasattr(service, '_create_project_use_case')
        assert hasattr(service, '_get_project_use_case')
        assert hasattr(service, '_list_projects_use_case')
        assert hasattr(service, '_update_project_use_case')
        assert hasattr(service, '_create_git_branch_use_case')
        assert hasattr(service, '_project_health_check_use_case')
    
    def test_init_with_user_id(self, mock_project_repository):
        """Test service initialization with user_id"""
        user_id = "test-user-123"
        service = ProjectApplicationService(mock_project_repository, user_id=user_id)
        assert service._user_id == user_id
    
    def test_with_user(self, service):
        """Test creating user-scoped service"""
        user_id = "test-user-456"
        user_scoped_service = service.with_user(user_id)
        assert isinstance(user_scoped_service, ProjectApplicationService)
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service._project_repository == service._project_repository
    
    def test_get_user_scoped_repository_no_user(self, service, mock_project_repository):
        """Test getting user-scoped repository without user_id"""
        result = service._get_user_scoped_repository()
        assert result == mock_project_repository
    
    def test_get_user_scoped_repository_with_user_with_user_method(self, mock_project_repository):
        """Test getting user-scoped repository with with_user method"""
        user_id = "test-user-789"
        mock_scoped_repo = Mock()
        mock_project_repository.with_user.return_value = mock_scoped_repo
        
        service = ProjectApplicationService(mock_project_repository, user_id=user_id)
        result = service._get_user_scoped_repository()
        
        mock_project_repository.with_user.assert_called_once_with(user_id)
        assert result == mock_scoped_repo
    
    def test_get_user_scoped_repository_with_user_property(self, mock_project_repository):
        """Test getting user-scoped repository with user_id property"""
        user_id = "test-user-999"
        mock_project_repository.with_user = None  # No with_user method
        mock_project_repository.user_id = "different-user"
        mock_project_repository.session = Mock()
        
        service = ProjectApplicationService(mock_project_repository, user_id=user_id)
        with patch('fastmcp.task_management.application.orchestrators.services.project_application_service.type') as mock_type:
            MockRepoClass = Mock()
            mock_type.return_value = MockRepoClass
            mock_scoped_repo = Mock()
            MockRepoClass.return_value = mock_scoped_repo
            
            result = service._get_user_scoped_repository()
            
            MockRepoClass.assert_called_once_with(mock_project_repository.session, user_id=user_id)
            assert result == mock_scoped_repo
    
    @pytest.mark.asyncio
    async def test_create_project(self, service):
        """Test create project"""
        project_id = "new-project-id"
        name = "New Project"
        description = "New Description"
        expected_result = {"success": True, "project_id": project_id}
        
        service._create_project_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.create_project(project_id, name, description)
        
        service._create_project_use_case.execute.assert_called_once_with(project_id, name, description)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_project(self, service):
        """Test get project"""
        project_id = "existing-project-id"
        expected_result = {"success": True, "project": {"id": project_id}}
        
        service._get_project_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.get_project(project_id)
        
        service._get_project_use_case.execute.assert_called_once_with(project_id)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_list_projects(self, service):
        """Test list projects"""
        expected_result = {"success": True, "projects": []}
        
        service._list_projects_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.list_projects()
        
        service._list_projects_use_case.execute.assert_called_once()
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_update_project(self, service):
        """Test update project"""
        project_id = "update-project-id"
        name = "Updated Name"
        description = "Updated Description"
        expected_result = {"success": True, "project_id": project_id}
        
        service._update_project_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.update_project(project_id, name, description)
        
        service._update_project_use_case.execute.assert_called_once_with(project_id, name, description)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_create_git_branch(self, service):
        """Test create git branch"""
        project_id = "branch-project-id"
        git_branch_name = "feature/new-feature"
        tree_name = "New Feature Tree"
        tree_description = "Feature Description"
        expected_result = {"success": True, "branch": git_branch_name}
        
        service._create_git_branch_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.create_git_branch(project_id, git_branch_name, tree_name, tree_description)
        
        service._create_git_branch_use_case.execute.assert_called_once_with(
            project_id, git_branch_name, tree_name, tree_description
        )
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_project_health_check(self, service):
        """Test project health check"""
        project_id = "health-check-id"
        expected_result = {"success": True, "health": "good"}
        
        service._project_health_check_use_case.execute = Mock(return_value=expected_result)
        
        result = await service.project_health_check(project_id)
        
        service._project_health_check_use_case.execute.assert_called_once_with(project_id)
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, service, sample_project, sample_agent):
        """Test successful agent registration"""
        project_id = sample_project.id
        agent_id = "new-agent-id"
        name = "New Agent"
        capabilities = ["CODING", "TESTING"]
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        mock_repo.update = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock project methods
        sample_project.register_agent = Mock()
        
        result = await service.register_agent(project_id, agent_id, name, capabilities)
        
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["agent"]["name"] == name
        assert "CODING" in result["agent"]["capabilities"]
        sample_project.register_agent.assert_called_once()
        mock_repo.update.assert_called_once_with(sample_project)
    
    @pytest.mark.asyncio
    async def test_register_agent_project_not_found(self, service):
        """Test agent registration with non-existent project"""
        project_id = "non-existent-project"
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=None)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.register_agent(project_id, "agent-id", "Agent Name")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_register_agent_invalid_capability(self, service, sample_project):
        """Test agent registration with invalid capability"""
        project_id = sample_project.id
        capabilities = ["INVALID_CAPABILITY"]
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        sample_project.register_agent = Mock()
        
        result = await service.register_agent(project_id, "agent-id", "Agent", capabilities)
        
        assert result["success"] is True
        # Invalid capabilities are skipped, not causing failure
        sample_project.register_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_agent_registration_error(self, service, sample_project):
        """Test agent registration with registration error"""
        project_id = sample_project.id
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        sample_project.register_agent = Mock(side_effect=ValueError("Agent already registered"))
        
        result = await service.register_agent(project_id, "agent-id", "Agent")
        
        assert result["success"] is False
        assert result["error"] == "Agent already registered"
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_success(self, service, sample_project):
        """Test successful agent assignment to tree"""
        project_id = sample_project.id
        agent_id = "agent-id"
        git_branch_name = "main"
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        mock_repo.update = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        sample_project.assign_agent_to_tree = Mock()
        
        result = await service.assign_agent_to_tree(project_id, agent_id, git_branch_name)
        
        assert result["success"] is True
        assert agent_id in result["message"]
        assert git_branch_name in result["message"]
        sample_project.assign_agent_to_tree.assert_called_once_with(agent_id, git_branch_name)
        mock_repo.update.assert_called_once_with(sample_project)
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_project_not_found(self, service):
        """Test agent assignment with non-existent project"""
        project_id = "non-existent-project"
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=None)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.assign_agent_to_tree(project_id, "agent-id", "main")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_assign_agent_to_tree_assignment_error(self, service, sample_project):
        """Test agent assignment with assignment error"""
        project_id = sample_project.id
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        sample_project.assign_agent_to_tree = Mock(side_effect=ValueError("Tree not found"))
        
        result = await service.assign_agent_to_tree(project_id, "agent-id", "non-existent-tree")
        
        assert result["success"] is False
        assert result["error"] == "Tree not found"
    
    @pytest.mark.asyncio
    async def test_unregister_agent_success(self, service, sample_project, sample_agent):
        """Test successful agent unregistration"""
        project_id = sample_project.id
        agent_id = sample_agent.id
        
        # Setup project with agent
        sample_project.registered_agents = {agent_id: sample_agent}
        sample_project.agent_assignments = {"main": agent_id, "feature": "other-agent"}
        sample_project.active_work_sessions = {
            "session1": Mock(agent_id=agent_id),
            "session2": Mock(agent_id="other-agent")
        }
        sample_project.resource_locks = {
            "resource1": agent_id,
            "resource2": "other-agent"
        }
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        mock_repo.update = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        service._project_repository = mock_repo  # For the final update
        
        result = await service.unregister_agent(project_id, agent_id)
        
        assert result["success"] is True
        assert result["agent"]["id"] == agent_id
        assert result["removed_sessions"] == 1
        assert result["unlocked_resources"] == 1
        assert agent_id not in sample_project.registered_agents
        assert "main" not in sample_project.agent_assignments
        assert "session1" not in sample_project.active_work_sessions
        assert "resource1" not in sample_project.resource_locks
        # Other agents should remain
        assert "feature" in sample_project.agent_assignments
        assert "session2" in sample_project.active_work_sessions
        assert "resource2" in sample_project.resource_locks
    
    @pytest.mark.asyncio
    async def test_unregister_agent_not_found(self, service, sample_project):
        """Test unregister non-existent agent"""
        project_id = sample_project.id
        agent_id = "non-existent-agent"
        sample_project.registered_agents = {}
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.unregister_agent(project_id, agent_id)
        
        assert result["success"] is False
        assert "not found in project" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_single_project(self, service, sample_project):
        """Test cleanup obsolete data for single project"""
        project_id = sample_project.id
        
        # Setup project with obsolete data
        sample_project.git_branchs = {"main": Mock(), "feature": Mock()}
        sample_project.registered_agents = {"agent1": Mock(), "agent2": Mock()}
        sample_project.agent_assignments = {
            "main": "agent1",
            "deleted-tree": "agent2",  # Tree doesn't exist
            "feature": "agent3"  # Agent doesn't exist
        }
        sample_project.active_work_sessions = {
            "session1": Mock(agent_id="agent1"),
            "session2": Mock(agent_id="agent3")  # Agent doesn't exist
        }
        sample_project.resource_locks = {
            "resource1": "agent1",
            "resource2": "agent3"  # Agent doesn't exist
        }
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=sample_project)
        mock_repo.update = Mock(return_value=sample_project)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.cleanup_obsolete(project_id)
        
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert len(result["cleaned_items"]) == 5
        assert "deleted-tree" not in sample_project.agent_assignments
        assert "feature" not in sample_project.agent_assignments
        assert "session2" not in sample_project.active_work_sessions
        assert "resource2" not in sample_project.resource_locks
        mock_repo.update.assert_called_once_with(sample_project)
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_all_projects(self, service):
        """Test cleanup obsolete data for all projects"""
        # Create two mock projects
        project1 = Mock()
        project1.id = "project1"
        project1.git_branchs = {}
        project1.registered_agents = {}
        project1.agent_assignments = {"tree1": "agent1"}  # Obsolete
        project1.active_work_sessions = {}
        project1.resource_locks = {}
        
        project2 = Mock()
        project2.id = "project2"
        project2.git_branchs = {}
        project2.registered_agents = {}
        project2.agent_assignments = {}
        project2.active_work_sessions = {"session1": Mock(agent_id="agent1")}  # Obsolete
        project2.resource_locks = {}
        
        mock_repo = Mock()
        mock_repo.find_all = Mock(return_value=[project1, project2])
        mock_repo.update = Mock()
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.cleanup_obsolete()
        
        assert result["success"] is True
        assert result["total_cleaned"] == 2
        assert len(result["cleanup_results"]) == 2
        assert len(result["cleanup_results"]["project1"]) == 1
        assert len(result["cleanup_results"]["project2"]) == 1
        assert mock_repo.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_obsolete_project_not_found(self, service):
        """Test cleanup with non-existent project"""
        project_id = "non-existent-project"
        
        mock_repo = Mock()
        mock_repo.find_by_id = Mock(return_value=None)
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.cleanup_obsolete(project_id)
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_cleanup_project_data(self, service, sample_project):
        """Test _cleanup_project_data method"""
        # Setup project with mixed valid and obsolete data
        sample_project.git_branchs = {"main": Mock()}
        sample_project.registered_agents = {"agent1": Mock()}
        sample_project.agent_assignments = {
            "main": "agent1",  # Valid
            "deleted": "agent1",  # Tree doesn't exist
            "main2": "agent2"  # Agent doesn't exist
        }
        sample_project.active_work_sessions = {
            "session1": Mock(agent_id="agent1"),  # Valid
            "session2": Mock(agent_id="agent2")  # Agent doesn't exist
        }
        sample_project.resource_locks = {
            "resource1": "agent1",  # Valid
            "resource2": "agent2"  # Agent doesn't exist
        }
        
        cleaned_items = service._cleanup_project_data(sample_project)
        
        assert len(cleaned_items) == 4
        assert any("tree 'deleted'" in item for item in cleaned_items)
        assert any("tree 'main2'" in item for item in cleaned_items)
        assert any("session 'session2'" in item for item in cleaned_items)
        assert any("resource 'resource2'" in item for item in cleaned_items)
        
        # Valid assignments should remain
        assert "main" in sample_project.agent_assignments
        assert "session1" in sample_project.active_work_sessions
        assert "resource1" in sample_project.resource_locks
        
        # Obsolete assignments should be removed
        assert "deleted" not in sample_project.agent_assignments
        assert "main2" not in sample_project.agent_assignments
        assert "session2" not in sample_project.active_work_sessions
        assert "resource2" not in sample_project.resource_locks
    
    def test_cleanup_project_data_no_obsolete_data(self, service, sample_project):
        """Test cleanup when there's no obsolete data"""
        sample_project.git_branchs = {"main": Mock()}
        sample_project.registered_agents = {"agent1": Mock()}
        sample_project.agent_assignments = {"main": "agent1"}
        sample_project.active_work_sessions = {"session1": Mock(agent_id="agent1")}
        sample_project.resource_locks = {"resource1": "agent1"}
        
        cleaned_items = service._cleanup_project_data(sample_project)
        
        assert len(cleaned_items) == 0
        assert len(sample_project.agent_assignments) == 1
        assert len(sample_project.active_work_sessions) == 1
        assert len(sample_project.resource_locks) == 1