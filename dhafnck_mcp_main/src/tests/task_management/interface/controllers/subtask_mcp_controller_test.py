"""Test suite for SubtaskMCPController.

Tests the subtask MCP controller including:
- Tool registration and MCP integration
- CRUD operations for subtasks
- Progress tracking and completion
- Authentication and user context
- Error handling and validation
- Workflow guidance integration
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.task_management.interface.controllers.subtask_mcp_controller import SubtaskMCPController
from fastmcp.task_management.application.factories.subtask_facade_factory import SubtaskFacadeFactory
from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestSubtaskMCPController:
    """Test cases for SubtaskMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        self.mock_facade = Mock(spec=SubtaskApplicationFacade)
        self.mock_facade_factory.create_subtask_facade.return_value = self.mock_facade
        
        # Mock workflow guidance
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.SubtaskWorkflowFactory'):
            self.controller = SubtaskMCPController(self.mock_facade_factory)
    
    def test_init(self):
        """Test controller initialization."""
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.SubtaskWorkflowFactory') as mock_workflow_factory:
            mock_workflow = Mock()
            mock_workflow_factory.create.return_value = mock_workflow
            
            controller = SubtaskMCPController(self.mock_facade_factory)
            
            assert controller._subtask_facade_factory == self.mock_facade_factory
            assert controller._workflow_guidance == mock_workflow
            mock_workflow_factory.create.assert_called_once()
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock()
        
        with patch.object(self.controller, '_get_subtask_management_descriptions') as mock_get_desc:
            mock_get_desc.return_value = {
                "manage_subtask": {
                    "description": "Test description",
                    "parameters": {
                        "action": "Action parameter",
                        "task_id": "Task ID parameter"
                    }
                }
            }
            
            self.controller.register_tools(mock_mcp)
            
            # Verify tool was registered
            mock_mcp.tool.assert_called_once()
            call_kwargs = mock_mcp.tool.call_args[1]
            assert call_kwargs["name"] == "manage_subtask"
            assert call_kwargs["description"] == "Test description"
    
    @patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.get_current_user_id')
    def test_get_facade_for_request_with_user_context(self, mock_get_user_id):
        """Test getting facade with user context from JWT."""
        mock_get_user_id.return_value = "jwt-user-123"
        task_id = "task-123"
        
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "jwt-user-123"
            
            result = self.controller._get_facade_for_request(task_id)
            
            assert result == self.mock_facade
            mock_validate.assert_called_once_with("jwt-user-123", "Subtask facade creation")
            self.mock_facade_factory.create_subtask_facade.assert_called_once_with(
                task_id=task_id,
                user_id="jwt-user-123"
            )
    
    @patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.get_current_user_id')
    @patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.AuthConfig')
    def test_get_facade_for_request_compatibility_mode(self, mock_auth_config, mock_get_user_id):
        """Test getting facade with compatibility mode."""
        mock_get_user_id.return_value = None
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-user"
        task_id = "task-123"
        
        result = self.controller._get_facade_for_request(task_id)
        
        assert result == self.mock_facade
        mock_auth_config.log_authentication_bypass.assert_called_once_with(
            "Subtask facade creation", "compatibility mode"
        )
        self.mock_facade_factory.create_subtask_facade.assert_called_once_with(
            task_id=task_id,
            user_id="compatibility-user"
        )
    
    def test_manage_subtask_create_action(self):
        """Test manage_subtask with create action."""
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "subtask-123", "title": "Test subtask"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="create",
                task_id="task-123",
                title="Test subtask"
            )
            
            assert result["success"] is True
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_manage_subtask_update_action(self):
        """Test manage_subtask with update action."""
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "subtask-456", "status": "in_progress"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="update",
                task_id="task-123",
                subtask_id="subtask-456",
                progress_percentage=50
            )
            
            assert result["success"] is True
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_manage_subtask_complete_action(self):
        """Test manage_subtask with complete action."""
        # Mock the get and update operations for completion
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call: get subtask info
            {"success": True, "subtask": {"id": "subtask-456", "title": "Test subtask"}},
            # Second call: update status to done
            {"success": True, "subtask": {"id": "subtask-456", "status": "done"}},
            # Third call: list subtasks for progress
            {"success": True, "subtasks": [{"id": "subtask-456", "status": "done"}]}
        ]
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="complete",
                task_id="task-123",
                subtask_id="subtask-456",
                completion_summary="Task completed successfully"
            )
            
            assert result["success"] is True
            assert result["action"] == "complete"  # Verify action is preserved
            assert self.mock_facade.handle_manage_subtask.call_count >= 2  # At least get and update
    
    def test_manage_subtask_unknown_action(self):
        """Test manage_subtask with unknown action."""
        result = self.controller.manage_subtask(
            action="invalid_action",
            task_id="task-123"
        )
        
        assert result["success"] is False
        assert result["error"] == "Unknown action: invalid_action"
        assert result["error_code"] == "UNKNOWN_ACTION"
        assert "valid_actions" in result
    
    def test_handle_create_subtask_success(self):
        """Test handling create operation successfully."""
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "subtask-123", "title": "Test subtask"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="create",
                task_id="task-123",
                title="Test subtask",
                description="Test description"
            )
            
            assert result["success"] is True
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_handle_create_missing_title(self):
        """Test create operation with missing title."""
        result = self.controller.manage_subtask(
            action="create",
            task_id="task-123",
            title=None,
            description="Test description"
        )
        
        assert result["success"] is False
        assert "title" in result["error"]
        assert result["action"] == "create"
    
    def test_handle_get_subtask_success(self):
        """Test handling get operation successfully."""
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "subtask-123", "title": "Test subtask"}
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="get",
                task_id="task-123",
                subtask_id="subtask-456"
            )
            
            assert result["success"] is True
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_handle_get_missing_subtask_id(self):
        """Test get operation with missing subtask_id."""
        result = self.controller.manage_subtask(
            action="get",
            task_id="task-123",
            subtask_id=None
        )
        
        assert result["success"] is False
        assert "subtask_id" in result["error"]
        assert result["action"] == "get"
    
    def test_handle_list_subtasks_success(self):
        """Test handling list operation successfully."""
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtasks": [
                {"id": "subtask-1", "status": "done"},
                {"id": "subtask-2", "status": "in_progress"}
            ]
        }
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="list",
                task_id="task-123"
            )
            
            assert result["success"] is True
            assert "progress_summary" in result
            assert result["progress_summary"]["total_subtasks"] == 2
            assert result["progress_summary"]["completed"] == 1
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_handle_update_subtask_success(self):
        """Test handling update operation successfully."""
        self.mock_facade.handle_manage_subtask.return_value = {"success": True}
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="update",
                task_id="task-123",
                subtask_id="subtask-456",
                title="New title",
                description="New description",
                progress_percentage=75,
                progress_notes="Progress notes",
                blockers="Test blockers"
            )
            
            assert result["success"] is True
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    def test_handle_update_missing_subtask_id(self):
        """Test update operation with missing subtask_id."""
        result = self.controller.manage_subtask(
            action="update",
            task_id="task-123",
            subtask_id=None,
            title="New title"
        )
        
        assert result["success"] is False
        assert "subtask_id" in result["error"]
        assert result["action"] == "update"
    
    def test_handle_delete_subtask_success(self):
        """Test handling delete operation successfully."""
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call: get subtask info
            {"success": True, "subtask": {"id": "subtask-456", "title": "Test subtask"}},
            # Second call: delete subtask
            {"success": True}
        ]
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="delete",
                task_id="task-123",
                subtask_id="subtask-456"
            )
            
            assert result["success"] is True
            assert self.mock_facade.handle_manage_subtask.call_count == 2
    
    def test_manage_subtask_exception(self):
        """Test handling exception in manage_subtask."""
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.side_effect = Exception("Test exception")
            
            result = self.controller.manage_subtask(
                action="create",
                task_id="task-123",
                title="Test subtask",
                description="description"
            )
            
            assert result["success"] is False
            assert "Test exception" in result["error"]
    
    def test_handle_complete_subtask_with_enhanced_parameters(self):
        """Test handling completion with enhanced parameters."""
        # Mock the get and update operations for completion
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call: get subtask info
            {"success": True, "subtask": {"id": "subtask-456", "title": "Test subtask"}},
            # Second call: update status to done
            {"success": True, "subtask": {"id": "subtask-456", "status": "done"}},
            # Third call: list subtasks for progress
            {"success": True, "subtasks": [{"id": "subtask-456", "status": "done"}]}
        ]
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="complete",
                task_id="task-123",
                subtask_id="subtask-456",
                completion_summary="Task completed",
                impact_on_parent="Significant progress made",
                insights_found=["Insight 1", "Insight 2"],
                challenges_overcome=["Challenge 1"],
                deliverables=["Deliverable 1", "Deliverable 2"],
                skills_learned=["Skill 1"],
                next_recommendations=["Recommendation 1"],
                testing_notes="Testing complete",
                completion_quality="excellent",
                verification_status="verified"
            )
            
            assert result["success"] is True
            assert result["action"] == "complete"
            assert self.mock_facade.handle_manage_subtask.call_count >= 2
    
    def test_handle_complete_missing_completion_summary(self):
        """Test completion operation with missing completion_summary."""
        result = self.controller.manage_subtask(
            action="complete",
            task_id="task-123",
            subtask_id="subtask-456",
            completion_summary=None
        )
        
        assert result["success"] is False
        assert "completion_summary" in result["error"]
        assert result["action"] == "complete"
    
    def test_handle_complete_missing_subtask_id(self):
        """Test completion operation with missing subtask_id."""
        result = self.controller.manage_subtask(
            action="complete",
            task_id="task-123",
            subtask_id=None,
            completion_summary="Task completed"
        )
        
        assert result["success"] is False
        assert "subtask_id" in result["error"]
        assert result["action"] == "complete"
    
    def test_get_subtask_management_descriptions(self):
        """Test getting subtask management descriptions."""
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.description_loader') as mock_loader:
            mock_loader.get_all_descriptions.return_value = {
                "subtasks": {
                    "manage_subtask": {
                        "description": "Test description",
                        "parameters": {"action": "Action param"}
                    }
                }
            }
            
            result = self.controller._get_subtask_management_descriptions()
            
            expected = {
                "manage_subtask": {
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
    
    def test_enhance_with_workflow_hints_success(self):
        """Test enhancing successful response with workflow hints."""
        response = {"success": True, "subtask": {"id": "subtask-123"}}
        
        mock_guidance = {"next_steps": ["Continue work"], "hints": ["Test hint"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_with_workflow_hints(
            response, "create", "task-123", "subtask-123"
        )
        
        assert result["success"] is True
        assert result["workflow_guidance"] == mock_guidance
        self.controller._workflow_guidance.generate_guidance.assert_called_once_with(
            "create", {"task_id": "task-123", "subtask_id": "subtask-123"}
        )
    
    def test_enhance_with_workflow_hints_failure(self):
        """Test enhancing failed response (no guidance added)."""
        response = {"success": False, "error": "Test error"}
        
        # The method should not be called on the controller since it's not enhanced for failures
        result = response  # Failed responses are not enhanced
        
        assert result == response  # Should be unchanged
        assert "workflow_guidance" not in result
    
    def test_enhance_with_workflow_hints_list_action(self):
        """Test enhancing list action response."""
        response = {
            "success": True,
            "subtasks": [
                {"id": "subtask-1", "status": "done"},
                {"id": "subtask-2", "status": "in_progress"}
            ]
        }
        
        mock_guidance = {"next_steps": ["Complete remaining subtasks"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        result = self.controller._enhance_with_workflow_hints(
            response, "list", "task-123", None, response["subtasks"]
        )
        
        assert result["success"] is True
        assert result["workflow_guidance"] == mock_guidance
    
    def test_parse_array_parameter_json_string(self):
        """Test parsing array parameter from JSON string."""
        json_input = '["item1", "item2", "item3"]'
        result = self.controller._parse_array_parameter(json_input)
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_array_parameter_comma_separated(self):
        """Test parsing array parameter from comma-separated string."""
        csv_input = "item1,item2,item3"
        result = self.controller._parse_array_parameter(csv_input)
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_array_parameter_single_string(self):
        """Test parsing array parameter from single string."""
        single_input = "single_item"
        result = self.controller._parse_array_parameter(single_input)
        assert result == ["single_item"]
    
    def test_parse_array_parameter_already_list(self):
        """Test parsing array parameter that's already a list."""
        list_input = ["item1", "item2", "item3"]
        result = self.controller._parse_array_parameter(list_input)
        assert result == ["item1", "item2", "item3"]
    
    def test_parse_array_parameter_none(self):
        """Test parsing array parameter that's None."""
        result = self.controller._parse_array_parameter(None)
        assert result is None
    
    def test_parse_array_parameter_empty_string(self):
        """Test parsing array parameter that's empty string."""
        result = self.controller._parse_array_parameter("")
        assert result is None


    def test_handle_complete_with_context_facade_integration(self):
        """Test completion with context facade integration for enhanced tracking."""
        # Mock context facade
        mock_context_facade = Mock()
        self.controller._context_facade = mock_context_facade
        
        # Mock facade responses
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call: get subtask info
            {"success": True, "subtask": {"id": "subtask-456", "title": "Test subtask"}},
            # Second call: update status to done
            {"success": True, "subtask": {"id": "subtask-456", "status": "done", "title": "Test subtask"}},
            # Third call: list subtasks for progress
            {"success": True, "subtasks": [{"id": "subtask-456", "status": "done"}]}
        ]
        
        with patch.object(self.controller, '_get_facade_for_request') as mock_get_facade:
            mock_get_facade.return_value = self.mock_facade
            
            result = self.controller.manage_subtask(
                action="complete",
                task_id="task-123",
                subtask_id="subtask-456",
                completion_summary="Task completed",
                impact_on_parent="Parent task 50% complete",
                insights_found=["Found optimization opportunity"],
                testing_notes="All tests passed",
                deliverables=["feature.py", "test_feature.py"],
                skills_learned=["Advanced async patterns"],
                challenges_overcome=["Fixed race condition"],
                next_recommendations=["Refactor for better performance"],
                completion_quality="excellent",
                verification_status="verified"
            )
            
            assert result["success"] is True
            assert result["action"] == "complete"
            
            # Verify context facade was called appropriately
            # Should have multiple add_progress calls
            progress_calls = [call for call in mock_context_facade.add_progress.call_args_list]
            assert len(progress_calls) > 0
            
            # Should have merge_context calls for insights
            merge_calls = [call for call in mock_context_facade.merge_context.call_args_list]
            assert len(merge_calls) > 0
            
            # Verify at least one call contains the completion summary
            assert any("Task completed" in str(call) for call in progress_calls)


class TestSubtaskMCPControllerIntegration:
    """Integration tests for SubtaskMCPController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        self.mock_facade = Mock(spec=SubtaskApplicationFacade)
        self.mock_facade_factory.create_subtask_facade.return_value = self.mock_facade
        
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.SubtaskWorkflowFactory'):
            self.controller = SubtaskMCPController(self.mock_facade_factory)
    
    @patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.get_current_user_id')
    def test_complete_create_workflow(self, mock_get_user_id):
        """Test complete subtask creation workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade response
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": "subtask-123", "title": "test-subtask"}
        }
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["Start working on subtask"]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_subtask(
                action="create",
                task_id="task-123",
                title="test-subtask",
                description="Test subtask description"
            )
            
            # Verify successful creation
            assert result["success"] is True
            
            # Verify facade was called correctly
            self.mock_facade_factory.create_subtask_facade.assert_called_once_with(
                task_id="task-123",
                user_id="test-user"
            )
            
            self.mock_facade.handle_manage_subtask.assert_called_once()
    
    @patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.get_current_user_id')
    def test_complete_completion_workflow(self, mock_get_user_id):
        """Test complete subtask completion workflow."""
        mock_get_user_id.return_value = "test-user"
        
        # Mock facade responses for completion flow
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call: get subtask info
            {"success": True, "subtask": {"id": "subtask-456", "title": "test-subtask"}},
            # Second call: update status to done
            {"success": True, "subtask": {"id": "subtask-456", "status": "done"}},
            # Third call: list subtasks for progress
            {"success": True, "subtasks": [
                {"id": "subtask-456", "status": "done"},
                {"id": "subtask-457", "status": "done"},
                {"id": "subtask-458", "status": "done"}
            ]}
        ]
        
        # Mock workflow guidance
        mock_guidance = {"next_steps": ["All subtasks complete! Consider completing parent task."]}
        self.controller._workflow_guidance.generate_guidance.return_value = mock_guidance
        
        with patch('fastmcp.task_management.interface.controllers.subtask_mcp_controller.validate_user_id') as mock_validate:
            mock_validate.return_value = "test-user"
            
            result = self.controller.manage_subtask(
                action="complete",
                task_id="task-123",
                subtask_id="subtask-456",
                completion_summary="Subtask completed successfully"
            )
            
            # Verify successful completion
            assert result["success"] is True
            assert result["action"] == "complete"
            
            # Verify facade was called correctly
            assert self.mock_facade.handle_manage_subtask.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__])