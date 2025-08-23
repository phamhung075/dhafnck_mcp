"""
Test for UUID iteration fix in agent repository
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from fastmcp.task_management.infrastructure.repositories.orm.agent_repository import ORMAgentRepository
from fastmcp.task_management.infrastructure.database.models import Agent


class TestUUIDIterationFix:
    """Test cases for UUID iteration bug fix in agent repository"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_project_id = str(uuid.uuid4())
        self.test_agent_id = str(uuid.uuid4())
        self.test_git_branch_id = str(uuid.uuid4())
        
    def test_assign_agent_with_single_uuid_string(self):
        """Test assign_agent_to_tree when assigned_trees is a single UUID string"""
        
        # Create mock agent with single UUID string in assigned_trees
        mock_agent = Mock(spec=Agent)
        mock_agent.id = self.test_agent_id
        mock_agent.name = "test_agent"
        mock_agent.model_metadata = {
            "assigned_trees": self.test_git_branch_id  # Single UUID string (the bug case)
        }
        
        # Create repository with mocked dependencies
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'), \
             patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseUserScopedRepository.__init__'):
            
            repo = ORMAgentRepository()
            repo.get_by_id = Mock(return_value=mock_agent)
            repo.update = Mock(return_value=True)
            
            # This should not raise "argument of type 'UUID' is not iterable" anymore
            result = repo.assign_agent_to_tree(
                self.test_project_id,
                self.test_agent_id,
                self.test_git_branch_id
            )
            
            # Should indicate agent already assigned (since git_branch_id matches the single string)
            assert result["success"] is True
            assert "already assigned" in result["message"]
    
    def test_assign_agent_with_empty_assigned_trees(self):
        """Test assign_agent_to_tree when assigned_trees is empty"""
        
        # Create mock agent with empty assigned_trees
        mock_agent = Mock(spec=Agent)
        mock_agent.id = self.test_agent_id
        mock_agent.name = "test_agent"
        mock_agent.model_metadata = {
            "assigned_trees": []  # Empty list
        }
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'), \
             patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseUserScopedRepository.__init__'):
            
            repo = ORMAgentRepository()
            repo.get_by_id = Mock(return_value=mock_agent)
            repo.update = Mock(return_value=True)
            
            result = repo.assign_agent_to_tree(
                self.test_project_id,
                self.test_agent_id,
                self.test_git_branch_id
            )
            
            assert result["success"] is True
            assert "assigned to tree" in result["message"]
            
            # Verify update was called with proper list
            repo.update.assert_called_once()
            call_args = repo.update.call_args
            updated_metadata = call_args[1]["model_metadata"]
            assert updated_metadata["assigned_trees"] == [self.test_git_branch_id]
    
    def test_assign_agent_with_list_assigned_trees(self):
        """Test assign_agent_to_tree when assigned_trees is a proper list"""
        
        other_branch_id = str(uuid.uuid4())
        
        # Create mock agent with list of assigned_trees
        mock_agent = Mock(spec=Agent)
        mock_agent.id = self.test_agent_id
        mock_agent.name = "test_agent"
        mock_agent.model_metadata = {
            "assigned_trees": [other_branch_id]  # List with existing branch
        }
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'), \
             patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseUserScopedRepository.__init__'):
            
            repo = ORMAgentRepository()
            repo.get_by_id = Mock(return_value=mock_agent)
            repo.update = Mock(return_value=True)
            
            result = repo.assign_agent_to_tree(
                self.test_project_id,
                self.test_agent_id,
                self.test_git_branch_id
            )
            
            assert result["success"] is True
            
            # Verify both branches are in the updated list
            call_args = repo.update.call_args
            updated_metadata = call_args[1]["model_metadata"]
            assigned_trees = updated_metadata["assigned_trees"]
            assert self.test_git_branch_id in assigned_trees
            assert other_branch_id in assigned_trees
            assert len(assigned_trees) == 2
    
    def test_unassign_agent_with_single_uuid_string(self):
        """Test unassign_agent_from_tree when assigned_trees is a single UUID string"""
        
        # Create mock agent with single UUID string in assigned_trees
        mock_agent = Mock(spec=Agent)
        mock_agent.id = self.test_agent_id
        mock_agent.name = "test_agent"
        mock_agent.model_metadata = {
            "assigned_trees": self.test_git_branch_id  # Single UUID string (the bug case)
        }
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'), \
             patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseUserScopedRepository.__init__'):
            
            repo = ORMAgentRepository()
            repo.get_by_id = Mock(return_value=mock_agent)
            repo.update = Mock(return_value=True)
            
            # This should not raise "argument of type 'UUID' is not iterable" anymore
            result = repo.unassign_agent_from_tree(
                self.test_project_id,
                self.test_agent_id,
                self.test_git_branch_id
            )
            
            assert "removed_assignments" in result
            assert self.test_git_branch_id in result["removed_assignments"]
            assert result["remaining_assignments"] == []
    
    def test_get_agent_with_single_uuid_string(self):
        """Test get_agent when assigned_trees is a single UUID string"""
        
        # Create mock agent with single UUID string in assigned_trees
        mock_agent = Mock(spec=Agent)
        mock_agent.id = self.test_agent_id
        mock_agent.name = "test_agent"
        mock_agent.description = "Test agent"
        mock_agent.capabilities = []
        mock_agent.status = "available"
        mock_agent.availability_score = 1.0
        mock_agent.created_at = Mock()
        mock_agent.created_at.isoformat.return_value = "2024-08-22T00:00:00"
        mock_agent.updated_at = Mock()
        mock_agent.updated_at.isoformat.return_value = "2024-08-22T00:00:00"
        mock_agent.model_metadata = {
            "assigned_trees": self.test_git_branch_id  # Single UUID string (the bug case)
        }
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseORMRepository.__init__'), \
             patch('fastmcp.task_management.infrastructure.repositories.orm.agent_repository.BaseUserScopedRepository.__init__'):
            
            repo = ORMAgentRepository()
            repo.get_by_id = Mock(return_value=mock_agent)
            
            # This should not raise "argument of type 'UUID' is not iterable" anymore
            result = repo.get_agent(self.test_project_id, self.test_agent_id)
            
            assert result["id"] == self.test_agent_id
            assert result["assignments"] == [self.test_git_branch_id]  # Should be converted to list


if __name__ == "__main__":
    pytest.main([__file__, "-v"])