"""Test agent assignment with both UUID and @agent_name formats"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
from fastmcp.task_management.infrastructure.repositories.orm.agent_repository import ORMAgentRepository
from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory


class TestAgentAssignmentFix:
    """Test that agent assignment accepts both UUID and @agent_name formats"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.controller = GitBranchMCPController(GitBranchFacadeFactory())
        self.project_id = str(uuid.uuid4())
        self.branch_id = str(uuid.uuid4())
        
    def test_resolve_agent_identifier_with_uuid(self):
        """Test that valid UUIDs are returned as-is"""
        agent_uuid = str(uuid.uuid4())
        resolved = self.controller._resolve_agent_identifier(self.project_id, agent_uuid)
        assert resolved == agent_uuid
        
    @patch.object(ORMAgentRepository, 'find_by_name')
    def test_resolve_agent_identifier_with_existing_name(self, mock_find):
        """Test that existing agent names are resolved to their UUID"""
        # Mock an existing agent
        mock_agent = Mock()
        mock_agent.id = str(uuid.uuid4())
        mock_find.return_value = mock_agent
        
        # Test with @ prefix
        resolved = self.controller._resolve_agent_identifier(self.project_id, "@coding_agent")
        assert resolved == mock_agent.id
        mock_find.assert_called_with("coding_agent")
        
        # Test without @ prefix
        resolved = self.controller._resolve_agent_identifier(self.project_id, "coding_agent")
        assert resolved == mock_agent.id
        
    @patch.object(ORMAgentRepository, 'find_by_name')
    def test_resolve_agent_identifier_with_new_name(self, mock_find):
        """Test that new agent names generate a consistent UUID"""
        # Mock no existing agent
        mock_find.return_value = None
        
        # Test with @ prefix
        resolved1 = self.controller._resolve_agent_identifier(self.project_id, "@new_agent")
        assert ':' in resolved1  # Should be in format "uuid:name"
        uuid_part, name_part = resolved1.split(':', 1)
        assert name_part == "new_agent"
        
        # UUID should be valid
        uuid.UUID(uuid_part)  # This will raise if invalid
        
        # Test consistency - same name should generate same UUID
        resolved2 = self.controller._resolve_agent_identifier(self.project_id, "@new_agent")
        assert resolved1 == resolved2
        
    def test_assign_agent_to_tree_with_special_format(self):
        """Test that the repository correctly handles the uuid:name format"""
        repo = ORMAgentRepository(project_id=self.project_id)
        
        # Create a mock for get_by_id to simulate non-existing agent
        with patch.object(repo, 'get_by_id', return_value=None):
            # Mock the create method to avoid actual DB operations
            with patch.object(repo, 'create') as mock_create:
                mock_agent = Mock()
                mock_agent.model_metadata = {}
                mock_create.return_value = mock_agent
                
                # Mock the update method
                with patch.object(repo, 'update'):
                    # Test with special format
                    agent_uuid = str(uuid.uuid4())
                    result = repo.assign_agent_to_tree(
                        self.project_id,
                        f"{agent_uuid}:my_custom_agent",
                        self.branch_id
                    )
                    
                    # Verify auto-registration happened
                    assert result["auto_registered"] == True
                    
                    # Verify the create call used the correct agent name
                    create_call_args = mock_create.call_args[1]
                    assert create_call_args["name"] == "my_custom_agent"
                    assert create_call_args["id"] == agent_uuid
                    
    def test_assign_agent_to_tree_with_plain_uuid(self):
        """Test that plain UUIDs still work and get a generated name"""
        repo = ORMAgentRepository(project_id=self.project_id)
        
        # Create a mock for get_by_id to simulate non-existing agent
        with patch.object(repo, 'get_by_id', return_value=None):
            # Mock the create method to avoid actual DB operations
            with patch.object(repo, 'create') as mock_create:
                mock_agent = Mock()
                mock_agent.model_metadata = {}
                mock_create.return_value = mock_agent
                
                # Mock the update method
                with patch.object(repo, 'update'):
                    # Test with plain UUID
                    agent_uuid = str(uuid.uuid4())
                    result = repo.assign_agent_to_tree(
                        self.project_id,
                        agent_uuid,
                        self.branch_id
                    )
                    
                    # Verify auto-registration happened
                    assert result["auto_registered"] == True
                    
                    # Verify the create call used a generated name
                    create_call_args = mock_create.call_args[1]
                    assert create_call_args["name"] == f"agent_{agent_uuid[:8]}"
                    assert create_call_args["id"] == agent_uuid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])