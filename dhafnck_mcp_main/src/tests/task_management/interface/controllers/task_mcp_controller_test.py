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
    def test_get_facade_for_request_no_auth_raises_error(self, mock_get_user_id):
        """Test getting facade without authentication raises error."""
        mock_get_user_id.return_value = None
        git_branch_id = "branch-123"
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            self.controller._get_facade_for_request(git_branch_id)
        
        assert "Task facade creation" in str(exc_info.value)
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_create_action(self, mock_get_user_id):
        """Test manage_task with create action."""
        mock_get_user_id.return_value = "test-user-123"
        
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
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_search_action(self, mock_get_user_id):
        """Test manage_task with search action."""
        mock_get_user_id.return_value = "test-user-123"
        
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
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_next_action(self, mock_get_user_id):
        """Test manage_task with next action."""
        mock_get_user_id.return_value = "test-user-123"
        
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
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_manage_task_unknown_action(self, mock_get_user_id):
        """Test manage_task with unknown action."""
        mock_get_user_id.return_value = "test-user-123"
        
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
            
            result = self.controller.handle_crud_operations(
                "create", "branch-123", None, "Test task", "Test description",
                None, "medium", None, None, None, None, None, None, None
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "task-123"
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
            
            result = self.controller.handle_crud_operations(
                "get", "branch-123", "task-456"
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "task-123"
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
            
            result = self.controller.handle_crud_operations(
                "list", "branch-123", None, None, None, "todo", "high", None, None, None, None, 10
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
                "update", "branch-123", "task-456", "New title", "New description",
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
                "complete", "branch-123", "task-456", None, None, None, None, None,
                "Task completed successfully", "All tests passed"
            )
            
            assert result["success"] is True
            self.mock_facade.complete_task.assert_called_once_with(
                "task-456", "Task completed successfully", "All tests passed"
            )
    
    def test_handle_crud_operations_delete_success(self):
        """Test handling delete operation successfully."""
        self.mock_facade.delete_task.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.handle_crud_operations(
                "delete", "branch-123", "task-456"
            )
            
            assert result["success"] is True
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
            
            result = self.controller.handle_search_operations(
                "search", "branch-123", "test query", 10
            )
            
            assert result["success"] is True
            assert len(result["tasks"]) == 1
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
            
            result = self.controller.handle_recommendation_operations(
                "next", "branch-123", True
            )
            
            assert result["success"] is True
            assert result["task"]["id"] == "task-123"
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
            
            result = self.controller.handle_dependency_operations(
                "add_dependency", "branch-123", "task-123", "dep-task-456"
            )
            
            assert result["success"] is True
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
            
            result = self.controller.handle_dependency_operations(
                "remove_dependency", "branch-123", "task-123", "dep-task-456"
            )
            
            assert result["success"] is True
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
    
    def test_create_invalid_action_error(self):
        """Test creating invalid action error response."""
        result = self.controller._create_invalid_action_error("invalid_action")
        
        assert result["success"] is False
        assert result["error"] == "Invalid action: invalid_action"
        assert result["error_code"] == "INVALID_ACTION"
        assert "valid_actions" in result
        assert len(result["valid_actions"]) > 0
    
    def test_missing_field_error_response(self):
        """Test missing field error response structure."""
        result = self.controller._create_missing_field_error("task_id", "get")
        
        assert result["success"] is False
        assert result["error"] == "Missing required field: task_id"
        assert result["error_code"] == "MISSING_FIELD"
        assert result["field"] == "task_id"
        assert result["action"] == "get"
    
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


class TestTaskMCPControllerIntegration:
    """Integration tests for TaskMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=TaskFacadeFactory)
        self.mock_facade = Mock(spec=TaskApplicationFacade)
        self.mock_facade_factory.create_task_facade.return_value = self.mock_facade
        
        self.controller = TaskMCPController(self.mock_facade_factory)
    
    @patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id')
    def test_complete_create_workflow(self, mock_get_user_id):
        """Test complete task creation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            # Mock facade response
            self.mock_facade.create_task.return_value = {
                "success": True,
                "task": {"id": "task-123", "title": "test-task"}
            }
            
            result = self.controller.manage_task(
                action="create",
                git_branch_id="branch-123",
                title="test-task",
                description="Test task description"
            )
            
            # Verify successful creation
            assert result["success"] is True
            assert result["task"]["id"] == "task-123"
            
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
        
        with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            # Mock facade response
            self.mock_facade.get_next_task.return_value = {
                "success": True,
                "task": {"id": "task-456", "title": "recommended-task"}
            }
            
            result = self.controller.manage_task(
                action="next",
                git_branch_id="branch-123",
                include_context=True
            )
            
            # Verify successful recommendation
            assert result["success"] is True
            assert result["task"]["id"] == "task-456"
            
            # Verify facade was called correctly
            self.mock_facade.get_next_task.assert_called_once_with(True)

    # Response Enrichment Tests
    def test_response_enrichment_service_integration(self):
        """Test integration with ResponseEnrichmentService."""
        with patch.object(self.mock_facade, 'create_task') as mock_create:
            with patch('fastmcp.task_management.application.services.response_enrichment_service.ResponseEnrichmentService.enrich_response') as mock_enrich:
                # Setup mock returns
                task_data = {
                    "id": "task-789",
                    "title": "Test Task",
                    "status": "todo"
                }
                mock_create.return_value = {"success": True, "task": task_data}
                mock_enrich.return_value = {
                    "success": True,
                    "task": task_data,
                    "vision_insights": {
                        "workflow_hints": ["Start with implementation"],
                        "next_actions": ["Add unit tests"],
                        "progress_indicator": "Not started"
                    }
                }
                
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                    with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                        mock_get_user_id.return_value = "test-user"
                        mock_validate.return_value = "test-user"
                        
                        result = self.controller.manage_task(
                            action="create",
                            git_branch_id="branch-123",
                            title="Test Task"
                        )
                        
                        assert result["success"] is True
                        assert "vision_insights" in result
                        assert result["vision_insights"]["workflow_hints"] == ["Start with implementation"]

    def test_parameter_enforcement_service(self):
        """Test parameter enforcement for different types."""
        # Test boolean parameter normalization
        with patch.object(self.mock_facade, 'list_tasks') as mock_list:
            mock_list.return_value = {"success": True, "tasks": []}
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    # Test various boolean formats
                    for bool_val in ["true", "True", "TRUE", "yes", "1", "on"]:
                        result = self.controller.manage_task(
                            action="list",
                            git_branch_id="branch-123",
                            include_context=bool_val
                        )
                        assert result["success"] is True

    def test_array_parameter_normalization(self):
        """Test array parameter normalization (assignees, labels, dependencies)."""
        with patch.object(self.mock_facade, 'create_task') as mock_create:
            mock_create.return_value = {
                "success": True,
                "task": {"id": "task-999"}
            }
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    # Test comma-separated string
                    result = self.controller.manage_task(
                        action="create",
                        git_branch_id="branch-123",
                        title="Test Task",
                        assignees="user1,user2,user3",
                        labels="bug,high-priority,frontend"
                    )
                    
                    assert result["success"] is True
                    call_kwargs = mock_create.call_args[1]
                    assert "assignees" in call_kwargs
                    assert "labels" in call_kwargs

    def test_dependencies_parameter_handling(self):
        """Test dependencies parameter in create action."""
        with patch.object(self.mock_facade, 'create_task') as mock_create:
            mock_create.return_value = {
                "success": True,
                "task": {"id": "task-888"}
            }
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    # Test array format
                    deps = ["dep-1", "dep-2"]
                    result = self.controller.manage_task(
                        action="create",
                        git_branch_id="branch-123",
                        title="Test Task",
                        dependencies=deps
                    )
                    
                    assert result["success"] is True
                    call_kwargs = mock_create.call_args[1]
                    assert "dependencies" in call_kwargs

    def test_vision_system_error_handling(self):
        """Test handling when Vision System enrichment fails."""
        with patch.object(self.mock_facade, 'get_task') as mock_get:
            mock_get.return_value = {
                "success": True,
                "task": {"id": "task-777", "title": "Test"}
            }
            
            with patch('fastmcp.task_management.application.services.response_enrichment_service.ResponseEnrichmentService.enrich_response') as mock_enrich:
                # Simulate Vision System failure
                mock_enrich.side_effect = Exception("Vision System unavailable")
                
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                    with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                        mock_get_user_id.return_value = "test-user"
                        mock_validate.return_value = "test-user"
                        
                        result = self.controller.manage_task(
                            action="get",
                            task_id="task-777"
                        )
                        
                        # Should still return task data without enrichment
                        assert result["success"] is True
                        assert result["task"]["id"] == "task-777"

    def test_estimated_effort_parameter(self):
        """Test estimated_effort parameter handling."""
        with patch.object(self.mock_facade, 'update_task') as mock_update:
            mock_update.return_value = {"success": True}
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    result = self.controller.manage_task(
                        action="update",
                        task_id="task-666",
                        estimated_effort="3 days"
                    )
                    
                    assert result["success"] is True
                    call_kwargs = mock_update.call_args[1]
                    assert call_kwargs.get("estimated_effort") == "3 days"

    def test_due_date_parameter_validation(self):
        """Test due_date parameter validation."""
        with patch.object(self.mock_facade, 'create_task') as mock_create:
            mock_create.return_value = {
                "success": True,
                "task": {"id": "task-555"}
            }
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    # Test ISO date format
                    result = self.controller.manage_task(
                        action="create",
                        git_branch_id="branch-123",
                        title="Test Task",
                        due_date="2024-12-31"
                    )
                    
                    assert result["success"] is True
                    call_kwargs = mock_create.call_args[1]
                    assert call_kwargs.get("due_date") == "2024-12-31"

    def test_force_full_generation_parameter(self):
        """Test force_full_generation boolean parameter."""
        with patch.object(self.mock_facade, 'get_next_task') as mock_next:
            mock_next.return_value = {
                "success": True,
                "task": {"id": "task-444"}
            }
            
            with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                    mock_get_user_id.return_value = "test-user"
                    mock_validate.return_value = "test-user"
                    
                    result = self.controller.manage_task(
                        action="next",
                        git_branch_id="branch-123",
                        force_full_generation="yes"
                    )
                    
                    assert result["success"] is True

    def test_context_staleness_detection(self):
        """Test context staleness detection in responses."""
        with patch.object(self.mock_facade, 'get_task') as mock_get:
            # Simulate task with stale context
            mock_get.return_value = {
                "success": True,
                "task": {
                    "id": "task-333",
                    "title": "Test Task",
                    "context_metadata": {
                        "last_updated": "2024-01-01T00:00:00Z",
                        "staleness_days": 30
                    }
                }
            }
            
            with patch('fastmcp.task_management.application.services.response_enrichment_service.ResponseEnrichmentService.enrich_response') as mock_enrich:
                mock_enrich.return_value = {
                    "success": True,
                    "task": mock_get.return_value["task"],
                    "context_state": {
                        "is_stale": True,
                        "staleness_indicator": "⚠️ Context is 30 days old",
                        "recommendation": "Consider updating context with recent changes"
                    }
                }
                
                with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.get_current_user_id') as mock_get_user_id:
                    with patch('fastmcp.task_management.interface.controllers.task_mcp_controller.validate_user_id') as mock_validate:
                        mock_get_user_id.return_value = "test-user"
                        mock_validate.return_value = "test-user"
                        
                        result = self.controller.manage_task(
                            action="get",
                            task_id="task-333",
                            include_context=True
                        )
                        
                        assert result["success"] is True
                        assert result["context_state"]["is_stale"] is True
                        assert "Context is 30 days old" in result["context_state"]["staleness_indicator"]


if __name__ == "__main__":
    pytest.main([__file__])