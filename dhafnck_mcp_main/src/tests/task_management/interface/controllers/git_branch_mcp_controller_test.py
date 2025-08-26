"""Test suite for GitBranchMCPController.

Tests the git branch MCP controller including:
- Tool registration and MCP integration
- CRUD operations for git branches
- Agent assignment to branches
- Statistics and monitoring
- Authentication and user context
- Error handling and validation
- Workflow guidance integration
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.git_branch_mcp_controller import GitBranchMCPController
from fastmcp.task_management.application.factories.git_branch_facade_factory import GitBranchFacadeFactory
from fastmcp.task_management.application.facades.git_branch_application_facade import GitBranchApplicationFacade
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestGitBranchMCPController:
    """Test cases for GitBranchMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=GitBranchFacadeFactory)
        self.mock_facade = Mock(spec=GitBranchApplicationFacade)
        self.mock_facade_factory.create_git_branch_facade.return_value = self.mock_facade
        
        # Mock workflow guidance
        with patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.GitBranchWorkflowFactory'):
            self.controller = GitBranchMCPController(self.mock_facade_factory)
    
    def test_init(self):
        """Test controller initialization."""
        with patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.GitBranchWorkflowFactory') as mock_workflow_factory:
            mock_workflow = Mock()
            mock_workflow_factory.create.return_value = mock_workflow
            
            controller = GitBranchMCPController(self.mock_facade_factory)
            
            assert controller._git_branch_facade_factory == self.mock_facade_factory
            assert controller._workflow_guidance == mock_workflow
            mock_workflow_factory.create.assert_called_once()
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        
        with patch.object(self.controller, '_get_git_branch_management_descriptions') as mock_get_desc:
            mock_get_desc.return_value = {
                "manage_git_branch": {
                    "description": "Test description",
                    "parameters": {
                        "action": "Action parameter",
                        "project_id": "Project ID parameter"
                    }
                }
            }
            
            self.controller.register_tools(mock_mcp)
            
            # Verify tool was registered
            mock_mcp.tool.assert_called_once()
            call_kwargs = mock_mcp.tool.call_args[1]
            assert call_kwargs["name"] == "manage_git_branch"
            assert call_kwargs["description"] == "Test description"
    
    @patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.get_current_user_id')
    def test_get_facade_for_request_with_user_context(self, mock_get_user_id):
        """Test getting facade with user context from JWT."""
        mock_get_user_id.return_value = "jwt-user-123"
        project_id = "test-project"
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id') as mock_validate:
            mock_validate.return_value = "jwt-user-123"
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.get_authenticated_user_id') as mock_get_auth_user:
                mock_get_auth_user.return_value = "jwt-user-123"
                
                result = self.controller._get_facade_for_request(project_id)
                
                assert result == self.mock_facade
                mock_validate.assert_called_once_with("jwt-user-123", "Git branch facade creation")
                self.mock_facade_factory.create_git_branch_facade.assert_called_once_with(
                    project_id=project_id,
                    user_id="jwt-user-123"
                )
    
    @patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.get_current_user_id')
    def test_get_facade_for_request_no_auth_raises_error(self, mock_get_user_id):
        """Test getting facade without authentication raises error."""
        mock_get_user_id.return_value = None
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.controller._get_facade_for_request("test-project")
        
        assert "Git branch facade creation" in str(exc_info.value)
    
    def test_manage_git_branch_create_action(self):
        """Test manage_git_branch with create action."""
        with patch.object(self.controller, 'handle_crud_operations') as mock_crud:
            mock_crud.return_value = {"success": True}
            
            result = self.controller.manage_git_branch(
                action="create",
                project_id="test-project",
                git_branch_name="feature-branch",
                git_branch_description="Test feature"
            )
            
            assert result == {"success": True}
            mock_crud.assert_called_once_with(
                "create", "test-project", "feature-branch", None, "Test feature"
            )
    
    def test_manage_git_branch_assign_agent_action(self):
        """Test manage_git_branch with assign_agent action."""
        with patch.object(self.controller, 'handle_agent_operations') as mock_agent:
            mock_agent.return_value = {"success": True}
            
            result = self.controller.manage_git_branch(
                action="assign_agent",
                project_id="test-project",
                agent_id="agent-123",
                git_branch_name="feature-branch"
            )
            
            assert result == {"success": True}
            mock_agent.assert_called_once_with(
                "assign_agent", "test-project", "feature-branch", None, "agent-123"
            )
    
    def test_manage_git_branch_get_statistics_action(self):
        """Test manage_git_branch with get_statistics action."""
        with patch.object(self.controller, 'handle_advanced_operations') as mock_advanced:
            mock_advanced.return_value = {"success": True}
            
            result = self.controller.manage_git_branch(
                action="get_statistics",
                project_id="test-project",
                git_branch_id="branch-123"
            )
            
            assert result == {"success": True}
            mock_advanced.assert_called_once_with(
                "get_statistics", "test-project", "branch-123"
            )
    
    def test_manage_git_branch_unknown_action(self):
        """Test manage_git_branch with unknown action."""
        result = self.controller.manage_git_branch(
            action="invalid_action",
            project_id="test-project"
        )
        
        assert result["success"] is False
        assert result["error"] == "Unknown action: invalid_action"
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert "valid_actions" in result
    
    def test_handle_crud_operations_create_success(self):
        """Test handling create operation successfully."""
        self.mock_facade.create_git_branch.return_value = {
            "success": True,
            "git_branch": {"id": "branch-123", "name": "feature-branch"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "create", "test-project", "feature-branch", None, "Test description"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.create_git_branch.assert_called_once_with(
                    "test-project", "feature-branch", "Test description"
                )
    
    def test_handle_crud_operations_create_missing_name(self):
        """Test create operation with missing git_branch_name."""
        result = self.controller.handle_crud_operations(
            "create", "test-project", None, None, "Test description"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: git_branch_name"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_get_success(self):
        """Test handling get operation successfully."""
        self.mock_facade.get_git_branch_by_id.return_value = {
            "success": True,
            "git_branch": {"id": "branch-123", "name": "feature-branch", "project_id": "test-project"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "get", "test-project", None, "branch-123"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.get_git_branch_by_id.assert_called_once_with("branch-123")
    
    def test_handle_crud_operations_get_missing_id(self):
        """Test get operation with missing git_branch_id."""
        result = self.controller.handle_crud_operations(
            "get", "test-project", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: git_branch_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_list_success(self):
        """Test handling list operation successfully."""
        self.mock_facade.list_git_branchs.return_value = {
            "success": True,
            "git_branches": [{"id": "branch-1"}, {"id": "branch-2"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "list", "test-project"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.list_git_branchs.assert_called_once_with("test-project")
    
    def test_handle_crud_operations_update_success(self):
        """Test handling update operation successfully."""
        self.mock_facade.update_git_branch.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "update", "test-project", "new-name", "branch-123", "new-description"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.update_git_branch.assert_called_once_with(
                    "branch-123", "new-name", "new-description"
                )
    
    def test_handle_crud_operations_delete_success(self):
        """Test handling delete operation successfully."""
        self.mock_facade.delete_git_branch.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "delete", "test-project", None, "branch-123"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.delete_git_branch.assert_called_once_with("branch-123")
    
    def test_handle_crud_operations_exception(self):
        """Test handling exception in CRUD operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_crud_operations(
                "create", "test-project", "branch-name", None, "description"
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_agent_operations_assign_success(self):
        """Test handling assign_agent operation successfully."""
        # Mock the agent facade factory and agent facade
        with patch('fastmcp.task_management.application.factories.agent_facade_factory.AgentFacadeFactory') as mock_factory_class:
            mock_agent_facade = Mock()
            mock_agent_facade.assign_agent.return_value = {"success": True}
            mock_factory = Mock()
            mock_factory.create_agent_facade.return_value = mock_agent_facade
            mock_factory_class.return_value = mock_factory
            
            with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
                mock_get_facade.return_value = self.mock_facade
                with patch.object(self.controller, '_resolve_branch_name_to_id') as mock_resolve:
                    mock_resolve.return_value = "branch-456"
                    with patch.object(self.controller, '_resolve_agent_identifier') as mock_resolve_agent:
                        mock_resolve_agent.return_value = "agent-123"
                        with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                            mock_enhance.return_value = {"success": True, "enhanced": True}
                            
                            result = self.controller.handle_agent_operations(
                                "assign_agent", "test-project", "branch-name", "branch-456", "agent-123"
                            )
                            
                            assert result == {"success": True, "enhanced": True}
                            # Should create agent facade and call assign_agent
                            mock_factory.create_agent_facade.assert_called_once_with(project_id="test-project")
                            mock_agent_facade.assign_agent.assert_called_once()
    
    def test_handle_agent_operations_missing_agent_id(self):
        """Test agent operation with missing agent_id."""
        result = self.controller.handle_agent_operations(
            "assign_agent", "test-project", "branch-name", "branch-456", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: agent_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_agent_operations_missing_branch_identifier(self):
        """Test agent operation with missing branch identifier."""
        result = self.controller.handle_agent_operations(
            "assign_agent", "test-project", None, None, "agent-123"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: git_branch_id or git_branch_name"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_advanced_operations_get_statistics_success(self):
        """Test handling get_statistics operation successfully."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_run_async_with_context') as mock_run_async:
                mock_run_async.return_value = {
                    "branch_name": "feature-branch",
                    "status": "active",
                    "priority": "high",
                    "assigned_agent_id": "agent-123",
                    "task_count": 5,
                    "completed_task_count": 3,
                    "progress_percentage": 60,
                    "created_at": "2024-01-01",
                    "updated_at": "2024-01-02"
                }
                with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                    mock_enhance.return_value = {"success": True, "enhanced": True}
                    
                    result = self.controller.handle_advanced_operations(
                        "get_statistics", "test-project", "branch-123"
                    )
                    
                    assert result == {"success": True, "enhanced": True}
    
    def test_handle_advanced_operations_missing_branch_id(self):
        """Test advanced operation with missing git_branch_id."""
        result = self.controller.handle_advanced_operations(
            "get_statistics", "test-project", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: git_branch_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_advanced_operations_archive_success(self):
        """Test handling archive operations successfully."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_advanced_operations(
                    "archive", "test-project", "branch-123"
                )
                
                assert result == {"success": True, "enhanced": True}
    
    def test_handle_advanced_operations_restore_success(self):
        """Test handling restore operations successfully."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_advanced_operations(
                    "restore", "test-project", "branch-123"
                )
                
                assert result == {"success": True, "enhanced": True}
    
    def test_get_git_branch_management_descriptions(self):
        """Test getting git branch management descriptions."""
        with patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.description_loader') as mock_loader:
            mock_loader.get_all_descriptions.return_value = {
                "git_branches": {
                    "manage_git_branch": {
                        "description": "Test description",
                        "parameters": {"action": "Action param"}
                    }
                }
            }
            
            result = self.controller._get_git_branch_management_descriptions()
            
            expected = {
                "manage_git_branch": {
                    "description": "Test description",
                    "parameters": {"action": "Action param"}
                }
            }
            assert result == expected
    
    def test_create_missing_field_error(self):
        """Test creating missing field error response."""
        result = self.controller._create_missing_field_error("test_field", "test_action")
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: test_field"
        assert result["error_code"] == "MISSING_FIELD"
        assert result["field"] == "test_field"
        assert result["action"] == "test_action"
    
    def test_create_invalid_action_error(self):
        """Test creating invalid action error response."""
        result = self.controller._create_invalid_action_error("invalid_action")
        
        assert result["success"] is False
        assert result["error"] == "Invalid action: invalid_action"
        assert result["error_code"] == "INVALID_ACTION"
        assert "valid_actions" in result
    
    def test_enhance_response_with_workflow_guidance_success(self):
        """Test enhancing successful response with workflow guidance."""
        response = {"success": True, "git_branch": {"id": "branch-123"}}
        
        mock_guidance = {"next_steps": ["Create tasks"], "hints": ["Test hint"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "test-project", "branch-123"
        )
        
        assert result["success"] is True
        assert result["workflow_guidance"] == mock_guidance
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", {"project_id": "test-project", "git_branch_id": "branch-123"}
        )
    
    def test_enhance_response_with_workflow_guidance_failure(self):
        """Test enhancing failed response (no guidance added)."""
        response = {"success": False, "error": "Test error"}
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "test-project"
        )
        
        assert result == response  # Should be unchanged
        assert "workflow_guidance" not in result
        self.controller._workflow_guidance.generate_guidance.assert_not_called()


class TestGitBranchMCPControllerIntegration:
    """Integration tests for GitBranchMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=GitBranchFacadeFactory)
        self.mock_facade = Mock(spec=GitBranchApplicationFacade)
        self.mock_facade_factory.create_git_branch_facade.return_value = self.mock_facade
        
        with patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.GitBranchWorkflowFactory'):
            self.controller = GitBranchMCPController(self.mock_facade_factory)
    
    @patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.get_current_user_id')
    def test_complete_create_workflow(self, mock_get_user_id):
        """Test complete git branch creation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.create_git_branch.return_value = {
            "success": True,
            "git_branch": {"id": "branch-123", "name": "feature-branch"}
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Create tasks in branch"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_git_branch(
                action="create",
                project_id="test-project",
                git_branch_name="feature-branch",
                git_branch_description="Test feature branch"
            )
            
            # Verify successful creation
            assert result["success"] is True
            assert result["git_branch"]["id"] == "branch-123"
            assert result["workflow_guidance"] == mock_guidance
            
            # Verify facade was called correctly
            self.mock_facade_factory.create_git_branch_facade.assert_called_once_with(
                project_id="test-project",
                user_id="test-user"
            )
            
            self.mock_facade.create_git_branch.assert_called_once_with(
                "test-project", "feature-branch", "Test feature branch"
            )
    
    @patch('fastmcp.task_management.interface.controllers.git_branch_mcp_controller.get_current_user_id')
    def test_complete_assign_agent_workflow(self, mock_get_user_id):
        """Test complete agent assignment workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Agent can now work on branch tasks"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.auth_helper.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            with patch('fastmcp.task_management.interface.controllers.auth_helper.get_authenticated_user_id') as mock_get_auth_user:
                mock_get_auth_user.return_value = "test-user"
                
                with patch('fastmcp.task_management.application.factories.agent_facade_factory.AgentFacadeFactory') as mock_factory_class:
                    # Mock the agent facade and its methods
                    mock_agent_facade = Mock()
                    mock_agent_facade.assign_agent.return_value = {"success": True}
                    mock_factory = Mock()
                    mock_factory.create_agent_facade.return_value = mock_agent_facade
                    mock_factory_class.return_value = mock_factory
                    
                    result = self.controller.manage_git_branch(
                        action="assign_agent",
                        project_id="test-project",
                        agent_id="agent-123",
                        git_branch_id="branch-456"
                    )
                    
                    # Verify successful assignment
                    assert result["success"] is True
                    assert result["workflow_guidance"] == mock_guidance
                    
                    # Verify agent facade was called correctly
                    mock_agent_facade.assign_agent.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])