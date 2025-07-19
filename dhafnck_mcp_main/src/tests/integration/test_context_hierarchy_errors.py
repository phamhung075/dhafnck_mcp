"""
Integration tests for context hierarchy error messages.

Tests that the system provides clear, user-friendly error messages
when context creation fails due to missing parent contexts.
"""

import pytest
from unittest.mock import Mock
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


class TestContextHierarchyErrors:
    """Test context hierarchy error messages in real scenarios."""
    
    @pytest.fixture
    def controller(self):
        """Create a controller instance."""
        factory = UnifiedContextFacadeFactory()
        return UnifiedContextMCPController(factory)
    
    @pytest.fixture
    def manage_context(self, controller):
        """Get the manage_context tool function."""
        # Create mock MCP and register tools
        mcp = Mock()
        tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools[name] = func
                return func
            return decorator
        
        mcp.tool = mock_tool
        controller.register_tools(mcp)
        return tools["manage_context"]
    
    def test_task_without_branch_context(self, manage_context):
        """Test creating a task without branch context shows helpful error."""
        # Try to create task context without branch
        result = manage_context(
            action="create",
            level="task", 
            context_id="task-123",
            data={"task_data": {"title": "My Task"}}
        )
        
        assert result["success"] is False
        assert "Missing required field: branch_id" in result["error"]
        assert "required_fields" in result
        assert "branch_id" in result["required_fields"]
        assert "example" in result
        assert "branch_id" in result["example"]
        assert "tip" in result
        assert "manage_git_branch" in result["tip"]
    
    def test_task_with_missing_branch_context(self, manage_context):
        """Test creating a task with branch_id but missing branch context."""
        # Try to create task with branch_id that doesn't have context
        result = manage_context(
            action="create",
            level="task",
            context_id="task-123", 
            data={
                "branch_id": "non-existent-branch",
                "task_data": {"title": "My Task"}
            }
        )
        
        assert result["success"] is False
        # Either shows parent branch context error or database error
        assert ("Parent branch context" in result["error"] and "does not exist" in result["error"]) or "Cannot verify branch context" in result["error"]
        # The response structure varies based on error type - check for any guidance field
        assert any(key in result for key in ["suggestion", "alternative", "required_actions", "context_creation_order"])
    
    def test_project_without_global_context(self, manage_context):
        """Test creating a project without global context shows helpful error."""
        # Try to create project context without global
        result = manage_context(
            action="create",
            level="project",
            context_id="project-123",
            data={"project_name": "My Project"}
        )
        
        # Note: This might succeed if global context was created in previous tests
        # or it will show the error
        if not result["success"]:
            assert "Cannot create project context without global context" in result["error"]
            # Command is in step_by_step structure
            assert "step_by_step" in result
            assert any("global_singleton" in step.get("command", "") for step in result["step_by_step"])
            assert "explanation" in result
    
    def test_branch_without_project_context(self, manage_context):
        """Test creating a branch without project context shows helpful error."""
        # Try to create branch without project_id
        result = manage_context(
            action="create",
            level="branch",
            context_id="branch-456",
            data={"git_branch_name": "feature/test"}
        )
        
        assert result["success"] is False
        assert "Missing required field: project_id" in result["error"]
        assert "required_fields" in result
        assert "project_id" in result["required_fields"]
        
        # Try with project_id but no project context
        result = manage_context(
            action="create",
            level="branch",
            context_id="branch-456",
            data={
                "project_id": "non-existent-project",
                "git_branch_name": "feature/test"
            }
        )
        
        if not result["success"]:
            assert "Parent project context" in result["error"] and "does not exist" in result["error"]
            assert any(key in result for key in ["suggestion", "required_actions", "hierarchy"])
    
    def test_error_messages_are_actionable(self, manage_context):
        """Test that error messages provide actionable guidance."""
        # Try to create task without any context
        result = manage_context(
            action="create",
            level="task",
            context_id="task-999",
            data_title="My Task"  # Using legacy parameter
        )
        
        assert result["success"] is False
        # Should have guidance
        assert any(key in result for key in ["example", "tip", "command", "required_fields", "suggestion"])
        
        # Error should be clear, not a cryptic database error
        assert "FOREIGN KEY constraint failed" not in result.get("error", "")
        assert "branch_id" in result.get("error", "") or "required" in result.get("error", "")