#!/usr/bin/env python3
"""
Demonstration of improved context hierarchy error messages.

This script shows how the system now provides helpful error messages
when trying to create contexts without their parent contexts.
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from unittest.mock import Mock


def demonstrate_improved_error_messages():
    """Show examples of the improved error messages."""
    # Setup
    factory = UnifiedContextFacadeFactory()
    controller = UnifiedContextMCPController(factory)
    
    # Create mocks to register the manage_context tool
    mcp = Mock()
    tools = {}
    def mock_tool(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    mcp.tool = mock_tool
    controller.register_tools(mcp)
    manage_context = tools['manage_context']
    
    print("=" * 80)
    print("CONTEXT HIERARCHY ERROR MESSAGES DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Example 1: Task without branch_id
    print("1. Creating a task without branch_id:")
    print("-" * 40)
    result = manage_context(
        action="create",
        level="task",
        context_id="task-123",
        data={"task_data": {"title": "My Task"}}
    )
    print("Error:", result["error"])
    print("Guidance:")
    print(json.dumps(result, indent=2, default=str))
    print()
    
    # Example 2: Task with non-existent branch
    print("2. Creating a task with non-existent branch:")
    print("-" * 40)
    result = manage_context(
        action="create",
        level="task",
        context_id="task-456",
        data={
            "branch_id": "non-existent-branch",
            "task_data": {"title": "Another Task"}
        }
    )
    print("Error:", result["error"])
    if "required_actions" in result:
        print("Required Actions:")
        for action in result["required_actions"]:
            print(f"  Step {action['step']}: {action['description']}")
            print(f"    Command: {action['command'][:80]}...")
    print()
    
    # Example 3: Project without global context
    print("3. Creating a project without global context:")
    print("-" * 40)
    result = manage_context(
        action="create",
        level="project",
        context_id="project-789",
        data={"project_name": "My Project"}
    )
    if result["success"]:
        print("Note: Global context already exists, project created successfully")
    else:
        print("Error:", result["error"])
        if "step_by_step" in result:
            print("Step by Step Instructions:")
            for step in result["step_by_step"]:
                print(f"  Step {step['step']}: {step['description']}")
    print()
    
    # Example 4: Branch without project_id
    print("4. Creating a branch without project_id:")
    print("-" * 40)
    result = manage_context(
        action="create",
        level="branch",
        context_id="branch-101",
        data={"git_branch_name": "feature/test"}
    )
    print("Error:", result["error"])
    if "required_fields" in result:
        print("Required Fields:", result["required_fields"])
    if "example" in result:
        print("Example:", result["example"][:80] + "...")
    print()
    
    print("=" * 80)
    print("KEY IMPROVEMENTS:")
    print("- Clear, actionable error messages")
    print("- Step-by-step guidance for fixing issues")
    print("- Example commands with correct syntax")
    print("- Tips for finding required information")
    print("- No more cryptic 'FOREIGN KEY constraint failed' errors!")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_improved_error_messages()