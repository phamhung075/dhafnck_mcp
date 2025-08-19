"""
Tests for ORM Agent Repository Implementation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from fastmcp.task_management.infrastructure.repositories.orm.agent_repository import ORMAgentRepository
from fastmcp.task_management.infrastructure.database.models import Agent
from fastmcp.task_management.domain.entities.agent import Agent as AgentEntity, AgentStatus, AgentCapability
from fastmcp.task_management.domain.exceptions.base_exceptions import (
    ResourceNotFoundException,
    ValidationException,
    DatabaseException
)


class TestORMAgentRepository:
    """Test the ORMAgentRepository class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def project_id(self):
        """Test project ID"""
        return "project-123"
    
    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "user-123"
    
    @pytest.fixture
    def repository(self, mock_session, project_id, user_id):
        """Create a repository instance"""
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'):
            repo = ORMAgentRepository(mock_session, project_id, user_id)
            repo.session = mock_session
            return repo
    
    @pytest.fixture
    def mock_agent_model(self):
        """Create a mock Agent model"""
        agent = Mock(spec=Agent)
        agent.id = "agent-123"
        agent.name = "Test Agent"
        agent.description = "Test agent description"
        agent.capabilities = ["code_review", "testing"]
        agent.status = "available"
        agent.availability_score = 1.0
        agent.last_active_at = datetime.now()
        agent.model_metadata = {
            "call_agent": "@test_agent",
            "assigned_trees": ["tree-1", "tree-2"]
        }
        agent.created_at = datetime.now()
        agent.updated_at = datetime.now()
        return agent
    
    @pytest.fixture
    def mock_agent_entity(self):
        """Create a mock Agent entity"""
        return AgentEntity(
            id="agent-123",
            name="Test Agent",
            description="Test agent description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            capabilities={AgentCapability.CODE_REVIEW, AgentCapability.TESTING},
            status=AgentStatus.AVAILABLE
        )
    
    def test_model_to_entity_conversion(self, repository, mock_agent_model):
        """Test converting SQLAlchemy model to domain entity"""
        entity = repository._model_to_entity(mock_agent_model)
        
        assert isinstance(entity, AgentEntity)
        assert entity.id == mock_agent_model.id
        assert entity.name == mock_agent_model.name
        assert entity.description == mock_agent_model.description
        assert entity.status == AgentStatus.AVAILABLE
        assert AgentCapability.CODE_REVIEW in entity.capabilities
        assert AgentCapability.TESTING in entity.capabilities
    
    def test_model_to_entity_with_invalid_capability(self, repository, mock_agent_model):
        """Test model to entity conversion with invalid capability"""
        mock_agent_model.capabilities = ["code_review", "invalid_capability"]
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.logger') as mock_logger:
            entity = repository._model_to_entity(mock_agent_model)
            
            assert AgentCapability.CODE_REVIEW in entity.capabilities
            assert len(entity.capabilities) == 1  # Invalid capability skipped
            mock_logger.warning.assert_called()
    
    def test_model_to_entity_with_invalid_status(self, repository, mock_agent_model):
        """Test model to entity conversion with invalid status"""
        mock_agent_model.status = "invalid_status"
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.logger') as mock_logger:
            entity = repository._model_to_entity(mock_agent_model)
            
            assert entity.status == AgentStatus.AVAILABLE  # Default status
            mock_logger.warning.assert_called()
    
    def test_entity_to_model_dict_conversion(self, repository, mock_agent_entity):
        """Test converting domain entity to model dictionary"""
        model_dict = repository._entity_to_model_dict(mock_agent_entity)
        
        assert model_dict["id"] == mock_agent_entity.id
        assert model_dict["name"] == mock_agent_entity.name
        assert model_dict["description"] == mock_agent_entity.description
        assert model_dict["status"] == "available"
        assert "code_review" in model_dict["capabilities"]
        assert "testing" in model_dict["capabilities"]
        assert model_dict["availability_score"] == 1.0
        assert "model_metadata" in model_dict
    
    def test_register_agent_success(self, repository, project_id):
        """Test successful agent registration"""
        agent_id = "new-agent"
        name = "@test_new_agent"
        call_agent = "@test_new_agent"
        
        # Mock the exists check
        repository.exists = Mock(return_value=False)
        repository.find_by_name = Mock(return_value=None)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        # Mock the create method
        mock_created_agent = Mock()
        mock_created_agent.id = agent_id
        mock_created_agent.name = name
        mock_created_agent.description = f"Agent for project {project_id}"
        mock_created_agent.capabilities = []
        mock_created_agent.status = "available"
        mock_created_agent.availability_score = 1.0
        mock_created_agent.model_metadata = {"call_agent": call_agent}
        mock_created_agent.created_at = datetime.now()
        mock_created_agent.updated_at = datetime.now()
        
        repository.create = Mock(return_value=mock_created_agent)
        
        result = repository.register_agent(project_id, agent_id, name, call_agent)
        
        assert result["id"] == agent_id
        assert result["name"] == name
        assert result["model_metadata"]["call_agent"] == call_agent
        repository.create.assert_called_once()
    
    def test_register_agent_already_exists(self, repository, project_id, mock_agent_model):
        """Test registering agent that already exists"""
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=mock_agent_model)
        
        with pytest.raises(ValidationException) as exc_info:
            repository.register_agent(project_id, "agent-123", "New Name")
        
        assert "already exists" in str(exc_info.value)
        assert "agent-123" in str(exc_info.value)
    
    def test_register_agent_duplicate_name(self, repository, project_id, mock_agent_model):
        """Test registering agent with duplicate name"""
        repository.exists = Mock(return_value=False)
        repository.find_by_name = Mock(return_value=mock_agent_model)
        
        with pytest.raises(ValidationException) as exc_info:
            repository.register_agent(project_id, "new-agent", mock_agent_model.name)
        
        assert "already exists" in str(exc_info.value)
        assert mock_agent_model.name in str(exc_info.value)
    
    def test_unregister_agent_success(self, repository, project_id, mock_agent_model):
        """Test successful agent unregistration"""
        agent_id = "agent-123"
        repository.get_by_id = Mock(return_value=mock_agent_model)
        repository.delete = Mock(return_value=True)
        
        result = repository.unregister_agent(project_id, agent_id)
        
        assert result["agent_data"]["id"] == agent_id
        assert result["agent_data"]["name"] == mock_agent_model.name
        assert "removed_assignments" in result
        repository.delete.assert_called_once_with(agent_id)
    
    def test_unregister_agent_not_found(self, repository, project_id):
        """Test unregistering non-existent agent"""
        agent_id = "nonexistent"
        repository.get_by_id = Mock(return_value=None)
        
        with pytest.raises(ResourceNotFoundException) as exc_info:
            repository.unregister_agent(project_id, agent_id)
        
        assert agent_id in str(exc_info.value)
    
    def test_assign_agent_to_tree_existing_agent(self, repository, project_id, mock_agent_model):
        """Test assigning existing agent to task tree"""
        agent_id = "agent-123"
        git_branch_id = "tree-456"
        
        repository.get_by_id = Mock(return_value=mock_agent_model)
        repository.update = Mock(return_value=mock_agent_model)
        
        result = repository.assign_agent_to_tree(project_id, agent_id, git_branch_id)
        
        assert result["success"] is True
        assert "assigned to tree" in result["message"]
        assert result["auto_registered"] is False
        repository.update.assert_called_once()
    
    def test_assign_agent_to_tree_auto_register(self, repository, project_id):
        """Test auto-registering agent during assignment"""
        agent_id = "new-agent-uuid"
        git_branch_id = "tree-456"
        
        # Mock agent not found initially
        repository.get_by_id = Mock(return_value=None)
        repository.exists = Mock(return_value=False)
        
        # Mock successful creation
        mock_created_agent = Mock()
        mock_created_agent.id = agent_id
        mock_created_agent.name = f"agent_{agent_id[:8]}"
        mock_created_agent.model_metadata = {}
        
        repository.create = Mock(return_value=mock_created_agent)
        repository.update = Mock(return_value=mock_created_agent)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        result = repository.assign_agent_to_tree(project_id, agent_id, git_branch_id)
        
        assert result["success"] is True
        assert result["auto_registered"] is True
        repository.create.assert_called_once()
    
    def test_assign_agent_to_tree_with_name_format(self, repository, project_id):
        """Test assigning agent with uuid:name format"""
        agent_id = "agent-uuid:@custom_agent_name"
        git_branch_id = "tree-456"
        
        repository.get_by_id = Mock(return_value=None)
        repository.exists = Mock(return_value=False)
        
        mock_created_agent = Mock()
        mock_created_agent.id = "agent-uuid"
        mock_created_agent.name = "@custom_agent_name"
        mock_created_agent.model_metadata = {}
        
        repository.create = Mock(return_value=mock_created_agent)
        repository.update = Mock(return_value=mock_created_agent)
        repository.set_user_id = Mock(side_effect=lambda x: {**x, "user_id": "user-123"})
        
        result = repository.assign_agent_to_tree(project_id, agent_id, git_branch_id)
        
        assert result["success"] is True
        assert result["auto_registered"] is True
        # Verify that the create was called with the parsed UUID
        create_call_args = repository.create.call_args[1]
        assert create_call_args["id"] == "agent-uuid"
        assert create_call_args["name"] == "@custom_agent_name"
    
    def test_unassign_agent_from_tree_specific(self, repository, project_id, mock_agent_model):
        """Test unassigning agent from specific tree"""
        agent_id = "agent-123"
        git_branch_id = "tree-1"
        
        repository.get_by_id = Mock(return_value=mock_agent_model)
        repository.update = Mock(return_value=mock_agent_model)
        
        result = repository.unassign_agent_from_tree(project_id, agent_id, git_branch_id)
        
        assert git_branch_id in result["removed_assignments"]
        assert "tree-2" in result["remaining_assignments"]
        repository.update.assert_called_once()
    
    def test_unassign_agent_from_tree_all(self, repository, project_id, mock_agent_model):
        """Test unassigning agent from all trees"""
        agent_id = "agent-123"
        
        repository.get_by_id = Mock(return_value=mock_agent_model)
        repository.update = Mock(return_value=mock_agent_model)
        
        result = repository.unassign_agent_from_tree(project_id, agent_id, None)
        
        assert len(result["removed_assignments"]) == 2
        assert len(result["remaining_assignments"]) == 0
        repository.update.assert_called_once()
    
    def test_get_agent_success(self, repository, project_id, mock_agent_model):
        """Test getting agent details"""
        agent_id = "agent-123"
        repository.get_by_id = Mock(return_value=mock_agent_model)
        
        result = repository.get_agent(project_id, agent_id)
        
        assert result["id"] == agent_id
        assert result["name"] == mock_agent_model.name
        assert result["assignments"] == ["tree-1", "tree-2"]
        assert "created_at" in result
        assert "updated_at" in result
    
    def test_list_agents(self, repository, project_id, mock_agent_model):
        """Test listing all agents"""
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.id = "agent-456"
        mock_agent2.name = "Agent 2"
        mock_agent2.description = "Second agent"
        mock_agent2.capabilities = []
        mock_agent2.status = "unavailable"
        mock_agent2.availability_score = 0.0
        mock_agent2.model_metadata = {}
        mock_agent2.created_at = datetime.now()
        mock_agent2.updated_at = datetime.now()
        
        repository.get_all = Mock(return_value=[mock_agent_model, mock_agent2])
        
        result = repository.list_agents(project_id)
        
        assert result["total_agents"] == 2
        assert len(result["agents"]) == 2
        assert result["agents"][0]["id"] == mock_agent_model.id
        assert result["agents"][1]["id"] == mock_agent2.id
    
    def test_update_agent_name(self, repository, project_id, mock_agent_model):
        """Test updating agent name"""
        agent_id = "agent-123"
        new_name = "Updated Agent Name"
        
        repository.get_by_id = Mock(return_value=mock_agent_model)
        
        updated_agent = Mock()
        updated_agent.id = agent_id
        updated_agent.name = new_name
        updated_agent.description = mock_agent_model.description
        updated_agent.capabilities = mock_agent_model.capabilities
        updated_agent.status = mock_agent_model.status
        updated_agent.availability_score = mock_agent_model.availability_score
        updated_agent.model_metadata = mock_agent_model.model_metadata
        updated_agent.created_at = mock_agent_model.created_at
        updated_agent.updated_at = datetime.now()
        
        repository.update = Mock(return_value=updated_agent)
        
        result = repository.update_agent(project_id, agent_id, name=new_name)
        
        assert result["name"] == new_name
        repository.update.assert_called_once()
    
    def test_update_agent_call_agent(self, repository, project_id, mock_agent_model):
        """Test updating agent call_agent"""
        agent_id = "agent-123"
        new_call_agent = "@updated_agent"
        
        repository.get_by_id = Mock(return_value=mock_agent_model)
        repository.update = Mock(return_value=mock_agent_model)
        
        result = repository.update_agent(project_id, agent_id, call_agent=new_call_agent)
        
        # Verify update was called with model_metadata containing new call_agent
        update_call_args = repository.update.call_args[1]
        assert update_call_args["model_metadata"]["call_agent"] == new_call_agent
    
    def test_rebalance_agents(self, repository, project_id, mock_agent_model):
        """Test rebalancing agent assignments"""
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "Agent 2"
        mock_agent2.model_metadata = {"assigned_trees": []}
        
        repository.get_all = Mock(return_value=[mock_agent_model, mock_agent2])
        
        result = repository.rebalance_agents(project_id)
        
        assert result["rebalance_result"]["changes_made"] is True
        assert len(result["rebalance_result"]["changes"]) == 1
        assert "2 assignments" in result["rebalance_result"]["changes"][0]
    
    def test_get_available_agents(self, repository, project_id):
        """Test getting available agents"""
        available_agent1 = Mock(spec=Agent)
        available_agent1.id = "agent-1"
        available_agent1.name = "Available 1"
        available_agent1.description = "Available agent 1"
        available_agent1.capabilities = []
        available_agent1.status = "available"
        available_agent1.availability_score = 1.0
        available_agent1.model_metadata = {"assigned_trees": ["tree-1"]}
        available_agent1.created_at = datetime.now()
        available_agent1.updated_at = datetime.now()
        
        repository.find_by = Mock(return_value=[available_agent1])
        
        result = repository.get_available_agents(project_id)
        
        assert len(result) == 1
        assert result[0]["id"] == "agent-1"
        assert result[0]["status"] == "available"
        repository.find_by.assert_called_once_with(status="available")
    
    def test_find_by_name(self, repository, mock_agent_model):
        """Test finding agent by name"""
        repository.get_by_field = Mock(return_value=mock_agent_model)
        
        result = repository.find_by_name("@Test Agent")
        
        assert result == mock_agent_model
        # Should try without @ prefix first
        repository.get_by_field.assert_called_with("name", "Test Agent")
    
    def test_find_by_name_not_found(self, repository):
        """Test finding non-existent agent by name"""
        repository.get_by_field = Mock(return_value=None)
        
        result = repository.find_by_name("Nonexistent")
        
        assert result is None
        # Should try both with and without @ prefix
        assert repository.get_by_field.call_count == 2
    
    def test_search_agents(self, repository, project_id, mock_agent_model):
        """Test searching agents"""
        query = "Test"
        
        # Mock the session query
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_agent_model]
        
        repository.get_db_session = Mock()
        repository.get_db_session().__enter__.return_value.query.return_value = mock_query
        
        result = repository.search_agents(project_id, query)
        
        assert len(result) == 1
        assert result[0]["name"] == mock_agent_model.name
    
    def test_error_handling_database_exception(self, repository, project_id):
        """Test database exception handling"""
        repository.exists = Mock(side_effect=Exception("Database connection error"))
        
        with pytest.raises(DatabaseException) as exc_info:
            repository.register_agent(project_id, "agent-123", "Test Agent")
        
        assert "Failed to register agent" in str(exc_info.value)
        assert "Database connection error" in str(exc_info.value)