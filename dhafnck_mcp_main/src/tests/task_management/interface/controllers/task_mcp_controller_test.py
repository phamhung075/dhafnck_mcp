"""Test suite for TaskMCPController.

Tests the task MCP controller including:
- Tool registration and MCP integration
- CRUD operations for tasks
- Task search and filtering
- Progress tracking and completion
- Authentication and user context
- Error handling and validation
- Workflow guidance integration
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestTaskMCPController:
    """Test cases for TaskMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=TaskFacadeFactory)
        self.mock_facade = Mock(spec=TaskApplicationFacade)
        self.mock_facade_factory.create_task_facade.return_value = self.mock_facade
        
        # Mock workflow guidance
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.TaskWorkflowFactory'):
            self.controller = TaskMCPController(self.mock_facade_factory)
    
    def test_init(self):
        """Test controller initialization."""
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.TaskWorkflowFactory') as mock_workflow_factory:
            mock_workflow = Mock()
            mock_workflow_factory.create.return_value = mock_workflow
            
            controller = TaskMCPController(self.mock_facade_factory)
            
            assert controller._task_facade_factory == self.mock_facade_factory
            assert controller._workflow_guidance == mock_workflow
            mock_workflow_factory.create.assert_called_once()
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        
        with patch.object(self.controller, '_get_task_management_descriptions') as mock_get_desc:
            mock_get_desc.return_value = {
                "manage_task": {
                    "description": "Test description",
                    "parameters": {
                        "action": "Action parameter",
                        "git_branch_id": "Branch ID parameter"
                    }
                }
            }
            
            self.controller.register_tools(mock_mcp)
            
            # Verify tool was registered
            mock_mcp.tool.assert_called_once()
            call_kwargs = mock_mcp.tool.call_args[1]
            assert call_kwargs["name"] == "manage_task"
            assert call_kwargs["description"] == "Test description"
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_get_facade_for_request_with_user_context(self, mock_get_user_id):
        """Test getting facade with user context from JWT."""
        mock_get_user_id.return_value = "jwt-user-123"
        git_branch_id = "branch-123"
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "jwt-user-123"
            
            result = self.controller._get_facade_for_request(git_branch_id)
            
            assert result == self.mock_facade
            mock_validate.assert_called_once_with("jwt-user-123", "Task facade creation")
            self.mock_facade_factory.create_task_facade.assert_called_once_with(
                git_branch_id=git_branch_id,
                user_id="jwt-user-123"
            )
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.AuthConfig')
    def test_get_facade_for_request_compatibility_mode(self, mock_auth_config, mock_get_user_id):
        """Test getting facade with compatibility mode."""
        mock_get_user_id.return_value = None
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-user"
        git_branch_id = "branch-123"
        
        result = self.controller._get_facade_for_request(git_branch_id)
        
        assert result == self.mock_facade
        mock_auth_config.log_authentication_bypass.assert_called_once_with(
            "Task facade creation", "compatibility mode"
        )
        self.mock_facade_factory.create_task_facade.assert_called_once_with(
            git_branch_id=git_branch_id,
            user_id="compatibility-user"
        )
    
    def test_manage_task_create_action(self):
        """Test manage_task with create action."""
        with patch.object(self.controller, 'handle_crud_operations') as mock_crud:
            mock_crud.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="create",
                git_branch_id="branch-123",
                title="Test task",
                description="Test description"
            )
            
            assert result == {"success": True}
            mock_crud.assert_called_once()
    
    def test_manage_task_search_action(self):
        """Test manage_task with search action."""
        with patch.object(self.controller, 'handle_search_operations') as mock_search:
            mock_search.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="search",
                git_branch_id="branch-123",
                query="test query"
            )
            
            assert result == {"success": True}
            mock_search.assert_called_once_with(
                "search", "branch-123", "test query", None
            )
    
    def test_manage_task_next_action(self):
        """Test manage_task with next action."""
        with patch.object(self.controller, 'handle_recommendation_operations') as mock_recommend:
            mock_recommend.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="next",
                git_branch_id="branch-123",
                include_context=True
            )
            
            assert result == {"success": True}
            mock_recommend.assert_called_once_with(
                "next", "branch-123", True
            )
    
    def test_manage_task_unknown_action(self):
        """Test manage_task with unknown action."""
        result = self.controller.manage_task(
            action="invalid_action",
            git_branch_id="branch-123"
        )
        
        assert result["success"] is False
        assert result["error"] == "Unknown action: invalid_action"
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert "valid_actions" in result
    
    def test_handle_crud_operations_create_success(self):
        """Test handling create operation successfully."""
        self.mock_facade.create_task.return_value = {
            "success": True,
            "task": {"id": "task-123", "title": "Test task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "create", "branch-123", None, "Test task", "Test description",
                    None, "medium", None, None, None, None, None, None, None
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.create_task.assert_called_once()
    
    def test_handle_crud_operations_create_missing_title(self):
        """Test create operation with missing title."""
        result = self.controller.handle_crud_operations(
            "create", "branch-123", None, None, "Test description"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: title"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_get_success(self):
        """Test handling get operation successfully."""
        self.mock_facade.get_task.return_value = {
            "success": True,
            "task": {"id": "task-123", "title": "Test task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "get", "branch-123", "task-456"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.get_task.assert_called_once_with("task-456", True)
    
    def test_handle_crud_operations_get_missing_task_id(self):
        """Test get operation with missing task_id."""
        result = self.controller.handle_crud_operations(
            "get", "branch-123", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: task_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_list_success(self):
        """Test handling list operation successfully."""
        self.mock_facade.list_tasks.return_value = {
            "success": True,
            "tasks": [{"id": "task-1"}, {"id": "task-2"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "list", "branch-123", None, None, None, "todo", "high", None, None, None, None, 10
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.list_tasks.assert_called_once()
    
    def test_handle_crud_operations_update_success(self):
        """Test handling update operation successfully."""
        self.mock_facade.update_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "update", "branch-123", "task-456", "New title", "New description",
                    "in_progress", "high", "Details", None, None, None, None, "context-123"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.update_task.assert_called_once()
    
    def test_handle_crud_operations_complete_success(self):
        """Test handling complete operation successfully."""
        self.mock_facade.complete_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "complete", "branch-123", "task-456", None, None, None, None, None,
                    "Task completed successfully", "All tests passed"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.complete_task.assert_called_once_with(
                    "task-456", "Task completed successfully", "All tests passed"
                )
    
    def test_handle_crud_operations_delete_success(self):
        """Test handling delete operation successfully."""
        self.mock_facade.delete_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_crud_operations(
                    "delete", "branch-123", "task-456"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.delete_task.assert_called_once_with("task-456")
    
    def test_handle_crud_operations_exception(self):
        """Test handling exception in CRUD operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_crud_operations(
                "create", "branch-123", None, "Test task", "description"
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_search_operations_success(self):
        """Test handling search operations successfully."""
        self.mock_facade.search_tasks.return_value = {
            "success": True,
            "tasks": [{"id": "task-1", "title": "Found task"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_search_operations(
                    "search", "branch-123", "test query", 10
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.search_tasks.assert_called_once_with("test query", 10)
    
    def test_handle_search_operations_missing_query(self):
        """Test search operation with missing query."""
        result = self.controller.handle_search_operations(
            "search", "branch-123", None, 10
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: query"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_search_operations_exception(self):
        """Test handling exception in search operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_search_operations(
                "search", "branch-123", "test query", 10
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_recommendation_operations_success(self):
        """Test handling recommendation operations successfully."""
        self.mock_facade.get_next_task.return_value = {
            "success": True,
            "task": {"id": "task-123", "title": "Next task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_recommendation_operations(
                    "next", "branch-123", True
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.get_next_task.assert_called_once_with(True)
    
    def test_handle_recommendation_operations_exception(self):
        """Test handling exception in recommendation operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_recommendation_operations(
                "next", "branch-123", True
            )
            
            assert result["success"] is False
            assert "Operation failed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_dependency_operations_success(self):
        """Test handling dependency operations successfully."""
        self.mock_facade.add_dependency.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_dependency_operations(
                    "add_dependency", "branch-123", "task-123", "dep-task-456"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.add_dependency.assert_called_once_with("task-123", "dep-task-456")
    
    def test_handle_dependency_operations_missing_task_id(self):
        """Test dependency operation with missing task_id."""
        result = self.controller.handle_dependency_operations(
            "add_dependency", "branch-123", None, "dep-task-456"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: task_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_dependency_operations_missing_dependency_id(self):
        """Test dependency operation with missing dependency_id."""
        result = self.controller.handle_dependency_operations(
            "add_dependency", "branch-123", "task-123", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: dependency_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_dependency_operations_remove_dependency(self):
        """Test handling remove dependency operation."""
        self.mock_facade.remove_dependency.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            with patch.object(self.controller, '_enhance_response_with_workflow_guidance') as mock_enhance:
                mock_enhance.return_value = {"success": True, "enhanced": True}
                
                result = self.controller.handle_dependency_operations(
                    "remove_dependency", "branch-123", "task-123", "dep-task-456"
                )
                
                assert result == {"success": True, "enhanced": True}
                self.mock_facade.remove_dependency.assert_called_once_with("task-123", "dep-task-456")
    
    def test_get_task_management_descriptions(self):
        """Test getting task management descriptions."""
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.description_loader') as mock_loader:
            mock_loader.get_all_descriptions.return_value = {
                "tasks": {
                    "manage_task": {
                        "description": "Test description",
                        "parameters": {"action": "Action param"}
                    }
                }
            }
            
            result = self.controller._get_task_management_descriptions()
            
            expected = {
                "manage_task": {
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
        response = {"success": True, "task": {"id": "task-123"}}
        
        mock_guidance = {"next_steps": ["Continue work"], "hints": ["Test hint"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "branch-123", "task-123"
        )
        
        assert result["success"] is True
        assert result["workflow_guidance"] == mock_guidance
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", {"git_branch_id": "branch-123", "task_id": "task-123"}
        )
    
    def test_enhance_response_with_workflow_guidance_failure(self):
        """Test enhancing failed response (no guidance added)."""
        response = {"success": False, "error": "Test error"}
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "branch-123"
        )
        
        assert result == response  # Should be unchanged
        assert "workflow_guidance" not in result
        self.controller._workflow_guidance.generate_guidance.assert_not_called()
    
    def test_enhance_response_extract_task_id_from_response(self):
        """Test extracting task ID from response for guidance."""
        response = {
            "success": True,
            "task": {"id": "new-task-123", "title": "test-task"}
        }
        
        mock_guidance = {"next_steps": ["Test step"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_response_with_workflow_guidance(
            response, "create", "branch-123"
        )
        
        # Should extract task ID from response
        expected_context = {
            "git_branch_id": "branch-123",
            "task_id": "new-task-123"
        }
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", expected_context
        )


class TestTaskMCPControllerIntegration:
    """Integration tests for TaskMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=TaskFacadeFactory)
        self.mock_facade = Mock(spec=TaskApplicationFacade)
        self.mock_facade_factory.create_task_facade.return_value = self.mock_facade
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.TaskWorkflowFactory'):
            self.controller = TaskMCPController(self.mock_facade_factory)
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_complete_create_workflow(self, mock_get_user_id):
        """Test complete task creation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.create_task.return_value = {
            "success": True,
            "task": {"id": "task-123", "title": "test-task"}
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Start working on task"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_task(
                action="create",
                git_branch_id="branch-123",
                title="test-task",
                description="Test task description"
            )
            
            # Verify successful creation
            assert result["success"] is True
            assert result["task"]["id"] == "task-123"
            assert result["workflow_guidance"] == mock_guidance
            
            # Verify facade was called correctly
            self.mock_facade_factory.create_task_facade.assert_called_once_with(
                git_branch_id="branch-123",
                user_id="test-user"
            )
            
            self.mock_facade.create_task.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_complete_next_task_workflow(self, mock_get_user_id):
        """Test complete next task recommendation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.get_next_task.return_value = {
            "success": True,
            "task": {"id": "task-456", "title": "recommended-task"}
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Start on this recommended task"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_task(
                action="next",
                git_branch_id="branch-123",
                include_context=True
            )
            
            # Verify successful recommendation
            assert result["success"] is True
            assert result["task"]["id"] == "task-456"
            assert result["workflow_guidance"] == mock_guidance
            
            # Verify facade was called correctly
            self.mock_facade.get_next_task.assert_called_once_with(True)


if __name__ == "__main__":
    pytest.main([__file__])