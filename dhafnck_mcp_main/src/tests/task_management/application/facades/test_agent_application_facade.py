#!/usr/bin/env python3
"""
Unit tests for AgentApplicationFacade
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

from fastmcp.task_management.application.facades.agent_application_facade import AgentApplicationFacade
from fastmcp.task_management.application.dtos.agent.register_agent_request import RegisterAgentRequest
from fastmcp.task_management.application.dtos.agent.assign_agent_request import AssignAgentRequest
from fastmcp.task_management.application.dtos.agent.update_agent_request import UpdateAgentRequest
from fastmcp.task_management.domain.entities.agent import Agent as AgentEntity
from fastmcp.task_management.domain.value_objects.agent_id import AgentId
from fastmcp.task_management.domain.exceptions.agent_exceptions import AgentNotFoundError


@pytest.fixture
def mock_agent_repository():
    """Create a mock agent repository"""
    return Mock()


@pytest.fixture
def mock_project_repository():
    """Create a mock project repository"""
    return Mock()


@pytest.fixture
def mock_git_branch_repository():
    """Create a mock git branch repository"""
    return Mock()


@pytest.fixture
def agent_facade(mock_agent_repository, mock_project_repository, mock_git_branch_repository):
    """Create an AgentApplicationFacade with mocked dependencies"""
    facade = AgentApplicationFacade(
        agent_repository=mock_agent_repository,
        project_repository=mock_project_repository,
        git_branch_repository=mock_git_branch_repository
    )
    return facade


@pytest.fixture
def sample_agent_entity():
    """Create a sample agent entity"""
    return AgentEntity(
        id=AgentId(str(uuid.uuid4())),
        name="Test Agent",
        project_id=str(uuid.uuid4()),
        status="active",
        capabilities=["coding", "testing"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestAgentApplicationFacade:
    """Test suite for AgentApplicationFacade"""
    
    @pytest.mark.unit
    def test_register_agent_success(self, agent_facade, mock_agent_repository, sample_agent_entity):
        """Test successful agent registration"""
        # Arrange
        project_id = str(uuid.uuid4())
        request = RegisterAgentRequest(
            project_id=project_id,
            agent_id="agent-1",
            name="New Agent",
            call_agent="@new_agent"
        )
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.agent = sample_agent_entity
        mock_response.message = "Agent registered successfully"
        
        agent_facade._register_agent_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.register_agent(project_id, "agent-1", "New Agent", "@new_agent")
        
        # Assert
        assert result["success"] is True
        assert "agent" in result
        agent_facade._register_agent_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_register_agent_validation_error(self, agent_facade):
        """Test agent registration with invalid data"""
        # Arrange
        project_id = str(uuid.uuid4())
        
        # Act - empty name should fail
        result = agent_facade.register_agent(project_id, "agent-1", "", None)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "name is required" in result["error"].lower()
    
    @pytest.mark.unit
    def test_assign_agent_success(self, agent_facade, mock_agent_repository):
        """Test successful agent assignment to git branch"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        git_branch_id = str(uuid.uuid4())
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.git_branch_id = git_branch_id
        mock_response.message = "Agent assigned successfully"
        
        agent_facade._assign_agent_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.assign_agent(project_id, agent_id, git_branch_id)
        
        # Assert
        assert result["success"] is True
        assert result["git_branch_id"] == git_branch_id
        agent_facade._assign_agent_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_unassign_agent_success(self, agent_facade):
        """Test successful agent unassignment"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        git_branch_id = str(uuid.uuid4())
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Agent unassigned successfully"
        
        agent_facade._unassign_agent_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.unassign_agent(project_id, agent_id, git_branch_id)
        
        # Assert
        assert result["success"] is True
        assert "unassigned successfully" in result["message"].lower()
    
    @pytest.mark.unit
    def test_get_agent_success(self, agent_facade, mock_agent_repository, sample_agent_entity):
        """Test successful agent retrieval"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        
        # Mock repository response
        mock_agent_repository.find_by_id.return_value = sample_agent_entity
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.agent = sample_agent_entity
        
        agent_facade._get_agent_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.get_agent(project_id, agent_id)
        
        # Assert
        assert result["success"] is True
        assert "agent" in result
        agent_facade._get_agent_use_case.execute.assert_called_once()
    
    @pytest.mark.unit
    def test_get_agent_not_found(self, agent_facade, mock_agent_repository):
        """Test getting non-existent agent"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "non-existent"
        
        # Mock the use case to return None
        agent_facade._get_agent_use_case.execute = Mock(return_value=None)
        
        # Act
        result = agent_facade.get_agent(project_id, agent_id)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.unit
    def test_list_agents(self, agent_facade, mock_agent_repository):
        """Test listing agents for a project"""
        # Arrange
        project_id = str(uuid.uuid4())
        
        # Create mock agents
        mock_agents = [
            Mock(id="agent-1", name="Agent 1", status="active"),
            Mock(id="agent-2", name="Agent 2", status="idle"),
            Mock(id="agent-3", name="Agent 3", status="busy")
        ]
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.agents = mock_agents
        mock_response.total = 3
        
        agent_facade._list_agents_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.list_agents(project_id)
        
        # Assert
        assert result["success"] is True
        assert "agents" in result
        assert result["total"] == 3
    
    @pytest.mark.unit
    def test_update_agent_success(self, agent_facade, mock_agent_repository, sample_agent_entity):
        """Test successful agent update"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        request = UpdateAgentRequest(
            project_id=project_id,
            agent_id=agent_id,
            name="Updated Agent",
            call_agent="@updated_agent"
        )
        
        # Mock the use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.agent = sample_agent_entity
        
        agent_facade._update_agent_use_case = Mock()
        agent_facade._update_agent_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.update_agent(project_id, agent_id, "Updated Agent", "@updated_agent")
        
        # Assert
        assert result["success"] is True
        assert "agent" in result
    
    @pytest.mark.unit
    def test_unregister_agent_success(self, agent_facade):
        """Test successful agent unregistration"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        
        # Mock the use case response
        agent_facade._unregister_agent_use_case.execute = Mock(return_value=True)
        
        # Act
        result = agent_facade.unregister_agent(project_id, agent_id)
        
        # Assert
        assert result["success"] is True
        assert "unregistered successfully" in result["message"].lower()
    
    @pytest.mark.unit
    def test_rebalance_agents(self, agent_facade):
        """Test agent rebalancing across tasks"""
        # Arrange
        project_id = str(uuid.uuid4())
        
        # Mock rebalance response
        mock_response = Mock()
        mock_response.success = True
        mock_response.rebalanced_count = 3
        mock_response.reassignments = [
            {"agent_id": "agent-1", "from": "branch-1", "to": "branch-2"},
            {"agent_id": "agent-2", "from": "branch-2", "to": "branch-3"}
        ]
        mock_response.message = "Agents rebalanced successfully"
        
        agent_facade._rebalance_agents_use_case = Mock()
        agent_facade._rebalance_agents_use_case.execute = Mock(return_value=mock_response)
        
        # Act
        result = agent_facade.rebalance_agents(project_id)
        
        # Assert
        assert result["success"] is True
        assert result["rebalanced_count"] == 3
        assert len(result["reassignments"]) == 2
    
    @pytest.mark.unit
    def test_get_agent_workload(self, agent_facade):
        """Test getting agent workload information"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        
        # Mock workload data
        workload_data = {
            "agent_id": agent_id,
            "current_tasks": 5,
            "completed_tasks": 12,
            "workload_percentage": 65.0,
            "status": "busy"
        }
        
        agent_facade.get_agent_workload = Mock(return_value={
            "success": True,
            "workload": workload_data
        })
        
        # Act
        result = agent_facade.get_agent_workload(project_id, agent_id)
        
        # Assert
        assert result["success"] is True
        assert result["workload"]["workload_percentage"] == 65.0
        assert result["workload"]["current_tasks"] == 5
    
    @pytest.mark.unit
    def test_get_agent_capabilities(self, agent_facade):
        """Test getting agent capabilities"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        
        # Mock capabilities
        capabilities = ["coding", "testing", "debugging", "documentation"]
        
        agent_facade.get_agent_capabilities = Mock(return_value={
            "success": True,
            "capabilities": capabilities
        })
        
        # Act
        result = agent_facade.get_agent_capabilities(project_id, agent_id)
        
        # Assert
        assert result["success"] is True
        assert len(result["capabilities"]) == 4
        assert "coding" in result["capabilities"]
    
    @pytest.mark.unit
    def test_error_handling(self, agent_facade):
        """Test error handling in facade methods"""
        # Arrange
        project_id = str(uuid.uuid4())
        agent_id = "agent-1"
        
        # Mock use case to raise an exception
        agent_facade._get_agent_use_case.execute = Mock(
            side_effect=Exception("Connection timeout")
        )
        
        # Act
        result = agent_facade.get_agent(project_id, agent_id)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "unexpected error" in result["error"].lower()