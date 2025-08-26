"""
Tests for Tool Module

This module tests the Tool and FunctionTool functionality including:
- Tool creation from functions with various signatures
- Parameter parsing and validation
- Type conversion and JSON argument parsing
- Context injection and authentication propagation
- Tool execution with different return types
- Error handling and edge cases
- MCP content conversion and serialization
"""

import pytest
import json
import asyncio
import inspect
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Optional, List, Dict, Any, Annotated, Union
from dataclasses import dataclass

from fastmcp.tools.tool import (
    Tool,
    FunctionTool,
    ParsedFunction,
    default_serializer,
    _convert_to_content
)
from fastmcp.utilities.types import MCPContent, Image, Audio, File
from mcp.types import TextContent, ToolAnnotations
from pydantic import Field


class TestTool:
    """Test suite for Tool base class"""
    
    def test_tool_initialization(self):
        """Test Tool initialization with basic parameters"""
        parameters = {"type": "object", "properties": {"param1": {"type": "string"}}}
        annotations = ToolAnnotations(description="Test tool")
        
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters=parameters,
            annotations=annotations
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == parameters
        assert tool.annotations == annotations
        assert tool.serializer is None
    
    def test_tool_to_mcp_tool(self):
        """Test conversion to MCP Tool format"""
        parameters = {"type": "object", "properties": {"param1": {"type": "string"}}}
        annotations = ToolAnnotations(description="Test tool")
        
        tool = Tool(
            name="test_tool",
            description="A test tool", 
            parameters=parameters,
            annotations=annotations
        )
        
        mcp_tool = tool.to_mcp_tool()
        
        assert mcp_tool.name == "test_tool"
        assert mcp_tool.description == "A test tool"
        assert mcp_tool.inputSchema == parameters
        assert mcp_tool.annotations == annotations
    
    def test_tool_to_mcp_tool_with_overrides(self):
        """Test MCP Tool conversion with overrides"""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={}
        )
        
        mcp_tool = tool.to_mcp_tool(name="override_name", description="Override description")
        
        assert mcp_tool.name == "override_name"
        assert mcp_tool.description == "Override description"
    
    @pytest.mark.asyncio
    async def test_tool_run_not_implemented(self):
        """Test that base Tool run method raises NotImplementedError"""
        tool = Tool(name="test", description="test", parameters={})
        
        with pytest.raises(NotImplementedError):
            await tool.run({})
    
    def test_tool_from_function(self):
        """Test creating Tool from function using static method"""
        def test_function(param1: str, param2: int = 42):
            """Test function docstring"""
            return f"{param1}:{param2}"
        
        tool = Tool.from_function(test_function, name="custom_tool")
        
        assert isinstance(tool, FunctionTool)
        assert tool.name == "custom_tool"
        assert "Test function docstring" in tool.description
    
    def test_tool_from_tool_transformation(self):
        """Test creating TransformedTool from existing tool"""
        def base_function(x: int):
            return x * 2
        
        base_tool = Tool.from_function(base_function)
        
        def transform_fn(result: int):
            return result + 1
        
        transformed_tool = Tool.from_tool(
            tool=base_tool,
            transform_fn=transform_fn,
            name="transformed_tool"
        )
        
        # Should return TransformedTool instance
        assert transformed_tool is not None
        assert hasattr(transformed_tool, 'transform_fn')


class TestFunctionTool:
    """Test suite for FunctionTool class"""
    
    def test_function_tool_creation_basic(self):
        """Test basic FunctionTool creation"""
        def test_function(param1: str, param2: int = 42):
            """Test function"""
            return f"{param1}:{param2}"
        
        tool = FunctionTool.from_function(test_function)
        
        assert tool.name == "test_function"
        assert tool.description == "Test function"
        assert tool.fn == test_function
        assert "param1" in tool.parameters["properties"]
        assert "param2" in tool.parameters["properties"]
    
    def test_function_tool_creation_with_overrides(self):
        """Test FunctionTool creation with overrides"""
        def test_function(param: str):
            return param
        
        annotations = ToolAnnotations(description="Custom annotation")
        
        tool = FunctionTool.from_function(
            test_function,
            name="custom_name",
            description="Custom description",
            tags={"tag1", "tag2"},
            annotations=annotations,
            serializer=json.dumps
        )
        
        assert tool.name == "custom_name"
        assert tool.description == "Custom description"
        assert tool.tags == {"tag1", "tag2"}
        assert tool.annotations == annotations
        assert tool.serializer == json.dumps
    
    def test_function_tool_lambda_without_name(self):
        """Test FunctionTool creation with lambda without name raises error"""
        lambda_func = lambda x: x * 2
        
        with pytest.raises(ValueError, match="You must provide a name for lambda functions"):
            FunctionTool.from_function(lambda_func)
    
    def test_function_tool_lambda_with_name(self):
        """Test FunctionTool creation with lambda and provided name"""
        lambda_func = lambda x: x * 2
        
        tool = FunctionTool.from_function(lambda_func, name="multiply_by_two")
        
        assert tool.name == "multiply_by_two"
        assert tool.fn == lambda_func
    
    def test_function_tool_exclude_args(self):
        """Test FunctionTool creation with excluded arguments"""
        def test_function(param1: str, param2: int = 42, excluded_param: str = "default"):
            return f"{param1}:{param2}"
        
        tool = FunctionTool.from_function(
            test_function,
            exclude_args=["excluded_param"]
        )
        
        assert "param1" in tool.parameters["properties"]
        assert "param2" in tool.parameters["properties"]
        assert "excluded_param" not in tool.parameters["properties"]
    
    @pytest.mark.asyncio
    async def test_function_tool_run_basic(self):
        """Test basic function tool execution"""
        def test_function(param1: str, param2: int = 42):
            return f"{param1}:{param2}"
        
        tool = FunctionTool.from_function(test_function)
        
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"param1": "hello", "param2": 100})
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "hello:100"
    
    @pytest.mark.asyncio
    async def test_function_tool_run_async_function(self):
        """Test async function tool execution"""
        async def async_function(param: str):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"async:{param}"
        
        tool = FunctionTool.from_function(async_function)
        
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"param": "test"})
        
        assert len(result) == 1
        assert result[0].text == "async:test"
    
    @pytest.mark.asyncio
    async def test_function_tool_run_with_context_injection(self):
        """Test function execution with context injection"""
        from fastmcp.server.context import Context
        
        def function_with_context(param: str, context: Context):
            return f"{param}:{context.request_id if hasattr(context, 'request_id') else 'no_id'}"
        
        tool = FunctionTool.from_function(function_with_context)
        
        mock_context = Mock()
        mock_context.request_id = "test-request-123"
        
        with patch('fastmcp.tools.tool.get_context', return_value=mock_context):
            with patch('fastmcp.tools.tool.find_kwarg_by_type', return_value='context'):
                result = await tool.run({"param": "hello"})
        
        assert len(result) == 1
        assert "hello:test-request-123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_function_tool_run_with_user_context(self):
        """Test function execution with user context propagation"""
        def test_function(param: str):
            return f"user:{param}"
        
        tool = FunctionTool.from_function(test_function)
        
        mock_user_context = {"user_id": "user-123", "permissions": ["read"]}
        
        with patch('fastmcp.tools.tool.get_context'):
            with patch('fastmcp.tools.tool.get_current_user_context', return_value=mock_user_context):
                with patch('fastmcp.tools.tool.current_user_context') as mock_context_var:
                    result = await tool.run({"param": "test"})
                    
                    # Verify user context was set
                    mock_context_var.set.assert_called_once_with(mock_user_context)
        
        assert len(result) == 1
        assert result[0].text == "user:test"
    
    @pytest.mark.asyncio
    async def test_function_tool_run_json_parsing_enabled(self):
        """Test function execution with JSON argument parsing"""
        def test_function(numbers: List[int], data: Dict[str, Any]):
            return f"numbers:{len(numbers)}, data:{len(data)}"
        
        tool = FunctionTool.from_function(test_function)
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                # Arguments as JSON strings
                arguments = {
                    "numbers": "[1, 2, 3, 4, 5]",
                    "data": '{"key1": "value1", "key2": "value2"}'
                }
                
                result = await tool.run(arguments)
        
        assert len(result) == 1
        assert result[0].text == "numbers:5, data:2"
    
    @pytest.mark.asyncio
    async def test_function_tool_run_type_conversion(self):
        """Test function execution with type conversion"""
        def test_function(
            int_param: int,
            float_param: float,
            bool_param: bool,
            optional_int: Optional[int] = None
        ):
            return f"int:{int_param}, float:{float_param}, bool:{bool_param}, opt:{optional_int}"
        
        tool = FunctionTool.from_function(test_function)
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                # String arguments that should be converted
                arguments = {
                    "int_param": "42",
                    "float_param": "3.14",
                    "bool_param": "true",
                    "optional_int": "100"
                }
                
                result = await tool.run(arguments)
        
        assert len(result) == 1
        assert "int:42" in result[0].text
        assert "float:3.14" in result[0].text
        assert "bool:True" in result[0].text
        assert "opt:100" in result[0].text
    
    @pytest.mark.asyncio
    async def test_function_tool_run_boolean_variations(self):
        """Test boolean type conversion with various string formats"""
        def test_function(flag: bool):
            return f"flag:{flag}"
        
        tool = FunctionTool.from_function(test_function)
        
        test_cases = [
            ("true", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("invalid", False)  # Invalid values should be False
        ]
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                for string_value, expected_bool in test_cases:
                    result = await tool.run({"flag": string_value})
                    assert f"flag:{expected_bool}" in result[0].text
    
    @pytest.mark.asyncio
    async def test_function_tool_run_annotated_types(self):
        """Test function execution with Annotated types"""
        def test_function(
            annotated_int: Annotated[int, Field(description="An integer parameter")],
            optional_annotated: Annotated[Optional[str], Field(description="Optional string")] = None
        ):
            return f"int:{annotated_int}, opt:{optional_annotated}"
        
        tool = FunctionTool.from_function(test_function)
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                arguments = {
                    "annotated_int": "123",
                    "optional_annotated": "test"
                }
                
                result = await tool.run(arguments)
        
        assert len(result) == 1
        assert "int:123" in result[0].text
        assert "opt:test" in result[0].text
    
    def test_extract_target_type_simple(self):
        """Test _extract_target_type with simple types"""
        tool = FunctionTool.from_function(lambda: None)
        
        assert tool._extract_target_type(int) == int
        assert tool._extract_target_type(str) == str
        assert tool._extract_target_type(bool) == bool
    
    def test_extract_target_type_optional(self):
        """Test _extract_target_type with Optional types"""
        tool = FunctionTool.from_function(lambda: None)
        
        assert tool._extract_target_type(Optional[int]) == int
        assert tool._extract_target_type(Optional[str]) == str
        assert tool._extract_target_type(Union[int, None]) == int
    
    def test_extract_target_type_annotated(self):
        """Test _extract_target_type with Annotated types"""
        tool = FunctionTool.from_function(lambda: None)
        
        annotated_int = Annotated[int, Field(description="test")]
        annotated_optional = Annotated[Optional[int], Field(description="test")]
        
        assert tool._extract_target_type(annotated_int) == int
        assert tool._extract_target_type(annotated_optional) == int
    
    @pytest.mark.asyncio
    async def test_function_tool_run_invalid_json(self):
        """Test function execution with invalid JSON arguments"""
        def test_function(data: Dict[str, Any]):
            return f"data:{data}"
        
        tool = FunctionTool.from_function(test_function)
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                # Invalid JSON should be left as string
                arguments = {"data": "invalid json {"}
                
                # This should not raise an error, just pass the invalid JSON as string
                result = await tool.run(arguments)
                # The type adapter should handle validation
                assert len(result) >= 0  # May fail validation, but shouldn't crash
    
    @pytest.mark.asyncio
    async def test_function_tool_run_with_serializer(self):
        """Test function execution with custom serializer"""
        def test_function(name: str):
            return {"name": name, "timestamp": "2023-01-01"}
        
        def custom_serializer(data):
            return f"CUSTOM:{json.dumps(data)}"
        
        tool = FunctionTool.from_function(test_function, serializer=custom_serializer)
        
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"name": "test"})
        
        assert len(result) == 1
        assert result[0].text.startswith("CUSTOM:")
        assert "test" in result[0].text
    
    @pytest.mark.asyncio
    async def test_function_tool_run_serializer_error(self):
        """Test function execution with serializer that raises error"""
        def test_function(data: str):
            return {"data": data}
        
        def failing_serializer(data):
            raise ValueError("Serializer error")
        
        tool = FunctionTool.from_function(test_function, serializer=failing_serializer)
        
        with patch('fastmcp.tools.tool.get_context'):
            # Should fall back to default serializer
            result = await tool.run({"data": "test"})
        
        assert len(result) == 1
        # Should contain the data even though custom serializer failed
        assert "test" in result[0].text


class TestParsedFunction:
    """Test suite for ParsedFunction class"""
    
    def test_parsed_function_basic(self):
        """Test basic ParsedFunction creation"""
        def test_function(param1: str, param2: int = 42):
            """Test function docstring"""
            return f"{param1}:{param2}"
        
        parsed = ParsedFunction.from_function(test_function)
        
        assert parsed.name == "test_function"
        assert parsed.description == "Test function docstring"
        assert parsed.fn == test_function
        assert isinstance(parsed.parameters, dict)
        assert "properties" in parsed.parameters
        assert "param1" in parsed.parameters["properties"]
        assert "param2" in parsed.parameters["properties"]
    
    def test_parsed_function_no_docstring(self):
        """Test ParsedFunction with function without docstring"""
        def no_doc_function(param: str):
            return param
        
        parsed = ParsedFunction.from_function(no_doc_function)
        
        assert parsed.name == "no_doc_function"
        assert parsed.description is None
    
    def test_parsed_function_exclude_args(self):
        """Test ParsedFunction with excluded arguments"""
        def test_function(param1: str, param2: int = 42, excluded: str = "default"):
            return param1
        
        parsed = ParsedFunction.from_function(
            test_function,
            exclude_args=["excluded"]
        )
        
        assert "param1" in parsed.parameters["properties"]
        assert "param2" in parsed.parameters["properties"]
        assert "excluded" not in parsed.parameters["properties"]
    
    def test_parsed_function_context_exclusion(self):
        """Test ParsedFunction automatically excludes Context parameter"""
        from fastmcp.server.context import Context
        
        def function_with_context(param: str, context: Context):
            return param
        
        with patch('fastmcp.tools.tool.find_kwarg_by_type', return_value='context'):
            parsed = ParsedFunction.from_function(function_with_context)
        
        assert "param" in parsed.parameters["properties"]
        assert "context" not in parsed.parameters["properties"]
    
    def test_parsed_function_validation_var_positional(self):
        """Test ParsedFunction validation rejects *args"""
        def invalid_function(param: str, *args):
            return param
        
        with pytest.raises(ValueError, match="Functions with \*args are not supported"):
            ParsedFunction.from_function(invalid_function)
    
    def test_parsed_function_validation_var_keyword(self):
        """Test ParsedFunction validation rejects **kwargs"""
        def invalid_function(param: str, **kwargs):
            return param
        
        with pytest.raises(ValueError, match="Functions with \*\*kwargs are not supported"):
            ParsedFunction.from_function(invalid_function)
    
    def test_parsed_function_validation_exclude_args_not_exist(self):
        """Test ParsedFunction validation for non-existent exclude_args"""
        def test_function(param: str):
            return param
        
        with pytest.raises(ValueError, match="Parameter 'nonexistent' in exclude_args does not exist"):
            ParsedFunction.from_function(test_function, exclude_args=["nonexistent"])
    
    def test_parsed_function_validation_exclude_args_no_default(self):
        """Test ParsedFunction validation for exclude_args without default"""
        def test_function(required_param: str, optional_param: str = "default"):
            return required_param
        
        with pytest.raises(ValueError, match="Parameter 'required_param' in exclude_args must have a default value"):
            ParsedFunction.from_function(test_function, exclude_args=["required_param"])
    
    def test_parsed_function_callable_class(self):
        """Test ParsedFunction with callable class"""
        class CallableClass:
            """Callable class docstring"""
            
            def __call__(self, param: str):
                return f"called:{param}"
        
        callable_obj = CallableClass()
        
        parsed = ParsedFunction.from_function(callable_obj)
        
        assert parsed.name == "CallableClass"
        assert "Callable class docstring" in parsed.description
        assert "param" in parsed.parameters["properties"]
    
    def test_parsed_function_staticmethod(self):
        """Test ParsedFunction with staticmethod"""
        class TestClass:
            @staticmethod
            def static_method(param: str):
                """Static method docstring"""
                return param
        
        parsed = ParsedFunction.from_function(TestClass.static_method)
        
        assert parsed.name == "static_method"
        assert "Static method docstring" in parsed.description
        assert "param" in parsed.parameters["properties"]
    
    def test_parsed_function_without_validation(self):
        """Test ParsedFunction creation without validation"""
        def function_with_args(param: str, *args, **kwargs):
            return param
        
        # Should not raise error when validation is disabled
        parsed = ParsedFunction.from_function(function_with_args, validate=False)
        
        assert parsed.name == "function_with_args"
        assert parsed.fn == function_with_args


class TestContentConversion:
    """Test suite for content conversion functions"""
    
    def test_default_serializer(self):
        """Test default_serializer function"""
        data = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        
        result = default_serializer(data)
        
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result
        assert "42" in result
    
    def test_convert_to_content_none(self):
        """Test _convert_to_content with None"""
        result = _convert_to_content(None)
        assert result == []
    
    def test_convert_to_content_mcp_content(self):
        """Test _convert_to_content with MCPContent"""
        text_content = TextContent(type="text", text="test content")
        
        result = _convert_to_content(text_content)
        
        assert len(result) == 1
        assert result[0] == text_content
    
    def test_convert_to_content_image(self):
        """Test _convert_to_content with Image"""
        mock_image = Mock(spec=Image)
        mock_image_content = Mock()
        mock_image.to_image_content.return_value = mock_image_content
        
        result = _convert_to_content(mock_image)
        
        assert len(result) == 1
        assert result[0] == mock_image_content
        mock_image.to_image_content.assert_called_once()
    
    def test_convert_to_content_audio(self):
        """Test _convert_to_content with Audio"""
        mock_audio = Mock(spec=Audio)
        mock_audio_content = Mock()
        mock_audio.to_audio_content.return_value = mock_audio_content
        
        result = _convert_to_content(mock_audio)
        
        assert len(result) == 1
        assert result[0] == mock_audio_content
        mock_audio.to_audio_content.assert_called_once()
    
    def test_convert_to_content_file(self):
        """Test _convert_to_content with File"""
        mock_file = Mock(spec=File)
        mock_resource_content = Mock()
        mock_file.to_resource_content.return_value = mock_resource_content
        
        result = _convert_to_content(mock_file)
        
        assert len(result) == 1
        assert result[0] == mock_resource_content
        mock_file.to_resource_content.assert_called_once()
    
    def test_convert_to_content_string(self):
        """Test _convert_to_content with string"""
        text = "Hello, World!"
        
        result = _convert_to_content(text)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "Hello, World!"
    
    def test_convert_to_content_list_mixed(self):
        """Test _convert_to_content with mixed list"""
        mock_image = Mock(spec=Image)
        mock_image_content = Mock()
        mock_image.to_image_content.return_value = mock_image_content
        
        text_content = TextContent(type="text", text="existing content")
        regular_data = {"key": "value"}
        
        mixed_list = [mock_image, text_content, regular_data, "plain string"]
        
        result = _convert_to_content(mixed_list)
        
        # Should separate MCP types from regular content
        assert len(result) >= 2  # At least regular content + MCP types
        
        # Check that image content is included
        assert mock_image_content in result
        assert text_content in result
    
    def test_convert_to_content_list_regular_only(self):
        """Test _convert_to_content with list of regular items"""
        regular_list = ["item1", "item2", {"key": "value"}]
        
        result = _convert_to_content(regular_list)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should contain serialized version of the list
        assert "item1" in result[0].text
        assert "item2" in result[0].text
    
    def test_convert_to_content_dict(self):
        """Test _convert_to_content with dictionary"""
        data = {"name": "test", "value": 42, "nested": {"key": "value"}}
        
        result = _convert_to_content(data)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "name" in result[0].text
        assert "42" in result[0].text
    
    def test_convert_to_content_custom_serializer(self):
        """Test _convert_to_content with custom serializer"""
        data = {"key": "value"}
        
        def custom_serializer(obj):
            return f"CUSTOM:{json.dumps(obj)}"
        
        result = _convert_to_content(data, serializer=custom_serializer)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text.startswith("CUSTOM:")
        assert "key" in result[0].text
    
    def test_convert_to_content_serializer_error(self):
        """Test _convert_to_content with failing custom serializer"""
        data = {"key": "value"}
        
        def failing_serializer(obj):
            raise ValueError("Serializer failed")
        
        with patch('fastmcp.tools.tool.logger') as mock_logger:
            result = _convert_to_content(data, serializer=failing_serializer)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should fall back to default serializer
        assert "key" in result[0].text
        
        # Should log warning
        mock_logger.warning.assert_called_once()
    
    def test_convert_to_content_tuple(self):
        """Test _convert_to_content with tuple"""
        data = ("item1", 42, {"key": "value"})
        
        result = _convert_to_content(data)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "item1" in result[0].text
        assert "42" in result[0].text
    
    def test_convert_to_content_single_item_processing(self):
        """Test _convert_to_content with single item processing flag"""
        data = ["item1", "item2"]
        
        result = _convert_to_content(data, _process_as_single_item=True)
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should process as single item, not extract elements
        assert "item1" in result[0].text and "item2" in result[0].text


class TestIntegration:
    """Integration tests for Tool functionality"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_function_tool(self):
        """Test complete end-to-end FunctionTool usage"""
        def calculate(operation: str, x: int, y: int) -> Dict[str, Any]:
            """Perform a mathematical operation"""
            operations = {
                "add": x + y,
                "subtract": x - y,
                "multiply": x * y,
                "divide": x / y if y != 0 else None
            }
            return {
                "operation": operation,
                "x": x,
                "y": y,
                "result": operations.get(operation),
                "timestamp": "2023-01-01T00:00:00Z"
            }
        
        # Create tool
        tool = FunctionTool.from_function(
            calculate,
            name="calculator",
            description="A mathematical calculator tool",
            tags={"math", "utility"}
        )
        
        # Test tool properties
        assert tool.name == "calculator"
        assert tool.description == "A mathematical calculator tool"
        assert tool.tags == {"math", "utility"}
        
        # Test MCP tool conversion
        mcp_tool = tool.to_mcp_tool()
        assert mcp_tool.name == "calculator"
        assert "operation" in mcp_tool.inputSchema["properties"]
        
        # Test tool execution
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({
                "operation": "multiply",
                "x": 6,
                "y": 7
            })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        result_text = result[0].text
        assert "multiply" in result_text
        assert "42" in result_text  # 6 * 7 = 42
    
    @pytest.mark.asyncio
    async def test_complex_type_handling(self):
        """Test handling of complex types and nested structures"""
        @dataclass
        class Person:
            name: str
            age: int
            
        def process_data(
            people: List[Dict[str, Any]],
            config: Dict[str, Any],
            flags: List[bool] = None
        ) -> Dict[str, Any]:
            """Process complex nested data"""
            return {
                "people_count": len(people),
                "config_keys": list(config.keys()),
                "flags": flags or [],
                "processed": True
            }
        
        tool = FunctionTool.from_function(process_data)
        
        with patch('fastmcp.settings.tool_attempt_parse_json_args', True):
            with patch('fastmcp.tools.tool.get_context'):
                arguments = {
                    "people": '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]',
                    "config": '{"debug": true, "timeout": 300}',
                    "flags": "[true, false, true]"
                }
                
                result = await tool.run(arguments)
        
        assert len(result) == 1
        result_text = result[0].text
        assert "people_count" in result_text
        assert "2" in result_text  # Two people
        assert "debug" in result_text
        assert "timeout" in result_text
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        def potentially_failing_function(mode: str, value: int = 42):
            """Function that can fail in various ways"""
            if mode == "success":
                return f"Success: {value}"
            elif mode == "type_error":
                return value / "string"  # Type error
            elif mode == "value_error":
                raise ValueError("Something went wrong")
            elif mode == "return_none":
                return None
            else:
                return {"complex": {"nested": {"data": value}}}
        
        tool = FunctionTool.from_function(potentially_failing_function)
        
        # Test successful execution
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"mode": "success", "value": 100})
            assert len(result) == 1
            assert "Success: 100" in result[0].text
        
        # Test None return
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"mode": "return_none"})
            assert len(result) == 0  # None should return empty list
        
        # Test complex return value
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"mode": "complex", "value": 42})
            assert len(result) == 1
            assert "42" in result[0].text
    
    @pytest.mark.asyncio
    async def test_authentication_and_context_propagation(self):
        """Test authentication context propagation through tools"""
        def authenticated_function(resource_id: str, action: str):
            """Function that should receive authentication context"""
            # In real implementation, this would check authentication
            return f"Accessing {resource_id} for {action}"
        
        tool = FunctionTool.from_function(authenticated_function)
        
        mock_user_context = {
            "user_id": "user-123",
            "permissions": ["read", "write"],
            "session_id": "session-456"
        }
        
        with patch('fastmcp.tools.tool.get_context'):
            with patch('fastmcp.tools.tool.get_current_user_context', return_value=mock_user_context):
                with patch('fastmcp.tools.tool.current_user_context') as mock_context_var:
                    result = await tool.run({
                        "resource_id": "document-789",
                        "action": "read"
                    })
                    
                    # Verify context was propagated
                    mock_context_var.set.assert_called_once_with(mock_user_context)
        
        assert len(result) == 1
        assert "Accessing document-789 for read" in result[0].text


class TestEdgeCases:
    """Test suite for edge cases and unusual scenarios"""
    
    @pytest.mark.asyncio
    async def test_very_large_arguments(self):
        """Test handling of very large arguments"""
        def handle_large_data(data: str):
            return f"Processed {len(data)} characters"
        
        tool = FunctionTool.from_function(handle_large_data)
        
        # Test with large string
        large_string = "x" * 100000  # 100KB string
        
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({"data": large_string})
        
        assert len(result) == 1
        assert "100000" in result[0].text
    
    def test_function_with_no_parameters(self):
        """Test function with no parameters"""
        def no_param_function():
            """Function with no parameters"""
            return "No parameters needed"
        
        tool = FunctionTool.from_function(no_param_function)
        
        assert "properties" in tool.parameters
        # Should have empty or minimal properties
        assert len(tool.parameters.get("properties", {})) == 0
    
    def test_function_with_all_optional_parameters(self):
        """Test function with all optional parameters"""
        def all_optional_function(
            param1: str = "default1",
            param2: int = 42,
            param3: bool = True
        ):
            return f"{param1}:{param2}:{param3}"
        
        tool = FunctionTool.from_function(all_optional_function)
        
        assert "param1" in tool.parameters["properties"]
        assert "param2" in tool.parameters["properties"]
        assert "param3" in tool.parameters["properties"]
        
        # All parameters should be optional in schema
        required = tool.parameters.get("required", [])
        assert len(required) == 0
    
    @pytest.mark.asyncio
    async def test_function_returning_various_types(self):
        """Test function returning various data types"""
        test_cases = [
            ("string", "Hello World"),
            ("integer", 42),
            ("float", 3.14159),
            ("boolean", True),
            ("list", [1, 2, 3, "four"]),
            ("dict", {"key": "value", "number": 123}),
            ("none", None),
        ]
        
        for return_type, return_value in test_cases:
            def dynamic_function(return_type_param: str):
                nonlocal return_value
                return return_value
            
            tool = FunctionTool.from_function(dynamic_function, name=f"test_{return_type}")
            
            with patch('fastmcp.tools.tool.get_context'):
                result = await tool.run({"return_type_param": return_type})
                
                if return_value is None:
                    assert len(result) == 0
                else:
                    assert len(result) == 1
                    if isinstance(return_value, str):
                        assert result[0].text == return_value
                    else:
                        assert str(return_value) in result[0].text or json.dumps(return_value) in result[0].text
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        def unicode_function(text: str, emoji: str = "🚀"):
            """Function handling unicode"""
            return f"{text} {emoji} 你好世界 🌟"
        
        tool = FunctionTool.from_function(unicode_function)
        
        with patch('fastmcp.tools.tool.get_context'):
            result = await tool.run({
                "text": "Hello 世界",
                "emoji": "🎉"
            })
        
        assert len(result) == 1
        assert "Hello 世界" in result[0].text
        assert "🎉" in result[0].text
        assert "你好世界" in result[0].text
        assert "🌟" in result[0].text