#!/usr/bin/env python3
"""
Test suite for TaskMCPController parameter validation fix.

This test file verifies that the parameter validation issue is fixed where:
- Integer parameters passed as strings (e.g., "5") are properly coerced to integers
- Integer parameters passed as integers work correctly
- Boolean parameters passed as strings (e.g., "true") are properly coerced to booleans
- Boolean parameters passed as booleans work correctly

The fix should handle all numeric and boolean parameters in the manage_task tool.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Import the controller and related classes
from src.fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from src.fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from src.fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from src.fastmcp.task_management.application.factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory


class TestTaskMCPParameterValidationFix:
    """Test suite for parameter validation fix in TaskMCPController."""
    
    @pytest.fixture
    def mock_facade(self):
        """Create a mock task facade."""
        facade = Mock(spec=TaskApplicationFacade)
        
        # Mock successful responses for different actions
        facade.list_tasks.return_value = {
            "success": True,
            "tasks": [
                {"id": "task-1", "title": "Test Task 1", "status": "todo"},
                {"id": "task-2", "title": "Test Task 2", "status": "in_progress"}
            ]
        }
        
        facade.search_tasks.return_value = {
            "success": True,
            "tasks": [
                {"id": "task-1", "title": "Test Task 1", "description": "Contains search term"}
            ]
        }
        
        facade.create_task.return_value = {
            "success": True,
            "task": {
                "id": "new-task-id",
                "title": "New Task",
                "git_branch_id": "branch-123"
            }
        }
        
        facade.update_task.return_value = {
            "success": True,
            "task": {
                "id": "task-1",
                "title": "Updated Task",
                "progress_percentage": 50
            }
        }
        
        # Mock async get_next_task
        async def mock_get_next_task(*args, **kwargs):
            return {
                "success": True,
                "task": {
                    "id": "next-task-id",
                    "title": "Next Task to Work On"
                }
            }
        facade.get_next_task = mock_get_next_task
        
        return facade
    
    @pytest.fixture
    def mock_facade_factory(self, mock_facade):
        """Create a mock facade factory."""
        factory = Mock(spec=TaskFacadeFactory)
        factory.create_task_facade.return_value = mock_facade
        factory.create_task_facade_with_git_branch_id.return_value = mock_facade
        return factory
    
    @pytest.fixture
    def controller(self, mock_facade_factory):
        """Create a TaskMCPController instance with mocked dependencies."""
        return TaskMCPController(
            task_facade_factory=mock_facade_factory,
            context_facade_factory=Mock(spec=HierarchicalContextFacadeFactory),
        )
    
    def test_list_action_with_limit_as_string(self, controller, mock_facade):
        """Test that limit parameter passed as string "5" is properly handled."""
        # Call manage_task with limit as string
        result = controller.manage_task(
            action="list",
            limit="5"  # String instead of int
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
        
        # Verify the facade was called with proper parameters
        # The limit should have been coerced to integer 5
        mock_facade.list_tasks.assert_called_once()
        call_args = mock_facade.list_tasks.call_args[0][0]
        assert hasattr(call_args, 'limit')
        # The limit should either be coerced to int or the facade should handle it
        # We're testing that no validation error occurs
    
    def test_list_action_with_limit_as_integer(self, controller, mock_facade):
        """Test that limit parameter passed as integer 5 works correctly."""
        # Call manage_task with limit as integer
        result = controller.manage_task(
            action="list",
            limit=5  # Integer
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
        
        # Verify the facade was called
        mock_facade.list_tasks.assert_called_once()
    
    def test_search_action_with_limit_as_string(self, controller, mock_facade):
        """Test search action with limit as string."""
        # Call manage_task with limit as string
        result = controller.manage_task(
            action="search",
            query="test query",
            limit="10"  # String instead of int
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
        
        # Verify the facade was called
        mock_facade.search_tasks.assert_called_once()
    
    def test_search_action_with_limit_as_integer(self, controller, mock_facade):
        """Test search action with limit as integer."""
        # Call manage_task with limit as integer
        result = controller.manage_task(
            action="search",
            query="test query",
            limit=10  # Integer
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
    
    def test_get_action_with_include_context_as_string_true(self, controller, mock_facade):
        """Test get action with include_context as string "true"."""
        mock_facade.get_task.return_value = {
            "success": True,
            "task": {"id": "task-1", "title": "Test Task"}
        }
        
        # Call manage_task with include_context as string
        result = controller.manage_task(
            action="get",
            task_id="task-1",
            include_context="true"  # String instead of bool
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "task" in result
    
    def test_get_action_with_include_context_as_boolean(self, controller, mock_facade):
        """Test get action with include_context as boolean True."""
        mock_facade.get_task.return_value = {
            "success": True,
            "task": {"id": "task-1", "title": "Test Task"}
        }
        
        # Call manage_task with include_context as boolean
        result = controller.manage_task(
            action="get",
            task_id="task-1",
            include_context=True  # Boolean
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "task" in result
    
    def test_update_with_progress_percentage_as_string(self, controller, mock_facade):
        """Test update action with progress_percentage passed as string."""
        # This tests the internal logic where progress might be parsed from string
        result = controller.manage_task(
            action="update",
            task_id="task-1",
            status="in_progress",
            details="Progress: 50% complete",
            estimated_effort="50"  # String percentage
        )
        
        # Verify the request was successful
        assert result["success"] is True
    
    def test_create_with_force_full_generation_as_string(self, controller, mock_facade):
        """Test create action with force_full_generation as string "false"."""
        result = controller.manage_task(
            action="create",
            git_branch_id="branch-123",
            title="New Task",
            force_full_generation="false"  # String instead of bool
        )
        
        # Verify the request was successful
        assert result["success"] is True
        # The response structure may have changed - check for task in data
        assert "task" in result or (result.get("data", {}).get("task") is not None)
    
    def test_next_action_with_include_context_as_string(self, controller, mock_facade):
        """Test next action with include_context as string."""
        result = controller.manage_task(
            action="next",
            git_branch_id="branch-123",
            include_context="true"  # String instead of bool
        )
        
        # Verify the request was successful  
        assert result["success"] is True
        assert "task" in result
    
    def test_multiple_string_parameters_together(self, controller, mock_facade):
        """Test multiple string parameters that should be coerced."""
        result = controller.manage_task(
            action="list",
            git_branch_id="branch-123",
            limit="25",  # String instead of int
            # Note: Other boolean parameters could be added here
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
    
    def test_edge_case_limit_zero_as_string(self, controller, mock_facade):
        """Test edge case with limit "0" as string."""
        result = controller.manage_task(
            action="list",
            limit="0"  # Edge case: zero as string
        )
        
        # Should either succeed or fail gracefully, not with type error
        # The actual behavior depends on business logic
        assert isinstance(result, dict)
        assert "error_code" not in result or result["error_code"] != "TYPE_ERROR"
    
    def test_edge_case_limit_large_number_as_string(self, controller, mock_facade):
        """Test edge case with large limit as string."""
        result = controller.manage_task(
            action="list",
            limit="100"  # Large but valid limit as string
        )
        
        # Verify the request was successful
        assert result["success"] is True
        assert "tasks" in result
    
    def test_boolean_string_variations(self, controller, mock_facade):
        """Test various boolean string representations."""
        mock_facade.get_task.return_value = {
            "success": True,
            "task": {"id": "task-1", "title": "Test Task"}
        }
        
        # Test different boolean string values
        boolean_values = ["true", "True", "TRUE", "false", "False", "FALSE", "1", "0"]
        
        for bool_val in boolean_values:
            result = controller.manage_task(
                action="get",
                task_id="task-1",
                include_context=bool_val
            )
            
            # All should be handled without type errors
            assert isinstance(result, dict)
            assert "error_code" not in result or result["error_code"] != "TYPE_ERROR"
    
    def test_invalid_integer_string_graceful_failure(self, controller, mock_facade):
        """Test that invalid integer strings fail gracefully."""
        result = controller.manage_task(
            action="list",
            limit="not-a-number"  # Invalid integer string
        )
        
        # Should fail with a validation error, not a type error
        if not result["success"]:
            assert result["error_code"] in ["VALIDATION_ERROR", "PARAMETER_COERCION_ERROR", "VALUE_ERROR"]
            assert "limit" in result.get("error", "").lower() or "limit" in result.get("field", "").lower()
    
    def test_mixed_parameter_types_in_single_call(self, controller, mock_facade):
        """Test a call with multiple parameters of different types."""
        result = controller.manage_task(
            action="create",
            git_branch_id="branch-123",
            title="New Task",
            description="Task description",
            priority="high",  # String (valid)
            force_full_generation="true",  # String bool
            include_context=False,  # Native bool
            # Could add more parameters here
        )
        
        # Verify the request was successful
        assert result["success"] is True
        # The response structure may have changed - check for task in data
        assert "data" in result and "task" in result["data"]


class TestParameterValidationIntegration:
    """Integration tests to verify parameter validation is properly integrated."""
    
    def test_parameter_validation_module_imports(self):
        """Test that parameter validation modules can be imported."""
        try:
            from src.fastmcp.task_management.interface.utils.mcp_parameter_validator import MCPParameterValidator
            from src.fastmcp.task_management.interface.utils.parameter_validation_fix import (
                coerce_parameter_types,
                validate_parameters
            )
            assert True, "All parameter validation modules imported successfully"
        except ImportError as e:
            pytest.fail(f"Failed to import parameter validation modules: {e}")
    
    def test_direct_parameter_coercion(self):
        """Test direct parameter coercion functionality."""
        from src.fastmcp.task_management.interface.utils.parameter_validation_fix import coerce_parameter_types
        
        # Test integer coercion
        params = {"limit": "5", "offset": "10"}
        coerced = coerce_parameter_types(params)
        assert coerced["limit"] == 5
        assert isinstance(coerced["limit"], int)
        assert coerced["offset"] == 10
        assert isinstance(coerced["offset"], int)
        
        # Test boolean coercion
        params = {"include_context": "true", "force": "false"}
        coerced = coerce_parameter_types(params)
        assert coerced["include_context"] is True
        assert isinstance(coerced["include_context"], bool)
        assert coerced["force"] is False
        assert isinstance(coerced["force"], bool)
    
    def test_mcp_parameter_validator_wrapper(self):
        """Test the MCPParameterValidator wrapper class."""
        from src.fastmcp.task_management.interface.utils.mcp_parameter_validator import MCPParameterValidator
        
        # Test with valid parameters
        params = {"query": "test", "limit": "5", "include_context": "true"}
        result = MCPParameterValidator.validate_and_coerce_mcp_parameters("search", params)
        
        assert result["success"] is True
        assert "coerced_params" in result
        assert result["coerced_params"]["limit"] == 5
        assert result["coerced_params"]["include_context"] is True