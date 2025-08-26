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
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.services.response_enrichment_service import ResponseEnrichmentService
from fastmcp.task_management.application.services.parameter_enforcement_service import ParameterEnforcementService
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
        
        self.controller = TaskMCPController(self.mock_facade_factory)
    
    def test_init(self):
        """Test controller initialization."""
        controller = TaskMCPController(self.mock_facade_factory)
        
        assert controller._task_facade_factory == self.mock_facade_factory
    
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
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_authenticated_user_id')
    def test_get_facade_for_request_with_user_context(self, mock_get_auth_user_id):
        """Test getting facade with user context from JWT."""
        mock_get_auth_user_id.return_value = "jwt-user-123"
        git_branch_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock database session to return branch data
        with patch('fastmcp.task_management.infrastructure.database.session_manager.get_session_manager') as mock_session_mgr:
            mock_session = MagicMock()
            mock_session_mgr.return_value.get_session.return_value.__enter__.return_value = mock_session
            
            # Mock database query result
            mock_result = MagicMock()
            mock_result.fetchone.return_value = ("test-project-id", "feature/test-branch")
            mock_session.execute.return_value = mock_result
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                mock_validate.return_value = "jwt-user-123"
                
                result = self.controller._get_facade_for_request(git_branch_id)
                
                assert result == self.mock_facade
                mock_validate.assert_called_once_with("jwt-user-123", "Task facade creation")
                self.mock_facade_factory.create_task_facade.assert_called_once_with(
                    git_branch_id=git_branch_id,
                    user_id="jwt-user-123"
                )
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_authenticated_user_id')
    def test_get_facade_for_request_no_auth_raises_error(self, mock_get_auth_user_id):
        """Test getting facade without authentication raises error."""
        mock_get_auth_user_id.side_effect = UserAuthenticationRequiredError("No auth")
        git_branch_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.controller._get_facade_for_request(git_branch_id)
        
        assert "Task facade creation" in str(exc_info.value)
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_create_action(self, mock_get_user_id):
        """Test manage_task with create action."""
        mock_get_user_id.return_value = "test-user-123"
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade, \
             patch.object(self.controller, 'handle_crud_operations') as mock_crud:
            mock_get_facade.return_value = self.mock_facade
            mock_crud.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="create",
                git_branch_id="550e8400-e29b-41d4-a716-446655440000",
                title="Test task",
                description="Test description"
            )
            
            assert result == {"success": True}
            mock_crud.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_search_action(self, mock_get_user_id):
        """Test manage_task with search action."""
        mock_get_user_id.return_value = "test-user-123"
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade, \
             patch.object(self.controller, 'handle_search_operations') as mock_search:
            mock_get_facade.return_value = self.mock_facade
            mock_search.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="search",
                git_branch_id="550e8400-e29b-41d4-a716-446655440000",
                query="test query"
            )
            
            assert result == {"success": True}
            mock_search.assert_called_once_with(
                "search", "550e8400-e29b-41d4-a716-446655440000", "test query", None
            )
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_next_action(self, mock_get_user_id):
        """Test manage_task with next action."""
        mock_get_user_id.return_value = "test-user-123"
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade, \
             patch.object(self.controller, 'handle_recommendation_operations') as mock_recommend:
            mock_get_facade.return_value = self.mock_facade
            mock_recommend.return_value = {"success": True}
            
            result = self.controller.manage_task(
                action="next",
                git_branch_id="550e8400-e29b-41d4-a716-446655440000",
                include_context=True
            )
            
            assert result == {"success": True}
            mock_recommend.assert_called_once_with(
                "next", "550e8400-e29b-41d4-a716-446655440000", True
            )
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_unknown_action(self, mock_get_user_id):
        """Test manage_task with unknown action."""
        mock_get_user_id.return_value = "test-user-123"
        
        result = self.controller.manage_task(
            action="invalid_action",
            git_branch_id="550e8400-e29b-41d4-a716-446655440000"
        )
        
        assert result["success"] is False
        assert result["error"] == "Unknown action: invalid_action"
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert "valid_actions" in result
    
    def test_handle_crud_operations_create_success(self):
        """Test handling create operation successfully."""
        self.mock_facade.create_task.return_value = {
            "success": True,
            "task": {"id": "550e8400-e29b-41d4-a716-446655440001", "title": "Test task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                "create", "550e8400-e29b-41d4-a716-446655440000", None, "Test task", "Test description",
                None, "medium", None, None, None, None, None, None, None
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "550e8400-e29b-41d4-a716-446655440001"
            self.mock_facade.create_task.assert_called_once()
    
    def test_handle_crud_operations_create_missing_title(self):
        """Test create operation with missing title."""
        result = self.controller.handle_crud_operations(
            "create", "550e8400-e29b-41d4-a716-446655440000", None, None, "Test description"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: title"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_get_success(self):
        """Test handling get operation successfully."""
        self.mock_facade.get_task.return_value = {
            "success": True,
            "task": {"id": "550e8400-e29b-41d4-a716-446655440001", "title": "Test task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                "get", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440002"
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "550e8400-e29b-41d4-a716-446655440001"
            self.mock_facade.get_task.assert_called_once_with("550e8400-e29b-41d4-a716-446655440002", True)
    
    def test_handle_crud_operations_get_missing_task_id(self):
        """Test get operation with missing task_id."""
        result = self.controller.handle_crud_operations(
            "get", "550e8400-e29b-41d4-a716-446655440000", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: task_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_crud_operations_list_success(self):
        """Test handling list operation successfully."""
        self.mock_facade.list_tasks.return_value = {
            "success": True,
            "tasks": [{"id": "550e8400-e29b-41d4-a716-446655440004"}, {"id": "550e8400-e29b-41d4-a716-446655440005"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            # Use handle_list_search_next instead of handle_crud_operations for list action
            result = self.controller.handle_list_search_next(
                "list", "550e8400-e29b-41d4-a716-446655440000", "todo", "high", None, None, 10
            )
            
            assert result["success"] is True
            assert len(result["tasks"]) == 2
            self.mock_facade.list_tasks.assert_called_once()
    
    def test_handle_crud_operations_update_success(self):
        """Test handling update operation successfully."""
        self.mock_facade.update_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                "update", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440002", "New title", "New description",
                "in_progress", "high", "Details", None, None, None, None, "context-123"
            )
            
            assert result["success"] is True
            self.mock_facade.update_task.assert_called_once()
    
    def test_handle_crud_operations_complete_success(self):
        """Test handling complete operation successfully."""
        self.mock_facade.complete_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                action="complete",
                git_branch_id="550e8400-e29b-41d4-a716-446655440000",
                task_id="550e8400-e29b-41d4-a716-446655440002",
                completion_summary="Task completed successfully",
                testing_notes="All tests passed"
            )
            
            assert result["success"] is True
            self.mock_facade.complete_task.assert_called_once_with(
                task_id="550e8400-e29b-41d4-a716-446655440002", 
                completion_summary="Task completed successfully", 
                testing_notes="All tests passed"
            )
    
    def test_handle_crud_operations_delete_success(self):
        """Test handling delete operation successfully."""
        self.mock_facade.delete_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                "delete", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440002"
            )
            
            assert result["success"] is True
            self.mock_facade.delete_task.assert_called_once_with("550e8400-e29b-41d4-a716-446655440002")
    
    def test_handle_crud_operations_exception(self):
        """Test handling exception in CRUD operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_crud_operations(
                "create", "550e8400-e29b-41d4-a716-446655440000", None, "Test task", "description"
            )
            
            assert result["success"] is False
            assert "could not be completed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_search_operations_success(self):
        """Test handling search operations successfully."""
        self.mock_facade.search_tasks.return_value = {
            "success": True,
            "tasks": [{"id": "550e8400-e29b-41d4-a716-446655440004", "title": "Found task"}]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_search_operations(
                action="search", 
                query="test query", 
                limit=10,
                git_branch_id="550e8400-e29b-41d4-a716-446655440000"
            )
            
            assert result["success"] is True
            assert len(result["tasks"]) == 1
            self.mock_facade.search_tasks.assert_called_once_with("test query", 10)
    
    def test_handle_search_operations_missing_query(self):
        """Test search operation with missing query."""
        result = self.controller.handle_search_operations(
            action="search", 
            query=None, 
            limit=10,
            git_branch_id="550e8400-e29b-41d4-a716-446655440000"
        )
        
        assert result["success"] is False
        assert result["error"]["message"] == "Validation failed for field: query"
        assert result["error"]["code"] == "VALIDATION_ERROR"
    
    def test_handle_search_operations_exception(self):
        """Test handling exception in search operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_search_operations(
                "search", "550e8400-e29b-41d4-a716-446655440000", "test query", 10
            )
            
            assert result["success"] is False
            assert "could not be completed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_recommendation_operations_success(self):
        """Test handling recommendation operations successfully."""
        self.mock_facade.get_next_task.return_value = {
            "success": True,
            "task": {"id": "550e8400-e29b-41d4-a716-446655440001", "title": "Next task"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade, \
             patch.object(self.controller, '_handle_next_task') as mock_handle_next:
            mock_get_facade.return_value = self.mock_facade
            mock_handle_next.return_value = {
                "success": True,
                "task": {"id": "550e8400-e29b-41d4-a716-446655440001", "title": "Next task"}
            }
            
            result = self.controller.handle_recommendation_operations(
                "next", "550e8400-e29b-41d4-a716-446655440000", True
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "550e8400-e29b-41d4-a716-446655440001"
            mock_handle_next.assert_called_once_with(self.mock_facade, "550e8400-e29b-41d4-a716-446655440000", True)
    
    def test_handle_recommendation_operations_exception(self):
        """Test handling exception in recommendation operations."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.handle_recommendation_operations(
                "next", "550e8400-e29b-41d4-a716-446655440000", True
            )
            
            assert result["success"] is False
            assert "could not be completed" in result["error"]
            assert result["error_code"] == "INTERNAL_ERROR"
    
    def test_handle_dependency_operations_success(self):
        """Test handling dependency operations successfully."""
        self.mock_facade.add_dependency.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_dependency_operations(
                "add_dependency", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440003"
            )
            
            assert result["success"] is True
            self.mock_facade.add_dependency.assert_called_once_with("550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440003")
    
    def test_handle_dependency_operations_missing_task_id(self):
        """Test dependency operation with missing task_id."""
        result = self.controller.handle_dependency_operations(
            "add_dependency", "550e8400-e29b-41d4-a716-446655440000", None, "550e8400-e29b-41d4-a716-446655440003"
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: task_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_dependency_operations_missing_dependency_id(self):
        """Test dependency operation with missing dependency_id."""
        result = self.controller.handle_dependency_operations(
            "add_dependency", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001", None
        )
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: dependency_id"
        assert result["error_code"] == "MISSING_FIELD"
    
    def test_handle_dependency_operations_remove_dependency(self):
        """Test handling remove dependency operation."""
        self.mock_facade.remove_dependency.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_dependency_operations(
                "remove_dependency", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440003"
            )
            
            assert result["success"] is True
            self.mock_facade.remove_dependency.assert_called_once_with("550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440003")
    
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
        
        assert result["status"] == "failure"
        assert result["error"]["message"] == "Validation failed for field: test_field"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["operation"] == "test_action"
        assert "validation_details" in result["metadata"]
        assert result["metadata"]["validation_details"]["field"] == "test_field"
    
    def test_create_invalid_action_error(self):
        """Test creating invalid action error response."""
        result = self.controller._create_invalid_action_error("invalid_action")
        
        assert result["status"] == "failure"
        assert result["error"]["message"] == "Validation failed for field: action"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["operation"] == "unknown_action"
        assert "validation_details" in result["metadata"]
        assert result["metadata"]["validation_details"]["field"] == "action"
        assert "One of:" in result["metadata"]["validation_details"]["expected"]
        assert "Invalid action: invalid_action" in result["metadata"]["validation_details"]["hint"]
    
    def test_missing_field_error_response(self):
        """Test missing field error response structure."""
        result = self.controller._create_missing_field_error("task_id", "get")
        
        assert result["status"] == "failure"
        assert result["error"]["message"] == "Validation failed for field: task_id"
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["operation"] == "get"
        assert "validation_details" in result["metadata"]
        assert result["metadata"]["validation_details"]["field"] == "task_id"
    
    def test_get_task_management_descriptions_flattening(self):
        """Test getting flattened task management descriptions."""
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.description_loader') as mock_loader:
            mock_loader.get_all_descriptions.return_value = {
                "tasks": {
                    "manage_task": {
                        "description": "Task management description",
                        "parameters": {"action": "Action parameter"}
                    }
                },
                "other_section": {
                    "different_tool": {
                        "description": "Other tool"
                    }
                }
            }
            
            result = self.controller._get_task_management_descriptions()
            
            # Should only include manage_task from nested structure
            expected = {
                "manage_task": {
                    "description": "Task management description",
                    "parameters": {"action": "Action parameter"}
                }
            }
            assert result == expected


if __name__ == "__main__":
    pytest.main([__file__])