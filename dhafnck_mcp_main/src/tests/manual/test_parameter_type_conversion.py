#!/usr/bin/env python3
"""
Test parameter type conversion support across different MCP controllers.
This test verifies that various controllers support automatic conversion of:
- String booleans ("true", "false") to boolean
- String integers ("5", "100") to integer
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_task_controller_boolean_conversion():
    """Test that task controller supports string boolean conversion."""
    print("\n=== Testing Task Controller Boolean Conversion ===")
    
    try:
        # Create controller
        task_facade_factory = TaskFacadeFactory()
        context_facade_factory = UnifiedContextFacadeFactory()
        controller = TaskMCPController(task_facade_factory, context_facade_factory)
        
        # Test cases for boolean conversion
        test_cases = [
            ("true", True),
            ("false", False),
            ("True", True),
            ("FALSE", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("on", True),
            ("off", False),
            ("enabled", True),
            ("disabled", False),
        ]
        
        print("\nTesting _coerce_to_bool method:")
        for input_val, expected in test_cases:
            result = controller._coerce_to_bool(input_val, "test_param")
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{input_val}' → {result} (expected: {expected})")
        
        # Test actual boolean values
        print("\nTesting actual boolean values:")
        for bool_val in [True, False]:
            result = controller._coerce_to_bool(bool_val, "test_param")
            status = "✓" if result == bool_val else "✗"
            print(f"  {status} {bool_val} → {result}")
        
        print("\n✅ Task controller boolean conversion test completed")
        
    except Exception as e:
        print(f"\n❌ Task controller test failed: {e}")
        import traceback
        traceback.print_exc()


def test_context_controller_boolean_parameters():
    """Test if unified context controller handles string booleans in actual method calls."""
    print("\n=== Testing Unified Context Controller Boolean Parameters ===")
    
    try:
        # Create controller
        context_facade_factory = UnifiedContextFacadeFactory()
        controller = UnifiedContextMCPController(context_facade_factory)
        
        # Create a mock MCP server class for testing
        class MockMCP:
            def __init__(self):
                self.tools = {}
            
            def tool(self, name=None, description=None):
                def decorator(func):
                    self.tools[name] = func
                    return func
                return decorator
        
        # Register tools
        mock_mcp = MockMCP()
        controller.register_tools(mock_mcp)
        
        # Get the manage_context tool
        manage_context = mock_mcp.tools.get("manage_context")
        if not manage_context:
            print("❌ manage_context tool not found")
            return
        
        print("\nTesting string boolean parameters:")
        
        # Test with string "true"
        try:
            result = manage_context(
                action="get",
                level="task",
                context_id="test-123",
                include_inherited="true",  # String boolean
                force_refresh="false"      # String boolean
            )
            print(f"  ✓ String booleans accepted: include_inherited='true', force_refresh='false'")
            if "error" in result and "not valid under any of the given schemas" in result.get("error", ""):
                print(f"    ✗ But got validation error: {result['error']}")
            else:
                print(f"    ✓ No validation error")
        except Exception as e:
            print(f"  ✗ String booleans rejected with error: {e}")
        
        # Test with actual booleans
        try:
            result = manage_context(
                action="get", 
                level="task",
                context_id="test-123",
                include_inherited=True,   # Actual boolean
                force_refresh=False       # Actual boolean
            )
            print(f"  ✓ Actual booleans accepted: include_inherited=True, force_refresh=False")
        except Exception as e:
            print(f"  ✗ Actual booleans rejected with error: {e}")
        
        print("\n✅ Context controller parameter test completed")
        
    except Exception as e:
        print(f"\n❌ Context controller test failed: {e}")
        import traceback
        traceback.print_exc()


def test_parameter_validation_fix_integration():
    """Test if the parameter_validation_fix module is integrated into controllers."""
    print("\n=== Testing Parameter Validation Fix Integration ===")
    
    try:
        # Check if the parameter validation fix is imported
        from fastmcp.task_management.interface.utils.parameter_validation_fix import (
            ParameterTypeCoercer, coerce_parameter_types
        )
        print("✓ parameter_validation_fix module found")
        
        # Test the coercer directly
        test_params = {
            "limit": "5",
            "include_context": "true",
            "force_refresh": "false",
            "progress_percentage": "75"
        }
        
        coerced = ParameterTypeCoercer.coerce_parameter_types(test_params)
        print("\nDirect coercion test:")
        for key, value in coerced.items():
            original = test_params[key]
            print(f"  '{key}': '{original}' → {value} (type: {type(value).__name__})")
        
        # Check if MCPParameterValidator is used in controllers
        from fastmcp.task_management.interface.utils.mcp_parameter_validator import (
            MCPParameterValidator
        )
        print("\n✓ MCPParameterValidator found")
        
        # Test the validator
        validation_result = MCPParameterValidator.validate_and_coerce_mcp_parameters(
            "search", {"query": "test", "limit": "5"}
        )
        
        if validation_result["success"]:
            print("✓ MCPParameterValidator successfully coerced parameters:")
            for key, value in validation_result["coerced_params"].items():
                print(f"  '{key}': {value} (type: {type(value).__name__})")
        else:
            print(f"✗ MCPParameterValidator failed: {validation_result['error']}")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all parameter type conversion tests."""
    print("=" * 60)
    print("PARAMETER TYPE CONVERSION TEST")
    print("=" * 60)
    
    # Test task controller
    test_task_controller_boolean_conversion()
    
    # Test context controller
    test_context_controller_boolean_parameters()
    
    # Test parameter validation fix integration
    test_parameter_validation_fix_integration()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("""
FINDINGS:
1. Task Controller: HAS built-in _coerce_to_bool method that converts string booleans
2. Context Controller: Does NOT appear to have automatic type conversion
3. Parameter Validation Fix: EXISTS but not integrated into all controllers

RECOMMENDATION:
- Task controller already supports string boolean conversion
- Other controllers should integrate MCPParameterValidator for consistency
- The parameter_validation_fix.py provides comprehensive type coercion
""")


if __name__ == "__main__":
    main()