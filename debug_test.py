#!/usr/bin/env python3
"""Debug test to understand the controller flow."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dhafnck_mcp_main', 'src'))

from unittest.mock import Mock, patch
from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade

def test_debug():
    # Create mock task facade factory
    mock_task_facade_factory = Mock()
    mock_facade = Mock(spec=TaskApplicationFacade)
    mock_task_facade_factory.create_task_facade.return_value = mock_facade
    mock_task_facade_factory.create_task_facade_with_git_branch_id.return_value = mock_facade
    
    # Create controller
    controller = TaskMCPController(
        task_facade_factory=mock_task_facade_factory,
        context_facade_factory=None,
        project_manager=None,
        repository_factory=None
    )
    
    # Mock _get_facade_for_request
    with patch.object(controller, '_get_facade_for_request') as mock_get_facade:
        mock_get_facade.return_value = mock_facade
        mock_facade.create_task.return_value = {
            "success": True, 
            "task": {"id": "task-123", "title": "Test Task"}
        }
        
        # Call manage_task with user_id
        try:
            result = controller.manage_task(
                action="create",
                git_branch_id="branch-123",
                title="Test Task",
                user_id="test-user-001"
            )
            print(f"Result: {result}")
            print(f"Mock was called {mock_get_facade.call_count} times")
            if mock_get_facade.called:
                print(f"Mock called with args: {mock_get_facade.call_args}")
        except Exception as e:
            print(f"Exception occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_debug()