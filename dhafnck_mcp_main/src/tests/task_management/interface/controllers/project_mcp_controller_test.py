"""Test suite for ProjectMCPController.

Tests the project MCP controller including:
- Tool registration and MCP integration
- CRUD operations for projects
- Health checks and maintenance
- Authentication and user context
- Error handling and validation
- Workflow guidance integration
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.project_mcp_controller import ProjectMCPController
from fastmcp.task_management.application.factories.project_facade_factory import ProjectFacadeFactory
from fastmcp.task_management.application.facades.project_application_facade import ProjectApplicationFacade
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestProjectMCPController:
    """Test cases for ProjectMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=ProjectFacadeFactory)
        self.mock_facade = Mock(spec=ProjectApplicationFacade)
        self.mock_facade_factory.create_project_facade.return_value = self.mock_facade
        
        # Mock workflow guidance
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.ProjectWorkflowFactory'):
            self.controller = ProjectMCPController(self.mock_facade_factory)
    
    def test_init(self):
        """Test controller initialization."""
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.ProjectWorkflowFactory') as mock_workflow_factory:
            mock_workflow = Mock()
            mock_workflow_factory.create.return_value = mock_workflow
            
            controller = ProjectMCPController(self.mock_facade_factory)
            
            assert controller._project_facade_factory == self.mock_facade_factory
            assert controller._workflow_guidance == mock_workflow
            mock_workflow_factory.create.assert_called_once()
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        
        with patch.object(self.controller, '_get_project_management_descriptions') as mock_get_desc:
            mock_get_desc.return_value = {
                "manage_project": {
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
            assert call_kwargs["name"] == "manage_project"
            assert call_kwargs["description"] == "Test description"
    
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.get_current_user_id')
    def test_get_facade_for_request_with_user_context(self, mock_get_user_id):
        """Test getting facade with user context from JWT."""
        mock_get_user_id.return_value = "jwt-user-123"
        
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "jwt-user-123"
            
            result = self.controller._get_facade_for_request()
            
            assert result == self.mock_facade
            mock_validate.assert_called_once_with("jwt-user-123", "Project facade creation")
            self.mock_facade_factory.create_project_facade.assert_called_once_with(
                user_id="jwt-user-123"
            )
    
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.get_current_user_id')
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.AuthConfig')
    def test_get_facade_for_request_compatibility_mode(self, mock_auth_config, mock_get_user_id):
        """Test getting facade with compatibility mode."""
        mock_get_user_id.return_value = None
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-user"
        
        result = self.controller._get_facade_for_request()
        
        assert result == self.mock_facade
        mock_auth_config.log_authentication_bypass.assert_called_once_with(
            "Project facade creation", "compatibility mode"
        )
        self.mock_facade_factory.create_project_facade.assert_called_once_with(
            user_id="compatibility-user"
        )
    
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.get_current_user_id')
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.AuthConfig')
    def test_get_facade_for_request_no_auth(self, mock_auth_config, mock_get_user_id):
        """Test getting facade without authentication raises error."""
        mock_get_user_id.return_value = None
        mock_auth_config.is_default_user_allowed.return_value = False
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.controller._get_facade_for_request()
        
        assert "Project facade creation" in str(exc_info.value)
    
    def test_manage_project_create_action(self):
        """Test manage_project with create action."""
        with patch.object(self.controller, 'handle_crud_operations') as mock_crud:
            mock_crud.return_value = {"success": True}
            
            result = self.controller.manage_project(
                action="create",
                name="test-project",
                description="Test project description"
            )
            
            assert result == {"success": True}
            mock_crud.assert_called_once_with(
                "create", None, "test-project", "Test project description"
            )
    
    def test_manage_project_health_check_action(self):
        """Test manage_project with project_health_check action."""
        with patch.object(self.controller, 'handle_maintenance_operations') as mock_maintenance:
            mock_maintenance.return_value = {"success": True}
            
            result = self.controller.manage_project(
                action="project_health_check",
                project_id="test-project"
            )
            
            assert result == {"success": True}
            mock_maintenance.assert_called_once_with(
                "project_health_check", "test-project", False
            )
    
    def test_manage_project_unknown_action(self):
        """Test manage_project with unknown action."""
        result = self.controller.manage_project(
            action="invalid_action",
            name="test-project"
        )
        
        assert result["success"] is False
        assert result["error"] == "Unknown action: invalid_action"
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert "valid_actions" in result
    
    def test_handle_crud_operations_create_success(self):
        """Test handling create operation successfully."""
        self.mock_facade.create_project.return_value = {
            "success": True,
            "project": {"id": "project-123", "name": "test-project"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "create", None, "test-project", "Test description"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.create_project.assert_called_once_with(
                    None, "test-project", "Test description"
                )
    
    def test_handle_crud_operations_create_missing_name(self):
        """Test create operation with missing name."""
        result = self.controller.handle_crud_operations(
            "create", None, None, "Test description"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: name"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_get_success(self):
        """Test handling get operation successfully."""
        self.mock_facade.get_project.return_value = {
            "success": True,
            "project": {"id": "project-123", "name": "test-project"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "get", "project-123", "test-project"
                )
                
                assert result == {"success": True, "enhanced": True}
                # Should use project_id if provided, otherwise name
                self.mock_facade.get_project.assert_called_once_with("project-123")
    
    def test_handle_crud_operations_get_by_name(self):
        """Test get operation using name when project_id not provided."""
        self.mock_facade.get_project_by_name.return_value = {
            "success": True,
            "project": {"id": "project-123", "name": "test-project"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "get", None, "test-project"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.get_project_by_name.assert_called_once_with("test-project")
    
    def test_handle_crud_operations_get_missing_identifier(self):
        """Test get operation with missing project identifier."""
        result = self.controller.handle_crud_operations(
            "get", None, None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: project_id or name"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_list_success(self):
        """Test handling list operation successfully."""
        self.mock_facade.list_projects.return_value = {
            "success": True,
            "projects": [{"id": "project-1"}, {"id": "project-2"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations("list")
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.list_projects.assert_called_once()
    
    def test_handle_crud_operations_update_success(self):
        """Test handling update operation successfully."""
        self.mock_facade.update_project.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "update", "project-123", "new-name", "new-description"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.update_project.assert_called_once_with(
                    "project-123", "new-name", "new-description"
                )
    
    def test_handle_crud_operations_update_missing_project_id(self):
        """Test update operation with missing project_id."""
        result = self.controller.handle_crud_operations(
            "update", None, "new-name", "new-description"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: project_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_exception(self):
        """Test handling exception in CRUD operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_crud_operations(
                "create", None, "test-project", "description"
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_maintenance_operations_health_check_success(self):
        """Test handling health check operation successfully."""
        self.mock_facade.project_health_check.return_value = {
            "success": True,
            "health_score": 85,
            "issues": []
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_maintenance_operations(
                    "project_health_check", "project-123", False
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.project_health_check.assert_called_once_with("project-123")
    
    def test_handle_maintenance_operations_cleanup_obsolete_success(self):
        """Test handling cleanup obsolete operation successfully."""
        self.mock_facade.cleanup_obsolete.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_maintenance_operations(
                    "cleanup_obsolete", "project-123", True
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.cleanup_obsolete.assert_called_once_with("project-123", True)
    
    def test_handle_maintenance_operations_validate_integrity_success(self):
        """Test handling validate integrity operation successfully."""
        self.mock_facade.validate_integrity.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_maintenance_operations(
                    "validate_integrity", "project-123", False
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.validate_integrity.assert_called_once_with("project-123", False)
    
    def test_handle_maintenance_operations_rebalance_agents_success(self):
        """Test handling rebalance agents operation successfully."""
        self.mock_facade.rebalance_agents.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_maintenance_operations(
                    "rebalance_agents", "project-123", False
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.rebalance_agents.assert_called_once_with("project-123", False)
    
    def test_handle_maintenance_operations_missing_project_id(self):
        """Test maintenance operation with missing project_id."""
        result = self.controller.handle_maintenance_operations(
            "project_health_check", None, False
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: project_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_maintenance_operations_exception(self):
        """Test handling exception in maintenance operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_maintenance_operations(
                "project_health_check", "project-123", False
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_get_project_management_descriptions(self):
        """Test getting project management descriptions."""
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.description_loader') as mock_loader:
            mock_loader.get_all_descriptions.return_value = {
                "projects": {
                    "manage_project": {
                        "description": "Test description",
                        "parameters": {"action": "Action param"}
                    }
                }
            }
            
            result = self.controller._get_project_management_descriptions()
            
            expected = {
                "manage_project": {
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
        response = {"success": True, "project": {"id": "project-123"}}
        
        mock_guidance = {"next_steps": ["Create git branches"], "hints": ["Test hint"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "project-123"
        )
        
        assert result["success"] is True
        assert result["workflow_guidance"] == mock_guidance
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", {"project_id": "project-123"}
        )
    
    def test_enhance_response_with_workflow_guidance_failure(self):
        """Test enhancing failed response (no guidance added)."""
        response = {"success": False, "error": "Test error"}
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "project-123"
        )
        
        assert result == response  # Should be unchanged
        assert "workflow_guidance" not in result
        self.controller._workflow_guidance.generate_guidance.assert_not_called()
    
    def test_enhance_response_extract_project_id_from_response(self):
        """Test extracting project ID from response for guidance."""
        response = {
            "success": True,
            "project": {"id": "new-project-123", "name": "test-project"}
        }
        
        mock_guidance = {"next_steps": ["Test step"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create"
        )
        
        # Should extract project ID from response
        expected_context = {"project_id": "new-project-123"}
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", expected_context
        )


class TestProjectMCPControllerIntegration:
    """Integration tests for ProjectMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=ProjectFacadeFactory)
        self.mock_facade = Mock(spec=ProjectApplicationFacade)
        self.mock_facade_factory.create_project_facade.return_value = self.mock_facade
        
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.ProjectWorkflowFactory'):
            self.controller = ProjectMCPController(self.mock_facade_factory)
    
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.get_current_user_id')
    def test_complete_create_workflow(self, mock_get_user_id):
        """Test complete project creation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.create_project.return_value = {
            "success": True,
            "project": {"id": "project-123", "name": "test-project"}
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Create git branches"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_project(
                action="create",
                name="test-project",
                description="Test project description"
            )
            
            # Verify successful creation
            assert result["success"] is True
            assert result["project"]["id"] == "project-123"
            assert result["workflow_guidance"] == mock_guidance
            
            # Verify facade was called correctly
            self.mock_facade_factory.create_project_facade.assert_called_once_with(
                user_id="test-user"
            )
            
            self.mock_facade.create_project.assert_called_once_with(
                None, "test-project", "Test project description"
            )
    
    @patch('fastmcp.task_management.interface.controllers.project_mcp_controller.get_current_user_id')
    def test_complete_health_check_workflow(self, mock_get_user_id):
        """Test complete project health check workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.project_health_check.return_value = {
            "success": True,
            "health_score": 75,
            "issues": ["Low task completion rate"]
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Address health issues"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.project_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_project(
                action="project_health_check",
                project_id="project-123"
            )
            
            # Verify successful health check
            assert result["success"] is True
            assert result["health_score"] == 75
            assert result["workflow_guidance"] == mock_guidance
            
            # Verify facade was called correctly
            self.mock_facade.project_health_check.assert_called_once_with("project-123")


if __name__ == "__main__":
    pytest.main([__file__])