"""
Unit tests for git_branch_id fix in context management

This test file verifies that:
1. manage_context accepts git_branch_id instead of git_branch_name
2. git_branch_id is auto-detected from task when not provided
3. HierarchicalContextFacadeFactory uses git_branch_id correctly
4. Error handling when git_branch_id cannot be determined
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import uuid

from fastmcp.task_management.interface.controllers.context_mcp_controller import ContextMCPController
from fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
from fastmcp.task_management.application.facades.hierarchical_context_facade import HierarchicalContextFacade


class TestContextGitBranchIdFix:
    """Test suite for git_branch_id requirement fix"""
    
    @pytest.fixture
    def mock_hierarchical_facade_factory(self):
        """Mock hierarchical context facade factory"""
        factory = Mock(spec=HierarchicalContextFacadeFactory)
        facade = Mock(spec=HierarchicalContextFacade)
        factory.create_facade.return_value = facade
        return factory
    
    @pytest.fixture
    def context_controller(self, mock_hierarchical_facade_factory):
        """Create context controller with mocked dependencies"""
        return ContextMCPController(
            hierarchical_context_facade_factory=mock_hierarchical_facade_factory
        )
    
    @pytest.fixture
    def test_task_id(self):
        """Test task UUID"""
        return "a957ec7f-f47f-49f9-8493-94bdb28b3e7b"
    
    @pytest.fixture
    def test_branch_id(self):
        """Test git branch UUID"""
        return "4a4e538b-dcc6-41ac-9854-ff505599de70"
    
    def test_manage_context_accepts_git_branch_id_parameter(self, context_controller):
        """Test that manage_context accepts git_branch_id parameter"""
        # The parameter should be defined in the function signature
        import inspect
        sig = inspect.signature(context_controller._manage_context_implementation)
        params = sig.parameters
        
        assert 'git_branch_id' in params
        # git_branch_name should NOT be in the parameters anymore
        assert 'git_branch_name' not in params
    
    @patch('fastmcp.task_management.infrastructure.database.database_config.get_session')
    def test_git_branch_id_auto_detected_from_task(self, mock_get_session, context_controller, test_task_id, test_branch_id):
        """Test that git_branch_id is auto-detected from task when not provided"""
        # Mock database session and task query
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock task with git_branch_id
        mock_task = Mock()
        mock_task.git_branch_id = test_branch_id
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        
        # Mock facade to return success
        mock_facade = context_controller._hierarchical_facade_factory.create_facade.return_value
        mock_facade.create_context.return_value = {
            "success": True,
            "context": {"id": "context-123"},
            "message": "Context created at task level"
        }
        
        # Call manage_context without git_branch_id
        result = context_controller._manage_context_implementation(
            action="create",
            task_id=test_task_id,
            data_title="Test Context",
            data_description="Testing auto-detection"
        )
        
        # Verify git_branch_id was extracted from task
        assert result["success"] is True
        # Verify facade was created with the auto-detected branch ID
        context_controller._hierarchical_facade_factory.create_facade.assert_called_with(
            user_id="default_id",
            project_id="",
            git_branch_id=test_branch_id
        )
    
    def test_git_branch_id_required_when_not_auto_detectable(self, context_controller, test_task_id):
        """Test that error is returned when git_branch_id cannot be determined"""
        # Mock session to return no task (task not found)
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None
            
            # Call manage_context without git_branch_id and with non-existent task
            result = context_controller._manage_context_implementation(
                action="create",
                task_id=test_task_id,
                data_title="Test Context"
            )
            
            # Should return error about missing git_branch_id
            assert result["success"] is False
            assert result["error_code"] == "MISSING_FIELD"
            assert "git_branch_id" in result["error"]
    
    def test_explicit_git_branch_id_takes_precedence(self, context_controller, test_task_id, test_branch_id):
        """Test that explicitly provided git_branch_id is used over auto-detection"""
        explicit_branch_id = "explicit-branch-id-123"
        
        # Mock facade to return success
        mock_facade = context_controller._hierarchical_facade_factory.create_facade.return_value
        mock_facade.create_context.return_value = {
            "success": True,
            "context": {"id": "context-123"},
            "message": "Context created at task level"
        }
        
        # Call with explicit git_branch_id
        result = context_controller._manage_context_implementation(
            action="create",
            task_id=test_task_id,
            git_branch_id=explicit_branch_id,
            data_title="Test Context"
        )
        
        # Verify explicit branch ID was used
        assert result["success"] is True
        context_controller._hierarchical_facade_factory.create_facade.assert_called_with(
            user_id="default_id",
            project_id="",
            git_branch_id=explicit_branch_id
        )
    
    def test_hierarchical_facade_factory_requires_git_branch_id(self):
        """Test that HierarchicalContextFacadeFactory requires git_branch_id"""
        factory = HierarchicalContextFacadeFactory()
        
        # Should raise error when git_branch_id is None
        with pytest.raises(ValueError, match="git_branch_id is required"):
            factory.create_facade(
                user_id="test-user",
                project_id="test-project",
                git_branch_id=None
            )
    
    def test_hierarchical_facade_factory_uses_git_branch_id_in_cache_key(self):
        """Test that factory uses git_branch_id in cache key"""
        factory = HierarchicalContextFacadeFactory()
        branch_id = "branch-123"
        
        # Create facade
        facade1 = factory.create_facade(
            user_id="user1",
            project_id="proj1",
            git_branch_id=branch_id
        )
        
        # Get cached facade - should return same instance
        facade2 = factory.create_facade(
            user_id="user1",
            project_id="proj1",
            git_branch_id=branch_id
        )
        
        assert facade1 is facade2
        
        # Different branch ID should create new facade
        facade3 = factory.create_facade(
            user_id="user1",
            project_id="proj1",
            git_branch_id="different-branch-id"
        )
        
        assert facade1 is not facade3
    
    @patch('fastmcp.task_management.infrastructure.database.database_config.get_session')
    def test_all_context_actions_support_git_branch_id(self, mock_get_session, context_controller, test_task_id, test_branch_id):
        """Test that all context actions support git_branch_id parameter"""
        # Mock database session and task
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_task = Mock()
        mock_task.git_branch_id = test_branch_id
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        
        # Mock facade methods
        mock_facade = context_controller._hierarchical_facade_factory.create_facade.return_value
        mock_facade.create_context.return_value = {"success": True, "context": {}}
        mock_facade.update_context.return_value = {"success": True}
        mock_facade.get_context.return_value = {"success": True, "context": {}}
        mock_facade.delete_context.return_value = {"success": True}
        mock_facade.merge_context.return_value = {"success": True}
        
        # Test various actions
        actions = ["create", "update", "get", "delete", "merge", "add_insight", "add_progress"]
        
        for action in actions:
            result = context_controller._manage_context_implementation(
                action=action,
                task_id=test_task_id,
                git_branch_id=test_branch_id,
                content="Test content" if action in ["add_insight", "add_progress"] else None
            )
            
            # All actions should succeed with git_branch_id
            assert "error" not in result or result.get("success") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])