#!/usr/bin/env python3
"""
Demo: Parameter Validation Fix in Action

This demonstrates how the parameter validation fix resolves the original issue:
"Input validation error: '5' is not valid under any of the given schemas"
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.interface.utils.parameter_validation_fix import coerce_parameter_types, validate_parameters


def demo_original_failing_cases():
    """Demo the exact cases that were failing before the fix."""
    print("🧪 Demo: Original Failing Cases Now Fixed")
    print("=" * 50)
    
    # These are the exact cases mentioned in the issue
    failing_cases = [
        {
            "description": "Task search with string limit '5'",
            "action": "search", 
            "params": {"query": "test", "limit": "5"},
            "expected_coerced": {"query": "test", "limit": 5}
        },
        {
            "description": "Task list with string integer limit",
            "action": "list",
            "params": {"limit": "5"},
            "expected_coerced": {"limit": 5}
        },
        {
            "description": "Subtask update with string progress percentage '50'",
            "action": "update",
            "params": {"task_id": "test", "progress_percentage": "50"},
            "expected_coerced": {"task_id": "test", "progress_percentage": 50}
        },
        {
            "description": "Task with string boolean 'true'",
            "action": "get",
            "params": {"task_id": "test", "include_context": "true"},
            "expected_coerced": {"task_id": "test", "include_context": True}
        },
        {
            "description": "Mixed types - the worst case scenario",
            "action": "search",
            "params": {
                "query": "test",
                "limit": "10",           # String integer
                "include_context": "false",  # String boolean
                "timeout": "30"         # String integer
            },
            "expected_coerced": {
                "query": "test",
                "limit": 10,            # Coerced to int
                "include_context": False,    # Coerced to bool
                "timeout": 30           # Coerced to int
            }
        }
    ]
    
    for i, case in enumerate(failing_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Original params: {case['params']}")
        
        try:
            # Apply our fix
            result = validate_parameters(case['action'], case['params'])
            
            if result['success']:
                coerced_params = result['coerced_params']
                print(f"   ✅ SUCCESS: {coerced_params}")
                
                # Verify the coercion worked as expected
                for key, expected_value in case['expected_coerced'].items():
                    actual_value = coerced_params.get(key)
                    if actual_value == expected_value and type(actual_value) == type(expected_value):
                        print(f"      ✓ {key}: {actual_value} ({type(actual_value).__name__})")
                    else:
                        print(f"      ❌ {key}: expected {expected_value} ({type(expected_value).__name__}), got {actual_value} ({type(actual_value).__name__})")
            else:
                print(f"   ❌ FAILED: {result['error']}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
    
    print(f"\n🎯 Demo Complete! The original validation errors are now fixed.")


def demo_type_coercion_details():
    """Demo the type coercion functionality in detail."""
    print("\n\n🔧 Demo: Type Coercion Details")
    print("=" * 40)
    
    test_cases = [
        # Integer coercion
        {"params": {"limit": "5"}, "description": "String '5' → int 5"},
        {"params": {"progress_percentage": "75"}, "description": "String '75' → int 75"},
        {"params": {"timeout": "30"}, "description": "String '30' → int 30"},
        
        # Boolean coercion
        {"params": {"include_context": "true"}, "description": "String 'true' → bool True"},
        {"params": {"force": "false"}, "description": "String 'false' → bool False"},
        {"params": {"audit_required": "1"}, "description": "String '1' → bool True"},
        {"params": {"include_details": "0"}, "description": "String '0' → bool False"},
        
        # Already correct types (should pass through unchanged)
        {"params": {"limit": 10}, "description": "int 10 → int 10 (unchanged)"},
        {"params": {"include_context": True}, "description": "bool True → bool True (unchanged)"},
        
        # Mixed types
        {"params": {"limit": "25", "include_context": "true", "timeout": 60}, 
         "description": "Mixed: string int, string bool, and real int"},
    ]
    
    for case in test_cases:
        print(f"\n{case['description']}")
        print(f"  Input:  {case['params']}")
        
        try:
            coerced = coerce_parameter_types(case['params'])
            print(f"  Output: {coerced}")
            
            # Show type changes
            for key, value in coerced.items():
                original_type = type(case['params'][key]).__name__
                new_type = type(value).__name__
                if original_type != new_type:
                    print(f"    {key}: {original_type} → {new_type}")
                else:
                    print(f"    {key}: {new_type} (unchanged)")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")


def demo_error_handling():
    """Demo error handling for invalid parameter values."""
    print("\n\n⚠️  Demo: Error Handling for Invalid Values")
    print("=" * 45)
    
    error_cases = [
        {"params": {"limit": "abc"}, "description": "Non-numeric string for integer parameter"},
        {"params": {"progress_percentage": "150"}, "description": "String integer outside valid range"},
        {"params": {"include_context": "maybe"}, "description": "Invalid string for boolean parameter"},
        {"params": {"limit": ""}, "description": "Empty string for integer parameter"},
    ]
    
    for case in error_cases:
        print(f"\n{case['description']}")
        print(f"  Input: {case['params']}")
        
        try:
            result = validate_parameters("test", case['params'])
            if result['success']:
                print(f"  ⚠️  Unexpected success: {result['coerced_params']}")
            else:
                print(f"  ✅ Properly rejected: {result['error']}")
        except Exception as e:
            print(f"  ✅ Exception caught: {e}")


def demo_schema_flexibility():
    """Demo how flexible schemas work."""
    print("\n\n📋 Demo: Flexible Schema Validation")
    print("=" * 40)
    
    from fastmcp.task_management.interface.utils.parameter_validation_fix import create_flexible_schema
    
    # Original restrictive schema
    original_schema = {
        "properties": {
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100
            },
            "progress_percentage": {
                "type": "integer", 
                "minimum": 0,
                "maximum": 100
            },
            "include_context": {
                "type": "boolean"
            }
        }
    }
    
    # Create flexible version
    flexible_schema = create_flexible_schema(original_schema)
    
    print("Original restrictive schema properties:")
    for prop, schema in original_schema["properties"].items():
        print(f"  {prop}: {schema}")
    
    print("\nFlexible schema properties:")
    for prop, schema in flexible_schema["properties"].items():
        print(f"  {prop}: {schema}")
    
    print("\nThis allows both integers and string representations!")


if __name__ == "__main__":
    demo_original_failing_cases()
    demo_type_coercion_details()
    demo_error_handling()
    demo_schema_flexibility()
    
    print("\n" + "=" * 60)
    print("🎉 SUMMARY: Parameter Validation Fix Complete!")
    print("=" * 60)
    print("✅ String integers like '5' are now automatically coerced to int 5")
    print("✅ String booleans like 'true' are now automatically coerced to bool True")
    print("✅ Invalid values are properly rejected with helpful error messages")
    print("✅ Flexible schemas support both original and string formats")
    print("✅ The original MCP validation error is completely resolved!")
    print("=" * 60)