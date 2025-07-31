"""
Test context data parameter format handling for Issue #3.

This tests the fix for JSON string parsing and various data parameter formats.
"""

import json
import pytest
from unittest.mock import Mock, patch

from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


class TestContextDataFormatFix:
    """Test that context data accepts multiple formats: dict, JSON string, and legacy parameters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = Mock(spec=UnifiedContextFacadeFactory)
        self.facade = Mock()
        self.factory.create_facade.return_value = self.facade
        
        self.controller = UnifiedContextMCPController(self.factory)
        
        # Mock MCP for tool registration
        self.mcp = Mock()
        self.tools = {}
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                self.tools[name] = func
                return func
            return decorator
        
        self.mcp.tool = mock_tool
        self.controller.register_tools(self.mcp)
        self.manage_context = self.tools["manage_context"]
        
        # Set up successful response for facade
        self.facade.create_context.return_value = {
            "success": True,
            "context": {
                "id": "test-context",
                "title": "Test Title",
                "description": "Test Description"
            }
        }
    
    def test_data_as_dictionary_object(self):
        """Test passing data as a dictionary object (the standard way)."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data={"title": "My Task", "description": "Task description"}
        )
        
        assert result["success"] is True
        
        # Verify facade was called with correct data
        self.facade.create_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data={"title": "My Task", "description": "Task description"}
        )
    
    def test_data_as_json_string(self):
        """Test passing data as a JSON string (should be parsed automatically)."""
        json_data = json.dumps({"title": "My Task", "description": "Task description"})
        
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data=json_data
        )
        
        assert result["success"] is True
        
        # Verify facade was called with parsed data
        self.facade.create_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data={"title": "My Task", "description": "Task description"}
        )
    
    def test_data_as_invalid_json_string(self):
        """Test passing invalid JSON string returns helpful error."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data='{"title": "Missing closing brace"'
        )
        
        assert result["success"] is False
        assert "Invalid JSON string" in result["error"]["message"]
        assert "suggestions" in result["metadata"]
        assert "examples" in result["metadata"]
        
        # Check that suggestions include all formats
        suggestions = result["metadata"]["suggestions"]
        assert any("dictionary object" in s for s in suggestions)
        assert any("JSON string" in s for s in suggestions)
        assert any("legacy parameters" in s for s in suggestions)
    
    def test_data_as_non_dict_json(self):
        """Test passing JSON that's not an object (e.g., array or string)."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data='["not", "an", "object"]'
        )
        
        assert result["success"] is False
        assert "JSON data must be an object" in result["error"]["message"]
    
    def test_legacy_parameters_format(self):
        """Test using legacy data_* parameters."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data_title="My Task",
            data_description="Task description",
            data_status="todo",
            data_priority="high"
        )
        
        assert result["success"] is True
        
        # Verify facade was called with reconstructed data
        self.facade.create_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data={
                "title": "My Task",
                "description": "Task description",
                "status": "todo",
                "priority": "high"
            }
        )
    
    def test_mixed_data_and_legacy_parameters(self):
        """Test that data parameter takes precedence over legacy parameters."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data={"title": "From data param"},
            data_title="From legacy param"  # Should be ignored
        )
        
        assert result["success"] is True
        
        # Verify data param took precedence
        self.facade.create_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data={"title": "From data param"}
        )
    
    def test_empty_data_handling(self):
        """Test handling of empty or None data."""
        # Test with None data and no legacy params
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data=None
        )
        
        assert result["success"] is True
        
        # Should be called with empty dict
        self.facade.create_context.assert_called_with(
            level="task",
            context_id="task-123",
            data={}
        )
    
    def test_data_with_special_characters(self):
        """Test JSON string with special characters and escaping."""
        json_data = json.dumps({
            "title": "Task with \"quotes\" and 'apostrophes'",
            "description": "Line 1\nLine 2\tTabbed",
            "path": "C:\\Users\\test\\file.txt"
        })
        
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data=json_data
        )
        
        assert result["success"] is True
        
        # Verify correct parsing of special characters
        expected_data = {
            "title": "Task with \"quotes\" and 'apostrophes'",
            "description": "Line 1\nLine 2\tTabbed",
            "path": "C:\\Users\\test\\file.txt"
        }
        self.facade.create_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data=expected_data
        )
    
    def test_update_action_with_json_string(self):
        """Test update action also handles JSON strings correctly."""
        self.facade.update_context.return_value = {"success": True}
        
        json_data = json.dumps({"status": "completed", "progress": 100})
        
        result = self.manage_context(
            action="update",
            level="task",
            context_id="task-123",
            data=json_data
        )
        
        assert result["success"] is True
        
        self.facade.update_context.assert_called_once_with(
            level="task",
            context_id="task-123",
            data={"status": "completed", "progress": 100},
            propagate_changes=True
        )
    
    def test_error_message_includes_valid_examples(self):
        """Test that error messages include valid, working examples."""
        result = self.manage_context(
            action="create",
            level="task",
            context_id="task-123",
            data=12345  # Invalid type
        )
        
        assert result["success"] is False
        assert "must be a dictionary object or JSON string" in result["error"]["message"]
        
        # Check examples are present and properly formatted
        examples = result["metadata"]["examples"]
        assert "dictionary_format" in examples
        assert "json_string_format" in examples
        assert "legacy_format" in examples
        
        # Verify JSON example is valid JSON
        json_example = examples["json_string_format"]
        assert "data='{" in json_example
        assert "}'" in json_example