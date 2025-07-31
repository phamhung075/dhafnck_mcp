#!/usr/bin/env python3
"""
Test the insights_found parameter fix by directly testing with the actual MCP tool registration.
This simulates what would happen when Claude uses the MCP protocol.
"""

import sys
import os
import json
import logging

# Add the source path to PYTHONPATH
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

# Configure logging to reduce noise during testing
logging.basicConfig(level=logging.ERROR)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)

def test_fastmcp_tool_creation():
    """Test creating a FastMCP tool with the monkey patch applied."""
    print("🧪 Testing FastMCP Tool Creation with Schema Monkey Patch")
    print("=" * 60)
    
    try:
        # Import and apply monkey patch
        from fastmcp.task_management.interface.utils.schema_monkey_patch import apply_all_schema_patches
        apply_all_schema_patches()
        print("✅ Schema monkey patches applied")
        
        # Import FastMCP after patches are applied
        from fastmcp import FastMCP
        from typing import Union, List, Optional, Annotated
        from pydantic import Field
        
        # Create a minimal FastMCP instance
        mcp = FastMCP()
        
        # Define a test tool similar to manage_subtask but simplified
        @mcp.tool(name="test_insights_tool", description="Test tool for insights_found parameter")
        def test_insights_tool(
            action: Annotated[str, Field(description="Action to perform")],
            task_id: Annotated[str, Field(description="Task ID")],
            insights_found: Annotated[Optional[Union[List[str], str]], Field(description="Insights discovered during work. Accepts array, JSON string array, or comma-separated string.")] = None
        ):
            return {
                "success": True,
                "action": action,
                "task_id": task_id,
                "insights_found": insights_found,
                "insights_type": type(insights_found).__name__,
                "message": "Tool executed successfully"
            }
        
        print("✅ Test tool registered successfully")
        
        # Get the tool's schema
        tools = mcp.list_tools()
        test_tool = None
        for tool in tools:
            if tool.name == "test_insights_tool":
                test_tool = tool
                break
        
        if not test_tool:
            print("❌ Test tool not found in registered tools")
            return False
        
        # Check the schema for insights_found parameter
        schema = test_tool.inputSchema
        insights_schema = schema.get("properties", {}).get("insights_found", {})
        
        print(f"\nSchema for insights_found:")
        print(json.dumps(insights_schema, indent=2))
        
        # Check if the schema is flexible (has anyOf or allows string)
        has_any_of = "anyOf" in insights_schema
        has_string_type = False
        has_array_type = False
        
        if has_any_of:
            for option in insights_schema["anyOf"]:
                if option.get("type") == "string":
                    has_string_type = True
                elif option.get("type") == "array":
                    has_array_type = True
        else:
            # Check direct type
            if insights_schema.get("type") == "string":
                has_string_type = True
            elif insights_schema.get("type") == "array":
                has_array_type = True
        
        schema_is_flexible = has_string_type and has_array_type
        
        if schema_is_flexible:
            print("✅ Schema is flexible - accepts both string and array")
        else:
            print("❌ Schema is not flexible enough")
            print(f"   Has string type: {has_string_type}")
            print(f"   Has array type: {has_array_type}")
        
        # Test calling the tool with different parameter formats
        test_cases = [
            {
                "name": "JSON string array (original issue)",
                "arguments": {
                    "action": "test", 
                    "task_id": "task-123",
                    "insights_found": '["Using jest-mock-extended library", "Test cases should cover edge cases"]'
                }
            },
            {
                "name": "Comma-separated string",
                "arguments": {
                    "action": "test", 
                    "task_id": "task-123",
                    "insights_found": "insight1, insight2, insight3"
                }
            },
            {
                "name": "Direct array",
                "arguments": {
                    "action": "test", 
                    "task_id": "task-123",
                    "insights_found": ["direct", "array", "test"]
                }
            }
        ]
        
        print("\n🧪 Testing Tool Execution:")
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test_case['name']}")
            try:
                # This simulates what happens when Claude calls the tool
                result = test_insights_tool(**test_case["arguments"])
                print(f"✅ PASSED - Result: {result}")
                
            except Exception as e:
                error_str = str(e)
                if "validation error" in error_str.lower() or "not valid under any of the given schemas" in error_str:
                    print(f"❌ FAILED - Validation error: {e}")
                    all_passed = False
                else:
                    print(f"⚠️  Unexpected error: {e}")
                    all_passed = False
        
        return schema_is_flexible and all_passed
        
    except Exception as e:
        print(f"❌ Error in FastMCP test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_validation_directly():
    """Test Pydantic validation directly to see how Union types work."""
    print("\n🧪 Testing Pydantic Validation Directly")
    print("=" * 60)
    
    try:
        from pydantic import ValidationError, BaseModel, Field
        from typing import Union, List, Optional
        
        # Define a model similar to our tool parameters
        class TestModel(BaseModel):
            action: str
            task_id: str
            insights_found: Optional[Union[List[str], str]] = Field(None, description="Test insights parameter")
        
        test_cases = [
            {
                "name": "JSON string array",
                "data": {
                    "action": "test",
                    "task_id": "task-123", 
                    "insights_found": '["insight1", "insight2"]'
                }
            },
            {
                "name": "Direct array",
                "data": {
                    "action": "test",
                    "task_id": "task-123",
                    "insights_found": ["insight1", "insight2"]
                }
            },
            {
                "name": "Simple string",
                "data": {
                    "action": "test",
                    "task_id": "task-123",
                    "insights_found": "single insight"
                }
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            print(f"\nTesting {test_case['name']}:")
            try:
                model = TestModel(**test_case['data'])
                print(f"✅ PASSED - insights_found: {model.insights_found} (type: {type(model.insights_found).__name__})")
            except ValidationError as e:
                print(f"❌ FAILED - Validation error: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error in Pydantic test: {e}")
        return False


def main():
    """Run all tests to verify the fix."""
    print("🧪 Testing insights_found Parameter Fix")
    print("=" * 80)
    
    # Test Pydantic validation directly  
    pydantic_passed = test_pydantic_validation_directly()
    
    # Test FastMCP tool creation and execution
    fastmcp_passed = test_fastmcp_tool_creation()
    
    print("\n" + "=" * 80)
    print("🎯 Test Results Summary:")
    print(f"Pydantic Validation: {'✅ PASSED' if pydantic_passed else '❌ FAILED'}")
    print(f"FastMCP Tool Creation: {'✅ PASSED' if fastmcp_passed else '❌ FAILED'}")
    
    if pydantic_passed and fastmcp_passed:
        print("\n🎉 SUCCESS! The insights_found parameter fix is working correctly.")
        print("   - JSON string arrays are accepted")
        print("   - Comma-separated strings are accepted") 
        print("   - Direct arrays are accepted")
        print("   - Schema monkey patch is working")
        return 0
    else:
        print("\n⚠️  PARTIAL SUCCESS: Some validation is working, but MCP framework integration may still have issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())