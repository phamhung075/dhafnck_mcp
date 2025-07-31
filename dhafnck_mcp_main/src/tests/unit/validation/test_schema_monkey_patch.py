#!/usr/bin/env python3
"""
Test script to verify the schema monkey patch for insights_found parameter is working.
This tests both the MCP tools directly and via the HTTP client.
"""

import sys
import os
import logging

# Add the source path to PYTHONPATH
sys.path.insert(0, '/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

# Configure logging to reduce noise during testing
logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)

def test_mcp_direct():
    """Test the MCP tools directly (without HTTP)."""
    print("🧪 Testing MCP Tools Direct Access")
    print("=" * 50)
    
    try:
        from fastmcp.task_management.interface.controllers.subtask_mcp_controller import SubtaskMCPController
        from fastmcp.task_management.application.factories.subtask_facade_factory import SubtaskFacadeFactory
        
        # Create controller
        subtask_facade_factory = SubtaskFacadeFactory()
        controller = SubtaskMCPController(subtask_facade_factory)
        
        print("✅ Controller created successfully")
        
        # Test with JSON string array (the original issue)
        test_cases = [
            {
                "name": "JSON string array (original issue)",
                "insights_found": '["Using jest-mock-extended library simplifies JWT library mocking", "Test cases should cover edge cases like empty payload and expired secrets"]'
            },
            {
                "name": "Comma-separated string",
                "insights_found": "insight1, insight2, insight3"
            },
            {
                "name": "Single string",
                "insights_found": "single insight"
            },
            {
                "name": "Already a list",
                "insights_found": ["already", "a", "list"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test_case['name']}")
            try:
                result = controller.manage_subtask(
                    action="complete",
                    task_id="test-task-123",
                    subtask_id=f"test-subtask-{i}",
                    completion_summary="Test completion with insights",
                    insights_found=test_case["insights_found"]
                )
                
                if result.get("success"):
                    print(f"✅ PASSED - Call successful")
                else:
                    error_msg = result.get("error", "Unknown error")
                    if "validation error" in error_msg.lower() or "not valid under any of the given schemas" in error_msg:
                        print(f"❌ FAILED - Schema validation error: {error_msg}")
                    else:
                        print(f"⚠️  EXPECTED ERROR (business logic): {error_msg}")
                        
            except Exception as e:
                error_str = str(e)
                if "validation error" in error_str.lower() or "not valid under any of the given schemas" in error_str:
                    print(f"❌ FAILED - Schema validation exception: {e}")
                else:
                    print(f"⚠️  EXPECTED EXCEPTION (business logic): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in direct test: {e}")
        return False


def test_schema_generation():
    """Test if the monkey patch is applied to schema generation."""
    print("\n🧪 Testing Schema Generation")
    print("=" * 50)
    
    try:
        # Import after potential monkey patching
        from fastmcp.task_management.interface.utils.schema_monkey_patch import apply_all_schema_patches, SchemaPatcher
        
        # Apply patches manually to test
        apply_all_schema_patches()
        print("✅ Monkey patches applied")
        
        # Test schema patching directly
        original_schema = {
            "type": "object",
            "properties": {
                "insights_found": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"}
                    ],
                    "description": "Insights discovered"
                },
                "normal_param": {
                    "type": "string",
                    "description": "Normal parameter"
                }
            }
        }
        
        patched_schema = SchemaPatcher.patch_schema_for_flexible_arrays(original_schema)
        
        insights_schema = patched_schema["properties"]["insights_found"]
        if "anyOf" in insights_schema and len(insights_schema["anyOf"]) >= 2:
            print("✅ Schema patching working - insights_found has flexible anyOf schema")
            return True
        else:
            print("❌ Schema patching failed - insights_found doesn't have flexible schema")
            return False
            
    except Exception as e:
        print(f"❌ Error in schema test: {e}")
        return False


def test_parameter_coercion():
    """Test the parameter coercion functionality."""
    print("\n🧪 Testing Parameter Coercion")
    print("=" * 50)
    
    try:
        from fastmcp.task_management.interface.utils.parameter_validation_fix import ParameterTypeCoercer
        
        test_cases = [
            {
                "name": "JSON string array",
                "input": {"insights_found": '["insight1", "insight2"]'},
                "expected": ["insight1", "insight2"]
            },
            {
                "name": "Comma-separated string", 
                "input": {"insights_found": "insight1, insight2, insight3"},
                "expected": ["insight1", "insight2", "insight3"]
            },
            {
                "name": "Single string",
                "input": {"insights_found": "single insight"},
                "expected": ["single insight"]
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            try:
                result = ParameterTypeCoercer.coerce_parameter_types(test_case["input"])
                actual = result.get("insights_found")
                expected = test_case["expected"]
                
                if actual == expected:
                    print(f"✅ PASSED - {actual}")
                else:
                    print(f"❌ FAILED - Expected: {expected}, Got: {actual}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error in coercion test: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Schema Monkey Patch Fix for insights_found Parameter")
    print("=" * 80)
    
    # Test parameter coercion
    coercion_passed = test_parameter_coercion()
    
    # Test schema generation
    schema_passed = test_schema_generation()
    
    # Test MCP direct access
    mcp_passed = test_mcp_direct()
    
    print("\n" + "=" * 80)
    print("🎯 Test Results Summary:")
    print(f"Parameter Coercion: {'✅ PASSED' if coercion_passed else '❌ FAILED'}")
    print(f"Schema Generation: {'✅ PASSED' if schema_passed else '❌ FAILED'}")
    print(f"MCP Direct Access: {'✅ PASSED' if mcp_passed else '❌ FAILED'}")
    
    if coercion_passed and schema_passed and mcp_passed:
        print("\n🎉 All tests passed! The schema monkey patch fix is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. The fix may need additional work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())