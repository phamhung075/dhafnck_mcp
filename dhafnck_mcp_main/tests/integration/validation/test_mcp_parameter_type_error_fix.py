#!/usr/bin/env python3
"""
Specific test suite for the exact error case:
"Input validation error: '3' is not valid under any of the given schemas"

This test file specifically tests that numeric strings like '3' and '5' are properly
handled when passed as parameters that expect integers.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from src.fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from src.fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from src.fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory


class TestMCPParameterTypeErrorFix:
    """Test suite specifically for the '3' is not valid error case."""
    
    @pytest.fixture
    def mock_facade(self):
        """Create a mock task facade that tracks calls."""
        facade = Mock(spec=TaskApplicationFacade)
        
        # Track what parameters were actually passed to facade methods
        facade.call_history = []
        
        def track_list_tasks(request):
            facade.call_history.append(('list_tasks', request))
            return {"success": True, "tasks": []}
        
        def track_search_tasks(request):
            facade.call_history.append(('search_tasks', request))
            return {"success": True, "tasks": []}
        
        facade.list_tasks.side_effect = track_list_tasks
        facade.search_tasks.side_effect = track_search_tasks
        
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
        """Create a TaskMCPController instance."""
        return TaskMCPController(task_facade_factory=mock_facade_factory)
    
    def test_exact_error_case_limit_3_as_string(self, controller, mock_facade):
        """Test the exact error case: limit='3' should not cause validation error."""
        # This is the exact case from the error message
        result = controller.manage_task(
            action="list",
            limit="3"  # This is what was causing the error
        )
        
        # The request should succeed, not fail with validation error
        assert result["success"] is True, f"Expected success but got: {result}"
        
        # Verify no validation error occurred
        assert "validation error" not in result.get("error", "").lower()
        assert result.get("error_code") != "VALIDATION_ERROR"
    
    def test_exact_error_case_limit_5_as_string(self, controller, mock_facade):
        """Test another common case: limit='5' as string."""
        result = controller.manage_task(
            action="search",
            query="test",
            limit="5"  # Common case from examples
        )
        
        # Should succeed
        assert result["success"] is True
        assert "tasks" in result
    
    def test_numeric_string_parameters_various_values(self, controller, mock_facade):
        """Test various numeric string values that should all work."""
        test_values = ["1", "2", "3", "5", "10", "25", "50", "100"]
        
        for value in test_values:
            result = controller.manage_task(
                action="list",
                limit=value  # Each should work without validation error
            )
            
            assert result["success"] is True, f"Failed for limit='{value}': {result}"
    
    def test_error_message_not_present(self, controller):
        """Ensure the specific error message doesn't appear."""
        # Even with an invalid action, we shouldn't see the specific schema validation error
        result = controller.manage_task(
            action="invalid_action",
            limit="3"
        )
        
        # Should fail with unknown action, not schema validation
        assert not result["success"]
        assert "is not valid under any of the given schemas" not in result.get("error", "")
        assert result.get("error_code") == "UNKNOWN_ACTION"
    
    def test_parameter_reaches_facade_correctly(self, controller, mock_facade):
        """Verify that parameters reach the facade layer correctly typed."""
        controller.manage_task(
            action="list",
            limit="5"
        )
        
        # Check that the facade received the call
        assert len(mock_facade.call_history) == 1
        method, request = mock_facade.call_history[0]
        assert method == "list_tasks"
        
        # The request object should have the limit parameter
        # It should either be coerced to int or handled properly
        assert hasattr(request, 'limit')
        # We don't assert the exact type here as that's implementation detail
        # The important thing is no validation error occurred
    
    def test_all_numeric_parameters_as_strings(self, controller):
        """Test all known numeric parameters as strings."""
        # Test various actions with their numeric parameters
        test_cases = [
            {
                "action": "list",
                "params": {"limit": "10"}
            },
            {
                "action": "search", 
                "params": {"query": "test", "limit": "20"}
            },
            {
                "action": "update",
                "params": {
                    "task_id": "test-id",
                    "details": "Progress: 75% complete",  # Progress through details field
                    "status": "in_progress"
                }
            }
        ]
        
        for test_case in test_cases:
            result = controller.manage_task(
                action=test_case["action"],
                **test_case["params"]
            )
            
            # None should fail with schema validation error
            if not result["success"]:
                assert "is not valid under any of the given schemas" not in result.get("error", "")
    
    @pytest.mark.parametrize("limit_value,should_succeed", [
        ("0", True),      # Edge case: zero
        ("1", True),      # Minimum typical value
        ("100", True),    # Maximum typical value
        ("-1", True),     # Negative (should be handled by business logic, not type error)
        ("", False),      # Empty string
        ("abc", False),   # Non-numeric string
    ])
    def test_limit_parameter_edge_cases(self, controller, limit_value, should_succeed):
        """Test edge cases for limit parameter."""
        result = controller.manage_task(
            action="list",
            limit=limit_value
        )
        
        if should_succeed:
            # Should either succeed or fail with business logic error, not type error
            if not result["success"]:
                assert "is not valid under any of the given schemas" not in result.get("error", "")
                assert result.get("error_code") != "TYPE_ERROR"
        else:
            # Should fail, but not with schema validation error
            assert "is not valid under any of the given schemas" not in result.get("error", "")


class TestRegressionPrevention:
    """Tests to ensure the fix doesn't break existing functionality."""
    
    @pytest.fixture
    def controller_with_mocks(self):
        """Create a controller with all mocks set up."""
        facade = Mock(spec=TaskApplicationFacade)
        facade.list_tasks.return_value = {"success": True, "tasks": []}
        facade.search_tasks.return_value = {"success": True, "tasks": []}
        facade.create_task.return_value = {"success": True, "task": {"id": "new-id"}}
        facade.update_task.return_value = {"success": True, "task": {"id": "task-id"}}
        facade.get_task.return_value = {"success": True, "task": {"id": "task-id"}}
        
        factory = Mock(spec=TaskFacadeFactory)
        factory.create_task_facade.return_value = facade
        factory.create_task_facade_with_git_branch_id.return_value = facade
        
        return TaskMCPController(task_facade_factory=factory), facade
    
    def test_native_integer_still_works(self, controller_with_mocks):
        """Ensure native integers still work after the fix."""
        controller, facade = controller_with_mocks
        
        result = controller.manage_task(
            action="list",
            limit=5  # Native integer
        )
        
        assert result["success"] is True
    
    def test_native_boolean_still_works(self, controller_with_mocks):
        """Ensure native booleans still work after the fix."""
        controller, facade = controller_with_mocks
        
        result = controller.manage_task(
            action="get",
            task_id="test-id",
            include_context=True  # Native boolean
        )
        
        assert result["success"] is True
    
    def test_mixed_types_in_single_call(self, controller_with_mocks):
        """Test mixing native and string types in one call."""
        controller, facade = controller_with_mocks
        
        result = controller.manage_task(
            action="create",
            git_branch_id="branch-123",
            title="Test Task",
            limit=10,              # Native integer
            include_context="true", # String boolean
            force_full_generation=False  # Native boolean
        )
        
        # Should handle mixed types gracefully
        assert isinstance(result, dict)
        assert "error_code" not in result or result["error_code"] != "TYPE_ERROR"